# 057 保存検査のログ欠落修正と時間内訳計測

- 状態：未着手
- 担当：Codex GPT-6.1 Sol／High
- 依頼日：2026-10-09 JST
- 前提：なし（055の受入成功を前提にする後続実装ではなく、056で確認した不備の修正・診断）。055/056は報告済み、055受入は差し戻し。
- 基点：056提出 849d02bd2ea4dd44298eef225fe9a12927858d1b
- ブランチ：codex/task-057-save-qa-diagnostics
- 承認：2026-10-09 19:08 JST、依頼者は提示済みA「専用検査のログ欠落を直し、Windows・Linuxで再検証の時間内訳を測る」/B「先に下書き」の選択について「どっちでもいい」と回答。親は推奨Aを選択した。場所はRPG-makerの保存済みクラウド、Sol／High、使用量への影響は不明と提示済み。
- 指揮・受入確認：ルッカ。実装修正・専用QA：上記Codex。通常UI・実ユーザー保存・新しいゲーム規則は対象外。

## 目的と背景
056のF5（timeout時の子ログ・終了証拠の欠落）を直し、F1（既存時間予算内に全取引検査が終了しない）の原因をWindows/Linuxで同条件の計測により切り分ける。今回は診断とログ保持の段階であり、既存codecの最適化や時間予算変更の許可ではない。
読むもの：AGENTS.md、docs/tasks/README.md、055依頼・報告、056依頼・報告全文、053原証拠・040保存統合計画、対象platform runner/workflow、関連する.agents/skillsのSKILL.md。存在しない資料を読んだとしない。
055 c469ae1の初回47ジョブは43成功4失敗。056最終の47ジョブも43成功4失敗だが失敗するLinux fixed/latestは同一ではない。現SHA・run・platform・profileを必ず区別する。

## 担当の場所
- tools/fixtures/equipment-save-transaction-platform/ 内の専用Python runner・証拠収集・診断helper、および追加の計測専用GDScript。既存のfixture入力・期待値・assertion・成功条件は変更しない。
- tools/check_equipment_save_transaction_platform.py（Suite.run／run_restart_batch／RestartBatch のF5ログ保持・回収修正と計測。既存assertion・判定は保持）。
- .github/workflows/equipment-transaction-platform.yml（同じWindows/Linux CI内の診断・証拠保存の追加だけ。既存job・コマンド・予算・必須判定を保持）。
- 新 docs/verification/task057-save-qa-diagnostics/（再現手順・原log・計測JSON・hash/索引など）
- 本依頼書の状態行、docs/tasks/reports/057-save-qa-diagnostics.md、docs/decision-log.md の今回追記だけ。

