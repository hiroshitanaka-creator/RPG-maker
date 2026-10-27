class_name Region3Port
extends RefCounted
## 採用済み外観と080の5室。既存海域の桟橋から通常移動へ接続する。
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/region3_port.json")))
	return _data

static func apply_to(document: Dictionary) -> void:
	document["sites"].append(data()["site"].duplicate(true))
	document["first_region"].merge(data()["definition"].duplicate(true))

static func connect_world(base: Dictionary) -> Dictionary:
	var result := base.duplicate(true)
	var origin := WorldExpedition.point(result["origin"])
	# 航路の範囲は保ち、港の入口と一歩手前だけを既存世界内へ接続する。
	for point in data()["world_entry_cells"]:
		var cell := WorldExpedition.point(point)-origin
		for field in ["layout","terrain"]:
			var row: String=result[field][cell.y]
			# 既存の橋地形bは徒歩・船の両方を通す。旧保存の船位置も失効させない。
			result[field][cell.y]=row.substr(0,cell.x)+("." if field=="layout" else "b")+row.substr(cell.x+1)
	result["tiles"]["region3_port_entry"]={"path":"assets/tiles/bright_bridge.png","region":[0,0,32,32]}
	var cells: Array=[]
	for point in data()["world_entry_cells"]:
		var cell := WorldExpedition.point(point)-origin
		cells.append([cell.x,cell.y,"region3_port_entry"])
	result["layers"].append({"name":"bridge","cells":cells})
	return result
