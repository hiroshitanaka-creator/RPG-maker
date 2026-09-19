extends SceneTree


var _failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures.append(message)


func _fixture(job_id: String, erosion: int, skill: String = "acid") -> GameSession:
	var game := GameSession.new()
	game.new_game(4)
	game.change_job("pc_01", job_id)
	var state := game.export_state()
	state["party"][0]["erosion"] = erosion
	state["party"][0]["irreversible"] = erosion >= 90
	state["party"][0]["learned_abilities"] = [skill]
	state["party"][0]["equipped_abilities"] = [skill]
	_check(game.import_state(state), "境界値の有効なセーブを読み込む")
	return game


func _round(encounter: BattleState, skill: String = "") -> void:
	for actor in encounter.pending():
		var action := BattleAction.guard(actor.id)
		if actor.id == "pc_01":
			action = BattleAction.strike(actor.id, "enemy_01") if skill.is_empty() else BattleAction.skill(actor.id, "enemy_01", skill)
			if skill == "firm_guard":
				action = BattleAction.skill(actor.id, actor.id, skill)
		_check(encounter.queue_action(action).is_empty(), "検査用の通常コマンドを受理する")
	encounter.resolve_round()


func _win(game: GameSession, skill: String) -> void:
	var encounter := game.start_battle(["slime"], 71)
	_round(encounter, skill)
	for index in range(20):
		if encounter.phase != BattleState.Phase.INPUT:
			break
		_round(encounter)
	_check(encounter.phase == BattleState.Phase.VICTORY, "実際の戦闘で勝利する")
	_check(game.finish_battle(), "勝利結果を反映する")
	var claimed := game.export_state()
	_check(not game.finish_battle(), "結果を二重反映しない")
	_check(game.export_state() == claimed, "二重反映で侵蝕やJPを増やさない")


func _run() -> void:
	var human := _fixture("warrior", 89)
	_win(human, "acid")
	var actor: Dictionary = human.export_state()["party"][0]
	_check(actor["erosion"] == 90, "人間職でも実使用した魔物専用技1回につき侵蝕+1")
	_check(actor["irreversible"], "90到達で不可逆になる")
	_check(actor["job_id"] == "slime", "90到達時に使用技の元の魔物職へ移る")
	_check(actor["monster_form"] == "", "未マスターなら魔物化フラグを勝手に立てない")
	_check(int(actor["jp"].get("warrior",0)) == 5, "戦闘時の人間職へ侵蝕60以上の半分JPを付ける")
	_check(not human.change_job("pc_01", "mage"), "不可逆後は人間職へ戻れない")
	_check(human.save_game("user://erosion_irreversible.json"), "90到達後の状態を保存できる")
	var restored := GameSession.new()
	_check(restored.load_game("user://erosion_irreversible.json"), "90到達後の状態を読める")
	_check(restored.export_state() == human.export_state(), "不可逆・職業・JPが保存往復で一致する")
	var monster := _fixture("slime", 86)
	_win(monster, "acid")
	_check(monster.export_state()["party"][0]["erosion"] == 90, "魔物職の戦闘+3と専用技1回+1を合算する")
	var shared := _fixture("warrior", 59, "firm_guard")
	_win(shared, "firm_guard")
	_check(shared.export_state()["party"][0]["erosion"] == 59, "人間職と共通の技では侵蝕を加算しない")
	_check(int(shared.export_state()["party"][0]["jp"].get("warrior",0)) == 10, "59では人間職のJPを半減しない")
	var crossed := _fixture("warrior", 59)
	_win(crossed, "acid")
	_check(crossed.export_state()["party"][0]["erosion"] == 60, "59から専用技使用で60へ達する")
	_check(int(crossed.export_state()["party"][0]["jp"].get("warrior",0)) == 5, "60へ達した戦闘から人間職JPを半減する")
	var cancelled := _fixture("slime", 20)
	var encounter := cancelled.start_battle(["slime"], 72)
	_check(encounter.queue_action(BattleAction.skill("pc_01", "enemy_01", "acid")).is_empty(), "専用技を予約する")
	encounter.clear_queue()
	for index in range(20):
		if encounter.phase != BattleState.Phase.INPUT:
			break
		_round(encounter)
	cancelled.finish_battle()
	_check(cancelled.export_state()["party"][0]["erosion"] == 23, "予約取消した専用技を実使用に数えない")
	var fizzled := _fixture("slime", 86)
	var fizzle_battle := fizzled.start_battle(["slime"], 73)
	for member in fizzle_battle.pending():
		fizzle_battle.queue_action(BattleAction.skill(member.id,"enemy_01","acid") if member.id == "pc_01" else BattleAction.strike(member.id,"enemy_01"))
	fizzle_battle.resolve_round()
	_check(fizzle_battle.phase == BattleState.Phase.VICTORY, "速い仲間が専用技より先に敵を倒す")
	fizzled.finish_battle()
	_check(fizzled.export_state()["party"][0]["erosion"] == 89, "敵が先に倒れて不発になった技は数えない")
	var capped := _fixture("slime", 99)
	_win(capped, "acid")
	_check(capped.export_state()["party"][0]["erosion"] == 100, "侵蝕を100で止める")
	var defeated := _fixture("warrior", 89)
	var weak_state := defeated.export_state()
	for member in weak_state["party"]:
		member["hp"] = 1 if member["id"] == "pc_01" else 0
	_check(defeated.import_state(weak_state), "全滅経路の有効な状態を用意する")
	var losing := defeated.start_battle(["slime"], 74)
	_round(losing, "acid")
	_check(losing.phase == BattleState.Phase.DEFEAT, "専用技の実行後に全滅する")
	defeated.finish_battle()
	_check(defeated.export_state()["party"][0]["erosion"] == 90, "全滅しても実行済みの専用技を数える")
	_check(defeated.export_state()["party"][0]["hp"] == 0, "不可逆の職業移行で戦闘不能者を復活させない")
	_check(defeated.export_state()["party"][0]["jp"].is_empty(), "全滅ではJPを与えない")
	await _check_ui()
	if not _failures.is_empty():
		for message in _failures:
			printerr("EROSION_FAIL: " + message)
		quit(1)
		return
	print("EROSION_PASS: 専用技実使用・60/90境界・確認取消・不可逆保存を検証")
	quit(0)