変えてはいけない場所：AGENTS.md、.scope-lock/**、test/**、保護26件・R-01〜R-08、既存S1/S2 codec/validator、scripts/ 以下の本番コード、native/・addons/配布物、旧053のrunner/wrapper/probe/fixture/証拠、過去の報告・原画・ゲームdata、他workflow・通常入口。古い検査を変更して緑にしない。必要なら具体パス・差分案を報告し、その変更だけ承認待ちとする。

## 作業内容
1. 開始時のdirty/未push、取得基点、対象パスと固定版を確認。専用QA内でF5を再現し、子30秒timeout・suite内側174秒締切・外側180秒・並行workerの例外を区別する。
2. 例外・timeout・強制終了・親の通常終了でもstdout/stderrと終了記録を確実に保持する。PID、argv、開始/終了時刻、exitまたは未取得の理由、timeout種別、deadline残量、kill/waitの成否を残す。出力の先行ファイル記録やfinallyを用いるなど、手段は担当が選ぶ。終了できなかったprocessを回収済みとしない。
3. queue投入・worker開始・batch ID・各root完了を記録し、共有batchを二重計上しない。未完future/workerの回収と証拠確定も元の予算内で行う。余裕不足なら失敗を維持して残せた証拠・欠落理由を明示する。
4. 正常/timeout/子異常終了/親例外/並行処理などの機械検証を追加。欠落・空・改変・manifest再hash等が成功にならない既存16伝播＋scope正負を維持する。追加ログの存在だけで取引成功と判定しない。
5. WindowsとLinuxをそれぞれ実測する。seed6種、Godot起動/依存構築、queue待ち、plan/verify、T.plan内decode/migration/prepare_candidate/encode_candidate、native I/O、snapshotの時刻と回数を測り、inclusive/exclusiveとwall-time/累積並行時間を分ける。既存本番ソースを変更せず、同じ引数をsuperまたは実関数へ渡す専用wrapper等で観測する。検証省略・cache復活は禁止。
6. 計測有無の対照と環境・CPU/OS/FS・worker/batch・Godot版・実SHAを記録する。Windows2worker/8case、Linux4/16など現在条件を勝手に変更しない。Linux約99%という056の限定観測をWindowsへ流用しない。起動/import/buildを取引予算へ混ぜない。元172/2178・97killの通し検査と診断sampleの結果を分ける。
7. 元の固定053 e003b126de6695fa131e07a3db14c3011fb74f2e と固定055 0a44409c99b06569b9e6088ffeb46c2238c821faを当時のコード・期待・検査器で保持。最新HEADの回帰を別に行う。新しい修正コードは完全SHAを確定して記録し、後続文書追加を誤拒否しない正例と担当外拒否負例を追加する。固定版失敗を隠さない。既存 code-fixed-sha.txt／inventory、expectations.json、recovery-phases.json、contract.md は変更しない。run_ci.pyの既存055 scope()はlatestでも055固定SHAを検査するため、許可prefixを拡大しない。057差分は基点849d02bから別の追加checkerで限定確認する。
8. 計測で分かった原因と、既存codec等の変更が必要な場合の最小案を提示するだけに留める。F4実ENOSPC・nested別volumeはNOT_RUNのまま。mount/VHD/ACL/OS設定、新環境の起動、共有disk充填を行わない。

## 検査・守ること
- 全体180秒、内側174秒、子30秒、import600秒、各job15分を延ばさない。既存各コマンド予算も維持。skip、continue-on-error、warning無視、期待弱化、検査削除、ケース削減は禁止。
- 原172ケース/2178条件/97kill、native primitive・配布物、16伝播・scope正負、S1/S2・装備・旧比較142/10全文、R-01〜R-08・保護26前後を実行/照合し、実行できなかったものは具体的に記録する。診断成功は全取引成功の代替ではない。
- Godot4.7.2、専用テストデータのみ。正常対照の警告拒否と負例の予期したエラーを区別。
- 原archive/過去証拠を上書きせず、Git blobとraw SHA-256、GitHub artifact digestを区別する。CI raw log/artifactを取得できないときは未確認の対象と理由を明記しアクセス制限を迂回しない。
- 新PR、PR33取込み、main push/merge、force、削除、追加委譲は禁止。指揮役が後で受入を行う。
- 専用workflowの追加診断も元のjob予算内に収める。収まらなければ未達として報告し、受入検査を診断sampleで置き換えない。

## 作業前の計画
最小変更パス、F5再現ケース、証拠の保存方法、Windows/Linuxの取得経路と計測の対照、タイムアウト時の回収方法を報告書の冒頭に記す。担当外変更が必要なら独立作業を続け、具体的な最小追加範囲を親へ報告する。

## 自己点検と報告
docs/tasks/reports/057-save-qa-diagnostics.md に、変更一覧、再現前/修正後、実argv・秒数・exit、各OS/profile/SHA別の成功/失敗/未実施、永続証拠と完全hash、F1/F4/F5の残件、次の最小案を書く。物語の詳細は不要。
指定branchへcommit/pushし、自身の状態を報告済みにする。最終SHAの全workflow/job終了を確認し、clean/未pushの有無を返す。時間未達が残る場合はAGENTSの意味で完了や全成功と呼ばず「未達を含む提出」とする。

## 完了の条件
F5の正負検証とWindows/Linuxの再現可能な計測資料が揃い、原検査・予算・本番bytesが維持され、変更が指定branchへ保存されていること。全CIが緑でなければ受入完了ではない。F1/F4を含む保存機能全体の受入は別判断であり、今回の診断終了をS3完成と扱わない。
