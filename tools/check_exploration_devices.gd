extends "res://tools/smoke_chapter1.gd"
## 旧保存形式1の互換検査。数値の期待値は維持し、形式2は別の統合機構検査で検証。
var _failures: Array[String] = []


func _check(condition: bool, message: String) -> void:
	if not condition and not message in _failures:
		_failures.append(message)


func _run() -> void:
	var game: Variant = GameSession.new()
	preload("res://tools/legacy_save_fixture.gd").begin(game,4)
	if not game.has_method("exploration_sites") or not game.has_method("use_exploration_site"):
		_check(false,"既存ダンジョンの仕掛け・補給箱・開通保存が未接続です。")
		_finish()
		return
	await _check_normal_route()
	_check_all_locations()
	_check_boundaries()
	_finish()


func _check_normal_route() -> void:
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	preload("res://tools/legacy_save_fixture.gd").as_legacy(main.game)
	# 最初の2戦を通常操作で終えて強打を習得する。進行フラグの注入はしない。
	for frame in range(MAX_STEPS):
		await process_frame
		var state: Dictionary = main.automation_snapshot()
		if state.get("quest_step",0) == 5 and state.get("mode") == "field":
			break
		match state.get("mode",""):
			"field":
				if state["player_cell"] == state["objective_cell"]:
					main.submit_player_action({"kind":"interact"})
				else:
					_move_toward(main,state,state["objective_cell"])
			"dialogue": main.submit_player_action({"kind":"confirm"})
			"battle":
				var input: Dictionary = state["battle_input"]
				if input["ready"]:
					main.submit_player_action({"kind":"resolve_round"})
				else:
					main.submit_player_action({"kind":"attack","actor":input["actor"],"target":input["enemy"]})
			_:
				_check(false,"通常の探索・戦闘で水路を進める: "+JSON.stringify(state))
				main.queue_free()
				return
	_check(main.game.world_state()["quest_step"] == 5,"仕掛けへ寄り道する前に2戦を終える")
	_check(main.game.equip_ability("pc_01","power_strike"),"習得した強打を実際に装着する")
	await _walk_to(main,[10,8])
	var before: Dictionary = main.game.export_state()
	_check(not main.game.use_exploration_site("pc_02","power_strike"),"未装着の仲間による操作を拒否する")
	_check(main.game.export_state() == before,"失敗した操作でMPやフラグを変更しない")
	_check(main.submit_player_action({"kind":"interact"}),"通常の調べる操作で仕掛けを開く")
	_check(main.automation_snapshot()["mode"] == "exploration","操作する仲間と技を選ぶ画面を表示する")
	_check(main.game.export_state() == before,"選択画面を開いただけでは消費しない")
	_check(main.submit_player_action({"kind":"back"}) and main.game.export_state() == before,"操作前の取消で状態を変えない")
	main.submit_player_action({"kind":"interact"})
	await _capture_device(main,"options")
	_check(main.submit_player_action({"kind":"use_site","actor":"pc_01","ability":"power_strike"}),"画面から仲間の装着技で水路を開く")
	var after: Dictionary = main.game.export_state()
	_check(after["party"][0]["mp"] == before["party"][0]["mp"]-3,"担当者だけが3MPを消費する")
	_check(after["party"][1] == before["party"][1],"他の仲間の能力やMPを変えない")
	_check(after["world"] == before["world"],"寄り道で物語の進行を飛ばさない")
	_check(not main.game.use_exploration_site("pc_01","power_strike") and main.game.export_state() == after,"再調査で重複消費しない")
	main.submit_player_action({"kind":"back"})
	await _walk_to(main,[12,8])
	_check(main.game.return_to_town(),"開通した通路の中から帰還する")
	_check(main.game.save_game("user://exploration_shortcut.json"),"通路内の帰還位置を保存する")
	var loaded := GameSession.new()
	_check(loaded.load_game("user://exploration_shortcut.json") and loaded.export_state() == main.game.export_state(),"開通と帰還位置の保存往復が一致する")
	_check(loaded.resume_exploration() and loaded.world_state()["player_cell"] == [12,8],"ロード後に開通した通路の中へ戻れる")
	main.game.import_state(loaded.export_state())
	main._resume_current()
	await _walk_to(main,[15,8])
	var items: int = main.game.export_state()["inventory"]["potion"]
	main.submit_player_action({"kind":"interact"})
	_check(main.submit_player_action({"kind":"use_site"}),"解錠した補給箱を受け取る")
	_check(main.game.export_state()["inventory"]["potion"] == items+2,"補給箱の回復薬2個を所持品へ加える")
	_check(not main.submit_player_action({"kind":"use_site"}) and main.game.export_state()["inventory"]["potion"] == items+2,"同じ箱から繰り返し受け取れない")
	_check(main.game.save_game("user://exploration_loot.json"),"補給受取後の状態を保存する")
	var loot_loaded := GameSession.new()
	_check(loot_loaded.load_game("user://exploration_loot.json"),"受取済みの補給箱を読み込む")
	var received := loot_loaded.export_state()
	_check(not loot_loaded.use_exploration_site() and loot_loaded.export_state() == received,"ロード後も同じ補給を重複取得できない")
	await _capture_device(main,"collected")
	main.submit_player_action({"kind":"back"})
	await _capture_device(main,"shortcut")
	main.queue_free()
	await process_frame


