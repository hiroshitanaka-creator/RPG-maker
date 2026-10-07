extends RefCounted
## 採用済みpolicyの未接続S1。入力・GameSession・計測・履歴・保存I/Oを変更しない。
const Validation = preload("res://scripts/game/equipment_save_validation.gd")
const Rules = preload("res://scripts/game/equipment_rules.gd")
const POLICY = "equipment-q1a-q2a-q3a-v1"
const COMMON = ["practice_blade", "cloth_fist_wrap", "iron_dagger", "practice_bow", "practice_staff", "cotton_travel_clothes", "layered_leather_vest", "vitality_braid", "thought_clasp", "guard_stitched_bracelet"]
const START_WEAPONS = ["practice_blade", "cloth_fist_wrap", "iron_dagger", "practice_bow", "practice_staff"]
const ARMORS = ["cotton_travel_clothes", "layered_leather_vest", "iron_plate_armor"]

static func migration_id(source_sha256: String) -> String:
	return JSON.stringify(["equipment-migration-v1", source_sha256, POLICY, 1]).sha256_text()

static func _failure(code: String, errors: Array) -> Dictionary:
	return {"ok": false, "reason_code": code, "errors": errors}

func plan(document: Dictionary, source_sha256: String, context: Dictionary) -> Dictionary:
	if source_sha256.length() != 64 or not source_sha256.is_valid_hex_number(false) or source_sha256 != source_sha256.to_lower():
		return _failure("invalid_source", [Validation.error("source_sha256", "invalid_source")])
	var new_keys := Validation.NEW_ROOT.any(func(key: String) -> bool: return document.has(key))
	if new_keys:
		if not document.get("equipment_rules_version") is int or document.equipment_rules_version != 1:
			return _failure("unsupported_version", [Validation.error("$.equipment_rules_version", "unsupported_version")])
		if not context.get("source_document") is Dictionary:
			return _failure("invalid_context", [Validation.error("context.source_document", "invalid_context")])
		var errors := Validation.validate_new(document, context.source_document, source_sha256, context)
		if not errors.is_empty():return _failure(errors[0].reason_code, errors)
		return _failure("already_migrated", [Validation.error("$.equipment_migration", "already_migrated")])
	var errors := Validation.validate_legacy(document, context)
	if not errors.is_empty():return _failure(errors[0].reason_code, errors)
	var result := _build(document, source_sha256, context)
	errors = Validation.equipment_layer(result.candidate_document, context)
	if not errors.is_empty():return _failure(errors[0].reason_code, errors)
	return result

static func _people(document: Dictionary) -> Array:
	var people: Array = []
	for group in ["party", "reserve"]:
		var array: Array = document.party if group == "party" else document.get("first_region", {}).get("reserve", [])
		for index in range(array.size()):people.append({"actor": array[index], "group": group, "index": index})
	people.sort_custom(func(left: Dictionary, right: Dictionary) -> bool: return left.actor.id < right.actor.id)
	return people

static func _add(document: Dictionary, audit: Dictionary, item: String, reason: String, actor_id: String = "") -> String:
	var identifier := "eqm_%s_%06d" % [document.equipment_migration.migration_id, document.equipment_stock.instances.size() + 1]
	document["equipment_stock"]["instances"][identifier] = item
	document.equipment_stock.bag.append(identifier)
	audit.generated.append({"instance_id": identifier, "item_id": item, "reason": reason, "actor_id": actor_id})
	return identifier

static func _common(document: Dictionary, audit: Dictionary) -> void:
	for item in COMMON:_add(document, audit, item, "common_set")
	document["equipment_grants"]["common_set"] = "granted"

static func _metadata(document: Dictionary) -> void:
	if document.has("_saved_value_types"):
		document.erase("_saved_value_types")
		document["_saved_value_types"] = SavedValueTypes.describe(document)

