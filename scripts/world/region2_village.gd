class_name Region2Village
extends RefCounted
## 採用済みの村背景を参照し、移動と既存の旅状態だけを接続する。
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/region2_village.json")))
		var backgrounds: Dictionary = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://"+str(_data["backgrounds"]))))
		_data["maps"] = {}
		for index in range(_data["site"]["rooms"].size()):
			var room: Dictionary = _data["site"]["rooms"][index]
			var map: Dictionary = backgrounds["maps"][room["background"]]
			room["layout"] = map["layout"].duplicate()
			_data["maps"]["region2_village:%d" % index] = map.duplicate(true)
		# 船の帰着先は既存第2港の定義を参照し、独立した桟橋を作らない。
		for destination in _data["destinations"]:
			for port in Region2Port.data()["destinations"]:
				if port["id"] == destination["ship_destination"]:
					destination["ship_cell"] = port["ship_cell"].duplicate()
	return _data

static func apply_to(document: Dictionary) -> void:
	var extra := data()
	document["sites"].append(extra["site"].duplicate(true))
	document["first_region"].merge(extra["definition"].duplicate(true))