func _check_ui() -> void:
	var packed: PackedScene = load(ProjectSettings.get_setting("application/run/main_scene"))
	var main := packed.instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	var fixture := _fixture("slime", 87)
	fixture.set_world("waterway", [7,12], 3)
	_check(main.game.import_state(fixture.export_state()), "UI境界値のセーブを読み込む")
	var before: Dictionary = main.game.export_state()
	main.submit_player_action({"kind":"field_battle"})
	var state: Dictionary = main.automation_snapshot()
	_check(state.get("mode") == "erosion_confirmation", "90を越える魔物職の戦闘開始前に確認する")
	_check(main.game.current_battle() == null, "確認中は戦闘を開始していない")
	_check(main.submit_player_action({"kind":"cancel_erosion"}), "境界を越える戦闘を取り消せる")
	_check(main.game.export_state() == before, "取消では侵蝕・物語進行・所持品を保持する")
	if main.game.current_battle() != null:
		return
	main.submit_player_action({"kind":"field_battle"})
	_check(main.submit_player_action({"kind":"confirm_erosion"}), "同意後に戦闘を開始する")
	_check(main.automation_snapshot().get("mode") == "battle", "同意した戦闘へ入る")
	main.start_new_game(4)
	fixture = _fixture("warrior", 89)
	fixture.set_world("waterway", [7,12], 3)
	main.game.import_state(fixture.export_state())
	main.submit_player_action({"kind":"field_battle"})
	var encounter: BattleState = main.game.current_battle()
	for member in encounter.pending():
		main.submit_player_action({"kind":"ability", "actor":member.id,"target":"enemy_01","ability":"acid"} if member.id == "pc_01" else {"kind":"guard","actor":member.id})
	before = main.game.export_state()
	var battle_before := encounter.snapshot()
	main.submit_player_action({"kind":"resolve_round"})
	_check(main.automation_snapshot().get("mode") == "erosion_confirmation", "予約した技で90へ達するターンを確定前に確認する")
	_check(encounter.snapshot() == battle_before, "確認中はHP・MP・ターンを変えない")
	await _capture(main, "turn_confirmation")
	main.submit_player_action({"kind":"cancel_erosion"})
	_check(main.game.export_state() == before and encounter.snapshot() == battle_before, "ターン確定の取消では全状態を保持する")
	_check(encounter.queued.size() == 4, "取消後も行動予約を保持して選び直せる")
	main.submit_player_action({"kind":"resolve_round"})
	main.submit_player_action({"kind":"confirm_erosion"})
	_check(encounter.actor_by_id("pc_01").mp == int(before["party"][0]["mp"]) - 3, "同意後に技を一度だけ実行する")
	_check(main.game.current_erosion("pc_01") == 90, "戦闘中も専用技実使用後の侵蝕を表示できる")
	await _capture(main, "after_skill")
	for turn in range(20):
		if encounter.phase != BattleState.Phase.INPUT:
			break
		for member in encounter.pending():
			main.submit_player_action({"kind":"attack","actor":member.id,"target":"enemy_01"} if member.id == "pc_01" else {"kind":"guard","actor":member.id})
		main.submit_player_action({"kind":"resolve_round"})
		_check(main.automation_snapshot().get("mode") != "erosion_confirmation", "同意済みの境界を同じ戦闘で繰り返し確認しない")
	_check(main.game.export_state()["party"][0]["job_id"] == "slime", "通常操作でも90到達後の魔物職移行を反映する")
	main.queue_free()
	await process_frame


func _capture(main: Node, name: String) -> void:
	if not "--capture" in OS.get_cmdline_user_args():
		return
	await process_frame
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	_check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/erosion_" + name + ".png") == OK, "実描画を保存する")
