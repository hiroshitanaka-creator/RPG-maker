extends RefCounted
## S3専用。通常保存/ロード/記録/メモリ適用へ接続しない。
const Codec = preload("res://scripts/game/equipment_save_codec.gd")
const Validation = preload("res://scripts/game/equipment_document_validation.gd")
const Migration = preload("res://scripts/game/equipment_save_migration.gd")
const S1 = preload("res://scripts/game/equipment_save_validation.gd")
var root: String
var context: Dictionary
var generation: String
var hook: Callable
var owner := ""
var owned := ""
var io: RefCounted
var io_ready := false
var lease_index := -1

func _init(qa_root: String, explicit_context: Dictionary, session_generation: String, qa_hook: Callable = Callable()) -> void:
	root=qa_root.replace("\\","/").trim_suffix("/")
	context=explicit_context
	generation=session_generation
	hook=qa_hook
	# 配布binaryをmanifestと照合してから利用。欠落/不正/未登録は全入口を閉じる。
	var platform := "windows" if OS.get_name()=="Windows" else "linux" if OS.get_name()=="Linux" else ""
	var target := "template_debug" if OS.has_feature("debug") else "template_release"
	var suffix := ".dll" if platform=="windows" else ".so"
	var binary := "res://addons/equipment_save_io/bin/equipment_save_io.%s.%s.x86_64%s" % [platform,target,suffix]
	var manifest: Variant=JSON.parse_string(FileAccess.get_file_as_string("res://addons/equipment_save_io/manifest.json")) if FileAccess.file_exists("res://addons/equipment_save_io/manifest.json") else null
	if platform.is_empty() or not manifest is Dictionary or not manifest.get("files") is Dictionary:return
	if not FileAccess.file_exists(binary) or manifest.files.get(binary.trim_prefix("res://"),"")!=FileAccess.get_sha256(binary):return
	if not ClassDB.class_exists("EquipmentSaveIO"):return
	io=ClassDB.instantiate("EquipmentSaveIO")
	io_ready=io!=null and io.configure(root)

func fail(code: String, path: String) -> Dictionary:
	return Codec.failure(code,path)

func boundary(point: String) -> bool:
	return not hook.is_valid() or hook.call(point)

func path_ok(path: String) -> bool:
	return io_ready and io.path_ok(path)

static func hash_raw(bytes: PackedByteArray) -> String:
	return "".sha256_text() if bytes.is_empty() else Codec.hash_bytes(bytes)

func make_directories(path: String) -> bool:
	return io_ready and io.make_directories(path)

func read_bytes(path: String) -> Dictionary:
	if not path_ok(path):return fail("path_invalid",path)
	if not boundary("read.open.before"):return fail("injected_io_failure",path)
	var opened: Dictionary=io.open_read(path)
	if not opened.ok:return fail(opened.reason_code,path)
	var handle: int=opened.handle
	if not boundary("read.open.after"):io.close_file(handle);return fail("injected_io_failure",path)
	if not boundary("read.buffer.before"):io.close_file(handle);return fail("injected_io_failure",path)
	var read: Dictionary=io.read_all(handle)
	var closed: Dictionary=io.close_file(handle)
	if not boundary("read.buffer.after"):return fail("injected_io_failure",path)
	if not read.ok or not closed.ok:return fail("read_failed",path)
	return {"ok":true,"bytes":read.bytes,"size":read.size,"sha256":hash_raw(read.bytes)}

func read_json(path: String) -> Dictionary:
	var read := read_bytes(path)
	if not read.ok:return read
	if not Codec.valid_utf8(read.bytes):return fail("recovery_required",path)
	var parser := JSON.new()
	if parser.parse(read.bytes.get_string_from_utf8())!=OK or not parser.data is Dictionary or not Codec.unique_json_keys(read.bytes.get_string_from_utf8()):return fail("recovery_required",path)
	return {"ok":true,"value":GameSession._normalize_numbers(parser.data)}

func transaction_path(token: String) -> String:
	if token.length()!=64 or not token.is_valid_hex_number(false) or token!=token.to_lower():return ""
	return root.path_join("transactions").path_join(token)

