# 059 保存QA終端記録・限定子孫監督の報告

**未達を含む提出。F5の修正・専用検証と、保存全体の受入を分ける。F1時間未達、F4実ENOSPC/nested別volume NOT_RUNは継続。** 最終文書SHAの全CI終了とclean/未pushは最終応答で確定する。自身のSHAを文書へ再帰固定しない。

## 351最終Linux診断失敗への継続対応

**現在の固定コードは41a34ea33fe184274e6722c88cdbca2a7ffd3708。元351ec408のLinux job113978145324の失敗原因は未確認のまま保持する。** [元提出の全51job](../../verification/task059-save-qa-finalization/submission351-ci.json)は45成功・6失敗。Linux最新は取引本体step成功、step16診断失敗。log取得はTransport closed、artifact11640835179は1,254,940,272bytesで取得ツールの536,870,912bytes上限を超えた。親も同じ取得不能を確認した。巨大artifactの再取得やアクセス拒否の迂回は行わない。

同じ既存環境で、元351の実装12ファイルが固定55のhashと一致することを確認し、元5診断を180/30/180/30/180秒で再実行した。既存12（33.281173秒）、scope10正負（2.589834秒）、追加27（7.599010秒）、058反例（0.772162秒）、6seed/12sample（37.315539秒）は全exit0、全外側監督stopped=true。容量を圧迫する複製を避け、clean/SHA確認済みの既存058 checkoutを再利用した点はCIの準備操作と異なる。これは元job失敗の原因特定や再現成功ではない。初回importはexit0でもERRORを検出したため成功扱いせず原logを保持し、既存run_ciと同じ専用processのprofile環境でimportをやり直し、警告/ERRORなしと終了を確認した。OS設定・依存導入・別環境は変更していない。

調査で別の実反例を確認した。旧診断runnerの058 checkout準備先に既存directoryがあると、Git実exit128で診断runnerはexit1となり、execution.jsonも準備process記録も欠落した。sentinelは不変。これが元job原因だったとは断定しない。41a34eaでは準備前にinventoryを保存し、同じ30秒上限の専用ProcessCaptureでGitの所有子孫も監督する。準備の実exit/保存失敗/未確認を上位に残し、5診断は失敗後も全て試行する。準備失敗の実再検証はGit128、全5試行、基点診断1、独立した既存12/scope10/追加27/6seedは0となり、全体FAILを維持した。

既存全artifactは維持し、新helper diagnostic_evidence059.pyと専用workflowでtask059だけのZIP、全regular fileのhash索引、空directory/リンクtarget記録、失敗case/実exit/秒/予算を持つsummaryを別artifactへ保存する。失敗理由はGitHub annotationにも出す。既存証拠・一時checkoutは削除せず、既存archive出力/検査/予算/旧055/057配線を変えない。実成功・過去実失敗・証拠欠落の3入力は期待exit0/1/1、ZIP全member bytes一致。新準備失敗の633fileも一致し、ZIPは2,975,382bytes。小さい証拠を成功へ補完する仕組みではない。

肥大については、既存upload-artifactがnative-evidence全体を含むため、Linuxの旧053 checkoutも含むことを確認した。手元の同経路legacy053は約1.4GB、binary検査の必要なmini project群は約73MBだった。元1.25GB ZIPの全bytesは未取得なので、その全内訳を照合したとはしない。新しい小さい診断artifactは旧checkoutやbinary mini projectの外に保存する。

原証拠はresume351-code55-diagnostic、setup-diagnostic-before41/after41、compact-diagnostic-validation41（実行helper hashあり）。compact-diagnostic-validationはsetup欄追加前の途中helperで、最終41の証明と混ぜない。旧固定55のcode inventory/scope証拠は別名で保持した。新固定13ファイル・scope10正負を確認。coreのprocess_capture/process_tree/driver/既存12・追加27検査本文は55から不変。inspect-preparedのQA log条件、F1/F4、原351の未確認は別に保持する。

### 新固定41の両OS CI原証拠

