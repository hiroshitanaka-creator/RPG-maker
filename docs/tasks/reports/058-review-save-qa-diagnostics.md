# 058 保存QAログ保持・時間計測の独立レビュー

判定：**差し戻し（未達を含む提出を維持）。F5は部分改善を確認したが、全面解消は不可。計測は取得できた正常sampleの範囲で妥当。F1時間未達・F4未実測は継続。** 保存機能全体の完了、S3完成、main統合可能とは判定しない。

対象057提出 `fdd6ce03c3e46cfac430930e001a383f3a7c9aec`、修正コード `3cf4b6c293f6796220b43cf566f8eb792c3932ec`、058登録 `bd52f9e8f2ebd0982fab94754cae71d35a6622d6`。057最終の指定branch・pushに限定した6workflow・47jobは全終了、42成功・5失敗。独立Linux全取引は172/2178・97killを通過したが、CIの時間未達を代用しない。

## 重大度付き指摘

### F5-a・中：子起動前の親例外で、dequeue済み要求の終了記録が欠落する

最終コードの `tools/check_equipment_save_transaction_platform.py:225` の `run_restart_batch` はconfig保存（229行）とenv準備（234行）をcaptureのtry/finallyより先に行う。ここで例外になると、workerはfutureへ例外を渡すが、子未起動のexecution記録を作らない。`RestartBatch.close:119` の補完条件は「worker_startedなし」または特定のshutdown例外文字列だけで、その他の起動前例外は対象外である。

独立反例：未存在QA rootを作り、その中の `restarted-batch.json` をdirectoryとして事前作成して、未改変Suiteの `restarts.submit(root, {root, operation:'normal'})` を呼ぶ。0.123057秒で実 `IsADirectoryError(21)`。requestはdequeue済み、batch-000000、worker_finished/future_doneあり、completed=false。close後のlive workerは0だが、**execution記録0件・recovery_complete=true**。stdoutを出した子は存在せず、ログ/PID/exitを捏造すべき状況ではない。要求に対応する未起動理由・終了記録が必要な状況である。これは正常取引が成功と偽装された証拠ではなく、終了証拠の完全性の欠陥。

再現コード（対象提出SHAの隔離checkoutで実行し、毎回未存在の一時dirを使う）：

```python
import argparse, importlib.util, json, sys, tempfile
from pathlib import Path
root = Path.cwd()
spec = importlib.util.spec_from_file_location('driver', root/'tools/check_equipment_save_transaction_platform.py')
driver = importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
out = Path(tempfile.mkdtemp(prefix='qa058-prelaunch-'))
suite = driver.Suite(argparse.Namespace(godot=sys.executable,
    fixture_root=str(out/'qa'), output=str(out/'results')))
r = suite.area/'root'; r.mkdir(); (r/'restarted-batch.json').mkdir()
try:
    suite.restarts.submit(r, dict(root=str(r), operation='normal'))
except IsADirectoryError:
    pass
assert not suite.restarts.close()
assert not list(suite.output.rglob('*-execution.json'))
assert json.loads((suite.output/'restart-queue.json').read_bytes())['recovery_complete']
```

最小修正案：同driver内でqueue要求の終了状態を起動前から所有し、config/env/capture構築例外も各rootの未起動記録へ確定する。close時は例外の文字列一致に頼らず、全受付要求と終了記録の対応を検査する。対応する反例を `test_capture057.py` に追加する。058では実装も検査も変更していない。

### F5-b・中（保証範囲）：外側強制killでは子孫回収・suite finallyを保証しない

`process_capture.py:82–102` は直接のPopenだけをkill/waitする。`run_ci.py` の外側180秒でその子のsuite親が強制終了すると、suiteのfinallyが走る保証はなく、suite配下のGodotをこのhelperが列挙・回収する仕組みもない。cleanup_deadlineを待機deadlineと同じにするため、timeout後wait(0)が未回収になることは記録上も許容されている。

