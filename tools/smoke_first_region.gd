extends "res://tools/smoke_chapter1.gd"
## 実装前の受入仕様。継承元から利用するのは読み取り専用の経路探索 _route だけ。

const REGION_SEED := 20260925
const LIMIT_MS := 180000
const LIMIT_INPUTS := 3000
const LIMIT_MOVES := 600
const LIMIT_TURNS := 300
const DATA_PATH := "res://world/interiors.json"
const DIRECTIONS := [Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP]
const FORBIDDEN_LABELS := ["世界地図へ", "本編へ"]

var _main: Node
var _results: Dictionary = {}
var _definition: Dictionary = {}
var _sites: Array = []
var _forbidden_seen: Array[String] = []
var _input_log: Array[String] = []
var _seen_battles: Dictionary = {}
var _deadline := 0
var _moves := 0
var _turns := 0
var _village_moves := 0
var _village_seen := false
var _village_battle := false
var _left_village := false
var _exit_party: Array = []
var _gate_breach := false
var _gate_probe_active := false
var _observation_fault := false
var _boss_starts := 0
var _boss_won := false
var _started_by_ui := false
var _menu_checked := false
var _route_finished := false
var _input_violation := false
var _finished := false
var _blocker := "経路の前提が未成立"
var _previous_pose: Dictionary = {}


func _initialize() -> void:
	seed(REGION_SEED)
	# 保存先だけを隔離する。位置・所持品・フラグ・乱数内部状態は書き換えない。
	OS.set_environment("RPG_QA_SAVE_PREFIX", "first_region_" + str(OS.get_process_id()))
	_deadline = Time.get_ticks_msec() + LIMIT_MS
	call_deferred("_run")


func _record(id: String, ok: bool, reason: String) -> bool:
	_results[id] = {"ok":ok, "reason":reason.replace("\n", " ")}
	return ok


func _active() -> bool:
	if _finished:return false
	if Time.get_ticks_msec() >= _deadline or _input_log.size() >= LIMIT_INPUTS:
		_blocker = "時間または入力回数の上限に到達"
		return false
	return true


func _session() -> Object:
	if not is_instance_valid(_main):return null
	for property in _main.get_property_list():
		if property["name"] == "game":
			var value: Variant = _main.get("game")
			if value is Object:return value
	return null


func _state() -> Dictionary:
	var session := _session()
	if session == null or not session.has_method("export_state"):return {}
	var value: Variant = session.call("export_state")
	return value if value is Dictionary else {}


func _snapshot() -> Dictionary:
	if not is_instance_valid(_main) or not _main.has_method("automation_snapshot"):return {}
	var value: Variant = _main.call("automation_snapshot")
	return value if value is Dictionary else {}


func _battle() -> Object:
	var session := _session()
	if session == null or not session.has_method("current_battle"):return null
	var value: Variant = session.call("current_battle")
	return value if value is Object else null


func _integer(value: Variant) -> bool:
	return value is int or (value is float and is_finite(value) and value == floor(value))


func _cell(value: Variant) -> bool:
	return value is Array and value.size() == 2 and _integer(value[0]) and _integer(value[1])


func _point(value: Variant) -> bool:
	return value is Dictionary and value.get("layer") in ["world", "interior"] and value.get("node") is String and _integer(value.get("room")) and value["room"] >= 0 and _cell(value.get("cell"))


func _pose() -> Dictionary:
	var value: Variant = _state().get("overworld")
	if not value is Dictionary or value.get("active") != true or not _point(value):return {}
	if not _integer(value.get("facing")) or value["facing"] not in [0,1,2,3]:return {}
	return {"layer":value["layer"],"node":value["node"],"room":value["room"],"cell":value["cell"].duplicate(),"facing":value["facing"]}


func _context(a: Dictionary, b: Dictionary) -> bool:
	return not a.is_empty() and a.get("layer") == b.get("layer") and a.get("node") == b.get("node") and a.get("room") == b.get("room")


