class_name Region2Port
extends RefCounted
## 新ゲームの第2港。旧本編の汎用拠点定義は変更しない。
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/region2_port.json")))
	return _data

static func apply_to(document: Dictionary) -> void:
	var extra := data()
	for i in range(document["sites"].size()):
		if document["sites"][i]["id"] == "brine_port":
			document["sites"][i] = extra["site"].duplicate(true)
			break
	document["first_region"].merge(extra["definition"].duplicate(true))