独立0.2秒縮尺fixtureで、Python親が待機する孫processを1個起動してから待つ構成を実行した。外側は0.200204秒でtimeout、親kill.ok=true、wait.ok=false、exit_code=nullと理由を正しく保持した。一方、外側終了後も孫PID5366は生存していた。レビュー側が専用孫だけをkillし、直接の子をwaitして後始末した。**これは実180秒試験でもGodot取引でもない**。未回収をexit0へ補完していない点は正しいが、子孫まで回収済みという根拠にはならない。

この限界はOSが親を殺した場合にfinallyで解決できるという主張を退けるものであり、今回CIの174秒失敗で孫が残ったとする主張ではない。取得した最終057 latest両OSのqueueはlive_workers=0・unreaped_process_records=0。必要な最小案は専用runner/helperの監督範囲と残予算内の停止手順を別依頼で検討すること。予算延長は解決策にしない。

### F1継続・高：CI両OSの固定/最新全取引は時間未達

最終057の専用 [run37922713632](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37922713632) からjob原ログを独立取得し、埋込みraw archiveを復元して全memberとtransaction manifestを照合した。

| job ID / OS・profile | 実対象SHA | 件数 / 条件 | suite秒 | transaction外側秒 / exit |
|---|---|---:|---:|---:|
| 113794239756 Linux fixed055 | 0a44409c99b06569b9e6088ffeb46c2238c821fa | 132 / 1770 | 174.047047 | 174.668488 / 1 |
| 113794239880 Linux latest | fdd6ce03c3e46cfac430930e001a383f3a7c9aec | 136 / 1806 | 174.231811 | 174.946384 / 1 |
| 113794239658 Windows fixed055 | 0a44409c99b06569b9e6088ffeb46c2238c821fa | 50 / 750 | 174.203 | 174.828 / 1 |
| 113794239741 Windows latest | fdd6ce03c3e46cfac430930e001a383f3a7c9aec | 55 / 825 | 174.532 | 175.172 / 1 |

各期待は172/2178・97kill。未完を成功へ足さない。これは内側174秒の締切枯渇とfuture待機の失敗で、外側180秒やjob15分のtimeoutとは異なる。fixed055は当時checkoutの旧runnerであり、057ログ修正の成功件数へ入れない。旧runnerの「全体180秒を超過」文言も内側174秒枯渇と区別する。

旧053 latest（run37922713668、job113794239471）も失敗。取得できたjob外側ログは `TRANSACTION_CI_FAIL: コマンド失敗/警告:transaction` まで。artifact ZIP取得は403で子本文未取得のため、そのCI固有の最終原因を専用4件と同じと断定しない。

### F4継続・中：実ENOSPC・nested別volumeはNOT_RUN

今回も使い捨て小容量FS/nested別volumeの提供・環境準備を行っていない。注入、同volume別dir、原archive照合やnative primitive成功を実ENOSPC・実別volumeの成功へ置き換えない。mount/VHD/ACL/OS設定変更・共有disk充填なし。F4解消の判断は不可。

## F5改善として確認できた範囲

基点849d02bの未改変driver bytesを一時領域へ取り出し、実メソッドrun_restart_batchにstdout/stderr出力後35秒待機する専用実子を渡した。30.037070秒でTimeoutExpired、例外のpartial outputには両出力があるが、output配下のログ・executionは0件。実argvは `/tmp/qa058/old-child --headless --path /tmp --script res://tools/equipment_save_transaction_probe.gd -- /tmp/qa058/old-root/restarted-batch.json`。driverを一時位置に置いたためROOTは/tmp、子は引数を無視するfixtureで、Godot保存取引の再現とは呼ばない。

修正版の既存 `test_capture057.py` を隔離提出SHAで実行し12件成功。実子30秒は30.001649秒。正常・exit3・親例外・境界kill・起動失敗・Suite.run親例外・並行正常/worker例外・active/future停止・内/外timeoutを照合した。内側/外側の既存fixtureは0.2秒縮尺であり、実174/180秒試験の成功ではない。最終057 CIでも両OSで12件成功、実30秒はLinux30.002050秒・Windows30.000秒。

