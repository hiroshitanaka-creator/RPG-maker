class_name GameSession
extends RefCounted

const MONSTER_BATTLE_EROSION := 3
const MONSTER_SKILL_EROSION := 1

var catalog: BattleCatalog
var jobs: Dictionary = {}
var abilities: Dictionary = {}
var enemy_definitions: Dictionary = {}
var errors: Array[String] = []
var play_metrics := PlaySessionMetrics.new()
var _archive: PlaythroughArchive
var job_progression: Dictionary = {}

var _state: Dictionary = {}
var _battle: BattleState
var _battle_enemy_ids: Array[String] = []
var _claimed: bool = true
var _field_battle: bool = false
var _story_wave_step: int = -1
var _story_wave_number: int = 0
var _expedition_battle_stage: int = -1
var _world_battle_id: String = ""


func _init() -> void:
	catalog = BattleCatalog.new()
	jobs = catalog.jobs
	abilities = catalog.abilities
	enemy_definitions = catalog.enemies
	job_progression = JSON.parse_string(FileAccess.get_file_as_string("res://data/job_progression_v1.json"))
	errors.assign(catalog.errors)
	errors.append_array(StoryCampaign.audit())
	errors.append_array(ExplorationSites.audit(abilities,jobs))
	errors.append_array(CampaignContent.audit(enemy_definitions))
	if LongCampaign.enabled():errors.append_array(LongCampaign.audit(abilities,enemy_definitions))
	if enemy_definitions.size() != 30:
		errors.append("v1の敵データは30種類です。")
	for index in range(StoryCampaign.total_steps()):
		var step := StoryCampaign.step(index)
		for wave in StoryCampaign.battle_waves(step):
			if not wave is Array or wave.is_empty() or wave.size() > 3:
				errors.append("本編の敵編成は1〜3体です。")
				continue
			for identifier in wave:
				if not enemy_definitions.has(identifier):
					errors.append("本編の敵編成に未知の敵があります。")
	var keeper_learned: Array[String] = []
	keeper_learned.assign(StoryCampaign.data().get("keeper_learned",[]))
	var keeper_equipped: Array[String] = []
	keeper_equipped.assign(StoryCampaign.data().get("keeper_loadout",[]))
	for identifier in keeper_learned:
		if not abilities.has(identifier):
			errors.append("番人の習得記録に未知の技があります。")
	if not Loadout.validate(keeper_learned,keeper_equipped,Loadout.capacity(false,true)).is_empty():
		errors.append("番人の装着記録が当時の三枠と一致しません。")
	var humans := 0
	var monsters := 0
	for definition in jobs.values():
		if not definition.has_all(["id", "name", "type", "stat_growth", "abilities", "mastery_cost"]):
			errors.append("職業の必須項目が不足しています。")
			continue
		if definition["type"] == "human":
			humans += 1
		elif definition["type"] == "monster":
			monsters += 1
	if humans != 12 or monsters != 8:
		errors.append("v1の職業数は人間12・モンスター8です。")


func new_game(party_size: int = 4) -> bool:
	if not errors.is_empty() or party_size < 3 or party_size > 4:
		return false
	if _archive != null and not _state.is_empty():
		_archive.lifetime.record_event("trial_closed",{"reason":"new_game"})
		close_recording()
	var starts := ["warrior", "martial_artist", "priest", "mage"]
	var cast: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/cast_v1.json"))
	var party: Array = []
	for i in range(party_size):
		var job: Dictionary = jobs[starts[i]]
		party.append({
			"id": "pc_%02d" % (i + 1), "name": cast["actors"]["pc_%02d" % (i+1)]["name"],
			"job_id": starts[i], "last_human_job": starts[i], "jp": {},
			"mastered_jobs": [], "learned_abilities": [], "equipped_abilities": [],
			"unlocked_jobs": [],
			"monster_form": "", "erosion": 0, "irreversible": false,
			"hp": int(job["stats"]["hp"]), "max_hp": int(job["stats"]["hp"]),
			"mp": int(job["stats"]["mp"]), "max_mp": int(job["stats"]["mp"])
		})
	play_metrics = PlaySessionMetrics.new()
	_state = {"format_version": 1, "party": party, "leader_id":"pc_01", "inventory": {"potion": 3},
		"progress_flags": {"chapter1_cleared": false, "midgame_slots": false},
		"field_battles": 0, "return_point": {}, "story_battle": {}, "content_revision":1, "expedition":{},
		"world": {"location": "town", "player_cell": [2, 4], "quest_step": 0}}
	if LongCampaign.enabled():_state["progress_flags"]["long_campaign_enrolled"]=true
	_battle = null
	_world_battle_id = ""
	_claimed = true
	_field_battle = false
	_story_wave_step = -1
	_expedition_battle_stage = -1
	if _archive != null:
		_archive.start(play_metrics)
		flush_recording()
	return true


func export_state() -> Dictionary:
	return _state.duplicate(true)


func _member(actor_id: String) -> Dictionary:
	for actor in _state.get("party", []):
		if actor["id"] == actor_id:
			return actor
	return {}


func import_state(value: Dictionary) -> bool:
	if _battle != null:
		return false
	var normalized: Variant = _normalize_numbers(value)
	if not _valid_state(normalized):
		return false
	_state = normalized.duplicate(true)
	_world_battle_id = ""
	_battle = null
	_claimed = true
	_field_battle = false
	_story_wave_step = -1
	_expedition_battle_stage = -1
	return true