実行HEAD8f03e280ab3bdb8cf772832e9393e8e8e22eeb77、専用run37982218518。全12job終了、7成功5失敗。最新両OSのtransaction/primitivesでは診断と独立証拠保存が全成功し、失敗5jobは取引本体stepである。旧固定055/057と全primitiveを保持。[job/step・小さいartifact metadata](../../verification/task059-save-qa-finalization/code41-native-ci.json)に記録した。

| OS / transaction job | 準備 / 既存12 / 追加27 | 独立照合した全受付 | 取引本体 |
|---|---|---|---|
| Linux / 113995301202 | 3.682180 / 31.679262 / 8.191811秒、全exit0 | 300受付、起動行276/未起動24、batch68、全終端・実log bytes一致、回収true | 131件/1755条件、174.564731秒、FAIL |
| Windows / 113995301326 | 5.750 / 31.063 / 6.547秒、全exit0 | 249受付、起動行151/未起動98、batch51、同じ全照合成功、回収true | 66件/990条件、174.563秒、FAIL |

両OSともscope10正負・058反例・6seed/12sampleが成功。準備30秒、元5診断180/30/180/30/180秒を保持し、全processのstopped=trueを原record/log hashまで照合。[ci-code41-receipt-audit](../../verification/task059-save-qa-finalization/ci-code41-receipt-audit.json)は明示したcode41/source8f03を期待値にして検査した。

Linux原tarは63f88cd97bd035769808b77e50c180f6ff842d59a462a8b1759e26ee616026e8、5,806,395bytes、6,606member。Windows原tarはc525b80104436aec9b1033ff951a3d5b2fdbc744add28771e39d392b661985e5、4,809,396bytes、4,333member。両方ともGitHub toolで取得できたdecoded job textから復元し、宣言hash/全member bytesを確認した。

独立した小さいartifactは最新4jobで生成され、API metadata上の外側ZIPは約2.65〜2.68MB。Windows transaction artifact11642102037の参照は取得できたが、既存環境への転送はproxy tunnel403で拒否された。外側ZIP bytes/API digestと、内側ZIPの宣言hashは未照合。拒否を迂回せず、アクセス可能だったtransaction原tarの照合成功と区別する。小さいartifact生成の成功を元351jobの原因特定や未取得ZIPの照合成功へ置き換えない。最終文書SHAの全workflow/job終了・clean/未pushは最終応答で確定する。

## 351提出までの固定コードと両OS原証拠の対応

**固定コード55a56d09d7c74becaeacdecede16836d93ba8cbc。実行HEAD ac768dee939783d41b8a6788af4b61551fd96d7b。** 30aca09の26件は途中版であり、この55/ac768deの成功へ流用しない。この55/ac768deでは既存12件＋追加27件（負例の所定非0/未確認も含む）を両OSで実行した。両OSともscope10正負・基点058の2反例・6seed診断はexit0。

| OS / job（run37973730943） | 既存12 / 追加27の秒・exit | 全受付原証拠の独立照合 | 全取引 |
|---|---|---|---|
| Linux / 113966598488 | 32.310444秒/0、6.937715秒/0 | 297受付（起動行275/未起動22）、一意batch69、全canonical/root投影/batch終端/実log bytes一致、worker/future/未回収0 | 133件/1773条件、174.708151秒、FAIL |
| Windows / 113966598644 | 33.062秒/0、6.172秒/0 | 258受付（起動行172/未起動86）、一意batch57、同じ全照合成功、worker/future/未回収0 | 78件/1170条件、174.391秒、FAIL |

受付行数はprocess数や取引完了ケース数ではない。共有batchを二重加算せず、未起動はPID/実argv/log/exitなしと理由を保持した。回収成功は全172/2178・97killの取引受入成功を意味しない。

