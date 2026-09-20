extends "res://tools/check_story_campaign.gd"

var regions: Dictionary = {}
var points: Array[Dictionary] = []
var inspected_sites: Dictionary = {}
var unreachable_sites: Dictionary = {}
var detour_moves: int = 0
var optional_battles: Dictionary = {}

func _frame_budget() -> int:
	return 90000

func _legacy_probe() -> bool:
	return false

func _optional_views() -> bool:
	return false

func _detour(main: Node, state: Dictionary, _entry: Dictionary) -> bool:
	if main.game.is_returning_to_town():
		return false
	var world: Dictionary = main.game.world_state()
	var key: String = world["location"]+":"+str(world.get("section",""))+":"+str(state["chapter"])
	if not regions.has(key):
		regions[key] = {"location":world["location"],"section":world.get("section","")}
		points.clear()
		# 任意地点は必須目標より先。施錠は迂回せず、到達可能なものだけを巡る。
		for site in main.game.exploration_sites():
			if site["cell"] == state["player_cell"] or not _route(state["player_cell"],site["cell"],state["walkable_cells"]).is_empty():
				points.append({"cell":site["cell"],"site":site["id"]})
			else:
				unreachable_sites[site["id"]] = true
		points.append({"cell":_farthest(state["player_cell"],state["objective_cell"],state["walkable_cells"]),"site":""})
	if points.is_empty():
		if not optional_battles.has(key) and not main.game.field_battle_enemies().is_empty():
			if not _check(main.submit_player_action({"kind":"return_to_town"}) and main.submit_player_action({"kind":"rest"}) and main.submit_player_action({"kind":"resume_exploration"}),"任意戦闘の前にも通常の帰還で準備する"):
				return true
			optional_battles[key] = true
			_check(main.submit_player_action({"kind":"field_battle"}),"各区画で利用可能な任意戦闘を一度先に消化する")
			return true
		return false
	var goal: Array = points[0]["cell"]
	if state["player_cell"] == goal:
		var destination: Dictionary = points.pop_front()
		if not destination["site"].is_empty():
			inspected_sites[destination["site"]] = true
			main.submit_player_action({"kind":"interact"})
		return true
	var route := _route(state["player_cell"],goal,state["walkable_cells"])
	if not _check(not route.is_empty(),"回り道が通常の通行セルでつながる"):
		return true
	if main.submit_player_action({"kind":"move","dx":route[0][0]-state["player_cell"][0],"dy":route[0][1]-state["player_cell"][1]}):
		detour_moves += 1
	return true

func _extra_mode(main: Node, state: Dictionary) -> bool:
	if state["mode"] != "exploration":
		return false
	for option in main.game.exploration_options():
		if option["allowed"]:
			main.submit_player_action({"kind":"use_site","actor":option["actor"],"ability":option["ability"]})
			break
	main.submit_player_action({"kind":"back"})
	return true

func _farthest(start: Array, objective: Array, cells: Array) -> Array:
	var allowed: Dictionary = {}
	for cell in cells:
		allowed[Vector2i(cell[0],cell[1])] = true
	var queue: Array[Vector2i] = [Vector2i(start[0],start[1])]
	var distance: Dictionary = {queue[0]:0}
	var selected := queue[0]
	var at := 0
	while at < queue.size():
		var here := queue[at]
		at += 1
		if distance[here] > distance[selected] and here != Vector2i(objective[0],objective[1]):
			selected = here
		for delta in [Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT,Vector2i.UP]:
			var next: Vector2i = here+delta
			if allowed.has(next) and not distance.has(next):
				distance[next] = distance[here]+1
				queue.append(next)
	return [selected.x,selected.y]

func _finish_extra(main: Node) -> bool:
	var locations: Dictionary = {}
	var sections: Dictionary = {}
	for region in regions.values():
		locations[region["location"]] = true
		if not region["section"].is_empty():
			sections[region["section"]] = true
	if not _check(locations.size() == 8 and sections.size() == 25,"3町・5ダンジョン・25点検区画で回り道を行う"):
		return false
	if not _check(inspected_sites.size() == 10,"任意の設備・補給箱10地点へ先に訪問する"):
		return false
	if not _check(optional_battles.size() >= 25,"25点検区画の任意戦闘を含む"):
		return false
	for actor in main.game.export_state()["party"]:
		if not _check(main.game.jobs[actor["job_id"]]["type"] == "human" and actor["monster_form"].is_empty(),"魔物化なしで結末へ到達する"):
			return false
	var record := {"regions":regions,"inspected_sites":inspected_sites.keys(),"unreachable_while_locked":unreachable_sites.keys(),"detour_moves":detour_moves,"optional_battles":optional_battles.size(),"all_clues_resolved":main.game.story_complete(),"optional_journal_opened_before_ending":false,"source":"automated"}
	if not _check(PlaySessionMetrics.write_json("res://docs/verification/worst-case-current.json",record),"最悪ケースの実行記録を保存する"):
		return false
	print("WORST_CASE_PASS: regions=%d sections=%d sites=%d detour_moves=%d" % [regions.size(),sections.size(),inspected_sites.size(),detour_moves])
	return true
