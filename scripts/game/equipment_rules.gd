extends RefCounted
## 装備所有の正規化状態に対する独立した計画器。保存・GameSession適用は行わない。
## 職解放・不可逆・戦闘中禁止・形態遷移の許可は呼出し側の責任。

const INT_MAX := 9223372036854775807
const INT_MIN := -9223372036854775807 - 1
const DATA_PATH := "res://data/equipment_rules.json"
const CATEGORIES := ["blade", "fist", "dagger", "bow", "staff"]
const SLOTS := ["weapon", "armor", "accessory"]
var _items: Dictionary = {}
var _jobs: Dictionary = {}
var _definition_errors: Array = []

func _init() -> void:
	_load_definitions()

func _error(errors: Array, target: String, code: String) -> void:
	errors.append({"target": target, "reason_code": code})

func _integer_value(value: Variant) -> bool:
	# intはfloatへ往復させない。floatの2^63はINT_MAXへ丸めず拒否する。
	if value is int:
		return true
	if not value is float:
		return false
	return is_finite(value) and value == floor(value) and value >= -9223372036854775808.0 and value < 9223372036854775808.0

func _read_definition(path: String, code: String) -> Variant:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		_error(_definition_errors, path, code)
		return null
	var parser := JSON.new()
	var status := parser.parse(file.get_as_text())
	file.close()
	if status != OK:
		_error(_definition_errors, path, code)
		return null
	return parser.data