| 原archive | raw SHA-256 / bytes / members |
|---|---|
| [Linux](../../verification/task059-save-qa-finalization/ci-code55-linux-transaction.tar.gz) | 83ae1a52a351d2222788ae0f5a101ed5e9acf54d1cfa21d8c22a1fd42a4a443b / 5783753 / 6581 |
| [Windows](../../verification/task059-save-qa-finalization/ci-code55-windows-transaction.tar.gz) | 9df6f3121f5b13c99dfb55ffd302ce94ec3c9b3af37977ca4f8548a4b621a16d / 4969006 / 4816 |

[全受付・実log bytesの独立照合](../../verification/task059-save-qa-finalization/latest-ci-receipt-audit.json)はarchiveを変更せず、実行HEAD/固定SHA、既存12/追加27、scope10、058反例、全要求ID・原record・batch全内容・log SHAを再検証した。Windows区切りはtarのPOSIX member表記へ対応させるだけでJSON原値を変更していない。

HEADac768deの専用CIは12job終了、primitivesの6job成功、transactionの6job失敗。最新・固定055・固定057の全jobを保持した。最新primitives両OSはjob metadata上成功だが、両方の原log取得はTransport closedのためraw bytes再照合は未確認。transactionの原bytes取得成功とは区別する。

同HEADの通常CI3jobは成功。Godot・凍結受入job113966597878のdecoded UTF-8全job textを[原物archive](../../verification/task059-save-qa-finalization/ci-code55-protected-godot.tar.gz)に保存し、R-01〜R-08の各exit0/tests_ran=true/parser_failed=falseと保護検査の前後成功を確認した。[code55-ci-snapshot](../../verification/task059-save-qa-finalization/code55-ci-snapshot.json)は収集時点で他workflowが進行中のため、このHEADの全workflow終了を表すものではない。最終文書SHAは別に全workflow/job終了を待ち、最終応答に件数と結果を記す。

## 計画・登録・範囲

登録a6022f1e4a7689440928efe65db444336e9128e4、基点579ca1f463aaf9e93275039a59cf9d1ffb86adb5、指定branch codex/task-059-fix-save-qa-finalization。開始dirtyなし・未pushなし。AGENTS.md、059/057依頼、伝言板、057/058報告全文と反例、専用driver/helpers/workflow、素材規約・職業/魔物化の企画・台帳構造・優先仕様、040保存計画、原053/055/057固定証拠を確認。checkout/workspaceに適用可能な追加AGENTS/.agents/skillsは存在しない。追加委譲・別環境切替なし。

最小変更と全assertion世代対応は[実装前plan](../../verification/task059-save-qa-finalization/plan.md)に先に記録した。現在の完成コード完全SHAは[code-fixed-sha.txt](../../verification/task059-save-qa-finalization/code-fixed-sha.txt)に固定する。8282248は切替前の過去固定として保持する。旧057 3cf4b6c、055 0a44409c、053 e003b126の完全SHA・inventory・期待・契約・旧scopeは変更していない。

## 修正内容

受付時に一意request ID・予定argv・予定record先を持つ。Suite.runのqueue前config経路とrun_restart_batchのconfig/env/capture準備、ProcessCaptureのlog.open/record保存を終端化する。未起動のPID/実argv/子log/exit/開始時刻はNone、予定情報と例外理由だけを残す。共有batchは一意原recordのrequest_idsと各root投影へ対応づける。

closeを直列化し、受付停止・future終了・worker終了、全受付ID/予定先/終端record/共有batch/root投影の対応、所有capture状態を独立照合する。記録不在をprocess不在の証明にしない。欠落/壊れJSON/ID違い/保存失敗はrecovery_complete=false、Suite/mainの非0へ伝播する。書けない先と理由・保持可能な終端情報は上位queue inventoryへ残す。回収完了と取引成功は別で、失敗要求を完了件数へ足さない。JSONは同directoryの一時fileからatomic replaceし、記録書込みの競合で半JSONを読ませない。

Linuxは自分が作った専用sessionとgroup、exec前から渡す継承ownership tokenで入れ子も監督する。所属/start_ticksを再確認したpidfdだけへsignalを送る。session/PID番号だけで他processを終了せず、所有token不明なら終了を拒否し未確認にする。Windowsは専用Job Object、suspended作成→所属確定→resumeで所属前の孫起動raceを防ぎ、breakawayを許さない。直接子waitと所属子孫の実行停止確認は別に記録する。