func plan(raw: PackedByteArray) -> Dictionary:
	var context_errors := Validation.context_errors(context)
	if not context_errors.is_empty():return Codec.failure(context_errors[0].reason_code,"context",context_errors)
	# validatorの実依存を毎回使い、純粋計画cacheで再検証を省略しない。
	var decoded := Codec.decode_source(raw,context)
	if not decoded.ok:return decoded
	if decoded.source_format=="equipment-v1":return fail("already_migrated","source")
	var migrated := Migration.new().plan(decoded.document,decoded.source_sha256,context)
	if not migrated.ok:return migrated
	var prepared := Validation.prepare_candidate(migrated.candidate_document,context)
	if not prepared.ok:return prepared
	var encoded := Codec.encode_candidate(prepared.document,context)
	if not encoded.ok:return encoded
	var result := {"ok":true,"source":decoded,"document":encoded.document,"bytes":encoded.bytes,"sha256":encoded.document_sha256,"token":migrated.migration_id}
	return result

func history(document: Dictionary) -> Dictionary:
	var id: String=document.get("_trial_id","")
	if id.is_empty():return {"ok":true,"status":"absent_id","path":"","bytes":PackedByteArray(),"sha256":"","size":0,"history_complete":false}
	var path := root.path_join("history").path_join(id+".json")
	if not path_ok(path):return fail("path_invalid",path)
	if not FileAccess.file_exists(path):return {"ok":true,"status":"missing","path":path.trim_prefix(root+"/"),"bytes":PackedByteArray(),"sha256":"","size":0,"history_complete":false}
	var raw := read_bytes(path)
	if not raw.ok:return raw
	var status := "corrupt"
	var complete := false
	if Codec.valid_utf8(raw.bytes):
		var parser := JSON.new()
		if parser.parse(raw.bytes.get_string_from_utf8())==OK and parser.data is Dictionary:
			var value: Dictionary=parser.data
			var valid: bool=value.get("trial_id")==id and value.get("archive_version")==1 and value.get("history_complete") is bool and value.get("builds") is Array
			valid=valid and value.get("run_open",true) is bool and value.get("duration_finished",false) is bool
			if valid:
				valid=not value.builds.is_empty() and value.builds.all(func(build):return build is String and build.length()==64 and build.is_valid_hex_number(false)) and PlaySessionMetrics.new().restore(value)
			if valid:
				status="unclean" if value.get("run_open",true) else "normal"
				complete=value.history_complete and status=="normal"
	return {"ok":true,"status":status,"path":path.trim_prefix(root+"/"),"bytes":raw.bytes,"sha256":raw.sha256,"size":raw.size,"history_complete":complete}

func inspect(source_path: String) -> Dictionary:
	var read := read_bytes(source_path)
	if not read.ok:return read
	var decoded := Codec.decode_source(read.bytes,context)
	var token := Migration.migration_id(read.sha256)
	var tx := transaction_path(token)
	var existing: Dictionary={"phase":"absent"}
	if path_ok(tx) and DirAccess.dir_exists_absolute(tx):existing=recover(token)
	return {"ok":true,"reason_code":"ok","source_bytes":read.bytes,"source_size":read.size,"source_sha256":read.sha256,"decoder":decoded,"existing":existing,"errors":[]}

