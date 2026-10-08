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
var devices: Dictionary={}
var root_device := ""
var planned_cache: Dictionary={}
var dependency_bytes := PackedByteArray()
var verified_bytes := PackedByteArray()
var lease_index := -1

func _init(qa_root: String, explicit_context: Dictionary, session_generation: String, qa_hook: Callable = Callable()) -> void:
	root=qa_root.trim_suffix("/")
	context=explicit_context
	generation=session_generation
	hook=qa_hook

func fail(code: String, path: String) -> Dictionary:
	return Codec.failure(code,path)

func boundary(point: String) -> bool:
	return not hook.is_valid() or hook.call(point)

func path_ok(path: String) -> bool:
	# S3で実証するLinuxだけを受理。リンクは内部向きも拒否し、未実証OSへfallbackしない。
	if OS.get_name()!="Linux" or not root.is_absolute_path() or not path.is_absolute_path():return false
	if root=="/" or root.contains("\\") or path.contains("\\") or root.contains(":") or path.contains(":"):return false
	if ".." in root.split("/") or ".." in path.split("/") or "." in path.split("/"):return false
	if path!=root and not path.begins_with(root+"/"):return false
	var cursor := "/"
	for part in path.split("/",false):
		cursor=cursor.path_join(part)
		var parent := DirAccess.open(cursor.get_base_dir())
		if parent!=null and parent.is_link(cursor):return false
	# mount/device逸脱も検査。存在しない末尾は最初の既存親を使う。
	var existing := path
	while not FileAccess.file_exists(existing) and not DirAccess.dir_exists_absolute(existing):existing=existing.get_base_dir()
	# 同一プロセス中にmount設定が変わらない隔離QA契約で、親directoryのdeviceを再利用。
	var directory := existing
	if existing.begins_with(root.path_join("transactions")+"/") and FileAccess.file_exists(existing):directory=existing.get_base_dir()
	if root_device.is_empty():
		var output: Array=[]
		if OS.execute("stat",["-c","%d","--",root],output,true)!=0:return false
		root_device=str(output[0]).strip_edges()
	if not devices.has(directory):
		var output: Array=[]
		if OS.execute("stat",["-c","%d","--",directory],output,true)!=0:return false
		devices[directory]=str(output[0]).strip_edges()
	return devices[directory]==root_device

static func hash_raw(bytes: PackedByteArray) -> String:
	return "".sha256_text() if bytes.is_empty() else Codec.hash_bytes(bytes)

func make_directories(path: String) -> bool:
	if not path_ok(path):return false
	var current := root
	for part in path.trim_prefix(root+"/").split("/",false):
		current=current.path_join(part)
		if not DirAccess.dir_exists_absolute(current) and DirAccess.make_dir_absolute(current)!=OK:return false
	return true

func read_bytes(path: String) -> Dictionary:
	if not path_ok(path):return fail("path_invalid",path)
	if not boundary("read.open.before"):return fail("injected_io_failure",path)
	var file := FileAccess.open(path,FileAccess.READ)
	if file==null:return fail("read_failed",path)
	if not boundary("read.open.after"):file.close();return fail("injected_io_failure",path)
	var size := file.get_length()
	if not boundary("read.buffer.before"):file.close();return fail("injected_io_failure",path)
	var bytes := file.get_buffer(size)
	var error := file.get_error()
	file.close()
	if not boundary("read.buffer.after"):return fail("injected_io_failure",path)
	if bytes.size()!=size or error!=OK:return fail("read_failed",path)
	return {"ok":true,"bytes":bytes,"size":size,"sha256":hash_raw(bytes)}

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
	# 同process内だけの純粋計画cache。別processは必ずrawから再計算。
	var dependencies := var_to_bytes([context.abilities,context.legacy_session.jobs,context.get("source_build","")])
	if dependencies!=dependency_bytes:
		planned_cache.clear()
		verified_bytes=PackedByteArray()
		dependency_bytes=dependencies
	var source_hash := hash_raw(raw)
	if planned_cache.has(source_hash):return planned_cache[source_hash].duplicate(true)
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
	planned_cache[source_hash]=result.duplicate(true)
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
	var leases := tx.path_join("leases")
	if not path_ok(leases) or not make_directories(leases):return fail("backup_failed",leases)
	var dir := DirAccess.open(leases)
	# leaseはownerを指すsymlink。検証済み相対リンクだけ読取り、旧leaseは削除しない。
	var links: Array=[]
	dir.list_dir_begin()
	var name := dir.get_next()
	while not name.is_empty():
		if name.begins_with("lease-"):links.append(name)
		name=dir.get_next()
	dir.list_dir_end()
	links.sort()
	var next := 0
	if not links.is_empty():
		var last: String=links.back()
		if last!="lease-%08d" % (links.size()-1):return fail("recovery_required",leases)
		for index in range(links.size()):
			if links[index]!="lease-%08d" % index:return fail("recovery_required",leases)
		if not dir.is_link(last):return fail("recovery_required",leases)
		var ref := dir.read_link(last)
		if ref.get_file()!=ref or not ref.begins_with("owner-") or not ref.ends_with(".json"):return fail("recovery_required",leases)
		var prior := read_json(leases.path_join(ref))
		if not prior.ok or prior.value.size()!=2 or not prior.value.get("pid") is int or not prior.value.get("nonce") is String:return fail("recovery_required",leases)
		if prior.value.pid<=0 or prior.value.nonce.length()!=32 or not prior.value.nonce.is_valid_hex_number(false) or ref!="owner-%d-%s.json" % [prior.value.pid,prior.value.nonce]:return fail("recovery_required",leases)
		if owned==tx and owner==prior.value.nonce and prior.value.pid==OS.get_process_id():return {"ok":true}
		# Godotのis_process_runningは未spawn PIDでERRORを出すため、OSの読取り照会を使う。
		var process_info: Array=[]
		if OS.execute("ps",["-p",str(prior.value.pid),"-o","pid="],process_info,true)==0:return fail("busy",tx)
		next=links.size()
	owner=Crypto.new().generate_random_bytes(16).hex_encode()
	var owner_name := "owner-%d-%s.json" % [OS.get_process_id(),owner]
	var written := write_raw(leases.path_join(owner_name),JSON.stringify({"pid":OS.get_process_id(),"nonce":owner}).to_utf8_buffer(),"owner",false)
	if not written.ok:return written
	if not boundary("lease.acquire.before"):return fail("injected_io_failure",tx)
	if dir.create_link(owner_name,"lease-%08d" % next)!=OK:return fail("busy",tx)
	owned=tx
	lease_index=next
	if not boundary("lease.acquire.after"):return fail("injected_io_failure",tx)
	return {"ok":true}

