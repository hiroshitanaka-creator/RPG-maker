extends GutTest
## 068: 実ファイルで候補順・中断状態・復旧失敗時の不変性を確かめる。

const ROOT := "user://task068_safe_save_replace"
const PATH := ROOT + "/save.json"
const TRIAL := "0123456789abcdef0123456789abcdef"
var documents: Array[String] = []
var states: Array[Dictionary] = []
var snapshots: Array[Dictionary] = []


func before_all() -> void:
	_clear(ROOT)
	assert_eq(DirAccess.make_dir_recursive_absolute(ROOT), OK)
	for count in [11, 22, 33]:
		var game := GameSession.new()
		assert_true(game.new_first_region())
		var state := game.export_state()
		state["inventory"]["potion"] = count
		assert_true(game.import_state(state))
		var values: Array[float] = [1.0, 1.5]
		game.play_metrics.record_event("保存確認", {"values":values, "integer":count})
		assert_true(game.save_game(PATH, TRIAL))
		documents.append(FileAccess.get_file_as_string(PATH))
		states.append(game.export_state())
		snapshots.append(game.play_metrics.snapshot())
	_clear(ROOT)


func before_each() -> void:
	assert_eq(DirAccess.make_dir_recursive_absolute(ROOT), OK)


func after_each() -> void:
	_clear(ROOT)


func _clear(path: String) -> void:
	if DirAccess.dir_exists_absolute(path):
		var directory := DirAccess.open(path)
		for child in directory.get_files():
			assert_eq(DirAccess.remove_absolute(path.path_join(child)), OK)
		for child in directory.get_directories():
			_clear(path.path_join(child))
		assert_eq(DirAccess.remove_absolute(path), OK)
	elif FileAccess.file_exists(path):
		assert_eq(DirAccess.remove_absolute(path), OK)