全停止/確認は元deadline残量内。期限0・設定失敗・所属不明・保存失敗を回収成功へ補完しない。Linux orphan zombieは実行/handle保持終了としてstateを記録し、他の親が持つwait責務の回収まで保証しない。OS停止、外部から監督者自体を強制終了した場合、QA子が明示的に所有環境を破棄/監督から離脱する場合まで完全保存を保証しない。global/name kill・他job/process終了・OS設定/権限変更なし。

## CIの世代分離とscope

専用workflowの元fixed055/latest、Windows/Linux、transaction/primitivesを保持し、fixed057を別jobへ追加した。当時のcheckout3cf4b6cから当時のprocess_capture・12検証・scope057正負・6seed対照を実行する。旧code-fixed-shaが当時b4ee1eaを指すため、別checkoutの検査引数を完全SHA3cf4b6cへ明示し、固定文書自体は変更しない。最新側は既存12検証・059追加27検証・scope059・基点058反例・6seed対照。sample計測は全取引受入と別。

親の提出前確認を受け、scope059の後続文書許可を059依頼書状態行・059報告・059証拠だけへ限定した。最新担当指示に従い、decision-logの後続追記も拒否する。10正負例を実Git tree/commit/子exitで確認。旧057証拠、058過去報告、担当外文書、依頼本文変更、decision-log書換えはexit1。旧scope057/055 prefixを広げていない。原2259パスのblob不変と44archive/317273全member照合もscopeとは独立して実行した。最終SHAについても全許可パスと原不変を再照合する。

## Linux初期実行・照合・未実施（途中版の履歴）

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

この節は初期提出の履歴である。旧固定55a56d09／実行ac768deの両OS原証拠は「351提出まで」の対応表、新固定41a34ea／実行8f03の原証拠は別の冒頭表を参照する。最終文書SHAの全CI終了結果は最終応答で確定する。

## 永続原証拠・変更一覧

[証拠README](../../verification/task059-save-qa-finalization/README.md)、[archive完全hash/索引](../../verification/task059-save-qa-finalization/archives.json)、code inventory・原不変inventory・旧archive監査・scope正負が入口。原log/実argv/秒/exit・各JSON・raw archive/member hashを保存する。decoded job UTF-8 textのhash、raw tar.gz hash、Git blob、API ZIP digestは区別する。自身の最終SHAは応答で確定。

変更はtools/check_equipment_save_transaction_platform.py、専用process_capture.py/run_ci.py/diagnostic_ci057.py、新process_tree059/process_exec059/diagnostic_fixed057/reproduce058/scope059/test_capture059/tree_fixture059、専用workflowの世代配線、059証拠/報告/依頼状態行、decision-log今回末尾のみ。本番scripts、native/addons、保護26/R8、旧scope/期待/契約/固定SHA/原証拠、原画/data、他workflow、AGENTS、過去報告を変更していない。

## 残件

F1の全取引時間未達とF4実測不足は別の残件であり、今回承認済みのQA修正のために本番codec・検査時間・OS設定へ範囲を広げない。当初の保留はF1/F4および当時取得できなかったCI原物であり、再開後の残件は末尾に記す。新PR・main/PR33反映・merge・force・削除・追加委譲なし。

## 最新担当分担の適用

最新の明示指示に従い、以後docs/decision-log.mdとdocs/tasks/README.mdは更新しない。既存commit d7ecd229baa2ce0cc56c65e9b474abca0e2595dcのdecision-log 126行に、受付ID/専用Linux session・Windows Job/057世代分離/全予算と本番不変/通常revertという059判断の1項目が保存済み。未コミット追記は0。既存項目は削除も履歴変更もせず保持する。以後の判断/検証は本059報告へ記載し、ルッカが取り込み後に記録とタスク表を更新する。scope059も後続decision-log書換え/追記の実exit1を確認する。