func _at(point: Dictionary) -> bool:
	var pose := _pose()
	return _context(pose, point) and pose["cell"] == point["cell"]


func _floor_at(point: Dictionary) -> int:
	if point.get("layer") != "interior":return 0
	for site in _sites:
		if site.get("id") == point.get("node"):
			var index := int(point.get("room", -1))
			var rooms: Array = site["rooms"]
			if index >= 0 and index < rooms.size():
				var value: Variant = rooms[index].get("floor", 0)
				return int(value) if _integer(value) else -1
	return -1


func _has_pass() -> bool:
	var inventory: Variant = _state().get("inventory")
	if not inventory is Dictionary:return false
	var count: Variant = inventory.get("gate_pass", 0)
	return _integer(count) and count > 0


func _party() -> Array:
	var value: Variant = _state().get("party")
	return value.duplicate(true) if value is Array else []


func _watch() -> void:
	if _finished or not is_instance_valid(_main):return
	var pending: Array[Node] = [root]
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		for child in node.get_children(true):pending.append(child)
		var labels: Array[String] = []
		if node is Button and node.is_visible_in_tree():labels.append(node.text)
		if node is PopupMenu and node.visible:
			for index in range(node.item_count):labels.append(node.get_item_text(index))
		for label in labels:
			for forbidden in FORBIDDEN_LABELS:
				if label.contains(forbidden) and forbidden not in _forbidden_seen:_forbidden_seen.append(forbidden)
	var pose := _pose()
	if _started_by_ui and pose.is_empty():_observation_fault = true
	if pose.get("layer") == "interior" and pose.get("node") == "start_village":
		_village_seen = true
		if _battle() != null or _snapshot().get("mode") == "battle":_village_battle = true
	if not _left_village and _previous_pose.get("node") == "start_village" and pose.get("layer") == "world":
		_left_village = true
		_exit_party = _party()
	if not _definition.is_empty() and not pose.is_empty():
		if _gate_probe_active and _at(_definition["gate"]["beyond"]) and not _has_pass():_gate_breach = true
	var battle := _battle()
	if battle != null and not _seen_battles.has(battle.get_instance_id()):
		var input: Variant = _snapshot().get("battle_input", {})
		var identifier: String = str(input.get("encounter_id", "")) if input is Dictionary else ""
		_seen_battles[battle.get_instance_id()] = identifier
		if identifier == "first_boss":_boss_starts += 1
	if not pose.is_empty():_previous_pose = pose


func _frames(count: int = 2) -> void:
	for index in range(count):
		await process_frame
		_watch()


func _key(code: int) -> bool:
	if not _active():return false
	if code not in [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_ENTER]:
		_input_violation = true
		return false
	_input_log.append("key:" + str(code))
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	_main.get_viewport().push_input(event, true)
	event = event.duplicate()
	event.pressed = false
	_main.get_viewport().push_input(event, true)
	await _frames()
	return _active()


func _button(labels: Array) -> bool:
	if not _active():return false
	for label in labels:
		for button in _main.find_children("*", "Button", true, false):
			if button.text != label or not button.is_visible_in_tree() or button.disabled:continue
			var rect: Rect2 = button.get_global_rect()
			if not button.get_viewport_rect().has_point(rect.get_center()) or rect.size.x <= 0 or rect.size.y <= 0:continue
			_input_log.append("button:" + str(label))
			var event := InputEventMouseButton.new()
			event.button_index = MOUSE_BUTTON_LEFT
			event.button_mask = MOUSE_BUTTON_MASK_LEFT
			event.position = rect.get_center()
			event.pressed = true
			_main.get_viewport().push_input(event, true)
			event = event.duplicate()
			event.pressed = false
			event.button_mask = 0
			_main.get_viewport().push_input(event, true)
			await _frames()
			return true
	_blocker = "表示された操作ボタンが見つからない: " + str(labels)
	return false


