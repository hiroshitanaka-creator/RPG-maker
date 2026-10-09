extends "res://scripts/game/equipment_save_transaction.gd"
## 057専用。planの同一制御経路で各実関数を呼ぶ。helperが元bodyとの一致を機械確認する。
var spans: Array=[]
var stack: Array=[]

func enter(label: String) -> int:
	var id := spans.size()
	spans.append({"label":label,"start_us":Time.get_ticks_usec(),"end_us":0,"parent":stack.back() if not stack.is_empty() else -1})
	stack.append(id)
	return id

func leave(id: int) -> void:
	spans[id].end_us=Time.get_ticks_usec()
	stack.pop_back()

func plan(raw: PackedByteArray) -> Dictionary:
	var id := enter("plan")
	var result := _plan_observed(raw)
	leave(id)
	return result

func _plan_observed(raw: PackedByteArray) -> Dictionary:
	var context_errors := Validation.context_errors(context)
	if not context_errors.is_empty():return Codec.failure(context_errors[0].reason_code,"context",context_errors)
	# validatorの実依存を毎回使い、純粋計画cacheで再検証を省略しない。
	var decoded := timed_decode(raw)
	if not decoded.ok:return decoded
	if decoded.source_format=="equipment-v1":return fail("already_migrated","source")
	var migrated := timed_migration(decoded.document,decoded.source_sha256)
	if not migrated.ok:return migrated
	var prepared := timed_prepare(migrated.candidate_document)
	if not prepared.ok:return prepared
	var encoded := timed_encode(prepared.document)
	if not encoded.ok:return encoded
	var result := {"ok":true,"source":decoded,"document":encoded.document,"bytes":encoded.bytes,"sha256":encoded.document_sha256,"token":migrated.migration_id}
	return result

func timed_decode(raw: PackedByteArray) -> Dictionary:
	var id := enter("plan.decode_source")
	var result := Codec.decode_source(raw,context)
	leave(id)
	return result

func timed_migration(document: Dictionary, sha: String) -> Dictionary:
	var id := enter("plan.migration")
	var result := Migration.new().plan(document,sha,context)
	leave(id)
	return result

func timed_prepare(document: Dictionary) -> Dictionary:
	var id := enter("plan.prepare_candidate")
	var result := Validation.prepare_candidate(document,context)
	leave(id)
	return result

func timed_encode(document: Dictionary) -> Dictionary:
	var id := enter("plan.encode_candidate")
	var result := Codec.encode_candidate(document,context)
	leave(id)
	return result

func verify_candidate(path: String, candidate: Dictionary) -> Dictionary:
	var id := enter("verify_candidate")
	var result := super.verify_candidate(path,candidate)
	leave(id)
	return result
