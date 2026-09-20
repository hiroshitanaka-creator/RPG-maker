class_name CampaignContent
extends RefCounted

static var _source: Dictionary = {}
static var _circuits: Dictionary = {}
static var _sections: Dictionary = {}
static var _content_hash: String = ""


static func data() -> Dictionary:
	if _source.is_empty():
		var text := FileAccess.get_file_as_string("res://data/campaign_content_v1.json")
		var raw: Variant = JSON.parse_string(text)
		if raw is Dictionary:
			_content_hash = text.sha256_text()
			_source = _integers(raw)
			for circuit in _source.get("circuits",[]):
				_circuits[circuit["id"]] = circuit
				for section in circuit["sections"]:
					_sections[section["id"]] = section
	return _source


static func content_hash() -> String:
	data()
	return _content_hash


static func _integers(value: Variant) -> Variant:
	if value is Dictionary:
		var result: Dictionary = {}
		for key in value:
			result[key] = _integers(value[key])
		return result
	if value is Array:
		var result: Array = []
		for item in value:
			result.append(_integers(item))
		return result
	return int(value) if value is float and value == floor(value) else value


static func circuit(identifier: String) -> Dictionary:
	data()
	return _circuits[identifier] if _circuits.has(identifier) else LongCampaign.mission(identifier)


static func section(identifier: String) -> Dictionary:
	data()
	return _sections[identifier] if _sections.has(identifier) else LongCampaign.room(identifier)


static func step(expedition: Dictionary, flags: Dictionary = {}) -> Dictionary:
	if not LongCampaign.mission(expedition.get("id","")).is_empty():return LongCampaign.step(expedition,flags)
	var source := circuit(expedition.get("id",""))
	var at := int(expedition.get("stage",-1))
	if source.is_empty() or at < 0 or at >= source["steps"].size():
		return {}
	return source["steps"][at].duplicate(true)


static func pending(state: Dictionary, requested: String = "") -> Dictionary:
	if int(state.get("content_revision",0)) != 1 or not state.get("expedition",{}).is_empty() or not state.get("return_point",{}).is_empty():
		return {}
	for source in data()["circuits"]:
		if state["world"]["quest_step"] == source["trigger_step"] and not state["progress_flags"].get("circuit_"+source["id"]+"_cleared",false):
			return source
	return LongCampaign.pending(state,requested)


static func is_walkable(identifier: String, cell: Vector2i, flags: Dictionary = {}) -> bool:
	if not LongCampaign.room(identifier).is_empty():return LongCampaign.is_walkable(identifier,cell,flags)
	var room := section(identifier)
	return not room.is_empty() and cell.x >= 0 and cell.y >= 0 and cell.x < 32 and cell.y < 18 and room["layout"][cell.y].substr(cell.x,1) == "."


static func walkable_cells(identifier: String, flags: Dictionary = {}) -> Array:
	if not LongCampaign.room(identifier).is_empty():return LongCampaign.walkable_cells(identifier,flags)
	var result: Array = []
	for y in range(18):
		for x in range(32):
			if is_walkable(identifier,Vector2i(x,y)):
				result.append([x,y])
	return result


static func valid_state(state: Dictionary) -> bool:
	if not state.get("content_revision",0) is int or state.get("content_revision",0) not in [0,1]:
		return false
	var current: Variant = state.get("expedition",{})
	if not current is Dictionary:
		return false
	if not LongCampaign.validate_flags(state["progress_flags"],current):return false
	if not LongCampaign.mission(current.get("id","")).is_empty():return LongCampaign.valid_state(state)
	for key in state["progress_flags"]:
		if str(key).begins_with("circuit_") and str(key).ends_with("_cleared") and circuit(str(key).trim_prefix("circuit_").trim_suffix("_cleared")).is_empty():
			return false
	if current.is_empty():
		return str(state["world"].get("section","")).is_empty() and str(state.get("return_point",{}).get("section","")).is_empty()
	if int(state.get("content_revision",0)) != 1 or not current.has_all(["id","stage","wave","origin","solved"]):
		return false
	if not current["id"] is String or not current["stage"] is int or not current["wave"] is int or not current["solved"] is Array or not current["origin"] is Dictionary:
		return false
	var definition := circuit(current["id"])
	var task := step(current)
	if definition.is_empty() or task.is_empty() or state["world"]["quest_step"] != definition["trigger_step"] or current["origin"].get("quest_step") != definition["trigger_step"]:
		return false
	var origin: Dictionary = current["origin"]
	var base := StoryCampaign.step(definition["trigger_step"])
	if origin.get("location") != base["location"] or origin.get("player_cell") != base["cell"] or not str(origin.get("section","")).is_empty():
		return false
	var active: Dictionary = state["world"] if state.get("return_point",{}).is_empty() else state["return_point"]
	if active.get("location") != task["location"] or active.get("section") != task["section"] or current["wave"] < 0 or current["wave"] > (1 if task["kind"] == "battle" else 0):
		return false
	var expected: Array = []
	for index in range(current["stage"]):
		var previous: Dictionary = definition["steps"][index]
		if previous["kind"] == "challenge":
			expected.append(previous["id"])
	return current["solved"] == expected


static func audit(enemies: Dictionary) -> Array[String]:
	var errors: Array[String] = []
	var source := data()
	if source.get("circuits",[]).size() != 5 or _sections.size() != 25:
		errors.append("本編の追加区画は既存5ダンジョン内の25区画です。")
	var identifiers: Array = []
	for area in source.get("circuits",[]):
		for room in area["sections"]:
			if room["layout"].size() != 18:
				errors.append("区画の高さは18マスです。")
			for row in room["layout"]:
				if row.length() != 32:
					errors.append("区画の幅は32マスです。")
		for task in area["steps"]:
			if task["kind"] not in ["dialogue","battle","challenge","section_travel","circuit_complete"]:
				errors.append("追加区画に未知の進行種別があります。")
			if task["id"] in identifiers:
				errors.append("追加課題のIDが重複しています。")
			identifiers.append(task["id"])
			if not is_walkable(task["section"],Vector2i(task["cell"][0],task["cell"][1])):
				errors.append("追加課題の地点を歩けません。")
			for enemy in task.get("enemies",[]):
				if not enemies.has(enemy):
					errors.append("追加区画に未知の敵があります。")
			if task["kind"] == "challenge" and (task["options"].size() != 3 or task["answer"] not in range(3)):
				errors.append("課題の選択肢と正答が不正です。")
			if task["kind"] == "challenge":
				for key in ["reward_hp_percent","reward_mp_percent"]:
					if not BattleCatalog._is_integer(task.get(key,0),0) or int(task.get(key,0))>100:errors.append("区画の休息報酬が不正です。")
	return errors