func _valid_state(value: Dictionary) -> bool:
	if value.get("format_version") != 1 or not value.get("party") is Array:
		return false
	var party: Array = value["party"]
	if party.size() < 3 or party.size() > 4 or not value.get("inventory") is Dictionary or not value.get("progress_flags") is Dictionary or not value.get("world") is Dictionary:
		return false
	if not _valid_world(value["world"],value["progress_flags"]):
		return false
	if value.has("overworld") and not WorldExpedition.valid(value["overworld"]):
		return false
	if value.has("overworld") and value["overworld"]["active"] and value["overworld"]["origin"] != value["world"]["location"]:
		return false
	for identifier in value["progress_flags"]:
		if not identifier is String or not value["progress_flags"][identifier] is bool:
			return false
	if not StoryCampaign.validate_flags(value["progress_flags"]):
		return false
	if not ExplorationSites.valid_flags(value["progress_flags"]):
		return false
	if not CampaignContent.valid_state(value):
		return false
	if value["progress_flags"].get("story_v1_cleared", false) and not StoryCampaign.all_resolved(value["progress_flags"]):
		return false
	if value["progress_flags"].get("story_v1_cleared",false) and value["progress_flags"].get("long_campaign_started",false) and not LongCampaign.all_cleared(value["progress_flags"]):return false
	var task: Variant = value.get("story_task", {})
	if not task is Dictionary:
		return false
	if not task.is_empty():
		if not task.get("id") is String or not task.get("step") is int or StoryCampaign.step(value["world"]["quest_step"]).get("kind") != "choice" or StoryCampaign.step(value["world"]["quest_step"], task).is_empty():
			return false
	if not value.get("field_battles", 0) is int or int(value.get("field_battles", 0)) < 0:
		return false
	var return_point: Variant = value.get("return_point", {})
	if not return_point is Dictionary:
		return false
	if not return_point.is_empty():
		if not _valid_world(return_point,value["progress_flags"]) or return_point["location"] == "town" or value["world"]["location"] != "town" or return_point["quest_step"] != value["world"]["quest_step"]:
			return false
	var active_world: Dictionary = value["world"] if return_point.is_empty() else return_point
	var active_step := StoryCampaign.step(active_world["quest_step"],task)
	if not value.get("expedition",{}).is_empty():
		active_step = CampaignContent.step(value["expedition"],value["progress_flags"])
	if not active_step.is_empty() and active_world["location"] != active_step["location"]:
		return false
	var progress: Variant = value.get("story_battle",{})
	if not progress is Dictionary:
		return false
	if not progress.is_empty():
		if not value.get("expedition",{}).is_empty():
			return false
		if not progress.get("step") is int or not progress.get("cleared") is int or progress["step"] != active_world["quest_step"] or active_step.get("kind") != "battle":
			return false
		if progress["cleared"] < 0 or progress["cleared"] > StoryCampaign.battle_waves(active_step).size():
			return false
	if not value["inventory"].get("potion") is int or value["inventory"]["potion"] < 0:
		return false
	var ids: Array[String] = []
	for item in party:
		if not item is Dictionary:
			return false
		var actor: Dictionary = item
		var required := ["id", "name", "job_id", "last_human_job", "jp", "mastered_jobs", "learned_abilities", "equipped_abilities", "monster_form", "erosion", "irreversible", "hp", "max_hp", "mp", "max_mp"]
		if not actor.has_all(required):
			return false
		if not actor["id"] is String or actor["id"].is_empty() or actor["id"] in ids or not actor["name"] is String:
			return false
		ids.append(actor["id"])
		if not jobs.has(actor["job_id"]) or not jobs.has(actor["last_human_job"]) or jobs[actor["last_human_job"]]["type"] != "human":
			return false
		if not actor["jp"] is Dictionary:
			return false
		if not actor.get("unlocked_jobs",[]) is Array:
			return false
		var unlocked: Array = []
		for identifier in actor.get("unlocked_jobs",[]):
			if not identifier is String or not job_progression["advanced"].has(identifier) or identifier in unlocked:
				return false
			unlocked.append(identifier)
		for job_id in actor["jp"]:
			if not jobs.has(job_id) or not actor["jp"][job_id] is int or actor["jp"][job_id] < 0:
				return false
		for field in ["mastered_jobs", "learned_abilities", "equipped_abilities"]:
			if not actor[field] is Array:
				return false
			var seen: Array = []
			for identifier in actor[field]:
				if not identifier is String or identifier in seen:
					return false
				seen.append(identifier)
				if field == "mastered_jobs":
					if not jobs.has(identifier) or int(actor["jp"].get(identifier, 0)) < int(jobs[identifier]["mastery_cost"]):
						return false
				elif not abilities.has(identifier):
					return false
		if not actor["erosion"] is int or actor["erosion"] < 0 or actor["erosion"] > 100 or not actor["irreversible"] is bool:
			return false
		if actor["erosion"] >= 90 and not actor["irreversible"]:
			return false
		var form: Variant = actor["monster_form"]
		if not form is String or (not form.is_empty() and (not jobs.has(form) or jobs[form]["type"] != "monster" or not form in actor["mastered_jobs"])):
			return false
		if actor["irreversible"] and jobs[actor["job_id"]]["type"] == "human":
			return false
		for field in ["hp", "max_hp", "mp", "max_mp"]:
			if not actor[field] is int or actor[field] < 0:
				return false
		var computed := _compute_stats(actor, true)
		if actor["max_hp"] != computed["hp"] or actor["max_mp"] != computed["mp"] or actor["hp"] > actor["max_hp"] or actor["mp"] > actor["max_mp"]:
			return false
		var available: Array[String] = _available(actor)
		var equipped_ids: Array[String] = []
		equipped_ids.assign(actor["equipped_abilities"])
		var slots := Loadout.capacity(bool(value["progress_flags"].get("midgame_slots", false)), not form.is_empty())
		if not Loadout.validate(available, equipped_ids, slots).is_empty():
			return false
	if value.has("leader_id") and (not value["leader_id"] is String or not value["leader_id"] in ids):
		return false
	var team: Variant = value.get("gate_team", [])
	if not team is Array:
		return false
	if not team.is_empty() or StoryCampaign.stage(value["progress_flags"],"R03") == 2:
		if team.size() != 3:
			return false
		var assigned: Array = []
		for identifier in team:
			if not identifier is String or not identifier in ids or identifier in assigned:
				return false
			assigned.append(identifier)
	return true


static func _valid_world(world: Dictionary, flags: Dictionary = {}) -> bool:
	if not world.has_all(["location", "player_cell", "quest_step"]):
		return false
	if not world["location"] is String or not ChapterOne.TITLES.has(world["location"]):
		return false
	if not world["quest_step"] is int or world["quest_step"] < 0 or world["quest_step"] > StoryCampaign.total_steps():
		return false
	var cell: Variant = world["player_cell"]
	if not str(world.get("section","")).is_empty():
		var section := CampaignContent.section(str(world["section"]))
		return section.get("location") == world["location"] and cell is Array and cell.size() == 2 and cell[0] is int and cell[1] is int and CampaignContent.is_walkable(world["section"],Vector2i(cell[0],cell[1]),flags)
	return cell is Array and cell.size() == 2 and cell[0] is int and cell[1] is int and ExplorationSites.is_walkable(world["location"], Vector2i(cell[0],cell[1]),flags)


static func _normalize_numbers(value: Variant) -> Variant:
	if value is Dictionary:
		var result: Dictionary = {}
		for key in value:
			result[key] = _normalize_numbers(value[key])
		return result
	if value is Array:
		var result: Array = []
		for item in value:
			result.append(_normalize_numbers(item))
		return result
	if value is float and value == floor(value):
		return int(value)
	return value


func change_job(actor_id: String, job_id: String) -> bool:
	# 状態適用の基礎API。通常の職業選択はchoose_jobで解放条件も確認する。
	if _battle != null or not jobs.has(job_id):
		return false
	var actor := _member(actor_id)
	if actor.is_empty() or (actor["irreversible"] and jobs[job_id]["type"] == "human"):
		return false
	var previous_job: String = actor["job_id"]
	actor["job_id"] = job_id
	if jobs[job_id]["type"] == "human":
		actor["last_human_job"] = job_id
	elif job_id in actor["mastered_jobs"]:
		actor["monster_form"] = job_id
		_learn_form(actor, job_id)
	_refresh_caps(actor)
	_reconcile_slots(actor)
	play_metrics.record_event("job_changed",{"actor":actor_id,"from":previous_job,"to":job_id})
	return true


func job_unlocked(actor_id: String, job_id: String) -> bool:
	var actor := _member(actor_id)
	if actor.is_empty() or not jobs.has(job_id):
		return false
	# 過去の保存で既に使った職は取り上げない。
	if actor["job_id"] == job_id or int(actor["jp"].get(job_id,0)) > 0 or job_id in actor["mastered_jobs"] or job_id in actor.get("unlocked_jobs",[]):
		return true
	var rule: Dictionary = job_progression["advanced"].get(job_id,{})
	if rule.is_empty():
		return true
	for required in rule["masters"]:
		if required not in actor["mastered_jobs"]:
			return false
	return int(actor["erosion"]) >= int(rule["erosion"])


func choose_job(actor_id: String, job_id: String) -> bool:
	if not job_unlocked(actor_id,job_id) or not change_job(actor_id,job_id):
		return false
	_grant_job_unlocks(_member(actor_id))
	return true


