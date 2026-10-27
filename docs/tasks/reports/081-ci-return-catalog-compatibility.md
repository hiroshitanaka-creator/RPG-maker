# 081 CIの帰還先一覧失敗：再現と互換修正案

現状：本番2ファイルの互換修正をcommit/push済み（最終本番ソース `e754b1e3fb38afd38456dac84068f264c5fb4f99`）。同じ本番ソースでローカル26コマンドが全PASS、追加の旧保存照会2判定を含む専用検証も40判定・失敗0。GitHub全CIはまだ終了しておらず、正式未完了。以下に原因・原失敗・修正・確定結果を残す。

## 原因と固定条件

失敗元headは `a04172a134971610e6760f7ff602451901130642`。CIと同じ `python tools/check_task009_assertion_map.py` は成功、`python tools/check_region2_village_regression.py --commit "$GITHUB_SHA" --godot ../godot` は7630判定中1件でexit1。5つのrestartは全PASS。原出力・runtime JSON・保存は `docs/verification/task-081-ci-fix/before*` に保持。

失敗assertionは既存 `tools/check_region2_village_regression.gd:372` の `FirstRegionTravel.destinations()==contract["destinations"]`（既存帰還先の全件と村の船先）。既存の無引数APIの閉じた5件を081で直接6件へ拡張したことが原因。世界2セルや新dockの静的到達性を理由にこの失敗を無視しない。lifecycleの正例も同じ継続検査を呼ぶため、無関係なNPC正例までこの1件で失敗する。

既存5件のID・順序・入口・船先・MP条件はすべて保持する。009のassertion分類・固定fixture・最新回帰・故障注入・CI・保護・契約・上限は変更しない。

## 先に示す両立案（互換APIの追加）

1. `FirstRegionTravel.destinations()` は既存の無引数APIとして5件・全フィールド・順序を元通り維持する。新港をvisitedに含む保存を渡していない呼出しでも結果は同じで、検査プロセス・環境変数・呼出元を判別しない。
2. 保存状態を明示的に受け取る `destinations_for(saved)` を追加する。既存5件はそのまま、新港を実際に訪問済みの保存では採用済み新港の帰還先だけを追加する。これは従来UIの「訪問済みだけを表示」という既存規則を使う本番用の拡張であり、新フラグ・新規則・第2の転移機能は作らない。
3. 本番の帰還画面と帰還実行は同じ `destinations_for(saved)` を使う。新港の通常メニュー帰還、MP2、生存者条件、人物/船の着地、未訪問・未知先の拒否を維持する。既存の無引数APIを使う既存クライアント/回帰は完全互換。
4. 専用の非保護検証で、無引数の5件完全一致（新港訪問の前後も一致）、旧保存時の候補不変、新港訪問済み時の拡張候補、未訪問拒否、通常UIの新港帰還を確認する。既存009検証・lifecycle故障注入は無変更のまま全て再実行する。

新港を無効化したり、既存検査からだけ新港を隠したりする修正ではない。既存APIの契約を維持し、本番の保存文脈を扱う互換拡張として接続する。固定条件そのものを変更する段階移行はこの案では不要と判断する。正式な契約変更が必要だと分かった場合は実装で回避せず具体条件を報告する。

## 変更予定の全ソースと証拠

- scripts/world/first_region_travel.gd（既存APIを復元し文脈APIを追加、帰還実行の参照先を変更）
- scripts/ui/first_region_screen.gd（帰還UIの参照先を同じ文脈APIへ変更）
- tools/check_task081_return_catalog.gd と .uid（追加の互換・新港の正負例）
- docs/tasks/reports/081-ci-return-catalog-compatibility.md、本体081報告の最新状態
- docs/verification/task-081-ci-fix/ の再現・修正後・原コマンド・全差分/SHA・画像

海域2セル・dock・原画・5室・保存形式・既存検査・保護・CI・親台帳は変更予定なし。変更が必要になった場合は先に追記する。調査・実装・証拠の既存commitは保持し、通常commit/pushで進める。

## 修正後の最初の確認

`destinations()`の既存5件完全一致を復元し、`destinations_for(saved)`を本番帰還画面と帰還実行の両方で使用した。追加検証16件で、旧保存の候補不変、新港訪問後の6件、帰還MP2・入口前・船の復帰、未訪問/未知先拒否、保存照会の状態不変を確認した。検査や環境変数で結果を出し分ける処理はない。

修正前lifecycleも別コピーで再現し、2つの正例が帰還一覧1件で失敗した。ローカル環境にはさらにMesa Vulkanドライバがなく、撮影の実判定132・画像28枚は成功したがOpenGLへのfallbackエラーを既存判定器が正しくFAILにした。この環境上の失敗も保持し、実際のMesa Vulkanを作業領域へ導入して同じ既存コマンドを実行する。エラー行の無視やCIの変更はしない。

## 親追加検収への対応

訪問済み→未訪問→訪問済みの連続照会、現在地が始まりの村の外でも新港が候補になることと実帰還、未知人物/未知先/未訪問/未習得/MP不足/戦闘不能/戦闘中の7負例の全状態保持を追加した。返却配列と内部辞書を変更する追加検証は、浅い参照では既存/新港キャッシュの2件で意図どおり失敗した。文脈APIの戻り配列・辞書をdeep duplicateする2行の修正後、全38判定・失敗0になった。照会で保存やキャッシュを変更せず、無引数APIの既存5件は訪問前後とも完全一致する。

