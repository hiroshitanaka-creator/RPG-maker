# 054 保存取引の独立レビュー・Windows対応案

判定：**差し戻し**。Linuxの固定172ケース/2178条件・97 kill・14伝播・scope2と対象78 CIは独立確認で成功したが、Windowsでは本体が全パスを拒否する。さらに生存ownerの排他を照会失敗で奪取する問題と、依存変更後に古い候補をcommitする問題を専用Linux QAで再現した。CI成功はWindows向けS3の受入成功ではない。実ENOSPC・実別volumeも未検証である。

対象提出 `10de1ff1c78d7a62e96f51b52f6135f82bc3fea0`、コード固定 `e003b126de6695fa131e07a3db14c3011fb74f2e`、054登録 `67a0caf348ccf81d0673ab2be4c9c97a8ecc41cc`。開始時のremote指定branchは登録SHA、未commitなし。初期checkoutはwork/87f4e66だったため指定branchをfetchし登録SHAへ切り替えた。053branch名を短縮してfetchした初回はref不在、fetch設定がmain限定のためremote tracking refからのswitchも失敗し、取得済みFETCH_HEADから指定branchを作成した。失敗を成功扱いしていない。

AGENTS全文、054/053依頼、053報告、040計画（特に4/7/9/10節）、051/052報告、素材規約・台帳構造、職業/魔物化企画と優先仕様の関係、S1/S2/S3・検査・fixture・workflowを確認した。checkoutに追加AGENTS/.agents/skillsはなく、workspaceにもskillsなし。追加委譲なし。変更は054状態行と本報告だけ。QAは `/tmp/qa054/` の固定SHA独立cloneと隔離XDGだけで、提出コード・過去証拠は変更していない。

## 指摘と最小修正

### F1 高：Windows上で全保存取引入口が拒否される

対象 `scripts/game/equipment_save_transaction.gd:32–57,186,199–204,236–249` と `.github/workflows/equipment-transaction.yml`。

`path_ok` は `OS.get_name() != "Linux"` を無条件拒否する。これを外してもコロン/バックスラッシュを全面拒否し、GNU `stat -c %d/%h`、`ps -p PID -o pid=`、`mv -T --no-clobber`、`DirAccess.create_link` に依存する。正常なWindows QAパスをinspect/prepareへ与えても最初のread_bytesでpath_invalidとなるコード経路である。**これはコード調査であり実Windows実行ではない**。Linux正常対照は後述の全172件。

期待：Windowsの一般ユーザーが特権・開発者モード・GNUツール導入なしで同じS3契約を利用できる。実際：Windowsは入口で拒否。workflowはubuntu-latestのみで、既存成功はこの欠落を検知しない。最小修正は後述のOS内部I/O境界の置換とWindows実QA追加。OS分岐を消すだけ、標準renameへ置換するだけでは不可。

### F2 高：owner生存照会の失敗を死亡と誤認し、同時writerを許す

対象 `equipment_save_transaction.gd:184–187`。psが0以外なら理由を区別せず次leaseを作る。権限不足・起動/照会失敗を「死亡確認」と扱ってはならない。

再現は固定本体と未変更probeを使用。先行Godot Aを `lease.acquire.after` で待機させ、実PIDが生存中に後発Bを起動する。通常PATHの対照Bはbusy。同じBだけのPATH先頭に `#!/bin/sh\nexit 2\n` の専用ps stubを置くと、Bはlease-00000001を取得してconverted.jsonを確定した。AのPID8076はその時点で生存、BのPID8127はexit0/phase=committed/committed=true。その後QAのrelease markerでAを正常終了し、Aもexit0。OS設定・実ps・他ユーザーの環境は変更していない。

これは**生存照会障害の注入**であり、現実のps障害を観測したという意味ではない。ただし本番コードを通り、二つの実processによる排他違反を実測した。破損保存そのものはこの再現では観測していない。単一writer契約違反が確定したため、破損を仮定しなくても修正対象になる。

最小修正：内部生存判定をalive/dead/unknownの3値にし、確定dead以外は書込み不可。推奨native層ではカーネルが保持する取引lockを使い、PIDの照会結果だけでlockを奪わない。既存owner metadataは監査資料にとどめる。生存/死亡/照会拒否/起動失敗/不正出力/PID再使用/同時初回取得を固定期待に追加。コードだけの短期修正ならpsの未知結果を拒否するが、Windows未達は解消しない。