func _grant_job_unlocks(actor: Dictionary) -> void:
	for identifier in job_progression["advanced"]:
		var rule: Dictionary = job_progression["advanced"][identifier]
		var met: bool = int(actor["erosion"]) >= int(rule["erosion"])
		for required in rule["masters"]:
			met = met and required in actor["mastered_jobs"]
		if met and identifier not in actor.get("unlocked_jobs",[]):
			if not actor.has("unlocked_jobs"):
				actor["unlocked_jobs"] = []
			actor["unlocked_jobs"].append(identifier)
			play_metrics.record_event("job_unlocked",{"actor":actor["id"],"job":identifier})


func slot_limit(actor_id: String) -> int:
	var actor := _member(actor_id)
	if actor.is_empty():
		return 0
	return Loadout.capacity(bool(_state["progress_flags"].get("midgame_slots", false)), not str(actor["monster_form"]).is_empty())


func _form_abilities() -> Array[String]:
	var result: Array[String] = []
	for job in jobs.values():
		if job["type"] == "monster":
			for identifier in job["monster_form"]["abilities"]:
				result.append(identifier)
	return result


func _available(actor: Dictionary) -> Array[String]:
	var result: Array[String] = []
	var only_in_form := _form_abilities()
	var current_form: String = actor["monster_form"]
	for identifier in actor["learned_abilities"]:
		if identifier in only_in_form:
			if current_form.is_empty() or not identifier in jobs[current_form]["monster_form"]["abilities"]:
				continue
		result.append(identifier)
	return result


func available_abilities(actor_id: String) -> Array[String]:
	var actor := _member(actor_id)
	return [] if actor.is_empty() else _available(actor)


func equip_ability(actor_id: String, ability_id: String) -> bool:
	if _battle != null:
		return false
	var actor := _member(actor_id)
	if actor.is_empty():
		return false
	var candidate: Array[String] = []
	candidate.assign(actor["equipped_abilities"])
	candidate.append(ability_id)
	if not Loadout.validate(_available(actor), candidate, slot_limit(actor_id)).is_empty():
		return false
	actor["equipped_abilities"] = candidate
	play_metrics.record_event("ability_equipped",{"actor":actor_id,"ability":ability_id})
	return true


func unequip_ability(actor_id: String, ability_id: String) -> bool:
	if _battle != null:
		return false
	var actor := _member(actor_id)
	if actor.is_empty() or not ability_id in actor["equipped_abilities"]:
		return false
	actor["equipped_abilities"].erase(ability_id)
	play_metrics.record_event("ability_unequipped",{"actor":actor_id,"ability":ability_id})
	return true


func _reconcile_slots(actor: Dictionary) -> void:
	var valid := _available(actor)
	var kept: Array[String] = []
	for identifier in actor["equipped_abilities"]:
		if identifier in valid and kept.size() < slot_limit(actor["id"]):
			kept.append(identifier)
	actor["equipped_abilities"] = kept


func _compute_stats(actor: Dictionary, include_form: bool) -> Dictionary:
	var result: Dictionary = jobs[actor["job_id"]]["stats"].duplicate(true)
	for identifier in actor["mastered_jobs"]:
		for stat in jobs[identifier]["stat_growth"]:
			result[stat] = int(result.get(stat, 0)) + int(jobs[identifier]["stat_growth"][stat])
	if include_form and not str(actor["monster_form"]).is_empty():
		var modifiers: Dictionary = jobs[actor["monster_form"]]["monster_form"]["stat_modifiers"]
		for stat in modifiers:
			result[stat] = int(result.get(stat, 0)) + int(modifiers[stat])
	for stat in result:
		result[stat] = int(result[stat])
	return result


func effective_stats(actor_id: String) -> Dictionary:
	var actor := _member(actor_id)
	return {} if actor.is_empty() else _compute_stats(actor, true)


func mastery_trait(job_id: String) -> Dictionary:
	if not jobs.has(job_id):
		return {}
	var growth: Dictionary = jobs[job_id]["stat_growth"]
	var names := {"hp":"HP","mp":"MP","attack":"攻撃","defense":"防御","magic":"魔力","resistance":"魔防","speed":"速さ"}
	var effects: Array[String] = []
	for stat in growth:
		effects.append(str(names[stat])+" +"+str(int(growth[stat])))
	return {"id":"mastery_"+job_id,"name":str(jobs[job_id]["name"])+"の鍛錬","description":" / ".join(effects),"stat_growth":growth.duplicate(true)}


func mastery_traits(actor_id: String) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for identifier in _member(actor_id).get("mastered_jobs",[]):
		result.append(mastery_trait(identifier))
	return result


func base_effective_stats(actor_id: String) -> Dictionary:
	var actor := _member(actor_id)
	return {} if actor.is_empty() else _compute_stats(actor, false)


func preview_job(actor_id: String, job_id: String) -> Dictionary:
	var actor := _member(actor_id)
	if actor.is_empty() or not jobs.has(job_id):
		return {}
	var candidate := actor.duplicate(true)
	candidate["job_id"] = job_id
	if jobs[job_id]["type"] == "monster" and job_id in candidate["mastered_jobs"]:
		candidate["monster_form"] = job_id
	return {"allowed": _battle == null and not (actor["irreversible"] and jobs[job_id]["type"] == "human"),
		"stats": _compute_stats(candidate, true), "monster_form": candidate["monster_form"],
		"jp": int(actor["jp"].get(job_id,0)), "mastery_cost": int(jobs[job_id]["mastery_cost"])}


func describe_ability(ability_id: String) -> String:
	if not abilities.has(ability_id):
		return ""
	var ability: Dictionary = abilities[ability_id]
	var targets := {"enemy":"敵1体", "ally":"味方1人", "self":"自分", "fallen_ally":"戦闘不能の味方1人"}
	var detail := ""
	match ability["kind"]:
		"physical": detail = "物理攻撃%d%% × %d回" % [ability["power"], ability["hits"]]
		"magic": detail = "%s魔法・威力%d" % [{"none":"無属性", "fire":"炎属性", "ice":"氷属性"}[ability["element"]], ability["power"]]
		"heal": detail = "HP回復・回復量は%d＋魔力×2" % ability["power"]
		"revive": detail = "最大HPの%d%%で蘇生" % ability["power"]
		"guard": detail = "このターンの被ダメージを%d%%に抑える" % ability["power"]
		"steal": detail = "相手1体につき1回、回復薬を盗む"
	if int(ability["priority"]) > 0:
		detail += "・優先行動"
	if not monster_skill_origin(ability_id).is_empty():
		detail += "・実使用で侵蝕+%d" % MONSTER_SKILL_EROSION
	return "%s / %dMP / %s\n%s" % [ability["name"], ability["cost"], targets[ability["target"]], detail]


func monster_skill_origin(ability_id: String) -> String:
	for job in jobs.values():
		if job["type"] == "human" and ability_id in job["abilities"]:
			return ""
	for job in jobs.values():
		if job["type"] == "monster" and (ability_id in job["abilities"] or ability_id in job["monster_form"]["abilities"]):
			return job["id"]
	return ""


static func erosion_stage(value: int) -> String:
	if value >= 90:
		return "不可逆"
	if value >= 60:
		return "変異"
	if value >= 30:
		return "兆候"
	return "平常"


func current_erosion(actor_id: String) -> int:
	var actor := _member(actor_id)
	if actor.is_empty():
		return 0
	var value := int(actor["erosion"])
	if _battle != null:
		for ability_id in _battle.successful_abilities(actor_id):
			if not monster_skill_origin(ability_id).is_empty():
				value += MONSTER_SKILL_EROSION
	return mini(100, value)


