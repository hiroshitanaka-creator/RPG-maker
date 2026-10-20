# 075 最新main統合候補・再検証報告

- 日付：2026-10-20 UTC/JST
- 第1親（075 branch）：`878b1d911fc9aa32c1addb66d1520b8f32fc8fb9`
- 第2親（指定最新main）：`891cba3433ed0ab72f8559051eee1e35a534e323`
- 共通基点：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`
- 元075完成実装：`50cc27302718e5650c2f558817591e380677f45f`
- 既存branch：`codex/task-075-items-keyboard-focus`、PR #51。
- 実装検査対象tree：`a6d66bdd05e60c6d12d9dd70ce07071e3c1e1991`（本報告を加える前の統合ソース）。
- ローカル統合候補の報告。merge commitの正式保存・push/PR CI・main反映は親担当。ここでは正式完了とはしない。

## 統合方法と範囲

2026-10-20の依頼者承認に基づく、完成済み075への074取込み。新機能・新規則は追加していない。既存075作業領域 `/workspace/task-075-items-focus` は未保存差分を含むため触らず、HEAD/statusとtracked/untracked全ファイルのhashを記録した。指定第1親から `/workspace/task-075-main-integration` をdetached worktreeとして作り、`git merge --no-commit --no-ff 891cba3433ed0ab72f8559051eee1e35a534e323` を実行した。

競合は `_button` の同じ挿入位置だけ。075のitems行と074のtravel行を両方そのまま残した。

```gdscript
if screen_mode=="items" and not enabled:button.focus_mode=Control.FOCUS_NONE
if screen_mode=="travel" and not enabled:button.focus_mode=Control.FOCUS_NONE
```

074の `_ready` 初期focus対象 `commands/items/travel/shop` も保持。items行を除くと第2親のUIとbyte単位で一致し、travel行と初期focusのtravel指定を除くと第1親UIとbyte単位で一致する。条件式の再設計、使用可否、薬効果、MP、帰還先、保存処理の変更はない。競合原文とmerge失敗ログを保全した。

第1親に対する候補差分は4件。

- `docs/tasks/074-return-menu-keyboard-focus.md`：指定mainから原bytesのまま追加。
- `docs/tasks/reports/074-return-menu-keyboard-focus.md`：指定mainから原bytesのまま追加。
- `scripts/ui/first_region_screen.gd`：074と075の上記UI統合。
- `docs/tasks/reports/075-main-integration.md`：本報告を新規追加。

075原依頼・原報告、親記録 `docs/decision-log.md` と `docs/tasks/README.md` は第1親の原bytesと完全一致。元075完成実装50cc…→指定第1親878…の変更が親記録2件だけであることも確認した。元branchのその他すべて、main側の074追加文書すべてを保持する。全パスを両親・共通基点のGit blob/modeと比較し、片側変更を落としていないことを機械検証した。両側変更はUIだけで、上記の逆算比較を使う。

保護・test・既存checker・CI・assets/registry.json・project.godot・原画・仕様・物語・066・親台帳を編集していない。mainや既存branchのrefを動かしていない。新しいcommit、remote push、PR作成、mainへのmergeは実施していない。候補はHEAD=第1親、MERGE_HEAD=第2親の未commit状態で保持。親が正式な2親merge commitを保存するためのcandidate tree、両親からの全差分patch、適用検証結果をZIPへ収録する。

## 今回の入力回帰

検査はすべて今回の統合候補で新規実行した。過去の成功ログを今回の成功に代用していない。元ハーネスはcheckout外へコピーし、隔離保存prefixだけを今回用に変えた。現行ソースと検査コピーのUI hash一致、既存検査器・test・assets・契約・CI・project.godotの原bytesを別途照合した。

075は通常ニューゲーム1件と3/4人・正逆順の再現4件、境界96件（3/4人×正逆順×地図0/1×薬0/1/3×混在/全満HP/全死亡/HP1）、地図なし・薬0/1の描画8件を実行。全方向とTab、無効人物/未所持地図のマウス、地図往復、薬使用・再生成、戻る・再表示・Escapeを確認した。通常ニューゲームケースは状態注入なし。その他は診断状態の正規importを使い、通常プレイ到達とは区別する。薬の独立期待は対象HP=min(max_hp,hp+50)と薬1減少だけで、全状態を比較する。

074は3/4人×正逆順×通常/先頭死亡/先頭MP1/全員MP1の16件をheadlessと実描画の両方で実行。初期focus、無効人物/未選択目的地の除外、使用者選択・選び直し、再生成、取消、戻る、再表示、有効帰還を確認。両実行の全入力とfocus遷移も一致する。帰還期待は選択者MP2消費、既存入口前の徒歩位置、船の既存帰港位置だけで、他の全状態を比較する。

さらに統合専用16件を実描画で検査した。3/4人・正逆順・上記4つの帰還条件の同じゲーム状態で、通常コマンドから「どうぐ→帰還→どうぐ→帰還」を実キーで往復する。無所持地図・満HP/死亡者を飛ばし、負傷者に薬を使用。薬0の再生成で戻るだけへfocusする。帰還画面へ移ると生存/MP条件を満たす最初の仲間を選択し、Tabで無効対象を飛ばす。取消してどうぐへ戻っても無効focus除外を保持し、再度帰還を開いてMP2・徒歩位置・船帰港を確認した。全員MP不足ケースは帰還せず取消して全状態を保持する。

| 今回の実行 | ケース | 判定 | 失敗 | 秒 |
| --- | ---: | ---: | ---: | ---: |
| items-normal-render | 5 | 44 | 0 | 21.42 |
| items-3-forward | 24 | 1092 | 0 | 95.12 |
| items-3-reverse | 24 | 1092 | 0 | 132.86 |
| items-4-forward | 24 | 1236 | 0 | 134.51 |
| items-4-reverse | 24 | 1236 | 0 | 100.45 |
| items-boundaries-render | 8 | 394 | 0 | 44.40 |
| travel-headless | 16 | 542 | 0 | 50.38 |
| travel-render | 16 | 606 | 0 | 94.28 |
| combined-3-render | 8 | 668 | 0 | 51.69 |
| combined-4-render | 8 | 722 | 0 | 50.47 |

入力はGUIへ送るInputEventKey/InputEventMouseButtonで、ハーネスからgrab_focus・signal直接emitは使わない。本体の既存初期focus処理はそのまま。診断注入はケース初期状態のみで、操作後の期待結果を注入しない。原PNGは1024×576で保存し、文字・選択枠・無効除外・使用後再表示を原画面で確認した。画像加工はない。過去074の長い通常到達ルートを新規完走したとは主張せず、今回の新規R-07と上記診断回帰をそれぞれ記録する。物理コントローラー・利用者実機の確認は未実施。

## 固定Godotと既存検査

Godot `4.7.2.stable.official.ed1daf0bf`。archive SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、binary SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。archive内binaryと使用binaryの全bytesを照合した。

main取込み後、他のGodot検査より先に `godot --headless --editor --import --quit` を実行して成功を確認。その後にheadless import、R-01〜R-08、frozen、assets strictと関連画面検査を実行した。独立した共通基点コピーもeditor import後に旧coastalを実行した。元の600/300/240/180/120秒上限を維持し、検査省略・弱化・待ち時間延長は行っていない。カスタムGUI各実行は180秒上限。

| ログ名 | コマンド | exit | 秒 |
| --- | --- | ---: | ---: |
| editor-import | `timeout 600 godot --headless --editor --import --quit` | 0 | 117.83 |
| headless-import | `timeout 600 godot --headless --import` | 0 | 10.74 |
| assets-strict | `python3 tools/validate_assets.py --strict` | 0 | 14.51 |
| frozen | `python3 tools/check_frozen_files.py` | 0 | 0.07 |
| locked | `python3 tools/run_locked_checks.py` | 0 | 177.67 |
| first-region-screen | `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 0 | 5.51 |
| second-region-coast | `timeout 180 godot --headless --path . --script res://tools/check_second_region_coast.gd` | 0 | 4.25 |
| region2-port | `timeout 180 godot --headless --path . --script res://tools/check_region2_port.gd` | 0 | 12.05 |
| village-regression | `timeout 180 godot --headless --path . --script res://tools/check_region2_village_regression.gd` | 0 | 86.96 |
| saved-position | `timeout 120 godot --headless --path . --script res://tools/check_saved_position_relocation.gd` | 0 | 9.33 |
| integrated-ui | `timeout 240 godot --headless --path . --script res://tools/check_integrated_ui.gd` | 0 | 15.58 |
| coastal-legacy | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 124 | 180.03 |
| baseline-editor-import | `timeout 600 godot --headless --editor --import --quit` | 0 | 6.19 |
| baseline-coastal-legacy | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 124 | 180.03 |