func writable_file(path: String) -> bool:
	if not path_ok(path):return false
	if FileAccess.file_exists(path):
		var info: Array=[]
		if OS.execute("stat",["-c","%h","--",path],info,true)!=0 or str(info[0]).strip_edges()!="1":return false
	return true

func write_raw(path: String, bytes: PackedByteArray, label: String, replace_tmp: bool) -> Dictionary:
	if not path_ok(path):return fail("path_invalid",path)
	if FileAccess.file_exists(path) and not replace_tmp:return fail("conflict",path)
	if not boundary(label+".open.before"):return fail("injected_io_failure",path)
	if not writable_file(path):return fail("conflict",path)
	var file := FileAccess.open(path,FileAccess.WRITE)
	if file==null:return fail("write_failed",path)
	if not boundary(label+".open.after"):file.close();return fail("injected_io_failure",path)
	if not boundary(label+".store.before"):file.close();return fail("injected_io_failure",path)
	var middle := floori(float(bytes.size())/2.0)
	file.store_buffer(bytes.slice(0,middle))
	if not boundary(label+".store.partial"):file.close();return fail("injected_io_failure",path)
	file.store_buffer(bytes.slice(middle))
	var error := file.get_error()
	if error!=OK or file.get_position()!=bytes.size():file.close();return fail("write_failed",path)
	if not boundary(label+".store.after"):file.close();return fail("injected_io_failure",path)
	if not boundary(label+".flush.before"):file.close();return fail("injected_io_failure",path)
	file.flush()
	error=file.get_error()
	if error!=OK:file.close();return fail("write_failed",path)
	if not boundary(label+".flush.after"):file.close();return fail("injected_io_failure",path)
	if not boundary(label+".close.before"):file.close();return fail("injected_io_failure",path)
	file.close()
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
	# Linux GNU mvのno-clobberを使用。外部競合で既存targetを置換しない。
	if not token.is_empty():
		var rechecked := recover(token)
		if not rechecked.ok:return rechecked
		if rechecked.phase!="prepared":return fail("not_prepared",from)
	if not path_ok(from) or not path_ok(to):return fail("path_invalid",to)
	var output: Array=[]
	if OS.execute("mv",["-T","--no-clobber","--",from,to],output,true)!=0:return fail("rename_failed",to)
	if FileAccess.file_exists(from):return fail("target_conflict",to)
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
	return {"version":1,"source_path":source_path.trim_prefix(root+"/"),"source_sha256":expected_sha,"source_size":candidate.source.source_bytes.size(),"candidate_sha256":candidate.sha256,"candidate_size":candidate.bytes.size(),"migration_id":token,"generation":session_token,"policy_id":Migration.POLICY,"catalog_revision":1,"trial_id":candidate.source.document.get("_trial_id",""),"history":{"status":h.status,"path":h.path,"sha256":h.sha256,"size":h.size,"history_complete":h.history_complete},"target":"converted.json"}

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
	if verified_bytes==raw.bytes:return {"ok":true}
	var decoded := Codec.decode_source(raw.bytes,context)
	if not decoded.ok or not S1.differences(decoded.document,candidate.document).is_empty() or not SavedValueTypes.same_types(decoded.document,candidate.document):return fail("recovery_required",path)
	if decoded.document.equipment_migration.migration_id!=candidate.token:return fail("recovery_required",path)
	verified_bytes=raw.bytes.duplicate()
	return {"ok":true}

func write_receipt(tx: String, intent: Dictionary, phase: String) -> Dictionary:
	var value := {"version":1,"intent":intent,"phase":phase}
	var temp := tx.path_join("receipt.tmp")
	var result := write_raw(temp,JSON.stringify(value,"",true,true).to_utf8_buffer(),"receipt-"+phase,true)
	if not result.ok:return result
	var final := tx.path_join("receipt.json")
	if not path_ok(final):return fail("path_invalid",final)
	if not boundary("receipt-"+phase+".rename.before"):return fail("injected_io_failure",final)
	if DirAccess.rename_absolute(temp,final)!=OK:return fail("receipt_failed",final)
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