func erosion_preview(include_queued: bool = false) -> Array[Dictionary]:
	var results: Array[Dictionary] = []
	for actor in _state.get("party", []):
		var before := int(actor["erosion"])
		var battle_cost := MONSTER_BATTLE_EROSION if jobs[actor["job_id"]]["type"] == "monster" else 0
		var after := mini(100, before + battle_cost)
		var skill_count := 0
		var forced_job := ""
		var uses: Array[String] = []
		if _battle != null:
			uses = _battle.successful_abilities(actor["id"])
			if include_queued and _battle.queued.has(actor["id"]):
				var action: BattleAction = _battle.queued[actor["id"]]
				if action.kind == BattleAction.Kind.ABILITY:
					uses.append(action.ability_id)
		for ability_id in uses:
			var origin := monster_skill_origin(ability_id)
			if origin.is_empty():
				continue
			var previous := after
			after = mini(100, after + MONSTER_SKILL_EROSION)
			skill_count += 1
			if previous < 90 and after >= 90 and jobs[actor["job_id"]]["type"] == "human":
				forced_job = origin
		results.append({"actor":actor["id"], "name":actor["name"], "before":before, "after":after,
			"battle_cost":battle_cost, "skill_uses":skill_count, "forced_job":forced_job,
			"crosses_irreversible": before < 90 and after >= 90})
	return results


func _refresh_caps(actor: Dictionary) -> void:
	var current := _compute_stats(actor, true)
	for pair in [["hp", "max_hp"], ["mp", "max_mp"]]:
		var field: String = pair[0]
		var maximum: String = pair[1]
		var previous_max: int = int(actor[maximum])
		var next_max: int = int(current[field])
		if previous_max <= 0:
			actor[field] = next_max
		elif actor[field] == previous_max:
			actor[field] = next_max
		else:
			var previous_value := int(actor[field])
			actor[field] = floori(float(previous_value) / float(previous_max) * float(next_max))
			if field == "hp" and previous_value > 0:
				actor[field] = maxi(1, int(actor[field]))
		actor[maximum] = next_max


func _learn_form(actor: Dictionary, job_id: String) -> void:
	for identifier in jobs[job_id]["monster_form"]["abilities"]:
		if not identifier in actor["learned_abilities"]:
			actor["learned_abilities"].append(identifier)


func release_monster_form(actor_id: String, event: String) -> bool:
	if _battle != null:
		return false
	var actor := _member(actor_id)
	if actor.is_empty() or (str(actor["monster_form"]).is_empty() and int(actor["erosion"]) == 0):
		return false
	var release: Dictionary = {"event":"purification_shrine","max_erosion":89,"erosion_reduction":30,"forget_monster_abilities":true} if str(actor["monster_form"]).is_empty() else jobs[actor["monster_form"]]["monster_form"]["release"]
	if event != release["event"] or actor["irreversible"] or int(actor["erosion"]) > int(release["max_erosion"]):
		return false
	_grant_job_unlocks(actor)
	var monster_skills: Array[String] = _form_abilities()
	var human_skills: Array[String] = []
	for job in jobs.values():
		for identifier in job["abilities"]:
			if job["type"] == "human":
				human_skills.append(identifier)
			else:
				monster_skills.append(identifier)
	if release["forget_monster_abilities"]:
		var kept: Array[String] = []
		for identifier in actor["learned_abilities"]:
			if not identifier in monster_skills or identifier in human_skills:
				kept.append(identifier)
		actor["learned_abilities"] = kept
	actor["monster_form"] = ""
	actor["erosion"] = maxi(0, int(actor["erosion"]) - int(release["erosion_reduction"]))
	if jobs[actor["job_id"]]["type"] == "monster":
		actor["job_id"] = actor["last_human_job"]
	_refresh_caps(actor)
	_reconcile_slots(actor)
	return true


func start_battle(enemy_ids: Array, random_seed: int) -> BattleState:
	if _state.is_empty() or party_defeated() or _battle != null or enemy_ids.is_empty() or enemy_ids.size() > 4:
		return null
	for identifier in enemy_ids:
		if not enemy_definitions.has(identifier):
			return null
	var party: Array[Combatant] = []
	for saved in _state["party"]:
		var actor := Combatant.new(saved["id"], saved["name"], Combatant.Team.PARTY, _compute_stats(saved, true))
		actor.job_id = saved["job_id"]
		actor.hp = saved["hp"]
		actor.mp = saved["mp"]
		actor.learned = _available(saved)
		actor.equipped.assign(saved["equipped_abilities"])
		party.append(actor)
	var foes: Array[Combatant] = []
	for i in range(enemy_ids.size()):
		var definition: Dictionary = enemy_definitions[enemy_ids[i]]
		var actor := Combatant.new("enemy_%02d" % (i + 1), definition["name"], Combatant.Team.ENEMY, definition["stats"])
		actor.learned.assign(definition["abilities"])
		actor.equipped.assign(definition["abilities"])
		actor.weaknesses.assign(definition["weaknesses"])
		actor.tactics = definition.get("tactics",actor.tactics).duplicate(true)
		foes.append(actor)
	_battle = BattleState.new(party, foes, catalog, random_seed)
	_world_battle_id = ""
	_battle.potions = int(_state["inventory"]["potion"])
	_battle_enemy_ids.assign(enemy_ids)
	_claimed = false
	_field_battle = false
	_story_wave_step = -1
	_expedition_battle_stage = -1
	return _battle


func party_defeated() -> bool:
	if _state.is_empty():
		return false
	for actor in _state["party"]:
		if actor["hp"] > 0:
			return false
	return true


func story_wave_index() -> int:
	if not _state.get("expedition",{}).is_empty():
		return int(_state["expedition"]["wave"])
	var progress: Dictionary = _state.get("story_battle",{})
	return int(progress.get("cleared",0)) if progress.get("step") == world_state().get("quest_step") else 0


func story_wave_count() -> int:
	return StoryCampaign.battle_waves(current_story_step()).size()


func story_battle_cleared() -> bool:
	return story_wave_count() > 0 and story_wave_index() == story_wave_count()


func start_story_battle() -> BattleState:
	if world_exploration_active():
		return null
	var entry := current_story_step()
	var world := world_state()
	if _battle != null or is_returning_to_town() or entry.get("kind") != "battle" or world["location"] != entry["location"] or world["player_cell"] != entry["cell"]:
		return null
	var waves := StoryCampaign.battle_waves(entry)
	var next := story_wave_index()
	if next >= waves.size():
		return null
	var encounter := start_battle(waves[next],int(entry.get("seed",20260919+int(world["quest_step"])))+next*1000)
	if encounter != null:
		_story_wave_step = int(world["quest_step"])
		_story_wave_number = next
		if not _state.get("expedition",{}).is_empty():
			_expedition_battle_stage = int(_state["expedition"]["stage"])
	return encounter


func field_battle_enemies() -> Array:
	var world := world_state()
	if world.is_empty() or story_complete():
		return []
	if not _state.get("expedition",{}).is_empty():
		return [["slime"],["bat"]][int(_state.get("field_battles",0))%2]
	var encounters: Array = []
	if world["location"] == "waterway" and world["quest_step"] >= 3:
		encounters = [["slime"], ["bat"]]
	elif world["location"] == "cave" and world["quest_step"] >= 7:
		encounters = [["shell_guard"], ["ember_wisp"]]
	elif world["location"] in ["school", "records"]:
		encounters = [["shell_guard"], ["ember_wisp"]]
	if encounters.is_empty():
		return []
	return encounters[int(_state.get("field_battles", 0)) % encounters.size()].duplicate()