stdout/stderrの先行file保存、PID/argv/UTC/monotonic/終了code/timeout種別/kill/waitとhashの保持を確認。実際のlatest CIでLinux203要求中1件、Windows140要求中5件の子未起動記録はPID/argv/log/exitがNoneと理由付きであり、架空の成功を作らない。残るF5-aをこのshutdown正例で隠さない。

捕捉可能な例外について改善を認める。記録先自体のwrite失敗、非atomic JSON書込み途中での親強制終了、cleanup deadline後に残るworkerと収集中ファイルの競合まで、finallyだけで完全保存を保証できない。未取得記録の不存在を「未回収processなし」の唯一の証明にしてはならない。

## 計測の独立照合

`diagnostic_transaction.gd` のplan本文は計測forwardingを除いて本番と一致。decode/migration/prepare/encodeは元と同一引数/contextを実関数へ渡し、verifyはsuperへ、native wrapper14入口は実targetへ引数を転送する。cache復活・検証省略なし。本番/検査bytesも後述のinventoryで確認。

最終057 latest両OS原archiveのdiagnostics.jsonを読み、全12sampleのspanからinclusive/exclusive、plan/verify union、native unionを再計算して保存値と一致。off/onの実source・履歴・source/history backup・converted.jsonのbytes/hash集合、数量12/22、memory_unchanged=trueを照合し、候補hashと実converted.json hashも一致した。診断helperの自動対照キー自体はsource/output/quantity/memoryで、履歴hashは明示比較していないため、今回の履歴判定は独立raw照合で補った範囲である。

| 最終057 latest診断 | Linux | Windows |
|---|---|---|
| 実OS / CPU | Linux6.17.0-1022-azure / AMD EPYC7763 | Server2025 10.0.26100 / AMD EPYC9V74 |
| logical CPU / FS | 4 / stat: ext2/ext3 | 4（2core）/ D: NTFS |
| restart / case workers / batch最大root | 4 / 16 / 4 | 2 / 8 / 4 |
| 6seed計測onの取引wall秒 | 1.290304〜1.406878 | 2.378567〜2.548450 |
| plan＋verify union / 取引wall | 98.7182〜98.8763% | 98.3765〜98.6921% |
| 一意batch / root投影 | 72 / 202 | 48 / 135 |
| batch process累積秒 / union秒 | 618.095322 / 168.803553 | 329.906 / 169.327 |

queue→dequeue→worker→batch→PID/argv→各rootの記録を対応づけ、root投影logがbatch原logのhashと一致することを確認。processは一意batchだけを数える。未起動要求はbatch実行時間へ足さず、未完の結果を完了件数へ含めない。queue待ち・coalesce・process・snapshotは重なるのでwallへ単純加算しない。native binding観測もplan/verify内に重なる。依存構築・engine起動/script load・build/importはtransaction wallの外である。

6seed×off/on各1回の正常sampleは統計的性能保証でも172件全取引の代表性の証明でもない。最終057 Linuxは7763で、80cff71のLinux8573Cと異なる。同じSHA/hashの両OSでもCPU・負荷・FS・並列数を分離し、差をOSだけや修正効果に帰属させない。21d6a66、f6d5697、80cff71、fdd6ce0のarchive/実sourceとhelperを区別した。057報告の80cff71の153/1959・63/945を最終fdd6ce0の値と混同しない。

## エラー原因の整理（観測・候補・未確定）

**直接原因（確認済み）**：専用CI4件は内側174秒で全ケースが終わらず、future/子待機の残時間が尽きる。外側180秒の強制killとは別。F5-aはこの性能問題とは独立した、起動前例外の終了記録漏れである。旧053 latestのCI固有原因は子原物を取得できず未確定。

**反復経路（コード読取り＋両OS6seedの実count一致）**：診断の新規正常取引ではplanが6回、verify_candidateが5回。各plan内でdecode_source・migration・prepare_candidate・encode_candidateが各1回、計各6回呼ばれる。