func acquire(tx: String) -> Dictionary:
	if not path_ok(tx):return fail("path_invalid",tx)
	if not boundary("directory.create.before"):return fail("injected_io_failure",tx)
	if not make_directories(tx):return fail("backup_failed",tx)
	if not boundary("directory.create.after"):return fail("injected_io_failure",tx)
	if not boundary("kernel.lock.before"):return fail("injected_io_failure",tx)
	var lock: Dictionary=io.acquire_lock(tx)
	if not lock.ok:return fail(lock.reason_code,tx)
	if not boundary("kernel.lock.after"):return fail("injected_io_failure",tx)
	var leases := tx.path_join("leases")
	if not path_ok(leases) or not make_directories(leases):return fail("backup_failed",leases)
	var dir := DirAccess.open(leases)
	var links: Array=[]
	dir.list_dir_begin()
	var name := dir.get_next()
	while not name.is_empty():
		if name.begins_with("lease-"):links.append(name)
		name=dir.get_next()
	dir.list_dir_end()
	links.sort()
	for index in range(links.size()):
		if links[index]!="lease-%08d" % index:return fail("recovery_required",leases)
	if not links.is_empty():
		var last: String=links.back()
		var link_path := leases.path_join(last)
		var ref: String=io.legacy_link(link_path)
		var metadata_path := link_path
		if not ref.is_empty():
			if ref.get_file()!=ref or not ref.begins_with("owner-") or not ref.ends_with(".json"):return fail("recovery_required",leases)
			metadata_path=leases.path_join(ref)
		var prior := read_json(metadata_path)
		if not prior.ok or prior.value.size()!=2 or not prior.value.get("pid") is int or not prior.value.get("nonce") is String:return fail("recovery_required",leases)
		if prior.value.pid<=0 or prior.value.nonce.length()!=32 or not prior.value.nonce.is_valid_hex_number(false):return fail("recovery_required",leases)
		if not ref.is_empty() and ref!="owner-%d-%s.json" % [prior.value.pid,prior.value.nonce]:return fail("recovery_required",leases)
		if owned==tx and owner==prior.value.nonce and prior.value.pid==OS.get_process_id():return {"ok":true}
		# 旧symlink writerはdead確定以外拒否。新regular leaseはkernel lockが唯一の所有権。
		if not ref.is_empty() and io.process_state(prior.value.pid)!=0:return fail("busy",tx)
	owner=Crypto.new().generate_random_bytes(16).hex_encode()
	var owner_name := "owner-%d-%s.json" % [OS.get_process_id(),owner]
	var metadata := JSON.stringify({"pid":OS.get_process_id(),"nonce":owner}).to_utf8_buffer()
	var written := write_raw(leases.path_join(owner_name),metadata,"owner",false)
	if not written.ok:return written
	if not boundary("lease.acquire.before"):return fail("injected_io_failure",tx)
	# regular exclusive leaseが旧053のis_link検証をfail-closedにする。旧原物は残す。
	var barrier: Dictionary=io.rename_file(leases.path_join(owner_name),leases.path_join("lease-%08d" % links.size()),false)
	if not barrier.ok:return fail("busy",tx)
	owned=tx
	lease_index=links.size()
	if not boundary("lease.acquire.after"):return fail("injected_io_failure",tx)
	return {"ok":true}

func writable_file(path: String) -> bool:
	if not path_ok(path):return false
	if FileAccess.file_exists(path):
		var identity: Dictionary=io.inspect_identity(path)
		return identity.ok and identity.links==1
	return true

func write_raw(path: String, bytes: PackedByteArray, label: String, replace_tmp: bool) -> Dictionary:
	if not path_ok(path):return fail("path_invalid",path)
	if FileAccess.file_exists(path) and not replace_tmp:return fail("conflict",path)
	if not boundary(label+".open.before"):return fail("injected_io_failure",path)
	if not writable_file(path):return fail("conflict",path)
	var opened: Dictionary=io.open_write(path,replace_tmp)
	if not opened.ok:return fail(opened.reason_code,path)
	var handle: int=opened.handle
	if not boundary(label+".open.after"):io.close_file(handle);return fail("injected_io_failure",path)
	if not boundary(label+".store.before"):io.close_file(handle);return fail("injected_io_failure",path)
	var middle := floori(float(bytes.size())/2.0)
	var first: Dictionary=io.write_exact(handle,bytes.slice(0,middle))
	if not first.ok:io.close_file(handle);return fail("write_failed",path)
	if not boundary(label+".store.partial"):io.close_file(handle);return fail("injected_io_failure",path)
	var second: Dictionary=io.write_exact(handle,bytes.slice(middle))
	if not second.ok:io.close_file(handle);return fail("write_failed",path)
	if not boundary(label+".store.after"):io.close_file(handle);return fail("injected_io_failure",path)
	if not boundary(label+".flush.before"):io.close_file(handle);return fail("injected_io_failure",path)
	var flushed: Dictionary=io.flush(handle)
	if not flushed.ok:io.close_file(handle);return fail("write_failed",path)
	if not boundary(label+".flush.after"):io.close_file(handle);return fail("injected_io_failure",path)
	if not boundary(label+".close.before"):io.close_file(handle);return fail("injected_io_failure",path)
	var closed: Dictionary=io.close_file(handle)
	if not closed.ok:return fail("write_failed",path)
	if not boundary(label+".close.after"):return fail("injected_io_failure",path)
	if not boundary(label+".readback.before"):return fail("injected_io_failure",path)
	var read := read_bytes(path)
	if not read.ok or read.bytes!=bytes:return fail("readback_failed",path)
	if not boundary(label+".readback.after"):return fail("injected_io_failure",path)
	return {"ok":true}

