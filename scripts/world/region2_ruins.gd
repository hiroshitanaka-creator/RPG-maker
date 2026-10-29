class_name Region2Ruins
extends RefCounted
## 遺跡4階の地形・往復階段と採用済みの世界接続。遭遇・物語は後続依頼。
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/region2_ruins.json")))
	return _data

static func apply_to(document: Dictionary) -> void:
	document["sites"].append(data()["site"].duplicate(true))
	if data()["world_connection"]["enabled"]:
		document["first_region"]["region2_ruins_entrance"] = {"cell":data()["world_connection"]["world_cell"].duplicate(),"outward":[0,1]}

static func enter(saved: Dictionary) -> bool:
	var connection: Dictionary = data()["world_connection"]
	var state: Dictionary = saved["overworld"]
	if not connection["enabled"] or not saved["progress_flags"].get(Region2ShrineStory.COMPLETE_FLAG,false):return false
	if state["layer"] != "world" or state.get("transport","walk") != "walk" or state["cell"] != connection["world_cell"]:return false
	FirstRegion.place(state,{"layer":"interior","node":"region2_ruins","room":connection["room"],"cell":connection["landing"]})
	state["facing"] = connection["entry_facing"]
	state["entry_lock"] = "region2_ruins_entrance"
	return true

static func landing(index: int) -> Array:
	var rooms: Array = data()["site"]["rooms"]
	return rooms[index]["spawn"].duplicate() if index >= 0 and index < rooms.size() else []

static func move(state: Dictionary) -> Dictionary:
	var connection: Dictionary = data()["world_connection"]
	# 旧内部保存も未完了のまま退場できる。入場の条件を保存validや出口へ広げない。
	if connection["enabled"] and state["room"] == connection["room"] and state["cell"] == connection["exit_cell"]:
		FirstRegion.place(state,{"layer":"world","node":"","room":0,"cell":connection["return_cell"]})
		state["facing"] = connection["return_facing"]
		state["entry_lock"] = "region2_ruins_entrance"
		# 既存027の故障注入は関数末尾の移動通知を対象にする。退出通知と混線させない。
		var exited := {"kind":"moved"}
		return exited
	for link in data()["stairs"]:
		if state["room"] == link["from_room"] and state["cell"] == link["from_cell"]:
			state["room"] = link["to_room"]
			state["cell"] = link["to_cell"].duplicate()
			state["facing"] = link["facing"]
			state["entry_lock"] = "region2_ruins_stairs"
			break
	return {"kind":"moved"}
