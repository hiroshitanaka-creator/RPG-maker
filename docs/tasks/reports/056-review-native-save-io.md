# 056 保存専用native I/Oの独立レビュー

判定：**差し戻し／未達を含む正式提出として維持**。055提出の全47 CIは43成功・4失敗。F2の生存writer保護とF3の依存再検証は、今回のLinux独立実行でも改善を確認した。一方、Windows固定・最新とLinux固定の全取引は時間予算内に完走していない。実ENOSPC・専用nested別volumeも未実施である。primitive成功を全取引・全環境の受入成功に置き換えない。

対象提出 `c469ae1836edb1084e26d6ae3355626fec8028d4`、完成コード `0a44409c99b06569b9e6088ffeb46c2238c821fa`、055登録基点 `b17f2b475ff8c58924720ea24cce8f205422c50b`、056登録 `88049e6173819c604b37340422e56994fb02a3c0`。原053固定は `e003b126de6695fa131e07a3db14c3011fb74f2e` のまま。

## 作業範囲・原物照合

初期checkoutはwork/87f4e66、未commitなし。指定branchをfetchし、remoteが056登録SHAであることを実確認して切り替えた。開始時に当該branchの未pushコミットなし。055は確認済みではないが、056依頼書・今回の明示指示は「未達の055を独立レビューする」承認であるため、その範囲で続行した。

AGENTS全文と保存nativeの限定例外、伝言板、053〜056依頼・053〜055報告、040計画・報告、素材規約・台帳構造、職業・魔物化企画と優先仕様の関係を確認。checkout内 `.agents/skills` と追加AGENTSはなく、workspaceにも適用可能なローカルskillなし。追加委譲なし。

変更は056依頼書の状態行と本報告だけ。QAは `/tmp/qa056/submitted` の提出SHA独立clone、原053の独立worktree、専用一時root・隔離XDGで実行。実装、元検査、workflow、test/.scope-lock、原画・通常入口・実ユーザー保存を変更していない。main反映、新PR、環境起動、mount/VHD/ACL/OS設定変更を行っていない。

- 登録基点→055提出の全111変更パスを列挙し、055許可範囲内であることを照合した。decision-logは末尾追記、055依頼書は状態行のみ。
- 完成inventoryの49パスは、完全SHAのGit blob、raw SHA-256、提出版、056登録版の実bytesが一致。保存本体だけでなくnative・配布物・専用runner/workflowも固定後不変。
- 既存S1/S2 API、旧053 runner/probe/fixture/証拠、既存workflow全件、test/.scope-lock、data/assetsに基点からの差分なし。新expectations/recovery-phasesは原053の同名ファイルと同一bytes。
- 原053の5archive（203,912 member）と055の16archive（55,036 member）、計21archive／258,948 memberを全hash・member集合・size・SHA-256まで照合。tar hardlinkは参照先bytes、symlinkは参照文字列bytesで照合。過去失敗原物も含め、不一致0。初回監査scriptは053索引にmember_index欄がなくKeyErrorになったため、実在する*-members.jsonへ対応させて再実行した。原証拠は変更していない。

## 指摘と最小修正案

### F1継続・高：全取引の時間予算未達

専用workflow run [37874812462](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37874812462) の実jobログと埋込みraw archiveを独立取得した。

| job ID・対象 | 完了ケース／条件 | suite内秒 | 外側transaction秒／exit |
|---|---:|---:|---:|
| 113640855700 Windows latest | 45／675 | 174.203 | 174.765／1 |
| 113640855736 Windows fixed055 | 49／735 | 174.188 | 174.796／1 |
| 113640855713 Linux fixed055 | 139／1833 | 174.045 | 174.683／1 |

期待は各172／2178・97強制終了を全て完走すること。未完走の残ケースは成功ではない。`check_equipment_save_transaction_platform.py` は開始時刻+174秒を内側締切とし、wrapperは180秒で子コマンドを制限する。末尾に出る「全体180秒を超過」は、この実装では174秒側の残時間枯渇でも出る。上表は外側180秒timeout・15分job timeoutではない。

