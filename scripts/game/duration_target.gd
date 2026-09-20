class_name DurationTarget
extends RefCounted

static func definition() -> Dictionary:
	var value: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/duration_target_v1.json"))
	if not value is Dictionary or not value.has_all(["id","target_minutes","min_minutes","max_minutes"]):return {}
	if value["target_minutes"] != 3600 or value["min_minutes"] <= 0 or value["min_minutes"] > value["target_minutes"] or value["max_minutes"] < value["target_minutes"]:return {}
	return value

static func matches(context: Dictionary) -> bool:
	var target := definition()
	return not target.is_empty() and context.get("duration_target_id") == target["id"]

static func includes(milliseconds: int) -> bool:
	var target := definition()
	return not target.is_empty() and milliseconds >= int(target["min_minutes"])*60000 and milliseconds <= int(target["max_minutes"])*60000
