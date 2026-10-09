# 059 実装前計画・世代対応

登録 a6022f1e4a7689440928efe65db444336e9128e4、基点579ca1f463aaf9e93275039a59cf9d1ffb86adb5。開始dirtyなし・指定branchへの未pushなし。追加委譲なし。checkoutに追加AGENTS.mdと.agents/skillsは存在しない。

| 条件 | 固定側 | 最新059側 |
|---|---|---|
| 原053全172/2178・97kill・14伝播・scope | e003b126de6695fa131e07a3db14c3011fb74f2eを既存workflowで保持 | 原053最新回帰を既存workflowで保持 |
| 055固有受入・primitive・配布物・16伝播・scope | 0a44409c99b06569b9e6088ffeb46c2238c821fa、既存fixed055 job | 既存latest job。055 scopeは055固定のみ、059範囲の代用にしない |
| 057コード不変・scope正負・固定証拠 | 3cf4b6c293f6796220b43cf566f8eb792c3932ecを専用fixed057 jobで当時のコード・検査・期待として再実行 | 057完成→059不変を適用しない。scope059で基点→059完成と後続文書追加を検査 |
| 057の12捕捉検証・6seed off/on対照 | fixed057 jobで当時の検査を全保持 | 12検証の継続回帰＋059追加正負検証。sampleは全取引成功とは分離 |
| F5-a起動前例外、F5-b外側kill | 基点の反例を専用fixtureで保存 | 全受付ID・予定record先と実record照合、専用所有tree監督を検証 |
| R01〜08・保護26・装備・S1/S2・旧142/10全文 | 元検査/期待のbytes不変 | 既存CIと専用ローカル回帰で実行・前後照合 |

最小変更はdriver/process_capture.py/run_ci.py、専用監督helperと059 fixture/scope/診断、diagnostic_ci057.pyと専用workflowの世代配線、059文書だけ。旧scope057/055許可prefix・固定SHA/inventory/期待/契約・本番/native/addons/保護ファイルは不変。

F5-aは受付時ID・予定argv/record先を所有し、queue前/config/env/capture/log/record失敗も終端化する。保存失敗は上位inventoryに記録し不完全とする。closeを直列化し、全受付・終端ID・共有batch・worker/future・直接子/子孫を照合する。記録の不存在からprocess不在を推論しない。

F5-bはLinux専用session/group（入れ子は同じ外側sessionに留める）、Windows専用Job Objectと起動時suspend→所属→resumeを使う。PID/name全体killや所有不明processの終了は行わない。直接子waitと所属子孫の停止確認を分け、174/180/30秒の残量内のみ確認する。残量0・設定失敗・記録失敗は未確認。OS停止や監督者自身の外部強制終了まで完全保存を保証しない。

両OSの取得は既存専用CI。新環境起動・mount/VHD/ACL/OS設定変更・共有disk充填なし。全180/174/30/600秒、15分、worker/batch、全期待を維持。縮尺fixtureは実174/180秒検査と呼ばず、F1時間未達/F4実ENOSPC・nested別volume NOT_RUNを別に報告する。
