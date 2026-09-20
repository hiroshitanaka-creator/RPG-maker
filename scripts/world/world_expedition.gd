class_name WorldExpedition
extends RefCounted
## 広域と拠点内部の進行。旧本編の現在地・章フラグとは保存上も分離する。
static var _graph: Dictionary = {}
static var _sites: Dictionary = {}
static var _nodes: Dictionary = {}
static var _events: Dictionary = {}

static func data() -> Dictionary:
	if _graph.is_empty():
		_graph = _integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/map_graph.json")))
		for node in _graph["nodes"]:
			_nodes[node["id"]] = node
		var source: Dictionary = _integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/interiors.json")))
		for site in source["sites"]:
			_sites[site["id"]] = site
			for room in site["rooms"]:
				if room.has("legacy_location"):
					var rows: Array = []
					for y in range(18):
						var row := ""
						for x in range(32):
							row += "." if ChapterOne.is_walkable(room["legacy_location"], Vector2i(x,y)) else "#"
						rows.append(row)
					room["layout"] = rows
					_place_legacy_events(room)
				for event in room["events"]:
					_events[event["id"]] = event
	return _graph

static func _integers(value: Variant) -> Variant:
	if value is Dictionary:
		var result: Dictionary = {}
		for key in value:
			result[key] = _integers(value[key])
		return result
	if value is Array:
		var result: Array = []
		for item in value:
			result.append(_integers(item))
		return result
	return int(value) if value is float and value == floor(value) else value

static func point(value: Array) -> Vector2i:
	return Vector2i(int(value[0]), int(value[1]))

static func _place_legacy_events(room: Dictionary) -> void:
	var reachable: Array[Vector2i] = [Vector2i(2,4)]
	var seen := {Vector2i(2,4):true}
	var at := 0
	while at < reachable.size():
		var cell := reachable[at]
		at += 1
		for direction in [Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP,Vector2i.DOWN]:
			var next: Vector2i = cell + direction
			if not seen.has(next) and walkable_room(room,next):
				seen[next] = true
				reachable.append(next)
	var used: Array[Vector2i] = [Vector2i(2,4)]
	var markers: Array = [{"owner":room,"key":"exit"}]
	for event in room["events"]:
		markers.append({"owner":event,"key":"cell"})
	for marker in markers:
		var desired := point(marker["owner"][marker["key"]])
		var best := reachable[0]
		var score := 999999
		for cell in reachable:
			if cell in used:
				continue
			var candidate: int = absi(cell.x-desired.x)+absi(cell.y-desired.y)
			if candidate < score:
				score = candidate
				best = cell
		marker["owner"][marker["key"]] = [best.x,best.y]
		used.append(best)

static func node(id: String) -> Dictionary:
	data()
	return _nodes.get(id,{})

static func site(id: String) -> Dictionary:
	data()
	return _sites.get(id,{})

static func room(id: String, index: int) -> Dictionary:
	var definition := site(id)
	return definition["rooms"][index] if not definition.is_empty() and index >= 0 and index < definition["rooms"].size() else {}

