# 020 村の住人・施設の独立レビュー

## 作業前の計画

- 登録SHA：88c44d1557a4e4d883a67f855b5e108ff8402821。対象SHA：0a29a8ada3692d05ea4e552ad2e1233960e77830。開始基準：8694aad22ce8ceab74ac96c090360739c30d9983。
- 007依頼書・報告・141変更ファイルを照合し、原画と6人72コマ、外観・4室の実画像を見る。サービス、保存、占有、固定/最新回帰を対象SHAの一時checkoutで再実行し、変異による正負例も確認する。
- 対象SHAのGitHub CI全20ジョブと保護検査を直接照合し、親mainの文書追加を保つ統合方法を報告する。main統合と見た目の採否は代行しない。
- 変更は本報告書と020依頼書の状態行のみ。開始時の未コミット変更0件。開始workにupstreamはないがorigin/mainと同じb001615であり、既存の未push差分はない。追加委譲なし。

## 結論

**要修正（P2・2件）。** 対象SHAの本番実装に再現するサービス不具合は見つからず、既存CI全20ジョブも成功している。ただし、依頼項目3の全状態保持の検出と、項目4の正常な後続変更を拒否しないことに不足がある。以下は本番の故障の断定ではなく、新規検査に対する再現済みの指摘。修正と再レビュー後、人物の採否を依頼者へ確認してから親が統合する。

### P2-1 最新回帰が初期の受付座標を固定している

- 根拠：`tools/check_task007_services.gd:101`・110は、`--stage` の有無にかかわらず宿の話しかけ位置を `[12,5]` に固定する。`tools/capture_task007_services.gd:53`・54・72にも全員の初期話しかけ位置が残り、同じ撮影器を最新側でも使う。
- 再現：対象の一時コピーで `world/region2_village.json` の `oasis_innkeeper.cell` だけを `[12,3]` → `[11,3]` に変更。固定段階ではなく `godot --headless --path . --script res://tools/check_task007_services.gd` を実行すると、276件のうち「受付台越しに既存宿処理」1件と「倒れた人も含め全員HP/MP回復」4件がFAIL、終了1。
- 正常例である根拠：同じ検査の動的な `residents()` は床・占有・入口からの到達・会話を通過する。別の一時probeで床 `[11,3]` と客側 `[11,5]` の通行、上向き・距離2の本番会話、4人全員HP/MP回復をassertし、終了0・`REVIEW020_RELOCATION_VALID: floor=true counter_reach=2 party_recovered=4` を確認した。
- 影響：受付内の正常な1マス移動が、本番の回復不具合として最新CIを落とす。「最初のセルは完成時だけ」という007報告の世代分離と一致しない。撮影器にも同じ初期座標依存がある。
- 最小修正案：完成SHA側の全期待値を保持し、最新側の宿検査・撮影では対象NPCのIDから、現在の床・占有・reach・入口からの到達を検証した話しかけ位置を選ぶ。期待する回復・料金なし・拒否・全状態保持は独立したassertのまま残す。受付の正常移動を正例、届かない受付を負例にする。新しい監査階層は不要。

### P2-2 祠の「全状態」比較で攻略済み情報の消失を見逃す

- 根拠：`tools/check_task007_services.gd:141` と176は、村と従来祠の場所の差だけでなく `overworld` 辞書全体を `erase` してから比較している。`cleared`・transport・residents等も比較から外れる。通常撮影の祠実行後も侵蝕30だけをassertし、保存の一致は実行後の状態を基準にする。
- 再現：対象の一時コピーで `GameSession.release_monster_form()` の成功直前（`_reconcile_slots(actor)` の次）に次の1行を追加した。

```gdscript
if _state["overworld"]["node"]=="region2_village":_state["overworld"]["cleared"]=[]
```

- 検査の初期入力には `cleared=["first_boss","forest_tower_boss"]` が存在する。村で祠を利用したときだけ攻略済み情報を消す負例なのに、最新サービス検査は終了0・`TASK007_SERVICES_PASS: checks=280 residents=6`・failures空だった。全コードの書換えや検査器の改変はしていない。
- 影響：007が継続保証するとしている祠の全状態保持について、通常の小さな回帰を検出できない。現在の本番にはこの消去行はなく、当レビューも追加していない。
- 最小修正案：祠の成功前後で `overworld` 全体の不変を個別assertする。従来祠との横比較では、移動のため意図的に違わせた layer/node/room/cell など最小項目だけをそろえ、残りを比較する。上記の攻略済み情報消去を負例として既存の新規検査内で検出する。