## GPT-6 Astra／Highへの引継ぎ時点（受入未完了）

依頼者の明示指定により、以後の実行はGPT-6 Astra／Highへ変更する。現行ターンでは追加実装・次段階の検証を開始せず、既に実行した結果と修正を保存して区切った。依頼書状態は作業中を維持し、本番性能修正の承認へ範囲を広げない。

HEAD6a62fd7のLinux latest transaction CI（run37966701471/job113942743343）原archiveを復元してraw SHA-256 cd3d5ae69f3b8f8404671e581fc032fb9f811398af8d55ef69c4947c788a83f0、4265560bytes、6392member全hash/sizeを照合した。追加21検証・修正前反例・当時scope4検証は成功したが、既存12のshutdown-active-and-futuresは失敗、全取引も119/1653・174.656秒で未達。受付299のうち監督未確認5をfalseのまま保存し、回収成功へ補完していない。

原物で、Linuxのstatからenviron読取りまでの間に所有子がexitすると、空token/EACCESが終端raceとして残ることを確認した。モデル変更指示以前に、同じPID世代の終了を再読取りで確認し、元cleanup_deadlineの残量内だけ再観測する修正と、実際の専用子exitによる回帰を追加済み。所有不明のlive processへsignalせず、予算延長・権限変更なし。変更はprocess_tree059.py/test_capture059.pyだけで、保存commitはbdc1097547a4e1243082f8433fb680683ddb4f1c。既に実行したLinux既存12件と追加22件はexit0/PASS。capture057-linux-exit-race、capture059-linux-22の原log/JSON/argvを保存した。途中の追加21件失敗もcapture059-linux-exit-race-intermediate-failureとして保持する。

WindowsのHEAD6a62fd7 latest primitives job113942743366はcompleted/successというmetadataを確認したが、原job log取得は2回ともTransport closedで失敗した。原archiveと個々のF5結果は未確認。Linux/Windowsとも最新修正22件を最終CIで確認したとは言わない。

[モデル変更時CI snapshot](../../verification/task059-save-qa-finalization/model-transition-ci-snapshot.json)はHEAD1fcb54fの6workflowと当時返った50job、旧HEAD6a62fd7の専用12jobの収集結果。HEAD1fcbの全終了を待ち切っていない。Equipment and Saveの後続jobはまだ未生成の可能性があるため50件を全件確定数としない。旧HEAD6aのWindows latest transactionも収集時in_progress。他の失敗/成功/queued/in_progressはsnapshotのとおりで、取消しはしていない。

次のAstraターンで必要な作業は、保存修正のレビュー、新コードの完全SHA固定/code inventory/scope10正負の再照合、Windows/Linuxの既存12＋追加22と全受付照合の最終CI原証拠回収、原2259blob不変と全archive再照合、059報告/状態の最終化、指定branch最終SHA全CI終了・clean/未push確認。code-fixed-sha.txt/code-inventory.json/scope059-current-policy.jsonは8282248の過去固定を保持したままで、bdc1097の新固定はまだ行っていない。この段階のpush CIで旧固定との差が失敗する可能性を隠さず、次ターンで固定更新と検証を行う。F1時間未達、F4実ENOSPC/nested別volume NOT_RUNは継続。decision-log/tasks READMEは以後も更新しない。


## 再開後の品質修正と検証

同じ/workspace/RPG-maker、引継ぎ83466d2aaee55ecdeee4e51e89c8d1036525fa54、dirtyなし・未pushなしで再開した。GPT-6 Astra／Highの指定とモデル切替通知を受領したが、runtimeのモデル名/effortを独立に取得するツールはなく、実行値を独立確認済みとは記さない。新環境・OS設定・依存導入・追加委譲は行っていない。