func _write(path: String, text: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	assert_not_null(file)
	if file == null:return
	file.store_string(text)
	file.flush()
	assert_eq(file.get_error(), OK)
	file.close()


func _prepare(copies: Array) -> void:
	for index in range(3):
		var path: String = PATH + ["", ".bak", ".tmp"][index]
		_clear(path)
		if copies[index] >= 0:_write(path, documents[copies[index]])
		elif copies[index] == -2:_write(path, "{broken")


func _assert_loaded(game: GameSession, index: int) -> void:
	assert_eq_deep(game.export_state(), states[index])
	assert_eq_deep(game.play_metrics.snapshot(), snapshots[index])
	assert_true(SavedValueTypes.same_types(game.export_state(), states[index]))
	assert_true(SavedValueTypes.same_types(game.play_metrics.snapshot(), snapshots[index]))


func test_candidates_and_every_interrupted_file_state() -> void:
	# 書込み途中、flush後、本物→bak後、tmp→本物後、bak削除後を含む。
	var cases := [
		[[0,-1,-1],0], [[-1,0,-1],0], [[-1,-1,0],0], [[-2,0,-1],0],
		[[0,2,1],0], [[0,2,-2],0], [[-1,0,1],0], [[1,0,-1],1],
		[[1,-1,-1],1], [[-2,-2,2],2], [[-1,-1,-2],-1], [[-2,-2,-2],-1]
	]
	for entry in cases:
		_prepare(entry[0])
		var game := GameSession.new()
		assert_eq(game.load_game(PATH), entry[1] >= 0, str(entry[0]))
		if entry[1] < 0:continue
		_assert_loaded(game, entry[1])
		# 復旧後は本物だけでも再開でき、候補のIDが保存されている。
		var document := SavedDocument.decode(JSON.parse_string(FileAccess.get_file_as_string(PATH)))
		assert_eq(document["_trial_id"], TRIAL)
		_clear(PATH + ".bak")
		_clear(PATH + ".tmp")
		var again := GameSession.new()
		assert_true(again.load_game(PATH))
		_assert_loaded(again, entry[1])


func test_all_validation_failures_fall_through_without_relocation_leak() -> void:
	var valid: Dictionary = JSON.parse_string(documents[0])
	var failures: Array[String] = ["{broken", "[]", '{"_storage_format":"invalid"}']
	for kind in ["metrics_shape", "metrics_values", "trial_type", "trial_value", "state", "types", "type_path", "type_builtin", "metric_type"]:
		var broken := valid.duplicate(true)
		# 検証の途中で位置補正が発生しても、失敗候補から外へ出さない。
		broken["overworld"]["cell"] = [0,0]
		match kind:
			"metrics_shape": broken["_play_session"] = []
			"metrics_values": broken["_play_session"]["elapsed_ms"] = -1
			"trial_type": broken["_trial_id"] = 1
			"trial_value": broken["_trial_id"] = "bad"
			"state": broken["party"] = []
			"types": broken["_saved_value_types"] = []
			"type_path": broken["_saved_value_types"]["arrays"][0]["path"] = ["missing"]
			"type_builtin": broken["_saved_value_types"]["arrays"][0]["builtin"] = TYPE_OBJECT
			"metric_type": broken["_saved_value_types"]["floats"].append(["_play_session","elapsed_ms"])
		failures.append(JSON.stringify(broken))
	for broken in failures:
		_prepare([-1,-1,1])
		_write(PATH, broken)
		_write(PATH + ".bak", broken)
		var game := GameSession.new()
		assert_true(game.load_game(PATH))
		_assert_loaded(game, 1)
		assert_false(game.position_relocated)
		# 同じ候補が最後まで不正ならfalseで、既存状態も補正フラグも不変。
		for suffix in ["", ".bak", ".tmp"]:_write(PATH + suffix, broken)
		game.position_relocated = true
		var previous_metrics := game.play_metrics
		assert_false(game.load_game(PATH))
		_assert_loaded(game, 1)
		assert_same(game.play_metrics, previous_metrics)
		assert_true(game.position_relocated)


func test_legacy_omissions_and_candidate_id_do_not_use_current_archive() -> void:
	for suffix in [".bak", ".tmp"]:
		for with_id in [false, true]:
			_prepare([-1,-1,-1])
			var legacy := states[0].duplicate(true)
			if with_id:legacy["_trial_id"] = TRIAL
			_write(PATH + suffix, JSON.stringify(legacy))
			var game := GameSession.new()
			assert_true(game.new_first_region())
			assert_true(game.enable_recording(ROOT + "/archive"))
			assert_true(game.load_game(PATH))
			assert_eq_deep(game.export_state(), states[0])
			assert_eq_deep(game.play_metrics.snapshot(), PlaySessionMetrics.new().snapshot())
			var document := SavedDocument.decode(JSON.parse_string(FileAccess.get_file_as_string(PATH)))
			assert_eq(document.get("_trial_id", ""), TRIAL if with_id else "")
			assert_eq(document.has("_trial_id"), with_id)


func test_recovery_write_failure_keeps_session_archive_and_source_unchanged() -> void:
	_prepare([-2,0,-1])
	assert_eq(DirAccess.make_dir_absolute(PATH + ".tmp"), OK)
	var game := GameSession.new()
	assert_true(game.new_first_region())
	assert_true(game.enable_recording(ROOT + "/archive"))
	game.position_relocated = true
	game._pending_region_travel = "保持"
	game._region_story = {"保持":true}
	var state := game.export_state()
	var metrics := game.play_metrics
	var archive := game._archive
	var lifetime := archive.lifetime.snapshot()
	var identifier := archive.identifier
	var clock := archive._last_flush
	assert_false(game.load_game(PATH))
	assert_eq_deep(game.export_state(), state)
	assert_same(game.play_metrics, metrics)
	assert_same(game._archive, archive)
	assert_eq_deep(archive.lifetime.snapshot(), lifetime)
	assert_eq(archive.identifier, identifier)
	assert_eq(archive._last_flush, clock)
	assert_true(archive.run_open)
	assert_true(game.position_relocated)
	assert_eq(game._pending_region_travel, "保持")
	assert_eq(game._region_story, {"保持":true})
	assert_eq(FileAccess.get_file_as_string(PATH + ".bak"), documents[0])
	assert_eq(FileAccess.get_file_as_string(PATH), "{broken")


func test_save_and_write_json_preserve_old_files_when_backup_is_blocked() -> void:
	_prepare([0,-1,-1])
	assert_eq(DirAccess.make_dir_absolute(PATH + ".bak"), OK)
	var game := GameSession.new()
	assert_true(game.import_state(states[1]))
	assert_false(game.save_game(PATH))
	assert_eq(FileAccess.get_file_as_string(PATH), documents[0])
	assert_false(game._read_save_candidate(PATH + ".tmp").is_empty())
	assert_true(DirAccess.dir_exists_absolute(PATH + ".bak"))
	assert_false(PlaySessionMetrics.write_json(PATH, {"new":true}))
	assert_eq(FileAccess.get_file_as_string(PATH), documents[0])
	assert_eq(JSON.parse_string(FileAccess.get_file_as_string(PATH + ".tmp")), {"new":true})
	assert_true(DirAccess.dir_exists_absolute(PATH + ".bak"))


func test_only_temporary_is_preserved_before_open_or_replacement_failure() -> void:
	for blocker in ["", ".bak"]:
		_prepare([-1,-1,0])
		assert_eq(DirAccess.make_dir_absolute(PATH + blocker), OK)
		var game := GameSession.new()
		assert_true(game.import_state(states[1]))
		assert_false(game.save_game(PATH))
		var kept := ".bak" if blocker.is_empty() else ".tmp"
		assert_eq(FileAccess.get_file_as_string(PATH + kept), documents[0])
		assert_false(PlaySessionMetrics.write_json(PATH, {"new":true}))
		assert_eq(FileAccess.get_file_as_string(PATH + kept), documents[0])


func test_invalid_new_metrics_do_not_replace_valid_backup() -> void:
	_prepare([-2,0,-1])
	var game := GameSession.new()
	assert_true(game.import_state(states[1]))
	game.play_metrics.elapsed_ms = -1
	assert_false(game.save_game(PATH))
	assert_eq(FileAccess.get_file_as_string(PATH + ".bak"), documents[0])
	assert_eq(FileAccess.get_file_as_string(PATH), "{broken")


func test_successful_saves_replace_and_clean_stale_backups() -> void:
	for copies in [[0,2,1],[-2,0,-1],[-1,-1,0],[-2,-2,0]]:
		_prepare(copies)
		var game := GameSession.new()
		assert_true(game.import_state(states[1]))
		assert_true(game.save_game(PATH, TRIAL))
		var loaded := GameSession.new()
		assert_true(loaded.load_game(PATH))
		assert_eq_deep(loaded.export_state(), states[1])
		assert_false(FileAccess.file_exists(PATH + ".bak"))
		assert_false(FileAccess.file_exists(PATH + ".tmp"))
		_prepare(copies)
		assert_true(PlaySessionMetrics.write_json(PATH, {"new":true}))
		assert_eq(FileAccess.get_file_as_string(PATH), JSON.stringify({"new":true}, "  ", true, true))
		assert_false(FileAccess.file_exists(PATH + ".bak"))
		assert_false(FileAccess.file_exists(PATH + ".tmp"))
