class_name BattleCatalog
extends RefCounted

const STAT_KEYS := ["hp", "mp", "attack", "defense", "magic", "resistance", "speed"]
const EFFECTS := ["physical", "magic", "heal", "revive", "guard", "steal", "focus", "conduct", "amplify", "overdrive", "deflect_physical", "deflect_magic", "cover", "seal", "field", "passive", "riposte", "recycle", "disarm", "restore_mp"]
const TARGETS := ["enemy", "ally", "self", "fallen_ally", "enemies", "allies"]
const AI_PROFILES := ["legacy","caster","guardian","healer","raider","reviver","mixed"]

var integration: Dictionary = {}
var errors: Array[String] = []
var jobs: Dictionary = {}
var abilities: Dictionary = {}
var enemies: Dictionary = {}
var encounters: Dictionary = {}
var potion_healing: int = 50


func _init(path: String = "res://data/catalog.json") -> void:
	var json := JSON.new()
	var parse_error := json.parse(FileAccess.get_file_as_string(path))
	if parse_error != OK or not json.data is Dictionary:
		errors.append("戦闘データを読み取れません: %s" % path)
		return
	var document: Dictionary = json.data
	if document.has("jobs_directory"):
		var directory: String = document["jobs_directory"]
		if not DirAccess.dir_exists_absolute(directory):
			errors.append("職業データがありません: " + directory)
			return
		var definitions: Array = []
		var files := DirAccess.get_files_at(directory)
		files.sort()
		for filename in files:
			if filename.ends_with(".json"):
				var job_json := JSON.new()
				if job_json.parse(FileAccess.get_file_as_string(directory.path_join(filename))) != OK or not job_json.data is Dictionary:
					errors.append("職業JSONが不正です: " + filename)
					return
				definitions.append(job_json.data)
		document["jobs"] = definitions
	var supplemental := JSON.new()
	if supplemental.parse(FileAccess.get_file_as_string("res://data/integrated_rules.json")) != OK or not supplemental.data is Dictionary:
		errors.append("統合機構の定義を読み取れません。")
		return
	integration = supplemental.data
	document["abilities"].append_array(integration["abilities"])
	_load_document(document)


func _load_document(document: Dictionary) -> void:
	if not _is_integer(document.get("potion_healing",50),1):
		errors.append("回復薬の回復量が不正です。")
		return
	potion_healing = int(document.get("potion_healing",50))
	if document.get("schema_version") != 1:
		errors.append("戦闘データのschema_versionが未対応です。")
	for collection_name in ["jobs", "abilities", "enemies", "encounters"]:
		if not document.get(collection_name) is Array:
			errors.append("一覧がありません: " + collection_name)
			return
	jobs = _index(document["jobs"], "職業")
	abilities = _index(document["abilities"], "技")
	enemies = _index(document["enemies"], "敵")
	encounters = _index(document["encounters"], "対戦")
	var monster_images: Array[String] = []
	var registry: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://assets/registry.json"))
	if registry is Dictionary:
		for entry in registry.get("assets",[]):
			if entry.get("kind") == "monster_idle":
				monster_images.append("res://" + str(entry["path"]))
	for ability_id in abilities:
		var entry: Dictionary = abilities[ability_id]
		if not entry.get("kind") in EFFECTS or not entry.get("target") in TARGETS:
			errors.append("技の種類・対象が不正です: " + ability_id)
		for field in ["cost", "power", "hits", "priority"]:
			if not _is_integer(entry.get(field), 1 if field == "hits" else 0):
				errors.append("技の数値が不正です: %s.%s" % [ability_id, field])
		if not entry.get("element") in ["none", "fire", "ice", "electric"]:
			errors.append("属性が不正です: " + ability_id)
		if not entry.get("description") is String:
			errors.append("技の説明がありません: " + ability_id)
		if entry.get("kind") in ["physical", "magic", "steal"] and entry.get("target") not in ["enemy","enemies"]:
			errors.append("攻撃技の対象は敵です: " + ability_id)
		if entry.get("kind") == "revive" and entry.get("target") != "fallen_ally":
			errors.append("蘇生の対象が不正です: " + ability_id)
		if entry.get("kind") == "guard" and (entry.get("target") != "self" or not _is_integer(entry.get("power"), 1) or float(entry.get("power", 0)) > 100.0):
			errors.append("防御技の設定が不正です: " + ability_id)
		if entry.get("kind") == "heal" and not entry.get("target") in ["self", "ally"]:
			errors.append("回復技の対象が不正です: " + ability_id)
	for job_id in jobs:
		var job: Dictionary = jobs[job_id]
		if not job.get("playable") is bool or not job.get("category") in ["human", "monster", "advanced"]:
			errors.append("職業の区分が不正です: " + job_id)
		if job.get("playable", false):
			_validate_stats(job.get("stats"), job_id)
			_validate_references(job.get("abilities"), abilities, job_id)
	for enemy_id in enemies:
		var enemy: Dictionary = enemies[enemy_id]
		_validate_stats(enemy.get("stats"), enemy_id)
		_validate_references(enemy.get("abilities"), abilities, enemy_id)
		if enemy.has("sprite_id"):
			var sprite_path := "res://assets/monsters/%s/idle.png" % enemy["sprite_id"]
			if not sprite_path in monster_images or not FileAccess.file_exists(sprite_path):
				errors.append("敵の画像参照が不正です: " + enemy_id)
		if enemy.has("tactics"):
			var behavior: Variant = enemy["tactics"]
			if not behavior is Dictionary:
				errors.append("敵の行動規則がありません: " + enemy_id)
			elif not behavior.get("profile") in AI_PROFILES or not behavior.get("focus") in ["random","lowest_hp","highest_magic"] or not _is_integer(behavior.get("heal_below"),1) or int(behavior.get("heal_below",0)) > 100 or not _is_integer(behavior.get("guard_every"),2):
				errors.append("敵の行動規則が不正です: " + enemy_id)
			if behavior is Dictionary:
				for setting in {"reaction_power":1000,"reaction_speed":20,"focus_variation":100}:
					if not _is_integer(behavior.get(setting,0),0) or int(behavior.get(setting,0))>int({"reaction_power":1000,"reaction_speed":20,"focus_variation":100}[setting]):errors.append("敵の反応設定が不正です: "+enemy_id+"/"+setting)
				if not _is_integer(behavior.get("chorus_guard",100),1) or int(behavior.get("chorus_guard",100))>100:errors.append("共鳴防御が不正です: "+enemy_id)
		if not enemy.get("weaknesses") is Array:
			errors.append("弱点の一覧がありません: " + enemy_id)
		else:
			for weakness in enemy["weaknesses"]:
				if not weakness in ["fire", "ice", "electric"]:
					errors.append("弱点が不正です: " + enemy_id)
	for encounter_id in encounters:
		_validate_references(encounters[encounter_id].get("enemies"), enemies, encounter_id, false)
		var members: Variant = encounters[encounter_id].get("enemies")
		if members is Array and (members.is_empty() or members.size() > 3):
			errors.append("検証画面の敵は1〜3体です: " + encounter_id)


