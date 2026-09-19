class_name GameSession
extends RefCounted

const MONSTER_BATTLE_EROSION := 3
const MONSTER_SKILL_EROSION := 1

var catalog: BattleCatalog
var jobs: Dictionary = {}
var abilities: Dictionary = {}
var enemy_definitions: Dictionary = {}
var errors: Array[String] = []

var _state: Dictionary = {}
var _battle: BattleState
var _battle_enemy_ids: Array[String] = []
var _claimed: bool = true
var _field_battle: bool = false


func _init() -> void:
	catalog = BattleCatalog.new()
	jobs = catalog.jobs
	abilities = catalog.abilities
	enemy_definitions = catalog.enemies
	errors.assign(catalog.errors)
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
	var starts := ["warrior", "martial_artist", "priest", "mage"]
	var party: Array = []
	for i in range(party_size):
		var job: Dictionary = jobs[starts[i]]
		party.append({
			"id": "pc_%02d" % (i + 1), "name": "仲間%d" % (i + 1),
			"job_id": starts[i], "last_human_job": starts[i], "jp": {},
			"mastered_jobs": [], "learned_abilities": [], "equipped_abilities": [],
			"monster_form": "", "erosion": 0, "irreversible": false,
			"hp": int(job["stats"]["hp"]), "max_hp": int(job["stats"]["hp"]),
			"mp": int(job["stats"]["mp"]), "max_mp": int(job["stats"]["mp"])
		})
	_state = {"format_version": 1, "party": party, "inventory": {"potion": 3},
		"progress_flags": {"chapter1_cleared": false, "midgame_slots": false},
		"field_battles": 0, "return_point": {},
		"world": {"location": "town", "player_cell": [2, 4], "quest_step": 0}}
	_battle = null
	_claimed = true
	_field_battle = false
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
	_battle = null
	_claimed = true
	_field_battle = false
	return true


func _valid_state(value: Dictionary) -> bool:
	if value.get("format_version") != 1 or not value.get("party") is Array:
		return false
	var party: Array = value["party"]
	if party.size() < 3 or party.size() > 4 or not value.get("inventory") is Dictionary or not value.get("progress_flags") is Dictionary or not value.get("world") is Dictionary:
		return false
	if not _valid_world(value["world"]):
		return false
	for identifier in value["progress_flags"]:
		if not identifier is String or not value["progress_flags"][identifier] is bool:
			return false
	if not value.get("field_battles", 0) is int or int(value.get("field_battles", 0)) < 0:
		return false
	var return_point: Variant = value.get("return_point", {})
	if not return_point is Dictionary:
		return false
	if not return_point.is_empty():
		if not _valid_world(return_point) or return_point["location"] == "town" or value["world"]["location"] != "town" or return_point["quest_step"] != value["world"]["quest_step"]:
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
	return true


static func _valid_world(world: Dictionary) -> bool:
	if not world.has_all(["location", "player_cell", "quest_step"]):
		return false
	if not world["location"] is String or not ChapterOne.TITLES.has(world["location"]):
		return false
	if not world["quest_step"] is int or world["quest_step"] < 0 or world["quest_step"] > ChapterOne.STEPS.size():
		return false
	var cell: Variant = world["player_cell"]
	return cell is Array and cell.size() == 2 and cell[0] is int and cell[1] is int and ChapterOne.is_walkable(world["location"], Vector2i(cell[0],cell[1]))


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
	if _battle != null or not jobs.has(job_id):
		return false
	var actor := _member(actor_id)
	if actor.is_empty() or (actor["irreversible"] and jobs[job_id]["type"] == "human"):
		return false
	actor["job_id"] = job_id
	if jobs[job_id]["type"] == "human":
		actor["last_human_job"] = job_id
	elif job_id in actor["mastered_jobs"]:
		actor["monster_form"] = job_id
		_learn_form(actor, job_id)
	_refresh_caps(actor)
	_reconcile_slots(actor)
	return true


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
	return true


func unequip_ability(actor_id: String, ability_id: String) -> bool:
	if _battle != null:
		return false
	var actor := _member(actor_id)
	if actor.is_empty() or not ability_id in actor["equipped_abilities"]:
		return false
	actor["equipped_abilities"].erase(ability_id)
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
	if actor.is_empty() or str(actor["monster_form"]).is_empty():
		return false
	var release: Dictionary = jobs[actor["monster_form"]]["monster_form"]["release"]
	if event != release["event"] or actor["irreversible"] or int(actor["erosion"]) > int(release["max_erosion"]):
		return false
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
	if _state.is_empty() or _battle != null or enemy_ids.is_empty() or enemy_ids.size() > 4:
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
		foes.append(actor)
	_battle = BattleState.new(party, foes, catalog, random_seed)
	_battle.potions = int(_state["inventory"]["potion"])
	_battle_enemy_ids.assign(enemy_ids)
	_claimed = false
	_field_battle = false
	return _battle


func field_battle_enemies() -> Array:
	var world := world_state()
	if world.is_empty() or _state["progress_flags"].get("chapter1_cleared", false):
		return []
	var encounters: Array = []
	if world["location"] == "waterway" and world["quest_step"] >= 3:
		encounters = [["slime"], ["bat"]]
	elif world["location"] == "cave" and world["quest_step"] >= 7:
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
	return _battle != null and _field_battle


func finish_battle() -> bool:
	if _battle == null or _claimed or not _battle.phase in [BattleState.Phase.VICTORY, BattleState.Phase.DEFEAT]:
		return false
	_claimed = true
	if _field_battle:
		_state["field_battles"] = int(_state.get("field_battles", 0)) + 1
	var won: bool = _battle.phase == BattleState.Phase.VICTORY
	var reward := 0
	if won:
		for identifier in _battle_enemy_ids:
			reward += int(enemy_definitions[identifier]["jp"])
	_state["inventory"]["potion"] = _battle.potions
	var erosion_results := erosion_preview()
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
	_battle = null
	_field_battle = false
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


func is_returning_to_town() -> bool:
	return not _state.get("return_point", {}).is_empty()


func return_to_town() -> bool:
	if _state.is_empty() or _battle != null or is_returning_to_town() or _state["world"]["location"] == "town" or _state["progress_flags"].get("chapter1_cleared", false):
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
	if not set_world(previous["location"], previous["player_cell"], previous["quest_step"]):
		return false
	_state["return_point"] = {}
	return true


func set_world(location: String, cell: Array, quest_step: int) -> bool:
	if _state.is_empty() or _battle != null or not ChapterOne.TITLES.has(location) or cell.size() != 2:
		return false
	if not ChapterOne.is_walkable(location, Vector2i(int(cell[0]), int(cell[1]))) or quest_step < 0 or quest_step > ChapterOne.STEPS.size():
		return false
	_state["world"] = {"location": location, "player_cell": [int(cell[0]), int(cell[1])], "quest_step": quest_step}
	return true


func set_progress_flag(identifier: String) -> void:
	if not _state.is_empty():
		_state["progress_flags"][identifier] = true


func current_battle() -> BattleState:
	return _battle


func save_game(path: String) -> bool:
	if _battle != null or not path.begins_with("user://") or ".." in path or not _valid_state(_state):
		return false
	var temporary := path + ".tmp"
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(_state, "\t"))
	file.close()
	return DirAccess.rename_absolute(temporary, path) == OK


func load_game(path: String) -> bool:
	if _battle != null or not path.begins_with("user://") or ".." in path or not FileAccess.file_exists(path):
		return false
	var document := JSON.new()
	if document.parse(FileAccess.get_file_as_string(path)) != OK or not document.data is Dictionary:
		return false
	return import_state(document.data)