func _load_definitions() -> void:
	# 検証中の候補は局所変数だけに置く。不正定義を半完成の状態で公開しない。
	var data: Variant = _read_definition(DATA_PATH, "invalid_definition")
	if not data is Dictionary:
		_error(_definition_errors, DATA_PATH, "invalid_definition")
		return
	if not _integer_value(data.get("equipment_rules_version")) or data.equipment_rules_version != 1 or not data.get("items") is Array or not data.get("jobs") is Dictionary or not data.get("legacy_source") is String:
		_error(_definition_errors, DATA_PATH, "invalid_definition")
		return
	if not data.legacy_source.begins_with("res://"):
		_error(_definition_errors, DATA_PATH, "invalid_definition")
		return
	var jobs: Dictionary = data.jobs.duplicate(true)
	var items: Dictionary = {}
	var source: Variant = _read_definition(data.legacy_source, "invalid_legacy_source")
	if not source is Dictionary or not source.get("weapons") is Array:
		_error(_definition_errors, data.legacy_source, "invalid_legacy_source")
		return
	var legacy: Dictionary = {}
	for item in source.weapons:
		if not item is Dictionary or not item.get("id") is String or item.id.is_empty() or not item.get("name") is String or not _integer_value(item.get("attack")):
			_error(_definition_errors, data.legacy_source, "invalid_legacy_source")
			continue
		if legacy.has(item.id):
			_error(_definition_errors, data.legacy_source, "invalid_legacy_source")
			continue
		legacy[item.id] = item
	for item in data.items:
		if not item is Dictionary or not item.get("id") is String or item.id.is_empty() or items.has(item.id):
			_error(_definition_errors, DATA_PATH, "invalid_item_id")
			continue
		var target: String = "items/" + item.id
		if not item.get("name") is String or not item.get("kind") is String or item.kind not in ["weapon", "armor", "accessory"] or not item.get("bonuses") is Dictionary or not item.get("provisional") is bool:
			_error(_definition_errors, target, "invalid_item_definition")
			continue
		var kind: String = item.kind
		if kind == "weapon" and (not item.get("weapon_category") is String or item.weapon_category not in CATEGORIES or item.has("armor_rank")):
			_error(_definition_errors, target, "invalid_weapon_definition")
		if kind == "armor" and (not _integer_value(item.get("armor_rank")) or int(item.armor_rank) not in [1, 2, 3] or item.has("weapon_category")):
			_error(_definition_errors, target, "invalid_armor_definition")
		if kind == "accessory" and (item.has("weapon_category") or item.has("armor_rank")):
			_error(_definition_errors, target, "invalid_accessory_definition")
		var allowed: Array = ["attack"] if kind == "weapon" else (["defense"] if kind == "armor" else ["hp", "mp", "defense"])
		for stat in item.bonuses:
			var value: Variant = item.bonuses[stat]
			if stat not in allowed or not _integer_value(value):
				_error(_definition_errors, target + "/bonuses/" + str(stat), "invalid_bonus")
			else:
				item.bonuses[stat] = int(value)
		if legacy.has(item.id):
			if not item.get("legacy") is Dictionary or item.legacy != legacy[item.id] or item.name != legacy[item.id].name or not _integer_value(item.bonuses.get("attack")) or item.bonuses.attack != legacy[item.id].attack or item.provisional:
				_error(_definition_errors, target, "legacy_mismatch")
		elif item.has("legacy"):
			_error(_definition_errors, target, "unknown_legacy_reference")
		items[item.id] = item.duplicate(true)
	for identifier in legacy:
		if not items.has(identifier):
			_error(_definition_errors, identifier, "missing_legacy_item")
	var observed: Dictionary = {}
	var files := DirAccess.get_files_at("res://data/jobs")
	files.sort()
	for filename in files:
		if not filename.ends_with(".json"):
			continue
		var job: Variant = _read_definition("res://data/jobs/" + filename, "invalid_job_source")
		if not job is Dictionary or not job.get("id") is String or job.id.is_empty() or not job.get("type") is String or job.type not in ["human", "monster"] or observed.has(job.id):
			_error(_definition_errors, filename, "invalid_job_source")
			continue
		observed[job.id] = job.type
	if observed.size() != 20 or jobs.size() != 20:
		_error(_definition_errors, "jobs", "job_count_mismatch")
	for identifier in jobs:
		var job: Variant = jobs[identifier]
		if not identifier is String or not job is Dictionary or not job.get("type") is String or not job.get("weapon_category") is String or not _integer_value(job.get("armor_rank")) or not _integer_value(job.get("accessory_slots")):
			_error(_definition_errors, str(identifier), "invalid_job_definition")
			continue
		if job.type == "human":
			if job.weapon_category not in CATEGORIES or int(job.armor_rank) not in [1, 2, 3] or job.accessory_slots != 2:
				_error(_definition_errors, identifier, "invalid_job_definition")
		elif job.type == "monster":
			if job.weapon_category != "" or job.armor_rank != 0 or job.accessory_slots != 3:
				_error(_definition_errors, identifier, "invalid_job_definition")
		else:
			_error(_definition_errors, identifier, "invalid_job_definition")
		if not observed.has(identifier) or observed[identifier] != job.type:
			_error(_definition_errors, identifier, "job_type_mismatch")
	for identifier in observed:
		if not jobs.has(identifier):
			_error(_definition_errors, identifier, "job_type_mismatch")
	if _definition_errors.is_empty():
		_items = items
		_jobs = jobs

func definition_errors() -> Array:
	return _definition_errors.duplicate(true)

func catalog() -> Dictionary:
	return _items.duplicate(true)

func _string_array(value: Variant) -> bool:
	if not value is Array:
		return false
	for entry in value:
		if not entry is String or entry.is_empty():
			return false
	return true

func _ability_reason(learned: Array, equipped: Array, capacity: int) -> String:
	if "twin_grip" in equipped and "two_handed" in equipped:
		return "ability_conflict"
	var seen: Array = []
	for identifier in equipped:
		if identifier not in learned:
			return "unlearned_ability"
		if identifier in seen:
			return "duplicate_ability"
		seen.append(identifier)
	return "ability_capacity" if equipped.size() > capacity else ""

func _capacity(state: Dictionary, actor: Dictionary) -> int:
	return mini(4, (3 if state.progress_flags.midgame_slots else 2) + (1 if not actor.monster_form.is_empty() else 0))

