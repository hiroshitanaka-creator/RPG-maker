class_name IntegratedProgression
extends RefCounted
## 保存形式2の進捗。旧保存の読込みと明示的な更新を混同しない。
static var _rules: Dictionary={}
static func rules() -> Dictionary:
	if _rules.is_empty():_rules=JSON.parse_string(FileAccess.get_file_as_string("res://data/integrated_rules.json"))
	return _rules
static func initial_actor() -> Dictionary:
	return {"exp":0,"level":1,"erosion_fraction":0,"jp_remainders":{},"forgotten":[],"relearn":{},"focus_binding":"","weapons":["practice_blade"]}
static func initial_world() -> Dictionary:
	return {"knowledge":{},"outcomes":{},"claimed":[],"job_notes":[],"armory":["practice_blade","practice_staff","practice_bow"]}
static func modern(state: Dictionary) -> bool:
	return state.get("format_version",1)==2
static func cost(job: Dictionary, modern_rules: bool) -> int:
	return int(job["mastery_cost"] if modern_rules else job.get("legacy_mastery_cost",job["mastery_cost"]))
static func skill_list(job: Dictionary, modern_rules: bool) -> Array:
	return job["abilities"] if modern_rules else job.get("legacy_abilities",job["abilities"])
static func threshold(job: Dictionary, ability: String) -> int:
	var index: int=job["abilities"].find(ability)
	var schedule: Array=rules()["growth"]["thresholds"]
	return int(schedule[mini(index,schedule.size()-1)]) if index>=0 else int(job["mastery_cost"])
static func level_for(exp: int) -> int:
	var level:=1
	var used:=0
	while level<int(rules()["growth"]["level_cap"]):
		var needed:=int(rules()["growth"]["first_exp"])+int(rules()["growth"]["exp_step"])*(level-1)
		if used+needed>exp:break
		used+=needed;level+=1
	return level
static func growth(actor: Dictionary) -> Dictionary:
	var level: int=actor.get("integrated",{}).get("level",1)
	return {"hp":(level-1)*int(rules()["growth"]["hp_per_level"]),"mp":int((level-1)/int(rules()["growth"]["mp_every_levels"]))}
static func erosion_tenths(actor: Dictionary) -> int:
	return int(actor["erosion"])*10+int(actor.get("integrated",{}).get("erosion_fraction",0))
static func set_erosion(actor: Dictionary, value: int) -> void:
	value=clampi(value,0,1000)
	actor["erosion"]=int(value/10)
	actor["integrated"]["erosion_fraction"]=value%10
	if value>=900:actor["irreversible"]=true
static func weapon(id: String) -> Dictionary:
	for item in rules()["weapons"]:
		if item["id"]==id:return item
	return {}
static func ability_cost(ability: Dictionary,affinities: Array,form_add: int=0) -> int:
	var amount: int=int(ability["cost"])
	if amount==0:return 0
	if amount>=4:
		for tag in ability.get("tags",[]):
			if tag in affinities:amount-=1;break
	return amount+form_add
static func weapon_bonus(actor: Dictionary) -> int:
	var held: Array=actor.get("integrated",{}).get("weapons",[])
	return 0 if held.is_empty() else int(weapon(held[0]).get("attack",0))
static func form_rule(actor: Dictionary) -> Dictionary:
	return rules()["forms"].get(actor.get("monster_form",""),{}) if actor.has("integrated") else {}
static func reward(kind: String) -> Dictionary:
	return rules()["growth"]["rewards"].get(kind,rules()["growth"]["rewards"]["normal"])
static func apply_reward(actor: Dictionary,job: Dictionary,award: Dictionary,half: bool) -> Dictionary:
	var own: Dictionary=actor["integrated"]
	var previous_level: int=own["level"]
	own["exp"]+=int(award["exp"])
	own["level"]=level_for(own["exp"])
	var earned: int=int(award["jp"])
	if half:
		var units:=earned+int(own["jp_remainders"].get(job["id"],0))
		earned=int(units/2)
		own["jp_remainders"][job["id"]]=units%2
	actor["jp"][job["id"]]=int(actor["jp"].get(job["id"],0))+earned
	var acquired: Array[String]=[]
	var possible: Array=job["abilities"].duplicate()
	if job["type"]=="monster":possible.append_array(job["monster_form"]["abilities"])
	for id in possible:
		if id in own["forgotten"]:
			own["relearn"][id]=int(own["relearn"].get(id,0))+earned
			if own["relearn"][id]>=threshold(job,id):
				own["forgotten"].erase(id);own["relearn"].erase(id)
				if id not in actor["learned_abilities"]:actor["learned_abilities"].append(id);acquired.append(id)
		elif id in job["abilities"] and int(actor["jp"][job["id"]])>=threshold(job,id) and id not in actor["learned_abilities"]:
			actor["learned_abilities"].append(id);acquired.append(id)
	return {"exp":int(award["exp"]),"jp":earned,"level_before":previous_level,"level_after":own["level"],"acquired":acquired}
static func forget(actor: Dictionary, removed: Array) -> void:
	var own: Dictionary=actor["integrated"]
	for id in removed:
		if id not in own["forgotten"]:own["forgotten"].append(id)
		own["relearn"][id]=0
	if own["focus_binding"] in removed:own["focus_binding"]=""
