# 055 原証拠

実装報告は [055-native-save-io.md](../../tasks/reports/055-native-save-io.md)。全受入成功ではなく、CIの180秒予算未達と実ENOSPC／別volume未実施を含む提出。

- `code-fixed-sha.txt`：完成コードの完全SHA。`code-fixed-inventory.json`：49pathのGit blobとraw SHA256。
- `local-execution.json`／`local-code-equivalence.json`：実行したc8f22dbeと固定adbdの差を明示。保存・build・論理検査・配布物47pathは同一blob、差はarchive helperと新workflowの明示fetchのみ。
- `local-fixed-raw.tar.gz`：172/2178・97kill、追加40、配布物7、伝播16、scope2の原bytes。negative-deltasの変更bytesと削除一覧はbaselineから各変異を復元できる。symlinkは参照文字列のbytesを`symlink-references.json`へ保存し、展開先外を参照させない。
- `development-raw.tar.gz`：元版F2/F3再現、既存回帰全文、初期失敗、専用領域調査。途中のsource不一致失敗も保持し、完成受入へ数えない。
- `ci-*.tar.gz`：各名前の開発世代CI失敗原物。成功世代と混ぜない。全archiveのraw hash・member数・索引は`archives.json`と`*-members.json`。
- `build-and-reproduction-raw.tar.gz`／`build-final-contract-*.json`／`reproducibility.json`／`toolchain-pins.json`／`binary-dependencies.json`：4配布物の実build、再コンパイル前後hash一致、公式依存・compiler・runtime/license。ソース手順は`native/equipment_save_io/README.md`。
- `original-evidence-check.json`：原053の5 archiveを全memberまで確認。Git blobとraw SHA256は別欄。
- `ci-observations.json`：保存時点のjob状態・artifact ID/digest/期限。原物未取得は明示し、GitHub digestを実測raw hashとは呼ばない。最終提出SHAの全CI結果は同一SHAのActionsと最終応答に残す。
- `environment*.json`：隔離小容量／nested別volume未提供と、切断通知後の実アクセス確認。環境設定や共有disk容量を変更していない。
- `changed-files.txt`：登録b17f2bからの今回差分一覧。

11:00 JSTの継続指示後、復旧worker 4／case worker 16へ専用runnerの2行だけを変更した。`scheduling-code-equivalence.json`に旧固定adbdとの49path比較を保存し、保存・ゲーム・build・配布物等48pathのblob不変を確認する。`schedule-four-working-tree-raw.tar.gz`は124.256秒の172/2178・97中断と独立validator照合の作業ツリー診断。実行開始HEADと未commit差分を原source.jsonへ明示し、完成SHAのCI証拠と区別する。

初回提出4f1eの全47job終了・43成功/4失敗は`ci-4f1e-all-jobs.json`。専用取引4jobの原log・archive・member索引は`ci-4f1e-*-transaction*`、原053固定/最新の成功logは`ci-4f1e-original-*-job.log`。全14 archiveの一覧は`archives.json`。

4復旧worker/16case workerを両OSへ適用したdd909 CIではLinux固定141件へ改善、Windows最新12件へ悪化した。原logとarchive/member索引は`ci-dd909-*-four-worker*`。最終構成はWindowsを元の2/8に戻し、Linuxだけ4/16。全16 archiveは`archives.json`参照。各観測を異なる世代として保持し、旧構成の成功を新構成の完走と取り違えない。

archiveは展開せずmemberのraw hashを照合できる。通常file/hardlinkはtarfile.extractfileで得たbytes、古いsymlinkはlinknameのUTF-8 bytes、新しいinert referenceは記録したtarget_base64を使う。archive自体のSHA256と各memberのsize/SHA256の両方を索引へ照合する。member数と名前集合も一致させる。自己生成した索引だけで受入を決めず、固定expectations、原PASS/FAIL log、Git blob、実exitを併せて読む。

後続CI原物はActionsのartifactに保存される。ローカルでは大きいprimitive log取得がTransport closed、署名artifact URLの取得がproxy CONNECT403となり、原bytes未取得のものがある。期限とIDはci-observations.json参照。Windows54ケースの最終状態や最終SHA全CIを、以前の小さい世代archiveから推定しない。