レビューで共有batch原記録の照合不足を修正した。起動前のenv失敗＋原batch保存失敗、起動済みbatch本文改変、未起動batch本文改変の3実反例は修正前に全て失敗した。予定原batch先を未起動の終端にも結び、所有するbatch終端全内容と保存原物を照合し、保存失敗を各受付の上位inventoryへ伝える。要求ID/PIDだけが同じでも本文が異なれば非0となる。元のcase/assertion本文、057の12検証、055/057 scope、worker/batch/全予算はbyte不変を再確認した。

受付ID構築途中とcloseの競合も実反例で確認した。受付側が構築中にcloseが空一覧でrecovery_complete=trueとなる旧動作を、新しいacceptance-close-raceで検出した。受付と停止確定に同じrequest_lockを使い、進行中受付が一覧から落ちないようにした。未終端の受付はfalseと欠落理由を残す。close競合/再呼出しの既存検証に加えたため、059追加は26件となる。

Windows HEAD6a62fd7のlatest transaction原ログを別経路で取得し、raw archive 8d33c1defa6018d29ddfc8e14e3a2b9bef2b1f7009d4866c07496ad5f86d6f27、3084932bytes、3574member全hash/sizeを照合した。既存12、当時追加21、scope、基点058反例、6seed診断は全exit0。058ではWindows実PermissionError後にexecution0/recovery_complete=true、外側0.5秒kill後も孫heartbeatが継続した。実174/180秒の反例とは呼ばない。同jobの全取引は49/735・174.797秒で失敗し、231受付の回収照合はtrue。新26件の結果とは分離する。

Windows primitives旧job113942743366の直接ログはTransport closedが継続した。artifact11634293939のZIP参照は取得できたが、既存環境から参照先への取得はproxy tunnel 403 Forbiddenで遮断されたため、ZIP bytes/digestは未照合。OS/通信設定は変更していない。transaction原archive取得成功を、このprimitives原物の照合成功へ置き換えない。


再開後のローカル固定30aca09e21783f228c00847029060fa03ecb86e9は、既存12件34.308007秒/exit0、追加26件11.194464秒/exit0、いずれも外側run_commandの180秒以内でsupervision.stopped=true。scope10正負は正例exit0・9負例各exit1。専用archiveはastra-linux-capture012-final/astra-linux-capture026。対応する修正前の3件失敗と受付closeの1件失敗も独立archiveとして保持する。

共有batch修正faa459ee5cc101e708477792b1c7891a9ba4beeaを既存の隔離checkoutで実行した全取引は154件/1968条件、suite174.437967秒、transaction外側175.147200秒/exit1。319受付、worker0、future未完0、evidence_errors0、未回収0、recovery_complete=true。これを原172/2178の成功や性能改善の証明にはしない。受付close修正前の全取引結果であることも区別する。元174/180/30/600秒・15分の制限を維持した。


## CIで追加観測した停止順序と担当外条件

HEAD7f91d04のLinux transaction（run37969914859/job113953604600）は172件/2178条件・153.143秒まで実行したがinspect-prepared:specific_invariantが失敗し、既存12のshutdown-active-and-futuresも失敗した。原archive090ff81e53ee91d9216f317a4c2c4b9b12ca6eeb182a409eae48e5e0becccad5、6189600bytes、7726memberを保存照合。追加25件は成功。Windows同HEAD（job113953604579）は既存12・追加25・scope10・058反例・6seed診断が成功し、全取引は時間未達だった。原archive84bac24b7c0ae005f099807fec61df722b2455463ccfe8692a64240c43b8d5fb、4527902bytes、3661memberを保存照合した。

Linux shutdown原物では初回停止がPermissionErrorとなり、直接子waitで回収残量を使い切った後にtree.finishが呼ばれ、worker2個と4要求の未確認が残った。PermissionErrorの発生箇所自体は旧reprではpathが欠落しており、OS設定の問題と断定しない。所有tree停止の再試行を直接子waitの前へ移し、初回失敗はkill.ok=falseのまま記録し、同じ残量内の停止確認とwaitを別に確定する。例外理由はtypeとstrでpathも保持する。実子を使った初回停止失敗の追加反例は旧順序で失敗、修正後は成功。元予算・既存12検証は変更せず、固定55a56d09d7c74becaeacdecede16836d93ba8cbcで既存12件33.220674秒/exit0・追加27件7.712963秒/exit0、scope10正負を確認した。