func _move_toward(main: Node, state: Dictionary, goal: Array) -> bool:
	var here: Array = state["player_cell"]
	var route := _route(here,goal,state["walkable_cells"])
	if route.is_empty():
		_check(false,"通行可能な経路がある: "+str(goal))
		return false
	main.submit_player_action({"kind":"move","dx":route[0][0]-here[0],"dy":route[0][1]-here[1]})
	return true


func _walk_to(main: Node, goal: Array) -> void:
	for frame in range(3000):
		await process_frame
		var state: Dictionary = main.automation_snapshot()
		if state.get("mode") != "field":
			_check(false,"寄り道中も探索画面へ戻る")
			return
		if state["player_cell"] == goal:
			return
		if not _move_toward(main,state,goal):
			return
	_check(false,"規定操作数で寄り道地点へ到達する")


func _check_all_locations() -> void:
	# 各地点の状態境界は有効な保存状態を用意して検査する。
	var starts := {"waterway":2,"cave":6,"school":23,"records":28,"gate":12}
	var devices := 0
	var caches := 0
	for location in starts:
		var game: Variant = GameSession.new()
		preload("res://tools/legacy_save_fixture.gd").begin(game,3)
		var world_step: int = starts[location]
		var step := StoryCampaign.step(world_step)
		game.set_world(location,step["cell"],world_step)
		for site in game.exploration_sites():
			game.set_world(location,site["cell"],world_step)
			if site["kind"] == "cache":
				caches += 1
				var unopened: Dictionary = game.export_state()
				_check(not game.use_exploration_site() and game.export_state() == unopened,"未開通の設備に対応する補給箱は受け取れない")
				continue
			devices += 1
			var initial: Dictionary = game.export_state()
			var prepared := initial.duplicate(true)
			var skill: String = site["abilities"][0]
			prepared["party"][0]["learned_abilities"] = [skill]
			prepared["party"][0]["equipped_abilities"] = [skill]
			_check(game.import_state(prepared),"装着済みの有効状態を読み込む")
			for alternate in site["abilities"]:
				var choice := initial.duplicate(true)
				choice["party"][0]["learned_abilities"] = [alternate]
				choice["party"][0]["equipped_abilities"] = [alternate]
				game.import_state(choice)
				_check(game.use_exploration_site("pc_01",alternate),"各設備の両方の技で開通できる")
				_check(game.export_state()["party"][0]["mp"] == choice["party"][0]["mp"]-int(game.abilities[alternate]["cost"]),"技ごとの実際のMP消費を反映する")
			game.import_state(prepared)
			var options: Array = game.exploration_options()
			_check(not options.is_empty() and game.export_state() == prepared,"利用条件の参照は状態を変えない")
			game.unequip_ability("pc_01",skill)
			var removed: Dictionary = game.export_state()
			_check(not game.use_exploration_site("pc_01",skill) and game.export_state() == removed,"直前に技を外した場合も操作を拒否する")
			var empty := prepared.duplicate(true)
			empty["party"][0]["mp"] = 0
			game.import_state(empty)
			_check(not game.use_exploration_site("pc_01",skill) and game.export_state() == empty,"MP不足なら操作前の状態を保持する")
			var fallen := prepared.duplicate(true)
			fallen["party"][0]["hp"] = 0
			game.import_state(fallen)
			_check(not game.use_exploration_site("pc_01",skill),"戦闘不能の担当者は操作できない")
			game.import_state(prepared)
			var opening: Array = site["opens"][0]
			var last_opening: Array = site["opens"][-1]
			var exit_cell := [last_opening[0]+opening[0]-site["cell"][0],last_opening[1]+opening[1]-site["cell"][1]]
			var old_route := _route(site["cell"],exit_cell,game.world_walkable_cells())
			_check(game.use_exploration_site("pc_01",skill),"3人編成でも各設備を開通できる")
			var short_route := _route(site["cell"],exit_cell,game.world_walkable_cells())
			_check(not old_route.is_empty() and not short_route.is_empty() and short_route.size() < old_route.size(),"開通後は迂回せず短い経路で通れる")
			var opened: Dictionary = game.export_state()
			for cell in site["opens"]:
				_check(game.set_world(location,cell,world_step),"開通後の通路へ実際に移動できる")
				var broken: Dictionary = game.export_state()
				broken["progress_flags"].erase("exploration_"+site["id"])
				var witness := GameSession.new()
				_check(not witness.import_state(broken),"開通フラグなしに通路内へロードできない")
			game.import_state(initial)
			for cell in site["opens"]:
				_check(not game.set_world(location,cell,world_step),"開通前の通路は通れない")
			_check(not opened.is_empty(),"開通状態を保持する")
	_check(devices == 5 and caches == 5,"既存5ダンジョンに各1設備・1補給箱を配置する")