Windows latestのhistory.rename.before待機では残時間が0.01秒となったTimeoutExpiredも原ログにある。Linux固定も末尾の境界待機・復旧queueに時間切れが広がっている。これは条件不一致を成功に直す問題ではなく、同じ要求を所定時間で実行できない問題である。Linux latestの同SHA jobは成功しており、固定49コードパスの差による失敗とは断定できない。buildしたbinary・runner負荷・実行順序の違いは区別する。

既存053 latest（run [37874812457](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37874812457)、job113640855336）もtransactionで失敗。外側jobログは `TRANSACTION_CI_FAIL: コマンド失敗/警告:transaction` までで、旧wrapperは失敗したtransaction.log本文をjobに印字しない。artifact11591334858は取得APIまで成功したが、返されたdownload先への接続はproxy CONNECT403で拒否された。制限を迂回していない。このCIの子ログ固有の最終原因は未確定であり、専用3件と同じ原因だったと断定しない。

独立ローカル追試では、その未改変の旧053 latest wrapperと提出本体で97ケース／1427条件、suite174.070秒、外側transaction174.507秒、exit1を再現した。fault-history等の復旧future待機後に締切が枯渇し、以後は未実行のまま失敗する。import5.338秒等を含むwrapper全体は180.583秒だが、transaction自体の外側180秒timeoutではない。これはローカルの特定結果であって、取得不能なCI子原物を確認したことにはしない。

最小改善は、下記の子ログ保存を先に直し、同予算のWindows/Linux計測で起動・待機・純粋検証・I/O・snapshotを分離してから、支配的な処理だけを改善すること。cache削除を元に戻してF3を再発させる案、件数減・期待値変更・skip・continue-on-error・174/180/30/600秒やjob15分の延長は採らない。055専用runner・probe・必要な保存内部処理への次の実装修正依頼が必要であり、056では修正していない。

### F5・中：timeoutした復旧子の原ログ・終了証拠が欠落する

対象は専用runner `Suite.run_restart_batch`（subprocess.runからログ保存まで）と `Suite.run` の例外経路、`RestartBatch.submit/worker`。復旧子はstdout=PIPEで実行され、TimeoutExpiredになると後続のlog.write_bytesとexecution.json保存に到達しない。Futureのtimeoutは空のstrになり、summaryには `case名:` だけが残り得る。kill側も例外を再raiseしてexecution.json生成へ到達しない。

再現済み：今回の未改変runner実行は93ケース／1367条件、174.101秒で失敗。receipt-prepared.readback.afterを先頭とする復旧batchが子30秒を超え、同batch4件のTimeoutExpiredが記録されたが、その復旧log／execution記録は残らなかった。CI復元原物でも同種の欠落を確認。これは「ログにエラーがないから正常」という推定を不可能にする診断上の欠陥であり、データ破損そのものを観測した主張ではない。

最小修正：起動時から専用fileへstdout/stderrを保持するかTimeoutExpired.outputを必ず保存し、finallyで実PID・argv・開始/終了・実exit・timeout・deadline残量・kill/wait結果を書き出す。queue投入時刻、worker開始、batch ID、各rootの完了有無も記録する。共有batchの秒数を各rootに複写して足し合わせない。未完future／daemon workerを終了時に回収し、残り予算内で原物を確定する。予算不足なら失敗のまま証拠を残す。旧wrapperの子log非表示の改善は旧検査の担当外なので、別の具体差分承認が必要。

### F4継続・中：実容量不足・専用別volumeの証拠不足

実ENOSPCと専用nested別volumeは今回も **NOT_RUN**。読み取りで確認した環境は4CPU相当のcgroup制限、workspace約32GB overlay、tmp/shm約9GB tmpfs。提供済みの使い捨て小容量volume／nested別volumeは確認できなかった。共有領域を埋める試験はしていない。injected-enospc、RLIMIT、同volume別directoryを実ENOSPC／別volumeと扱わない。

必要な準備・承認は後述。未実測のwrite/flush/metadata容量不足、別volume配置時の原bytes保持を、通常primitiveやprocess killの成功から推定しない。

