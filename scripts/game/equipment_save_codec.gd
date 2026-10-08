extends RefCounted
## raw保存の純粋codec。通常load/save・metrics・archive・ファイルI/Oへ接続しない。
const Validation = preload("res://scripts/game/equipment_document_validation.gd")
const S1 = preload("res://scripts/game/equipment_save_validation.gd")

static func failure(code: String, path: String, errors: Array = []) -> Dictionary:
	return {"ok":false,"reason_code":code,"errors":errors if not errors.is_empty() else [S1.error(path,code)]}

static func hash_bytes(bytes: PackedByteArray) -> String:
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(bytes)
	return hash.finish().hex_encode()

static func valid_utf8(bytes: PackedByteArray) -> bool:
	# Godotの不正UTF-8警告を起こす前に符号列を検査する。
	var index := 0
	while index<bytes.size():
		var head: int=bytes[index]
		var count := 0
		if head<=127:index+=1;continue
		if head>=194 and head<=223:count=1
		elif head>=224 and head<=239:count=2
		elif head>=240 and head<=244:count=3
		else:return false
		if index+count>=bytes.size():return false
		for offset in range(1,count+1):
			if bytes[index+offset]<128 or bytes[index+offset]>191:return false
		var second: int=bytes[index+1]
		if (head==224 and second<160) or (head==237 and second>159) or (head==240 and second<144) or (head==244 and second>143):return false
		index+=count+1
	return true

static func unique_json_keys(text: String) -> bool:
	# parse済みJSONの字句だけを走査し、Dictionaryへ畳まれる前の重複キーを拒否する。
	var pattern := RegEx.new()
	pattern.compile('"(?:[^"\\\\]|\\\\.)*"|[{}\\[\\]:,]|[^\\s{}\\[\\]:,]+')
	var tokens := pattern.search_all(text)
	var stack: Array=[]
	for index in range(tokens.size()):
		var token: String=tokens[index].get_string()
		if token=="{":stack.append({"keys":{}})
		elif token=="[":stack.append({})
		elif token in ["}","]"]:stack.pop_back()
		elif token.begins_with('"') and index+1<tokens.size() and tokens[index+1].get_string()==":":
			var key: String=JSON.parse_string(token)
			if stack.is_empty() or not stack.back().has("keys") or stack.back().keys.has(key):return false
			stack.back().keys[key]=true
	return true

static func metadata_errors(metadata: Variant) -> Array:
	return Validation.metadata_errors(metadata)

