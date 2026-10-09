# 057 保存QAログ保持・時間内訳の報告

## 作業前の計画

開始HEADは878c2316a4c9e72b253f7df001b6c6438ef7cb6d、基点849d02bd2ea4dd44298eef225fe9a12927858d1b。開始dirty・指定branch未pushは0。追加AGENTSとcheckout/workspaceの関連SKILL.mdは存在しない。追加委譲なし。

最小変更は専用platform driver、fixture内process記録/helper・057 scope checker・計測wrapper・機械検証、および専用workflowの診断/証拠step。055 scope許可prefix、固定SHA/原期待/契約を変更しない。

F5は出力後に待機する専用子を使い、実30秒timeout・174秒残量枯渇・外180秒経路・並行worker例外・親例外・正常/異常exitを区別する。stdout/stderrを起動時からfileへ保持し、PID/argv/UTC/monotonic/exit/timeout/deadline/kill/waitをfinallyに保存。queue/batch一意IDとroot完了を記録し、終了時に受付停止・未完future拒否・子kill/wait・worker joinを元180秒内で行う。回収不能は未回収の理由として残す。

Windows/Linuxは同じ専用CIの最新profileへ診断を追加し、既存8jobと固定版checkout/command/予算を保持する。実関数へ同一引数を渡すGDScript wrapperでseed6種、起動/依存、plan/verify、plan内部各段階、native I/Oを計測し、同seedの計測なし対照と比較。queue/snapshotは全取引側で観測する。診断sampleは172/2178・97kill受入と区別。原log/raw archive・member hash/索引を新057証拠へ保存しGit blob/API artifact digestと区別する。

## 提出の位置づけとSHA

**未達を含む提出。F5修正・診断の提出であり、保存機能全体の受入完了／S3完成ではない。** F1時間未達とF4未実測が残る。最終文書HEADの完全SHA・全CI終了・clean/未push数は提出応答で確定する（自身のcommit SHAは文書内へ自己固定できない）。

最終修正コードは **3cf4b6c293f6796220b43cf566f8eb792c3932ec**。[固定SHA](../../verification/task057-save-qa-diagnostics/code-fixed-sha.txt)と[code inventory](../../verification/task057-save-qa-diagnostics/code-inventory.json)にGit blobとraw SHA-256を分けて保存。初回CI計測HEADは21d6a66dfc9e3b1d17a90e4a53252a23fb847b48（コード97e09a9dbaad8596b4f97e148fa6a4c1196f09a2）、queue補完後のCI計測HEADはf6d56972c8b0f455866632c48d8c05c411be2ace（コードb4ee1ea28864fc2a081647b063ef1b11030d9fec）。これらの結果を最終コードの全取引成功へ流用しない。

最終点検で、停止中にdequeueされ子未起動の要求にも終了記録が必要と判明。b4ee1eaの保存済みshutdown証拠は8要求中4要求で記録欠落だった。3cf4b6cで補完し、全queue要求の記録を要求するassertionを追加した。最終12検証はこの補完後。

## 変更と保持

Suite.run／run_restart_batchとrun_ci.pyは子stdout/stderrを起動時からfileへ保持し、例外・timeout・境界killでもfinallyで終了記録を確定する。PID、実argv、UTC/monotonic開始・終了、exitまたは未取得理由、timeout種別、deadline残量、kill/wait成否、log hashを保存する。

RestartBatchは投入・dequeue・batch開始・worker終了・future完了・root結果を記録する。共有batchの原log/実行記録は一意、root logは同じbytesの投影。停止時に受付停止・未完futureの明示失敗・子kill/wait・worker joinを元180秒内で行う。子未起動ならPID/argv/exit/logはNone、既知batch IDと未起動理由を残す。worker/子が未回収なら成功にしない。

追加helperはprocess_capture.py、capture_fixture.py、test_capture057.py、scope057.py、diagnostic_ci057.py、diagnostics057.py、diagnostic_sample.gd／diagnostic_transaction.gd／diagnostic_io.gd（専用uid含む）。実関数へ同じ引数を渡し、T.plan本文が計測forwarding以外に同一であることも照合。cache復活・検証省略なし。専用workflowにlatestの診断stepと057 SHA取得だけを加え、既存8job・コマンド・15分上限を保持した。

固定053 e003b126de6695fa131e07a3db14c3011fb74f2e、固定055 0a44409c99b06569b9e6088ffeb46c2238c821fa、旧固定SHA／inventory／期待／recovery-phases／契約／055 scope prefixは不変。別057 checkerの後続文書正例exit0・担当外code負例exit1・担当外固定差分負例exit1が成功。