## F1配布・F2排他・F3再検証の確認範囲

Windows/Linux x86_64 debug/releaseの4配布物、manifest、gdextensionの対応を実ファイルhashで照合した。公式godot-cppは `e83fd0904c13356ed1d4c3d09f8bb9132bdc6b77`、ABI4.5、SCons4.10.0。MIT・LLVM exception・MinGW/runtimeの本文が配布側にもある。toolchain-pinsとビルド記録のcompiler/argv/hashを照合し、法的な独立審査をしたとは主張しない。

復元CIのLinuxはGCC13.3.0でdebug/releaseを19.57／17.95秒、WindowsはMSVC19.51.36260でlatest51.16／37.62秒・fixed36.36／30.50秒、全exit0。提出物のGCC14.2.0／llvm-mingw20261006とは別ビルドで、異compiler間のhash一致とは扱わない。buildとimportはtransactionの174/180秒とは別予算である。

独立readelf/objdumpでLinux提出SOはlibc/libm/ld-linuxとGLIBC_2.38までのsymbol要求、Windows提出DLLはKERNEL32とUCRTの依存を確認。Windows一般利用者にGNU/compilerを要求する本体経路はなく、NTFS・handle相対APIを使う。ただし今回の実行環境はLinuxのみで、Windows実行はCI原記録の確認。Windows標準ユーザーのtokenでの独立実行、通常ゲームexport配布は未実測である。Windows primitiveとLinux latest成功transactionの大きいjobログはconnectorのTransport closedで取得できず、全子原物の独立再照合まで済んだとはしない。

公式Godot4.7.2を専用領域へ取得し、ZIP `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実体 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` を確認。既設4.6.3と版確認時のfontconfig警告は受入には使用していない。

Linux追加40ケースは94.250秒（外側94.363秒）で全成功、配布物7ケースは6.551秒で成功。debug/release実ロード、manifest欠落/不正、binary欠落/破損/manifest再hash後も書込み拒否を確認。負例で想定されるloader errorと、正常対照の警告拒否を区別した。以下は実コード読取りと追加40ケースの独立実測の範囲である。

- F2：kernel lockをhandle/fdで保持。生存owner＋ps照会障害中も後発busy、同時初回取得は1writer、kill後は再取得、PID再使用相当metadataがlockを代替しない。unknown／範囲外PIDをdeadへ切り詰めない。旧053 live owner拒否、dead取引復旧、旧writerによる新regular leaseへの書込み拒否を実processで確認した。
- F3：plan/verify cacheがなく、同一Tとfresh Tでjob_progression/jobs/abilities/session変更後の拒否が一致。source_build変更はplan同値の正例だがintentの差でcommit拒否、controlだけcommit成功。世代文字列を呼出側が更新する仮定で検証を省いていない。
- no-clobber、既存確定file切詰め拒否、lock未所有write拒否、hardlink拒否、同bytes別identity拒否、root接頭辞/parent/dot拒否、非ASCII/空白/long path正例、最終target競合、inspect/recoverのsize/mtime/hash不変、追加6 native境界のkill→別process復旧を確認。
- Windowsのcase/予約名/ADS/UNC/reparseとhandle保持、Linuxのopenat/O_NOFOLLOW/同device/flock/O_EXCL/renameat2をコード照合した。実Windowsの全path反例、実PID再使用そのもの、敵対的な非協調namespaceの全race、停電/媒体故障は今回未実測。これらまでF2/F3解消と拡大しない。

## 証拠の同一性・失敗伝播・固定SHA

専用失敗jobの `NATIVE_RAW_PROOF_DATA` を復元し、同jobのMETAにある全archive hash/bytes/member数と照合。全memberを安全な一時領域へ読出してhash索引を生成し、results/sha256.jsonの全1,298／3,766／1,439項目も一致した。