## 実物の照合

- 007依頼書・002計画・007報告、素材規約、企画書、世界マップ仕様、素材台帳、対象の141変更ファイルを差分と実物で照合。追加コード・生成/検査/撮影器を読み、文書・出所・画像一覧と相互照合した。
- 本番コードの差は `at_purification_shrine()` に村室4を加える1行のみ。村データの差は6人のイベントのみで、006の地形・扉・接続は同じ。既存の宿回復・料金なし・祠の条件/低下量/忘却処理は不変。販売・商品・職業解放の新機能なし。
- `assets/registry.json` は既存1134項目の内容と相対順を保持し6項目を追加。パレットの追加・変更なし。既存tools、test、.scope-lock、project.godot、既存原画、第1地方/港の配置・素材に変更なし。CIは新規1ステップ追加で、既存ステップ・時間上限は不変。
- 原画のSHA-256は開始時と対象とも `495769b171adf3ba88fd5ba5fc4749dd67c0454d8606e248dad065d8645365c8`。出所記録は正面原画からの単純切り抜きではなく、別生成による横・背面・歩行補完と明記している。33枚の通常画像について `images.json` のSHA-256と実ファイルが全一致した。
- 完成固定点 `776ad944723d21c1e250a1ee5fd56d35da42cfed` は対象の祖先。以降の本番/新規toolsは同一で、CIの参照登録・報告/証拠更新が差分。固定側では当時の検査器の `--stage` を使い、最新側では範囲監査をせず継続検査を実行する構造は正しい。残る初期座標依存はP2-1。

## 画像所見（採否は依頼者）

原画の実ファイル、[全72コマ](../../verification/task-007/residents-walk.png)、[原画との比較](../../verification/task-007/residents-source-comparison.png)、[外観](../../verification/task-007/normal-operation-1.png)、[4室入室](../../verification/task-007/normal-operation-2.png)、[4室会話](../../verification/task-007/normal-operation-3.png)、[既存目標との比較](../../verification/task-007/target-comparison.png)を実際に開いた。宿・祠の手前壁画像も個別に確認した。

- 6人とも下/左/右/上の順、横顔と顔のない背面、3コマの足運びの違いを確認。輪郭・持ち物が隣のコマへはみ出す箇所は見当たらない。服色、柄杓・籠・壺・縄・杖・風車による識別は残る。低解像度への補完で原画から顔・細部の印象は変わるため、採用済みとはしない。
- 外観は屋根・葉の奥で人物が隠れ、門の下では見える。4室入口で操作人物の顔が前壁に消える状態は確認画像では見られない。宿のおかみ・2店の担当者は台の奥、操作人物は手前。長老は祠内の歩ける床にいる。店は会話のみ、祠は既存メニューの確認画面を使う。
- この所見は静止画と自動操作の確認。人間による歩行アニメーションの感触、人物の初回採否、ゲーム全体の長時間プレイを代行していない。

## 対象完全SHAのCI直接照合

GitHub CLIの `gh api` はForbiddenだったが、接続済みGitHubツールのGETでrun・全job・Godotログを直接取得できた。007報告に記載された旧検査HEADのCIとは区別し、ここでは全て `0a29a8ada3692d05ea4e552ad2e1233960e77830` に結び付く実行を確認した。