func start_field_battle() -> BattleState:
	var enemies := field_battle_enemies()
	if enemies.is_empty():
		return null
	var encounter := start_battle(enemies, 20260919 + int(_state.get("field_battles", 0)))
	if encounter != null:
		_field_battle = true
	return encounter


func current_enemy_ids() -> Array[String]:
	return _battle_enemy_ids.duplicate()


func is_field_battle() -> bool:
	return _battle != null and (_field_battle or not _world_battle_id.is_empty())


func is_world_battle() -> bool:
	return _battle != null and not _world_battle_id.is_empty()


func finish_battle() -> bool:
	if _battle == null or _claimed or not _battle.phase in [BattleState.Phase.VICTORY, BattleState.Phase.DEFEAT]:
		return false
	_claimed = true
	if _field_battle:
		_state["field_battles"] = int(_state.get("field_battles", 0)) + 1
	var won: bool = _battle.phase == BattleState.Phase.VICTORY
	if won and not _world_battle_id.is_empty() and _world_battle_id not in _state["overworld"]["cleared"]:
		_state["overworld"]["cleared"].append(_world_battle_id)
	if won and _expedition_battle_stage >= 0:
		_state["expedition"]["wave"] = _story_wave_number+1
	elif won and _story_wave_step >= 0:
		_state["story_battle"] = {"step":_story_wave_step,"cleared":_story_wave_number+1}
	var reward := 0
	if won:
		for identifier in _battle_enemy_ids:
			reward += int(enemy_definitions[identifier]["jp"])
	_state["inventory"]["potion"] = _battle.potions
	var erosion_results := erosion_preview()
	var battle_result := {"enemies":_battle_enemy_ids.duplicate(),"victory":won,"rounds":_battle.round_number,"jp":reward,"erosion":erosion_results.duplicate(true),"remaining":_battle.snapshot()["actors"]}
	var member_index := 0
	for actor in _state["party"]:
		var combatant := _battle.actor_by_id(actor["id"])
		actor["hp"] = combatant.hp
		actor["mp"] = combatant.mp
		var job: Dictionary = jobs[actor["job_id"]]
		var erosion: Dictionary = erosion_results[member_index]
		member_index += 1
		actor["erosion"] = erosion["after"]
		if actor["erosion"] >= 90:
			actor["irreversible"] = true
		if won:
			var earned := floori(float(reward) / 2.0) if job["type"] == "human" and int(actor["erosion"]) >= 60 else reward
			var jp := int(actor["jp"].get(actor["job_id"], 0)) + earned
			actor["jp"][actor["job_id"]] = jp
			var cost := int(job["mastery_cost"])
			if jp >= ceili(float(cost) / 2.0):
				var first_skill: String = job["abilities"][0]
				if not first_skill in actor["learned_abilities"]:
					actor["learned_abilities"].append(first_skill)
			if jp >= cost:
				for identifier in job["abilities"]:
					if not identifier in actor["learned_abilities"]:
						actor["learned_abilities"].append(identifier)
				if not actor["job_id"] in actor["mastered_jobs"]:
					actor["mastered_jobs"].append(actor["job_id"])
					if job["type"] == "monster":
						actor["monster_form"] = actor["job_id"]
						_learn_form(actor, actor["job_id"])
		# JPは戦闘時の職へ与え、その後に90到達時の職業移行を反映する。
		if not str(erosion["forced_job"]).is_empty():
			actor["job_id"] = erosion["forced_job"]
			if actor["job_id"] in actor["mastered_jobs"]:
				actor["monster_form"] = actor["job_id"]
				_learn_form(actor, actor["job_id"])
		_refresh_caps(actor)
		_reconcile_slots(actor)
		_grant_job_unlocks(actor)
	play_metrics.record_event("battle_finished",battle_result)
	_battle = null
	_world_battle_id = ""
	_field_battle = false
	_story_wave_step = -1
	_expedition_battle_stage = -1
	return true


func rest() -> bool:
	if _battle != null or _state.is_empty():
		return false
	for actor in _state["party"]:
		actor["hp"] = actor["max_hp"]
		actor["mp"] = actor["max_mp"]
	return true


func world_state() -> Dictionary:
	return _state.get("world", {}).duplicate(true)


func world_exploration_active() -> bool:
	return bool(_state.get("overworld",{}).get("active",false))


func overworld_state() -> Dictionary:
	return _state.get("overworld",{}).duplicate(true)


func open_world_exploration() -> bool:
	if _state.is_empty() or _battle != null or party_defeated():
		return false
	if world_exploration_active():
		return true
	var origin: String = world_state()["location"]
	if origin not in ChapterOne.TOWNS or not _state.get("expedition",{}).is_empty():
		return false
	var candidate := WorldExpedition.initial(origin,_state["progress_flags"])
	if _state.has("overworld"):
		for key in ["seen","cleared","choices","visited","flags"]:
			candidate[key] = _state["overworld"][key].duplicate(true)
		if _state["progress_flags"].get("chapter1_cleared",false):
			candidate["flags"]["world_causeway_open"] = true
	if not WorldExpedition.valid(candidate):
		return false
	_state["overworld"] = candidate
	play_metrics.record_event("world_exploration_started",{"origin":origin})
	return true


func close_world_exploration() -> bool:
	if not world_exploration_active() or _battle != null or not WorldExpedition.at_origin(_state["overworld"]):
		return false
	_state["overworld"]["active"] = false
	return true


func move_overworld(cell: Vector2i) -> bool:
	if not world_exploration_active() or _battle != null or party_defeated():
		return false
	var moved := WorldExpedition.move(_state["overworld"],cell)
	if moved:
		play_metrics.mark("moved_cells")
	return moved


func change_world_transport(mode: String) -> bool:
	return world_exploration_active() and _battle == null and WorldExpedition.change_transport(_state["overworld"],mode)


func interact_overworld() -> Dictionary:
	if not world_exploration_active() or _battle != null or party_defeated():
		return {}
	var result := WorldExpedition.interact(_state["overworld"])
	if result.get("kind") == "rest":
		rest()
		result["kind"] = "dialogue"
		result["text"].append("全員のHPとMPが回復しました。")
	return result


func choose_world_option(option: int) -> Dictionary:
	if not world_exploration_active() or _battle != null:
		return {}
	var result := WorldExpedition.choose(_state["overworld"],option)
	if not result.is_empty():
		_state["inventory"]["potion"] += result["potions"]
		play_metrics.record_event("world_site_completed",{"site":_state["overworld"]["node"],"option":option,"grant":result["grant"]})
	return result


func start_world_battle() -> BattleState:
	if not world_exploration_active() or _battle != null:
		return null
	var state: Dictionary = _state["overworld"]
	var event := WorldExpedition.event_at(state)
	if event.get("kind") != "battle" or WorldExpedition.done(state,event["id"]) or not WorldExpedition.ready(state,event):
		return null
	var encounter := start_battle(event["enemies"],20260921+int(WorldExpedition.node(state["node"])["progression_index"])*10+state["room"])
	if encounter != null:
		_world_battle_id = event["id"]
	return encounter


func is_returning_to_town() -> bool:
	return not _state.get("return_point", {}).is_empty()


func return_to_town() -> bool:
	if _state.is_empty() or _battle != null or is_returning_to_town() or _state["world"]["location"] in ChapterOne.TOWNS or story_complete():
		return false
	var previous := world_state()
	if not set_world("town", [5,4], previous["quest_step"]):
		return false
	_state["return_point"] = previous
	return true