static func decode_source(bytes: PackedByteArray, context: Dictionary) -> Dictionary:
	var errors := Validation.context_errors(context)
	if not errors.is_empty():return failure(errors[0].reason_code,"context",errors)
	if not valid_utf8(bytes):return failure("invalid_encoding","$")
	var text := bytes.get_string_from_utf8()
	if text.to_utf8_buffer()!=bytes:return failure("invalid_encoding","$")
	var parser := JSON.new()
	if parser.parse(text)!=OK or not parser.data is Dictionary or not unique_json_keys(text):return failure("invalid_json","$")
	var outer: Dictionary=parser.data
	var packed := outer.has("_storage_format")
	if packed:
		if not outer.get("_storage_format") is String or outer._storage_format!=SavedDocument.FORMAT or outer.size()!=5 or not outer.has_all(["decoded_bytes","sha256","payload_sha256","payload"]):return failure("invalid_envelope","$")
		for key in ["sha256","payload_sha256","payload"]:
			if not outer[key] is String:return failure("invalid_envelope","$")
		if not (outer.decoded_bytes is int or outer.decoded_bytes is float) or not is_finite(float(outer.decoded_bytes)) or outer.decoded_bytes<1 or outer.decoded_bytes>SavedDocument.MAX_DECODED or outer.decoded_bytes!=floor(outer.decoded_bytes):return failure("invalid_envelope","$")
	if packed:
		var payload: String=outer.payload
		if payload.length()>SavedDocument.MAX_DECODED*2 or payload.length()%4!=0 or payload.sha256_text()!=outer.payload_sha256:return failure("invalid_envelope","$")
		var alphabet := RegEx.new();alphabet.compile("^[A-Za-z0-9+/]*={0,2}$")
		if alphabet.search(payload)==null:return failure("invalid_envelope","$")
		var compressed := Marshalls.base64_to_raw(payload)
		if compressed.size()<18 or compressed[0]!=31 or compressed[1]!=139 or compressed[2]!=8 or compressed.decode_u32(compressed.size()-4)!=int(outer.decoded_bytes):return failure("invalid_envelope","$")
		var inner := compressed.decompress(int(outer.decoded_bytes),FileAccess.COMPRESSION_GZIP)
		if inner.size()!=int(outer.decoded_bytes):return failure("invalid_envelope","$")
		if not valid_utf8(inner):return failure("invalid_encoding","$")
		var inner_text := inner.get_string_from_utf8()
		if inner_text.sha256_text()!=outer.sha256:return failure("invalid_envelope","$")
		var inner_parser := JSON.new()
		if inner_parser.parse(inner_text)!=OK or not inner_parser.data is Dictionary:return failure("invalid_envelope","$")
		if not unique_json_keys(inner_text):return failure("invalid_json","$")
	var raw := SavedDocument.decode(outer)
	if raw.is_empty():return failure("invalid_envelope" if packed else "invalid_json","$")
	var raw_errors := S1.values(raw)
	if not raw_errors.is_empty():return failure(raw_errors[0].reason_code,"$",raw_errors)
	var has_types := raw.has("_saved_value_types")
	var metadata: Variant=raw.get("_saved_value_types")
	var body := raw.duplicate(true)
	body.erase("_saved_value_types")
	var document: Dictionary=GameSession._normalize_numbers(body)
	if has_types:
		errors=metadata_errors(metadata)
		if not errors.is_empty():return failure("invalid_types","$._saved_value_types",errors)
		var restored := SavedValueTypes.restore(document,metadata)
		if not restored.get("ok",false):return failure("invalid_types","$._saved_value_types")
		document=restored.value
		var described := SavedValueTypes.describe(document)
		# JSON内のpath/builtinの整数表現だけを正規化する。
		if not S1.differences(described,GameSession._normalize_numbers(metadata)).is_empty():return failure("invalid_types","$._saved_value_types")
		document["_saved_value_types"]=described
	# 位置処理が参照するparty/住人の形状を先に確認する。
	var equipment := S1.NEW_ROOT.any(func(key):return document.has(key))
	errors=Validation.schema(document,equipment)
	if not errors.is_empty():return failure(errors[0].reason_code,"$",errors)
	if document.get("overworld") is Dictionary and document.get("first_region") is Dictionary:
		for index in range(document.party.size()):
			if not document.party[index].get("id") is String:return failure("invalid_shape","$.party[%d].id" % index)
		for key in document.overworld.get("residents",{}):
			var cell: Variant=document.overworld.residents[key].get("cell")
			if not cell is Array or cell.size()!=2 or not cell[0] is int or not cell[1] is int:return failure("invalid_shape","$.overworld.residents."+str(key)+".cell")
	var located := document.duplicate(true)
	if context.legacy_session._relocate_saved_position(located):
		var result := failure("position_relocation_required","$.overworld")
		result["differences"]=S1.differences(document,located)
		result["position_before"]=document.overworld.duplicate(true)
		result["position_after"]=located.overworld.duplicate(true)
		return result
	if equipment:
		if not document.get("equipment_rules_version") is int or document.equipment_rules_version!=1:return failure("unsupported_version","$.equipment_rules_version")
		errors=Validation.validate(document,context)
	else:
		errors=Validation.schema(document,false)
		if errors.is_empty():errors=S1.validate_legacy(document,context)
	if not errors.is_empty():return failure(errors[0].reason_code,"$",errors)
	return {"ok":true,"reason_code":"ok","document":document,"source_bytes":bytes.duplicate(),"source_sha256":hash_bytes(bytes),"source_format":"equipment-v1" if equipment else "legacy-%d" % document.format_version,"observations":{"storage":"gzip" if packed else "plain","has_types":has_types,"has_metrics":raw.has("_play_session"),"has_trial_id":raw.has("_trial_id"),"normalization":"typed_restore" if has_types else "legacy_numbers"},"errors":[]}

static func encode_candidate(document: Dictionary, context: Dictionary) -> Dictionary:
	var errors := Validation.context_errors(context)
	if not errors.is_empty():return failure(errors[0].reason_code,"context",errors)
	var candidate := document.duplicate(true)
	candidate.erase("_saved_value_types")
	var metadata := SavedValueTypes.describe(candidate)
	if not metadata.errors.is_empty():return failure("unsupported_value","$")
	# 既存metadataの未知キー・壊れたpath・型不一致を再生成で消さない。
	if document.has("_saved_value_types"):
		errors=Validation.native_metadata_errors(document)
		if not errors.is_empty():return failure("invalid_types","$._saved_value_types",errors)
	errors=Validation.validate(candidate,context)
	if not errors.is_empty():return failure(errors[0].reason_code,"$",errors)
	candidate["_saved_value_types"]=metadata
	var bytes := SavedDocument.encode(candidate).to_utf8_buffer()
	var decoded := decode_source(bytes,context)
	if not decoded.ok:return failure("serialization_mismatch","$",decoded.errors)
	errors=S1.differences(candidate,decoded.document)
	if not errors.is_empty() or not SavedValueTypes.same_types(candidate,decoded.document):return failure("serialization_mismatch","$",errors)
	return {"ok":true,"reason_code":"ok","bytes":bytes,"document_sha256":hash_bytes(bytes),"document":candidate,"errors":[]}
