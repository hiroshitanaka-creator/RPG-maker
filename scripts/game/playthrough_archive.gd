class_name PlaythroughArchive
extends RefCounted

var directory: String
var identifier: String = ""
var lifetime := PlaySessionMetrics.new()
var history_complete: bool = true
var builds: Array[String] = []
var issue: String = ""
var run_open: bool = true
var duration_finished: bool = false
var _last_flush: int = -10000
var _last_context: Dictionary = {}

func _init(root: String) -> void:
	directory = root

static func valid_id(value: String) -> bool:
	return value.length() == 32 and value.is_valid_hex_number(false)

func start(progress: PlaySessionMetrics, complete_history: bool = true, parent: String = "") -> void:
	identifier = Crypto.new().generate_random_bytes(16).hex_encode()
	lifetime = PlaySessionMetrics.new()
	lifetime.restore(progress.snapshot())
	history_complete = complete_history
	builds.assign([BuildIdentity.current()["id"]])
	issue = ""
	run_open = true
	duration_finished = false
	attach(progress)
	lifetime.record_event("trial_started",{"parent":parent,"history_complete":history_complete})

func attach(progress: PlaySessionMetrics) -> void:
	progress.observer = lifetime
	var build_id: String = BuildIdentity.current()["id"]
	if not build_id in builds:
		builds.append(build_id)
	if progress.source != "unclassified":
		lifetime.set_source(progress.source)
	if progress.source_changed:
		lifetime.source_changed = true

func resume(record_id: String, progress: PlaySessionMetrics) -> void:
	if record_id == identifier and not identifier.is_empty():
		attach(progress)
		lifetime.record_event("progress_loaded",{"progress_elapsed_ms":progress.elapsed_ms})
		return
	var path := directory.path_join(record_id+".json")
	var restored := PlaySessionMetrics.new()
	var value: Variant = null
	if valid_id(record_id) and FileAccess.file_exists(path):
		var parser := JSON.new()
		if parser.parse(FileAccess.get_file_as_string(path)) == OK:
			value = parser.data
	var valid: bool = value is Dictionary and value.get("trial_id") == record_id and value.get("archive_version") == 1 and value.get("history_complete") is bool and value.get("builds") is Array
	valid = valid and value.get("run_open",true) is bool and value.get("duration_finished",false) is bool
	if valid:
		for build in value["builds"]:
			valid = valid and build is String and build.length() == 64 and build.is_valid_hex_number(false)
		valid = valid and not value["builds"].is_empty() and restored.restore(value)
	if not valid:
		start(progress,false,record_id)
		lifetime.record_event("history_unavailable",{"reason":"legacy_or_missing_or_invalid_archive"})
		return
	identifier = record_id
	lifetime = restored
	history_complete = value["history_complete"]
	builds.assign(value["builds"])
	issue = ""
	run_open = true
	duration_finished = bool(value.get("duration_finished",false))
	lifetime.clock_closed = duration_finished
	if value.get("run_open",true):
		history_complete = false
		lifetime.record_event("unclean_restart",{"tail_time_unknown":true})
	attach(progress)
	lifetime.record_event("progress_loaded",{"progress_elapsed_ms":progress.elapsed_ms})

func document(progress: PlaySessionMetrics, context: Dictionary) -> Dictionary:
	var details := context.duplicate(true)
	details["history_complete"] = history_complete and issue.is_empty()
	details["mixed_builds"] = builds.size() != 1
	lifetime.completed = progress.completed
	var value := lifetime.report(details)
	value["archive_version"] = 1
	value["trial_id"] = identifier
	value["history_complete"] = details["history_complete"]
	value["run_open"] = run_open
	value["duration_finished"] = duration_finished
	value["builds"] = builds.duplicate()
	value["measurement_scope"] = "whole_trial"
	value["progress_snapshot"] = progress.snapshot()
	return value

func flush(progress: PlaySessionMetrics, context: Dictionary, periodic: bool = false) -> bool:
	if identifier.is_empty():
		return true
	if progress.completed and context.get("content_revision",0) == 1 and context.get("circuits_completed",[]).size() == 5:
		duration_finished = true
		lifetime.clock_closed = true
	if periodic and Time.get_ticks_msec()-_last_flush < 10000:
		return issue.is_empty()
	_last_flush = Time.get_ticks_msec()
	_last_context = context.duplicate(true)
	if DirAccess.make_dir_recursive_absolute(directory) != OK or not PlaySessionMetrics.write_json(directory.path_join(identifier+".json"),document(progress,context)):
		issue = "試遊履歴を保存できません。保存先の空き容量と書込み権限を確認してください。"
		history_complete = false
		return false
	issue = ""
	return true
