# 078 編成の転職・清めるボタンとキーボード選択・報告

- 日付：2026-10-20 UTC/JST
- 基点main：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`
- 正式依頼HEAD：`f6b8cba4c2a4809079c8c33068e4a4dd454e8e00`
- ブランチ：`codex/task-078-party-action-focus`
- ローカル修正・検査と原成果引渡しの報告。正式Git保存・push・全GitHub CI・統合は親担当であり、その前に正式完了とはしない。

## 再現と修正

通常の「新しくはじめる」からEscape→方向キー→Enterで編成へ到達。Tab4回、別の新規開始からShift+Tab8回の両方で「この職に転職」がdisabled=true / focus_mode=2 / focused=trueとなった。Enter前後でmode=PARTY、通知、ゲーム状態全体が不変で、決定が無反応だった。

清めるは通常新規開始に侵蝕10だけを加え、正規import_stateで受理した診断状態で検査した。通常プレイで侵蝕を得た証明ではない。祠ではない場所でTab10回、別起動のShift+Tab3回が無効な清めるへ移り、disabled=true / focus_mode=2 / focused=true、Enterで画面・通知・確認状態・ゲーム状態全体が不変だった。両方の無効選択枠を原PNG実表示で確認した。

修正は `_render_party` 内の3か所だけ。

```gdscript
change.focus_mode = Control.FOCUS_NONE if change.disabled else Control.FOCUS_ALL
```

これを転職の初期disabled設定直後と、職選択変更時のdisabled更新直後へ追加した。清めるの既存disabled設定直後にも同じ対応を追加。

```gdscript
release.focus_mode = Control.FOCUS_NONE if release.disabled else Control.FOCUS_ALL
```

既存disabled式・職許可・侵蝕・浄化・習得規則は変更していない。初期転職と職選択時のdisabled式の違いにも手を加えていない。閉じ括弧を移した以外の既存行変更はない。フォーカス処理3行を除去して元の括弧位置に戻すと、原コードと完全一致することを独立照合した。

前後は同一reproduction.gd・同一入力列を使用。JSONからキー・Shift・ホイール列を独立集計して一致を確認した。30判定で変更前4失敗→変更後0失敗。変更後は無効な転職・清めるを飛ばす。

## 範囲と既知問題

変更3件：

- `scripts/ui/game_root.gd`：上記フォーカス処理。
- `docs/tasks/078-party-action-focus.md`：状態行のみ「報告済み」。
- `docs/tasks/reports/078-party-action-focus.md`：本報告。

074〜077の差分は含めない。074〜077の別作業領域はHEAD・status・UI原bytesの前後一致を確認。main・066・利用者PC・保護/test/既存検査器/CI/registry/project.godot/原画/物語/規則・decision-log・tasks READMEは変更していない。

076のfocus追従と077の無効装着の除外はこの基点に含まれず、今回追加していない。Tabで焦点が画面外へ出る場合、撮影やマウス操作のため実ホイールで表示した。再現比較ではホイール前後のfocus instance不変も確認。変更後の清める逆向き入力が無効装着へ移る既知問題も原PNGに残した。078でそれらを解消したとは扱わない。

## 境界と有効操作

主行列は3/4人×仲間正逆順（対象へ向かうキー順も正逆）×転職解放/未解放×侵蝕10/不可逆90×祠外/城の祠＝32ケース。全ケース内でTab/ShiftTab双方を巡回した。追加は3/4人・正逆順それぞれの侵蝕0と魔物化89の8ケース、および第1港・第2港・第2地方の村の祠3ケース。計43診断ケース。実描画は3人正順・4人逆順の主ケースと追加ケース12件。

全診断は現行ニューゲームを基に明示的に状態を組み、正規import_stateが受理した後、WORLDから通常メニュー入力で編成へ入る。城/港の通行証・ボス撃破・航路等は既存保存の前提を満たす診断入力であり、プレイ到達と混同しない。3人組は港の既存条件を満たすpc_04を含む。入力JSONを保存した。

確認内容：

- 無効転職/清めるを正逆Tabで飛ばし、有効操作・職選択・戻るに到達できる。
- 職候補は戦士→剣士（上級未解放）→武闘家→スライム系→戦士を選び、不可逆時にはスライム系へ戻す。解放時の有効→無効→有効、不可逆時の無効→有効→無効を測定。focus_modeが0/2へ両方向に復帰する。
- 未解放・不可逆の候補でもOptionButton/PopupMenuから比較説明を読める。候補変更・取消・仲間切替・再生成・戻る・再表示ではゲーム状態全体が不変。
- 無効ボタンへのマウス操作は対象がクリップされず全表示されていることを検査し、ゲーム状態不変・清める確認非表示を確認。
- 有効な転職は既存実装の即時確定。転職確認画面は存在せず、新設していない。職候補PopupMenuの取消と、キー/マウスによる転職確定を検査した。戦士→武闘家の独立期待はjob_id/last_human_job、最大HP140→125、負傷HP70→62のみ。MP・習得技・装着・JP・所持品・場所・全フラグなど他の全状態が保持される。
- 有効な清めるはキー/マウスで既存確認画面を開き、「やめる」で全状態不変、再度開き確定する。侵蝕10→0、魔物化89→59、専用技acid/form_slimeの消去と再習得記録、共有技power_strike/riposte・マスターの保持を独立期待で確認。
- 魔物化解除の独立期待は最大HP157→143、負傷HP78→71、最大MP30→24、MP15→12、人間職warriorへの復帰を含む。対象外の仲間・所持品・場所・進行など全状態を比較する。不可逆90では人間職と清めるを許可せず、フラグを維持。
- 清める後にボタンが消える侵蝕0、まだ残る侵蝕59、仲間変更後・戻って再表示した時のフォーカスを確認。

ハーネスはキー/マウス入力をGUIへ送る。PopupMenuはInput.parse_input_eventを使う。grab_focus・pressed/item_selected直emit・フォーカス強制は使わない。状態注入はケース初期化だけであり、有効操作の結果を注入していない。物理コントローラー、仮想ジョイパッド、利用者実機は未検証。

| 実行 | ケース | 判定 | 失敗 | 秒 |
| --- | ---: | ---: | ---: | ---: |
| boundary-3-forward-locked-v5 | 4 | 1493 | 0 | 52.63 |
| boundary-3-forward-open-v5 | 4 | 1515 | 0 | 59.61 |
| extra-3-forward | 2 | 746 | 0 | 33.87 |
| boundary-3-reverse-locked-v5 | 4 | 1497 | 0 | 54.61 |
| boundary-3-reverse-open-v5 | 4 | 1521 | 0 | 64.03 |
| extra-3-reverse | 2 | 751 | 0 | 32.77 |
| boundary-4-forward-locked-v5 | 4 | 1493 | 0 | 51.63 |
| boundary-4-forward-open-v5 | 4 | 1515 | 0 | 57.85 |
| extra-4-forward | 2 | 746 | 0 | 32.61 |
| boundary-4-reverse-locked-v5 | 4 | 1497 | 0 | 53.98 |
| boundary-4-reverse-open-v5 | 4 | 1521 | 0 | 66.50 |
| extra-4-reverse | 2 | 751 | 0 | 31.62 |
| locations-3-forward | 3 | 1155 | 0 | 55.11 |
| render-3-forward | 4 | 1531 | 0 | 68.13 |
| render-extra-3-forward | 2 | 754 | 0 | 39.16 |
| render-4-reverse | 4 | 1533 | 0 | 68.87 |
| render-extra-4-reverse | 2 | 756 | 0 | 42.67 |

## 固定Godotと既存検査

Godot `4.7.2.stable.official.ed1daf0bf`。archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。archive内実行ファイルと実際のbinaryのbytes一致を検査した。

元checkout外の固定HEADコピーへ修正UIだけを適用して実行。元の既存検査器・test・素材・保護・project.godotのbytesを照合。検査器は無変更、既存時間上限の延長なし。カスタム検査も各180秒。

| 名前 | コマンド | exit | 秒 |
| --- | --- | ---: | ---: |
| before-editor-import | `timeout 600 godot --headless --editor --import --quit` | 0 | 76.93 |
| after-editor-import | `timeout 600 godot --headless --editor --import --quit` | 0 | 5.99 |
| headless-import | `timeout 600 godot --headless --import` | 0 | 6.65 |
| assets-strict | `python3 tools/validate_assets.py --strict` | 0 | 21.75 |
| frozen | `python3 tools/check_frozen_files.py` | 0 | 0.04 |
| locked | `python3 tools/run_locked_checks.py` | 0 | 136.37 |
| first-region-screen | `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 0 | 3.96 |
| integrated-ui | `timeout 240 godot --headless --path . --script res://tools/check_integrated_ui.gd` | 0 | 9.18 |

