extends "res://tools/smoke_chapter1.gd"
## 旧保存形式1の互換検査。数値の期待値は維持し、形式2は別の統合機構検査で検証。

var _failures: Array[String] = []


func _capture(main: Node, name: String) -> void:
	if not "--capture" in OS.get_cmdline_user_args():
		return
	await process_frame
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var path := "res://docs/verification/screens/progression_" + name + ".png"
	_check(main.get_viewport().get_texture().get_image().save_png(path) == OK, "実描画の保存に成功する")


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures.append(message)


func _run() -> void:
	var game := GameSession.new()
	preload("res://tools/legacy_save_fixture.gd").begin(game,4)
	var original := game.export_state()
	for bad_world in [{}, {"location":"missing", "player_cell":[2,4], "quest_step":0}, {"location":"town", "player_cell":[0,0], "quest_step":0}]:
		var broken := original.duplicate(true)
		broken["world"] = bad_world
		_check(not game.import_state(broken), "破損した探索位置を読み込まない")
		_check(game.export_state() == original, "読み込み失敗時は現在の冒険を保持する")
	for job_id in game.jobs:
		preload("res://tools/legacy_save_fixture.gd").begin(game,4)
		var before_preview := game.export_state()
		var preview := game.preview_job("pc_01", job_id)
		_check(game.export_state() == before_preview, "転職比較は状態を変更しない")
		_check(game.change_job("pc_01", job_id), "比較対象の職へ転職できる")
		_check(game.effective_stats("pc_01") == preview["stats"], "転職後の能力値が比較表示と一致する")
	preload("res://tools/legacy_save_fixture.gd").begin(game,4)
	var legacy := game.export_state()
	legacy.erase("return_point")
	legacy.erase("field_battles")
	_check(game.import_state(legacy), "追加項目のない従来のセーブを読み込める")
	_check(game.export_state() == legacy, "従来の保存も読み込みだけでは変更しない")
	var packed: PackedScene = load(ProjectSettings.get_setting("application/run/main_scene"))
	var main := packed.instantiate()
	root.add_child(main)
	await process_frame
	var party_size := 3 if "--three-member-party" in OS.get_cmdline_user_args() else 4
	main.start_new_game(party_size)
	preload("res://tools/legacy_save_fixture.gd").as_legacy(main.game)
	_check(not main.submit_player_action({"kind":"field_battle"}), "町から任意戦闘は開始できない")
	# 進行フラグを直接書かず、最初の水路戦の勝利まで通常の操作で進む。
	for step in range(6000):
		await process_frame
		var state: Dictionary = main.automation_snapshot()
		if state.get("mode") == "field" and main.game.world_state().get("quest_step") == 3:
			break
		_drive(main, state)
	_check(main.game.world_state().get("quest_step") == 3, "最初の水路戦を通過する")
	await _capture(main, "waterway")
	var departure: Dictionary = main.game.export_state()
	_check(main.submit_player_action({"kind":"return_to_town"}), "探索から町へ帰還できる")
	if main.game.world_state().get("location") == "town":
		await _capture(main, "town")
		_check(not main.submit_player_action({"kind":"return_to_town"}), "帰還を重ねて戻り先を失わない")
		_check(main.submit_player_action({"kind":"rest"}), "帰還した町で休息できる")
		_check(main.game.save_game("user://progression_return.json"), "帰還位置を保存できる")
		var restored := GameSession.new()
		_check(restored.load_game("user://progression_return.json"), "帰還中の保存を読み込める")
		_check(restored.export_state() == main.game.export_state(), "帰還中も全状態が往復する")
		_check(restored.resume_exploration(), "ロードした帰還位置へ戻れる")
		_check(restored.world_state() == departure["world"], "ロード後も元の探索位置と進行へ戻る")
		_check(main.submit_player_action({"kind":"resume_exploration"}), "町から探索へ戻れる")
		_check(main.game.world_state() == departure["world"], "帰還前の位置と物語進行へ戻る")
	_check(main.game.change_job("pc_01", "slime"), "魔物職へ転職する")
	for encounter_index in range(4):
		var before: Dictionary = main.game.export_state()
		var accepted: bool = main.submit_player_action({"kind":"field_battle"})
		_check(accepted, "同じ水路で任意戦闘を繰り返せる")
		if not accepted:
			break
		_check(not main.game.save_game("user://progression_in_battle.json"), "戦闘途中には保存しない")
		_check(not main.submit_player_action({"kind":"return_to_town"}), "戦闘途中には帰還しない")
		for step in range(1000):
			await process_frame
			var state: Dictionary = main.automation_snapshot()
			if state.get("mode") == "field":
				break
			_drive(main, state)
		var after: Dictionary = main.game.export_state()
		_check(after["world"] == before["world"], "任意戦闘は位置・物語手順を進めない")
		_check(after["progress_flags"] == before["progress_flags"], "任意戦闘は物語フラグを立てない")
		_check(int(after["party"][0]["jp"].get("slime",0)) > int(before["party"][0]["jp"].get("slime",0)), "勝利からJPを得る")
		main.submit_player_action({"kind":"return_to_town"})
		main.submit_player_action({"kind":"rest"})
		main.submit_player_action({"kind":"resume_exploration"})
	var grown: Dictionary = main.game.export_state()
	_check(grown["party"][0]["monster_form"] == "slime", "通常の任意戦闘から魔物化へ到達する")
	_check(main.game.equip_ability("pc_01", "acid"), "習得した魔物技を装着できる")
	_check(main.submit_player_action({"kind":"field_battle"}), "習得した技を実戦で使う戦闘へ進める")
	_check(main.submit_player_action({"kind":"ability", "actor":"pc_01", "target":"enemy_01", "ability":"acid"}), "通常操作から装着した酸液を選べる")
	for step in range(1000):
		await process_frame
		var state: Dictionary = main.automation_snapshot()
		if state.get("mode") == "field":
			break
		# 他の仲間が先に敵を倒して酸液が不発にならないよう、防御を選ぶ。
		_drive(main, state, true)
	_check(main.game.export_state()["party"][0]["mp"] < grown["party"][0]["mp"], "装着した技を実行してMPを消費する")
	main.submit_player_action({"kind":"return_to_town"})
	main.submit_player_action({"kind":"party"})
	await _capture(main, "build")
	var before_release: Dictionary = main.game.export_state()
	_check(main.submit_player_action({"kind":"request_purify", "actor":"pc_01"}), "魔物化解除の確認を開ける")
	await _capture(main, "purify")
	_check(main.game.export_state() == before_release, "確認を開くだけでは技を消去しない")
	_check(main.submit_player_action({"kind":"cancel_purify"}), "解除を取り消せる")
	_check(main.game.export_state() == before_release, "取消時に全状態を保持する")
	main.submit_player_action({"kind":"request_purify", "actor":"pc_01"})
	_check(main.submit_player_action({"kind":"confirm_purify"}), "確認後に魔物化を解除できる")
	_check(main.game.export_state()["party"][0]["monster_form"] == "", "魔物化解除を反映する")
	_check(not "acid" in main.game.available_abilities("pc_01"), "確認された代償として魔物技を消去する")
	if not _failures.is_empty():
		for message in _failures:
			printerr("PROGRESSION_FAIL: " + message)
		quit(1)
		return
	print("PROGRESSION_PASS: party=%d 通常移動・帰還保存・任意戦闘・魔物化・取消と解除を通過" % party_size)
	quit(0)


func _drive(main: Node, state: Dictionary, guard_others: bool = false) -> void:
	match state.get("mode", ""):
		"dialogue": main.submit_player_action({"kind":"confirm"})
		"battle":
			var input: Dictionary = state.get("battle_input", {})
			if input.get("ready", false):
				main.submit_player_action({"kind":"resolve_round"})
			elif not str(input.get("actor", "")).is_empty() and not str(input.get("enemy", "")).is_empty():
				if guard_others and input["actor"] != "pc_01":
					main.submit_player_action({"kind":"guard", "actor":input["actor"]})
				else:
					main.submit_player_action({"kind":"attack", "actor":input["actor"], "target":input["enemy"]})
		"field":
			var here: Array = state.get("player_cell", [])
			var goal: Array = state.get("objective_cell", [])
			if here == goal:
				main.submit_player_action({"kind":"interact"})
			else:
				var route := _route(here, goal, state.get("walkable_cells", []))
				if not route.is_empty():
					main.submit_player_action({"kind":"move", "dx":route[0][0]-here[0], "dy":route[0][1]-here[1]})