| 正常経路 | plan / verify回数 | 守っている条件 |
|---|---:|---|
| 診断呼出元の最初のplan | 1 / 0 | prepareへ渡す候補を実旧入力から構築する |
| prepare冒頭とtmp書込み後の明示verify | 1 / 1 | 現source/hash・contextで候補を再構築し、実tmpのbytes/hash・解読した型/値/IDを照合 |
| prepare末尾のrecover | 1 / 1 | 保存したintent・原本/履歴backup・実tmpからpreparedを判定 |
| commit冒頭のrecover | 1 / 1 | 独立入口で現在依存・原本・候補・保存状態を再確認 |
| rename_newのcommit.rename.before境界後のrecover | 1 / 1 | 境界待機中のsource/tmp等の差替え後も、確定直前にpreparedを再確認 |
| rename後のrecover | 1 / 1 | 実converted.jsonを再読取りし、rename戻り値やreceiptだけによらずcommittedを認識 |

6/5はこの新規正常sampleの経路で、全172ケース、再開/既存intent/失敗経路に同じ回数を仮定しない。recoverは毎回planで現在contextを使い、F3のjob_progression/jobs/abilities/session変更後の拒否を守る。write/readback、確定直前、確定後の各境界には異なる安全上の役割があるため、同じ関数を呼ぶという理由だけでは省けない。

**根本原因候補（未確定部分を含む）**：正常sampleの約98%はplan/verifyの経過時間であり、純粋な「検証だけ」でなく候補再構築・decode/encode・比較も含む。最終057の6回累積ではprepare_candidateがLinux約.361〜.386秒/Windows約.688〜.729秒、encode_candidateが約.473〜.515秒/約.877〜.941秒を占める。prepareはmetadata/schema/装備/状態検査と上限計算後にvalidateを行い、encodeはmetadata・全状態を検証して直列化後さらにdecode_source→validate→型/全値比較を行う。こうした純粋走査・構築・コピーの反復は次の調査候補だが、内部のどの箇所を安全に共通化できるか、減らせる時間、全172件での寄与率はまだ測れていない。

したがって現段階で「再検証を減らせば直る」「I/Oが唯一の原因」「Windowsだけの不具合」とは断定しない。次は同じ安全条件を残した内部処理単位の計測・局所案レビューに留める。cache復活・検証省略・新たなcodec最適化・検査予算変更は行わない。

## 範囲・原証拠

開始checkoutはwork/87f4e66、dirtyなし。指定branchをfetchし登録SHAを確認して切替、登録からの未pushは0。最初にAGENTS.md・058依頼全文を読み、更新後AGENTS、伝言板、053/055依頼・報告、056/057報告全文・057依頼、040保存計画、専用runner/helper/workflow・原証拠を確認。素材規約・企画書の旧記述と優先仕様、台帳構造も確認。checkoutの追加AGENTS・.agents/skillsは存在せず、適用可能なworkspaceローカルskillも発見していない。追加委譲なし。

- 基点849d02b→057最終の119変更パスを列挙し許可範囲と照合。原7832ファイル中7828不変、既存変更は専用workflow、decision-log末尾、driver、専用run_ci.pyの4つ。057依頼書は登録版から状態行だけ変更。
- code inventory15パスのGit blob/raw SHA-256・実bytes一致。3cf4b6c→fdd6ce0はdocsのみ。本番/保護/原証拠inventory541パスの基点・完成コード・最終提出blob一致。保護26は独立前後検査でも一致。
- 原053固定e003b126、055固定0a44409、各inventory、expectations/recovery-phases/contract、原053 runner・fixture・証拠、055 scope prefixは不変。既存055 scopeはlatestでも055固定SHAを調べるため、057差分の保証には使用しない。
- 057 scopeの後続文書正例exit0、担当外code負例exit1、固定差分負例exit1を実Git tree/commitで再実行。元の実装bytesは変更せず一時indexを使用。
- 057の23archive/58,325 memberと原053/055の21archive/258,948 member、計44archive/317,273 memberについて、raw SHA-256・サイズ・全member hash/size・索引集合・Git blobを独立照合。不一致0。hardlinkは参照bytes、symlinkは参照文字列bytes。全memberを読み出したが、保存済み44本をすべてfilesystemへ展開したとはしない。
- 最終057のCI transaction4原archiveは今回全memberを隔離ディレクトリへ展開し、各results/sha256.jsonも照合した。復元tar.gz raw hashと、GitHub ZIPのAPI digestは別物。decoded UTF-8 job textはGitHubの生log bytesと同一だと主張しない。

