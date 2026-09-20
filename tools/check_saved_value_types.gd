extends SceneTree

const Compare = preload("res://tools/save_state_comparison.gd")
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	if not value:failures.append(message)

func _initialize() -> void:
	var game := GameSession.new()
	game.new_game(4)
	game.play_metrics.set_source("automated")
	for attempt in range(8):
		game.rest()
		var battle := game.start_battle(["slime"],19+attempt)
		for turn in range(20):
			if battle.phase != BattleState.Phase.INPUT:break
			for actor in battle.pending():battle.queue_action(BattleAction.strike(actor.id,battle.living(Combatant.Team.ENEMY)[0].id))
			battle.resolve_round()
		check(battle.phase == BattleState.Phase.VICTORY and game.finish_battle(),"実戦闘の履歴と装着配列を作る")
		if "power_strike" in game.available_abilities("pc_01"):break
	check(game.equip_ability("pc_01","power_strike"),"実戦闘で習得した技を装着して保存する")
	var float_values: Array[float] = [1.0,1.5,1.0/3.0,0.0000000123456789012345]
	game.play_metrics.record_event("typed_save_fixture",{"integer":1,"float":1.0,"values":float_values})
	var before := {"state":game.export_state(),"metrics":game.play_metrics.snapshot()}
	var path := "user://qa_saved_value_types.json"
	check(game.save_game(path),"型情報付き保存")
	var loaded := GameSession.new()
	check(loaded.load_game(path),"型情報付き読込")
	var diffs := Compare.differences(before,{"state":loaded.export_state(),"metrics":loaded.play_metrics.snapshot()},"$",[])
	check(diffs.is_empty(),"直接採取した保存元との一致: "+" / ".join(diffs))
	var saved: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	var legacy := saved.duplicate(true)
	legacy.erase("_saved_value_types")
	check(PlaySessionMetrics.write_json("user://qa_saved_value_legacy.json",legacy),"従来形式を準備")
	check(GameSession.new().load_game("user://qa_saved_value_legacy.json"),"補助情報がない従来の保存も読める")
	for mutation in ["path","builtin","shape","metric_type"]:
		var broken := saved.duplicate(true)
		if mutation == "path":broken["_saved_value_types"]["arrays"][0]["path"] = ["__missing__"]
		elif mutation == "builtin":broken["_saved_value_types"]["arrays"][0]["builtin"] = TYPE_OBJECT
		elif mutation == "shape":broken["_saved_value_types"] = []
		else:broken["_saved_value_types"]["floats"].append(["_play_session","elapsed_ms"])
		var original := loaded.export_state()
		check(PlaySessionMetrics.write_json("user://qa_saved_value_broken.json",broken),"不正な補助情報を準備")
		check(not loaded.load_game("user://qa_saved_value_broken.json") and loaded.export_state() == original,"不正な補助情報で現在状態を壊さない: "+mutation)
	for message in failures:printerr("SAVED_VALUE_TYPES_FAIL: "+message)
	if failures.is_empty():print("SAVED_VALUE_TYPES_PASS: 型付き配列・整数と小数・従来保存・破損時不変")
	quit(0 if failures.is_empty() else 1)
