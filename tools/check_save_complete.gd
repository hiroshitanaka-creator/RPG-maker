extends "res://tools/check_story_campaign.gd"

const Compare = preload("res://tools/save_state_comparison.gd")
var checked: Dictionary = {}
var covered: Dictionary = {}
var receipts: Array = []
var variant_counter := 0
var run_token := str(Time.get_ticks_usec())

func _run() -> void:
	var original := {"integer":1,"array":["a","b"],"nested":{"flag":true}}
	var mutations: Array = []
	var changed := original.duplicate(true)
	changed.erase("integer");mutations.append(changed)
	changed = original.duplicate(true);changed["integer"] = 1.0;mutations.append(changed)
	changed = original.duplicate(true);changed["integer"] = 2;mutations.append(changed)
	changed = original.duplicate(true);changed["array"] = ["b","a"];mutations.append(changed)
	changed = original.duplicate(true);changed["array"] = ["a"];mutations.append(changed)
	changed = original.duplicate(true);changed["nested"]["new"] = false;mutations.append(changed)
	var typed_array: Array[String] = ["a","b"]
	changed = original.duplicate(true);changed["array"] = typed_array;mutations.append(changed)
	if not _check(Compare.differences(original,original.duplicate(true),"$",[]).is_empty(),"同一状態の型比較が一致する"):return
	for mutation in mutations:
		if not _check(not Compare.differences(original,mutation,"$",[]).is_empty(),"欠落・型・値・順序・長さ・追加の改変を検出する"):return
	if not _check(not Compare.unlisted({"unlisted_field":1}).is_empty(),"列挙外の保存項目を無視しない"):return
	await super._run()

func _detour(main: Node, _state: Dictionary, _entry: Dictionary) -> bool:
	var state: Dictionary = main.game.export_state()
	var key := JSON.stringify([state["world"]["quest_step"],state.get("expedition",{}),state.get("story_task",{}),state.get("story_battle",{})])
	if checked.has(key):return false
	checked[key] = true
	if not _roundtrip(main.game,"route_"+str(checked.size())):return true
	if not main.game.is_returning_to_town() and state["world"]["location"] not in ChapterOne.TOWNS:
		var returning := _fork(main.game)
		if returning.return_to_town() and not _roundtrip(returning,"return_"+str(checked.size())):return true
	return false

func _fork(source: GameSession) -> GameSession:
	var result := GameSession.new()
	result.new_game(source.export_state()["party"].size())
	_check(result.import_state(source.export_state()),"比較用インスタンスへ有効な進行を複製する")
	var snapshot := source.play_metrics.snapshot()
	for field in snapshot:
		if field == "version":continue
		var value: Variant = snapshot[field]
		result.play_metrics.set(field,value.duplicate(true) if value is Dictionary or value is Array else value)
	return result

func _document(game: GameSession) -> Dictionary:
	var value := game.export_state()
	value["_play_session"] = game.play_metrics.snapshot()
	if not game.playthrough_id().is_empty():value["_trial_id"] = game.playthrough_id()
	value["_saved_value_types"] = SavedValueTypes.describe(value)
	return value

func _roundtrip(source: GameSession, label: String) -> bool:
	variant_counter += 1
	var directory := "user://qa_complete_save_"+run_token+"_"+str(variant_counter)
	# 比較前にrestoreや数値正規化を通さず、実際の保存元を直接採取する。
	var before := _document(source)
	if not _check(Compare.unlisted(before).is_empty(),"保存対象一覧から項目が漏れていない"):return false
	var path := "user://qa_complete_save_"+run_token+".json"
	if not _check(source.save_game(path),"実ファイルへ保存する: "+label):return false
	var loaded := GameSession.new()
	if before.has("_trial_id"):
		# 履歴ファイルは検査用にコピーし、別インスタンスから元の試行へ書き込まない。
		if not _check(DirAccess.make_dir_recursive_absolute(directory) == OK,"履歴の比較用保存先を作る"):return false
		var history: PackedByteArray = FileAccess.get_file_as_bytes(source._archive.directory.path_join(source.playthrough_id()+".json"))
		var history_file := FileAccess.open(directory.path_join(source.playthrough_id()+".json"),FileAccess.WRITE)
		if not _check(history_file != null and not history.is_empty(),"試行参照の比較用履歴を複製する"):return false
		history_file.store_buffer(history)
		history_file.close()
		loaded.enable_recording(directory)
	if not _check(loaded.load_game(path),"別インスタンスへロードする: "+label):return false
	var after := _document(loaded)
	var diffs: Array[String] = Compare.differences(before,after,"$",[])
	if not _check(diffs.is_empty(),label+": "+" / ".join(diffs)):return false
	Compare.paths(before,"$",covered)
	receipts.append({"case":label,"differences":diffs,"trial_id_equal":source.playthrough_id()==loaded.playthrough_id(),"save_sha256":FileAccess.get_sha256(path)})
	return true

