class_name IntegratedCampaign
extends RefCounted
static var _data: Dictionary={}
static var _routes: Dictionary={}
static func data() -> Dictionary:
	if _data.is_empty():
		_data=LongCampaign._integers(JSON.parse_string(FileAccess.get_file_as_string("res://data/integrated_campaign.json")))
		for entry in _data["assignments"].values():
			for route in entry["routes"]:
				if not _routes.has(route["room"]):_routes[route["room"]]=[]
				_routes[route["room"]].append({"cell":route["cell"],"flag":entry["flag"]})
	return _data
static func assignment(id: String) -> Dictionary:
	return data()["assignments"].get(id,{})
static func route_open(room_id: String,cell: Vector2i,flags: Dictionary) -> bool:
	data()
	for route in _routes.get(room_id,[]):
		if flags.get(route["flag"],false) and route["cell"]==[cell.x,cell.y]:return true
	return false
static func effective_method(methods: Array) -> bool:
	for method in methods:
		if method in data()["methods_open_route"]:return true
	return false
static func opens_route(methods: Array) -> bool:
	return "device" in methods or "seal_break" in methods
static func grants_weapon(methods: Array) -> bool:
	return "conducted_hit" in methods or "disarm" in methods
static func flags_valid(state: Dictionary) -> bool:
	var allowed: Dictionary={}
	for id in data()["assignments"]:
		var entry: Dictionary=assignment(id)
		if entry["flag"].is_empty():continue
		var outcome: Dictionary=state.get("integrated",{}).get("outcomes",{}).get(id,{})
		allowed[entry["flag"]]=opens_route(outcome.get("methods",[]))
	for flag in state.get("progress_flags",{}):
		if str(flag).begins_with("integration_route_") and (not allowed.has(flag) or state["progress_flags"][flag]!=allowed[flag]):return false
	for flag in allowed:
		if allowed[flag] and not state["progress_flags"].get(flag,false):return false
	return true