func rename_new(from: String, to: String, label: String, token: String = "") -> Dictionary:
	if not path_ok(from) or not path_ok(to):return fail("path_invalid",to)
	if FileAccess.file_exists(to) or DirAccess.dir_exists_absolute(to):return fail("target_conflict",to)
	if not boundary(label+".rename.before"):return fail("injected_io_failure",to)
	# nativeの同volume・置換禁止rename。存在確認は補助であり排他primitiveで確定する。
	if not token.is_empty():
		var rechecked := recover(token)
		if not rechecked.ok:return rechecked
		if rechecked.phase!="prepared":return fail("not_prepared",from)
	if not path_ok(from) or not path_ok(to):return fail("path_invalid",to)
	if not boundary(label+".native.rename.before"):return fail("injected_io_failure",to)
	var renamed: Dictionary=io.rename_file(from,to,false)
	if not renamed.ok:return fail(renamed.reason_code,to)
	if not boundary(label+".rename.after"):return fail("injected_io_failure",to)
	return {"ok":true}

func ensure_copy(tx: String, name: String, bytes: PackedByteArray, label: String) -> Dictionary:
	var final := tx.path_join(name)
	if not path_ok(final):return fail("path_invalid",final)
	if FileAccess.file_exists(final):
		var existing := read_bytes(final)
		return {"ok":true} if existing.ok and existing.bytes==bytes else fail("recovery_required",final)
	# 自取引の未完tmpだけ再書込み可。backup/確定出力には適用しない。
	var tmp := final+".tmp"
	var result := write_raw(tmp,bytes,label,true)
	if not result.ok:return result
	return rename_new(tmp,final,label)

func intent_for(source_path: String, expected_sha: String, token: String, candidate: Dictionary, h: Dictionary, session_token: String) -> Dictionary:
	return {"version":1,"source_path":io.relative_path(source_path),"source_sha256":expected_sha,"source_size":candidate.source.source_bytes.size(),"candidate_sha256":candidate.sha256,"candidate_size":candidate.bytes.size(),"migration_id":token,"generation":session_token,"policy_id":Migration.POLICY,"catalog_revision":1,"trial_id":candidate.source.document.get("_trial_id",""),"history":{"status":h.status,"path":h.path,"sha256":h.sha256,"size":h.size,"history_complete":h.history_complete},"target":"converted.json"}