今回独立復元した最終057原archive（057に保存済みの80cff71 archiveとは別）：

| 対象 | member | raw tar.gz SHA-256 |
|---|---:|---|
| Linux fixed055 | 5573 | d0ec4defccd32e640bba55f6395b5372d32712f71c65d10a7e70a81679a708c9 |
| Linux latest | 6224 | 48db599b0eac0f17032941f5c164557ba83a87e81fd682d473444810be09456f |
| Windows fixed055 | 2438 | 0ea9b5d5c9585fd75a406dcfab27900b2cf8356defc729c653683a8dc840ef6c |
| Windows latest | 3502 | e680be2492b35ea5e1e0b78d03ac072a77d82f1cba2004e316562cab36b8348f |

旧053 latest artifact11612414071はAPI metadataとdownload file referenceまで取得したが、実downloadはcurl exit22・HTTP403。ZIP bytes/hash・子原log未確認。API digest `646e5438ef981076e81153411b723834a76005b770272bbf5400a7bfba388fdf` をraw検証済みhashと呼ばない。latest primitivesのjob113794239829/113794239849はログ取得がTransport closed。job/step成功metadataとローカルprimitiveの実測を分ける。アクセス制限の迂回なし。

## 独立再実行（成功・失敗・未実施）

cwd `/tmp/qa058/submitted` は提出SHAの隔離clone。保存テストは専用未存在QA root/隔離XDGを使用。既設godotは4.6.3でFontconfig warningがあり受入に使用しなかった。既存launch.pyの公式取得経路で4.7.2を取得し、ZIP `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実体 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` を確認。新環境起動・OS準備・native rebuildは行わず提出済みSOを実ロードした。

| コマンド・検査 | 実秒 / exit・結果 |
|---|---|
| `python tools/fixtures/equipment-save-transaction-platform/launch.py --output /tmp/qa058/transaction --profile latest --phase transaction` | wrapper exit0、全172/2178・97kill、伝播16、055 scope2成功 |
| 上記のtransaction子（元driver、4/16、最大4root） | suite137.037336秒 / 外側137.517137秒・exit0 |
| 上記import | 40.954秒・exit0（transaction予算の外） |
| 上記native-extra / binary-checks | 73.478 / 4.174秒・exit0、40件 / 7件 |
| 原証拠16伝播（今回成功の最終コード証拠がbaseline） | 5.367262秒累積、control exit0・15負例各exit1、055 scope正負0/1 |
| `test_capture057.py --output /tmp/qa058/capture` | 12件成功、実子30秒30.001649秒、exit0 |
| `scope057.py --code-sha 3cf4b6c293f6796220b43cf566f8eb792c3932ec --source-sha fdd6ce03c3e46cfac430930e001a383f3a7c9aec --self-test --output /tmp/qa058/scope.json` | exit0、3件の期待exit一致 |
| `diagnostics057.py --godot /tmp/qa058/transaction/bin/Godot_v4.7.2-stable_linux.x86_64 --output /tmp/qa058/measurements` | exit0、12sample成功（全取引とは別） |
| `python tools/run_locked_checks.py` | 94.335秒・exit0、R01〜08全PASS、tests_ran=true/parser_failed=false |
| Godot `--headless --path . --script res://tools/check_equipment_rules.gd` | .465秒・exit0 |
| 同 `check_equipment_save_migration.gd` / `check_equipment_save_codec.gd` | 14.411 / 9.845秒・exit0 |
| 同 `res://tools/fixtures/equipment-save/legacy_equivalence.gd` | 1.669秒・exit0、142/10全文保持 |
| `python tools/validate_assets.py --strict` | 7.586秒・exit0 |
| `python tools/check_frozen_files.py` 前/後 | .032 / .032秒・exit0、26/26 |
| 原053固定 | 今回ローカル再実行なし。最終057 job113794239760の原PASS出力172/2178・伝播14・scope2を取得。旧原archiveは全member照合 |
| Windows独立ローカル実行 / 実174・180秒境界fixture / F4実ENOSPC・nested別volume | NOT_RUN。WindowsはCI原物、実174秒枯渇はCI transaction、0.2秒fixtureとは分離 |