### F3 中：cacheの依存集合が不足し、新規検証で拒否する候補をcommitできる

対象 `equipment_save_transaction.gd:97–108,319–329,392–414`、依存先 `game_session.gd:509–514`。

plan cacheはabilities/jobs/source_buildだけで無効化される。一方、実旧人物検証は `session.job_progression.advanced` も参照する。独立probeは正常fixtureのparty[0].unlocked_jobsへ実advancedキーを1つ入れ、plan/prepare成功後に専用GameSessionのそのadvanced定義だけを除去した。同一raw、同一g1、同一contextで、既存T.planはok=true・候補hash不変、新規T.planはok=false/invalid_source。既存T.commitはcommitted=trueとなった。ファイルのdata定義は一切変更せず、QAの専用メモリだけを変えた。

期待：現依存で拒否される候補をcommitしない。実際：キャッシュにより検証が省かれる。通常プレイ中にこの依存変更が起きることや実ユーザー保存の損傷までは立証していない。S3の明示context・依存変更時無効化という保証の穴である。現在の検査は要求ごとにT/contextを作り直すため、同一Tの依存変更をカバーしない。

最小修正：安全性を優先するならcommit/recoverの検証をfreshにするかcacheを除く。性能上保持する場合は、validatorが実際に読む全依存（job_progressionを含む）のimmutable snapshot/revisionとcacheを結び、T構築後の変更を明示拒否する。世代文字列を呼出側が変えるはずという仮定だけで通さない。原180秒を延ばさず再実測する。同一T/fresh Tの結果一致、jobs/abilities/job_progression/source_build/session差替え、候補の型・順序差を追加QAとする。

### F4 中・受入証拠不足：実容量不足・専用別volumeが未実測

`tools/check_equipment_save_transaction.py:432` のinjected-enospcはcandidate.store.beforeで汎用injected_io_failureを返す。OSがENOSPC/ERROR_DISK_FULLを返した試験ではなく、短い書込み・flush失敗・metadata allocation失敗の保証にもならない。別volumeもstat deviceのコード調査だけで、専用nested volume上の実拒否を確認していない。これは未検証の指摘であって、未再現のデータ破損バグを断定するものではない。後述の専用環境QAが受入に必要。

## 独立実測と原証拠

公式Godot 4.7.2.stable.official.ed1daf0bfをQAへ取得した。ZIP SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実体 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。既設4.6.3とfontconfig警告は版確認時だけで、受入に使用していない。固定cloneのimport後、元wrapperを改変せず実行した。

```text
cwd=/tmp/qa054/fixed (e003b126de6695fa131e07a3db14c3011fb74f2e)
python tools/fixtures/equipment-save-transaction/run_ci.py \
  --profile fixed053 --source-sha e003b126de6695fa131e07a3db14c3011fb74f2e \
  --fixed-sha e003b126de6695fa131e07a3db14c3011fb74f2e \
  --godot /tmp/qa054/bin/Godot_v4.7.2-stable_linux.x86_64 \
  --output /tmp/qa054/independent/results
```

version 0.248秒、保護前0.017秒、clean import28.736秒、transactionコマンド61.145秒（suite内部60.786秒）、保護後0.018秒、すべてexit0/警告0。全体180秒・各子30秒・import600秒・CI15分を変更していない。wrapperは全172/2178、kill97、fault24、special51、14伝播（control0＋負13件1）、scope2（後続文書0/担当外1）を固定集合と全bytes/hash・独立phase期待で照合しPASS。保護26/26。試験workerの並列処理は既存検査の挙動であり、エージェント委譲ではない。

重点確認：通常二重writerはbusy、PID再使用は現在の実装では安全側にbusyとなるが実PID再使用は未実測。SIGKILL97地点は別process復旧で成功し、同raw別名/別raw/新版再入力、source/history/backup/output改変、hardlink/symlink、receipt破損/intent不一致/phase stale、rename後receipt失敗も原固定ケースで照合した。receiptのphaseだけを成功根拠とせず実bytesを確認する点は妥当。recoverは判定だけで、自動修復はprepare側である。追加inspect（既存committed取引からrecoverも呼ぶ）は専用root全24entryの名前・種類・size・mtime_ns・hash/link参照が前後一致、exit0/警告0。atimeの変化まで書込みゼロと主張しない。