func _combat_command(action: Dictionary) -> bool:
	if action.get("kind") not in ["attack", "resolve_round"]:
		_input_violation = true
		return false
	if not _main.has_method("submit_player_action"):return false
	_input_log.append("battle:" + str(action["kind"]))
	var accepted: Variant = _main.call("submit_player_action", action)
	await _frames()
	return accepted == true


func _settle() -> bool:
	for iteration in range(LIMIT_INPUTS):
		if not _active():return false
		_watch()
		var snapshot := _snapshot()
		var mode: String = str(snapshot.get("mode", ""))
		if mode in ["field", "world"]:return true
		if mode == "dialogue":
			if not await _key(KEY_ENTER):return false
		elif mode == "battle":
			var battle := _battle()
			var input: Variant = snapshot.get("battle_input")
			if battle == null or not input is Dictionary or not input.has_all(["ready","actor","enemy","encounter_id"]):
				_blocker = "戦闘の通常入力またはencounter_idが未接続"
				return false
			if input["ready"] == true:
				_turns += 1
				if _turns > LIMIT_TURNS:return false
				if not await _combat_command({"kind":"resolve_round"}):return false
				if input["encounter_id"] == "first_boss" and is_instance_valid(battle) and battle.get("phase") == BattleState.Phase.VICTORY:_boss_won = true
			elif input["actor"] is String and input["enemy"] is String and not input["actor"].is_empty() and not input["enemy"].is_empty():
				if not await _combat_command({"kind":"attack","actor":input["actor"],"target":input["enemy"]}):return false
			else:
				_blocker = "通常攻撃の対象が不足"
				return false
			# 既存の決定キーで戦闘表示を送る。戦闘結果や勝敗を書き換えない。
			if not await _key(KEY_ENTER):return false
		else:
			_blocker = "進行できない画面: " + mode
			return false
	return false


func _step_direction(delta: Vector2i) -> bool:
	if delta not in DIRECTIONS or _moves >= LIMIT_MOVES:return false
	_moves += 1
	var before := _pose()
	var keys := [KEY_DOWN,KEY_LEFT,KEY_RIGHT,KEY_UP]
	if not await _key(keys[DIRECTIONS.find(delta)]):return false
	# 実ゲームの150ms制限を待つ。時計起点や移動速度には触れない。
	await create_timer(0.16).timeout
	_watch()
	if before.get("node") == "start_village" and _pose() != before:_village_moves += 1
	return await _settle()


func _walkable() -> Array:
	var cells: Variant = _snapshot().get("walkable_cells")
	if not cells is Array or cells.is_empty() or cells.size() > 65536:return []
	for cell in cells:
		if not _cell(cell):return []
	return cells


func _trigger_points() -> Array:
	var points: Array = [_definition["village_exit"], _definition["cave_exit"], _definition["boss"]["point"], _definition["gate"]["cell"]]
	for key in ["village_entrance", "cave_entrance"]:points.append(_world_point(_definition[key]["cell"]))
	for key in ["stairs_down", "stairs_up"]:points.append(_definition[key]["from"])
	for door in _definition.get("doors", []):points.append(door["from"])
	return points


func _walk_local(goal: Dictionary, landing: Dictionary = {}) -> bool:
	for iteration in range(LIMIT_MOVES):
		if not _active() or not await _settle():return false
		var here := _pose()
		if not _context(here, goal):return false
		if _at(goal):return landing.is_empty()
		var cells := _walkable()
		if cells.is_empty():
			_blocker = "現在地のwalkable_cellsが未接続"
			return false
		for trigger in _trigger_points():
			if _context(here, trigger) and trigger["cell"] != goal["cell"] and trigger["cell"] != here["cell"]:cells.erase(trigger["cell"])
		var route := _route(here["cell"], goal["cell"], cells)
		if route.is_empty():
			_blocker = "通常移動で到達できない観測地点"
			return false
		var next: Array = route[0]
		var delta := Vector2i(int(next[0])-int(here["cell"][0]), int(next[1])-int(here["cell"][1]))
		if not await _step_direction(delta):return false
		if not landing.is_empty() and next == goal["cell"]:return _at(landing)
		if not _context(_pose(), here):return false
	_blocker = "移動回数の上限に到達"
	return false