R/装備/S1/S2/旧比較/素材の正常logは警告・エラー検出なし。binary負例の予期したloader errorは正常対照と別扱い。元172/2178・97kill、16伝播、旧比較全文、30/174/180/600秒と各job15分を維持。skip・continue-on-error・期待弱化・条件削減・時間延長なし。手元ではarchive監査等と一部検査が同hostで重なっているため、手元のwallをOS性能比較やCI改善の証明に使わない。

## 057最終CIの全終了確認

以下はいずれもbranch `codex/task-057-save-qa-diagnostics`、head=fdd6ce0、pushのrun。058branch作成時に同SHAで発生した別runと混ぜない。中間f6の45/2とも混ぜない。

| workflow | run | 成功 / 失敗 |
|---|---:|---:|
| CI | 37922713846 | 3 / 0 |
| 006固定受入と最新回帰 | 37922713855 | 17 / 0 |
| Equipment and Save CI | 37922713696 | 14 / 0 |
| Equipment Codec CI | 37922714089 | 3 / 0 |
| 装備保存I/O・中断復旧 | 37922713668 | 1 / 1 |
| 保存専用native Windows・Linux | 37922713632 | 4 / 4 |

合計47件全completed。primitives4件成功とlatest追加診断4step成功は全取引成功とは別。058自身の最終SHA・全CI終了結果・clean/未pushは最終応答で確定する。自己SHAを文書へ再帰固定しない。文書追加scope拒否が生じた場合は既存実装の失敗から分離する。

## 再現証拠・提出境界

永続変更は058依頼の状態行と本報告だけ。新PR・main/PR33反映・force・削除・本番/検査/workflow・原証拠の変更なし。一時証拠 `/tmp/qa058` は永続成果物とは呼ばず、重要反例の再現方法とhashを本報告へ記録する。

| 一時証拠（/tmp/qa058/以下） | SHA-256 |
|---|---|
| before.json | 5deca96961c86ca3d62a1ead67e2a28e4d1d915ac77491d6646b3641ca58267a |
| counter/counterexamples.json | 03df86e96ce9da7c5636371a26aa0b7aa8039f4d77e82b3302d9187a68c39a32 |
| outer-tree/review.json | 8029f9adb4f21c9f16f727858f235a5eeb37ddc298769a914b76750a38344cdd |
| archive-audit.json | 05f90e2e02c31014837c6aa56dcb34b7832047422ea5063610e608ce62caefa4 |
| transaction/execution.json | 16665d719135f307e6e182677b66384db0ed4e92fa62f3aefdbb9848090deda9 |
| capture/tests.json | 82eda792f68e3d7150ec55526ab9ddfa9e8c76184cea4f87877080d678f9243f |
| scope.json | 4a29765b59606b0220e0f062212a073e8eaa8edeb0d887cd6f173b67c0968857 |
| measure-review.json | 8bf5e980a3e9ac47d004c3c3f3a597e98e1eb6ac9958453fc2d18f9f174ab115 |
| regression/commands.json | 872d9b484d6337b21d437211b5551095a16f926bc8bacd9616c6c4eca56f8aa4 |
| regression/R01-R08.json | 7be1857c34d46ebd87cfac7f921901ebefabb91523cc0bd703dd39b2f6c49ecb |
| measurements/diagnostics.json | 58a16a264b1b98278c42e28e39b6d06f86b420f7b93735cf449f4eb223dc3199 |
| ci057-jobs.json | 6be2c156e3d30b9792c6fa606d567bcffbb10474949314ed0f89fcf30175e878 |

次の最小案は、まずF5-aの起動前終了記録と回収完全性の判定を専用driver/fixture内で直すこと。その後F1は、同じ検証義務・全拒否条件を維持したままencode_candidate/prepare_candidate内部の重複純粋処理を更に観測する別依頼とする。既存codec最適化、cache復活、環境準備、予算延長は今回実施していない。
