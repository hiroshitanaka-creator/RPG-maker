class_name Region2Ruins
extends RefCounted
## 遺跡4階の地形と往復階段。本番の入口・遭遇・物語は後続依頼で接続する。
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/region2_ruins.json")))
	return _data

static func apply_to(document: Dictionary) -> void:
	document["sites"].append(data()["site"].duplicate(true))

static func landing(index: int) -> Array:
	var rooms: Array = data()["site"]["rooms"]
	return rooms[index]["spawn"].duplicate() if index >= 0 and index < rooms.size() else []

static func move(state: Dictionary) -> Dictionary:
	for link in data()["stairs"]:
		if state["room"] == link["from_room"] and state["cell"] == link["from_cell"]:
			state["room"] = link["to_room"]
			state["cell"] = link["to_cell"].duplicate()
			state["facing"] = link["facing"]
			state["entry_lock"] = "region2_ruins_stairs"
			break
	return {"kind":"moved"}
