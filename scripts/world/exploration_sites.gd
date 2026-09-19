class_name ExplorationSites
extends RefCounted

static var _source: Dictionary = {}


static func data() -> Dictionary:
	if _source.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/exploration_v1.json"))
		if parsed is Dictionary:
			_source = parsed
	return _source


static func all_sites() -> Array:
	var sites: Array = data().get("sites",[]).duplicate(true)
	for site in sites:
		if not site is Dictionary:
			continue
		# JSONの数値をマス座標の整数へ揃え、移動・調査・保存で同じ位置として扱う。
		if _cell_valid(site.get("cell")):
			site["cell"] = [int(site["cell"][0]),int(site["cell"][1])]
		if site.get("opens") is Array:
			for index in range(site["opens"].size()):
				var cell: Variant = site["opens"][index]
				if _cell_valid(cell):
					site["opens"][index] = [int(cell[0]),int(cell[1])]
	return sites


static func by_id(identifier: String) -> Dictionary:
	for site in all_sites():
		if site["id"] == identifier:
			return site
	return {}


static func in_location(location: String, flags: Dictionary) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for site in all_sites():
		if site["location"] == location:
			site["complete"] = bool(flags.get("exploration_"+site["id"],false))
			result.append(site)
	return result


static func is_walkable(location: String, cell: Vector2i, flags: Dictionary) -> bool:
	if ChapterOne.is_walkable(location,cell):
		return true
	for site in in_location(location,flags):
		if site["kind"] == "device" and site["complete"] and [cell.x,cell.y] in site["opens"]:
			return true
	return false


static func valid_flags(flags: Dictionary) -> bool:
	for key in flags:
		if not str(key).begins_with("exploration_"):
			continue
		var site := by_id(str(key).trim_prefix("exploration_"))
		if site.is_empty():
			return false
		if flags[key] and site["kind"] == "cache" and not flags.get("exploration_"+site["requires"],false):
			return false
	return true


static func audit(abilities: Dictionary, jobs: Dictionary) -> Array[String]:
	var errors: Array[String] = []
	var seen: Array[String] = []
	var positions: Array[String] = []
	var human_skills: Array = []
	for job in jobs.values():
		if job["type"] == "human":
			human_skills.append_array(job["abilities"])
	var sites := all_sites()
	if sites.size() != 10:
		errors.append("探索地点は5設備と5補給箱です。")
	for site in sites:
		if not site is Dictionary or not site.has_all(["id","location","cell","kind","name","text"]):
			errors.append("探索地点の定義が不足しています。")
			continue
		if not site["id"] is String or site["id"].is_empty() or site["id"] in seen:
			errors.append("探索地点のIDが空または重複しています。")
			continue
		seen.append(site["id"])
		if site["location"] not in ["waterway","cave","school","records","gate"] or not _cell_valid(site["cell"]) or not ChapterOne.is_walkable(site["location"],Vector2i(site["cell"][0],site["cell"][1])):
			errors.append("探索地点が既存ダンジョンの通行可能な位置にありません。")
			continue
		var position := str(site["location"])+str(site["cell"])
		if position in positions:
			errors.append("探索地点の位置が重複しています。")
		positions.append(position)
		for index in range(StoryCampaign.total_steps()):
			var step := StoryCampaign.step(index)
			if step["location"] == site["location"] and step["cell"] == site["cell"]:
				errors.append("探索地点が本編の目標地点と重なっています。")
		if site["kind"] == "device":
			if not site.get("abilities") is Array or site["abilities"].is_empty() or not site.get("opens") is Array or site["opens"].is_empty():
				errors.append("設備の必要技と開通マスがありません。")
				continue
			for skill in site["abilities"]:
				if not abilities.has(skill) or not skill in human_skills:
					errors.append("設備は人間職でも習得できる既存技を使います。")
			for cell in site["opens"]:
				if not _cell_valid(cell) or ChapterOne.is_walkable(site["location"],Vector2i(cell[0],cell[1])):
					errors.append("開通マスは区画内の閉じた壁に置きます。")
		elif site["kind"] == "cache":
			var prerequisite := by_id(str(site.get("requires","")))
			if prerequisite.get("kind") != "device" or prerequisite.get("location") != site["location"] or not BattleCatalog._is_integer(site.get("potions"),1):
				errors.append("補給箱の解錠条件と報酬が不正です。")
		else:
			errors.append("未知の探索地点の種類です。")
	return errors


static func _cell_valid(cell: Variant) -> bool:
	return cell is Array and cell.size() == 2 and BattleCatalog._is_integer(cell[0],1) and BattleCatalog._is_integer(cell[1],1) and cell[0] < ChapterOne.WIDTH-1 and cell[1] < ChapterOne.HEIGHT-1