5つの053原archiveはtar.gz全hash/sizeとmembers集合を読取り照合し、計203912 memberの全size/SHA256が一致した。hardlink memberは参照先の原bytes hashへ解決し、symlinkは参照文字列のbytesで比較。初稿はtar hardlinkを検査対象から誤って除外して集合assertに失敗したため、検査スクリプトだけを訂正し全照合した。原物は変更していない。

| 原archive | 全member | SHA256 |
|---|---:|---|
| fixed053-raw.tar.gz | 69973 | 1c9bbba57e4422055e9f984f7479dac8059c1e5bb62dcb24f7157b5a79d2f76c |
| development-raw.tar.gz | 56573 | 5268edccc97d37d2a499ca519fa54aa63360408d9f43363cabd922055265d5b4 |
| regression-raw.tar.gz | 240 | 7d56cbf60060f90cd68a58582bed842d664c16ae12d81fb52a6074abff542d09 |
| final-fixed053-raw.tar.gz | 70150 | 1af2cb17ad8315ffdf0f099fb57391665435e77e4d63d336287dcd9dbd19f33b |
| marker-race-raw.tar.gz | 6976 | c07b243010ee3f573ed19c74f399f2a8de66d94d2335ab3bb6ae1af4a9b30a06 |

最終archiveのexecution.jsonは固定e003b126・PASS172/2178/14/scope2。marker-race原物の `latest-run/qa/kill-source.store.before/paused.json` は実0bytesだった。過去失敗と初回成功を最終受入へ混ぜていない。原ログはarchive全member照合で内容同一性を確認し、全ログの人手逐語レビューをしたとは述べない。

今回追加証拠は提出制限によりcommitせず、この報告に再現法と主要hashを残す。原ログ・全case・専用QA原物は `/tmp/qa054/` に保持。主要SHA256：

| 今回のファイル | SHA256 |
|---|---|
| independent/execution.json | f6e22b048fbac37183abaafe2816538ac954b879efd8c8413519cdd89e4c7656 |
| independent/results/sha256.json | d823569e9fff8044adc564a821ce11ca0d34b9895305313659565c782402a533 |
| extra2.gd | ce929921f00899be992b4ebadbefbf04279a3101c49125e6a6aff0f3a09b6b4b |
| extra2.log | a6126b8653ddfc9dcb3291bdccd65e11b35fe1d7160a5f9614d7833ee4668584 |
| two_writers.py | 025e9675eedf03f5298b9b64624541f3eeaa40b26fe599e1de2ecf0a83b50123 |
| two-writers/summary.json | d578173521396b932864a9fbd566af0edb938090748b5926c50213ab425675df |
| readonly.log | 3ef5dcde0e596c8a369696455d85adb2f87b9ec0c450c9ea7cd7687c2937edbe |

## 追加回帰の独立実行

固定QA clone、同じ公式Godot/隔離XDGで以下を実行。全exit0、SCRIPT ERROR/ERROR/WARNING/Parse Errorなし。run_locked_checksの内部各verify300秒はそのまま、外側900秒以内。装備240秒、S1/S2/旧比較/素材120秒、保護30秒。原assert/期待/予算を変更していない。

| コマンド | 実秒 | 結果 |
|---|---:|---|
| `python tools/run_locked_checks.py` | 71.075 | R-01〜08すべてPASS、tests_ran=true/parser_failed=false |
| `godot --headless --path . --script res://tools/check_equipment_rules.gd` | 0.325 | 5394＋93条件、400切替 |
| `godot --headless --path . --script res://tools/check_equipment_save_migration.gd` | 8.697 | 61/2828 |
| `godot --headless --path . --script res://tools/check_equipment_save_codec.gd` | 7.120 | 154/975 |
| `godot --headless --path . --script res://tools/fixtures/equipment-save/legacy_equivalence.gd` | 1.477 | 142検証/10更新 |
| `python tools/validate_assets.py --strict` | 4.703 | 問題0 |
| `python tools/check_frozen_files.py` | 0.023 | 26/26 |

旧比較raw JSON SHA256 `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` は既存原証拠の値と一致。旧異常定義202件のローカル再実行と手動legacy-campaign workflowは今回未実施で、対象/提出CIの既存jobとは区別する。