| job | raw archive SHA-256 | member数 |
|---|---|---:|
| Windows latest 113640855700 | f4581053e84016770a8643129991c39f6046a7dff0273d84810e96b03c338114 | 2,286 |
| Linux fixed 113640855713 | 2f6dfdb51e34f4db99d42df29b3f804130bc178e8a78325daf550855cce94f6c | 5,711 |
| Windows fixed 113640855736 | a186b715e7a63e036689a9b2110473f70dd6edc735eeca73af8efd6b9d2f10dc | 2,475 |

これは取得不能だったartifact ZIPのraw hashを検証したという意味ではない。GitHubのZIP digestは順にartifact11592173171=`a3244514781956908a08747b370daf25250a2191ac6c222ea187c58ca32cf0e0`、11591873915=`8bb9cfaa8a1298fb8b11840f7295fa577cedbae1576e93ec89c01b51ffdaa62c`、11592136905=`497a1b1b8397306fa00977018d56e266895eac1e75c16e74cba145e67ea8be2a`。API側digestと今回復元したtar.gzの実hashを混同しない。

最新validatorの16伝播を、検証済みlocal-fixed-raw内の正常baselineに対して実子processで再実行した。control=0、missing-case/zero-checks/warning-log/failed-exit/timeout/modified-bytes/missing-bytes/false-assert/wrong-phase/missing-manifest/missing-summary/rehash-output/rehash-backup/empty-log/count-log-rehashの15負例=各1。後続文書latest正例=0、担当外fixed負例=1。計16伝播＋scope2は16.998秒。

このbaselineは `c8f22dbe4edb8ff5e4dcd699ce0887a25f9b0974` の過去実行であり、今回055提出版の全取引成功には数えない。現完成版との差は49対象内で専用workflow・driverの並列設定・evidence helperの3パス。保存本体/native/期待の同一性と、全取引を今回再実行したかは別の主張である。

fixed055 jobの実checkoutとsource_shaは `0a44409c99b06569b9e6088ffeb46c2238c821fa`。同checkout内の古いcode-fixed-sha欄からargvへ渡る `b96658b66c313655b276603d4ead92b507f2b6cd` は、fixed profileではscope対象に使われない。wrapperのtargetはfixedならsource_sha、latestならfixed_sha。古い欄を実checkoutと誤認しない。latestの比較対象は0a44409であり、056文書追加を055実装範囲違反に混ぜない。

## 条件を保持した時間内訳の独立計測

初回native全取引は未改変runnerで実行したが、archive読取り監査・末尾の回帰実行との重なりがあった。その93件という進捗をCI性能の代表値にしない。続く計測は他の検査終了後に単独で実行した。提出版driverをimportし、seed/run/run_restart_batch/snapshot/submitの入口・出口を一時Pythonラッパーで観測しただけで、元source/fixture/assert/並列4worker・16case/174秒締切/子30秒は変更していない。

結果は142ケース／1860条件、suite174.033秒、外側174.545秒、exit1。計測により完走したとはしない。以下は並行区間の観測値であり、合計して174秒の内訳と呼ばない。

| 観測 | 結果 |
|---|---|
| seed6種、順にtyped/plain/granted/missing/corrupt/unclean | 1.287／1.415／1.397／1.354／1.286／1.403秒、直列計8.141秒 |
| 復旧queue投入→batch開始 | 192要求、中央値0.060秒、最大5.828秒 |
| 復旧batch、各processを1回だけ計上 | 74batch、観測経過時間の合計630.374秒、中央値7.803秒、最大23.650秒、例外3 |
| snapshot | 260回、合計5.338秒、中央値0.015秒、最大0.089秒 |

batchは最大4本が並行するため、630秒はwall-time超過の値ではない。同じbatch argvを各rootへ複写したexecution行は重複計上しない。submitの待ち時間にはqueueと子実行が含まれるのでbatch時間と足さない。queue待ちによりケース完了が遅れることは実測できたが、WindowsのCPU/I/O内訳までこのLinux計測から確定しない。

