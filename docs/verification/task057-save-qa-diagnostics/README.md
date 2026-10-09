# 057 保存QAログ保持・診断証拠

受入全体は未達。F1時間未達とF4実ENOSPC／nested別volume NOT_RUNを含む。[057報告](../../tasks/reports/057-save-qa-diagnostics.md)を参照。診断sampleを172ケース／2178条件／97killの成功に扱わない。

最終コードは[code-fixed-sha.txt](code-fixed-sha.txt)の3cf4b6c293f6796220b43cf566f8eb792c3932ec。[code-inventory.json](code-inventory.json)はこのSHAのGit blobとraw SHA-256。b4ee1eaの旧inventory/scopeも別名で保持する。既存055 scopeと固定SHAは変更していない。

## 証拠の入口

- [archives.json](archives.json)：23archiveの完全raw SHA-256、サイズ、member索引への対応。各*-members.jsonは全memberのraw hashとサイズ。
- local-capture-completed-code.tar.gz：最終12正負検証、停止時の全8要求の記録、b4ee1eaのdequeue未起動欠落4件の再確認、最終057 scope正負。旧local-capture-final.tar.gzはb4ee1ea段階の証拠で、名前だけを最終コードと解釈しない。
- local-regression.tar.gz：R-01〜R-08／保護26前後／S1/S2／装備／旧比較142/10全文／素材strict。隔離clone21d6a66の結果。本番・保護検査のblobは最終コードまで同一。
- local-propagation.tar.gz：検証済み過去正常証拠に現validatorを適用した16伝播＋055 scope正負。現在版の全取引成功ではない。
- local-primitives.tar.gz：f6d5697の専用primitive40件と提出済みSO binary7件、実argv/秒数/exit。
- local-full-first.tar.gz／local-full-code-final.tar.gz：手元の失敗も保持。後者はf6d5697（コードb4ee1ea）の全取引であり、3cf4b6cの全取引成功ではない。初回import warning拒否も残す。
- ci-first-{linux,windows}-{fixed,latest}.tar.gz：初回HEAD21d6a66の専用transaction4jobの原archive。実fixed対象は0a44409…、latest対象は21d6a66。全4失敗を保持。
- ci-code-windows-{fixed,latest}.tar.gz：f6d5697専用transactionの原archive。Windows固定71/1065、最新53/795で失敗。最新のF5/057 scope/6seed対照は成功。
- *-decoded-log.tar.gz／ci-code-decoded-logs.tar.gz：connectorが返したdecoded UTF-8 textの保存。GitHub生logの原bytes hashではない。
- [measurement-summary.json](measurement-summary.json)：原JSONからの集計。seed off/on、inclusive/exclusive、実環境、起動/依存、build/import、queue/snapshotを含む。並行累積とwall union、上位spanと下位span、nativeの重複を加算しない。
- [original-archive-audit.json](original-archive-audit.json)：元053/055の21原archive・258948member照合。旧原証拠を上書きせず、そのGit blobとraw hashを分けて記録。
- [unchanged-inventory.json](unchanged-inventory.json)：基点の7828不変ファイル、うち本番/保護/原証拠541ファイルのblob一致。
- ci-code-platform-terminal.json：f6d5697専用8jobの終了記録（6成功2失敗）。ci-*-all-terminal.jsonはそれぞれ計測時HEAD全47jobの終了記録（初回42成功5失敗／f6 45成功2失敗）。ci-*-jobs-snapshot.json／ci-first-jobs.jsonは取得時点のsnapshotで、未終了jobを全終了と読まない。最終提出HEAD全CI結果は提出応答で確認。
- ci-*-artifacts-*.json：API artifact ZIP digest、ID、サイズ、期限。ローカルZIP取得・hash照合の成功を意味しない。

## 最終修正コードの両OS証拠補足

HEAD80cff71fed017729bc30a5c36a1bd918588fb3bb／コード3cf4b6cのci-completed-{linux,windows}-{fixed,latest}.tar.gzを追加。専用8job終了・4成功4失敗。両OSで強化後F5 12件・057 scope正負・6seed対照の原bytesを確認した。計測JSON集計もこのrunを追加し、前runのCPU/速度を流用していない。ci-completed-code-platform-terminal.jsonとci-completed-code-artifacts.jsonに終端metadataとAPI digestを保存。原053固定・最新PASS出力もci-completed-decoded-logs.tar.gzへ保存。全CIの後続文書HEAD結果は提出応答で確定する。

## 取得とhashの区別

取得できたCI原archiveはdecoded job log中のNATIVE_RAW_PROOF_DATAをbase64復元し、METAの宣言raw SHA-256/bytes/member数と一致を確認。全memberとresults/sha256.jsonも再照合した。*-meta.jsonに来歴とdecoded text hashを保持。

artifact download connectorはfile refを返したが、ローカルURL取得がproxy CONNECT403で失敗した。ZIP原bytes/hashは未確認。一部f6d5697成功jobのlogはconnector Transport closedで取得不能（再試行も同じ）。そのjobの原archive・実測秒数を初回証拠から推定しない。[acquisition-and-provenance.json](acquisition-and-provenance.json)に対象IDと理由を記録。アクセス制限の迂回なし。

ローカルarchiveはprofile／.godot／legacy053 checkout／bin／template／propagationの複製と一時indexを除外した証拠集合。local-propagationはbaseline results・negative-deltas・validation logを保持。symlink自体はローカルarchiveへ追従せず、snapshotの*.link.txtやmanifestでtargetを観測する。CI原archiveのsymlink-references.jsonは元target bytesを保存する。完全なQA作業ディレクトリのコピーとは主張しない。

## 再検証

安全な専用未存在出力先を指定し、Godot4.7.2のimport後に実行する。fixtures/expectationsや本番を変えない。

```bash
python tools/fixtures/equipment-save-transaction-platform/test_capture057.py --output /tmp/qa057-recheck/capture
python tools/fixtures/equipment-save-transaction-platform/scope057.py --code-sha 3cf4b6c293f6796220b43cf566f8eb792c3932ec --source-sha <文書を含む完全HEAD> --self-test --output /tmp/qa057-recheck/scope.json
python tools/fixtures/equipment-save-transaction-platform/diagnostics057.py --godot <公式4.7.2実体> --output /tmp/qa057-recheck/measurements
python docs/verification/task057-save-qa-diagnostics/evidence-tools/verify_archives.py
```

evidence-toolsには実際に使ったdecode/旧archive照合/回帰/伝播/集計/初回収集の手順を保存。/tmp/qa057と取得済み素材を前提にする作業記録で、全取引の原検査を置き換える入口ではない。最終archive検証は上記verify_archives.pyで単独実行できる。