| job | 直接取得したjob | 結果 |
| --- | --- | --- |
+| 試遊前の通常戦闘・案内・画面・復帰検査 | [111548901804](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781415/job/111548901804) | completed / success |
| 素材検査 | [111548901834](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781415/job/111548901834) | completed / success |
| Godot・凍結受入テスト | [111548901863](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781415/job/111548901863) | completed / success |
| lifecycle-audit | [111548901728](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548901728) | completed / success |
| normal-input-and-rendering (fixed, restart-2) | [111548901852](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548901852) | completed / success |
| acceptance-and-regression (fixed) | [111548901855](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548901855) | completed / success |
| acceptance-and-regression (latest) | [111548901898](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548901898) | completed / success |
| normal-input-and-rendering (latest, details) | [111548901965](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548901965) | completed / success |
| normal-input-and-rendering (latest, restart-3) | [111548901969](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548901969) | completed / success |
| normal-input-and-rendering (fixed, restart-4) | [111548901998](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548901998) | completed / success |
| normal-input-and-rendering (latest, restart-4) | [111548902009](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902009) | completed / success |
| normal-input-and-rendering (latest, restart-1) | [111548902019](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902019) | completed / success |
| normal-input-and-rendering (latest, journey) | [111548902025](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902025) | completed / success |
| normal-input-and-rendering (latest, restart-2) | [111548902026](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902026) | completed / success |
| normal-input-and-rendering (fixed, details) | [111548902051](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902051) | completed / success |
| normal-input-and-rendering (fixed, journey) | [111548902056](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902056) | completed / success |
| normal-input-and-rendering (fixed, restart-0) | [111548902069](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902069) | completed / success |
| normal-input-and-rendering (fixed, restart-3) | [111548902074](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902074) | completed / success |
| normal-input-and-rendering (fixed, restart-1) | [111548902086](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902086) | completed / success |
| normal-input-and-rendering (latest, restart-0) | [111548902154](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37240781407/job/111548902154) | completed / success |

Godot jobは2026-10-04 22:38:30〜22:47:31 UTC、541秒（9分1秒）。同jobログからR-01〜R-08の全8件PASS、前後の保護26/26一致、`TASK007_PASS: completed=776ad944723d21c1e250a1ee5fd56d35da42cfed latest=0a29a8ada3692d05ea4e552ad2e1233960e77830` を直接照合した。固定/最新マトリクスの対象でない側のstepのskippedは既存条件分岐によるもので、job自体は全20件成功している。

## 独立した再実行と正負例

全実験は対象SHAの `/tmp/review020` とその一時コピーだけで行った。登録ブランチの本番・検査・画像・既存証拠は変更しない。GodotはCIと同じ公式ZIPを取得し、SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` 一致、`4.7.2.stable.official.ed1daf0bf` を確認。標準の4.6.3は成功証拠に使わず、XDG保存先は `/tmp` に隔離した。

| コマンド/対象 | 独立再実行の結果 |
| --- | --- |
| `godot --headless --editor --import --quit` | 終了0、SCRIPT ERROR / ERROR / WARNING / Parse Errorなし |
| `python tools/check_frozen_files.py` | 実行前後とも終了0、保護26/26一致 |
| `python tools/run_locked_checks.py` | 終了0、R-01〜R-08全8件PASS、tests_ran=True・parser_failed=False |
| `python tools/validate_assets.py --strict` | 終了0、画像1140・音15・字体2・パレット3、問題なし |
| `python tools/check_task007_assets.py --stage` | 終了0、6人72コマ・原画/生成元/出所・再生成・範囲検査PASS |
| 同検査 `--stage` なし | 終了0、最新6人72コマPASS |
| `godot --headless --path . --script res://tools/check_task007_services.gd -- --stage` | 終了0、299件・6人PASS |
| 同検査 `--stage` なし | 終了0、280件・6人PASS。会話の正向き/逆向き、宿4人回復/戦闘拒否、祠の境界/全8系統/拒否、6位置全状態保存/再開、6NPC占有保存の入口補正を実行 |
| `python tools/check_region2_village_regression.py --godot /tmp/review020-bin/godot` | 終了0、最新地形/接続/保存7630件、再開5別プロセス（10/27/38/52/44件）PASS |

通常撮影の初回通し実行は `xvfb-run` が環境になく途中終了したため成功扱いしない。Debianのxvfb・必要ライブラリ・Mesaを `/tmp` に展開してパスを指定し、同じ検査・同じ180秒上限・Vulkan/X11で通し再実行した。OS設定や既存検査は変更していない。


通し再実行 `python tools/check_task007.py --completed 776ad944723d21c1e250a1ee5fd56d35da42cfed --godot /tmp/review020-bin/godot` は終了0・`TASK007_PASS`。固定/最新の実行SHAとJSONを照合した。固定は素材・299サービス・外観49件/11枚・4室113件/22枚、最新は素材・280サービス・外観49件/11枚・4室113件/22枚がすべてPASS。各撮影はX11/Vulkan、警告・エラーなし。固定import56.281秒、固定の外観89.619秒/4室76.255秒、最新の外観85.608秒/4室69.106秒で、既存600秒/180秒上限内。通常キー・ボタンによる入村、両門、6会話、全室保存/再開、祠の確認/取消/実行を再実行した。