R-01〜R-08全PASS。素材1154・音15・字体2・パレット3で問題なし、保護26件一致。現行のfirst-region-screen、second-region-coast、region2-port、village-regression、saved-position、integrated-uiも成功。R個別生ログと成功マーカーを保存した。未commit候補のため、検査が表示するgit HEAD/buildは第1親878…であり、統合後正式commitのCI成功を意味しない。検査対象実ファイルのtree/hashで候補を識別する。

## 残る失敗と警告

旧 `tools/check_coastal_travel.gd` は候補と共通基点の今回実行で同じ失敗。34行目の `return_learned` 参照でSCRIPT ERRORとなり、どちらも既定180秒のtimeoutでexit124。両原ログはbyte単位で一致した。現行関連検査の成功でこの失敗を相殺せず、全検査成功とは扱わない。検査器・fixture・期待値・上限は変更していない。旧coastalの修正は今回の許可範囲外であり、必要なら別範囲の依頼が必要。

X11描画にはV-Sync変更非対応WARNINGがあり、Xorgには/tmp/.X11-unix所有者通知とDBus接続失敗の反復ログがある。警告を消去していない。Xorgは今回用:83だけを使い、撮影終了後に停止して原ログを固定した。元074/075のXorgや元成果ZIPは操作していない。headless成功検査とR原ログのSCRIPT ERROR/ERROR/WARNING/Parse Error/リークを監査した。

