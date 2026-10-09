# 059 保存QA終端記録・限定子孫監督の報告

**未達を含む提出。F5の修正・専用検証と、保存全体の受入を分ける。F1時間未達、F4実ENOSPC/nested別volume NOT_RUNは継続。** 最終文書SHAの全CI終了とclean/未pushは最終応答で確定する。自身のSHAを文書へ再帰固定しない。

## 計画・登録・範囲

登録a6022f1e4a7689440928efe65db444336e9128e4、基点579ca1f463aaf9e93275039a59cf9d1ffb86adb5、指定branch codex/task-059-fix-save-qa-finalization。開始dirtyなし・未pushなし。AGENTS.md、059/057依頼、伝言板、057/058報告全文と反例、専用driver/helpers/workflow、素材規約・職業/魔物化の企画・台帳構造・優先仕様、040保存計画、原053/055/057固定証拠を確認。checkout/workspaceに適用可能な追加AGENTS/.agents/skillsは存在しない。追加委譲・別環境切替なし。

最小変更と全assertion世代対応は[実装前plan](../../verification/task059-save-qa-finalization/plan.md)に先に記録した。完成コードは8282248971482790a62485b9b510684e4469e2c7。旧057 3cf4b6c、055 0a44409c、053 e003b126の完全SHA・inventory・期待・契約・旧scopeは変更していない。

## 修正内容

受付時に一意request ID・予定argv・予定record先を持つ。Suite.runのqueue前config経路とrun_restart_batchのconfig/env/capture準備、ProcessCaptureのlog.open/record保存を終端化する。未起動のPID/実argv/子log/exit/開始時刻はNone、予定情報と例外理由だけを残す。共有batchは一意原recordのrequest_idsと各root投影へ対応づける。

closeを直列化し、受付停止・future終了・worker終了、全受付ID/予定先/終端record/共有batch/root投影の対応、所有capture状態を独立照合する。記録不在をprocess不在の証明にしない。欠落/壊れJSON/ID違い/保存失敗はrecovery_complete=false、Suite/mainの非0へ伝播する。書けない先と理由・保持可能な終端情報は上位queue inventoryへ残す。回収完了と取引成功は別で、失敗要求を完了件数へ足さない。JSONは同directoryの一時fileからatomic replaceし、記録書込みの競合で半JSONを読ませない。

Linuxは自分が作った専用sessionとgroup、exec前から渡す継承ownership tokenで入れ子も監督する。所属/start_ticksを再確認したpidfdだけへsignalを送る。session/PID番号だけで他processを終了せず、所有token不明なら終了を拒否し未確認にする。Windowsは専用Job Object、suspended作成→所属確定→resumeで所属前の孫起動raceを防ぎ、breakawayを許さない。直接子waitと所属子孫の実行停止確認は別に記録する。

全停止/確認は元deadline残量内。期限0・設定失敗・所属不明・保存失敗を回収成功へ補完しない。Linux orphan zombieは実行/handle保持終了としてstateを記録し、他の親が持つwait責務の回収まで保証しない。OS停止、外部から監督者自体を強制終了した場合、QA子が明示的に所有環境を破棄/監督から離脱する場合まで完全保存を保証しない。global/name kill・他job/process終了・OS設定/権限変更なし。

## CIの世代分離とscope

専用workflowの元fixed055/latest、Windows/Linux、transaction/primitivesを保持し、fixed057を別jobへ追加した。当時のcheckout3cf4b6cから当時のprocess_capture・12検証・scope057正負・6seed対照を実行する。旧code-fixed-shaが当時b4ee1eaを指すため、別checkoutの検査引数を完全SHA3cf4b6cへ明示し、固定文書自体は変更しない。最新側は既存12検証・059追加21検証・scope059・基点058反例・6seed対照。sample計測は全取引受入と別。

親の提出前確認を受け、scope059の後続文書許可を059依頼書状態行・059報告・059証拠だけへ限定した。最新担当指示に従い、decision-logの後続追記も拒否する。10正負例を実Git tree/commit/子exitで確認。旧057証拠、058過去報告、担当外文書、依頼本文変更、decision-log書換えはexit1。旧scope057/055 prefixを広げていない。原2259パスのblob不変と44archive/317273全member照合もscopeとは独立して実行した。最終SHAについても全許可パスと原不変を再照合する。

## Linuxの実行・照合・未実施