inspect-preparedは、元case/assertionを変えずにinspect呼出し前後の既存file bytesを追加読取りし、独立した2rootで再現した。変化した既存fileはprofile/XDG_DATA_HOME/godot/app_userdata/RPG-maker/logs/godot.logだけで、prepareのphase=prepared出力142bytesからinspectのphase空文字出力134bytesへ変わった。保存source/history・decoder・prepared状態・process exit等の他8条件は成功。before SHA-256 ac9c55d62c8cdb7b93b925386d257df560cf34bffe4f937a42ed543940db1418、after c7f651706a62b9c9ce6ee94b20d82ef0591e79a6b9112eeea084e002e362d0b2。inspect-condition-observation-0/1に実argv・原log・case条件・観測手順とbytesを保存した。

この1条件はF1時間未達ともF5回収とも分けて保留する。親への具体的な追加判断事項は「保存不変性の全file条件にGodotのQA監査logを含めるか、その契約とQA出力先を別作業で整理するか」。profile/logの除外による条件弱化、ログ設定変更、本番codec変更は059で実施しない。元special/case/assertion本文のbytesは保持している。独立したF5回収修正・両OS検証は継続する。


## 提出時の保証範囲と取得不能

F5-a/F5-bの既存12＋追加27件は、旧固定55a56d09／実行ac768deと、新固定41a34ea／実行8f03の両OS原archiveで、それぞれ照合した。新41の準備監督・準備process記録・診断原logも8f03の原archiveで照合済み。元351のstep16失敗原因は未確認であり、後の成功から原因を補完しない。Linuxは専用session/start_ticks/継承token/pidfd、Windowsはsuspended作成→専用Job所属→resumeの範囲で今回起動したQA processを監督する。所有不明・期限0・保存不能・設定失敗を成功へ補完しない。既存180/174/30/600秒・15分、元assertion、worker/batch、原固定SHA/旧scope/原証拠、保護26を保持した。OS全体停止・権限/namespaceにより所有確認できないprocess・監督から意図的に離脱するQAまで保証しない。

残件はF1時間内の全取引未達、F4実ENOSPC/nested別volume NOT_RUN、観測済みinspect-preparedのQA log不変条件の別判断、元351診断失敗の原因未確認、小型artifact転送/bytes未照合。旧55／実行ac768deのprimitives原bytes未照合の対象はrun37973730943のLinux job113966598499/Windows job113966598640で、各fetch_workflow_job_logsがTransport closed。job metadata成功だけで原log再照合済みとはしない。新41／実行8f03のprimitivesは両OS job/診断step metadata成功で、transaction原archiveの取得成功をprimitives原bytesの取得成功へ転用しない。新41の小型artifactは生成/参照取得まで、Windows外側ZIP転送はproxy403で未照合。旧artifact11634293939の代替取得がproxy tunnel 403 Forbiddenだったことも別に保持する。環境を切り替えず、OS設定や検査条件を変えない。

原archive/member索引は追加保存し、途中失敗も保持した。提出直前の独立再照合は32archive・62833member・原2259blobすべて一致（10.113890秒/exit0）、保護対象26件も26件一致（0.070796秒/exit0）。artifact-validation-current/frozen-finalの原logとprocess記録に保存した。最終文書SHAのall CI/clean/未pushは最終応答で確定する。main/PR33/新PR、force、削除、追加委譲、decision-log/tasks READMEの追加更新は行っていない。依頼書は状態行だけを報告済みへ変更する。

提出直前の再照合：39archive・73,827member・原2,259blobすべて一致（12.027200秒/exit0）、保護26件一致（0.071126秒/exit0）。artifact-validation-code41-ci-final/frozen-code41-ci-finalに保存。原照合toolの55既定動作も旧55両OSで再確認し、旧期待を41へ置き換えていない。