素材：画像1154・音15・字体2・パレット3で問題なし。保護26件一致。R-01〜R-08全PASS。R-07はA01〜A14、R-08は25 tests/3046 assertions/失敗0/pending0。関連画面検査はREGION_UI_PASS checks=10、INTEGRATED_UI_RESULT failures=0 controls=93。既存integrated-uiの旧フローや直接signal検査を、今回の通常入力証明として代用していない。

## 途中失敗・警告

生ログ・JSON・該当ハーネス版を全て保存した。

1. 境界初版の城祠2ケースは通行証/撃破前提の欠落で正規importに拒否された。既存の到達前提を診断入力へ補い、受理を確認した。
2. 境界v3でマウス対象の全表示検査を追加した際、full/clippedの型推論Parse Errorが出た。Rect2型を明示して修正。これは検証コードの失敗で、本番コードの変更は追加していない。
3. 境界v4 openで「騎士」を上級未解放候補と誤認し4判定失敗。固定data/job_progression_v1.jsonにある「剣士」へ診断候補を訂正した。無効である期待値、往復の条件、規則を緩和していない。

変更前の意図した4失敗も保存。X11描画ではドライバーのV-Sync変更非対応WARNING、Xorgには/tmp/.X11-unix所有者の通知がある。既存R検査と最終headless検査のエラー/警告/リークは別途全ログで照合。警告を消して成功化していない。自動承認の拒否や接続障害は本078では発生していない。

