# 079 タイトルの自動保存復帰とキーボード選択・報告

- 日付：2026-10-20 UTC/JST
- 基点main：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`
- 正式依頼HEAD：`8411327499a67c7fe2e8fb25dc7e1a2125a0c630`
- ブランチ：`codex/task-079-checkpoint-focus`
- ローカル修正・検査の報告。正式保存・push・PR・全GitHub CI・統合は親担当であり、ここでは正式完了としない。

## 再現と修正

隔離された保存なしの初期タイトル、および通常「新しくはじめる」→Escape→「タイトルへ」の2状態を検査した。各状態でTab、Shift+Tab、下、上、マウスの5経路、計10ケースすべてでcheckpointがdisabled=true / focus_mode=2 / focused=trueとなった。キー経路はEnterを送ってもMENU・通知・ゲーム全状態・保存ファイルが不変で、決定が無反応だった。マウス経路はクリックのみ。原PNGの灰色ボタンに選択枠が出ることも実表示で確認した。

初期タイトルのTab3回／現在冒険ありのTab4回、両者のShift+Tab3回で再現。方向キーは通常Tabで初期選択を始めてから下2回／3回、逆向きはShift+Tabで末尾を選んでから上2回で再現した。初期focusなしでは方向キーだけで選択が始まらず、上キーは先頭から末尾へ折り返さない既存挙動も記録した。この別挙動は変更していない。

修正は `_render_menu` の既存 `checkpoint.disabled = not FileAccess.file_exists(checkpoint_path)` 直後に、次の1行を追加しただけ。

```gdscript
checkpoint.focus_mode = Control.FOCUS_NONE if checkpoint.disabled else Control.FOCUS_ALL
```

追加行を除けば元ソースとbyte単位で完全一致する。disabled条件・手動保存の分離・読込・拒否・backup回復規則は変更していない。前後同じハーネス、同じ51イベントで104判定中10失敗→0失敗。変更後は無効ボタンを飛ばし、順方向は試遊記録、逆方向は手動再開へ移る。Enterは移動先の既存有効操作を実行するため、修正後も画面不変であるとは要求していない。どちらでも保存ファイルは不変。

## 保存と遷移の検査

全処理は079専用XDG領域と `RPG_QA_SAVE_PREFIX` の固有名を使用。実利用者の保存は読取・削除していない。各ケースは新規隔離名で既存ファイルがないことを確認する。再起動相当ケースだけ同じ隔離名を再利用する。

正常保存は基点の無変更R-07を完走して得た原checkpoint（8533bytes、SHA256 `88501875070c1a362eac45910a47780216e10309a2b1fd88288dc240b42dc1f4`）。原byteと生ログ・生成元checkerのhashを保存した。R-07はニューゲーム・移動等にInputEventを使うが、戦闘は既存の戦闘APIも使うため、全行程を物理キーで到達した証明とはしていない。各ケースへの原保存のコピーは診断配置として明示し、そのケースで再び道中をプレイしたとは扱わない。期待するゲーム全状態はPythonでJSON/gzipとメタデータを独立に分離して抽出し、復帰実装のexport結果を期待値に転用していない。

- 正常8ケース：現在冒険なし/あり×Tab・逆Tab・下キー・マウス。有効なcheckpointへ到達し、洞窟の原保存状態（3人、全位置・所持品・進行等）へ完全復帰。既存通知、手動保存と正常checkpointのbyte保持、checkpoint_loadsだけ1増加を確認。連続Enter/echo入力で重複復帰しない。タイトルへ戻って再表示しても有効選択を維持。
- 拒否12ケース：現在冒険なし/あり×壊れたJSON・無効な空object・全員戦闘不能×キー/マウス。全滅fixtureは正規import/save APIで作成した診断入力。既存拒否通知とMENUを保持し、ゲーム全状態、manual/checkpointの本体・bak・tmpの存在/hash、計測のcounters/events/answers/sourceを変更しない。連続Enter3回と試遊画面から戻る再生成後も同じ。時間計測はフレームで自然に進むため、不変比較の対象にしていない。
- 遷移4ケース：通常UIの手動保存のみではcheckpointは無効。原checkpointを隔離名へ追加し試遊画面→戻るで再表示すると有効化し正常復帰。ニューゲームを再開してタイトルへ戻っても手動/自動保存のbyteを保持。手動保存ボタンは独立した元の冒険へ復帰し、checkpointを変更しない。Escapeで通常メニューの取消も確認。同じ保存を持つ新規Mainノードではマウスで正常復帰する（実OSプロセスの再起動ではない）。
- backupのみで本体がない場合は既存条件どおり無効のまま。マウス連続操作でも読込/書換えしない。壊れた本体＋正常backupの場合は既存回復処理が正常状態を復元し、手動保存を保持する。本体を正常backupから修復する既存動作は許容し、byte不変とはしていない。

試遊画面のEscapeには既存取消処理がないため、実在する「戻る」を使って再生成を確認した。対象外の手動再開ボタンはファイルがなくても有効である既存挙動を保持。状態や規則を変える別の修正はしていない。

前後の実入力イベントをJSONから独立比較した。再現51、正常325、拒否657、遷移136イベントがそれぞれ完全一致（キー/Shift/echo/マウス対象・座標・ケース順）。遷移の変更前14失敗は無効checkpointのfocusだけで、変更後0失敗。さらに正常8・拒否12・遷移4ケースをX11描画で実行し、原PNGを保存した。

| 実行 | ケース | 判定 | 失敗 | 秒 |
| --- | ---: | ---: | ---: | ---: |
| before-render-v3 | 10 | 104 | 10 | 22.74 |
| after-render | 10 | 104 | 0 | 29.54 |
| before-valid-v2 | 8 | 486 | 0 | 28.23 |
| after-valid | 8 | 486 | 0 | 29.56 |
| before-rejected | 12 | 728 | 0 | 60.30 |
| after-rejected | 12 | 728 | 0 | 74.66 |
| before-transitions | 4 | 206 | 14 | 13.16 |
| after-transitions | 4 | 206 | 0 | 19.40 |
| render-valid | 8 | 516 | 0 | 48.44 |
| render-rejected | 12 | 746 | 0 | 69.79 |
| render-transitions | 4 | 214 | 0 | 24.05 |

ハーネスはGUIへInputEventKey/InputEventMouseButtonを送る。grab_focus、signal直emit、focus強制を実入力証明に使っていない。診断fixtureを作る処理とユーザー操作の検査は分離している。原PNGは加工していない。物理コントローラー・仮想ジョイパッド・利用者実機は未検証。

## 固定環境と既存検査

Godot `4.7.2.stable.official.ed1daf0bf`。archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。archive内binaryとのbyte一致を確認。固定HEADのcheckout外コピーにUI修正だけを適用し、既存checker・test・assets・保護・project.godotを原hash照合した。検査器変更・省略・時間上限延長はない。カスタム各実行も180秒以内。

| 検査 | コマンド | exit | 秒 |
| --- | --- | ---: | ---: |
| before-editor-import | `timeout 600 godot --headless --editor --import --quit` | 0 | 98.54 |
| source-normal-r07 | `timeout 180 godot --headless --path . --script res://tools/smoke_first_region.gd` | 0 | 90.08 |
| after-editor-import | `timeout 600 godot --headless --editor --import --quit` | 0 | 9.02 |
| headless-import | `timeout 600 godot --headless --import` | 0 | 5.97 |
| assets-strict | `python3 tools/validate_assets.py --strict` | 0 | 10.86 |
| frozen | `python3 tools/check_frozen_files.py` | 0 | 0.07 |
| locked | `python3 tools/run_locked_checks.py` | 0 | 155.88 |
| battle-recovery | `timeout 180 godot --headless --path . --script res://tools/check_battle_recovery.gd` | 0 | 58.25 |
| first-region-screen | `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 0 | 5.53 |
| integrated-ui | `timeout 240 godot --headless --path . --script res://tools/check_integrated_ui.gd` | 0 | 8.02 |

