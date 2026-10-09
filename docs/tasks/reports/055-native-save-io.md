# 055 保存専用native I/O 実装報告

未達を含む実装提出。コード固定SHAは `adbd4b1b1fde34a0fa8f5a48388571e25e996eb3`。Windows/Linuxの固定055／最新専用8jobと最終SHA全CIの終了結果は、同一SHAのActions原記録と最終応答で確定する。全受入済みとはしていない。

基点は登録b17f2b475ff8c58924720ea24cce8f205422c50b、054提出71908a13bcf704287fbc653ca307c504b4bc7f08。指定branch `codex/task-055-native-save-io` で作業し、Gitの実read/push、公式Godot4.7.2とcompilerの実アクセスを確認した。ゲーム本体はGDScriptのままで、通常UI・実ユーザー保存・S4/S5には接続していない。新PR・main反映・merge・強制push・削除・追加委譲・別実行環境の起動は行っていない。

AGENTS、054報告全文・055依頼、040依頼／報告と装備保存統合計画、053依頼／報告・実コード／検査／証拠、S1/S2と実validator依存、素材規約と既存企画の関係を確認した。repoの追加AGENTS／.agents/skillsはなく、workspaceの.agents/.codexに必要なローカルskillはなかった。

## 変更

- `scripts/game/equipment_save_transaction.gd`: phase/codec/migrationと既存97境界を保持。I/Oを内部拡張へ接続し、plan/verify cacheを削除。manifest・binary・登録／初期化不正はfail-closed。Windowsの区切り文字／大小文字別名を含め取引内sourceを拒否。
- `native/equipment_save_io/`: 保存のroot・identity・kernel lock・exclusive create・write_exact/flush/close/readback・no-clobber rename。固定godot-cpp commit、公式license、狭いbinding profile、再現ビルド手順。ゲーム規則は移植していない。
- `addons/equipment_save_io/`: x86_64のWindows/Linux debug/release 4配布物、gdextension、manifest、依存runtimeのlicense。
- 今回専用runner/fixture/workflow: 原053固定を変更せず、新nativeの同じ172/2178・97中断、追加境界／F2/F3／path／identity、配布物正負、原証拠伝播16、完成SHA scope正負を独立実行。
- 今回証拠ディレクトリ、本報告、055状態行、decision-logへの追記。

既存workflow/wrapper/fixture/期待、S1/S2公開API、data/assets/原画、通常入口、保護26、test/.scope-lock、053/054文書と過去証拠は変更していない。基点からの一覧は今回証拠のchanged-files.txtに記録した。

## F1〜F3

WindowsはローカルNTFSに限定する。drive root以降のNtCreateFileのRootDirectory/OBJ_DONT_REPARSE/FILE_CREATE、reparse拒否、directory/file handleのdelete共有禁止、volume/file ID/link数照合、LockFileEx、FlushFileBuffers、NtSetInformationFileのRootDirectory/ReplaceIfExists=falseを使用。receipt.tmp→receipt.jsonだけ置換を許す。UNC/namespace/ADS/予約名（COM/LPTの上付き¹²³を含む）/dot-space/root外を拒否し、case/Unicode/空白/長いpathの正例を分ける。配布先にGNU/compiler/管理者/Developer Modeは不要。Linuxはroot fdからopenat/O_NOFOLLOW/fstat、flock、O_EXCL、fsync、renameat2(RENAME_NOREPLACE)。未確認APIへの通常WRITE/rename fallbackはない。

kernel lockを生存handleで保持し、PID/nonceは監査だけにする。OSのPID型の範囲外もunknownにし、integerの切詰めで別process/deadへ誤判定しない。Windowsのlock/identity/directoryキーはCompareStringOrdinalのcase-insensitive比較を使う。旧053 symlink leaseは確定dead以外拒否し、新regular leaseを公開すると旧053がis_link確認で拒否する。旧取引原物は削除しない。Linuxで旧live owner拒否、旧dead原物から復旧、旧writerによる新取引書込み拒否を実processで確認する。

