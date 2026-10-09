# 057 保存QAログ保持・時間内訳の報告

## 作業前の計画

開始HEADは878c2316a4c9e72b253f7df001b6c6438ef7cb6d、基点849d02bd2ea4dd44298eef225fe9a12927858d1b。開始dirty・指定branch未pushは0。追加AGENTSとcheckout/workspaceの関連SKILL.mdは存在しない。追加委譲なし。

最小変更は専用platform driver、fixture内process記録/helper・057 scope checker・計測wrapper・機械検証、および専用workflowの診断/証拠step。055 scope許可prefix、固定SHA/原期待/契約を変更しない。

F5は出力後に待機する専用子を使い、実30秒timeout・174秒残量枯渇・外180秒経路・並行worker例外・親例外・正常/異常exitを区別する。stdout/stderrを起動時からfileへ保持し、PID/argv/UTC/monotonic/exit/timeout/deadline/kill/waitをfinallyに保存。queue/batch一意IDとroot完了を記録し、終了時に受付停止・未完future拒否・子kill/wait・worker joinを元180秒内で行う。回収不能は未回収の理由として残す。

Windows/Linuxは同じ専用CIの最新profileへ診断を追加し、既存8jobと固定版checkout/command/予算を保持する。実関数へ同一引数を渡すGDScript wrapperでseed6種、起動/依存、plan/verify、plan内部各段階、native I/Oを計測し、同seedの計測なし対照と比較。queue/snapshotは全取引側で観測する。診断sampleは172/2178・97kill受入と区別。原log/raw archive・member hash/索引を新057証拠へ保存しGit blob/API artifact digestと区別する。

現在は作業中。実結果を追記する。