func prepare(source_path: String, expected_sha: String, candidate_document: Dictionary, session_token: String) -> Dictionary:
	if session_token.is_empty() or session_token!=generation:return fail("stale_state","generation")
	var raw := read_bytes(source_path)
	if not raw.ok:return raw
	if raw.sha256!=expected_sha:return fail("source_changed",source_path)
	var candidate := plan(raw.bytes)
	if not candidate.ok:return candidate
	# 完全同値の候補は検証済み純粋結果を再利用。異なる入力はS2で拒否理由を照合。
	if not S1.differences(candidate_document,candidate.document).is_empty() or not SavedValueTypes.same_types(candidate_document,candidate.document):
		var encoded := Codec.encode_candidate(candidate_document,context)
		if not encoded.ok:return encoded
		if not S1.differences(encoded.document,candidate.document).is_empty() or not SavedValueTypes.same_types(encoded.document,candidate.document):return fail("candidate_changed","candidate")
	var tx := transaction_path(candidate.token)
	if path_ok(tx):
		var directory := DirAccess.open(tx)
		if directory!=null:
			for name in ["source.bin","converted.tmp","converted.json"]:
				if FileAccess.file_exists(tx.path_join(name)) and directory.is_equivalent(source_path,tx.path_join(name)):return fail("same_file",source_path)
	if source_path.begins_with(root.path_join("transactions")+"/"):return fail("same_file",source_path)
	var h := history(candidate.source.document)
	if not h.ok:return h
	var intent := intent_for(source_path,expected_sha,candidate.token,candidate,h,session_token)
	var claim := acquire(tx)
	if not claim.ok:return claim
	if FileAccess.file_exists(tx.path_join("intent.json")):
		var prior := read_json(tx.path_join("intent.json"))
		if not prior.ok:return fail("conflict",tx)
		# raw同一の別名は元取引のsource_pathを保持して再利用する。
		intent.source_path=prior.value.get("source_path","")
		if not S1.differences(prior.value,intent).is_empty():return fail("conflict",tx)
		var recovered := recover(candidate.token)
		if not recovered.ok:return recovered
		if recovered.phase=="committed":return recovered
	else:
		for name in ["source.bin","source.bin.tmp","history.bin","history.bin.tmp","converted.tmp","converted.json","receipt.json","receipt.tmp"]:
			if FileAccess.file_exists(tx.path_join(name)):return fail("conflict",tx.path_join(name))
		if lease_index==0 and FileAccess.file_exists(tx.path_join("intent.json.tmp")):return fail("conflict",tx)
		var stored := ensure_copy(tx,"intent.json",JSON.stringify(intent,"",true,true).to_utf8_buffer(),"intent")
		if not stored.ok:return stored
	var backup := ensure_copy(tx,"source.bin",raw.bytes,"source")
	if not backup.ok:return backup
	if h.status in ["normal","unclean","corrupt"]:
		var saved := ensure_copy(tx,"history.bin",h.bytes,"history")
		if not saved.ok:return saved
	var written := write_raw(tx.path_join("converted.tmp"),candidate.bytes,"candidate",true)
	if not written.ok:return written
	var verified := verify_candidate(tx.path_join("converted.tmp"),candidate)
	if not verified.ok:return verified
	var receipt := write_receipt(tx,intent,"prepared")
	if not receipt.ok:return receipt
	return recover(candidate.token)

func verify_candidate(path: String, candidate: Dictionary) -> Dictionary:
	var raw := read_bytes(path)
	if not raw.ok:return raw
	if raw.bytes!=candidate.bytes or raw.sha256!=candidate.sha256:return fail("recovery_required",path)
	var decoded := Codec.decode_source(raw.bytes,context)
	if not decoded.ok or not S1.differences(decoded.document,candidate.document).is_empty() or not SavedValueTypes.same_types(decoded.document,candidate.document):return fail("recovery_required",path)
	if decoded.document.equipment_migration.migration_id!=candidate.token:return fail("recovery_required",path)
	return {"ok":true}

func write_receipt(tx: String, intent: Dictionary, phase: String) -> Dictionary:
	var value := {"version":1,"intent":intent,"phase":phase}
	var temp := tx.path_join("receipt.tmp")
	var result := write_raw(temp,JSON.stringify(value,"",true,true).to_utf8_buffer(),"receipt-"+phase,true)
	if not result.ok:return result
	var final := tx.path_join("receipt.json")
	if not path_ok(final):return fail("path_invalid",final)
	if not boundary("receipt-"+phase+".rename.before"):return fail("injected_io_failure",final)
	if not io.rename_file(temp,final,true).ok:return fail("receipt_failed",final)
	if not boundary("receipt-"+phase+".rename.after"):return fail("injected_io_failure",final)
	return {"ok":true}