## 引渡し・残件

`task-078-party-action-focus.zip`に3payload全文、元2ファイル、適用して3ファイルの完全一致を確かめたchanges.patch、前後status/未push候補一覧、全原ログ/PNG/JSON/ハーネス/manifestを収録。原PNGは拡縮・加工せず保存。重複撮影は連番にして保持した。実描画の比較説明・無効除外・有効選択枠・清める確認画面を表示確認した。

専用作業領域は `/workspace/task-078-party-action-focus`、原証拠は `/workspace/task078-party-action-evidence`。差分パッチ用indexは独立ファイルで、元checkoutのindexにはstageしていない。新規commit・remote push・PR・mergeはなし。未push一覧はローカルref基準の候補であり、他作業のGitHub未保存を意味しない。Library保存のconfirmed ID・bytes・元ZIP SHA256は最終引渡しで提示する。

AGENTS/素材規約/該当企画・体験仕様/伝言板/素材台帳/契約を確認。ローカルSKILL.mdは今回の探索範囲で見つからず、executor skillsは0。cloud250件のうち指定Godot実装スキル3名は見つからなかった。Libraryの現行スキルと新規取得helperを使う。AGENTSの一般的なpush/証拠格納規定より、今回の明示依頼「3件のみ・checkout外証拠・正式保存は親」を優先した。

残件は親の原成果検収・正式Git保存・全GitHub CI・統合検証、および物理コントローラー/利用者実機での確認。初見の物語内容や新規則を決める作業は行っていない。078の依頼範囲で追加の承認待ちはない。