Gitの初回通常mergeは同じ挿入位置の競合でexit1となった。これは両方の追加行を保持して解消し、競合原文と操作記録を残した。原PNGの生成途中に未生成パスを表示しようとした際はNo such file or directoryとなった。検査や原画像を変更せず、生成後の同じ原PNGを表示確認した（preparation-notes.txt）。カスタム検査の失敗・期待値修正は今回発生していない。

包装時の全パス照合で、Git ls-treeが日本語名を引用する形式を誤ってPathに使ったFileNotFoundErrorを検出した。NUL区切りへ修正し、基点コピーだけで誤名になっていた12パス（incoming画像11・文書1）を、全原bytesを保持して正規名へ直した。統合候補や元原画は変更していない。補正スクリプトの件数1という誤ったassertionも失敗として記録し、実際の全12パスとhashを保存した。

実行順序の誤りで補正終了前に再検査を始め、初回baseline editor importの全文生ログを上書きした。この原ログは回復不能であり、全途中ログを完全保全できたとはしない。初回exit0/136.8224391469994秒は取得済みtool結果から別記録。初回coastal本文は上書き前に候補ログとbyte一致を確認済みで、同一内容からrecovered名で復元したが、元ファイルそのものの保全とは区別する。早期再検査はcoastal実行中に中止（exit -15/51.22892616399622秒）し、prematureログを保持。

その後、基点全7721ファイルのGit blob一致を確認し、既存ログの上書きを拒否するガードを付け、editor import→coastalを600/180秒のまま再実行した。表のbaseline行はこの最終再実行である。元版の包装/基点作成コード、パス補正記録、証拠欠損、中止した実行はpackaging-errors.txt等へ明示した。統合候補の全検査ログ・原PNG・親記録・原075領域・原成果ZIPは不変。自動承認拒否・アクセス迂回・認証変更はない。

## 契約と引渡し

配置済AGENTS・.scope-lock・素材規約・企画/体験仕様・原074/075依頼と報告・親記録を確認。不変の契約は既読075の原bytesとのhash比較も行った。配置済 `.agents/skills/rpg-maker-storyteller/SKILL.md` はゲーム実装を対象外とするため適用していない。元依頼にあるgodot/godot-game-verification/godot-dev-directorは配置されておらず、導入も利用済みとの主張もしていない。Library保存は今回取得した現行スキルとhelperに従う。AGENTSの一般的commit/push・親台帳記録より、今回の明示指示「親が正式保存・親記録は読取保持のみ」を優先した。

`task-075-main-integration.zip` は両親SHA、全差分一覧、候補全ファイルのblob/mode/bytes/SHA、4payload全文、両親の元ファイル、両親それぞれから候補treeへ適用できるpatch、最終原ログ・保持できた途中ログ/PNG/JSON/ハーネス/manifestを含む。パッチは独立indexへ適用し、候補treeの完全一致まで検証した。元075未保存worktreeの全ファイルと、074/075原成果ZIPは前後SHA一致。今回のZIPは別名で作り、原ZIPを上書きしていない。

Library confirmed ID・bytes・元ZIP SHAは最終引渡しに記載する。残件は親による候補検収・正式2親merge commit保存・全push/PR CI・main統合確認、および物理controller/利用者実機検証。旧coastalは既述の基点共通失敗として残り、初回baseline importの全文ログ欠損も証拠上の制限として残る。使用量への影響は不明。
