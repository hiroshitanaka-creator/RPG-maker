class_name FirstRegionTravel
extends RefCounted
## 第1地方の船・訪問済み転移先。旧本編の移動解放とは独立した状態を持つ。
static var _data: Dictionary={}
static func data() -> Dictionary:
	if _data.is_empty():_data=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/first_region_travel.json")))
	return _data

static func ensure(saved: Dictionary) -> Dictionary:
	if not saved["first_region"].has("travel"):
		var visited: Array=["start_village"]
		if saved["progress_flags"].get("castle_north_permission",false):visited.append("first_castle")
		if saved["overworld"]["node"]=="first_port":visited.append("first_port")
		saved["first_region"]["travel"]={"version":1,"visited":visited,"return_learned":false,"ship_owned":false,"ship_cell":[]}
	return saved["first_region"]["travel"]

static func visit(saved: Dictionary, id: String) -> void:
	var travel := ensure(saved)
	if id in ["start_village","first_castle","first_port"] and id not in travel["visited"]:travel["visited"].append(id)

static func snapshot(saved: Dictionary) -> Dictionary:
	return saved.get("first_region",{}).get("travel",{})

static func ship_water(cell: Vector2i) -> bool:
	var bounds: Array=data()["sea_bounds"]
	if cell.x<bounds[0] or cell.y<bounds[1] or cell.x>bounds[2] or cell.y>bounds[3]:return false
	var m: Dictionary=FirstRegionPresentation.data()["maps"]["world"]
	var p := cell-WorldExpedition.point(m["origin"])
	return p.x>=0 and p.y>=0 and p.x<m["width"] and p.y<m["height"] and str(m["terrain"][p.y]).substr(p.x,1) in ["~","b"]

static func dock_for(saved: Dictionary) -> Dictionary:
	var travel := snapshot(saved)
	if not travel.get("ship_owned",false):return {}
	for dock in data()["docks"]:
		if travel["ship_cell"]!=dock["ship_cell"]:continue
		if saved["overworld"].get("transport","walk")=="ship":
			if saved["overworld"]["cell"]==dock["ship_cell"]:return dock
		elif FirstRegion.at(saved["overworld"],dock["land"]):return dock
	return {}

static func boarding_label(saved: Dictionary) -> String:
	if dock_for(saved).is_empty():return ""
	return "船を降りる" if saved["overworld"].get("transport","walk")=="ship" else "船に乗る"

static func board_or_land(saved: Dictionary) -> bool:
	var dock := dock_for(saved)
	if dock.is_empty():return false
	var state: Dictionary=saved["overworld"]
	if state.get("transport","walk")=="ship":
		state["transport"]="walk";FirstRegion.place(state,dock["land"]);state["facing"]=0
	else:
		state["transport"]="ship";FirstRegion.place(state,{"layer":"world","node":"","room":0,"cell":dock["ship_cell"]});state["facing"]=2
	state["entry_lock"]="ship_dock"
	return true

static func can_return(saved: Dictionary) -> bool:
	return snapshot(saved).get("return_learned",false) and (saved["overworld"]["layer"]=="world" or saved["overworld"]["node"] in ["start_village","first_castle","first_port"])

static func return_to(saved: Dictionary, actor_id: String, destination: String) -> bool:
	if not can_return(saved) or destination not in snapshot(saved).get("visited",[]):return false
	var actor: Dictionary={};var target: Dictionary={}
	for member in saved["party"]:
		if member["id"]==actor_id:actor=member
	for place in data()["destinations"]:
		if place["id"]==destination:target=place
	if actor.is_empty() or target.is_empty() or actor["hp"]<=0 or actor["mp"]<data()["return_mp"]:return false
	var point := FirstRegion.outside(target["entrance"])
	actor["mp"]-=data()["return_mp"]
	var state: Dictionary=saved["overworld"];state["transport"]="walk";FirstRegion.place(state,point)
	state["facing"]=[Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP].find(WorldExpedition.point(FirstRegion.data()[target["entrance"]]["outward"]))
	state["entry_lock"]="return_spell"
	if snapshot(saved).get("ship_owned",false):saved["first_region"]["travel"]["ship_cell"]=data()["docks"][0]["ship_cell"].duplicate()
	return true

static func valid(saved: Dictionary) -> bool:
	var state: Dictionary=saved["overworld"]
	if state.get("transport","walk") not in ["walk","ship"]:return false
	if not saved["first_region"].has("travel"):return state.get("transport","walk")=="walk"
	var travel: Variant=saved["first_region"]["travel"]
	if not travel is Dictionary or travel.get("version")!=1 or not travel.get("visited") is Array:return false
	if not travel.get("return_learned") is bool or not travel.get("ship_owned") is bool or not travel.get("ship_cell") is Array:return false
	var seen: Array=[]
	for id in travel["visited"]:
		if id not in ["start_village","first_castle","first_port"] or id in seen:return false
		seen.append(id)
	if (travel["return_learned"] or travel["ship_owned"]) and ("first_port" not in seen or not saved["progress_flags"].get("mountain_path_open",false)):return false
	if travel["ship_owned"]:
		var cell: Array=travel["ship_cell"]
		if cell.size()!=2 or not cell[0] is int or not cell[1] is int or not ship_water(Vector2i(cell[0],cell[1])):return false
	elif not travel["ship_cell"].is_empty():return false
	if state.get("transport","walk")=="ship":
		return travel["ship_owned"] and state["layer"]=="world" and state["cell"]==travel["ship_cell"]
	return true