func _slot_valid(job_id: String, equipped: Array, slot: String, index: int) -> bool:
	if not _jobs.has(job_id) or index < 0 or ("twin_grip" in equipped and "two_handed" in equipped):
		return false
	var job: Dictionary = _jobs[job_id]
	if slot == "weapon":
		return job.type == "human" and index < (2 if "twin_grip" in equipped else 1)
	if slot == "armor":
		return job.type == "human" and index == 0
	return slot == "accessory" and index < int(job.accessory_slots)

func can_equip(job_id: String, equipped_abilities: Array, item_id: String, slot: String, index: int = 0) -> bool:
	if not _definition_errors.is_empty() or not _string_array(equipped_abilities) or not _items.has(item_id) or not _slot_valid(job_id, equipped_abilities, slot, index):
		return false
	var item: Dictionary = _items[item_id]
	var job: Dictionary = _jobs[job_id]
	if slot == "weapon":
		return item.kind == "weapon" and item.weapon_category == job.weapon_category
	if slot == "armor":
		return item.kind == "armor" and int(item.armor_rank) <= int(job.armor_rank)
	return item.kind == "accessory"

func _actors(state: Dictionary) -> Array:
	return state.party + state.first_region.reserve

func _actor(state: Dictionary, identifier: String) -> Dictionary:
	for person in _actors(state):
		if person.id == identifier:
			return person
	return {}

func _record_owner(owners: Dictionary, stock: Dictionary, instance: Variant, target: String, errors: Array) -> void:
	if not instance is String or instance.is_empty():
		_error(errors, target, "invalid_instance_type")
	elif not stock.has(instance):
		_error(errors, target, "unknown_instance")
	elif owners.has(instance):
		_error(errors, target, "duplicate_owner")
	else:
		owners[instance] = target

func validate_equipment_state(state: Dictionary) -> Array:
	var errors: Array = definition_errors()
	if not errors.is_empty():
		return errors
	if not state.get("equipment_rules_version") is int or state.equipment_rules_version != 1:
		_error(errors, "equipment_rules_version", "invalid_version")
	if not state.get("equipment_stock") is Dictionary or not state.equipment_stock.get("instances") is Dictionary or not state.equipment_stock.get("bag") is Array:
		_error(errors, "equipment_stock", "invalid_stock_type")
	if not state.get("party") is Array or not state.get("first_region") is Dictionary or not state.first_region.get("reserve") is Array:
		_error(errors, "party/first_region.reserve", "invalid_party_type")
	if not state.get("progress_flags") is Dictionary or not state.progress_flags.get("midgame_slots") is bool:
		_error(errors, "progress_flags.midgame_slots", "invalid_capacity_input")
	if state.get("integrated") is Dictionary and state.integrated.has("armory"):
		_error(errors, "integrated.armory", "mixed_legacy_state")
	if not errors.is_empty():
		return errors
	var stock: Dictionary = state.equipment_stock.instances
	var owners: Dictionary = {}
	for instance in stock:
		if not instance is String or instance.is_empty() or not stock[instance] is String or not _items.has(stock[instance]):
			_error(errors, "instances/" + str(instance), "unknown_item")
	for index in range(state.equipment_stock.bag.size()):
		_record_owner(owners, stock, state.equipment_stock.bag[index], "bag/%d" % index, errors)
	var ids: Array = []
	for person in _actors(state):
		if not person is Dictionary or not person.get("id") is String or person.id.is_empty():
			_error(errors, "actors", "invalid_actor")
			continue
		var target: String = "actor/" + person.id
		if person.id in ids:
			_error(errors, target, "duplicate_actor")
		ids.append(person.id)
		if not person.get("job_id") is String or not _jobs.has(person.job_id):
			_error(errors, target, "unknown_job")
		if not person.get("monster_form") is String or (not person.monster_form.is_empty() and (not _jobs.has(person.monster_form) or _jobs[person.monster_form].type != "monster")):
			_error(errors, target, "invalid_monster_form")
		if not _string_array(person.get("learned_abilities")) or not _string_array(person.get("equipped_abilities")):
			_error(errors, target, "invalid_ability_type")
		if person.get("integrated") is Dictionary and person.integrated.has("weapons"):
			_error(errors, target, "mixed_legacy_state")
		var equipment: Variant = person.get("equipment")
		if not equipment is Dictionary or equipment.size() != 3 or not equipment.get("weapons") is Array or not equipment.get("armor") is String or not equipment.get("accessories") is Array or equipment.accessories.size() != 3:
			_error(errors, target, "invalid_equipment_shape")
			continue
		if not person.get("job_id") is String or not _jobs.has(person.job_id) or not _string_array(person.get("equipped_abilities")) or not _string_array(person.get("learned_abilities")) or not person.get("monster_form") is String:
			continue
		var ability_reason := _ability_reason(person.learned_abilities, person.equipped_abilities, _capacity(state, person))
		if not ability_reason.is_empty():
			_error(errors, target, ability_reason)
		if equipment.weapons.size() > (2 if "twin_grip" in person.equipped_abilities else 1):
			_error(errors, target + "/weapons", "invalid_slot")
		for slot in SLOTS:
			var entries: Array = equipment.weapons if slot == "weapon" else ([equipment.armor] if slot == "armor" else equipment.accessories)
			for index in range(entries.size()):
				var instance: Variant = entries[index]
				var location: String = target + "/" + slot + "/%d" % index
				if instance is String and instance.is_empty() and slot != "weapon":
					continue
				_record_owner(owners, stock, instance, location, errors)
				if instance is String and stock.has(instance) and stock[instance] is String and not can_equip(person.job_id, person.equipped_abilities, stock[instance], slot, index):
					_error(errors, location, "wrong_category")
	for instance in stock:
		if not owners.has(instance):
			_error(errors, "instances/" + str(instance), "orphan_instance")
	return errors