素材1154・音15・字体2・パレット3で問題なし。保護26件一致。R-01〜R-08全PASS。既存の直接API/signalを含む検査は、上記のGUI入力証明とは別に記録している。各検査の詳しい集計・警告はaudit.jsonと全生ログを参照。

## 途中失敗・警告・接続通知

変更前の意図した失敗を含め、生ログ・JSON・旧ハーネスを保存した。

1. 保存codecの探索で存在しない旧パスを読み、現物saved_document.gdを検索して確認した。
2. 再現初版では未選択状態の方向キーが選択を開始しなかった。v2で通常Tabを追加。上キーは先頭で折り返さないためv3はShift+Tabから上へ移動。元版・v2・v3の全原証拠を保持し、無効focus除外の期待値は緩和していない。
3. behavior初版は `var f := path+suffix` の型推論Parse Errorで起動できなかった。String型を明示した。behavior-v1.gdとbefore-valid.logを保持。後続の成功ログで上書きしていない。
4. X11はV-Sync変更非対応WARNING、Xorgは/tmp/.X11-unix所有者通知とDBus接続失敗の反復ログがある。警告を削除していない。最終headless・既存検査・R別ログのエラー/警告/リークを独立に点検した。
5. 02:55 UTCの接続切れ通知を親から受領。同一環境で読取・ps・git確認は成功し、修正後import完了・Godot検査の実行中なし・証拠保存済みを確認した。重複起動や別経路の迂回はせず、同じ079で未実施分を続行。connection-check.txt参照。自動承認拒否は発生していない。

