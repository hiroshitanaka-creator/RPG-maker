extends SceneTree
var failures: Array[String] = []
var visits := 0
var fights := 0
var saves := 0
var moved_cells := 0

func _initialize() -> void:
	call_deferred("_run")

func check(value: bool, message: String) -> bool:
	if not value:
		failures.append(message)
	return value

func walk_path(game: GameSession, path: Array[Vector2i]) -> bool:
	if not check(not path.is_empty(),"移動経路が存在する"):
		return false
	for i in range(1,path.size()):
		if not check(game.move_overworld(path[i]),"隣接セルへの通常移動"):
			return false
		moved_cells += 1
	return true

func interior_path(state: Dictionary, destination: Vector2i) -> Array[Vector2i]:
	var start := WorldExpedition.point(state["cell"])
	var queue: Array[Vector2i] = [start]
	var parents := {start:Vector2i(-1,-1)}
	var at := 0
	while at < queue.size() and not parents.has(destination):
		var cell := queue[at]
		at += 1
		for direction in [Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP,Vector2i.DOWN]:
			var next: Vector2i = cell+direction
			if not parents.has(next) and WorldExpedition.walkable(state,next):
				parents[next] = cell
				queue.append(next)
	var result: Array[Vector2i] = []
	if not parents.has(destination):
		return result
	var current := destination
	while current != Vector2i(-1,-1):
		result.push_front(current)
		current = parents[current]
	return result

func travel(game: GameSession, id: String) -> bool:
	var state := game.overworld_state()
	var target := WorldTerrain.cell_of(id)
	var current := WorldExpedition.point(state["cell"])
	if not check(WorldExpedition.unlocked(id,state["flags"]),"行き先の解放済み条件"):
		return false
	if "flight" in WorldExpedition.available_transports(state["flags"]):
		if not check(game.change_world_transport("flight"),"入口で飛行へ切替"):
			return false
		return walk_path(game,WorldTerrain.path(current,target,"flight"))
	var walking := WorldTerrain.path(current,target,"walk")
	if not walking.is_empty():
		if not check(game.change_world_transport("walk"),"入口で徒歩へ切替"):
			return false
		return walk_path(game,walking)
	var best: Array = []
	var best_cost := 999999
	for departure in WorldTerrain.data()["nodes"]:
		if not departure["dock"] or not WorldExpedition.unlocked(departure["id"],state["flags"]):
			continue
		var dock := WorldTerrain.cell_of(departure["id"])
		var to_dock := WorldTerrain.path(current,dock,"walk")
		if to_dock.is_empty():
			continue
		for arrival in WorldTerrain.data()["nodes"]:
			if not arrival["dock"] or not WorldExpedition.unlocked(arrival["id"],state["flags"]):
				continue
			var berth := WorldTerrain.cell_of(arrival["id"])
			var from_dock := WorldTerrain.path(berth,target,"walk")
			if from_dock.is_empty():
				continue
			var sea := WorldTerrain.path(dock,berth,"ship")
			var cost := to_dock.size()+sea.size()+from_dock.size()
			if not sea.is_empty() and cost < best_cost:
				best = [to_dock,sea,from_dock]
				best_cost = cost
	if not check(best.size() == 3,"徒歩・船・徒歩で到達する航路"):
		return false
	if not check(game.change_world_transport("walk"),"船着場へ向かう"):
		return false
	if not walk_path(game,best[0]) or not check(game.change_world_transport("ship"),"船着場で乗船"):
		return false
	if not walk_path(game,best[1]) or not check(game.change_world_transport("walk"),"船着場で下船"):
		return false
	return walk_path(game,best[2])

func equip(game: GameSession) -> void:
	var desired := {"warrior":["power_strike","firm_guard","cover"],"martial_artist":["four_strike","double_strike","breath"],"priest":["heal","revive","restore_mp"],"mage":["fire","conduct","ice"]}
	for actor in game.export_state()["party"]:
		for id in actor["equipped_abilities"]:game.unequip_ability(actor["id"],id)
		for id in desired.get(actor["job_id"],[]):
			if id in game.available_abilities(actor["id"]):
				game.equip_ability(actor["id"],id)

func fight(game: GameSession) -> bool:
	equip(game)
	var before := game.export_state()
	check(game.save_game("user://qa_world_battle_before.json"),"広域戦闘前を保存")
	var battle := game.start_world_battle()
	if not check(battle != null,"現地のイベントから通常戦闘を開始"):
		return false
	check(game.is_world_battle(),"広域戦闘の識別")
	check(not game.move_overworld(Vector2i(1,1)),"戦闘中は移動拒否")
	check(not game.save_game("user://qa_world_during_battle.json"),"戦闘中の保存を拒否")
	for turn in range(60):
		if battle.phase != BattleState.Phase.INPUT:
			break
		for actor in battle.pending():
			var action: BattleAction = preload("res://tools/integrated_play_policy.gd").action(battle,actor)
			check(battle.queue_action(action).is_empty(),"画面で選べる行動を予約")
		for action in preload("res://tools/integrated_play_policy.gd").adjustments(battle):
			check(battle.queue_action(action).is_empty(),"予告に応じて行動を組み直す")
		battle.resolve_round()
	if not check(battle.phase == BattleState.Phase.VICTORY,"初期パーティと獲得した技・薬で勝利: "+game.overworld_state()["node"]):
		printerr("WORLD_BATTLE_DIAGNOSTIC: "+JSON.stringify({"party":before["party"],"snapshot":battle.snapshot()}))
		return false
	check(game.finish_battle(),"実際の勝利からJPと進行を反映")
	check(game.overworld_state()["cleared"].size() == before["overworld"]["cleared"].size()+1,"戦闘の突破は一度だけ増える")
	check(not game.finish_battle(),"報酬二重受取を拒否")
	fights += 1
	return true