| 実行/証拠 | 実秒・exit・結果 |
|---|---|
| 058基点reproduce058.py --checkout /tmp/qa059/before --output /tmp/qa059/repro-linux | config directoryで実IsADirectoryError、execution0/recovery_complete=true、外側0.5秒後の孫heartbeat継続を再現。専用releaseで後始末 |
| 既存test_capture057.py --output /tmp/qa059/capture057-final21 | exit0、12件全成功、実子30秒を含む。元検証byte不変 |
| test_capture059.py（run_command経由、/tmp/qa059/capture059-ownership-final） | exit0、21件全成功、入れ子監督も実行。縮尺0.5秒を実174/180秒検査とはしない |
| scope059.py --code-sha 8282248… --source-sha 8282248… --self-test | exit0、正例0・9負例各1。原argv/秒/exitはscope059-current-policy.json |
| run_ci.py --source-sha 9d4d361… --profile latest（隔離/tmp/qa059/full） | transaction子175.014917秒/exit1、suite174.389923秒、118/1642。294受付、live worker0、未回収0、全終端照合true。原172/2178・97killは未達 |
| 同source/primitives-only | wrapper exit0、native-extra40件90.710秒、binary7件6.693秒、提出済みSO実ロード。手元rebuildなし |
| 原正常証拠への現validator16伝播・055 scope2例 | exit0、control0・15負例各1、scope0/1。現在全取引成功と別 |
| R01〜R08（隔離7f4c608、run_locked_checks.py） | 192.037秒/exit0、tests_ran=true/parser_failed=false、全PASS |
| 装備/S1/S2/旧比較142/10全文 | .774/24.790/15.725/2.389秒、各exit0、正常logの警告/エラーなし |
| 素材strict、保護26前後 | 9.070秒/.069秒/.069秒、各exit0、26/26不変 |
| 原053固定 | 今回ローカル全取引再実行なし。固定/最新の既存CIと原archive全member照合を分ける |
| F4実ENOSPC・nested別volume | NOT_RUN。mount/VHD/ACL/共有disk充填/新環境起動なし |

手元R8と全取引の一部は同hostで重なったため、wallをOS性能差や改善率の証明にしない。正常sampleのbatch一意、inclusive/exclusive、wall/並行累積の既存計測はbyte不変。case/assertion本文・元172/2178・97kill・16伝播・保護26・全予算/worker/batchを保持し、skip/continue-on-error/警告無視/期待弱化/ケース削減/時間延長なし。

## 両OS CIと取得限界

初回HEAD9d4d361のfixed057 Windows原archiveを復元し、宣言raw hash/sizeと3884memberを照合。12捕捉・scope3例成功、全取引69/1035・174.407秒未達、診断のGet-CimInstanceが既存30秒でtimeout。この当時固定側の失敗を059の監督不備や成功へ混同しない。初回latestの原checkout位置が証拠archive内に入る点を修正し、以後は原checkoutをarchiveの外に分離した。

現在の059両OS原証拠・全jobの終了結果は取得中。未取得の原bytesを確認済みとはしない。最終更新で実結果と取得不能の理由を記録する。

## 永続原証拠・変更一覧

[証拠README](../../verification/task059-save-qa-finalization/README.md)、[archive完全hash/索引](../../verification/task059-save-qa-finalization/archives.json)、code inventory・原不変inventory・旧archive監査・scope正負が入口。原log/実argv/秒/exit・各JSON・raw archive/member hashを保存する。decoded job UTF-8 textのhash、raw tar.gz hash、Git blob、API ZIP digestは区別する。自身の最終SHAは応答で確定。

変更はtools/check_equipment_save_transaction_platform.py、専用process_capture.py/run_ci.py/diagnostic_ci057.py、新process_tree059/process_exec059/diagnostic_fixed057/reproduce058/scope059/test_capture059/tree_fixture059、専用workflowの世代配線、059証拠/報告/依頼状態行、decision-log今回末尾のみ。本番scripts、native/addons、保護26/R8、旧scope/期待/契約/固定SHA/原証拠、原画/data、他workflow、AGENTS、過去報告を変更していない。

## 残件

F1の全取引時間未達とF4実測不足は別の残件であり、今回承認済みのQA修正のために本番codec・検査時間・OS設定へ範囲を広げない。必要な保留はF1/F4および取得できないCI原物のみ。新PR・main/PR33反映・merge・force・削除・追加委譲なし。

## 最新担当分担の適用

最新の明示指示に従い、以後docs/decision-log.mdとdocs/tasks/README.mdは更新しない。既存commit d7ecd229baa2ce0cc56c65e9b474abca0e2595dcのdecision-log 126行に、受付ID/専用Linux session・Windows Job/057世代分離/全予算と本番不変/通常revertという059判断の1項目が保存済み。未コミット追記は0。既存項目は削除も履歴変更もせず保持する。以後の判断/検証は本059報告へ記載し、ルッカが取り込み後に記録とタスク表を更新する。scope059も後続decision-log書換え/追記の実exit1を確認する。
