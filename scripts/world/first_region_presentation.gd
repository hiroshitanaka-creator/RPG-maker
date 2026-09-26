class_name FirstRegionPresentation
extends RefCounted
## 描画層と通行地形は同じ本番データを参照する。
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/first_region_visuals.json")))
	return _data

static func map_for(state: Dictionary) -> Dictionary:
	var key := "world" if state["layer"] == "world" else "%s:%d" % [state["node"],state["room"]]
	return data()["maps"].get(key,{})

static func world_walkable(cell: Vector2i) -> bool:
	var document: Dictionary = data()["maps"]["world"]
	var local := cell-WorldExpedition.point(document["origin"])
	return local.x >= 0 and local.y >= 0 and local.x < document["width"] and local.y < document["height"] and str(document["layout"][local.y]).substr(local.x,1) == "."

static func place_name(state: Dictionary) -> String:
	return "エルヴァ地方" if state["layer"] == "world" else str(FirstRegion.room(state).get("title",""))

static func residents(state: Dictionary) -> Array:
	return data()["maps"]["world"].get("residents",[]) if state["layer"] == "world" else FirstRegion.room(state).get("events",[])