func _walk(goal: Dictionary, landing: Dictionary = {}) -> bool:
	# 同じ階の室間移動だけは、実データの扉グラフから経路を選ぶ。
	var queue: Array = [{"point":_pose(),"links":[]}]
	var seen: Dictionary = {}
	while not queue.is_empty():
		var entry: Dictionary = queue.pop_front()
		if _context(entry["point"], goal):
			for door in entry["links"]:
				if not await _transition(door):return false
			return await _walk_local(goal, landing)
		var context_id := str([entry["point"].get("layer"),entry["point"].get("node"),entry["point"].get("room")])
		if seen.has(context_id):continue
		seen[context_id] = true
		for door in _definition.get("doors", []):
			if _context(entry["point"], door["from"]) and door["to"]["node"] == goal["node"] and _floor_at(door["from"]) == _floor_at(door["to"]):
				queue.append({"point":door["to"],"links":entry["links"]+[door]})
	_blocker = "部屋間の通常経路が未定義"
	return false


func _transition(link: Dictionary) -> bool:
	if _at(link["from"]):
		var here := _pose()
		var candidates := _walkable()
		for trigger in _trigger_points():
			if _context(here, trigger):candidates.erase(trigger["cell"])
		var moved := false
		for direction in DIRECTIONS:
			var adjacent: Array = [here["cell"][0]+direction.x,here["cell"][1]+direction.y]
			if adjacent in candidates:
				moved = await _step_direction(direction)
				break
		if not moved:return false
	return await _walk(link["from"], link["to"])


func _world_point(cell: Array) -> Dictionary:
	return {"layer":"world","node":"","room":0,"cell":cell.duplicate()}


func _outside(entrance: Dictionary) -> Dictionary:
	return _world_point([entrance["cell"][0]+entrance["outward"][0],entrance["cell"][1]+entrance["outward"][1]])


func _outward(entrance: Dictionary) -> bool:
	return _at(_outside(entrance)) and _pose().get("facing") == DIRECTIONS.find(Vector2i(int(entrance["outward"][0]),int(entrance["outward"][1])))


func _link(value: Variant) -> bool:
	return value is Dictionary and _point(value.get("from")) and _point(value.get("to"))


