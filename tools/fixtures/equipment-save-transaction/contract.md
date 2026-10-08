# S3 QA限定APIと失敗契約

対象はLinux上の明示QA rootと隔離XDG。rootは既存の専用directory、contextは実GameSessionとBattleCatalogに一致するabilities、generationは呼出側の世代文字列。通常入口・記録再開・メモリ適用なし。Windows/macOS、停電、媒体故障は未検証。Linux以外はpath_invalid。rootの明示許可は呼出側の責任で、user://を暗黙解決しない。

`new(root, context, generation, qa_hook=Callable())` → `inspect(source)` / `prepare(source, expected_sha256, candidate_document, expected_generation)` / `commit(migration_id, expected_generation)` / `recover(migration_id)`。

- inspectはbytes/size/hash、decoder、同raw取引の観測だけ。書込みゼロ。
- prepareはraw hashとgenerationを先に照合し、S1再計画＋S2 prepare/encodeと候補の全値/型/順序一致を要求。migration_idを排他単位とする。同raw別名は最初のsource_pathを保持して同取引を再使用する。異なるrawは別ID。
- 原本backupはsource.bin.tmp→flush/close/byte読戻し→source.bin。履歴は明示QA `history/<trialID>.json` のrawをhistory.binへ保持。trialなし/欠落/破損/正常/未正常終了を区別し、新IDや記録イベントを生成しない。
- immutable intent.jsonはsource/候補/hash/size/世代/history/policy/ID/targetを記録。receipt.jsonはそのintentのコピーとphase。復旧は元保存を再decode・S1/S2再計画しintentの全fieldと照合。phaseはprepared/committedのどちらでも実出力の存在で判定。破損receipt、backup、出力はrecovery_required。source差替えはsource_changed。
- 実bytesに完全一致するconverted.tmpはprepared。backup/historyがそろった正しいconverted.jsonはcommitted、applied=false。rename後receipt失敗はok=true/committed=true/receipt_updated=false。未完tmpだけ同じ取引で再生成可。backup/確定出力・原source・既存履歴を置換/削除しない。
- 本実装は単一writerのappend-only leaseを使用。owner記録を先に書き、固定連番lease symlinkの排他作成を成功点にする。旧leaseを保持し、前owner PIDが生存ならbusy。同instanceのnonceだけ再使用可能。再起動時は死んだPIDの後の連番を排他取得。PID再使用は安全側にbusyで止まり、自動的に生存ownerを奪わない。
- 入出力の全パス成分でsymlinkを拒否（内部向きも拒否）。leaseだけは検証済み単一basename owner参照として専用扱い。実体のstat deviceを照合し別volumeも拒否。sourceと取引fileのhardlink同一性も拒否。Linux GNU mv --no-clobberで新規renameし、fromが残ればtarget_conflict。receiptのみ自取引metadataとして更新する。
- source/候補/世代の変化、既存衝突、二重writer、context異常を明示拒否。失敗はok=false/reason_code/errors（成功document/bytesなし）。I/O途中の所有済み専用tmpは保持し、復旧から同候補を再使用する。

qa_hookは境界名を受けてboolを返す専用障害注入引数。falseはinjected_io_failure。真の容量不足・権限拒否を表さない。強制終了時はprobeが専用markerを書いて待機し、Python側がSIGKILL、wait後に別Godotプロセスを起動する。

Godot標準APIだけではディレクトリfsync・媒体耐久性は保証しない。一般の悪意あるプロセスによる、パス検証とopen間のdirectory置換のTOCTOUを防ぐopenat2はこのS3で実装していない。隔離QA内で静的リンク・境界前の差替えと協調writerを実測する。通常UIへの公開にこのまま使わない。

未所有の初期tmp、hardlinkで他の原本へつながる書込み先、owner PID/nonceとleaseのbasename不一致も拒否する。実容量不足と実別volumeは専用小容量/nested mount環境がなく未検証。ENOSPC注入はinjected_io_failureでありOS由来ENOSPCとは区別する。