CI失敗原物のunique argvでも重複を除いた。Windows latestは25batch・累積303.439秒、固定は26batch・304.489秒（2worker）。Linux固定は65batch・611.601秒（4worker）。Windowsの6seedは各約1.31秒、Linux固定は各約0.91秒。計算には成功してexecutionが残ったbatchだけが含まれ、timeout子の欠落分は補完していない。過去のWindows4復旧worker／16caseで12件まで悪化した原物も保持されており、並列数を増やすだけの改善を推奨しない。

さらに専用一時GDScriptで提出Tを継承し、superへ同じ引数を渡してplan/verify/read/writeを時刻計測した。ioも実nativeへ同じcallを転送して計測。元コードを編集せず、6seedをそれぞれ新しいQA rootへコピーしてplan→prepare→commitを1回ずつ実行した。これは内訳診断であり、172ケースの受入実行の代用ではない。各子予算30秒、全exit0・committed=true、警告なし。

| seed | 子全体秒 | 取引部分秒 | plan秒（6回） | verify秒（5回、read重複除外） | native呼出し計秒※ |
|---|---:|---:|---:|---:|---:|
| typed | 3.660 | 1.716 | 1.425 | 0.276 | 0.002815 |
| plain | 2.801 | 1.491 | 1.237 | 0.241 | 0.002502 |
| granted | 2.600 | 1.507 | 1.233 | 0.259 | 0.003343 |
| trial-missing | 2.498 | 1.413 | 1.178 | 0.223 | 0.002332 |
| trial-corrupt | 3.024 | 1.802 | 1.484 | 0.303 | 0.003730 |
| trial-unclean | 2.977 | 1.829 | 1.493 | 0.317 | 0.002480 |

※native呼出しはread/write/その他に内包する別観測。Godot bindingの呼出し時間を含み、kernel内部CPU時間ではないので二重に加算しない。engine起動後から_initialize入口までのticksは0.574〜0.824秒、GameSession構築0.316〜0.535秒、T初期化0.0035〜0.0048秒。起動・script load・依存構築をnative I/Oへ混ぜない。

このLinux tmpfs上の正常取引ではplan＋verifyが取引部分の約99.0〜99.2%だった。**この条件では純粋な再検証が支配的**。native flushやsnapshotだけを速くすれば解消すると判断できない。次の最小案は、fresh検証の入口・全依存の確認を維持しつつ、純粋検証内部の重複走査・型比較・割当てを計測して減らすこと。まずT.plan内のdecode/migration/prepare_candidate/encode_candidateを分離計測し、encode内部の再decodeやmetadata検査を含む全検証義務を残す。既存S1/S2 codec/validator自身の変更が必要なら、055の既存許可範囲ではなく次依頼の具体パスとして承認を得る。plan結果を古いTから無条件再利用するcacheは復活させない。最適化を受入にするには、元172/2178・97kill、同一T/fresh依存変更、正負・原bytes・warning・時間上限の全再実行が必要。Windowsは同じ診断を別途実行し、Linux比率を流用しない。

## 既存回帰の独立実行

cwdは提出版独立clone、全て公式4.7.2と隔離XDG。R検査の各verify300秒、既存個別予算、警告検出を維持した。

| コマンド | 実秒 | 結果 |
|---|---:|---|
| `python tools/check_frozen_files.py` 前／後 | 0.082／0.041 | exit0、26/26 |
| `python tools/run_locked_checks.py` | 161.132 | exit0、R-01〜08全PASS、tests_ran=true/parser_failed=false |
| `godot --headless --path . --script res://tools/check_equipment_rules.gd` | 0.556 | exit0 |
| 同 `res://tools/check_equipment_save_migration.gd` | 20.920 | exit0 |
| 同 `res://tools/check_equipment_save_codec.gd` | 12.290 | exit0 |
| 同 `res://tools/fixtures/equipment-save/legacy_equivalence.gd` | 1.938 | exit0 |
| `python tools/validate_assets.py --strict` | 9.320 | exit0、問題0 |

全上記logにSCRIPT ERROR/ERROR:/WARNING:/Parse Error/Fontconfig error/_FAIL:なし。初回native suiteのclean importは54.336秒、追加primitive前importは5.248秒、原053別checkoutのclean importは70.753秒。全体計測ではこれらのimportを取引の内訳へ足さない。

