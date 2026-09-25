extends SceneTree

func _initialize() -> void:
	var game:=GameSession.new()
	game.new_game(3)
	var input: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/mastery-charger-replay-input.json"))
	var fixture:=game.export_state()
	fixture["party"]=input["party"].duplicate(true)
	fixture["progress_flags"]["midgame_slots"]=true
	if not game.import_state(fixture):printerr("MASTERY_ROLE_FAIL: 入力");quit(1);return
	var driver=preload("res://tools/long_play_driver.gd").new()
	driver.prepare(game,false)
	var actor: Dictionary=game.export_state()["party"][1]
	var passed: bool=driver.errors.is_empty() and actor["job_id"]=="martial_artist" and actor["equipped_abilities"]==["four_strike","firm_guard"]
	PlaySessionMetrics.write_json("res://docs/verification/mastery-role-transition.json",{"status":"PASS" if passed else "FAIL","job":actor["job_id"],"equipped":actor["equipped_abilities"],"errors":driver.errors,"scope":"自動操作方針が転職後の職を参照して装着する。制御された習得済み入力。"})
	if not passed:printerr("MASTERY_ROLE_FAIL: 転職前の職を使って装着を選んでいる")
	quit(0 if passed else 1)