本番scripts、native、addons、data、保護、原053/055証拠等541ファイルのGit blob一致を[不変inventory](../../verification/task057-save-qa-diagnostics/unchanged-inventory.json)へ保存。元archive21本・258948 memberのraw hash／サイズ／索引集合を全照合。過去証拠は上書きしていない。生成された担当外uid2本はcheckout外へ移しcommitから除外した。

## F5 再現前／修正後

登録版run_restart_batchへ専用の出力後35秒待機子を渡した実30秒再現は30.032608492秒でTimeoutExpired、log0・終了記録0。元driver bytesが登録SHAのblobと同一であることも照合。この子は保存取引の代替ではない。

最終コードのLinux実子検証12件は成功。正常、子exit3、親例外、強制kill、実子30秒timeout、内側締切、起動失敗、Suite.run内親例外、並行batch正常、worker例外、停止時active/future、外側timeoutを区別。実30秒は約30.002秒。内側/外側の分岐fixtureは0.2秒への縮尺で、実174/180秒timeout検証の成功とは書かない。外側のbudget消費後wait未取得はNone/理由付きで保持する。

Windowsのf6d5697 CIも12件成功（実子30秒30.016秒）。最終コードで強化したdequeue未起動assertionは最終文書HEADの同じCIで再実行される。補完後Linux停止fixtureでは8要求全てに終了記録、未起動4要求は架空のlog/PID/exitを作らず理由を保持。

f6d5697のローカル全取引は87件／1297条件、suite174.271632秒、wrapper174.800817秒・exit1、175queue要求・live worker0・未回収process記録0。初回85件／1263条件・174.242294秒の失敗も別archiveで保持。3cf4b6cの全取引は最終文書HEADのCIと区別する。実argv・秒数・exitは各原archiveのcommands/process JSONに保存。

```text
python tools/fixtures/equipment-save-transaction-platform/test_capture057.py --output /tmp/qa057/capture-final-dequeued
python tools/fixtures/equipment-save-transaction-platform/scope057.py --code-sha 3cf4b6c293f6796220b43cf566f8eb792c3932ec --source-sha 3cf4b6c293f6796220b43cf566f8eb792c3932ec --self-test --output /tmp/qa057/scope-completed-code.json
python tools/fixtures/equipment-save-transaction-platform/run_ci.py --godot /tmp/qa057/engine/Godot_v4.7.2-stable_linux.x86_64 --output /tmp/qa057/local-code-final/results --source-sha f6d56972c8b0f455866632c48d8c05c411be2ace --fixed-sha 0a44409c99b06569b9e6088ffeb46c2238c821fa --profile latest
D:\a\_temp\native-evidence\bin\Godot_v4.7.2-stable_win64.exe --headless --path D:\a\RPG-maker\RPG-maker --script res://tools/fixtures/equipment-save-transaction-platform/diagnostic_sample.gd -- D:\a\_temp\native-evidence\task057\measurements\typed-on on
```

## Windows/Linux 実測

計測時HEADの全CIも終了を確認した。初回21d6a66は6workflow・47job終了、42成功5失敗（専用transaction4件と原053最新1件）。f6d5697は6workflow・47job終了、45成功2失敗（Windows専用fixed055/latest transaction）。ci-first-all-terminal.json／ci-code-all-terminal.jsonに全job数と終端metadataを保存。これは最終3cf4b6cを含む文書HEADの結果とは区別する。

同一初回HEAD21d6a66の[専用run37917741675](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37917741675)は8job終了・4成功4失敗。次表は全取引の失敗。診断12sample（6seed×off/on）成功を全172ケース／2178条件／97killへ置き換えない。

| OS / profile | 実対象SHA | 件数 / 条件 | suite秒 | wrapper秒 / exit |
|---|---|---:|---:|---:|
| Linux fixed055 | 0a44409c99b06569b9e6088ffeb46c2238c821fa | 137 / 1815 | 174.040303 | 174.661675 / 1 |
| Linux latest | 21d6a66dfc9e3b1d17a90e4a53252a23fb847b48 | 131 / 1761 | 174.162456 | 174.829585 / 1 |
| Windows fixed055 | 0a44409c99b06569b9e6088ffeb46c2238c821fa | 51 / 765 | 174.203 | 174.828 / 1 |
| Windows latest | 21d6a66dfc9e3b1d17a90e4a53252a23fb847b48 | 53 / 795 | 174.484 | 175.172 / 1 |