func recover(token: String) -> Dictionary:
	var tx := transaction_path(token)
	if tx.is_empty() or not path_ok(tx):return fail("path_invalid",tx)
	if not path_ok(tx.path_join("intent.json")):return fail("path_invalid",tx)
	if not FileAccess.file_exists(tx.path_join("intent.json")):
		return {"ok":true,"reason_code":"ok","phase":"incomplete","token":token,"errors":[]}
	var stored := read_json(tx.path_join("intent.json"))
	if not stored.ok:return fail("recovery_required",tx)
	var intent: Dictionary=stored.value
	if not intent.get("source_path") is String or not intent.get("source_sha256") is String or not intent.get("generation") is String:return fail("recovery_required",tx)
	var source_path := root.path_join(intent.source_path)
	if source_path.begins_with(root.path_join("transactions")+"/"):return fail("same_file",source_path)
	var dir := DirAccess.open(tx)
	for name in ["source.bin","source.bin.tmp","converted.tmp","converted.json","history.bin","intent.json","receipt.json"]:
		var check_path := tx.path_join(name)
		if not path_ok(check_path):return fail("path_invalid",check_path)
		if FileAccess.file_exists(check_path) and dir.is_equivalent(source_path,check_path):return fail("same_file",check_path)
	var raw := read_bytes(source_path)
	if not raw.ok:return raw
	if raw.sha256!=intent.source_sha256:return fail("source_changed",source_path)
	var candidate := plan(raw.bytes)
	if not candidate.ok:return candidate
	var h := history(candidate.source.document)
	if not h.ok:return h
	var expected := intent_for(source_path,raw.sha256,token,candidate,h,intent.generation)
	if candidate.token!=token or not S1.differences(intent,expected).is_empty():return fail("recovery_required",tx)
	if FileAccess.file_exists(tx.path_join("receipt.json")):
		var r := read_json(tx.path_join("receipt.json"))
		if not r.ok or r.value.size()!=3 or r.value.get("version")!=1 or r.value.get("phase") not in ["prepared","committed"] or not S1.differences(r.value.get("intent"),intent).is_empty():return fail("recovery_required",tx.path_join("receipt.json"))
	var backup := tx.path_join("source.bin")
	if FileAccess.file_exists(backup):
		var original := read_bytes(backup)
		if not original.ok or original.bytes!=raw.bytes:return fail("recovery_required",backup)
	var history_path := tx.path_join("history.bin")
	if FileAccess.file_exists(history_path):
		var history_raw := read_bytes(history_path)
		if not history_raw.ok or h.status not in ["normal","unclean","corrupt"] or history_raw.bytes!=h.bytes:return fail("recovery_required",history_path)
	var enough: bool=FileAccess.file_exists(backup) and (h.status not in ["normal","unclean","corrupt"] or FileAccess.file_exists(history_path))
	var phase := "incomplete"
	for name in ["converted.tmp","converted.json"]:
		var path := tx.path_join(name)
		if FileAccess.file_exists(path):
			var verified := verify_candidate(path,candidate)
			if verified.ok:
				if not enough:return fail("recovery_required",path)
				phase="committed" if name=="converted.json" else "prepared"
			elif name=="converted.json":return fail("recovery_required",path)
	# 不完tmpはprepareで同取引を再生成する。外部確定物は修復しない。
	return {"ok":true,"reason_code":"ok","phase":phase,"committed":phase=="committed","applied":false,"token":token,"migration_id":token,"quantity":candidate.document.equipment_stock.instances.size(),"candidate_sha256":candidate.sha256,"history":expected.history,"errors":[]}

func commit(token: String, session_token: String) -> Dictionary:
	if session_token.is_empty() or session_token!=generation:return fail("stale_state","generation")
	var tx := transaction_path(token)
	if tx.is_empty():return fail("path_invalid",tx)
	var claim := acquire(tx)
	if not claim.ok:return claim
	var recovered := recover(token)
	if not recovered.ok:return recovered
	if recovered.get("phase")=="incomplete":return fail("not_prepared",tx)
	var stored := read_json(tx.path_join("intent.json"))
	if not stored.ok:return stored
	if stored.value.generation!=session_token:return fail("stale_state","generation")
	if recovered.get("phase")=="committed":return recovered
	var result := rename_new(tx.path_join("converted.tmp"),tx.path_join("converted.json"),"commit",token)
	# rename戻り値/receipt更新失敗でも実出力を再照合して成功点を認識する。
	var after := recover(token)
	if after.ok and after.get("phase")=="committed":
		var receipt := write_receipt(tx,stored.value,"committed")
		after["receipt_updated"]=receipt.ok
		return after
	return result if not result.ok else after
