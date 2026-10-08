# 053 保存I/O・中断復旧の実装報告

依頼登録 `e2c28474b55bd3a9e3dee00be768661ba87e09c4`、前提main `87f4e66ed64f2ae9a92538acb9716c6a01f5cb27`。指定branch `codex/task-053-equipment-save-transaction`。コード完成固定 `e003b126de6695fa131e07a3db14c3011fb74f2e`。draft [PR33](https://github.com/hiroshitanaka-creator/RPG-maker/pull/33)。最終提出SHAと、そのSHAの全CI終了結果・runリンクは最終応答とPR本文へ記録する（自身のSHAを含めたcommitは再帰するため）。

承認済みのS3を明示QA root/隔離XDGだけに実装した。通常画面・通常GameSession入口・運用記録・実ユーザー保存へ接続せず、メモリ適用はfalse。AGENTS全文、040計画第4/7/9/10節、051/052報告、S1/S2実API、関係規約を読んだ。checkoutに追加AGENTS/.agents/skillsなし。verification-before-completionを適用し、実結果で成功を確認した。

## 完成動作

`equipment_save_transaction.gd` は明示root/context/generationを受ける。inspectは原bytes/size/hash、実decoder、既存取引を読むだけ。prepareはraw expected hashと世代を照合し、実GameSession/BattleCatalog/abilities依存のS1再計画→S2候補準備/encodeと、候補の全値・native型・順序を比較する。同raw別名は最初のsource_pathとmigration_idを再使用し、raw違いは別ID、新版再入力はalready_migrated。

原sourceを保持し、source.bin.tmpのflush/close/実bytes読戻し後に別source.binを確定。既存trialIDの専用履歴は正常/未正常終了/欠落/破損/IDなしを区別し、存在する破損rawもhistory.binへ保持する。新ID・イベントは生成しない。immutable intentは原source/候補/hash/size/世代/history/policy/ID/targetを保持する。

converted.tmpの書込み後の最初の実読戻しをS2でdecodeし、全値/型/順序/migration_idを照合。commitは元hash/世代/候補/衝突を再検査し、新規converted.jsonへのrenameを成功点とする。rename後のreceipt更新失敗も実出力を確認してcommitted=trueと返す。recoverはreceipt phaseだけを信用せず、検証済み元rawから再計画し、intentの全field、source/backup/history/tmp/確定出力の実bytesと照合する。外部backup/出力/原本/履歴は置換・削除せず、自分の未完tmpだけ同取引で再生成する。

単一writerはappend-only連番lease symlinkの排他作成で取得し、owner PID/nonce/参照basenameを検証する。生存ownerをbusyで拒否し、SIGKILL後は次連番で取得。PID再使用は安全側にbusy。全path成分の内部/外部symlink、..、root外、source/取引file同一性、書込み先hardlink、未所有初期tmp、衝突を拒否する。stat deviceで別volumeを拒否する設計だが、実専用別volumeは未実測。Linux GNU mv --no-clobberを使うため、このS3はLinux限定で他OSを拒否する。

## 実測と固定期待

固定SHAの独立checkoutで公式Godot 4.7.2 wrapperを全実行し、172ケース/2178条件を成功。実SIGKILL97地点、注入24件、個別51件。各killはmarkerの地点/PIDを確認してSIGKILL/waitし、その後の別Godot processでrecover→同取引prepare/commitを実行する。97地点の期待phaseは独立fixtureと実bytesで比較する。全原source/history不変、backup/出力hash、数量12（既付与22）、二重付与0、入力/state/metrics不変、実GameSession依存、null/不正context拒否を実測した。

最大4件を新Godotへまとめ、完全構築した実GameSessionを読取り専用依存として使う。要求ごとにcontext/transaction/cacheを新規生成し、前後state/metrics不変を検査する。元kill processと復旧PIDの相違を検査し、共有batchの全root/argv/実exitを保存する。2つのbatch実行器と8検査workerは実行予算のためで、追加委譲ではない。同instance内の純粋計画/decoded cacheはrawと実依存変更時に無効化し、新processは再decode/replanする。

正常証拠対照の実Python子exit0と、改変/警告/件数ゼロ/exit異常/timeout/原bytes/欠落/false assertion/phase改変/改変後manifest再hashなど13負例の実exit1を確認。実Git tree/commitの無名後続文書正例exit0、固定側担当外負例exit1を確認。旧wrapper/期待を変更せず、新workflowだけfixed053/latestの全条件を実行する。後続文書のscope比較先だけを完成053へ固定し、latestの動作検査を省略しない。

| 実コマンド・内容 | 予算秒 | 実測秒 | 実exit/結果 |
|---|---:|---:|---|
| Godot --version | 30 | 0.409 | 0、4.7.2.stable.official.ed1daf0bf |
| 固定checkout import | 600 | 5.918 | 0 |
| check_equipment_save_transaction.py（全件） | 180 | 147.587 | 0、172/2178、警告/エラー0 |
| run_locked_checks.py：R全8、tests_ran=true/parser_failed=false | 900 | 125.234 | 0 |
| check_frozen_files.py：26/26 | 30 | 0.065 | 0 |
| check_equipment_rules.gd：5394＋93条件/400切替 | 240 | 0.967 | 0 |
| check_equipment_save_migration.gd：61/2828 | 120 | 20.151 | 0 |
| check_equipment_save_codec.gd：154/975 | 120 | 13.566 | 0 |
| legacy_equivalence.gd：142検証/10更新 | 120 | 2.272 | 0 |
| validate_assets.py --strict：画像1154/音15/palette3/font2、問題0 | 120 | 7.558 | 0 |

全argv・各子30秒・実exit・原log hashは [final-fixed-execution.json](../../verification/equipment-save-transaction/final-fixed-execution.json) と [regression-commands.json](../../verification/equipment-save-transaction/regression-commands.json)。旧比較全文のSHA256は `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` で既存原全文と一致。Rの原spec/test/smoke hashも新 [R01-R08.json](../../verification/equipment-save-transaction/R01-R08.json) に記録する。既存異常定義202件のローカル再実行は未実施で、既存CIの全世代で確認する。

## 原証拠・範囲

[証拠README](../../verification/equipment-save-transaction/README.md)、全172件の [ケース表](../../verification/equipment-save-transaction/cases.md)、[archive hash](../../verification/equipment-save-transaction/archives.json) とmembers.jsonに原bytes/size/hash/リンク参照を保存。archive全memberを再読出し照合した。初期試作の中断/予算超過、非子PID・空bytes hash・再帰mkdir由来のエラー、依存初期化の試行、未完成validatorによる拒否もdevelopment archiveに残し、最終受入から除外した。原ログを成功へ書換えない。archive梱包の初回照合は実行効率のため中断し、索引を使って全member照合を完了した（試験本体や固定コードの変更ではない）。

Linux公式ZIP SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実体SHA256 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。既設4.6.3を使わず公式4.7.2を専用領域へ取得。gh CLI認証は無効だがGit pushとGitHub appによるdraft PRは成功した。

全変更は [changed-files.txt](../../verification/equipment-save-transaction/changed-files.txt)。旧workflow/wrapper/fixture/過去証拠、test/.scope-lock/data/assets、通常入口は不変。元checkoutの初期未commitなし、固定後scripts/tools/data/test/.scope-lock/assetsの差分なし。Godotが生成した担当外uid2件はQA領域へ保管して提出から除外した。担当外変更要求なし。保護26を前後実測。固定SHA後はコード・検査・固定期待を変更せずCI/文書/証拠だけ追加する。

## 未検証と残件

実権限拒否は非root uid1000の新設専用directoryを作成時0500にして実測。ユーザー権限・OS・ディスク設定は変更しない。ENOSPCは注入を実測し、実容量不足は専用小容量領域がないため未検証。専用nested別volume、他OS、停電/媒体故障/directory fsync、非協調processによるpath検査/open間の悪意あるdirectory差替えTOCTOUも未検証。プロセス強制終了後の復旧を停電保証としない。mount設定がprocess中に変わらない隔離QAを前提とする。

通常load/メモリ適用/UI/戦闘/運用記録との接続、実ユーザー保存、S4/S5、人間の作品/操作体験の採否は未実施・範囲外。main反映・merge・強制push・削除・追加委譲は行わない。親の独立レビューと受入判断を待つ。

## 追加実測で見つかった通知競合の修正

初回固定75b6e350の独立wrapperは172/2178・147.603秒で成功したが、文書追加head d144ea49の追加local latestで停止通知paused.jsonを作成直後・書込み前に読む競合が1件発生した。kill-source.store.beforeの原markerは0bytes、171ケース/2163条件、156.939秒、exit1。原証拠と旧CIのfixed/latest成功ログをmarker-race archiveへ保持し、成功CIでlocal失敗を隠さない。検査側は厳密JSON解析を維持し、成功へ補完しない。

修正はprobe_worker.gdの停止通知だけ。専用paused.json.tmpへJSONを書き、flush/error/closeを確認してrenameで公開する。新完成固定e003b126de6695fa131e07a3db14c3011fb74f2eを独立checkoutしてwrapper全体を再実行し、全172/2178・実SIGKILL97地点・伝播14・scope2・保護26を成功。新固定のimportは既にimport済みcheckoutの5.918秒（旧clean import60.499秒と区別）。新固定の全argv/実時間/exit/source hashはfinal-fixed-execution.json。原log/全bytesはfinal-fixed053-raw archive。旧成功・新成功・失敗を混ぜない。

保存本体、S1/S2、既存検査/期待/予算に差分なし。既存回帰の表は初回固定SHAでの実測を保持し、最終SHAの全CIも確認する。今回の通知専用修正後の完成固定をe003b126として、それ以降はコード/検査/期待を変更せずCI/文書/証拠だけを追加する。