元版F2は生存PID1810を境界で待機させ、通常対照busy、専用ps stub exit2では後発committedかつowner_alive=trueを再現した。元版F3はjob_progression変異後、同一Tだけplan=true／fresh=false、commit=true・数量12を再現した。修正後は同一T／freshがともにinvalid_sourceで、commitも拒否。control/jobs/abilities/source_build/sessionも実contextで固定期待と照合する。世代文字列の変更を呼出側へ要求して回避していない。

通常競合のno-clobberとprocess異常終了を対象とする。Linuxの名前によるrename直前identity照合を、敵対的な非協調namespaceの全race排除とは呼ばない。process kill成功から電源断・媒体故障の全耐久性は推定しない。

## ビルド・配布

godot-cpp `e83fd0904c13356ed1d4c3d09f8bb9132bdc6b77` (公式godot-4.5-stable/MIT)のABIを公式4.7.2で実ロードする。SCons4.10.0、Linux GCC14.2.0、Windows提出DLLは公式llvm-mingw20261006/UCRT/LLVM23.1.3。CIではMSVCでWindowsを再ビルドし、提出済みDLLとCIビルドDLLを別々にdebug/release実ロードする。toolchain-pins.json、build.json、binary-dependencies.jsonに完全commit／archive hash／compiler／argv／依存DLL・ELF symbol versionを保存する。

4配布物を署名DBのない状態から再コンパイルして、全て前後hash一致を確認した。異なるcompiler／別OSのビルド間で同一hashを主張しない。保護export設定は変更していない。配布時はaddons/equipment_save_io全体とlicenseが必要。QAのmini projectでheadless debug/releaseの実ロードを検査し、通常ゲームのexport配布・UI保存へ接続したと報告しない。

## 検査・原証拠