func _locations(state: Dictionary) -> Dictionary:
	var result: Dictionary = {}
	for instance in state.equipment_stock.bag:
		result[instance] = "bag"
	for group in ["party", "reserve"]:
		var people: Array = state.party if group == "party" else state.first_region.reserve
		for person in people:
			for slot in SLOTS:
				var entries: Array = person.equipment.weapons if slot == "weapon" else ([person.equipment.armor] if slot == "armor" else person.equipment.accessories)
				for index in range(entries.size()):
					if not entries[index].is_empty():
						result[entries[index]] = "%s/%s/%s/%d" % [group, person.id, slot, index]
	return result

func _owned(equipment: Dictionary) -> Array:
	var result: Array = equipment.weapons.duplicate()
	if not equipment.armor.is_empty():
		result.append(equipment.armor)
	for instance in equipment.accessories:
		if not instance.is_empty():
			result.append(instance)
	return result

func _replace_bag(candidate: Dictionary, old: Dictionary, new_equipment: Dictionary) -> void:
	var old_owned := _owned(old)
	var new_owned := _owned(new_equipment)
	for instance in new_owned:
		candidate.equipment_stock.bag.erase(instance)
	for instance in old_owned:
		if instance not in new_owned:
			candidate.equipment_stock.bag.append(instance)

func _select(pool: Array, old_order: Array, state: Dictionary, person: Dictionary, slot: String, count: int) -> Array:
	var choices: Array = []
	for instance in pool:
		if can_equip(person.job_id, person.equipped_abilities, state.equipment_stock.instances[instance], slot, 0):
			choices.append(instance)
	var stat: String = "attack" if slot == "weapon" else "defense"
	choices.sort_custom(func(left: String, right: String) -> bool:
		var left_item: Dictionary = _items[state.equipment_stock.instances[left]]
		var right_item: Dictionary = _items[state.equipment_stock.instances[right]]
		var left_score: int = left_item.bonuses.get(stat, 0)
		var right_score: int = right_item.bonuses.get(stat, 0)
		if left_score != right_score:
			return left_score > right_score
		var left_old: int = old_order.find(left)
		var right_old: int = old_order.find(right)
		if left_old != right_old:
			return left_old >= 0 and (right_old < 0 or left_old < right_old)
		return left_item.id < right_item.id if left_item.id != right_item.id else left < right
	)
	return choices.slice(0, count)