func _load_definition() -> bool:
	if not FileAccess.file_exists(DATA_PATH):return false
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(DATA_PATH)) != OK or not parser.data is Dictionary:return false
	var data: Dictionary = parser.data
	var region: Variant = data.get("first_region")
	if not region is Dictionary or region.get("version") != 1:
		_blocker = "world/interiors.json のfirst_region定義がない"
		return false
	for key in ["village_exit","cave_exit","cave_spawn","save_probe","boss_revisit"]:
		if not _point(region.get(key)):return false
	for key in ["village_entrance","cave_entrance"]:
		var value: Variant = region.get(key)
		if not value is Dictionary or not _cell(value.get("cell")) or not _cell(value.get("outward")):return false
		if Vector2i(int(value["outward"][0]),int(value["outward"][1])) not in DIRECTIONS:return false
	for key in ["stairs_down","stairs_up"]:
		if not _link(region.get(key)):return false
	var boss: Variant = region.get("boss")
	if not boss is Dictionary or boss.get("encounter_id") != "first_boss" or not _point(boss.get("point")):return false
	var gate: Variant = region.get("gate")
	if not gate is Dictionary:return false
	for key in ["before","cell","beyond"]:
		if not _point(gate.get(key)) or gate[key]["layer"] != "world":return false
	var delta := Vector2i(int(gate["cell"]["cell"][0]-gate["before"]["cell"][0]),int(gate["cell"]["cell"][1]-gate["before"]["cell"][1]))
	if delta not in DIRECTIONS or gate["beyond"]["cell"] != [gate["cell"]["cell"][0]+delta.x,gate["cell"]["cell"][1]+delta.y]:return false
	var recruits: Variant = region.get("recruits")
	if not recruits is Array or recruits.size() != 2:return false
	for recruit in recruits:
		if not recruit is Dictionary or not _point(recruit.get("stand")) or not _cell(recruit.get("facing")):return false
		if recruit["stand"]["node"] != "start_village" or Vector2i(int(recruit["facing"][0]),int(recruit["facing"][1])) not in DIRECTIONS:return false
	if not region.get("doors", []) is Array:return false
	for door in region.get("doors", []):
		if not _link(door):return false
	if not data.get("sites") is Array:return false
	for site in data["sites"]:
		if not site is Dictionary or not site.get("rooms") is Array:return false
		for room in site["rooms"]:
			if not room is Dictionary:return false
	_definition = region
	_sites = data["sites"]
	if region["village_exit"]["layer"] != "interior" or region["village_exit"]["node"] != "start_village":return false
	for key in ["cave_exit","cave_spawn","save_probe"]:
		if region[key]["node"] != "first_cave" or _floor_at(region[key]) != 1:return false
	for point in [region["boss"]["point"],region["boss_revisit"]]:
		if point["node"] != "first_cave" or _floor_at(point) != 2:return false
	if _context(region["boss"]["point"],region["boss_revisit"]) and region["boss"]["point"]["cell"] == region["boss_revisit"]["cell"]:return false
	if _floor_at(region["stairs_down"]["from"]) != 1 or _floor_at(region["stairs_down"]["to"]) != 2:return false
	if _floor_at(region["stairs_up"]["from"]) != 2 or _floor_at(region["stairs_up"]["to"]) != 1:return false
	return true


func _chests() -> bool:
	var found: Dictionary = {}
	var positions: Dictionary = {}
	var floors: Dictionary = {}
	var cave_count := 0
	for site in _sites:
		if site.get("id") != "first_cave":continue
		cave_count += 1
		for room_index in range(site["rooms"].size()):
			var room: Dictionary = site["rooms"][room_index]
			if not _integer(room.get("floor")) or room["floor"] not in [1,2] or not room.get("events") is Array:return false
			floors[int(room["floor"])] = true
			for event in room["events"]:
				if not event is Dictionary:return false
				if event.get("kind") != "treasure":continue
				if not event.get("id") is String or event["id"].is_empty() or not _cell(event.get("cell")):return false
				var position := str([room_index,event["cell"]])
				if found.has(event["id"]) or positions.has(position):return false
				found[event["id"]] = true
				positions[position] = true
	return cave_count == 1 and floors.size() == 2 and found.size() == 3


func _save_observation() -> Dictionary:
	var state := _state()
	if _pose().is_empty() or not state.get("party") is Array or not state.get("inventory") is Dictionary:return {}
	return {"pose":_pose(),"floor":_floor_at(_pose()),"party":state["party"].duplicate(true),"inventory":state["inventory"].duplicate(true)}


func _same(a: Variant, b: Variant) -> bool:
	if typeof(a) != typeof(b):return false
	if a is Dictionary:
		if a.size() != b.size():return false
		for key in a:
			if not b.has(key) or not _same(a[key],b[key]):return false
	elif a is Array:
		if a.size() != b.size() or a.is_typed() != b.is_typed() or a.get_typed_builtin() != b.get_typed_builtin():return false
		for index in range(a.size()):
			if not _same(a[index],b[index]):return false
	else:return a == b
	return true