func _finish_extra(main: Node) -> bool:
	if not _roundtrip(main.game,"ending"):return false
	for job_id in main.game.jobs:
		if main.game.jobs[job_id]["type"] != "monster":continue
		var game := _fork(main.game)
		if not _check(game.change_job("pc_01",job_id),"変身保存用の職へ変更する"):return false
		var state := game.export_state()
		state["party"][0]["jp"][job_id] = int(game.jobs[job_id]["mastery_cost"])-1
		if not _check(game.import_state(state),"実戦闘でマスターできる直前状態"):return false
		game.rest()
		var battle := game.start_battle(["slime"],73)
		for turn in range(30):
			if battle.phase != BattleState.Phase.INPUT:break
			for actor in battle.pending():battle.queue_action(BattleAction.strike(actor.id,battle.living(Combatant.Team.ENEMY)[0].id))
			battle.resolve_round()
		if not _check(battle.phase == BattleState.Phase.VICTORY and game.finish_battle(),"変身は実戦闘から確定する"):return false
		if not _roundtrip(game,"form_"+job_id):return false
	var fixture := _fork(main.game)
	var supplied := fixture.export_state()
	# 回収の進行は実操作で到達済み。以下は保存項目を満たす有効状態の検査。
	for site in ExplorationSites.data()["sites"]:
		supplied["progress_flags"]["exploration_"+site["id"]] = true
	supplied["party"][0]["unlocked_jobs"] = ["swordsman","sage","hunter","spirit"]
	if not _check(fixture.import_state(supplied),"設備と職解放の保存検査用状態が有効"):return false
	fixture.play_metrics.answers.append({"chapter":"6","active_ms":0,"exploration":3,"reward":4,"difficulty":2,"note":"自動検査用の合成回答。人間の試遊結果ではない。","self_reported":true})
	fixture.play_metrics.source_changed = true
	if not _roundtrip(fixture,"flags_unlocks_synthetic_answer"):return false
	var world_fixture := GameSession.new()
	world_fixture.new_game(main.game.export_state()["party"].size())
	world_fixture.play_metrics.set_source("automated")
	if not _check(world_fixture.open_world_exploration(),"町の新規状態から通常APIで広域を開く"):return false
	if not _roundtrip(world_fixture,"overworld_active"):return false
	if not _check(world_fixture.close_world_exploration(),"出発地点から本編へ戻る"):return false
	if not _roundtrip(world_fixture,"overworld_retained"):return false
	for field in Compare.ROOT_FIELDS:
		if not _check(covered.has("$."+field),"列挙した保存領域が検査されている: "+field):return false
	for field in Compare.ACTOR_FIELDS:
		if not _check(covered.has("$.party[]."+field),"列挙した人物変数が検査されている: "+field):return false
	for required in ["$.return_point.location","$.story_battle.cleared","$.story_task.id","$.gate_team[]","$.expedition.solved[]","$.party[].unlocked_jobs[]","$._play_session.answers[].note","$._trial_id"]:
		if not _check(covered.has(required),"条件付き保存項目の実測がある: "+required):return false
	var count: int = main.game.export_state()["party"].size()
	var report := {"requirement":"AC-03","status":"PASS","party_size":count,"checked_states":receipts.size(),"difference_count":0,"covered_paths":covered,"cases":receipts,"comparison_self_test_mutations":7,"build":BuildIdentity.current(),"runner_sha256":FileAccess.get_sha256("res://tools/check_save_complete.gd"),"comparison_sha256":FileAccess.get_sha256("res://tools/save_state_comparison.gd"),"human_playtest":"NOT_RUN","trial_history_is_separate":true}
	if not _check(PlaySessionMetrics.write_json("res://docs/verification/save-complete-%d.json" % count,report),"保存往復の証拠を記録する"):return false
	print("SAVE_COMPLETE_PASS: party=%d states=%d differences=0" % [count,receipts.size()])
	return true