func _check_boundaries() -> void:
	var game: Variant = GameSession.new()
	preload("res://tools/legacy_save_fixture.gd").begin(game,4)
	var unchanged: Dictionary = game.export_state()
	_check(not game.use_exploration_site("pc_01","power_strike") and game.export_state() == unchanged,"離れた町から設備を操作できない")
	for key in ["exploration_unknown","exploration_waterway_cache"]:
		var broken := unchanged.duplicate(true)
		broken["progress_flags"][key] = true
		_check(not game.import_state(broken) and game.export_state() == unchanged,"未知の設備と解錠前の受取済み保存を拒否する")
	game.set_world("waterway",[10,8],2)
	var prepared: Dictionary = game.export_state()
	prepared["party"][0]["learned_abilities"] = ["power_strike"]
	prepared["party"][0]["equipped_abilities"] = ["power_strike"]
	game.import_state(prepared)
	game.start_battle(["slime"],9)
	_check(not game.use_exploration_site("pc_01","power_strike") and game.export_state() == prepared,"戦闘中は設備を操作しない")
	var monster := GameSession.new()
	monster.import_state(prepared)
	monster.change_job("pc_01","slime")
	var erosion: int = monster.export_state()["party"][0]["erosion"]
	_check(monster.use_exploration_site("pc_01","power_strike"),"魔物職でも持ち越して装着した共通技を使える")
	_check(monster.export_state()["party"][0]["erosion"] == erosion,"人間職でも習得できる共通技には魔物専用技の侵蝕を加算しない")


func _capture_device(main: Node, name: String) -> void:
	if not "--capture" in OS.get_cmdline_user_args():
		return
	await process_frame
	await process_frame
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	_check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/exploration_"+name+".png") == OK,"実画面を保存する")


func _finish() -> void:
	for message in _failures:
		printerr("EXPLORATION_FAIL: "+message)
	if _failures.is_empty():
		print("EXPLORATION_PASS: 5設備・5補給箱・装着/MP判定・通常移動・近道保存・重複防止を検証")
	quit(0 if _failures.is_empty() else 1)
