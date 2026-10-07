extends RefCounted
## S1の旧入力・装備層・元入力との厳密照合。新版codec/statsの検証器ではない。
const View = preload("res://scripts/game/equipment_state_view.gd")
const Rules = preload("res://scripts/game/equipment_rules.gd")
const ROOT = ["format_version", "party", "leader_id", "inventory", "progress_flags", "field_battles", "return_point", "story_battle", "content_revision", "expedition", "world", "overworld", "story_task", "gate_team", "_play_session", "_trial_id", "_saved_value_types", "integrated", "first_region"]
const ACTOR = ["id", "name", "job_id", "last_human_job", "jp", "mastered_jobs", "learned_abilities", "equipped_abilities", "unlocked_jobs", "monster_form", "erosion", "irreversible", "hp", "max_hp", "mp", "max_mp", "integrated"]
const OWN = ["exp", "level", "erosion_fraction", "jp_remainders", "forgotten", "relearn", "focus_binding", "weapons", "mastery"]
const NEW_ROOT = ["equipment_rules_version", "equipment_stock", "equipment_migration", "equipment_grants"]

static func error(path: String, code: String) -> Dictionary:
	return {"target": path, "reason_code": code}

static func fields(value: Dictionary, allowed: Array, path: String, errors: Array) -> void:
	for key in value:
		if key not in allowed:
			errors.append(error(path + "." + str(key), "unknown_field"))

static func values(value: Variant, path: String = "$") -> Array:
	var errors: Array = []
	if value is Dictionary:
		if value.is_typed():errors.append(error(path, "unsupported_value"))
		for key in value:
			if not key is String:errors.append(error(path, "unsupported_value"))
			errors.append_array(values(value[key], path + "." + str(key)))
	elif value is Array:
		if value.is_typed() and value.get_typed_builtin() not in SavedValueTypes.ARRAY_TYPES:
			errors.append(error(path, "unsupported_value"))
		for index in range(value.size()):errors.append_array(values(value[index], path + "[%d]" % index))
	elif value is float:
		if not is_finite(value):errors.append(error(path, "numeric_overflow"))
	elif typeof(value) not in [TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING]:
		errors.append(error(path, "unsupported_value"))
	return errors

static func context_errors(context: Dictionary) -> Array:
	if not context.get("legacy_session") is GameSession:
		return [error("context.legacy_session", "invalid_context")]
	var session: GameSession = context.legacy_session
	if not session.errors.is_empty() or not context.get("abilities") is Dictionary:
		return [error("context.abilities", "invalid_catalog")]
	var abilities: Dictionary = context.abilities
	# 既存catalogを別の定義で上書きしない。新能力は完全定義を明示する。
	if not differences(session.abilities, _legacy_abilities(abilities, session.abilities)).is_empty():
		return [error("context.abilities", "invalid_catalog")]
	for identifier in abilities:
		var entry: Variant = abilities[identifier]
		if not identifier is String or not entry is Dictionary or entry.get("id") != identifier or entry.get("kind") not in BattleCatalog.EFFECTS or entry.get("target") not in BattleCatalog.TARGETS or not entry.get("description") is String or entry.get("element") not in ["none", "fire", "ice", "electric"]:
			return [error("context.abilities." + str(identifier), "invalid_catalog")]
		for key in ["cost", "power", "hits", "priority"]:
			var number: Variant = entry.get(key)
			if not (number is int or number is float) or not is_finite(float(number)) or float(number) != floor(float(number)) or float(number) >= 9223372036854775808.0 or number < (1 if key == "hits" else 0):
				return [error("context.abilities." + identifier + "." + key, "invalid_catalog")]
	if not abilities.has("two_handed"):
		return [error("context.abilities.two_handed", "unknown_ability")]
	if abilities.two_handed.kind != "passive" or abilities.two_handed.target != "self":
		return [error("context.abilities.two_handed", "invalid_catalog")]
	if context.has("source_build") and not context.source_build is String:
		return [error("context.source_build", "invalid_context")]
	return Rules.new().definition_errors()

static func _legacy_abilities(abilities: Dictionary, legacy: Dictionary) -> Dictionary:
	var result: Dictionary = {}
	for identifier in legacy:
		if abilities.has(identifier):result[identifier] = abilities[identifier]
	return result