func _failure(code: String, errors: Array = []) -> Dictionary:
	return {"ok": false, "reason_code": code, "moves": [], "errors": errors}

func _request_valid(request: Dictionary) -> bool:
	var kind: Variant = request.get("kind")
	if not kind is String:
		return false
	var allowed: Array
	if kind == "equip":
		allowed = ["kind", "slot", "index", "instance_id"]
		if not request.get("slot") in SLOTS or not request.get("index") is int or not request.get("instance_id") is String:
			return false
	elif kind == "set_abilities":
		allowed = ["kind", "equipped_abilities"]
		if not _string_array(request.get("equipped_abilities")):
			return false
	elif kind == "change_job":
		allowed = ["kind", "job_id", "monster_form", "equipped_abilities"]
		if not request.get("job_id") is String or (request.has("monster_form") and not request.monster_form is String) or (request.has("equipped_abilities") and not _string_array(request.equipped_abilities)):
			return false
	else:
		return false
	for key in request:
		if key not in allowed:
			return false
	return true

func plan_equipment_change(state: Dictionary, actor_id: String, request: Dictionary) -> Dictionary:
	var errors := validate_equipment_state(state)
	if not errors.is_empty():
		return _failure("invalid_state", errors)
	if not _request_valid(request):
		return _failure("invalid_request")
	if _actor(state, actor_id).is_empty():
		return _failure("unknown_actor")
	var candidate: Dictionary = state.duplicate(true)
	var person := _actor(candidate, actor_id)
	var old: Dictionary = person.equipment.duplicate(true)
	if request.kind == "change_job":
		if not _jobs.has(request.job_id):
			return _failure("unknown_job")
		person.job_id = request.job_id
		if request.has("monster_form"):
			if not request.monster_form.is_empty() and (not _jobs.has(request.monster_form) or _jobs[request.monster_form].type != "monster"):
				return _failure("invalid_monster_form")
			person.monster_form = request.monster_form
		# 後続が整理済み能力を明示できる。省略時は既存順の先頭を新容量まで保持。
		person.equipped_abilities = request.equipped_abilities.duplicate(true) if request.has("equipped_abilities") else person.equipped_abilities.slice(0, _capacity(candidate, person))
	elif request.kind == "set_abilities":
		person.equipped_abilities = request.equipped_abilities.duplicate(true)
	var ability_reason := _ability_reason(person.learned_abilities, person.equipped_abilities, _capacity(candidate, person))
	if not ability_reason.is_empty():
		return _failure(ability_reason)
	if request.kind == "change_job":
		var pool: Array = candidate.equipment_stock.bag.duplicate() + _owned(old)
		var weapon_count: int = 2 if "twin_grip" in person.equipped_abilities else 1
		person.equipment.weapons = _select(pool, old.weapons, candidate, person, "weapon", weapon_count)
		var armor: Array = _select(pool, [old.armor], candidate, person, "armor", 1)
		person.equipment.armor = "" if armor.is_empty() else armor[0]
		if _jobs[person.job_id].type == "human" or _jobs[_actor(state, actor_id).job_id].type == "human":
			person.equipment.accessories[2] = ""
	elif request.kind == "set_abilities":
		if "twin_grip" not in person.equipped_abilities:
			person.equipment.weapons = person.equipment.weapons.slice(0, 1)
	else:
		var reason := _manual(candidate, person, request)
		if not reason.is_empty():
			return _failure(reason)
	_replace_bag(candidate, old, person.equipment)
	errors = validate_equipment_state(candidate)
	if not errors.is_empty():
		return _failure("invalid_candidate", errors)
	var before := _locations(state)
	var after := _locations(candidate)
	var moves: Array = []
	var instances: Array = before.keys()
	instances.sort()
	for instance in instances:
		if before[instance] != after[instance]:
			moves.append({"instance_id": instance, "from": before[instance], "to": after[instance]})
	var stats_before := equipment_bonuses(state, actor_id)
	var stats_after := equipment_bonuses(candidate, actor_id)
	if not stats_before.ok:
		return _failure(stats_before.reason_code, stats_before.errors)
	if not stats_after.ok:
		return _failure(stats_after.reason_code, stats_after.errors)
	return {"ok": true, "reason_code": "ok", "candidate": candidate, "moves": moves, "stats_before": stats_before.bonuses, "stats_after": stats_after.bonuses}