原053固定も当時のcheckout・当時のwrapperを改変せず再実行し、**172／2178・97kill・14伝播・scope2全成功**。suite136.399秒、外側transaction136.925秒、wrapper全体156.693秒、exit0。保護前後26/26。原053成功とnative版の未達を別々に保持する。

## 実argv・今回証拠の所在

次は今回実行した主要argv。Godotはすべて `/tmp/qa056/independent/bin/Godot_v4.7.2-stable_linux.x86_64`。Python実体はwrapper記録の `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python`。同一QA rootを再利用せず、追試時は新しい専用outputを指定する。

```text
cwd=/tmp/qa056/submitted (c469ae1836edb1084e26d6ae3355626fec8028d4)
python tools/fixtures/equipment-save-transaction-platform/launch.py --output /tmp/qa056/independent --profile latest --phase transaction
python tools/fixtures/equipment-save-transaction-platform/run_ci.py --godot /tmp/qa056/independent/bin/Godot_v4.7.2-stable_linux.x86_64 --source-sha c469ae1836edb1084e26d6ae3355626fec8028d4 --fixed-sha 0a44409c99b06569b9e6088ffeb46c2238c821fa --profile latest --output /tmp/qa056/primitives/results --primitives-only
python /tmp/qa056/profile_suite.py
/tmp/qa056/independent/bin/Godot_v4.7.2-stable_linux.x86_64 --headless --path /tmp/qa056/submitted --script /tmp/qa056/measured.gd -- /tmp/qa056/measured/typed
# 同じargvの最後をplain/granted/trial-missing/trial-corrupt/trial-uncleanへ変えて各1回

cwd=/tmp/qa056/primitives/legacy053 (e003b126de6695fa131e07a3db14c3011fb74f2e)
python tools/fixtures/equipment-save-transaction/run_ci.py --profile fixed053 --source-sha e003b126de6695fa131e07a3db14c3011fb74f2e --fixed-sha e003b126de6695fa131e07a3db14c3011fb74f2e --godot /tmp/qa056/independent/bin/Godot_v4.7.2-stable_linux.x86_64 --output /tmp/qa056/original-fixed/results

cwd=/tmp/qa056/submitted (c469ae1836edb1084e26d6ae3355626fec8028d4)
python tools/fixtures/equipment-save-transaction/run_ci.py --profile latest --source-sha c469ae1836edb1084e26d6ae3355626fec8028d4 --fixed-sha e003b126de6695fa131e07a3db14c3011fb74f2e --godot /tmp/qa056/independent/bin/Godot_v4.7.2-stable_linux.x86_64 --output /tmp/qa056/original-latest/results
```

原物・実argv/秒/exit/hashは一時QAに保持し、提出許可が2文書だけなので追加archiveをcommitしていない。本報告に再現入口・結果・主要hashを残す。これらの一時ファイルはリポジトリの永続成果物とは呼ばない。

| `/tmp/qa056/` 以下の証拠 | SHA-256 |
|---|---|
| ci055-jobs.json | 65eae58cd36bc11f623e2090ed2fbd16366d8fc9320c4032ee85c7f5d6d55296 |
| archive-audit.json | b51bd6e850b7accaaf1823a7abfb53ceb0fc56917c69ae8c0c78fc019a402d32 |
| primitives/execution.json | df7447cfc4732ef474956e08bc65d9f8177c7d43fd2ace6e9eafef99f646f1e6 |
| propagation-review/review.json | 7669553e1c9bbda85c00e24806faf9c80a5bccb79700207513046a5bdc6e6a25 |
| regression/commands.json | 44a67f4255bba12d1ccda829a7fa84089038968026f3f4d56f3fab7eabf76c74 |
| original-fixed/execution.json | f489d4cc8f612bf2e557d687b713bbd1cbef1dc37d4342a1a4ca7ece95b4d98b |
| original-latest/results/summary.json | 18c040d506d638e2443ed7186be98a8b7de46acdeb0212f249fa8516563a614e |
| original-latest/transaction.log | 86ebc3bd58ca750d28afa9f2b8b999cdbf8caa858b272aae44ba9cd7cd35d01a |
| profile-suite/timing.json | 1f3b19758f0de25d7da1f73ef781a71645336205fa77502f19d3b88cdde0216f |
| profile-suite/results/summary.json | 4898f0231c67fa31a0baf7b2ed18bc616bac01bcbec7ca26c443b56425a8eaba |
| profile_suite.py | 2c74f02bf05c8439aa230ca1b7ecad3797952a0703d4639dc87ec1fd3814d486 |
| measured.gd | 488986c188fc32a6fb346b94866cc6f98d1c6d67f6e9846bd4a0776c2e36e03d |