func _index(entries: Array, label: String) -> Dictionary:
	var result: Dictionary = {}
	for entry in entries:
		if not entry is Dictionary or not entry.get("id") is String or not entry.get("name") is String:
			errors.append(label + "のIDまたは名前がありません。")
			continue
		var identifier: String = entry["id"]
		if identifier.is_empty() or result.has(identifier):
			errors.append(label + "のIDが空または重複しています: " + identifier)
			continue
		result[identifier] = entry
	return result


func _validate_stats(value: Variant, label: String) -> void:
	if not value is Dictionary:
		errors.append("能力値がありません: " + label)
		return
	for field in STAT_KEYS:
		if not _is_integer(value.get(field), 1 if field == "hp" else 0):
			errors.append("能力値が不正です: %s.%s" % [label, field])


func _validate_references(value: Variant, index: Dictionary, label: String, unique: bool = true) -> void:
	if not value is Array:
		errors.append("参照一覧がありません: " + label)
		return
	var seen: Array[String] = []
	for key in value:
		if not key is String or not index.has(key):
			errors.append("未定義の参照があります: " + label)
		elif unique and key in seen:
			errors.append("参照が重複しています: " + label)
		else:
			seen.append(key)


static func _is_integer(value: Variant, minimum: int) -> bool:
	return (value is int or value is float) and float(value) >= minimum and float(value) == floor(float(value))


func playable_jobs() -> Array[String]:
	var result: Array[String] = []
	for job_id in jobs:
		if jobs[job_id]["playable"]:
			result.append(job_id)
	return result


func training_abilities() -> Array[String]:
	var result: Array[String] = []
	for job_id in playable_jobs():
		for ability_id in jobs[job_id]["abilities"]:
			if not ability_id in result:
				result.append(ability_id)
	return result


func make_party(job_ids: Array[String], loadouts: Array) -> Array[Combatant]:
	var result: Array[Combatant] = []
	if not errors.is_empty() or job_ids.size() != 4 or loadouts.size() != 4:
		return result
	for i in range(4):
		if not job_ids[i] in playable_jobs():
			return []
		var equipped: Array[String] = []
		equipped.assign(loadouts[i])
		if not Loadout.validate(training_abilities(), equipped, 2).is_empty():
			return []
		var job: Dictionary = jobs[job_ids[i]]
		var actor := Combatant.new("pc_%02d" % (i + 1), "仲間%d" % (i + 1), Combatant.Team.PARTY, job["stats"])
		actor.job_id = job_ids[i]
		actor.learned = training_abilities()
		actor.equipped = equipped
		result.append(actor)
	return result


func make_enemies(encounter_id: String) -> Array[Combatant]:
	var result: Array[Combatant] = []
	if not errors.is_empty() or not encounters.has(encounter_id):
		return result
	var definitions: Array = encounters[encounter_id]["enemies"]
	for i in range(definitions.size()):
		var entry: Dictionary = enemies[definitions[i]]
		var actor := Combatant.new("enemy_%02d" % (i + 1), entry["name"], Combatant.Team.ENEMY, entry["stats"])
		actor.learned.assign(entry["abilities"])
		actor.equipped.assign(entry["abilities"])
		actor.weaknesses.assign(entry["weaknesses"])
		actor.tactics = entry.get("tactics",actor.tactics).duplicate(true)
		result.append(actor)
	return result