func _manual(state: Dictionary, person: Dictionary, request: Dictionary) -> String:
	var slot: String = request.slot
	var index: int = request.index
	var instance: String = request.instance_id
	if not _slot_valid(person.job_id, person.equipped_abilities, slot, index):
		return "invalid_slot"
	var entries: Array = person.equipment.weapons.duplicate() if slot == "weapon" else ([person.equipment.armor] if slot == "armor" else person.equipment.accessories.duplicate())
	if slot == "weapon" and index > entries.size():
		return "invalid_slot"
	if not instance.is_empty():
		if not state.equipment_stock.instances.has(instance):
			return "unknown_instance"
		if instance not in state.equipment_stock.bag and instance not in _owned(person.equipment):
			return "owned_by_other"
		if not can_equip(person.job_id, person.equipped_abilities, state.equipment_stock.instances[instance], slot, index):
			return "wrong_category"
	var previous: String = entries[index] if index < entries.size() else ""
	var source_index: int = entries.find(instance) if not instance.is_empty() else -1
	if source_index >= 0:
		entries[source_index] = previous
	if index == entries.size():
		entries.append(instance)
	else:
		entries[index] = instance
	if slot == "weapon":
		person.equipment.weapons = entries.filter(func(value: String) -> bool: return not value.is_empty())
	elif slot == "armor":
		person.equipment.armor = entries[0]
	else:
		person.equipment.accessories = entries
	return ""

func equipment_bonuses(state: Dictionary, actor_id: String) -> Dictionary:
	var errors := validate_equipment_state(state)
	if not errors.is_empty():
		return _failure("invalid_state", errors)
	var person := _actor(state, actor_id)
	if person.is_empty():
		return _failure("unknown_actor")
	var bonuses := {"hp": 0, "mp": 0, "attack": 0, "defense": 0}
	for instance in _owned(person.equipment):
		var item: Dictionary = _items[state.equipment_stock.instances[instance]]
		# 二刀流の副武器は各打の差替え用。基礎攻撃へ二重加算しない。
		if item.kind == "weapon" and instance != person.equipment.weapons[0]:
			continue
		for stat in item.bonuses:
			var value: int = item.bonuses[stat]
			var previous: int = bonuses[stat]
			# 加算そのものを行う前にintの表現可能域を検査する。
			if (value > 0 and previous > INT_MAX - value) or (value < 0 and previous < INT_MIN - value):
				_error(errors, "bonuses/" + stat, "numeric_overflow")
				return _failure("numeric_overflow", errors)
			bonuses[stat] = previous + value
	return {"ok": true, "reason_code": "ok", "bonuses": bonuses}

func two_handed_active(state: Dictionary, actor_id: String) -> bool:
	if not validate_equipment_state(state).is_empty():
		return false
	var person := _actor(state, actor_id)
	if person.is_empty() or _jobs[person.job_id].type != "human" or "two_handed" not in person.equipped_abilities or "twin_grip" in person.equipped_abilities or person.equipment.weapons.size() != 1:
		return false
	return _items[state.equipment_stock.instances[person.equipment.weapons[0]]].weapon_category == "blade"