func _save_load() -> bool:
	var before := _save_observation()
	if before.is_empty() or before["floor"] != 1 or _at(_definition["save_probe"]):return false
	if not await _button(["セーブ"]):return false
	if not await _walk(_definition["save_probe"]):return false
	if _same(before, _save_observation()):return false
	if not await _button(["メニュー"]):return false
	if not await _button(["手動セーブから再開"]):return false
	if not await _settle():return false
	return _same(before, _save_observation())


func _play_route() -> void:
	_blocker = "A04の仲間との会話・村出口への移動が未成立"
	for recruit in _definition["recruits"]:
		if not await _walk(recruit["stand"]):return
		if not await _step_direction(Vector2i(int(recruit["facing"][0]),int(recruit["facing"][1]))):return
		if not _at(recruit["stand"]):return
		if not await _key(KEY_ENTER) or not await _settle():return
	var exit: Dictionary = _definition["village_exit"]
	_blocker = "A05の村出口からの遷移が未成立"
	# 最後の一歩だけを遷移として扱い、メニューや決定キーで退出しない。
	var outside := _outside(_definition["village_entrance"])
	if not await _walk(exit, outside):return
	if not _record("A05", _outward(_definition["village_entrance"]), "村出口から一つ手前・外向きに遷移"):return
	await _frames(6)
	if not _outward(_definition["village_entrance"]):
		_record("A05", false, "操作せず入口へ再突入した")
		return
	var gate: Dictionary = _definition["gate"]
	_blocker = "A06の通行証なしの関所試行が未成立"
	if _has_pass() or not await _walk(gate["before"]):return
	var direction := Vector2i(int(gate["cell"]["cell"][0]-gate["before"]["cell"][0]),int(gate["cell"]["cell"][1]-gate["before"]["cell"][1]))
	_gate_probe_active = true
	for attempt in range(2):
		if not await _step_direction(direction):return
	_gate_probe_active = false
	if not _record("A06", not _gate_breach and not _has_pass() and (_at(gate["before"]) or _at(gate["cell"])), "通行証なしの2歩の通行試行で門の向こうへ進まない"):return
	_blocker = "A07の洞窟入口への歩行が未成立"
	if not await _walk(_outside(_definition["cave_entrance"])):return
	var cave_spawn: Dictionary = _definition["cave_spawn"]
	var entered := await _walk(_world_point(_definition["cave_entrance"]["cell"]), cave_spawn)
	if not _record("A07", entered and _pose().get("node") == "first_cave" and _floor_at(_pose()) == 1, "歩行で洞窟1階へ入る"):return
	if not _record("A10", await _save_load(), "位置・向き・編成・所持品の変更後ロードが完全一致"):return
	_blocker = "A08の階段の往復が未成立"
	for expected_floor in [2,1,2]:
		var link: Dictionary = _definition["stairs_down"] if expected_floor == 2 else _definition["stairs_up"]
		if not await _transition(link) or _floor_at(_pose()) != expected_floor:
			_record("A08", false, "階段の往復順序が成立しない")
			return
	_record("A08", true, "1階→2階→1階→2階を実歩行で確認")
	_blocker = "A11のボス位置への移動・勝利・再訪が未成立"
	if _has_pass() or not await _walk(_definition["boss"]["point"]):return
	if not _boss_won or _boss_starts != 1 or not _has_pass():
		_record("A11", false, "ボス戦開始・実勝利・通行証取得を確認できない")
		return
	if not await _walk(_definition["boss_revisit"]) or not await _walk(_definition["boss"]["point"]):return
	await _frames(6)
	if not _record("A11", _boss_won and _boss_starts == 1 and _has_pass(), "ボス勝利で通行証取得、離れて再訪しても再戦なし"):return
	_blocker = "A12の洞窟からの退出が未成立"
	if not await _transition(_definition["stairs_up"]):return
	if not await _walk(_definition["cave_exit"], _outside(_definition["cave_entrance"])):return
	await _frames(6)
	if not _record("A12", _outward(_definition["cave_entrance"]), "洞窟出口から一つ手前・外向きに戻り再突入しない"):return
	_blocker = "A13の通行証ありの関所通過が未成立"
	if not _has_pass() or not await _walk(gate["before"]):return
	if not await _step_direction(direction):return
	if not _at(gate["beyond"]) and not await _step_direction(direction):return
	_route_finished = _record("A13", _at(gate["beyond"]) and _has_pass(), "通行証を持って門の向こうのセルへ歩行到達")


