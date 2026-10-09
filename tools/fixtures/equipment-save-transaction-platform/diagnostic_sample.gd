extends SceneTree
const T = preload("res://scripts/game/equipment_save_transaction.gd")
const Measured = preload("res://tools/fixtures/equipment-save-transaction-platform/diagnostic_transaction.gd")
const IO = preload("res://tools/fixtures/equipment-save-transaction-platform/diagnostic_io.gd")

func _initialize() -> void:
	var entered := Time.get_ticks_usec()
	var args := OS.get_cmdline_user_args()
	var root: String=args[0]
	var measured: bool=args[1]=="on"
	var dependency_start := Time.get_ticks_usec()
	var session := GameSession.new()
	var context := {"legacy_session":session,"abilities":session.catalog.equipment_context_abilities()}
	var dependency_end := Time.get_ticks_usec()
	var transaction: RefCounted=Measured.new(root,context,"g1") if measured else T.new(root,context,"g1")
	var initialized := Time.get_ticks_usec()
	var native: RefCounted=IO.new(transaction.io) if measured else null
	if measured:transaction.io=native
	var state := var_to_bytes(session.export_state())
	var metrics := var_to_bytes(session.play_metrics.snapshot())
	var source: String=root.path_join("source.json")
	var begin := Time.get_ticks_usec()
	var raw: Dictionary=transaction.read_bytes(source)
	var planned: Dictionary=transaction.plan(raw.bytes) if raw.ok else raw
	var result: Dictionary=transaction.prepare(source,raw.sha256,planned.document,"g1") if planned.ok else planned
	if result.ok:result=transaction.commit(result.token,"g1")
	var finished := Time.get_ticks_usec()
	var quantity: int=result.get("quantity",0)
	var value := {"measured":measured,"pid":OS.get_process_id(),"initialize_enter_us":entered,"dependency_start_us":dependency_start,"dependency_end_us":dependency_end,"transaction_initialized_us":initialized,"transaction_start_us":begin,"transaction_end_us":finished,"result":result,"quantity":quantity,"source_sha256":FileAccess.get_sha256(source),"output_sha256":result.get("candidate_sha256",""),"memory_unchanged":state==var_to_bytes(session.export_state()) and metrics==var_to_bytes(session.play_metrics.snapshot()),"spans":transaction.spans if measured else [],"native_spans":native.spans if measured else []}
	var file := FileAccess.open(root.path_join("timing-result.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(value,"",true,true));file.close()
	print("DIAGNOSTIC_SAMPLE: ",JSON.stringify({"measured":measured,"phase":result.get("phase",""),"quantity":quantity}))
	quit(0 if result.ok and result.get("committed",false) and value.memory_unchanged else 1)