func roundtrip(game: GameSession) -> bool:
	var before := game.export_state()
	if not check(game.save_game("user://qa_world_roundtrip.json"),"現在地・交通・内部進行を保存"):
		return false
	var restored := GameSession.new()
	if not check(restored.load_game("user://qa_world_roundtrip.json") and restored.export_state() == before,"別インスタンスへの保存往復で全状態一致"):
		return false
	saves += 1
	return true

func visit(game: GameSession, id: String) -> bool:
	if not travel(game,id):
		return false
	if not check(game.interact_overworld().get("kind") == "moved","拠点へ入る: "+id):
		return false
	var site := WorldExpedition.site(id)
	for index in range(site["rooms"].size()):
		var state := game.overworld_state()
		var definition := WorldExpedition.current_room(state)
		check(state["room"] == index,"区画を順に進める")
		for event in definition["events"]:
			if not walk_path(game,interior_path(game.overworld_state(),WorldExpedition.point(event["cell"]))):
				return false
			var original_text: Array = event.get("text",[]).duplicate(true)
			var result := game.interact_overworld()
			match event["kind"]:
				"observe", "rest":
					check(result.get("kind") == "dialogue","現地の観察または休息")
					game.interact_overworld()
					check(event.get("text",[]) == original_text,"繰り返し調べても元の台詞データが増殖しない")
				"battle":
					if not check(result.get("kind") == "battle","戦闘地点の条件を満たす") or not fight(game):
						return false
				"choice":
					check(result.get("kind") == "choice","記録・戦闘を終えて選択へ進む")
					var before: int = game.export_state()["inventory"]["potion"]
					var chosen := game.choose_world_option(int(WorldExpedition.node(id)["progression_index"])%2)
					if not check(not chosen.is_empty(),"依頼の選択が成立する"):
						return false
					check(game.export_state()["inventory"]["potion"] == before+chosen["potions"],"選択した報酬が反映される")
					check(game.choose_world_option(0).is_empty(),"依頼報酬の二重受取を拒否")
		if not roundtrip(game):
			return false
		if not definition["next"].is_empty():
			if not walk_path(game,interior_path(game.overworld_state(),WorldExpedition.point(definition["next"]))):
				return false
			check(game.interact_overworld().get("kind") == "moved","突破後に次の区画へ入る")
	while game.overworld_state()["layer"] == "interior":
		var definition := WorldExpedition.current_room(game.overworld_state())
		if not walk_path(game,interior_path(game.overworld_state(),WorldExpedition.point(definition["exit"]))):
			return false
		check(game.interact_overworld().get("kind") == "moved","入った経路で戻れる")
	visits += 1
	print("WORLD_INTEGRATION_PROGRESS: sites=%d/49 battles=%d" % [visits,fights])
	return true

func _run() -> void:
	var party_size := 3 if "--party=3" in OS.get_cmdline_user_args() else 4
	var game := GameSession.new()
	check(game.new_game(party_size),"初期状態のパーティで開始")
	game.play_metrics.set_source("automated")
	var legacy := game.export_state()
	check(not legacy.has("overworld"),"旧保存形式に広域状態を勝手に追加しない")
	check(game.open_world_exploration(),"通常の町から広域へ出る")
	check(not game.change_world_transport("ship"),"未解放の船を拒否")
	check(not game.change_world_transport("flight"),"未解放の飛行を拒否")
	check(not game.move_overworld(Vector2i(-1,-1)),"境界外と非隣接移動を拒否")
	check(not game.advance_story_step(),"広域探索中は旧本編を背後で進めない")
	for entry in WorldExpedition.data()["nodes"]:
		if not visit(game,entry["id"]):
			break
	check(visits == 49 and fights == 22,"49拠点・新規11ダンジョンの22戦を実操作APIで踏破")
	if failures.is_empty():
		check(travel(game,game.overworld_state()["origin"]),"出発地点へ戻る")
		check(game.close_world_exploration(),"元の本編へ復帰")
		check(game.world_state() == legacy["world"],"旧本編の現在地と章進行を保持")
		check(roundtrip(game),"広域を閉じた状態でも保存往復")
		var corrupted := game.export_state()
		corrupted["overworld"]["cell"] = [-1,0]
		var previous := game.export_state()
		check(not game.import_state(corrupted) and game.export_state() == previous,"不正位置の読込を拒否し現在の冒険を保持")
		corrupted = previous.duplicate(true)
		corrupted["overworld"]["choices"]["missing_node"] = 0
		check(not game.import_state(corrupted),"未定義の拠点進行を拒否")
		check(game.open_world_exploration() and game.overworld_state()["choices"].size() == 49,"再開しても依頼記録を保持")
	var output := FileAccess.open("res://docs/verification/world-integration%s.json" % ("-3" if party_size == 3 else ""),FileAccess.WRITE)
	if output != null:
		output.store_string(JSON.stringify({"status":"PASS" if failures.is_empty() else "FAIL","errors":failures,"sites":visits,"battles":fights,"save_roundtrips":saves,"moved_cells":moved_cells,"party_size":party_size,"party_source":"new_game_no_stat_or_flag_injection","movement_source":"adjacent_cell_api_without_ui_wait","human_play":"NOT_RUN"},"  ",true)+"\n")
		output.close()
	else:
		check(false,"検査結果の保存")
	for message in failures:
		printerr("WORLD_INTEGRATION_FAIL: "+message)
	if failures.is_empty():
		print("WORLD_INTEGRATION_PASS: sites=%d battles=%d saves=%d moved=%d errors=0" % [visits,fights,saves,moved_cells])
	quit(0 if failures.is_empty() else 1)