GitHub CLIのActions readはForbidden。接続済みGitHub read-only APIのruns/jobs/logs/artifactsを用いて上記の原記録を確認した。artifactダウンロード拒否と大きいjobログのTransport closedは未取得のまま明記し、代替したjob内raw archiveと区別する。

## 専用環境の準備で別途必要な承認

推奨は既存の使い捨てrunner/VMを管理者が事前準備し、標準ユーザーへ専用領域だけを渡す方法。新環境の勝手な起動・本番や共有diskの充填はしない。承認事項は次の2群にまとめられる。

1. **領域と上限の提供**：Linuxなら専用64MiB小容量FSと32MiBのnested別FS、Windowsなら専用固定上限128MiB NTFS volumeを2つ、など。具体値はfixtureの実サイズ・metadata余裕と照合して確定する。QA用root、device/volume ID、標準ユーザー、書込み容量上限、ログを保存する別の領域、保持期限・後片付け担当を指定する。既設領域があれば準備操作を省けるが、実別volumeをIDで確認する。
2. **準備・撤去操作の限定承認**：必要な場合だけ、指定imageへのformat、専用rootへのmount／VHD attach、必要最小の専用directory権限設定と、終了後のunmount／detachを承認対象にする。対象image・mount先・最大消費容量・標準ユーザーへの影響を事前提示する。共有driveのACLやOS全体の設定は対象に含めない。撤去はprocess終了→raw/log/hash退避→空き容量・残handle確認→指定mount/VHDだけ解除→image処分の順。今回これらの操作は未実施。

実試験ではwrite/flush/metadataそれぞれのOS error、直前直後のfree bytes、部分write、原source/history/backupのbytes、再起動後のphase/数量を記録する。nativeが返すos_errorをQA側で保存し、汎用injected_io_failureと混ぜない。nested volumeはsource/backup/target配置別に同volume対照を置き、Linuxのdevice不一致拒否とWindowsのreparse拒否を区別する。Windowsでjunction拒否だけをvolume ID分岐の実証としない。

提供・承認がない間はF4未達のまま。他の改善・回帰は独立して進められる。通常UI／実ユーザー保存／S4/S5、作品の採否、停電・媒体故障、全FS保証は本レビューの成功範囲に含めない。

## 055提出CIと056提出境界

GitHub jobs APIでbranch=`codex/task-055-native-save-io`、head_sha=c469ae1、pushの6runに限定し、各total_countと実取得件数一致、47件全completedを確認。同SHAで056branch作成時に発生した別runは混ぜていない。

| workflow | run ID | 成功／失敗 |
|---|---:|---:|
| CI | 37874812468 | 3／0 |
| 006固定受入と最新回帰 | 37874812477 | 17／0 |
| Equipment and Save CI | 37874812479 | 14／0 |
| Equipment Codec CI | 37874812492 | 3／0 |
| 装備保存I/O・中断復旧 | 37874812457 | 1／1 |
| 保存専用native Windows・Linux | 37874812462 | 5／3 |

056は指定branchへ2文書だけcommit/pushする。最終自己SHAとその全CI終了結果、clean／未push有無は最終応答に記録し、存在しない最終CIの成功を先取りしない。文書追加によるscope拒否が出た場合は既存実装の失敗と分ける。全CIが緑でない間はAGENTSの意味で「完了」とはしない。