func _build(source: Dictionary, source_sha256: String, context: Dictionary) -> Dictionary:
	var candidate := source.duplicate(true)
	var legacy := {"source_format": source.format_version, "target_format": 2, "actors": [], "world_created": {}, "mastery_initialized": []}
	if source.format_version == 1:
		candidate["format_version"] = 2
		candidate["integrated"] = IntegratedProgression.initial_world()
		legacy["world_created"] = candidate.integrated.duplicate(true)
		for entry in _people(candidate):
			var before: Dictionary = entry.actor.duplicate(true)
			var after := IntegratedProgression.upgrade_actor(before, context.legacy_session.jobs)
			# 配列そのものの型・位置を保持する。
			var people: Array = candidate.party if entry.group == "party" else candidate.first_region.reserve
			people[entry["index"]] = after
			legacy.actors.append({"actor_id": before.id, "group": entry.group, "index": entry.index, "jp_before": before.jp.duplicate(true), "jp_after": after.jp.duplicate(true), "integrated_created": after.integrated.duplicate(true)})
	# 旧形式2の未記録修練だけを既存upgrade_rulesと同じ初期値にする。
	# JP換算と忘却はここでは行わない。記録済みのcountsは保持する。
	if not candidate.integrated.has("mastery_rules_version"):
		candidate.integrated["mastery_rules_version"] = 1
		for entry in _people(candidate):
			entry.actor.integrated["mastery"] = JobMastery.initial(entry.actor.mastered_jobs)
			legacy.mastery_initialized.append({"actor_id": entry.actor.id, "group": entry.group, "index": entry.index, "mastery": entry.actor.integrated.mastery.duplicate(true)})
	var audit := {"source_armory": source.get("integrated", {}).get("armory", []).duplicate(true), "actor_slots": [], "generated": [], "returned": [], "learned_added": []}
	candidate["equipment_rules_version"] = 1
	candidate["equipment_stock"] = {"instances": {}, "bag": []}
	candidate["equipment_grants"] = {"version": 1, "policy_id": POLICY, "common_set": "pending", "actor_initial": {}, "actor_support": {}}
	candidate["equipment_migration"] = {"version": 1, "migration_id": migration_id(source_sha256), "source_sha256": source_sha256, "source_format": source.format_version, "policy_id": POLICY, "catalog_revision": 1, "source_build": context.get("source_build", ""), "source_build_reason": "provided" if not context.get("source_build", "").is_empty() else "unknown", "legacy_format_audit": legacy, "equipment_audit": audit}
	var people := _people(candidate)
	var slots: Dictionary = {}
	var occurrences: Dictionary = {}
	for entry in people:
		var actor: Dictionary = entry.actor
		var old: Array = actor.integrated.weapons.duplicate(true) if source.format_version == 2 else []
		var instances: Array = []
		var supplied: Array = old if source.format_version == 2 else ["practice_blade"]
		for item in supplied:
			instances.append(_add(candidate, audit, item, "legacy_slot" if source.format_version == 2 else "format1_supply", actor.id))
			occurrences[item] = occurrences.get(item, 0) + 1
		slots[actor["id"]] = instances
		audit.actor_slots.append({"actor_id": actor.id, "group": entry.group, "index": entry.index, "weapons": old, "instances": instances.duplicate(true)})
		actor.integrated.erase("weapons")
		actor["equipment"] = {"weapons": [], "armor": "", "accessories": ["", "", ""]}
		candidate["equipment_grants"]["actor_support"][actor["id"]] = []
	if source.format_version == 2:
		var released: Array = audit.source_armory.duplicate()
		released.sort()
		for item in released:
			if not occurrences.has(item):_add(candidate, audit, item, "legacy_unheld")
	else:
		for item in ["practice_staff", "practice_bow"]:_add(candidate, audit, item, "format1_supply")
	candidate.integrated.erase("armory")
	var rules = Rules.new()
	var catalog: Dictionary = rules.catalog()
	# 全人物の合法従前を先に確保し、不適合品だけ袋へ残す。
	for entry in people:
		var actor: Dictionary = entry.actor
		for index in range(slots[actor.id].size()):
			var identifier: String = slots[actor.id][index]
			var item: String = candidate.equipment_stock.instances[identifier]
			if rules.can_equip(actor.job_id, actor.equipped_abilities, item, "weapon", index):
				candidate.equipment_stock.bag.erase(identifier)
			else:
				slots[actor["id"]][index] = ""
				audit.returned.append({"instance_id": identifier, "item_id": item, "actor_id": actor.id, "slot": "weapon", "index": index})
	for entry in people:
		var actor: Dictionary = entry.actor
		var held: Array = slots[actor.id]
		if held.is_empty() or held[0].is_empty():
			var choice := _choose(candidate, actor, rules, catalog, "weapon")
			if choice.is_empty():
				for item in START_WEAPONS:
					if rules.can_equip(actor.job_id, actor.equipped_abilities, item, "weapon"):
						choice = _support(candidate, audit, actor.id, item)
						break
			if not choice.is_empty():
				candidate.equipment_stock.bag.erase(choice)
				if held.is_empty():held.append(choice)
				else:held[0] = choice
		actor["equipment"]["weapons"] = held.filter(func(identifier: String) -> bool: return not identifier.is_empty())
		var armor := _choose(candidate, actor, rules, catalog, "armor")
		if armor.is_empty():
			for index in range(ARMORS.size() - 1, -1, -1):
				if rules.can_equip(actor.job_id, actor.equipped_abilities, ARMORS[index], "armor"):
					armor = _support(candidate, audit, actor.id, ARMORS[index])
					break
		if not armor.is_empty():
			candidate.equipment_stock.bag.erase(armor)
			actor["equipment"]["armor"] = armor
		if "warrior" in actor.mastered_jobs and "two_handed" not in actor.learned_abilities:
			actor.learned_abilities.append("two_handed")
			audit.learned_added.append({"actor_id": actor.id, "ability_id": "two_handed", "reason": "warrior_master"})
	if not source.has("first_region") or source.progress_flags.get("job_change_unlocked", false):_common(candidate, audit)
	_metadata(candidate)
	return {"ok": true, "reason_code": "ok", "candidate_document": candidate, "migration_id": candidate.equipment_migration.migration_id, "legacy_format_audit": legacy.duplicate(true), "equipment_audit": audit.duplicate(true), "errors": [], "guaranteed_layer": "equipment_and_transition_S1"}