最新サービス検査への変異は、毎回対象のバイトへ戻し、検査コードとassertは変更せず本番コードまたは村データの小変更だけで行った。

| 一時変更 | 実測 | 判定 |
| --- | --- | --- |
| 無変更 | 280件PASS | 正例 |
| 番人の短い会話文だけ変更 | 280件PASS | 字句の初期値に最新を固定しない正常例 |
| 宿を受付内で `[11,3]` へ移動 | 終了1・5件FAIL | 正常例の誤拒否、P2-1 |
| 宿のreachを2→1 | 終了1・5件FAIL | 受付に届かない負例を検出 |
| `rest()` のMP回復を0に変更 | 終了1・5件FAIL | 回復欠落を検出 |
| 村の祠対象を室4→室3 | 終了1・61件FAIL | 場所/正負境界/全8系統の負例を検出 |
| 保存読込で位置補正を実行しない | 終了1・6件FAIL | NPC占有保存の補正欠落を検出 |
| 地形はそのままでNPC占有だけ無視 | 終了1・10件FAIL | 床/人物占有5件と旧保存補正5件で検出 |
| 村の祠成功時だけoverworld.clearedを消去 | 終了0・280件PASS | 負例の見逃し、P2-2 |
| 変異を元へ戻す | 終了0・280件PASS | 基準状態へ復帰 |

一時ログ/JSONを読んで上表へ転記した。依頼書が変更先を2文書だけに限定するため、新たな証拠フォルダ・恒久probe・検査階層は追加していない。P2指摘は上記の最小変更と既存コマンドで再現できる。

## main統合時の注意

- 開始時の親mainは `b001615`、提出前の再取得時は `9283844b9203f00bacb619a50c2f932086487f97`（STATUS追記）。対象との共通祖先は開始基準 `8694aad22ce8ceab74ac96c090360739c30d9983`。共通祖先→mainの差は `docs/STATUS.md` の更新と `docs/director-next-preparation.md`、`docs/tasks/014-record-four-lords.md`、`docs/tasks/015-record-monster-job-unlock.md` の追加4件だけ。007の担当外違反や削除対象ではない。
- `git merge-tree --write-tree origin/main 88c44d1557a4e4d883a67f855b5e108ff8402821` は終了0、競合なし。生成された仮想tree `8e53e4527bb148984d2552758f6f0168122e1abc` で上記4件のblobがmainと完全一致することを確認した。ブランチ移動・checkoutへのmerge・mainへのpushはしていない。
- 親は指摘修正と再レビュー、人物の採用確認後、**最新mainを起点に対象履歴を通常merge**する。対象ブランチ全体をmainの代わりに配置する、reset/force-pushする、旧STATUSで上書きする方法を使わない。統合前にmainを再取得し、4文書とその後の文書追加を保持したことを比較する。
- この020は007対象と登録SHAを祖先に持つ。020全体をmainへmergeすると007も入るため、指摘未解消の間にレビュー文書だけ反映したければ、親はまず依頼書のみ追加する登録コミット `88c44d1557a4e4d883a67f855b5e108ff8402821`、次に今回の2文書のレビューコミットをcherry-pickする。mainには020依頼書がまだないため、レビューコミットだけだと状態行変更がmodify/delete競合になる。履歴全体のmergeと、この2つの文書コミットのcherry-pickを区別する。
- 実際の統合後は素材importを先に行い、統合HEADの全CI・R-01〜R-08・保護照合・最新回帰を親が確認する。merge-tree成功や旧対象CIを統合後CIの代用にしない。

## 変更ファイルと未達

- `docs/tasks/020-review-village-services.md`：状態行のみ、報告済みへ。
- `docs/tasks/reports/020-review-village-services.md`：本レビュー。
- 指摘2件の修正は担当外のため行っていない。見た目の初回採否、main統合、007確認済み化、008発注は親/依頼者へ引き渡す。追加委譲なし。

提出前の `git diff --check` と依頼書の状態1行以外の不変確認は成功。レビュー差分は指定2文書だけ。本レビュー提出コミットの新規CIは、対象実装の上記20ジョブとは別であり、ここでは成功と宣言しない。