func resume_exploration() -> bool:
	if _battle != null or not is_returning_to_town():
		return false
	var previous: Dictionary = _state["return_point"]
	if not set_world(previous["location"], previous["player_cell"], previous["quest_step"],previous.get("section","")):
		return false
	_state["return_point"] = {}
	return true


func set_world(location: String, cell: Array, quest_step: int, section: String = "") -> bool:
	if world_exploration_active():
		return false
	if _state.is_empty() or _battle != null or not ChapterOne.TITLES.has(location) or cell.size() != 2:
		return false
	var position := Vector2i(int(cell[0]),int(cell[1]))
	var walkable: bool = ExplorationSites.is_walkable(location,position,_state["progress_flags"]) if section.is_empty() else CampaignContent.section(section).get("location") == location and CampaignContent.is_walkable(section,position,_state["progress_flags"])
	if not walkable or quest_step < 0 or quest_step > StoryCampaign.total_steps():
		return false
	_state["world"] = {"location": location, "player_cell": [int(cell[0]), int(cell[1])], "quest_step": quest_step}
	if not section.is_empty():
		_state["world"]["section"] = section
	return true


func current_story_step() -> Dictionary:
	if not _state.get("expedition",{}).is_empty():
		return CampaignContent.step(_state["expedition"],_state["progress_flags"])
	var base := StoryCampaign.step(int(world_state().get("quest_step",0)), _state.get("story_task", {}))
	if not _state.is_empty():
		var pending := CampaignContent.pending(_state)
		if not pending.is_empty():
			base["kind"] = "expedition"
			base["expedition_id"] = pending["id"]
			base["objective"] = pending["title"]+"へ進む"
	return base


func begin_expedition(identifier: String) -> bool:
	var pending := CampaignContent.pending(_state,identifier)
	var entry := current_story_step()
	if _battle != null or pending.get("id") != identifier or world_state().get("player_cell") != entry.get("cell"):
		return false
	var candidate := _state.duplicate(true)
	candidate["expedition"] = {"id":identifier,"stage":0,"wave":0,"origin":world_state(),"solved":[]}
	var room: Dictionary = pending["sections"][0]
	candidate["world"] = {"location":room["location"],"player_cell":room["spawn"].duplicate(),"section":room["id"],"quest_step":pending["trigger_step"]}
	if not _valid_state(candidate):
		return false
	_state = candidate
	play_metrics.mark("circuits_started")
	return true


func long_missions() -> Array[Dictionary]:
	if _state.is_empty():return []
	# 既存の点検を終えるまでは、その地点の長編依頼へ進ませない。
	var pending:=CampaignContent.pending(_state)
	if pending.is_empty() or LongCampaign.mission(pending.get("id","")).is_empty():return []
	return LongCampaign.available(_state)


func answer_challenge(option: int) -> bool:
	var entry := current_story_step()
	if _battle != null or is_returning_to_town() or entry.get("kind") != "challenge" or world_state()["player_cell"] != entry["cell"] or option not in range(entry["options"].size()):
		return false
	play_metrics.mark("challenge_attempts")
	var accepted: bool=entry.get("choice",false) or option==entry["answer"]
	play_metrics.record_event("challenge_answer",{"id":entry["id"],"option":option,"correct":accepted})
	if not accepted:
		play_metrics.mark("challenge_mistakes")
		return false
	return _advance_expedition(true,option)


func _advance_expedition(challenge_answered: bool = false, option: int = -1) -> bool:
	var entry := current_story_step()
	if _battle != null or is_returning_to_town() or world_state()["player_cell"] != entry["cell"]:
		return false
	if entry["kind"] == "challenge" and not challenge_answered:
		return false
	if entry["kind"] == "battle" and not story_battle_cleared():
		return false
	var candidate := _state.duplicate(true)
	var expedition: Dictionary = candidate["expedition"]
	var is_long:=not LongCampaign.mission(expedition["id"]).is_empty()
	if entry["kind"] == "circuit_complete":
		var completed_flag: String=LongCampaign.cleared_flag(expedition["id"]) if is_long else "circuit_"+expedition["id"]+"_cleared"
		candidate["progress_flags"][completed_flag] = true
		candidate["world"] = expedition["origin"].duplicate(true)
		candidate["expedition"] = {}
	else:
		if entry["kind"] == "challenge":
			expedition["solved"].append(entry["id"])
			apply_challenge_reward(candidate,entry)
			if is_long and entry.get("choice",false):
				if option not in range(entry["options"].size()):return false
				candidate["progress_flags"][LongCampaign.choice_flag(entry["id"],option)]=true
				var effects: Array=entry.get("choice_effects",[])
				if option<effects.size():
					for flag in effects[option].get("flags",[]):candidate["progress_flags"][flag]=true
					candidate["inventory"]["potion"]+=int(effects[option].get("potion_bonus",0))
		expedition["stage"] += 1
		expedition["wave"] = 0
		if entry["kind"] == "section_travel":
			candidate["world"]["section"] = entry["destination"]
			candidate["world"]["player_cell"] = entry["spawn"].duplicate()
	if not _valid_state(candidate):
		return false
	_state = candidate
	if entry["kind"] == "circuit_complete":
		play_metrics.mark("long_missions_completed" if is_long else "circuits_completed")
	return true


static func apply_challenge_reward(state: Dictionary, entry: Dictionary) -> void:
	state["inventory"]["potion"] += int(entry.get("reward_potions",0))
	for actor in state["party"]:
		if actor["hp"]<=0:continue
		for pair in [["hp","max_hp","reward_hp_percent"],["mp","max_mp","reward_mp_percent"]]:
			var recovered:=ceili(float(actor[pair[1]])*float(entry.get(pair[2],0))/100.0)
			actor[pair[0]]=mini(actor[pair[1]],actor[pair[0]]+recovered)


func world_walkable_cells() -> Array:
	if not str(world_state().get("section","")).is_empty():
		return CampaignContent.walkable_cells(world_state()["section"],_state["progress_flags"])
	var location: String = world_state().get("location","")
	var result := ChapterOne.walkable_cells(location)
	for site in exploration_sites():
		if site["kind"] == "device" and site["complete"]:
			for cell in site["opens"]:
				if not cell in result:
					result.append(cell)
	return result


func exploration_sites() -> Array[Dictionary]:
	if not str(world_state().get("section","")).is_empty():
		return []
	return ExplorationSites.in_location(world_state().get("location",""),_state.get("progress_flags",{}))


func exploration_at_player() -> Dictionary:
	for site in exploration_sites():
		if site["cell"] == world_state()["player_cell"]:
			return site
	return {}


func exploration_options() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var site := exploration_at_player()
	if _battle != null or site.is_empty() or site["complete"]:
		return result
	if site["kind"] == "cache":
		result.append({"actor":"","ability":"","label":"回復薬%d個を受け取る" % site["potions"],"allowed":bool(_state["progress_flags"].get("exploration_"+site["requires"],false))})
		return result
	for actor in _state["party"]:
		for skill in site["abilities"]:
			var cost := int(abilities[skill]["cost"])
			result.append({"actor":actor["id"],"ability":skill,"label":"%s・%s（%dMP）" % [actor["name"],abilities[skill]["name"],cost],
				"allowed":actor["hp"] > 0 and skill in actor["equipped_abilities"] and skill in _available(actor) and actor["mp"] >= cost})
	return result


