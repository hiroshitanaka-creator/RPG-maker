# 077 編成画面の無効な装着ボタンとキーボード選択・報告

- 検証日：2026-10-20 UTC/JST
- 基点main：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`
- 正式依頼HEAD：`351989f3cf0c380fcadde2bb25486dde5bced4da`
- ブランチ：`codex/task-077-party-disabled-focus`
- ローカル修正・検証・原成果引渡し。正式Git保存・GitHub全CIは親担当であり、その前に正式完了とはしない。

## 通常到達での実害と変更

状態注入なしの「新しくはじめる」からEscape→方向キー→Enterで現在の編成画面へ到達した。初回のTab9回、別の新規開始からShift+Tab3回の双方で、空の技欄の隣にある「装着」へ焦点が移った。

変更前は装着Buttonのdisabled=true、focus_mode=2（FOCUS_ALL）、focused=trueを実測。Enterの前後でmode=4（PARTY）、通知、ゲーム状態全体が不変で、決定は無反応だった。前後で同じハーネス・入力列を使用し、キーと撮影補助ホイールの列も別集計で一致確認した。

変更は `_render_party` で装着の既存disabled条件を設定した直後の1行だけ。

```gdscript
if equip.disabled:equip.focus_mode = Control.FOCUS_NONE
```

変更後は通常のTab9回が「探索へ戻る」へ進み、Enterで探索へ戻れる。逆向きのShift+Tab3回は空のOptionButtonへ進み、無効装着を飛ばす。空のOptionButtonも説明閲覧用の選択欄として残している。前後17判定で変更前3失敗、変更後0失敗。

対象は無効な装着Buttonだけ。転職、清める、OptionButton、PopupMenuのfocus設定は変更せず、検査でも元の値を確認。技候補が残る満枠では、ボタンが有効な既存挙動を維持し、決定時に既存の枠上限判定が拒否する。無効条件や枠数を新しく追加していない。

変更した3件：

- `scripts/ui/game_root.gd`：上記1行。
- `docs/tasks/077-party-disabled-focus.md`：状態行だけ「報告済み」。
- `docs/tasks/reports/077-party-disabled-focus.md`：本報告。

074/075/076の差分は含まない。依頼HEADと基点mainの差分は077依頼書だけである。

## 既知のスクロール問題との区別

076の `scroll.follow_focus = true` は追加していない。基点の編成ではTab移動時に下部の焦点が見えなくなる問題が残ることを、矩形・scroll_vertical・follow_focus=falseで記録した。

無効な装着へ焦点が入ることとEnter無反応を検査し、撮影時だけ実際のホイール入力で下部を表示した。ホイール前後で焦点所有者のinstance IDが同じことも確認した。スクロール位置やfocusをコードで強制設定して見た目を成功化したものではない。前後のPNGは原bytesのまま保存し、無効装着の白い選択枠、変更後の「探索へ戻る」/OptionButtonの選択枠を実表示で比較した。

本提出だけで画面外選択問題も解消したとは報告しない。076との統合とその検収は親担当である。

## 境界・状態条件・説明閲覧

3人/4人×正順/逆順×技候補0/1/2件×未解放/解放×空枠/満枠＝48ケースを検査した。

空枠では習得総数も0/1/2件。満枠では既習得の「堅守」「護衛」を2枠へ装着し、そのほかの候補0/1/2件を加えたため習得総数は2/3/4件となる。習得技0件なのに満枠などの矛盾する状態は作っていない。候補は「強打」「応撃の構え」。各状態は正規GameSession.import_stateで受理されることを確認した診断注入であり、通常プレイ到達の証明とは区別した。注入後は通常メニューのキーで編成へ入った。

各ケースで次を実施した。

- Tab/Shift+Tab各16回で無効な装着に焦点が入らず、OptionButton・戻る・有効な装着には到達できることを実入力で確認。
- 仲間を末尾へ切り替え、再生成したボタンのdisabled/focus_modeとゲーム状態全体を照合。
- 技候補があればPopupMenuで説明を閲覧。複数なら「強打」から「応撃の構え」へ変更して説明が切り替わり、元へ戻せることを確認。未解放時も同様に閲覧でき、状態は変わらない。強打の「物理攻撃150% × 1回」は固定期待値と照合。
- 無効装着へのマウスクリックは全状態不変。有効な満枠のEnterは既存の拒否通知と全状態不変を確認。
- 有効な空枠ではキーで装着/解除、マウスで装着/解除し、対象のequipped_abilitiesへの1要素追加/削除だけを独立期待値とした全状態比較を実施。
- 満枠からの解除で候補が復活した場合も、解放条件に応じたボタン状態を保持。解放済みならマウスで復活候補を再装着できる。
- 装着/解除後、戻る再表示後にも同じfocus条件を再確認。表示移動・説明・仲間表示変更・取消ではHP/MP・JP・所持品・位置・進行を含むゲーム状態全体が不変。

| 実行 | ケース | 判定 | 失敗 | 秒 |
|---|---:|---:|---:|---:|
| 3人正順 | 12 | 1817 | 0 | 152.71 |
| 3人逆順 | 12 | 1817 | 0 | 152.19 |
| 4人正順 | 12 | 1817 | 0 | 155.20 |
| 4人逆順 | 12 | 1817 | 0 | 154.23 |
| 実描画追加（各人数/順序の未解放複数候補、有効1候補） | 8 | 1328 | 0 | 123.41 |

説明欄・有効装着の原PNGを実表示し、文字・選択枠を確認した。focus所有者、disabled、focus_mode、矩形、可視部分、scroll量、PopupMenu選択番号、全状態をJSONへ収録。追加実描画JSONには説明本文と候補数も記録した。

入力はInputEventKey/MouseButtonを既存GUIへ送り、PopupMenuだけはInput.parse_input_eventで本来の入力処理へ渡した。grab_focus、pressed/item_selected直接emit、UI状態の書換えはハーネスにない。ここでの入力は自動化したキー/マウスの仮想入力であり、物理コントローラー操作を検証したとはしない。077では仮想ジョイパッドも別途実行していない。

## 固定Godotと既存検査

Godot `4.7.2.stable.official.ed1daf0bf`。archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。archive内と実行binaryのbytes一致を確認。

checkout外の固定HEADコピーへ修正UIを適用して実行した。既存検査器・test・保護・素材・project.godotのbytesを固定HEAD manifestと照合し、成果以外の生成物を元checkoutへ書かない。

| コマンド | 結果 |
|---|---|
| `timeout 600 godot --headless --editor --import --quit` | 前79.15秒/後5.91秒、exit 0 |
| `timeout 600 godot --headless --import` | 6.19秒、exit 0 |
| `python3 tools/validate_assets.py --strict` | 8.73秒、exit 0。画像1154・音15・字体2・パレット3、問題なし |
| `python3 tools/check_frozen_files.py` | exit 0。保護26件全一致 |
| `python3 tools/run_locked_checks.py` | 119.35秒、exit 0。R-01〜R-08全PASS、各verify既存300秒上限維持 |
| `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 4.51秒、exit 0、REGION_UI_PASS checks=10 |
| `timeout 240 godot --headless --path . --script res://tools/check_integrated_ui.gd` | 7.54秒、exit 0、INTEGRATED_UI_RESULT failures=0 controls=93 |