static func _support(document: Dictionary, audit: Dictionary, actor_id: String, item: String) -> String:
	var identifier := _add(document, audit, item, "migration_support", actor_id)
	document.equipment_grants.actor_support[actor_id].append({"reason": "migration_support", "item_id": item, "instance_id": identifier})
	return identifier

static func _choose(document: Dictionary, actor: Dictionary, rules: RefCounted, catalog: Dictionary, slot: String) -> String:
	var choices: Array = []
	for identifier in document.equipment_stock.bag:
		if rules.can_equip(actor.job_id, actor.equipped_abilities, document.equipment_stock.instances[identifier], slot):choices.append(identifier)
	var stat := "attack" if slot == "weapon" else "defense"
	choices.sort_custom(func(left: String, right: String) -> bool:
		var li: String = document.equipment_stock.instances[left]
		var ri: String = document.equipment_stock.instances[right]
		var ls: int = catalog[li].bonuses.get(stat, 0)
		var rs: int = catalog[ri].bonuses.get(stat, 0)
		if ls != rs:return ls > rs
		return li < ri if li != ri else left < right
	)
	return "" if choices.is_empty() else choices[0]

func grant_common(document: Dictionary, source: Dictionary, source_sha256: String, context: Dictionary) -> Dictionary:
	# 解放済みの事実を呼出し側が明示する。通常解放ハンドラとは未接続。
	if not context.get("job_change_unlocked") is bool or not context.job_change_unlocked:
		return _failure("grant_not_unlocked", [Validation.error("context.job_change_unlocked", "grant_not_unlocked")])
	var expected := plan(source, source_sha256, context)
	if not expected.ok:return expected
	var granted := _granted_candidate(expected.candidate_document)
	if source.has("first_region") and not source.progress_flags.get("job_change_unlocked", false):
		if not document.get("progress_flags") is Dictionary or not document.progress_flags.get("job_change_unlocked") is bool or not document.progress_flags.job_change_unlocked:
			return _failure("grant_not_unlocked", [Validation.error("$.progress_flags.job_change_unlocked", "grant_not_unlocked")])
		granted.progress_flags["job_change_unlocked"] = true
		_metadata(granted)
	var errors := Validation.differences(granted, document)
	if errors.is_empty():return _failure("already_granted", [Validation.error("$.equipment_grants.common_set", "already_granted")])
	var before_context := context.duplicate()
	before_context.erase("job_change_unlocked")
	var before_document := document.duplicate(true)
	if source.has("first_region") and not source.progress_flags.get("job_change_unlocked", false):
		if source.progress_flags.has("job_change_unlocked"):before_document.progress_flags["job_change_unlocked"] = source.progress_flags.job_change_unlocked
		else:before_document.progress_flags.erase("job_change_unlocked")
		_metadata(before_document)
	errors = Validation.validate_new(before_document, source, source_sha256, before_context)
	if not errors.is_empty():return _failure(errors[0].reason_code, errors)
	errors = Validation.equipment_layer(granted, context)
	if not errors.is_empty():return _failure(errors[0].reason_code, errors)
	return {"ok": true, "reason_code": "ok", "candidate_document": granted, "equipment_audit": granted.equipment_migration.equipment_audit.duplicate(true), "errors": []}

func _granted_candidate(document: Dictionary) -> Dictionary:
	var candidate := document.duplicate(true)
	if candidate.equipment_grants.common_set == "pending":_common(candidate, candidate.equipment_migration.equipment_audit)
	_metadata(candidate)
	return candidate
