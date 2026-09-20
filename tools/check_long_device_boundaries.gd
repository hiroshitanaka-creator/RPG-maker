extends "res://tools/check_long_ui.gd"
func _run() -> void:
	var driver = preload("res://tools/long_play_driver.gd").new()
	var count := 0
	for mission in LongCampaign.data()["missions"]:
		var game := GameSession.new()
		game.new_game(3)
		var activity: Dictionary = mission["activities"][0]
		var task: Dictionary = mission["steps"][activity["unlock_stage"]]
		var fixture := _journal_fixture(game.export_state(),{"mission":mission["id"],"step":task["id"]},false)
		fixture["party"][0]["learned_abilities"] = ["firm_guard"]
		check(game.import_state(fixture),"境界検査用の有効な途中状態")
		var original := game.export_state()
		var broken := original.duplicate(true)
		broken["progress_flags"][LongCampaign.activity_flag(activity["id"],"done")] = true
		check(not game.import_state(broken) and game.export_state()==original,"未観察の完了旗を拒否")
		broken = original.duplicate(true)
		broken["progress_flags"][activity["support_flag"]] = true
		check(not game.import_state(broken) and game.export_state()==original,"未完了の支援旗を拒否")
		for observation in activity["observations"]:
			check(driver.walk(game,observation["cell"]),"二つの観察へ通行できる")
			check(game.read_long_observation()==[observation["text"]],"現地で観察する")
		check(driver.walk(game,activity["cell"]),"装置へ通行できる")
		original = game.export_state()
		check(not game.complete_long_activity(activity["answer"],"pc_01") and game.export_state()==original,"習得だけで未装着の技は支援に使えない")
		check(not game.complete_long_activity(activity["answer"],"pc_02") and game.export_state()==original,"未習得の技は支援に使えない")
		check(game.equip_ability("pc_01","firm_guard"),"習得済みの技を装着")
		var exhausted := game.export_state()
		exhausted["party"][0]["mp"] = 0
		check(game.import_state(exhausted),"MP切れの有効な状態")
		check(not game.complete_long_activity(activity["answer"],"pc_01") and game.export_state()==exhausted,"MP不足を拒否し状態を守る")
		var dead := game.export_state()
		dead["party"][0]["hp"] = 0
		dead["party"][0]["mp"] = dead["party"][0]["max_mp"]
		check(game.import_state(dead),"担当者が戦闘不能の有効な状態")
		check(not game.complete_long_activity(activity["answer"],"pc_01") and game.export_state()==dead,"戦闘不能者は支援できない")
		check(game.complete_long_activity(activity["answer"]),"MPと支援なしでも手順で進行できる")
		var after := game.export_state()
		check(not game.complete_long_activity(activity["answer"]) and game.export_state()==after,"完了を重ねても状態を変えない")
		check(game.return_to_town() and game.rest() and game.resume_exploration(),"装置後に帰還再開できる")
		check(game.export_state()["progress_flags"]==after["progress_flags"],"帰還で観察と完了を保持する")
		count += 1
	failures.append_array(driver.errors)
	failures.append_array(diagnostics.messages())
	OS.remove_logger(diagnostics)
	PlaySessionMetrics.write_json("res://docs/verification/long-device-boundaries.json",{"status":"PASS" if failures.is_empty() else "FAIL","activities":count,"failures":failures,"build":BuildIdentity.current(),"scope":"各話の途中状態による境界検査。完走検査はlong-fullを参照。"})
	for failure in failures:printerr("LONG_DEVICE_BOUNDARY_FAIL: "+failure)
	if failures.is_empty():print("LONG_DEVICE_BOUNDARY_PASS: activities=%d" % count)
	quit(0 if failures.is_empty() else 1)
