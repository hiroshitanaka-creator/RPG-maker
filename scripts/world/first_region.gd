class_name FirstRegion
extends RefCounted
## 最初の地方の配置・衝突・通常歩行イベント。旧本編の章進行は扱わない。

static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/interiors.json")))
	return _data["first_region"]

static func room(state: Dictionary) -> Dictionary:
	data()
	for site in _data["sites"]:
		if site["id"] == state["node"]:
			return site["rooms"][state["room"]] if state["room"] >= 0 and state["room"] < site["rooms"].size() else {}
	return {}

static func at(state: Dictionary, point: Dictionary) -> bool:
	return state["layer"] == point["layer"] and state["node"] == point["node"] and state["room"] == point["room"] and state["cell"] == point["cell"]

static func place(state: Dictionary, point: Dictionary) -> void:
	for key in ["layer", "node", "room", "cell"]:
		state[key] = point[key].duplicate() if point[key] is Array else point[key]

static func outside(key: String) -> Dictionary:
	var entry: Dictionary = data()[key]
	return {"layer":"world", "node":"", "room":0, "cell":[entry["cell"][0]+entry["outward"][0], entry["cell"][1]+entry["outward"][1]]}

static func walkable(saved: Dictionary, cell: Vector2i) -> bool:
	var state: Dictionary = saved["overworld"]
	if state["layer"] == "world":
		if [cell.x,cell.y] == data()["gate"]["cell"]["cell"] and int(saved["inventory"].get("gate_pass",0)) == 0:return false
		for event in FirstRegionPresentation.residents(state):
			if event_cell(saved,event) == cell:return false
		return FirstRegionPresentation.world_walkable(cell)
	var layout: Array = room(state).get("layout",[])
	if cell.y < 0 or cell.y >= layout.size() or cell.x < 0 or cell.x >= str(layout[cell.y]).length():return false
	if str(layout[cell.y]).substr(cell.x,1) != ".":return false
	for event in room(state).get("events",[]):
		if event["kind"] == "recruit" and joined(saved,event["actor"]):continue
		if event["kind"] in ["recruit","rest","shop","weapon_shop","npc"] and event_cell(saved,event) == cell:return false
	return true

static func joined(saved: Dictionary, id: String) -> bool:
	for actor in saved["party"]:
		if actor["id"] == id:return true
	return false

static func walkable_cells(saved: Dictionary) -> Array:
	var cells: Array = []
	var state: Dictionary = saved["overworld"]
	var layout: Array = room(state).get("layout",[])
	var bounds: Array = data()["bounds"] if state["layer"] == "world" else [0,0,str(layout[0]).length()-1,layout.size()-1]
	for y in range(bounds[1],bounds[3]+1):
		for x in range(bounds[0],bounds[2]+1):
			if walkable(saved,Vector2i(x,y)):cells.append([x,y])
	return cells

static func move(saved: Dictionary, cell: Vector2i) -> Dictionary:
	var state: Dictionary = saved["overworld"]
	var before := WorldExpedition.point(state["cell"])
	if absi(cell.x-before.x)+absi(cell.y-before.y) != 1 or not walkable(saved,cell):return {}
	state["cell"] = [cell.x,cell.y]
	state["entry_lock"] = ""
	var definition := data()
	if state["layer"] == "world":
		for entry in [["village_entrance","start_village",1,definition["village_spawn"]["cell"]],["cave_entrance","first_cave",0,definition["cave_spawn"]["cell"]]]:
			if state["cell"] == definition[entry[0]]["cell"]:
				place(state,{"layer":"interior","node":entry[1],"room":entry[2],"cell":entry[3]})
				return {"kind":"moved"}
		if at(state,definition["gate"]["cell"]):
			return {"kind":"dialogue","speaker":"門番","sound":"door","text":["通行証を確認しました。お通りください。"]}
	else:
		for entry in [["village_exit","village_entrance"],["cave_exit","cave_entrance"]]:
			if at(state,definition[entry[0]]):
				if state["node"] == "start_village" and saved["party"].size() < 3:
					state["cell"] = [before.x,before.y]
					return {"kind":"dialogue","text":["村の二人に声をかけてから出発しよう。"]}
				place(state,outside(entry[1]))
				state["facing"] = [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP].find(WorldExpedition.point(definition[entry[1]]["outward"]))
				state["entry_lock"] = entry[1]
				return {"kind":"moved"}
		var links: Array = definition["doors"].duplicate()
		links.append(definition["stairs_down"])
		links.append(definition["stairs_up"])
		for link in links:
			if at(state,link["from"]):
				place(state,link["to"])
				return {"kind":"moved"}
		if at(state,definition["boss"]["point"]) and "first_boss" not in state["cleared"]:
			return {"kind":"battle","id":"first_boss","enemies":definition["boss"]["enemies"],"seed":randi()}
	if state["node"] != "start_village":
		var rule: Dictionary = definition["encounters"]["world" if state["layer"] == "world" else "first_cave"]
		if randf() < float(rule["chance"]):
			return {"kind":"battle","id":"first_region_encounter","enemies":rule["enemies"],"seed":randi()}
	return {"kind":"moved"}

