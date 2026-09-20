class_name PlaySessionMetrics
extends RefCounted

const IDLE_MS := 60000
var source: String = "unclassified"
var active_ms: int = 0
var idle_ms: int = 0
var pause_ms: int = 0
var elapsed_ms: int = 0
var last_input_ms: int = 0
var chapter: String = "1"
var chapters: Dictionary = {}
var counters: Dictionary = {}
var answers: Array[Dictionary] = []
var events: Array[Dictionary] = []
var completed: bool = false
var source_changed: bool = false
var _clock_ms: int = -1
var observer: PlaySessionMetrics
var clock_closed: bool = false


func touch() -> void:
	last_input_ms = Time.get_ticks_msec()


func update_clock(mode: String, current_chapter: int, focused: bool) -> void:
	var now := Time.get_ticks_msec()
	if _clock_ms < 0:
		_clock_ms = now
		last_input_ms = now
		return
	var delta := maxi(0,now-_clock_ms)
	_clock_ms = now
	chapter = str(current_chapter)
	if not chapters.has(chapter):
		chapters[chapter] = {"active_ms":0,"elapsed_ms":0}
	if completed:
		return
	var bucket := "active_ms"
	if not focused or mode in ["menu","paused","complete","review"]:
		bucket = "pause_ms"
	elif now-last_input_ms > IDLE_MS:
		bucket = "idle_ms"
	_accept_delta(delta,chapter,bucket)
	if observer != null:
		observer._accept_delta(delta,chapter,bucket)


func _accept_delta(delta: int, current_chapter: String, bucket: String) -> void:
	if clock_closed:
		return
	chapter = current_chapter
	if not chapters.has(chapter):
		chapters[chapter] = {"active_ms":0,"elapsed_ms":0}
	elapsed_ms += delta
	chapters[chapter]["elapsed_ms"] += delta
	match bucket:
		"pause_ms": pause_ms += delta
		"idle_ms": idle_ms += delta
		_:
			active_ms += delta
			chapters[chapter]["active_ms"] += delta


func mark(name: String, amount: int = 1) -> void:
	counters[name] = int(counters.get(name,0))+amount
	if observer != null:
		observer.mark(name,amount)


func record_event(kind: String, details: Dictionary) -> void:
	events.append({"kind":kind,"chapter":chapter,"elapsed_ms":elapsed_ms,"details":details.duplicate(true)})
	if observer != null:
		observer.chapter = chapter
		observer.record_event(kind,details)


func set_source(value: String) -> bool:
	if value not in ["human","automated"]:
		return false
	if source != "unclassified" and source != value:
		source_changed = true
	source = value
	if observer != null:
		observer.set_source(value)
	return true


func add_review(exploration: int, reward: int, difficulty: int, note: String) -> bool:
	if source != "human" or exploration not in range(1,6) or reward not in range(1,6) or difficulty not in range(1,6):
		return false
	answers.append({"chapter":chapter,"active_ms":active_ms,"exploration":exploration,"reward":reward,"difficulty":difficulty,"note":note.left(2000),"self_reported":true})
	if observer != null:
		observer.chapter = chapter
		observer.add_review(exploration,reward,difficulty,note)
	return true


func snapshot() -> Dictionary:
	return {"version":1,"source":source,"source_changed":source_changed,"active_ms":active_ms,"elapsed_ms":elapsed_ms,"idle_ms":idle_ms,"pause_ms":pause_ms,"chapters":chapters.duplicate(true),"counters":counters.duplicate(true),"answers":answers.duplicate(true),"events":events.duplicate(true),"completed":completed}