static func valid_actor(actor: Dictionary,jobs: Dictionary,abilities: Dictionary,armory: Array) -> bool:
	var own: Variant=actor.get("integrated")
	if not own is Dictionary or not own.has_all(["exp","level","erosion_fraction","jp_remainders","forgotten","relearn","focus_binding","weapons"]):return false
	for key in ["exp","level","erosion_fraction"]:
		if not own[key] is int or own[key]<0:return false
	if own["level"]!=level_for(own["exp"]) or own["erosion_fraction"]>9 or (actor["erosion"]==100 and own["erosion_fraction"]!=0):return false
	if not own["jp_remainders"] is Dictionary or not own["relearn"] is Dictionary or not own["forgotten"] is Array or not own["weapons"] is Array or not own["focus_binding"] is String:return false
	for id in own["jp_remainders"]:
		if not jobs.has(id) or not own["jp_remainders"][id] is int or own["jp_remainders"][id] not in [0,1]:return false
	var seen: Array=[]
	for id in own["forgotten"]:
		if not abilities.has(id) or id in seen or id in actor["learned_abilities"] or not own["relearn"].has(id):return false
		seen.append(id)
	for id in own["relearn"]:
		if id not in own["forgotten"] or not own["relearn"][id] is int or own["relearn"][id]<0:return false
	if not own["focus_binding"].is_empty() and (own["focus_binding"] not in actor["equipped_abilities"] or "focus_vow" not in actor["equipped_abilities"] or not abilities.has(own["focus_binding"]) or abilities[own["focus_binding"]]["kind"] not in ["physical","magic"]):return false
	if own["weapons"].is_empty() or own["weapons"].size()>2 or (own["weapons"].size()==2 and "twin_grip" not in actor["equipped_abilities"]):return false
	for id in own["weapons"]:
		if not id is String or id not in armory or weapon(id).is_empty():return false
	return true
static func valid_world(value: Variant) -> bool:
	if not value is Dictionary or not value.has_all(["knowledge","outcomes","claimed","armory","job_notes"]):return false
	if not value["job_notes"] is Array:return false
	var notes: Array=[]
	for note in value["job_notes"]:
		if note not in ["hunter/rumor","hunter/bestiary","sage/rumor","sage/bestiary","swordsman/rumor","swordsman/bestiary","spirit/rumor","spirit/bestiary"] or note in notes:return false
		notes.append(note)
	if not value["knowledge"] is Dictionary or not value["outcomes"] is Dictionary or not value["claimed"] is Array or not value["armory"] is Array:return false
	var ids: Array=[]
	for rule in rules()["enemy_rules"]:ids.append(rule["id"])
	for id in value["knowledge"]:
		if id not in ids:return false
		var entry: Variant=value["knowledge"][id]
		if not entry is Dictionary or not entry.get("facts") is Array or not entry.get("confirmed") is bool:return false
		var seen: Array=[]
		for index in entry["facts"]:
			if not index is int or index not in [0,1] or index in seen:return false
			seen.append(index)
	for id in value["armory"]:
		if not id is String or weapon(id).is_empty():return false
	var seen_weapons: Array=[]
	for id in value["armory"]:
		if id in seen_weapons:return false
		seen_weapons.append(id)
	var methods: Array=["electric","observe","field","seal_break","conducted_hit","device","field_break","seal","disarm","focus","conduct","amplify","overdrive","deflect_physical","deflect_magic","cover","reflect_field","riposte","recycle","restore_mp"]
	for id in value["outcomes"]:
		if not id is String:return false
		var assignment:=IntegratedCampaign.assignment(id)
		var outcome: Variant=value["outcomes"][id]
		if assignment.is_empty() or not outcome is Dictionary or outcome.get("rule")!=assignment["rule"] or not outcome.get("methods") is Array:return false
		var seen: Array=[]
		for method in outcome["methods"]:
			if method not in methods or method in seen:return false
			seen.append(method)
	var claims: Array=[]
	for id in value["claimed"]:
		if not id is String or id in claims or not value["outcomes"].has(id) or "field_break" not in value["outcomes"][id]["methods"]:return false
		claims.append(id)
	return true
static func upgrade(old: Dictionary,jobs: Dictionary) -> Dictionary:
	var result:=old.duplicate(true)
	result["format_version"]=2
	result["integrated"]=initial_world()
	for actor in result["party"]:
		actor["integrated"]=initial_actor()
		var formerly_possible: Array=[]
		for job_id in actor["jp"]:
			var job: Dictionary=jobs[job_id]
			var old_jp: int=actor["jp"][job_id]
			var old_cost:=cost(job,false)
			actor["jp"][job_id]=floori(float(old_jp)*float(cost(job,true))/float(old_cost))
			var former: Array=skill_list(job,false)
			if old_jp>=ceili(old_cost/2.0):formerly_possible.append(former[0])
			if job_id in actor["mastered_jobs"]:
				actor["jp"][job_id]=maxi(cost(job,true),actor["jp"][job_id])
				formerly_possible.append_array(former)
				if job["type"]=="monster":formerly_possible.append_array(job["monster_form"]["abilities"])
		var human_skills: Array=[]
		for job in jobs.values():
			if job["type"]=="human":human_skills.append_array(job["abilities"])
		var erased: Array=[]
		for id in formerly_possible:
			if id not in actor["learned_abilities"] and id not in human_skills and id not in erased:erased.append(id)
		forget(actor,erased)
	return result
