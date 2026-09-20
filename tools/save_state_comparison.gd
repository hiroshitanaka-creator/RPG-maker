extends RefCounted

const ROOT_FIELDS := ["format_version","party","leader_id","inventory","progress_flags","field_battles","return_point","story_battle","content_revision","expedition","world","overworld","story_task","gate_team","_play_session","_trial_id","_saved_value_types"]
const ACTOR_FIELDS := ["id","name","job_id","last_human_job","jp","mastered_jobs","learned_abilities","equipped_abilities","unlocked_jobs","monster_form","erosion","irreversible","hp","max_hp","mp","max_mp"]

static func differences(before: Variant, after: Variant, path: String = "$", output: Array[String] = []) -> Array[String]:
	if typeof(before) != typeof(after):
		output.append(path+": 型不一致")
	elif before is Dictionary:
		for key in before:
			if not after.has(key):output.append(path+"."+str(key)+": キー欠落")
			else:differences(before[key],after[key],path+"."+str(key),output)
		for key in after:
			if not before.has(key):output.append(path+"."+str(key)+": キー増加")
	elif before is Array:
		if before.is_typed() != after.is_typed() or before.get_typed_builtin() != after.get_typed_builtin():output.append(path+": 配列要素型不一致")
		if before.size() != after.size():output.append(path+": 配列長不一致")
		for index in range(mini(before.size(),after.size())):
			differences(before[index],after[index],path+"[%d]" % index,output)
	elif before != after:
		output.append(path+": 値不一致")
	return output

static func unlisted(document: Dictionary) -> Array[String]:
	var result: Array[String] = []
	for key in document:
		if key not in ROOT_FIELDS:result.append("未列挙の保存項目: "+str(key))
	for actor in document.get("party",[]):
		for key in actor:
			if key not in ACTOR_FIELDS:result.append("未列挙の人物項目: "+str(key))
	var schemas := {"world":["location","player_cell","quest_step","section"],"return_point":["location","player_cell","quest_step","section"],"story_task":["id","step"],"story_battle":["step","cleared"],"expedition":["id","stage","wave","origin","solved"],"_play_session":["version","source","source_changed","active_ms","elapsed_ms","idle_ms","pause_ms","chapters","counters","answers","events","completed"]}
	for area in schemas:
		for key in document.get(area,{}):
			if key not in schemas[area]:result.append("未列挙の保存項目: "+area+"."+str(key))
	for key in document.get("overworld",{}):
		if key not in ["active","origin","layer","cell","world_cell","transport","node","room","flags","seen","cleared","choices","visited"]:result.append("未列挙の広域保存項目: "+str(key))
	for key in document.get("expedition",{}).get("origin",{}):
		if key not in schemas["world"]:result.append("未列挙の保存項目: expedition.origin."+str(key))
	var metrics: Dictionary = document.get("_play_session",{})
	for totals in metrics.get("chapters",{}).values():
		for key in totals:
			if key not in ["active_ms","elapsed_ms"]:result.append("未列挙の章別計測項目: "+str(key))
	for answer in metrics.get("answers",[]):
		for key in answer:
			if key not in ["chapter","active_ms","exploration","reward","difficulty","note","self_reported"]:result.append("未列挙の評価項目: "+str(key))
	for event in metrics.get("events",[]):
		for key in event:
			if key not in ["kind","chapter","elapsed_ms","details"]:result.append("未列挙の履歴項目: "+str(key))
	return result

static func paths(value: Variant, prefix: String = "$", found: Dictionary = {}) -> Dictionary:
	found[prefix] = type_string(typeof(value))
	if value is Dictionary:
		for key in value:paths(value[key],prefix+"."+str(key),found)
	elif value is Array:
		for item in value:paths(item,prefix+"[]",found)
	return found