func restore(value: Dictionary) -> bool:
	if value.is_empty():
		return true
	if value.get("version") != 1 or value.get("source") not in ["unclassified","human","automated"] or not value.get("chapters") is Dictionary or not value.get("counters") is Dictionary or not value.get("answers") is Array:
		return false
	for key in ["active_ms","elapsed_ms","idle_ms","pause_ms"]:
		if not BattleCatalog._is_integer(value.get(key),0):
			return false
	if int(value["elapsed_ms"]) != int(value["active_ms"])+int(value["idle_ms"])+int(value["pause_ms"]):
		return false
	if not value.get("completed") is bool or not value.get("source_changed") is bool:
		return false
	var chapter_active := 0
	var chapter_elapsed := 0
	for key in value["chapters"]:
		var totals: Variant = value["chapters"][key]
		if not key is String or not totals is Dictionary or not BattleCatalog._is_integer(totals.get("active_ms"),0) or not BattleCatalog._is_integer(totals.get("elapsed_ms"),0) or totals["active_ms"] > totals["elapsed_ms"]:
			return false
		chapter_active += int(totals["active_ms"])
		chapter_elapsed += int(totals["elapsed_ms"])
	if chapter_active != int(value["active_ms"]) or chapter_elapsed != int(value["elapsed_ms"]):
		return false
	for key in value["counters"]:
		if not key is String or not BattleCatalog._is_integer(value["counters"][key],0):
			return false
	for record in value["answers"]:
		if not record is Dictionary or not record.has_all(["chapter","active_ms","exploration","reward","difficulty","note","self_reported"]) or record["self_reported"] != true or not record["note"] is String:
			return false
		if not record["chapter"] is String or not BattleCatalog._is_integer(record["active_ms"],0) or record["active_ms"] > value["active_ms"] or record["note"].length() > 2000:
			return false
		for key in ["exploration","reward","difficulty"]:
			if not BattleCatalog._is_integer(record[key],1) or int(record[key]) > 5:
				return false
	if not value.get("events",[]) is Array:
		return false
	for event in value.get("events",[]):
		if not event is Dictionary or not event.get("kind") is String or not event.get("chapter") is String or not event.get("details") is Dictionary or not BattleCatalog._is_integer(event.get("elapsed_ms"),0) or event["elapsed_ms"] > value["elapsed_ms"]:
			return false
	source = value["source"]
	source_changed = value["source_changed"]
	active_ms = int(value["active_ms"])
	elapsed_ms = int(value["elapsed_ms"])
	idle_ms = int(value["idle_ms"])
	pause_ms = int(value["pause_ms"])
	chapters = {}
	for key in value["chapters"]:
		chapters[key] = {"active_ms":int(value["chapters"][key]["active_ms"]),"elapsed_ms":int(value["chapters"][key]["elapsed_ms"])}
	counters = {}
	for key in value["counters"]:
		counters[key] = int(value["counters"][key])
	answers.assign(_integers(value["answers"]))
	events.assign(_integers(value.get("events",[])))
	completed = value["completed"]
	_clock_ms = -1
	return true


func report(context: Dictionary = {}) -> Dictionary:
	var value := snapshot()
	var play_ms := active_ms+idle_ms
	value["foreground_play_ms"] = play_ms
	value["idle_review_required"] = idle_ms > 0
	value["target_play_minutes"] = [300,360]
	value["target_duration_observed"] = source == "human" and not source_changed and completed and context.get("history_complete",false) and not context.get("mixed_builds",true) and context.get("content_revision",0) == 1 and context.get("circuits_completed",[]).size() == 5 and play_ms >= 300*60000 and play_ms <= 360*60000
	value["human_review_received"] = source == "human" and not answers.is_empty()
	value["human_identity_verified"] = false
	value["acceptance_status"] = "UNREVIEWED"
	value["recorded_at"] = Time.get_datetime_string_from_system(true)
	value["game"] = context.duplicate(true)
	return value


func export_report(path: String, context: Dictionary = {}) -> bool:
	return write_json(path,report(context))


static func write_json(path: String, value: Dictionary) -> bool:
	var temporary := path+".tmp"
	var file := FileAccess.open(temporary,FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(value,"  ",true,true))
	file.flush()
	var written := file.get_error() == OK
	file.close()
	if not written:
		DirAccess.remove_absolute(temporary)
		return false
	return DirAccess.rename_absolute(temporary,path) == OK


static func _integers(value: Variant) -> Variant:
	if value is Dictionary:
		var result: Dictionary = {}
		for key in value:
			result[key] = _integers(value[key])
		return result
	if value is Array:
		var result: Array = []
		for item in value:
			result.append(_integers(item))
		return result
	return int(value) if value is float and value == floor(value) else value
