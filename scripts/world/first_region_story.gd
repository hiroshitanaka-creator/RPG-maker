class_name FirstRegionStory
extends RefCounted
## 第1地方の短い導入。完了済みだけを保存し、会話中の配置・ページは保存状態から分離する。
const FLAGS := ["gado_workshop_seen", "gado_encounter_seen", "gado_promise_seen"]
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = JSON.parse_string(FileAccess.get_file_as_string("res://data/first_region_gado_scenes.json"))
	return _data

static func scene(identifier: String) -> Dictionary:
	for entry in data()["scenes"]:
		if entry["id"] == identifier:return entry.duplicate(true)
	return {}

static func complete(saved: Dictionary) -> bool:
	return saved.get("first_region") is Dictionary and FLAGS.all(func(flag:String)->bool:return saved.get("progress_flags",{}).get(flag,false))

static func queue_for(saved: Dictionary, context: String) -> Array[String]:
	var result: Array[String] = []
	var flags: Dictionary = saved["progress_flags"]
	if not flags.get(FLAGS[0],false):result.append("workshop")
	if context == "village":return result
	var encountered: bool = flags.get(FLAGS[1],false)
	var after: bool = "first_boss" in saved["overworld"]["cleared"]
	if not encountered:result.append("encounter_after" if after else "encounter")
	if after and not flags.get(FLAGS[2],false):result.append("promise" if encountered else "promise_after")
	return result

static func dialogue(identifier: String, catchup: bool) -> Dictionary:
	var entry := scene(identifier)
	var lines: Array = []
	var speakers: Array = []
	var prompts: Array = []
	for line in entry["lines"]:
		lines.append(line["text"])
		speakers.append(line["speaker"])
		prompts.append({"leave_tool":"道具をそっと置く","tend_wound":"許された傷を手当てする"}.get(line["action"],""))
	return {"kind":"dialogue","story_scene":identifier,"scene_title":("追加された導入の場面 / " if catchup else "")+entry["title"],"text":lines,"speakers":speakers,"line_prompts":prompts}

static func needs_return(saved: Dictionary) -> bool:
	return "first_boss" in saved["overworld"]["cleared"] and not complete(saved)

static func missing_art() -> Array[String]:
	var result: Array[String] = []
	for slot in data()["art"]:
		if data()["art"][slot] == null:result.append(slot)
	return result

static func presentation(identifier: String, title: String, page: int) -> Dictionary:
	var entry := scene(identifier)
	var actors: Array = []
	var workshop: bool = identifier == "workshop"
	for index in entry["party"].size():
		actors.append({"npc":entry["party"][index],"cell":[5+index,4+index%2] if workshop else [[28,15],[29,15],[27,15]][index],"facing":2 if workshop else 3})
	var repairing: bool = identifier=="workshop" or identifier.begins_with("encounter")
	var tool_placed: bool = entry["lines"].slice(0,page).any(func(line:Dictionary)->bool:return line["action"]=="leave_tool")
	var repaired: bool = identifier.begins_with("promise") or tool_placed
	var slot: String = entry["form"]+"_standing_front"
	return {"title":title,"workshop":workshop,"camera":[0,0] if workshop else [22,11],"actors":actors,"npc_cell":[8,4] if workshop else [30,14],"npc_texture":data()["art"][slot],"tool_texture":data()["art"]["tool_repaired" if repaired else "tool_broken"],"tool_cell":[7,4] if workshop else [29,13],"repair_sound":data()["art"]["repair_sound"] if repairing else null}