func use_exploration_site(actor_id: String = "", ability_id: String = "") -> bool:
	var site := exploration_at_player()
	for option in exploration_options():
		if not option["allowed"] or option["actor"] != actor_id or option["ability"] != ability_id:
			continue
		var candidate := _state.duplicate(true)
		if site["kind"] == "cache":
			candidate["inventory"]["potion"] += int(site["potions"])
		else:
			for actor in candidate["party"]:
				if actor["id"] == actor_id:
					actor["mp"] -= int(abilities[ability_id]["cost"])
		candidate["progress_flags"]["exploration_"+site["id"]] = true
		if not _valid_state(candidate):
			return false
		_state = candidate
		return true
	return false


func journal_entries() -> Array[Dictionary]:
	var entries := StoryCampaign.journal(_state.get("progress_flags", {}))
	entries.append_array(LongCampaign.journal(_state))
	for entry in entries:
		if entry["id"] == "R05":
			var chosen: Array[String] = []
			var unused: Array[String] = []
			for identifier in StoryCampaign.data()["keeper_learned"]:
				if identifier in StoryCampaign.data()["keeper_loadout"]:
					chosen.append(describe_ability(identifier))
				else:
					unused.append(abilities[identifier]["name"])
			entry["loadout"] = "当時の装着 %d枠\n%s\n習得済み・未装着: %s" % [Loadout.capacity(false,true),"\n".join(chosen),"、".join(unused)]
	return entries

func journal_capacity() -> int:
	var count: int=StoryCampaign.data().get("clues",[]).size()
	if _state.get("progress_flags",{}).get("long_campaign_started",false):count+=LongCampaign.data().get("clues",[]).size()
	return count


func story_complete() -> bool:
	return _state.get("progress_flags", {}).get("story_v1_cleared", false)


func story_audit() -> Array[String]:
	return StoryCampaign.audit()


func chapter_one_pause() -> bool:
	var flags: Dictionary = _state.get("progress_flags", {})
	return flags.get("chapter1_cleared", false) and not flags.get("chapter1_continued", false)


func continue_story() -> bool:
	if _battle != null or not chapter_one_pause() or int(world_state().get("quest_step",0)) != ChapterOne.STEPS.size():
		return false
	_state["progress_flags"]["chapter1_continued"] = true
	return true


func story_lines(entry: Dictionary = {}) -> Array:
	if entry.is_empty():
		entry = current_story_step()
	var definition := StoryCampaign.event(entry.get("event", ""))
	if not definition.is_empty() and StoryCampaign.apply_event(_state["progress_flags"],entry["event"]).is_empty():
		return []
	var lines: Array = definition.get("text", []).duplicate()
	if lines.is_empty():
		lines = entry.get("text", []).duplicate()
	if definition.has("reaction"):
		var changed := false
		for actor in _state["party"]:
			changed = changed or int(actor["erosion"]) >= 30 or not str(actor["monster_form"]).is_empty()
		var reactions := {"archive":["記録係は、旅人の通行札を確かめて記録を開いた。","記録係は変わり始めた身体を見て一度手を止めたが、同じ通行札を確かめて記録を開いた。"],"school":["教習係は、今使える枠と習得済みの技を順に確認した。","教習係は身体の変化より先に、使える枠と覚えた技を確認した。"],"teaching":["町の人は、旅をした仲間に教習の手伝いを頼んだ。","町の人は、身体の変化した仲間にも同じ役目を頼んだ。『覚えた手順を次の人へ教えてほしい』。"]}
		lines.push_front("【現在】" + reactions[definition["reaction"]][1 if changed else 0])
	return lines


func replayable_records() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for identifier in StoryCampaign.data()["events"]:
		var definition := StoryCampaign.event(identifier)
		if definition.get("past",false) and _state["progress_flags"].get("story_event_"+identifier,false):
			result.append({"id":identifier,"text":definition["text"].duplicate()})
	return result


func start_revisit_task(identifier: String) -> bool:
	var entry := current_story_step()
	if _battle != null or is_returning_to_town() or entry.get("kind") != "choice" or world_state()["location"] != entry["location"] or world_state()["player_cell"] != entry["cell"]:
		return false
	if identifier not in ["teaching","reply"]:
		return false
	var clue_id := "R08" if identifier == "teaching" else "R05"
	if StoryCampaign.stage(_state["progress_flags"],clue_id) == 2:
		return false
	_state["story_task"] = {"id":identifier,"step":0}
	return true


func gate_requirements(team: Array) -> Array[String]:
	var reasons: Array[String] = []
	var entry := current_story_step()
	if entry.get("kind") != "gate" or world_state()["location"] != entry.get("location") or world_state()["player_cell"] != entry.get("cell") or is_returning_to_town():
		return ["三つの操作台がある地点へ進んでください。"]
	if StoryCampaign.apply_event(_state["progress_flags"],"operation").is_empty():
		reasons.append("町の教習と番人への応答を先に確かめてください。")
	if team.size() != 3:
		reasons.append("担当する仲間を三人選んでください。")
	var seen: Array = []
	for identifier in team:
		var actor := _member(str(identifier))
		if actor.is_empty() or identifier in seen:
			reasons.append("同じ仲間を二つの操作台へ配置できません。")
			continue
		seen.append(identifier)
		if actor["hp"] <= 0:
			reasons.append(actor["name"] + "は戦闘不能です。")
		for ability_id in ["firm_guard","sound_wave"]:
			if not ability_id in _available(actor) or not ability_id in actor["equipped_abilities"]:
				reasons.append(actor["name"] + "に" + abilities[ability_id]["name"] + "の装着が必要です。")
		if actor["mp"] < gate_mp_cost():
			reasons.append(actor["name"] + "のMPが足りません。")
	return reasons


func gate_mp_cost() -> int:
	return int(abilities["firm_guard"]["cost"]) + int(abilities["sound_wave"]["cost"])


func advance_story_step(team: Array = []) -> bool:
	if world_exploration_active():
		return false
	if not _state.get("expedition",{}).is_empty():
		return _advance_expedition()
	if _battle != null or _state.is_empty() or is_returning_to_town():
		return false
	var entry := current_story_step()
	var world := world_state()
	if entry.is_empty() or world["location"] != entry["location"] or world["player_cell"] != entry["cell"]:
		return false
	if entry["kind"] == "battle" and not story_battle_cleared():
		return false
	if entry["kind"] == "choice" and (StoryCampaign.stage(_state["progress_flags"],"R05") != 2 or StoryCampaign.stage(_state["progress_flags"],"R08") != 2):
		return false
	if entry["kind"] == "gate" and (not gate_requirements(team).is_empty() or _state["progress_flags"].get("story_event_operation",false)):
		return false
	if entry["kind"] == "story_complete" and not StoryCampaign.all_resolved(_state["progress_flags"]):
		return false
	if entry["kind"]=="story_complete" and _state["progress_flags"].get("long_campaign_started",false) and not LongCampaign.all_cleared(_state["progress_flags"]):return false
	var candidate := _state.duplicate(true)
	if entry.get("id")=="v1_17" and candidate["progress_flags"].get("long_campaign_enrolled",false):candidate["progress_flags"]["long_campaign_started"]=true
	if entry["kind"] == "battle":
		candidate["story_battle"] = {}
	if entry.has("event"):
		var flags := StoryCampaign.apply_event(candidate["progress_flags"],entry["event"])
		if flags.is_empty():
			return false
		candidate["progress_flags"] = flags
		if StoryCampaign.event(entry["event"]).get("training",false):
			for actor in candidate["party"]:
				for ability_id in ["firm_guard","sound_wave"]:
					if not ability_id in actor["learned_abilities"]:
						actor["learned_abilities"].append(ability_id)
	if entry.has("flag"):
		candidate["progress_flags"][entry["flag"]] = true
	for identifier in entry.get("flags",[]):
		candidate["progress_flags"][identifier] = true
	if entry["kind"] == "gate":
		candidate["gate_team"] = team.duplicate()
		for actor in candidate["party"]:
			if actor["id"] in team:
				actor["mp"] -= gate_mp_cost()
	if entry["kind"] == "complete":
		candidate["progress_flags"]["chapter1_cleared"] = true
	if entry["kind"] == "story_complete":
		candidate["progress_flags"]["story_v1_cleared"] = true
	if entry["kind"] == "travel":
		candidate["world"]["location"] = entry["destination"]
		candidate["world"]["player_cell"] = entry["spawn"].duplicate()
	var task: Dictionary = candidate.get("story_task", {})
	if not task.is_empty():
		task["step"] += 1
		candidate["story_task"] = {} if task["step"] >= StoryCampaign.data()["branches"][task["id"]].size() else task
	else:
		candidate["world"]["quest_step"] += 1
	if not _valid_state(candidate):
		return false
	_state = candidate
	return true