## 範囲・引渡し

変更はUIの1行、依頼書の状態行「報告済み」、本報告の3ファイルのみ。その他7720 tracked filesは元bytesのまま。074〜078の修正は混入せず、別作業領域のHEAD/status/UI hashを照合。078の既存証拠は原ZIPを含む275ファイルが元hash一致。1件の展開先logs/xorg.logだけは、079開始前から稼働するXorg :81 PID7334がDBus接続失敗を自動追記していた。元85769bytesのprefixは作業開始時SHAと完全一致し、原内容は保持される。078側には書き込まず、079に原prefix・追記snapshot・照合JSONを保存した。初回包装のAssertionErrorもpackaging-errors.txtとfinalize-v1.pyに保持。main/066/利用者PC/保護/test/checker/CI/registry/project.godot/原画/物語/規則/親台帳は変更していない。

AGENTS・素材規約・該当企画/体験仕様・battle-recovery-v1・配置済スキルを確認。078から不変の契約はhash比較で再利用した。ローカルstoryteller skillはゲーム実装を対象外と明示しており適用していない。指定Godot実装スキルは利用可能一覧に見つからなかった。Libraryはこの作業中に読んだ現行スキルと取得helperを使う。明示依頼の3件範囲・checkout外証拠・正式保存は親を優先した。

`task-079-checkpoint-focus.zip`は3payload全文、基点の元2ファイル、独立indexで適用して全payload一致を検証したchanges.patch、前後statusと未push候補一覧、原ログ/PNG/JSON/ハーネス/manifestを含む。raw runtime/キャッシュは配布せず、検証で使った保存bytesは各savesとsource-normalへ収録。ハーネスの実行時絶対パスはmanifestの作業領域を参照する。ZIP全entryのbyte一致・CRC・SHAを検証し、Library confirmed ID/bytes/元ZIP SHAを最終引渡しで返す。

新規commit・remote push・PR・mergeは行っていない。未push一覧はローカルrefの候補であり、他タスクのリモート未保存を示すものではない。079の残件は親による原成果検収・正式Git保存・全GitHub CI・統合確認と物理コントローラー/利用者実機検証。ローカル検査成功をゲーム全CI成功とは扱わない。