[f6d5697専用run37918499749](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37918499749)も8job終了・6成功2失敗。Linux fixed055/latest transaction及び両OS両profile primitivesが成功。Windows fixed055は71/1065・174.125秒、wrapper174.718秒・exit1。Windows latestは53/795・174.485秒、wrapper175.157秒・exit1、追加診断成功。Linux成功jobの原bytesは取得制限で未確認なので実測秒を推定しない。runner変動もあり、差をF5修正の性能改善とは結論しない。

環境はGodot4.7.2.stable.official.ed1daf0bf。Linux CIはAzure Linux6.17／glibc2.39、4 logical CPU・AMD EPYC7763、stat FS種別ext2/ext3、restart4／case16。WindowsはServer2025 10.0.26100、同CPU4 logical（2core）、QA D: NTFS、restart2／case8。batch最大4rootは維持。[計測JSON集計](../../verification/task057-save-qa-diagnostics/measurement-summary.json)と原JSONに環境・実SHA・時刻・回数・inclusive/exclusiveを保持。

次表は同一初回HEAD21d6a66の計測onにおける**plan内部各段階6回の累積秒**。各seedでplan6/verify5。上位plan inclusiveと下位段階を加算しない。

| seed | Linux decode / migration / prepare / encode | Windows decode / migration / prepare / encode |
|---|---|---|
| typed | .096182 / .129280 / .376810 / .496555 | .147787 / .277433 / .810323 / 1.013629 |
| plain | .081103 / .123404 / .362520 / .474674 | .136058 / .284886 / .828327 / 1.076154 |
| granted | .099845 / .136564 / .391412 / .528730 | .179302 / .312311 / .956463 / 1.219274 |
| trial-missing | .099930 / .134118 / .389202 / .511727 | .176198 / .317551 / .945314 / 1.221342 |
| trial-corrupt | .098886 / .133676 / .386950 / .510085 | .178684 / .323896 / .912554 / 1.154746 |
| trial-unclean | .099439 / .134107 / .388166 / .512672 | .161801 / .333495 / .865798 / 1.071888 |

取引wallはLinux1.293041〜1.446065秒、Windows2.782672〜3.317805秒。plan/verify union占有はLinux98.628〜98.864%、Windows98.469〜98.863%と独立実測。native binding呼出しunionはLinux.007135〜.008610秒、Windows.026262〜.036522秒でplan/verifyと重なる。kernel CPU/I/Oだけを分離した値ではない。

子ticksのinitialize入口まで（Godot起動・scriptロードを含む観測境界）はLinux約.495〜.519秒、Windows約.738〜.917秒。GameSession/context等の依存構築はLinux.297498〜.306296秒、Windows.378019〜.447833秒。native debug/release buildはLinux17.809703/17.756412秒、import61.621971秒。Windows build/importも別原JSONに保持。起動・依存・build/importを取引174秒の使用量へ混ぜない。

初回全取引queue待ち累積/最大はLinux208.026463/6.490122秒（196要求）、Windows182.826/8.079秒（136要求）。一意batch70/47、process累積621.525019/329.740秒・union167.803024/169.125秒。snapshot242/112回・累積9.047204/3.099秒・union4.527260/1.667秒。累積並行時間をsuite wallへ加算せず、root投影も再計上しない。

追加f6 Windows診断も6seed off/on全てsource/output hash・数量・memory不変で成功。取引wall2.578892〜2.957724秒、plan/verify98.496〜98.744%、native .023439〜.032227秒。debug/release build32.468/27.219秒、import95秒。queue138要求、48batch、snapshot114回・累積2.366秒/union1.302秒、live worker/未回収記録0。初回Linuxと同一HEADの比較にはしない。

全対照は入力・履歴・出力hash・数量・session memory一致。off/on各1回のsampleで性能差の統計的保証や全取引代表性は主張しない。4つの計測helperは初回21d6a66から最終3cf4b6cまで同一bytes。

## 原検査・回帰と未実施

