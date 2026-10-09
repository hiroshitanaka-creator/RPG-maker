# 059 保存QA終端記録・限定子孫監督の原証拠

[実装前計画と世代対応](plan.md)、[059報告](../../tasks/reports/059-fix-save-qa-finalization.md)を入口とする。全取引のF1時間未達、F4実ENOSPC/nested別volume NOT_RUNを診断sampleや回収成功で置き換えない。

- [完成コードSHA](code-fixed-sha.txt)は8282248971482790a62485b9b510684e4469e2c7。[code inventory](code-inventory.json)でGit blob/raw SHA-256/bytesを区別する。
- [制限済みscope正負](scope059-current-policy.json)は後続059文書正例、担当外code/固定差分/code改変/旧057証拠/058過去報告/担当外文書/依頼本文/decision-log書換えの10件を実exitで検証する。旧scope057は変更していない。古いscope059-code/scope059-final-codeは途中版として保持し、制限済み版の結果と混ぜない。
- [本番・保護・原証拠不変inventory](unchanged-inventory.json)は基点579ca1fの2259パス。実bytesのGit blobとraw SHA-256を記録。[原archive照合](old-archives-audit.json)は053/055/057の44archive・317273member全照合。
- [元検査保持](method-preservation.json)：元172/2178・97kill、16伝播、worker/batch、180/174/30/600秒・15分、case/assertion本文、055 scope、057の12検証を保持。
- [archives.json](archives.json)と各member索引：原archiveのraw SHA-256/bytes・全member hash/size。baseline058-linuxは修正前反例。capture059-linuxは20件の途中版、capture059-linux-21は所有不明拒否を加えた21件。capture057-linux-finalは同監督版の既存12件。
- local-full-9d4-failureはHEAD9d4d361の174秒未達118件/1642条件。294受付の終端/worker/future/監督を確認したが、全172件の成功ではない。
- local-regression-7f4は隔離7f4c608でR01〜08・装備・S1/S2・旧142/10全文・素材・保護26前後の原log。現在本番/保護の不変bytesは別inventoryで照合する。
- local-primitives-9d4は提出済みSOのextra40・binary7。手元native rebuildなし。DLL/SO再buildと提出済み配布物の照合は既存両OS CIで別実行。
- local-propagation-059はhash照合済み過去正常証拠c8f22dbeを原057archiveから再構築し、現validatorで再照合して16改変と055 scope2例を再実行。現059全取引の成功には数えない。
- ci-first-fixed057-windowsは初回HEAD9d4d361のfixed057当時checkout3cf4b6c。12捕捉・scope3例は成功、取引時間とGet-CimInstanceの30秒計測は失敗。059の監督成功へ流用しない。
- engine-linux.jsonは既存launch.pyと同じ公式4.7.2取得経路のZIP hashと実体hash。既設4.6.3は受入に使わない。

`evidence-tools/verify_artifacts.py`で059archive全memberと旧2259blobを再照合できる。package_local.py/regressions.py/propagation.py/check_source.pyは今回実際に使った手順で、所定の/tmp/qa059原物を前提にする。旧証拠を上書きしない。

CIの原archiveは取得できたdecoded UTF-8 job textのNATIVE_RAW_PROOF_DATAを復元し、宣言hash/size/member数と照合する。decoded text hash・raw tar.gz hash・Git blob・API artifact ZIP digestは別物。取得不能は未確認として記録する。

モデル変更時の保存：capture057-linux-exit-race（既存12/PASS）、capture059-linux-22（追加22/PASS）、capture059-linux-exit-race-intermediate-failure（途中21/FAIL）、ci-second-linux-latest（HEAD6a62fd7追加21成功・既存12の1件失敗・全取引時間未達）を追加した。原archiveは合計14。次のGPT-6 Astra／Highターンまで新修正の固定SHA更新と最終両OS検証を保留する。従来8282248のcode pin/inventory/scope証拠は過去固定のまま。[引継ぎCI snapshot](model-transition-ci-snapshot.json)は収集時点のmetadataで、全CI終了/全受入成功の証明ではない。