static func validate_legacy(document: Dictionary, context: Dictionary) -> Array:
	var errors := context_errors(context)
	if not errors.is_empty():return errors
	errors = values(document)
	fields(document, ROOT, "$", errors)
	if not errors.is_empty():return errors
	if not document.get("format_version") is int or document.format_version not in [1, 2]:
		return [error("$.format_version", "unsupported_version")]
	var projected := View.project(document)
	if not projected.ok:return projected.errors
	for key in ["world", "inventory", "progress_flags", "expedition", "story_task", "story_battle", "return_point"]:
		if document.has(key) and not document[key] is Dictionary:
			return [error("$." + key, "invalid_source")]
	if not document.has_all(["world", "inventory", "progress_flags"]):return [error("$", "invalid_source")]
	if document.format_version == 2 and not IntegratedProgression.valid_world(document.get("integrated")):
		return [error("$.integrated", "invalid_source")]
	if document.format_version == 1 and document.has("integrated"):
		return [error("$.integrated", "mixed_legacy_state")]
	var session: GameSession = context.legacy_session
	var ids: Array = []
	for group in ["party", "reserve"]:
		var people: Array = projected.view.party if group == "party" else projected.view.first_region.reserve
		for index in range(people.size()):
			var path := "$.party[%d]" % index if group == "party" else "$.first_region.reserve[%d]" % index
			var person: Variant = people[index]
			var code := "invalid_reserve" if group == "reserve" else "invalid_source"
			if not person is Dictionary:return [error(path, code)]
			fields(person, ACTOR, path, errors)
			if person.get("integrated") is Dictionary:
				fields(person.integrated, OWN, path + ".integrated", errors)
				if person.integrated.get("mastery") is Dictionary:fields(person.integrated.mastery, ["counts", "legacy_masters"], path + ".integrated.mastery", errors)
			if not errors.is_empty():return errors
			if not session.validate_legacy_actor(person.duplicate(true), document.format_version, document.get("integrated", {}).duplicate(true), document.progress_flags.duplicate(true)) or person.id in ids:
				return [error(path, code)]
			ids.append(person.id)
			if document.format_version == 1:
				for identifier in person.jp:
					var job: Dictionary = session.jobs[identifier]
					var converted := float(person.jp[identifier]) * float(IntegratedProgression.cost(job, true)) / float(IntegratedProgression.cost(job, false))
					if not is_finite(converted) or converted >= 9223372036854775808.0:
						return [error(path + ".jp." + identifier, "numeric_overflow")]
	if not session._valid_state(document.duplicate(true)):
		return [error("$", "invalid_source")]
	if document.has("_trial_id") and (not document._trial_id is String or document._trial_id.length() != 32 or not document._trial_id.is_valid_hex_number(false)):
		return [error("$._trial_id", "invalid_record_id")]
	return []

static func equipment_layer(document: Dictionary, context: Dictionary) -> Array:
	var errors := context_errors(context)
	if not errors.is_empty():return errors
	errors = values(document)
	fields(document, ROOT + NEW_ROOT, "$", errors)
	if not errors.is_empty():return errors
	if not document.get("format_version") is int or document.format_version != 2:
		return [error("$.format_version", "unsupported_version")]
	var projected := View.project(document)
	if not projected.ok:return projected.errors
	errors = Rules.new().validate_equipment_state(projected.view)
	if not errors.is_empty():return errors
	for person in projected.view.party + projected.view.first_region.reserve:
		for identifier in person.learned_abilities:
			if not context.abilities.has(identifier):errors.append(error("actor/" + person.id + "/learned_abilities", "unknown_ability"))
		var bonus: Dictionary = Rules.new().equipment_bonuses(projected.view, person.id)
		if not bonus.ok:errors.append_array(bonus.errors)
	return errors

static func differences(before: Variant, after: Variant, path: String = "$") -> Array:
	var errors: Array = []
	if typeof(before) != typeof(after):return [error(path, "unexpected_difference")]
	if before is Dictionary:
		if before.is_typed() != after.is_typed():errors.append(error(path, "unexpected_difference"))
		for key in before:
			if not after.has(key):errors.append(error(path + "." + str(key), "unexpected_difference"))
			else:errors.append_array(differences(before[key], after[key], path + "." + str(key)))
		for key in after:
			if not before.has(key):errors.append(error(path + "." + str(key), "unexpected_difference"))
	elif before is Array:
		if before.is_typed() != after.is_typed() or before.get_typed_builtin() != after.get_typed_builtin() or before.size() != after.size():errors.append(error(path, "unexpected_difference"))
		for index in range(mini(before.size(), after.size())):errors.append_array(differences(before[index], after[index], path + "[%d]" % index))
	elif before != after:errors.append(error(path, "unexpected_difference"))
	return errors

static func compare_transition(source: Dictionary, candidate: Dictionary, source_sha256: String, context: Dictionary) -> Array:
	# 許可差分は信頼する旧入力から再計算する。候補側の台帳を許可表にしない。
	if NEW_ROOT.any(func(key: String) -> bool: return source.has(key)):
		return [error("context.source_document", "invalid_context")]
	var migration = load("res://scripts/game/equipment_save_migration.gd").new()
	var expected: Dictionary = migration.plan(source, source_sha256, context)
	if not expected.ok:return expected.errors
	if context.get("job_change_unlocked") is bool and context.job_change_unlocked:
		expected["candidate_document"] = migration._granted_candidate(expected.candidate_document)
		if source.has("first_region") and not source.progress_flags.get("job_change_unlocked", false):
			expected.candidate_document.progress_flags["job_change_unlocked"] = true
			migration._metadata(expected.candidate_document)
	return differences(expected.candidate_document, candidate)

static func validate_new(document: Dictionary, source: Dictionary, source_sha256: String, context: Dictionary) -> Array:
	var errors := equipment_layer(document, context)
	if not errors.is_empty():return errors
	return compare_transition(source, document, source_sha256, context)
