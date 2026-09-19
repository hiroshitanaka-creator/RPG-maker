class_name StoryCampaign
extends RefCounted

static var _data: Dictionary = {}


static func data() -> Dictionary:
	if _data.is_empty():
		var value: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/story_v1.json"))
		if value is Dictionary:
			_data = value
	return _data


static func total_steps() -> int:
	return ChapterOne.STEPS.size() + data().get("route", []).size()


static func step(index: int, task: Dictionary = {}) -> Dictionary:
	if not task.is_empty():
		var branch: Array = data().get("branches", {}).get(task.get("id", ""), [])
		var at := int(task.get("step", -1))
		return _prepared(branch[at]) if at >= 0 and at < branch.size() else {}
	if index < ChapterOne.STEPS.size():
		var entry := ChapterOne.step(index)
		entry["chapter"] = 1
		var event_id: String = data().get("chapter1_events", {}).get(str(index), "")
		if not event_id.is_empty():
			entry["event"] = event_id
		return entry
	var at := index - ChapterOne.STEPS.size()
	var route: Array = data().get("route", [])
	return _prepared(route[at]) if at >= 0 and at < route.size() else {}


static func _prepared(value: Dictionary) -> Dictionary:
	var entry := value.duplicate(true)
	for key in ["cell", "spawn"]:
		if entry.has(key):
			entry[key] = [int(entry[key][0]),int(entry[key][1])]
	entry["chapter"] = int(entry["chapter"])
	return entry


static func event(identifier: String) -> Dictionary:
	return data().get("events", {}).get(identifier, {}).duplicate(true)


static func battle_waves(entry: Dictionary) -> Array:
	if entry.get("kind") != "battle":
		return []
	return entry.get("waves",[entry.get("enemies",[])]).duplicate(true)


static func stage(flags: Dictionary, identifier: String) -> int:
	if flags.get("clue_" + identifier + "_resolved", false):
		return 2
	return 1 if flags.get("clue_" + identifier + "_seeded", false) else 0


static func apply_event(flags: Dictionary, identifier: String) -> Dictionary:
	var definition := event(identifier)
	if definition.is_empty():
		return {}
	if flags.get("story_event_" + identifier, false):
		return flags.duplicate(true)
	for clue_id in definition["requires"]:
		if stage(flags, clue_id) < int(definition["requires"][clue_id]):
			return {}
	var candidate := flags.duplicate(true)
	for clue_id in definition["effects"]:
		var target := int(definition["effects"][clue_id])
		if target == 2 and stage(candidate, clue_id) < 1:
			return {}
		candidate["clue_" + clue_id + "_seeded"] = true
		if target == 2:
			candidate["clue_" + clue_id + "_resolved"] = true
	candidate["story_event_" + identifier] = true
	if definition.get("midgame_slots", false):
		candidate["midgame_slots"] = true
	return candidate


static func validate_flags(flags: Dictionary) -> bool:
	for clue in data().get("clues", []):
		var identifier: String = clue["id"]
		if stage(flags, identifier) == 2 and not flags.get("clue_" + identifier + "_seeded", false):
			return false
	for identifier in data().get("events", {}):
		var definition := event(identifier)
		var completed: bool = flags.get("story_event_" + identifier, false)
		for clue_id in definition["effects"]:
			if int(definition["effects"][clue_id]) == 2 and stage(flags, clue_id) == 2:
				completed = true
		if not completed:
			continue
		for clue_id in definition["requires"]:
			if stage(flags, clue_id) < int(definition["requires"][clue_id]):
				return false
		for clue_id in definition["effects"]:
			if stage(flags, clue_id) < int(definition["effects"][clue_id]):
				return false
	return true


static func journal(flags: Dictionary) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for clue in data().get("clues", []):
		var level := stage(flags, clue["id"])
		if level == 0:
			continue
		var entry: Dictionary = {"id":clue["id"], "title":clue["title"], "stage":level,
			"observation":clue["observation"], "first":clue["first"]}
		if level == 2:
			entry["resolved"] = clue["resolved"]
		result.append(entry)
	return result


static func all_resolved(flags: Dictionary) -> bool:
	if data().get("clues", []).size() != 8:
		return false
	for clue in data()["clues"]:
		if stage(flags, clue["id"]) != 2:
			return false
	return validate_flags(flags)