## 最終ローカル結果と証拠

最終本番ソースは `e754b1e3fb38afd38456dac84068f264c5fb4f99`。今回の本番修正は `scripts/world/first_region_travel.gd` と `scripts/ui/first_region_screen.gd` の2ファイル。文脈APIは戻り配列・各辞書を複製し、キャッシュへappendしない。照会はsnapshotから読むだけで、visitedに基づいて新港を追加する。旧5件の全フィールド・順序は無引数APIでも文脈APIの先頭でも不変。本番UIとreturn_toは同じAPIを使い、新港を検査だけで隠す分岐はない。

| 確定した検査 | 原結果 |
| --- | --- |
| Godot 4.7.2 editor import | exit0、エラー/警告なし |
| 009 assertion map | 135 sites・unclassified0、exit0 |
| 009 最新回帰のCI原コマンド | 7630判定とrestart0〜4、全PASS/exit0 |
| 既存lifecycle故障注入 | 13ケース全PASS。正例exit0、異常SHA・誤接続・不正保存受理等の負例は期待したassertionでexit1。timeout/parse errorなし |
| 既存通常入力/描画7系統 | journey132判定/28画像、details34/6画像、restart0〜4は各17/3画像、全PASS/exit0 |
| R-01〜R-08 | 原verify・原judgeで全PASS/exit0。R-08は25テスト/3046 assertions、failed/pending/invalidなし |
| 081 本番API境界 | 2677判定・失敗0 |
| 081 原画/出所/変換/地形/保全 | 1235判定・失敗0、素材strictもexit0 |
| 081 通常入力の新港到着/石門/帰還/再出航 | 40判定・失敗0。220歩・334入力、元の180秒/600歩/3000入力の範囲内 |
| 帰還候補と旧保存の追加検収 | 40判定・失敗0。travel項目のない旧保存も5件のまま、travel/visitedを補完しない |
| check_frozen_files.py | 前後26/26一致、同じ原ログSHA |

元headの原失敗は `before*`、追加検証の赤→緑は `catalog-*-before/red/after.log`、確定した26コマンドのUTC・実コマンド・上限・終了値・原ログSHAは [after/execution.json](../../verification/task-081-ci-fix/after/execution.json)。各原ログは同じフォルダの `.log.gz`。旧保存2判定追加後の専用検証は [catalog-legacy-final-execution.json](../../verification/task-081-ci-fix/catalog-legacy-final-execution.json) と [catalog-checks.json](../../verification/task-081-ci-fix/catalog-checks.json)。26コマンド後の差分はこの専用検証2判定だけで、本番コードは不変。

実行環境が一時unavailableとなり、再接続時にはsession95531と元プロセスが存在しなかった。restart3までの原記録を照合し、未確定のrestart4以降3コマンドだけを同じ上限で実行した。中断時の残存資料と不確定範囲は `interruption.json` に明示し、残存資料を成功根拠には使わない。再実行の3コマンドは終了0と最終JSONを確認済み。オーケストレーター原文は `runner.py.txt` と `resume-runner.py.txt`。

実Vulkan環境を作業領域へ展開して描画を検証した。最初のドライバ不足/fallback失敗は保持し、既存検査のエラー拒否は変更していない。公式Debian依存のURL/bytes/SHAは `local-render-dependency.json`、実Vulkan起動原ログは `vulkan-smoke.log`。システム設定・権限・GitHub認証は変更していない。

検証が上書きした既存記録76ファイルは、新しい専用証拠へ原bytesを保全した後、HEADの元bytesへ戻した。新生成の担当外41ファイルも原bytesを保存して専用証拠へ移し、元の未追跡uid2件には触れていない。原生成物と復元SHAは `generated-record-restoration.json`。既存test・検査・保護・CI・契約・時間上限・親台帳2件は今回差分0。原画と採用5室のPNGも変更していない。

- [新港の通常到着](../../verification/task-081-ci-fix/after/081-newport-input/arrival-pier.png)
- [通常メニュー帰還後の入口前](../../verification/task-081-ci-fix/after/081-newport-input/arrival-spell-outside.png)
- [5室の入口・室内・復帰（先行本編入力の原証拠）](../../verification/task-081-implementation/five-rooms-contact-sheet-diagnostic.png)

5室自体・dock・世界2セル・入口座標・保存形式は今回変更せず、5室の本番API往復/保存境界を再検証した。全床巡回・扉別反復・通常保存再読込・前後遮蔽の先行本編入力証拠は元の081報告に保持し、今回の最新26コマンドと混同しない。

## 残りと戻し方

GitHub全CIの終了確認は未達。途中取得した原API応答は `github-pr-*-e754-*.json`。GitHubの実ジョブに未終了があるため、ローカル成功で正式完了を代用しない。PR61は親担当のdraftのまま、PR/main操作は行っていない。main取込後のeditor importも親担当として未実行。

作品仕様・保護変更・契約移行の判断は不要。今回の判断は保存文脈APIの追加という可逆の技術判断。戻す場合は本番の2つの修正commit `a560df4e9724cde341f66ade53bb0a2f78917261` / `e754b1e3fb38afd38456dac84068f264c5fb4f99` の該当差分を通常revertし、追加検証を合わせて戻す。ただし元の一覧不具合が再発するため、戻した状態を検収済みとは扱わない。今回revert・削除・履歴改変は実行していない。