| 検査 | 結果と根拠 |
|---|---|
| 原053固定・最新 | f6の既存run37918499832の2job終了・成功。原wrapperが各172/2178・伝播14・scope2を出力。固定e003b126…と最新f6d5697を分離。97kill期待/検査不変。初回21d6a66最新の失敗もjob snapshotへ保持。 |
| native primitive / 配布物 | f6専用primitives4job終了・成功。手元は既存extra40件94.496247秒・binary7件5.426003秒・exit0（提出済みSO、手元rebuildなし）。DLL/SO再buildと提出済み配布物の実ロードは既存両OS CI。 |
| 既存16伝播・055 scope正負 | 現validatorをhash確認済み過去正常証拠c8f22dbe4edb8ff5e4dcd699ce0887a25f9b0974へ適用。control exit0・15異常exit1・scope2件の期待exit一致、17.126710秒。現在版全取引の成功ではない。 |
| 057 scope正負 | 最終コード3cf4b6cに対する3件成功。055 prefix拡大なし。 |
| R-01〜R-08 | 隔離clone21d6a66で全成功、115.679044秒・exit0。最終コードまで本番/保護検査bytes不変。 |
| S1 / S2 / 装備 / 旧比較全文 | 同cloneで24.398378 / 15.950614 / .565451 / 2.327046秒・exit0。旧比較142/10、正常対照warning/errorなし。 |
| 保護26前後 / 素材 | 26/26・before/after成功。素材strict9.821217秒・exit0。f6専用CIのalways保護照合も8job成功。 |
| F4実ENOSPC・nested別volume | **NOT_RUN**。注入は実容量不足の実測ではない。mount/VHD/ACL/共有disk充填/新環境起動なし。 |

最初の手元importはexit0だが、生成uidを先に移したためcacheのmissing UID warningが出て原warning拒否で失敗。uidを戻してimportから再実行し、失敗ログも保持。warning無視なし。手元全取引と証拠圧縮の一部は同hostで重なったため、そのwallはOS間性能比較に使わず独立CI値を使う。

## 永続証拠・取得制限

[証拠README](../../verification/task057-save-qa-diagnostics/README.md)、[全archiveと完全hash](../../verification/task057-save-qa-diagnostics/archives.json)、各*-members.jsonが入口。raw hash・サイズ・索引集合を再展開照合。元053/055は[元archive照合](../../verification/task057-save-qa-diagnostics/original-archive-audit.json)を参照。

| 原証拠archive | raw SHA-256 |
|---|---|
| 最終F5 capture | c9907c4bfcc56b079bbcaedf0d07633813ce543cb58e037149f84f22376904e9 |
| 初回Linux latest CI | 6bcf577b653209f9afe12de38d8c42d586448b78a040b43309b8badfa984cdf3 |
| 初回Windows latest CI | b17530a2c926db433f37c49fdeb3f8f34aebaccb84cc33574f1230c608fdb1ce |
| f6 Windows latest CI | 39ae0cd2c1d70385936bb0b13eee645aca80fe59018a764ae33ce418c6b46d37 |
| 手元f6全取引失敗 | 562bc25fcd3c9456521f4998ce0d011629901fe5238e290f706be8cf0ad16d12 |

API artifact digestはZIPのAPI値として別JSONに保存。connector downloadはfile refを返したが、ローカル取得はproxy CONNECT403で失敗しZIP bytes/hash未確認。取得できたdecoded job log内base64からCI原archiveを復元し、宣言hash/bytes/member数・全member・取引manifestを照合。decoded UTF-8 log hashはGitHub生log bytes hashではない。

f6のLinux fixed/latest transactionとWindows latest primitivesのjob log取得はconnector Transport closed（再試行も同じ）。そのjobのraw log/埋込みarchive/実測秒数は未確認。成功step metadataと初回原bytesを混同しない。[取得制限・来歴](../../verification/task057-save-qa-diagnostics/acquisition-and-provenance.json)、[専用8job終了記録](../../verification/task057-save-qa-diagnostics/ci-code-platform-terminal.json)、artifact metadataを保存。制限の迂回なし。

## 残件と次の最小案

F5は捕捉できる例外/timeoutと未起動queueの終了証拠を補完した。最終コードの全CI終了・Windows強化検証は提出応答で確認する。F1はWindows及び手元の予算未達が残り、F4は未実測。

次の最小案は別依頼・別承認で **scripts/game/equipment_save_codec.gdのencode_candidateとscripts/game/equipment_document_validation.gdのprepare_candidate内部を更に観測し、重複する純粋構築/検証の実箇所を特定する**こと。その後、同一引数・全拒否条件・型/値・候補hashを維持する局所変更案をレビューする。sampleだけで検証削減・cache復活・native化・時間延長を決めない。今回は本番パスを変更せず、ルッカの受入判断待ち。