static func event_key(state: Dictionary, event: Dictionary) -> String:
	return "%s:%d:%s" % [state["node"],state["room"],event["id"]]

static func event_cell(saved: Dictionary, event: Dictionary) -> Vector2i:
	var state: Dictionary = saved["overworld"]
	var record: Dictionary = state.get("residents",{}).get(event_key(state,event),{})
	return WorldExpedition.point(record.get("cell",event["cell"]))

static func event_facing(saved: Dictionary, event: Dictionary) -> int:
	var state: Dictionary = saved["overworld"]
	return int(state.get("residents",{}).get(event_key(state,event),{}).get("facing",0))

static func face_event(saved: Dictionary, event: Dictionary) -> void:
	var state: Dictionary = saved["overworld"]
	if not state.has("residents"):state["residents"]={}
	var key := event_key(state,event)
	var position := event_cell(saved,event)
	var direction := WorldExpedition.point(state["cell"])-position
	var facing := 1 if direction.x < 0 else 2 if direction.x > 0 else 3 if direction.y < 0 else 0
	state["residents"][key]={"cell":[position.x,position.y],"facing":facing}

static func advance_residents(saved: Dictionary) -> bool:
	var state: Dictionary = saved["overworld"]
	if state["layer"] != "interior" or state["node"] != "start_village":return false
	var changed := false
	for event in residents_for(saved):
		if not event.has("patrol"):continue
		var path: Array = event["patrol"]
		var position := event_cell(saved,event)
		var index := path.find([position.x,position.y])
		var target := WorldExpedition.point(path[(index+1)%path.size()])
		if target == WorldExpedition.point(state["cell"]) or not walkable(saved,target):continue
		if not state.has("residents"):state["residents"]={}
		var direction := target-position
		state["residents"][event_key(state,event)]={"cell":[target.x,target.y],"facing":1 if direction.x<0 else 2 if direction.x>0 else 3 if direction.y<0 else 0}
		changed=true
	return changed

static func residents_for(saved: Dictionary) -> Array:
	return FirstRegionPresentation.residents(saved["overworld"])

static func valid(saved: Dictionary) -> bool:
	var region: Variant = saved.get("first_region")
	var state: Variant = saved.get("overworld")
	if not region is Dictionary or region.get("version") != 1 or not region.get("reserve") is Array or not region.get("coins") is int or region["coins"] < 0:return false
	if not state is Dictionary or not state.has_all(["active","layer","node","room","cell","facing","cleared","opened","entry_lock"]):return false
	if state["active"] != true or state["layer"] not in ["world","interior"] or not state["node"] is String or not state["room"] is int:return false
	if not state["cell"] is Array or state["cell"].size() != 2 or not state["cell"][0] is int or not state["cell"][1] is int:return false
	if not state["facing"] is int or state["facing"] not in [0,1,2,3] or not state["entry_lock"] is String:return false
	if not state["cleared"] is Array or not state["opened"] is Array:return false
	var residents: Variant=state.get("residents",{})
	if not residents is Dictionary:return false
	for key in residents:
		var record: Variant=residents[key]
		if not key is String or not record is Dictionary:return false
		var cell: Variant=record.get("cell")
		if not cell is Array or cell.size()!=2 or not cell[0] is int or not cell[1] is int:return false
		if not record.get("facing") is int or record["facing"] not in [0,1,2,3]:return false
	if state["layer"] == "interior" and (state["node"] not in ["start_village","first_cave"] or room(state).is_empty()):return false
	if state["layer"] == "world" and (state["node"] != "" or state["room"] != 0):return false
	if not saved["inventory"].get("gate_pass",0) is int or saved["inventory"].get("gate_pass",0) not in [0,1]:return false
	if ("first_boss" in state["cleared"]) != (saved["inventory"].get("gate_pass",0) == 1):return false
	return walkable(saved,WorldExpedition.point(state["cell"]))