func set_progress_flag(identifier: String) -> void:
	if not _state.is_empty():
		_state["progress_flags"][identifier] = true


func current_battle() -> BattleState:
	return _battle


func set_party_leader(actor_id: String) -> bool:
	if _battle != null or _member(actor_id).is_empty():
		return false
	_state["leader_id"] = actor_id
	return true


func walking_party() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var members: Array = _state.get("party",[])
	if members.is_empty():
		return result
	var leader: String = _state.get("leader_id",members[0]["id"])
	result.append(_member(leader).duplicate(true))
	for member in members:
		if member["id"] != leader:
			result.append(member.duplicate(true))
	return result


func recording_context() -> Dictionary:
	play_metrics.completed = story_complete()
	var cleared: Array[String] = []
	for circuit in CampaignContent.data()["circuits"]:
		if _state.get("progress_flags",{}).get("circuit_"+circuit["id"]+"_cleared",false):
			cleared.append(circuit["id"])
	var build := BuildIdentity.current()
	var journeys: Array[String]=[]
	for entry in LongCampaign.data().get("missions",[]):
		if _state.get("progress_flags",{}).get(LongCampaign.cleared_flag(entry["id"]),false):journeys.append(entry["id"])
	return {"engine":build["engine"],"build_id":build["id"],"build_identity_version":build["version"],"world":world_state(),"party_size":_state.get("party",[]).size(),"content_revision":_state.get("content_revision",0),"circuits_completed":cleared,"content_sha256":CampaignContent.content_hash(),"duration_target_id":DurationTarget.definition().get("id",""),"long_campaign_required":true,"long_campaign_complete":LongCampaign.all_cleared(_state.get("progress_flags",{})),"long_missions_completed":journeys}


func enable_recording(directory: String) -> bool:
	if not directory.begins_with("user://") or ".." in directory or _archive != null:
		return false
	_archive = PlaythroughArchive.new(directory)
	if not _state.is_empty():
		_archive.start(play_metrics,false)
	return true


func playthrough_id() -> String:
	return "" if _archive == null else _archive.identifier


func recording_issue() -> String:
	return "" if _archive == null else _archive.issue


func flush_recording(periodic: bool = false) -> bool:
	return true if _archive == null else _archive.flush(play_metrics,recording_context(),periodic)


func close_recording() -> bool:
	if _archive != null:
		_archive.run_open = false
	return flush_recording()


func playtest_document() -> Dictionary:
	var context := recording_context()
	if _archive != null and not _archive.identifier.is_empty():
		return _archive.document(play_metrics,context)
	var result := play_metrics.report(context)
	result["measurement_scope"] = "progress_only"
	result["history_complete"] = false
	return result


func save_playtest_report(path: String = "user://playtest-report.json") -> bool:
	if not path.begins_with("user://") or ".." in path:
		return false
	flush_recording()
	return PlaySessionMetrics.write_json(path,playtest_document())


func save_game(path: String, record_id: String = "") -> bool:
	if _battle != null or not path.begins_with("user://") or ".." in path or not _valid_state(_state):
		return false
	if not record_id.is_empty() and not PlaythroughArchive.valid_id(record_id):
		return false
	flush_recording()
	var temporary := path + ".tmp"
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return false
	var document := _state.duplicate(true)
	# 計測は進行状態と分離し、読むだけで進行状態の比較が変化しないようにする。
	document["_play_session"] = play_metrics.snapshot()
	var identifier := playthrough_id() if record_id.is_empty() else record_id
	if not identifier.is_empty():
		document["_trial_id"] = identifier
	var saved_types := SavedValueTypes.describe(document)
	if not saved_types["errors"].is_empty():
		file.close()
		DirAccess.remove_absolute(temporary)
		return false
	document["_saved_value_types"] = saved_types
	file.store_string(JSON.stringify(document, "\t", true, true))
	file.flush()
	var written := file.get_error() == OK
	file.close()
	if not written:
		DirAccess.remove_absolute(temporary)
		return false
	return DirAccess.rename_absolute(temporary, path) == OK


func load_game(path: String) -> bool:
	if _battle != null or not path.begins_with("user://") or ".." in path or not FileAccess.file_exists(path):
		return false
	var document := JSON.new()
	if document.parse(FileAccess.get_file_as_string(path)) != OK or not document.data is Dictionary:
		return false
	var candidate: Dictionary = document.data.duplicate(true)
	var saved_types: Variant = candidate.get("_saved_value_types",null)
	var has_saved_types := candidate.has("_saved_value_types")
	candidate.erase("_saved_value_types")
	var metrics := PlaySessionMetrics.new()
	var raw_metrics: Variant = candidate.get("_play_session",{})
	if not raw_metrics is Dictionary or not metrics.restore(raw_metrics):
		return false
	candidate.erase("_play_session")
	var record_id: Variant = candidate.get("_trial_id","")
	if not record_id is String or (not record_id.is_empty() and not PlaythroughArchive.valid_id(record_id)):
		return false
	candidate.erase("_trial_id")
	if not _valid_state(_normalize_numbers(candidate)):
		return false
	var restored_state: Dictionary = _normalize_numbers(candidate)
	var restored_metrics := metrics.snapshot()
	if has_saved_types:
		var typed_document := restored_state.duplicate(true)
		typed_document["_play_session"] = restored_metrics
		if not record_id.is_empty():typed_document["_trial_id"] = record_id
		var restored := SavedValueTypes.restore(typed_document,saved_types)
		if not restored["ok"]:return false
		restored_state = restored["value"]
		restored_metrics = restored_state["_play_session"]
		restored_state.erase("_play_session")
		restored_state.erase("_trial_id")
		if not _valid_state(restored_state):return false
	if not metrics.restore(restored_metrics):return false
	for field in restored_metrics:
		if field != "version":metrics.set(field,restored_metrics[field])
	if SavedValueTypes.describe(metrics.snapshot()) != SavedValueTypes.describe(restored_metrics):return false
	if _archive != null and _archive.identifier != record_id:
		close_recording()
	else:
		flush_recording()
	if not import_state(candidate):
		return false
	_state = restored_state
	play_metrics = metrics
	if _archive != null:
		_archive.resume(record_id,play_metrics)
		flush_recording()
	return true