func _finish() -> void:
	if _finished:return
	_watch()
	_finished = true
	_record("A02", _route_finished and _menu_checked and _forbidden_seen.is_empty(), "禁止ラベルを検出: " + str(_forbidden_seen) if not _forbidden_seen.is_empty() else ("全経路・メニューで禁止ラベルなし" if _route_finished else "全経路を観測できず不在を証明できない"))
	_record("A03", _village_seen and _village_moves > 0 and _left_village and not _village_battle and not _observation_fault, "村内移動から退出までの戦闘なし" if _village_seen and _left_village and not _village_battle and not _observation_fault else "村内経路が未観測、または村内戦闘・観測欠落あり")
	_record("A04", _left_village and _exit_party.size() == 3, "村退出時の人数=%d（必要3）" % _exit_party.size() if _left_village else "村退出時の3人編成を観測できない")
	_record("A14", _route_finished and _started_by_ui and _moves > 0 and _turns > 0 and not _input_violation and not _observation_fault, "通常UI・方向キー・既存戦闘操作だけで全経路到達" if _route_finished and not _input_violation and not _observation_fault else "通常入力だけでの全経路到達が未成立")
	var failed := 0
	for index in range(1,15):
		var id := "A%02d" % index
		var result: Dictionary = _results.get(id,{"ok":false,"reason":"未到達: "+_blocker})
		if not result["ok"]:failed += 1
		print("FIRST_REGION_CHECK: %s %s %s" % [id,"PASS" if result["ok"] else "FAIL",result["reason"]])
	print("FIRST_REGION_PASS: checks=14" if failed == 0 else "FIRST_REGION_FAIL: failed=%d/14" % failed)
	quit(0 if failed == 0 else 1)


func _run() -> void:
	var path: String = str(ProjectSettings.get_setting("application/run/main_scene", ""))
	if path.is_empty() or not ResourceLoader.exists(path):
		_blocker = "起動シーンが存在しない"
		_finish()
		return
	var packed: Variant = load(path)
	if not packed is PackedScene:
		_blocker = "起動シーンがPackedSceneではない"
		_finish()
		return
	_main = packed.instantiate()
	root.add_child(_main)
	process_frame.connect(_watch)
	await _frames()
	var session := _session()
	if session == null or not session.has_method("export_state") or not session.has_method("current_battle") or not _main.has_method("automation_snapshot"):
		_blocker = "既存の読み取り用観測APIがない"
		_finish()
		return
	if not await _button(["新しくはじめる", "新しくはじめる（3人）"]):
		_finish()
		return
	_started_by_ui = not _party().is_empty() and _snapshot().get("mode") != "menu"
	var pose := _pose()
	_record("A01", _started_by_ui and pose.get("layer") == "interior" and pose.get("node") == "start_village" and _party().size() >= 1, "New Game後のstart_village内部・1人以上" if pose.get("node") == "start_village" else "New Game後にstart_village内部の位置情報がない")
	# 現行版の禁止ラベルも実際にメニューを開いて検出する。
	if await _button(["メニュー"]):
		_menu_checked = true
		await _frames()
		if not await _button(["現在の冒険に戻る"]):
			_finish()
			return
	var data_ok := _load_definition()
	_record("A09", data_ok and _chests(), "洞窟2階分の宝箱定義が重複なしで3個" if data_ok else "world/interiors.json のfirst_region定義がない、または不正")
	if data_ok and _results["A01"]["ok"]:
		await _play_route()
	elif data_ok:
		_blocker = "A01の開始位置が未成立"
	_finish()