## Windowsの最小技術案（未実装・未実測）

Godotの公式4.7.2 [FileAccess定義](https://raw.githubusercontent.com/godotengine/godot/4.7.2-stable/doc/classes/FileAccess.xml)には指定名のCREATE_NEW/O_EXCLがなく、WRITEは既存を切り詰める。[DirAccess定義](https://raw.githubusercontent.com/godotengine/godot/4.7.2-stable/doc/classes/DirAccess.xml)のrenameは既存宛先を上書きし得る。mkdirによる排他作成自体は利用できても、死亡後の所有権回収・全ファイル操作の安全性までは構成できない。create_linkのWindows使用には特権または開発者モードが必要。[OS.is_process_running](https://docs.godotengine.org/en/stable/classes/class_os.html#class-os-method-is-process-running)の契約はcreate_processで生成した子PIDで、前回起動のownerの一般的照会には使えない。Godot公開APIだけにはvolume ID・link count・handleに基づく一連のI/Oを揃える入口がない。標準APIの組合せだけで全契約を満たせるとは判断しない。

| 選択肢 | 評価 |
|---|---|
| GDScript標準APIだけ | 排他mkdirは可能でもno-clobber rename/任意owner/volume・hardlink照合が不足。存在確認→WRITE/renameへの置換は競合窓を残すため不採用 |
| 内部GDExtensionの小さいI/O層（推奨案） | ゲーム規則・codec・phase判断はGDScriptのまま、OS primitiveだけ同一process内へ集約。lock寿命がゲームprocessと一致する。DLL/SO・ビルド工程・nativeコードの承認が必要 |
| 同梱native helper executable | engine ABI依存を減らせるが、IPC、親死亡監視、helper残存、lock/書込みprocessの分裂、配布物が増える。最小案としては拡張より不利。PowerShell/.NET/外部GNU導入を暗黙前提にしない |

以下は公式APIから導いた設計案でありWindows動作保証ではない。

1. `open_root/resolve/inspect_identity`：許可QA rootのdirectory handleを保持し、各成分を検証する。WindowsはCreateFileWのFILE_FLAG_BACKUP_SEMANTICS/OPEN_REPARSE_POINTを使い、reparse point（junction/mount含む）は拒否。GetFinalPathNameByHandleWでroot外を拒否し、GetFileInformationByHandle(Ex)でvolume/file ID/link数を取得する。文字列lowercaseやdrive letterだけの一致をidentityとしない。rootとsource/取引は同volume、sourceと出力は別file ID、書込み対象hardlinkは拒否。Linuxはdirectory fd基準のopenat/fstat/O_NOFOLLOW等で同じ結果へ写像する。検査後に文字列で開き直す設計は避ける。
2. `try_lock_transaction`：専用lockファイルは残し、Windows LockFileExの非待機排他lockをhandleで保持。Linuxは対応するkernel lockを使う。process終了でOSが解放するためPID再使用だけで所有権を譲らない。unknown/アクセス拒否は失敗。PID/nonce/開始時刻は監査用、必要ならGetProcessTimesのcreation timeで照合する。inspect/recoverはlockやownerファイルを作らない。元053のsymlink leaseは破棄せず、既存取引の移行互換QAを別に持つ。新旧writer同時稼働は旧writerが新lockを見ないため安全保証できず、混在起動防止も実装課題として明示する。
3. `create_exclusive/write_exact/flush/close/readback`：Windows CreateFileW(CREATE_NEW)で既存を絶対に切り詰めず、部分書込み・GetLastError・FlushFileBuffers失敗を返す。再利用tmpは取引所有権・file ID/link数を再検証してからのみ開く。Linux O_CREAT|O_EXCLと同等にする。raw backup/型/全値/hash/数量/履歴判定は現GDScriptを保持。
4. `rename_new`：Windows SetFileInformationByHandle(FileRenameInfo, ReplaceIfExists=FALSE)を候補とし、実handle/同volumeを確認する。MoveFileExWを使う場合もREPLACE_EXISTING/COPY_ALLOWEDを使わず、copy+delete fallbackを設けない。Linux renameat2(RENAME_NOREPLACE)等の実primitiveを使う。既存targetはbytesが同じでも勝手に置換しない。receiptだけは元契約どおり所有済みtempの置換専用APIに分ける。rename成功後はreceipt失敗とcommit成功を別結果にする。
5. 既存の各boundary hookを新層の実操作の前後へ接続し、97地点を黙って削らない。kernel lock化で内部owner方式が変わる場合は旧053全assertを固定側に保持し、最新の同じ単一writer不変条件と新primitive境界の対応表を作る。新APIのエラーを既存reason_codeへ写像し、成功点・migration_id・出力形式・数量・適用falseは不変。F2/F3も同じ修正件へ含める。

根拠：[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)、[LockFileEx](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex)、[GetFinalPathNameByHandleW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew)、[file identity/link数](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information)、[FILE_RENAME_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info)、[MoveFileExW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw)、[FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)、[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)。lock解放は終了直後の即時完了を仮定せず、既存予算内でbusyを再確認する。file flushとdirectory/媒体全体の電源断保証は別である。

必要パス案：既存 `scripts/game/equipment_save_transaction.gd`、新 `native/equipment_save_io/{src/,SConstruct}`、新 `addons/equipment_save_io/{equipment_save_io.gdextension,bin/}`、新 `tools/fixtures/equipment-save-transaction-platform/` と専用runner、新 `.github/workflows/equipment-transaction-platform.yml`、修正件の報告/証拠。既存S1/S2公開API・通常UI・ゲームdata・保護検査は変更しない。現在wrapperのOS依存（SIGKILL/負exit、os.geteuid、POSIX permission、Linux実体hash）をWindows成功へ偽装せず、同じ期待集合を使うOS adapterを別途用意する。旧wrapper/fixture/hash固定は維持する。

配布/ビルド：4.7.2対応godot-cppの完全commit/ライセンスを固定、Python/SCons・MSVC Build Tools＋Windows SDK、Linux C++ compilerでx86_64 debug/releaseを構築しDLL/SOと.gdextensionを同梱する案。Godot公式[拡張ビルド手順](https://docs.godotengine.org/en/stable/tutorials/scripting/cpp/gdextension_cpp_example.html)を参照。拡張hash・依存表・コンパイラ版を記録し、ロード失敗/欠落時はfail-closed。配布先PCへの追加開発環境・特権・設定変更を要求しない。nativeを最小化するC API案ならgodot-cppは省けるがbinding保守が増える。いずれも今回は導入しない。

**承認境界**：保存契約を弱める必要はないが、GDScript固定のAGENTS第1節の下でnative言語・配布物・ビルド工程の追加を黙って実施できない。親は「ゲーム実装はGDScriptのまま、限定内部I/O拡張だけ」の例外と具体パス、新CI追加を次依頼で明示承認する必要がある。保護・既存検査の変更は現案では不要。必要になった場合だけ具体差分を別承認へ戻す。これは提案の採否事項で、本レビューの作業を止める確認依頼ではない。

## 必要なQAと未実測の解消

Windows実機/専用VMで公式Godot4.7.2、標準ユーザー、Developer Mode無効、追加GNUなし、まずlocal NTFS上の専用rootで行う。Linux固定053と最新Linuxは原172/2178・97 SIGKILL・14伝播・scope2を保持。Windowsは同じ論理全ケース/全assertを実行し、97地点それぞれ実プロセス強制終了→wait→別PID復旧を観測する。WindowsをSIGKILLやexit=-9と呼ばず、TerminateProcess/Popen.killの実結果を別欄に保存する。原phase期待・raw bytes/型/値/順序・12/22個/重複0・input/state/metrics不変、全子30秒/全体180秒/import600秒/job15分は維持。予算不足は失敗として返す。

追加QAは新件数を別固定し、旧件数の水増しに混ぜない。F2の生存owner＋照会unknown、同時lock獲得、強制終了後解放、PID再使用相当の開始時刻不一致、F3同一T依存変異、inspect/recover前後の全root不変、原receiptとbytes矛盾、targetの直前競合、hardlinkの直前作成、元ファイル差替えを実行する。パスはdrive/case別名、UNC、長いパス、非ASCII、空白、末尾dot/space、予約device名、ADS、reparse/junction、root接頭辞だけ同じ別dirを正負に分け、正規化で別物を上書きしない。未対応FSを正常成功扱いせず、Windows全FS保証とも呼ばない。配布binaryの実export/headless QA起動・拡張欠落/改変拒否も必要。通常UI接続はS5まで行わない。

実ENOSPCは**事前提供済みの小容量専用volume**を持つ使い捨てQA VM/runnerで行う。Linuxの専用ext4/tmpfs等、Windowsの専用固定容量NTFS VHD等を環境管理者が準備し、対象ファイルだけで実allocationを消費する。ユーザーPC/共有volumeを埋めない。生成する充填fileは専用試験データで、sparseだけで残容量を偽らず、free bytesとwrite/store/flushの実OS errorを記録する。source/履歴/backupをvolume内に配置し、open・途中write・flush・rename/receipt metadataのどこで不足したかを区別する。rename後不足でもcommitted=trueを保持し、別process復旧でraw/数量/phaseを確認する。注入だけのケースも並行して残す。容量は全体の正例/負例が走る範囲であらかじめ設計し、成功のために予算を延ばさない。

実別volumeはQA root内に事前用意したnested mountと、同一volume対照のvolume/file IDを原証拠に取る。Linuxのst_dev不一致による拒否、Windowsの別volume/reparse拒否理由を分け、APIのdevice比較自体も別handleで検査する。単なる外部symlink拒否を別volume分岐の実証としない。backup/target/sourceを各配置した正負例でroot外や別volumeに書込み0を確認する。Windowsのnested volumeがreparse拒否で止まることと、volume ID比較の実証を混同しない。

mount/VHD attach/ACL設定を要する準備は通常管理者権限が必要で、今回のOS設定変更禁止範囲では実施しない。既に準備済みの領域を標準ユーザーが利用するか、別途専用環境の準備権限を明示した次依頼を必要とする。単なるRLIMIT_FSIZEや同一volume上の別directory、注入を実ENOSPC/実別volumeと呼ばない。現環境では実Windows・実ENOSPC・専用別volume・PID再使用そのもの・敵対的directory TOCTOU・停電/媒体故障は未実測。S4/S5、実ユーザー保存、通常UI・通常運用記録への接続も未実施である。

## 対象CI・提出境界

GitHub jobs APIで対象10de1ffの053branchに限定し、push39＋PR39の全78jobがcompleted/success、ページのtotal_countと取得件数一致を確認した。同SHAの054branch作成時の別pushは除外した。gh CLI APIはForbiddenだったため接続済みGitHub read-only APIを使った。

| workflow | push run | PR run | 各job数 |
|---|---|---|---:|
| CI | [37851424358](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851424358) | [37851431561](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851431561) | 3 |
| 006固定受入と最新回帰 | [37851424310](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851424310) | [37851431540](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851431540) | 17 |
| Equipment and Save CI | [37851424299](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851424299) | [37851431513](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851431513) | 14 |
| Equipment Codec CI | [37851424335](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851424335) | [37851431616](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851431616) | 3 |
| 保存I/O・中断復旧 | [37851424307](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851424307) | [37851431498](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37851431498) | 2 |

054は新PRを作らず指定branchへ報告だけをcommit/pushする。自己SHAの再帰更新を避け、最終完全SHA・同一SHA全CIの終了・clean/未push0は最終応答で記録する。053受入、main反映、修正実装は行わない。親に必要な判断は (1)F1〜F3の修正依頼と限定native I/Oの承認、(2)Windows/実容量不足/別volume用の専用環境の手配である。

## 追加probeの再現コード

次をQA外部scriptへ保存し、固定checkoutを `--path` に指定して実行する。本番ファイルは変更しない。rootは未使用の専用パスとし、同一rootでの再実行結果を初回と混同しない。事前にQA shim/psを実行可能な2行 `#!/bin/sh` / `exit 2` として作り、XDG3変数もQAへ隔離する。Godotコマンドは `timeout 30 /tmp/qa054/bin/godot --headless --path /tmp/qa054/fixed --script /tmp/qa054/extra2.gd`。実exit0/警告0。最初のextra.gdはplan比較まで、下記extra2.gdがcommitまでの確認である。

```gdscript
extends SceneTree
const T=preload("res://scripts/game/equipment_save_transaction.gd")
const F=preload("res://tools/fixtures/equipment-save-codec/fixtures.gd")
func _initialize():
 var root="/tmp/qa054/extra-root-v2"
 DirAccess.make_dir_recursive_absolute(root)
 var a=T.new(root,{},"g1")
 var b=T.new(root,{},"g1")
 var tx=a.transaction_path("a".repeat(64))
 var first=a.acquire(tx)
 var control=b.acquire(tx)
 var old=OS.get_environment("PATH")
 OS.set_environment("PATH","/tmp/qa054/shim:"+old)
 var uncertain=b.acquire(tx)
 OS.set_environment("PATH",old)
 print("LEASE ",JSON.stringify({"first":first,"normal_second":control,"ps_exit2_second":uncertain,"first_still_owned":a.owned==tx,"second_owned":b.owned==tx,"live_pid":OS.get_process_id()}))
 var s=GameSession.new()
 var ctx={"legacy_session":s,"abilities":s.catalog.equipment_context_abilities()}
 var document=F.region()
 var id=s.job_progression.advanced.keys()[0]
 document.party[0]["unlocked_jobs"]=[id]
 var raw=JSON.stringify(document,"",true,true).to_utf8_buffer()
 var t=T.new(root,ctx,"g1")
 var initial=t.plan(raw)
 var file=FileAccess.open(root.path_join("source.json"),FileAccess.WRITE)
 file.store_buffer(raw);file.close()
 var prepared=t.prepare(root.path_join("source.json"),T.hash_raw(raw),initial.document,"g1")
 s.job_progression.advanced.erase(id)
 var cached=t.plan(raw)
 var fresh=T.new(root,ctx,"g1").plan(raw)
 var committed=t.commit(initial.token,"g1")
 print("CACHE ",JSON.stringify({"initial_ok":initial.ok,"prepared":prepared.ok,"committed":committed.get("committed",false),"cached_ok":cached.ok,"fresh_ok":fresh.ok,"fresh_reason":fresh.get("reason_code"),"cached_unchanged":cached.get("sha256")==initial.get("sha256")}))
 quit(0)
```

別processのF2再現は、上記で作ったsource.jsonを専用rootへコピーし、未変更053 probeを呼ぶ以下のPython。正常対照busy、障害注入後committed、先行owner_alive=trueを実測した。初稿で存在しないnormal/source.jsonをコピー元に指定しFileNotFoundErrorとなった後、実在する専用extra-root-v2/source.jsonへ訂正した。初稿ではGodotを起動していない。

```python
import os,subprocess,json,time,shutil,hashlib
from pathlib import Path
root=Path('/tmp/qa054/two-writers');root.mkdir(exist_ok=True);shutil.copy('/tmp/qa054/extra-root-v2/source.json',root/'source.json')
env=os.environ.copy()
for k in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME']:env[k]='/tmp/qa054/xdg/'+k
cmd=['/tmp/qa054/bin/godot','--headless','--path','/tmp/qa054/fixed','--script','res://tools/equipment_save_transaction_probe.gd','--']
base=dict(root=str(root),operation='full',generation='g1',session_token='g1')
(root/'a.json').write_text(json.dumps(dict(base,kill_point='lease.acquire.after',result='a-result.json')))
(root/'b.json').write_text(json.dumps(dict(base,result='b-result.json')))
with (root/'a.log').open('wb') as log:
 a=subprocess.Popen(cmd+[str(root/'a.json')],env=env,stdout=log,stderr=subprocess.STDOUT)
 try:
  deadline=time.monotonic()+15
  while not (root/'paused.json').exists():
   assert a.poll() is None and time.monotonic()<deadline
   time.sleep(.01)
  mark=json.loads((root/'paused.json').read_text());assert mark['pid']==a.pid
  normal=subprocess.run(cmd+[str(root/'b.json')],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
  (root/'control.log').write_bytes(normal.stdout);control=json.loads((root/'b-result.json').read_text())
  env['PATH']='/tmp/qa054/shim:'+env['PATH']
  b=subprocess.run(cmd+[str(root/'b.json')],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
  (root/'b.log').write_bytes(b.stdout);result=json.loads((root/'b-result.json').read_text())
  summary=dict(owner_pid=a.pid,owner_alive=a.poll() is None,control=control['reason_code'],second_pid=result['pid'],second_exit=b.returncode,second_committed=result.get('committed'),second_phase=result.get('phase'))
 finally:
  (root/'release').write_text('release own QA process');a.wait(timeout=30)
 summary['first_exit']=a.returncode
 (root/'summary.json').write_text(json.dumps(summary,indent=2));print(summary)
```