static func audit() -> Array[String]:
	var problems: Array[String] = []
	var source := data()
	if not source.has_all(["clues", "events", "route", "branches", "chapters"]):
		return ["本編データの必須項目がありません。"]
	if source["clues"].size() != 8 or source["chapters"].size() != 6:
		problems.append("v1案の8回収・6章がそろっていません。")
	var identifiers: Array[String] = []
	var edges: Dictionary = {}
	for clue in source["clues"]:
		var identifier: String = clue.get("id", "")
		if identifier.is_empty() or identifier in identifiers or not clue.has_all(["title","observation","first","resolved","dependencies"]):
			problems.append("回収台帳のID重複または項目不足。")
		identifiers.append(identifier)
		edges[identifier] = clue.get("dependencies", [])
	for identifier in identifiers:
		var seeds := 0
		var payoffs := 0
		for definition in source["events"].values():
			seeds += 1 if int(definition["effects"].get(identifier,0)) == 1 else 0
			payoffs += 1 if int(definition["effects"].get(identifier,0)) == 2 else 0
		if seeds != 1 or payoffs != 1:
			problems.append(identifier + ": 設置と回収が一対ではありません。")
		if _has_cycle(identifier, edges, []):
			problems.append(identifier + ": 未知の依存IDまたは循環依存。")
	var used_events: Array = source["chapter1_events"].values().duplicate()
	for index in range(total_steps()):
		var entry := step(index)
		_check_step(entry, problems)
		if entry.has("event"):
			used_events.append(entry["event"])
	for branch in source["branches"].values():
		for entry in branch:
			_check_step(entry, problems)
			if entry.has("event"):
				used_events.append(entry["event"])
	for identifier in source["events"]:
		var definition := event(identifier)
		if not identifier in used_events:
			problems.append(identifier + ": 配置されていないイベント。")
		for field in ["requires","effects"]:
			for clue_id in definition[field]:
				if not clue_id in identifiers or int(definition[field][clue_id]) not in [1,2]:
					problems.append(identifier + ": 未知の回収IDまたは段階。")
	for chain in [["R01","R02"],["R02","R03"],["R04","R05"],["R05","R06"]]:
		var connected := false
		for definition in source["events"].values():
			if int(definition["effects"].get(chain[0],0)) == 2 and int(definition["effects"].get(chain[1],0)) == 1:
				connected = true
		if not connected:
			problems.append("回収と次の設置が一括ではありません: " + chain[0])
	for clue in source["clues"]:
		if clue["id"] == "R07":
			var original: String = clue["observation"]
			if not original in ChapterOne.STEPS[13]["text"] or not original in event("seed_guard")["summary"] or event("board")["text"][0] != original or event("board")["summary"][0] != original:
				problems.append("R07の観測原文が場面間で変わっています。")
	# 二つの再訪順で、全回収へ至る前提と一括更新が成立するかを調べる。
	for visit_order in [["teaching","reply"],["reply","teaching"]]:
		var flags: Dictionary = {}
		var ordered: Array = []
		for index in range(total_steps()):
			var entry := step(index)
			if entry.has("event"):
				ordered.append(entry["event"])
			if entry["kind"] == "choice":
				for task in visit_order:
					for branch_entry in source["branches"][task]:
						if branch_entry.has("event"):
							ordered.append(branch_entry["event"])
		for identifier in ordered:
			var updated := apply_event(flags, identifier)
			if updated.is_empty():
				problems.append(str(identifier) + ": 前提が到達不能です。")
				break
			flags = updated
		if not all_resolved(flags):
			problems.append("再訪の順序で未回収が残ります。")
	return problems


static func _has_cycle(identifier: String, edges: Dictionary, path: Array) -> bool:
	if not edges.has(identifier) or identifier in path:
		return true
	var next := path.duplicate()
	next.append(identifier)
	for parent in edges[identifier]:
		if _has_cycle(parent, edges, next):
			return true
	return false


static func _check_step(entry: Dictionary, problems: Array[String]) -> void:
	if not entry.has_all(["location","cell","kind","objective"]) or not ChapterOne.is_walkable(entry.get("location", ""), Vector2i(int(entry.get("cell",[0,0])[0]),int(entry.get("cell",[0,0])[1]))):
		problems.append("進行地点が歩ける場所にありません。")
	if entry.has("event") and event(entry["event"]).is_empty():
		problems.append("進行地点のイベントがありません。")
	if entry.get("kind") == "travel" and not ChapterOne.is_walkable(entry["destination"],Vector2i(int(entry["spawn"][0]),int(entry["spawn"][1]))):
		problems.append("移動先の入口へ到達できません。")
