extends RefCounted
const T = preload("res://scripts/game/equipment_save_transaction.gd")
const C = preload("res://scripts/game/equipment_save_codec.gd")
const V = preload("res://scripts/game/equipment_document_validation.gd")
const M = preload("res://scripts/game/equipment_save_migration.gd")
const S1 = preload("res://scripts/game/equipment_save_validation.gd")
const F = preload("res://tools/fixtures/equipment-save-codec/fixtures.gd")
var config: Dictionary
var points: Array=[]

func hook(point: String) -> bool:
	points.append(point)
	if config.get("kill_point","")==point:
		var marker := FileAccess.open(config.root.path_join("paused.json"),FileAccess.WRITE)
		marker.store_string(JSON.stringify({"point":point,"pid":OS.get_process_id()}));marker.close()
		while not FileAccess.file_exists(config.root.path_join("release")):OS.delay_msec(5)
	return config.get("fail_point","")!=point

func run_config(options: Dictionary, supplied_session: GameSession = null) -> void:
	config=options
	points=[]
	var session: GameSession=GameSession.new() if supplied_session==null else supplied_session
	var context := {"legacy_session":session,"abilities":session.catalog.equipment_context_abilities()}
	if config.get("context","")=="null-session":context.legacy_session=null
	if config.get("context","")=="null-abilities":context.abilities=null
	var transaction := T.new(config.root,context,config.get("generation","g1"),hook)
	var source: String=config.get("source",config.root.path_join("source.json"))
	var state := var_to_bytes(session.export_state())
	var metrics := var_to_bytes(session.play_metrics.snapshot())
	var result: Dictionary
	match config.operation:
		"fixture":
			var document := F.region()
			if config.get("unlocked",false):document.progress_flags["job_change_unlocked"]=true
			if config.get("trial",false):document["_trial_id"]="0123456789abcdef0123456789abcdef"
			if config.get("typed",false):document["_play_session"]=F.metrics();document=F.typed(document)
			var bytes := JSON.stringify(document,"",true,true).to_utf8_buffer()
			if config.get("alternate",false):bytes="  ".to_utf8_buffer()+bytes+"\n".to_utf8_buffer()
			var file := FileAccess.open(source,FileAccess.WRITE)
			file.store_buffer(bytes);file.close()
			if config.get("history","") in ["normal","unclean","corrupt"]:
				DirAccess.make_dir_recursive_absolute(config.root.path_join("history"))
				var history_file := FileAccess.open(config.root.path_join("history/0123456789abcdef0123456789abcdef.json"),FileAccess.WRITE)
				if config.history=="corrupt":history_file.store_string("{broken raw history\n")
				else:
					var value := F.metrics()
					value.merge({"archive_version":1,"trial_id":document._trial_id,"history_complete":true,"builds":["a".repeat(64)],"run_open":config.history=="unclean","duration_finished":false})
					history_file.store_string(JSON.stringify(value,"",true,true))
				history_file.close()
			result={"ok":true,"reason_code":"ok","source_sha256":C.hash_bytes(bytes),"token":M.migration_id(C.hash_bytes(bytes))}
		"inspect":result=transaction.inspect(source)
		"recover":result=transaction.recover(config.token)
		"commit":result=transaction.commit(config.token,config.get("session_token","g1"))
		"prepare","full","resume":
			var recovery_before: Dictionary={}
			if config.operation=="resume":recovery_before=transaction.recover(config.token)
			var raw := transaction.read_bytes(source)
			if not raw.ok:result=raw
			else:
				var planned := transaction.plan(raw.bytes)
				if not planned.ok:result=planned
				else:
					var document: Dictionary=planned.document
					if config.get("candidate","")=="quantity":document.equipment_stock.instances["bad"]="practice_blade"
					if config.get("candidate","")=="value":document.party[0].hp-=1
					if config.get("candidate","")=="types":document["_saved_value_types"]=null
					result=transaction.prepare(source,config.get("expected_sha",raw.sha256),document,config.get("session_token","g1"))
					if result.ok and config.operation in ["full","resume"]:result=transaction.commit(result.token,config.get("session_token","g1"))
			if config.operation=="resume":result["recovery_before"]=recovery_before
		"decode":
			var read := transaction.read_bytes(source)
			result=read if not read.ok else C.decode_source(read.bytes,context)
			if result.ok:
				result["quantity"]=result.document.equipment_stock.instances.size()
				result["migration_id"]=result.document.equipment_migration.migration_id
				result["metadata"]=result.document.get("_saved_value_types",{})
				result.erase("document");result.erase("source_bytes")
		_:
			result={"ok":false,"reason_code":"unknown_operation"}
	result["memory_unchanged"]=state==var_to_bytes(session.export_state()) and metrics==var_to_bytes(session.play_metrics.snapshot())
	result["user_dir"]=OS.get_user_data_dir()
	result["pid"]=OS.get_process_id()
	result["points"]=points
	if result.has("source_bytes"):result.erase("source_bytes")
	if result.has("decoder"):
		var decoder: Dictionary=result.decoder
		result.decoder={"ok":decoder.ok,"reason_code":decoder.reason_code,"observations":decoder.get("observations",{})}
	var output := FileAccess.open(config.root.path_join(config.get("result","result.json")),FileAccess.WRITE)
	output.store_string(JSON.stringify(result,"",true,true));output.close()
	print("TRANSACTION_PROBE: ",JSON.stringify({"ok":result.ok,"reason_code":result.get("reason_code","ok"),"phase":result.get("phase","")}))