static func walkable_room(definition: Dictionary, cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < 32 and cell.y < 18 and definition["layout"][cell.y].substr(cell.x,1) == "."

static func held(required: Array, flags: Dictionary) -> bool:
	for id in required:
		if not flags.get(id,false):
			return false
	return true

static func available_transports(flags: Dictionary) -> Array[String]:
	var result: Array[String] = []
	for mode in data()["transports"]:
		if held(mode["unlock_flags"],flags):
			if mode["id"] not in result:
				result.append(mode["id"])
			for retained in mode["retains"]:
				if retained not in result:
					result.append(retained)
	return result

static func unlocked(id: String, flags: Dictionary) -> bool:
	var entry := node(id)
	return not entry.is_empty() and held(entry["unlock_flags"],flags) and entry["required_transport"] in available_transports(flags)

static func initial(origin: String, legacy_flags: Dictionary) -> Dictionary:
	var cell := WorldTerrain.cell_of(origin)
	var flags := {}
	for flag in data()["flags"]:
		flags[flag["id"]] = false
	flags["world_causeway_open"] = bool(legacy_flags.get("chapter1_cleared",false))
	return {"active":true,"origin":origin,"layer":"world","cell":[cell.x,cell.y],"world_cell":[cell.x,cell.y],"transport":"walk","node":"","room":0,"flags":flags,"seen":[],"cleared":[],"choices":{},"visited":[]}

static func current_room(state: Dictionary) -> Dictionary:
	return room(state["node"],state["room"]) if state.get("layer") == "interior" else {}

static func event_at(state: Dictionary) -> Dictionary:
	var definition := current_room(state)
	if definition.is_empty():
		return {}
	for event in definition["events"]:
		if point(event["cell"]) == point(state["cell"]):
			return event
	return {}

static func done(state: Dictionary, id: String) -> bool:
	return id in state["seen"] or id in state["cleared"]

static func ready(state: Dictionary, event: Dictionary) -> bool:
	for id in event.get("requires",[]):
		if not done(state,id):
			return false
	return true

static func walkable(state: Dictionary, cell: Vector2i) -> bool:
	if state["layer"] != "world":
		return walkable_room(current_room(state),cell)
	return WorldTerrain.passable(cell,state["transport"]) and (state["transport"] != "walk" or region_open(cell,state["flags"]))

static func region_open(cell: Vector2i, flags: Dictionary) -> bool:
	for region in WorldTerrain.data()["regions"]:
		var bounds: Array = region["bounds"]
		if cell.x < bounds[0] or cell.y < bounds[1] or cell.x > bounds[2] or cell.y > bounds[3]:
			continue
		var first: Dictionary = {}
		for candidate in data()["nodes"]:
			if candidate["region"] == region["id"] and (first.is_empty() or candidate["progression_index"] < first["progression_index"]):
				first = candidate
		return not first.is_empty() and unlocked(first["id"],flags)
	return false

static func move(state: Dictionary, cell: Vector2i) -> bool:
	var current := point(state["cell"])
	if absi(current.x-cell.x)+absi(current.y-cell.y) != 1 or not walkable(state,cell):
		return false
	state["cell"] = [cell.x,cell.y]
	if state["layer"] == "world":
		state["world_cell"] = state["cell"].duplicate()
	return true

static func transport_allowed(state: Dictionary, mode: String) -> bool:
	var cell := point(state["cell"])
	if state["layer"] != "world" or WorldTerrain.node_at(cell).is_empty() or mode not in available_transports(state["flags"]) or not WorldTerrain.passable(cell,mode):
		return false
	return mode != "walk" or region_open(cell,state["flags"])

static func change_transport(state: Dictionary, mode: String) -> bool:
	if not transport_allowed(state,mode):
		return false
	state["transport"] = mode
	return true

static func at_origin(state: Dictionary) -> bool:
	if state["layer"] == "interior":
		return state["node"] == state["origin"]
	return point(state["cell"]) == WorldTerrain.cell_of(state["origin"])

static func interact(state: Dictionary) -> Dictionary:
	if state["layer"] == "world":
		var id := WorldTerrain.node_at(point(state["cell"]))
		if not unlocked(id,state["flags"]):
			return {"kind":"blocked","text":["まだ入れる拠点ではありません。解放された道と乗り物を確かめてください。"]}
		state["node"] = id
		state["room"] = 0
		state["world_cell"] = state["cell"].duplicate()
		state["layer"] = "interior"
		state["cell"] = room(id,0)["spawn"].duplicate()
		if id not in state["visited"]:
			state["visited"].append(id)
		return {"kind":"moved"}
	var definition := current_room(state)
	var cell := point(state["cell"])
	if cell == point(definition["exit"]):
		if state["room"] == 0:
			state["layer"] = "world"
			state["node"] = ""
			state["cell"] = state["world_cell"].duplicate()
		else:
			state["room"] -= 1
			state["cell"] = current_room(state)["next"].duplicate()
		return {"kind":"moved"}
	if not definition["next"].is_empty() and cell == point(definition["next"]):
		for event in definition["events"]:
			if event["kind"] in ["observe","battle"] and not done(state,event["id"]):
				return {"kind":"blocked","text":["この区画には、まだ調べる記録か退ける魔物が残っています。"]}
		state["room"] += 1
		state["cell"] = current_room(state)["spawn"].duplicate()
		return {"kind":"moved"}
	var event := event_at(state)
	if event.is_empty():
		return {"kind":"blocked","text":["記録・魔物・机の印の上で調べてください。出口は左下です。"]}
	if event["kind"] == "observe":
		if not done(state,event["id"]):
			state["seen"].append(event["id"])
		return {"kind":"dialogue","text":event["text"].duplicate(true)}
	if event["kind"] == "rest":
		return {"kind":"rest","text":event["text"].duplicate(true)}
	if not ready(state,event):
		return {"kind":"blocked","text":["先に周囲の記録を調べ、残る魔物を退けてください。"]}
	if event["kind"] == "battle":
		return {"kind":"dialogue","text":["この場所の魔物は退けました。"]} if done(state,event["id"]) else event.duplicate(true)
	if state["choices"].has(state["node"]):
		return {"kind":"dialogue","text":[event["results"][state["choices"][state["node"]]],"この依頼の報酬は受取済みです。"]}
	return event.duplicate(true)

static func choose(state: Dictionary, option: int) -> Dictionary:
	var event := event_at(state)
	if event.get("kind") != "choice" or option < 0 or option >= event["options"].size() or state["choices"].has(state["node"]) or not ready(state,event):
		return {}
	var grant: String = event.get("grant","")
	if not grant.is_empty():
		for flag in data()["flags"]:
			if flag["id"] == grant and not held(flag["requires"],state["flags"]):
				return {}
	state["choices"][state["node"]] = option
	if not grant.is_empty():
		state["flags"][grant] = true
	var text: Array = [event["results"][option],"回復薬を%d個受け取りました。" % int(event["potions"][option])]
	var messages := {"world_causeway_open":"内陸の道が開きました。全図で新しい行き先を確認できます。","world_ship_unlocked":"船が使えるようになりました。青い点の船着場で切り替えられます。","world_flight_unlocked":"飛行が使えるようになりました。拠点入口で切り替えると海や山を越えられます。"}
	if messages.has(grant):
		text.append(messages[grant])
	return {"text":text,"potions":int(event["potions"][option]),"grant":grant}

static func _cell_valid(value: Variant) -> bool:
	return value is Array and value.size() == 2 and value[0] is int and value[1] is int

static func valid(state: Variant) -> bool:
	data()
	if not state is Dictionary or not state.has_all(["active","origin","layer","cell","world_cell","transport","node","room","flags","seen","cleared","choices","visited"]):
		return false
	if not state["active"] is bool or state["origin"] not in ChapterOne.TOWNS or not _cell_valid(state["cell"]) or not _cell_valid(state["world_cell"]) or not state["room"] is int or not state["node"] is String or not state["transport"] is String:
		return false
	if not state["flags"] is Dictionary or state["flags"].size() != _graph["flags"].size():
		return false
	for flag in _graph["flags"]:
		if not state["flags"].get(flag["id"]) is bool:
			return false
	if state["transport"] not in available_transports(state["flags"]):
		return false
	if state["layer"] == "world":
		if state["node"] != "" or state["room"] != 0 or state["cell"] != state["world_cell"] or not walkable(state,point(state["cell"])):
			return false
	elif state["layer"] == "interior":
		var definition := current_room(state)
		if definition.is_empty() or not unlocked(state["node"],state["flags"]) or point(state["world_cell"]) != WorldTerrain.cell_of(state["node"]) or not walkable_room(definition,point(state["cell"])):
			return false
	else:
		return false
	for field in ["seen","cleared","visited"]:
		if not state[field] is Array:
			return false
		var seen: Array = []
		for id in state[field]:
			if not id is String or id in seen:
				return false
			seen.append(id)
			if field == "visited":
				if not _nodes.has(id):
					return false
			elif not _events.has(id) or _events[id]["kind"] != ("observe" if field == "seen" else "battle"):
				return false
	if not state["choices"] is Dictionary:
		return false
	for id in state["choices"]:
		var event: Dictionary = _events.get(str(id)+"_choice",{})
		var option: Variant = state["choices"][id]
		if event.is_empty() or not option is int or option < 0 or option >= event["options"].size() or not ready(state,event):
			return false
		if not event.get("grant","").is_empty() and not state["flags"][event["grant"]]:
			return false
	return true