公式4.7.2.stable.official.ed1daf0bfを使用。Linux ZIP cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4、exe 8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e。Windows ZIP731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953。Windows本体exeを直接起動し、TerminateProcess exit1／engine PIDを測る。console wrapperがCreateProcessすることは[公式source](https://github.com/godotengine/godot/blob/4.7/platform/windows/console_wrapper_windows.cpp)で確認した。SIGKILL exit-9とは区別する。

原053のe003b126de6695fa131e07a3db14c3011fb74f2eを元workflowで保持する。最新は独立コピーの同一bytesの期待／phase集合を使用し、Windowsのnonroot-permissionだけ専用readonly fileの実write_failedへ写像する。Linuxは従来0500/backup_failed。ACL/OS設定は変更しない。全体180秒・子30秒・import600秒・job15分を維持。完走失敗で後続検査が消えるのを避けるため、全取引jobと追加primitive/配布物jobを独立に置いた。後者の成功は172件の成功の代わりにしない。件数・期待・warning拒否・failure伝播を弱めていない。

最終の保存・build・論理検査コードc8f22dbe4edb8ff5e4dcd699ce0887a25f9b0974では172/2178・97killが154.692秒（外側command155.127秒）、追加40ケース64.334秒、配布物正負7ケース4.013秒、改変伝播16・scope正負2・source前後照合を通過。固定adbdとの49pathの差は証拠archive helperとCIの固定commit明示fetchだけで、保存・build・検査・配布物47pathのGit blobは等しい（local-code-equivalence.json）。Windowsの追加固定集合は54ケース。開発時Linuxの156.803/154.189秒・追加38ケースの記録も成功世代を分けて保持する。途中に専用runnerを改訂した開発runは、最後の実source/Git blob不一致で正しく失敗しており、完成SHAの受入証拠へ数えない。初期ビルドprofile不足、LLVM宣言不足、Windows Python文字コード、console wrapper PIDの失敗と修正を分けて保持する。

既存回帰の実argv／秒数／exit／log hashはdevelopment-raw内のregression/commands.json。import、保護26前後、run_locked_checks.py (R01〜R08)、装備、S1、S2、旧比較142/10全文、validate_assets.py --strictが全てexit0、検査ログにSCRIPT ERROR/ERROR/WARNINGなし。

過去053の5 archive全raw hashと全member（file/hardlink/symlinkの参照bytesを含む）を照合した。original-evidence-check.jsonにGit blobを別欄で保存。新raw archiveも全member hashで検証し、欠落／空／改変／件数とlog同時偽装／manifest再hashを実子exitで拒否する。artifact取得制約に備え専用job logにも同じarchive bytesを保持し、復元hashを一致させる。負例の全正例copyはarchiveから除き、baseline原bytesとnegative-deltasの変更bytes/削除一覧で各原物を再構築可能にする。失敗原物は成功原物と別名で保存する。

原証拠の入口は今回証拠のREADME.md。初期失敗・ローカル成功・未達の9 archiveを全memberまで再照合した。後続CI artifactのID／GitHub側digest／期限とjob原記録はci-observations.jsonに保存する。大きいprimitive job logはconnectorのTransport closed、artifactの署名URLは実行環境のproxy CONNECT403により、後続原bytesをローカル取得できていない。GitHub側digestをローカルraw検証済みhashとは扱わない。後続artifactはActionsに残るため、独立レビューで同じIDの原物を取得できる。

latest側がscope参照する完成commitを明示fetchするよう新workflowを修正した。旧workflowのshallow checkoutでは参照commitの取得が明示されていなかった。修正前latest primitiveの失敗原因は大きい原logが未取得のため未確定であり、この変更だけで修正成功を断定しない。ローカルのshallow再現試行は参照commitが既に存在して想定条件を再現できず、成功証拠には数えない。

## F1の予算未達、F4・残事項

全172件を180秒以内で完走する専用CIは未達。初期Windowsはconsole wrapperと本体のPID差も失敗原因だった。公式本体exeへ修正後は早期kill/restartの15条件と実終了exit1を確認したが、815 Windowsは45件/675検査・174.187秒、ede Windowsは50件/750検査・174.187秒で停止。Linux CIも815で116件/1626検査・174.082秒、4388で107件/1535検査・174.053秒、edeで117件/1635検査・174.081秒。ローカル通過でCIの予算未達を代用しない。2並列×4再開を1並列×8へ変えた実験は悪化し、元構成へ戻した。検証cacheは削除したままで、予算延長・件数減・skip・continue-on-errorをしていない。F1を全受入済みとはしない。

実ENOSPCと専用nested別volumeは **NOT_RUN／未解消**。workspaceは32GB overlay、tmp/shmは約9GB tmpfsで、提供済みの隔離小容量volume／専用nested volumeは見つからなかった。これら共有領域を埋めていない。mount/VHD attach/ACL/OS設定変更、新環境起動は行っていない。injected-enospcは注入として残し、実OS容量不足と呼ばない。

準備に必要なのは、既存の今回専用使い捨てrunner／VM内の小容量FS（write/flush/metadataが実容量不足へ到達できるもの）と、QA rootの下に置く別volumeの専用領域。親からroot/volume ID/上限容量/後片付け担当の提供・承認を受けた後、その領域だけへ書込み、free bytes・OS error・同volume対照・原bytes保持を記録する。mount等が必要なら、その準備操作の対象・影響・取り外し手順を別途提示する。ユーザーPCや共有diskの充填は提案していない。

通常UI／実ユーザー保存／S4/S5、電源断・媒体故障、全filesystem保証、通常ゲームのexport配布は未接続／未実測。親の独立再レビューへ引き渡す。最終SHA、同一SHA全CI終了、終了時clean／未push0は最終応答で報告し、自己SHAの再帰更新を行わない。

10:13 JSTの環境切断通知後、01:16 UTCにshell・repo fileのread/write・Git ls-remoteを実行し、HEADとremote a7044e61056ab1990153a686ef896225849a96e0の一致を確認した。環境は使用可能。未commitの証拠・草稿をbranchへ保全し、CI終了検証を継続する。