R-07はA01〜A14とFIRST_REGION_PASS、R-08は25 tests・3046 assertions、failed/pending 0を照合。既存integrated-uiには旧フロー・直接signal検査があるため、それで077の通常入力を代用していない。

## 失敗・警告の保全

境界ハーネス初回は `Cannot infer the type of "disabled" variable because the value doesn't have a set type.` というParse Errorで起動しなかった。初版boundary_probe-v1.gdとlogs/boundary-3-forward.logを保持し、検査側の変数へbool型を明示して再実行した。期待値・装着条件・既存検査・上限の変更なし。集計用Pythonワンショットの閉じ括弧不足もpreparation-errors.txtに記録し、修正後に前後入力一致を検証した。

全実行でタイムアウトなし。成功マーカーに加えてSCRIPT ERROR/Parse Error/ERROR/WARNING/リークを監査。成功したheadless検査に該当エラー/警告はない。実描画3実行には各1件、環境のV-Sync非対応警告 `Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.` がある。Xorgのソケット所有者通知も保存した。警告ゼロとして扱わない。

## 契約・範囲・引渡し

AGENTS.md、.scope-lock、素材規約、docs/tasks/README.md、職業/装着仕様は前件で読んだ版とのbytes一致を確認。現行の装着・解除コードと関連画面検査を読み直した。Godotスキルはローカル配置・クラウド一覧250件・executor0件に見つからず、導入していない。Library保存は現在のLibraryスキルに従う。

今回の明示依頼に従い、通常のcommit/push・repo内証拠保存を親の正式保存方式へ分担した。docs/decision-log.mdとdocs/tasks/README.mdは親担当として未変更。066、main、利用者PC、remote push/PR/mergeは実施していない。074/075/076作業木のHEAD・状態・UIハッシュを前後比較する。

作業前後の差分・ローカルrefとの差分候補をgit-before.txt/git-after.txtへ保存。候補一覧をGitHub未保存と断定しない。read-only ls-remoteで077のリモート枝が正式依頼HEADと一致することを確認し、新規ローカルcommitは作っていない。

証拠ルート `/workspace/task077-party-disabled-evidence/`。ZIPには3payload全文、元bytes、固定HEADへ適用し3パス全文一致まで照合したpatch、原PNG・前後比較索引、原ログとR全ログ、ハーネス、全状態/入力JSON、全ファイルhash、audit、manifestを収録する。環境変数・キャッシュ・検証コピー・一時Git index・Library転送情報は除外。ZIP全件のbytes/CRC/SHA256と保存成功時のID/bytesを別途返す。

復旧は追加1行を削除し、依頼状態行を戻し、本報告を除くことで基点の3パスへ戻せる。

残る未検証は親による正式保存後のGitHub全CI・統合、物理コントローラー/利用者実機。076の既知スクロール問題も本差分には含めず、解消済みとはしない。実装作業を妨げる権限拒否・承認待ちは発生していない。
