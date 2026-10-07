extends SceneTree

const Rules = preload("res://scripts/game/equipment_rules.gd")
const HUMAN = {
	"warrior": ["blade", 3], "knight": ["blade", 3], "swordsman": ["blade", 2],
	"martial_artist": ["fist", 1], "thief": ["dagger", 2], "hunter": ["bow", 2],
	"apothecary": ["dagger", 1], "bard": ["dagger", 1], "priest": ["staff", 1],
	"mage": ["staff", 1], "sage": ["staff", 1], "shaman": ["staff", 1]
}
const MONSTER = ["slime", "beast", "undead", "bird", "plant", "shell", "spirit", "dragon"]
const WEAPONS = {"blade": "practice_blade", "fist": "cloth_fist_wrap", "dagger": "iron_dagger", "bow": "practice_bow", "staff": "practice_staff"}
const ARMORS = ["cotton_travel_clothes", "layered_leather_vest", "iron_plate_armor"]
var failures: Array[String] = []
var checks: int = 0
var transitions: int = 0
var rules: RefCounted

func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures.append(label)

func actor(identifier: String, job: String) -> Dictionary:
	return {"id": identifier, "job_id": job, "monster_form": "", "learned_abilities": ["twin_grip", "two_handed", "power_strike"], "equipped_abilities": [], "equipment": {"weapons": [], "armor": "", "accessories": ["", "", ""]}, "hp": 0, "mp": 1}

func fixture(job: String = "warrior") -> Dictionary:
	return {"equipment_rules_version": 1, "equipment_stock": {"instances": {}, "bag": []}, "party": [actor("a", job), actor("b", "warrior")], "first_region": {"reserve": [actor("r", "warrior")]}, "progress_flags": {"midgame_slots": false}, "unrelated": {"history": [7, {"nested": [1, 2]}]}}

func add(state: Dictionary, instance: String, item: String) -> void:
	state.equipment_stock.instances[instance] = item
	state.equipment_stock.bag.append(instance)

func wear(state: Dictionary, instance: String, item: String, slot: String, index: int = 0, who: Dictionary = {}) -> void:
	add(state, instance, item)
	state.equipment_stock.bag.erase(instance)
	var person: Dictionary = state.party[0] if who.is_empty() else who
	if slot == "weapon":
		person.equipment.weapons.append(instance)
	elif slot == "armor":
		person.equipment.armor = instance
	else:
		person.equipment.accessories[index] = instance

func plan(state: Dictionary, request: Dictionary, label: String, identifier: String = "a") -> Dictionary:
	var before: Dictionary = state.duplicate(true)
	var request_before: Dictionary = request.duplicate(true)
	var result: Dictionary = rules.plan_equipment_change(state, identifier, request)
	check(state == before and request == request_before, label + ": stateとrequest入力不変")
	if result.ok:
		check(rules.validate_equipment_state(result.candidate).is_empty(), label + ": 候補有効")
		check(result.candidate.equipment_stock.instances == before.equipment_stock.instances, label + ": 個体台帳不変")
		check(result.candidate.party[1] == before.party[1] and result.candidate.first_region.reserve == before.first_region.reserve, label + ": 他人とreserve不変")
		check(result.candidate.party[0].hp == 0 and result.candidate.party[0].mp == 1, label + ": HP/MP不変")
		check(result.candidate.unrelated == before.unrelated, label + ": 非装備情報不変")
		result.candidate.unrelated.history[1].nested.append(3)
		check(state == before, label + ": 候補に共有参照なし")
		result.candidate.unrelated = before.unrelated.duplicate(true)
		result.candidate.party[0].equipped_abilities.append("mutated")
		check(state == before and request == request_before, label + ": 能力配列も共有なし")
		result.candidate.party[0].equipped_abilities.pop_back()
	else:
		check(not result.has("candidate"), label + ": 失敗時候補なし")
	return result

func reject(state: Dictionary, request: Dictionary, reason: String, label: String, identifier: String = "a") -> void:
	var result := plan(state, request, label, identifier)
	check(not result.ok and result.reason_code == reason, label + ": " + reason)

func invalid(state: Dictionary, label: String) -> void:
	var before := state.duplicate(true)
	var errors: Array = rules.validate_equipment_state(state)
	check(not errors.is_empty(), label + ": 検証拒否")
	if not errors.is_empty():
		check(errors[0].has("target") and errors[0].has("reason_code"), label + ": 対象と理由")
	check(state == before, label + ": 検証も入力不変")
	reject(state, {"kind": "change_job", "job_id": "warrior"}, "invalid_state", label)

func test_catalog() -> void:
	check(rules.definition_errors().is_empty(), "定義の整合")
	var catalog: Dictionary = rules.catalog()
	check(catalog.size() == 14, "既存6・新8品")
	var legacy: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/integrated_rules.json")).weapons
	var names := {"practice_blade": "稽古剣", "practice_staff": "術杖", "practice_bow": "稽古弓", "iron_blade": "補強剣", "twin_blade": "軽双剣", "long_bow": "封緘の長弓"}
	var attacks := {"practice_blade": 0, "practice_staff": -2, "practice_bow": -1, "iron_blade": 3, "twin_blade": 1, "long_bow": 3}
	for item in legacy:
		check(catalog[item.id].legacy == item, "旧原本との完全照合 " + item.id)
		check(item.name == names[item.id] and item.attack == attacks[item.id], "旧6品の固定名・値 " + item.id)
	check(catalog.long_bow.legacy.on_hit == {"kind": "seal"}, "封緘効果保持")
	var adopted := {"cloth_fist_wrap": "布巻き拳帯", "iron_dagger": "鉄の短剣", "cotton_travel_clothes": "綿の旅服", "layered_leather_vest": "革合わせの胴着", "iron_plate_armor": "鉄片の胴鎧", "vitality_braid": "活力の組紐", "thought_clasp": "思索の留め具", "guard_stitched_bracelet": "守り縫いの腕輪"}
	for identifier in adopted:
		check(catalog[identifier].name == adopted[identifier] and catalog[identifier].provisional == true, "採用名・仮値 " + identifier)
	for item in catalog.values():
		check(item.name != "鉄の小短剣" and item.name != "不屈の結び輪" and not item.has("immunity"), "未採用品なし " + item.id)
	catalog.practice_blade.legacy.tags.append("changed")
	check(rules.catalog().practice_blade.legacy.tags == ["melee"], "カタログ共有参照なし")

func test_permissions() -> void:
	var jobs: Array = HUMAN.keys() + MONSTER
	for job in jobs:
		for category in WEAPONS:
			check(rules.can_equip(job, [], WEAPONS[category], "weapon", 0) == (HUMAN.has(job) and HUMAN[job][0] == category), job + ": 武器 " + category)
			check(not rules.can_equip(job, [], WEAPONS[category], "weapon", 1), job + ": 二刀流なし2枠目")
			check(rules.can_equip(job, ["twin_grip"], WEAPONS[category], "weapon", 1) == (HUMAN.has(job) and HUMAN[job][0] == category), job + ": 二刀流2枠目")
		for rank in range(1, 4):
			check(rules.can_equip(job, [], ARMORS[rank - 1], "armor", 0) == (HUMAN.has(job) and rank <= HUMAN[job][1]), job + ": 防具%d" % rank)
		for index in range(4):
			check(rules.can_equip(job, [], "vitality_braid", "accessory", index) == (index < (2 if HUMAN.has(job) else 3)), job + ": 装飾%d" % index)
	check(not rules.can_equip("missing", [], "practice_blade", "weapon", 0), "未知職不可")
	check(not rules.can_equip("warrior", [], "missing", "weapon", 0), "未知品不可")
	check(not rules.can_equip("warrior", ["twin_grip", "two_handed"], "practice_blade", "weapon", 0), "可否APIも排他違反不可")

func test_transitions() -> void:
	var jobs: Array = HUMAN.keys() + MONSTER
	for source in jobs:
		for target in jobs:
			var state := fixture(source)
			for category in WEAPONS:
				add(state, "pool_" + category, WEAPONS[category])
			for rank in range(1, 4):
				add(state, "pool_armor%d" % rank, ARMORS[rank - 1])
			wear(state, "acc1", "vitality_braid", "accessory", 0)
			wear(state, "acc2", "thought_clasp", "accessory", 1)
			if HUMAN.has(source):
				wear(state, "old_weapon", WEAPONS[HUMAN[source][0]], "weapon")
				wear(state, "old_armor", ARMORS[HUMAN[source][1] - 1], "armor")
			else:
				wear(state, "acc3", "guard_stitched_bracelet", "accessory", 2)
			wear(state, "other_best", "iron_blade", "weapon", 0, state.party[1])
			wear(state, "reserve_best", "iron_blade", "weapon", 0, state.first_region.reserve[0])
			var result := plan(state, {"kind": "change_job", "job_id": target}, source + "→" + target)
			check(result.ok, "全切替成功 " + source + "→" + target)
			if not result.ok:
				continue
			transitions += 1
			var expected_weapon: Array = []
			var expected_armor := ""
			if HUMAN.has(target):
				expected_weapon = ["old_weapon" if HUMAN.has(source) and HUMAN[source][0] == HUMAN[target][0] else "pool_" + HUMAN[target][0]]
				expected_armor = "old_armor" if HUMAN.has(source) and HUMAN[source][1] == HUMAN[target][1] else "pool_armor%d" % HUMAN[target][1]
			var expected_acc := ["acc1", "acc2", "acc3" if not HUMAN.has(source) and not HUMAN.has(target) else ""]
			check(result.candidate.party[0].equipment == {"weapons": expected_weapon, "armor": expected_armor, "accessories": expected_acc}, "固定期待枠 " + source + "→" + target)
			var expected_bag: Array = state.equipment_stock.instances.keys()
			for instance in expected_weapon + expected_acc + [expected_armor, "other_best", "reserve_best"]:
				expected_bag.erase(instance)
			expected_bag.sort()
			var observed: Array = result.candidate.equipment_stock.bag.duplicate()
			observed.sort()
			check(observed == expected_bag, "固定期待袋 " + source + "→" + target)
	check(transitions == 400, "400切替を省略なしで実行")

func test_selection() -> void:
	var state := fixture()
	wear(state, "old", "practice_blade", "weapon")
	add(state, "strong", "iron_blade")
	var result := plan(state, {"kind": "change_job", "job_id": "knight"}, "袋の強い品")
	check(result.ok and result.candidate.party[0].equipment.weapons == ["strong"] and result.candidate.equipment_stock.bag == ["old"], "強い袋の品・返却")
	check(result.moves == [{"instance_id": "old", "from": "party/a/weapon/0", "to": "bag"}, {"instance_id": "strong", "from": "bag", "to": "party/a/weapon/0"}], "移動明細固定期待")
	state = fixture("priest")
	add(state, "negative", "practice_staff")
	result = plan(state, {"kind": "change_job", "job_id": "mage"}, "負値合法実物")
	check(result.ok and result.candidate.party[0].equipment.weapons == ["negative"], "術杖は空より選択")
	state = fixture()
	result = plan(state, {"kind": "change_job", "job_id": "warrior"}, "候補なし")
	check(result.ok and result.candidate.party[0].equipment.weapons == [] and result.candidate.party[0].equipment.armor == "", "候補なしだけ空")
	state = fixture()
	state.party[0].equipped_abilities = ["twin_grip"]
	wear(state, "z_old0", "iron_blade", "weapon")
	wear(state, "a_old1", "iron_blade", "weapon")
	add(state, "a_bag", "iron_blade")
	add(state, "a_long", "long_bow")
	result = plan(state, {"kind": "change_job", "job_id": "knight"}, "同名二個体・従前枠順")
	check(result.ok and result.candidate.party[0].equipment.weapons == ["z_old0", "a_old1"], "同率は従前と従前順を優先")
	state = fixture()
	add(state, "z_iron", "iron_blade")
	add(state, "a_iron", "iron_blade")
	for attempt in range(5):
		result = plan(state, {"kind": "change_job", "job_id": "knight"}, "同点安定%d" % attempt)
		check(result.ok and result.candidate.party[0].equipment.weapons == ["a_iron"], "instance_id安定順")
	state = fixture()
	wear(state, "only_other", "iron_blade", "weapon", 0, state.party[1])
	wear(state, "only_reserve", "iron_blade", "weapon", 0, state.first_region.reserve[0])
	result = plan(state, {"kind": "change_job", "job_id": "warrior"}, "他人の候補だけ")
	check(result.ok and result.candidate.party[0].equipment.weapons.is_empty(), "他人から奪わない")

func test_manual_and_abilities() -> void:
	var state := fixture()
	wear(state, "old", "practice_blade", "weapon")
	wear(state, "armor", "iron_plate_armor", "armor")
	wear(state, "acc", "vitality_braid", "accessory")
	add(state, "strong", "iron_blade")
	var result := plan(state, {"kind": "set_abilities", "equipped_abilities": ["twin_grip"]}, "二刀流装着")
	check(result.ok and result.candidate.party[0].equipment == state.party[0].equipment, "能力装着は最強へ変えない")
	state = result.candidate
	result = plan(state, {"kind": "equip", "slot": "weapon", "index": 1, "instance_id": "strong"}, "第2武器手動")
	check(result.ok and result.candidate.party[0].equipment.weapons == ["old", "strong"], "手動第2枠")
	state = result.candidate
	result = plan(state, {"kind": "equip", "slot": "weapon", "index": 0, "instance_id": "strong"}, "本人枠交換")
	check(result.ok and result.candidate.party[0].equipment.weapons == ["strong", "old"], "本人の武器は交換できる")
	result = plan(state, {"kind": "set_abilities", "equipped_abilities": []}, "二刀流解除")
	check(result.ok and result.candidate.party[0].equipment.weapons == ["old"] and result.candidate.equipment_stock.bag == ["strong"], "第2だけ袋へ")
	check(result.candidate.party[0].equipment.armor == "armor" and result.candidate.party[0].equipment.accessories == ["acc", "", ""], "防具装飾不変")
	reject(state, {"kind": "set_abilities", "equipped_abilities": ["twin_grip", "two_handed"]}, "ability_conflict", "能力排他")
	reject(state, {"kind": "set_abilities", "equipped_abilities": ["missing"]}, "unlearned_ability", "未習得")
	reject(state, {"kind": "set_abilities", "equipped_abilities": ["twin_grip", "power_strike", "two_handed"]}, "ability_conflict", "排他は満杯より優先")
	reject(state, {"kind": "set_abilities", "equipped_abilities": ["power_strike", "power_strike"]}, "duplicate_ability", "能力重複")
	state.party[0].learned_abilities.append("guard")
	reject(state, {"kind": "set_abilities", "equipped_abilities": ["twin_grip", "power_strike", "guard"]}, "ability_capacity", "満杯")
	state.party[0].monster_form = "slime"
	state.party[0].equipped_abilities = ["power_strike", "guard", "twin_grip"]
	result = plan(state, {"kind": "change_job", "job_id": "knight", "monster_form": ""}, "形態変更後枠縮小")
	check(result.ok and result.candidate.party[0].equipped_abilities == ["power_strike", "guard"] and result.candidate.party[0].equipment.weapons == ["strong"], "能力枠整理後に武器1本選択")
	state = fixture()
	wear(state, "weapon", "practice_blade", "weapon")
	result = plan(state, {"kind": "set_abilities", "equipped_abilities": ["two_handed"]}, "両手持ち装着")
	check(result.ok and rules.two_handed_active(result.candidate, "a"), "両手持ち条件だけ導出")
	state = fixture("mage")
	wear(state, "staff", "practice_staff", "weapon")
	state.party[0].equipped_abilities = ["two_handed"]
	check(not rules.two_handed_active(state, "a"), "杖は両手持ち不発・能力保持")
	state = fixture()
	wear(state, "weapon", "practice_blade", "weapon")
	result = plan(state, {"kind": "equip", "slot": "weapon", "index": 0, "instance_id": ""}, "手動で空装備")
	check(result.ok and result.candidate.party[0].equipment.weapons == [] and result.candidate.equipment_stock.bag == ["weapon"], "手動解除")
	add(state, "dagger", "iron_dagger")
	reject(state, {"kind": "equip", "slot": "weapon", "index": 0, "instance_id": "dagger"}, "wrong_category", "分類拒否")
	reject(state, {"kind": "equip", "slot": "accessory", "index": 2, "instance_id": ""}, "invalid_slot", "人間3枠目拒否")
	reject(state, {"kind": "equip", "slot": "weapon", "index": 1, "instance_id": "weapon"}, "invalid_slot", "二刀流なし2枠目拒否")
	wear(state, "other", "iron_blade", "weapon", 0, state.party[1])
	wear(state, "reserved", "iron_blade", "weapon", 0, state.first_region.reserve[0])
	for instance in ["other", "reserved"]:
		reject(state, {"kind": "equip", "slot": "weapon", "index": 0, "instance_id": instance}, "owned_by_other", "他人所有指定 " + instance)
	reject(state, {"kind": "equip", "slot": "weapon", "index": 0, "instance_id": "missing"}, "unknown_instance", "未知個体")
	reject(state, {"kind": "change_job", "job_id": "missing"}, "unknown_job", "未知職")
	reject(state, {"kind": "change_job", "job_id": "warrior"}, "unknown_actor", "未知対象", "missing")
	reject(state, {"kind": "unsupported"}, "invalid_request", "未知操作")
	reject(state, {"kind": "equip", "slot": "weapon", "index": 0.0, "instance_id": "weapon"}, "invalid_request", "小数の枠")
	reject(state, {"kind": "change_job", "job_id": "warrior", "extra": 1}, "invalid_request", "余分キー")

func test_invalid_states() -> void:
	var state := fixture()
	state.erase("equipment_rules_version")
	invalid(state, "旧状態を移行しない")
	for version in [2, 1.0, "1", true]:
		state = fixture()
		state.equipment_rules_version = version
		invalid(state, "不正版・型 " + str(version))
	state = fixture()
	add(state, "unknown", "missing")
	invalid(state, "未知商品")
	state = fixture()
	add(state, "orphan", "practice_blade")
	state.equipment_stock.bag.clear()
	invalid(state, "孤児")
	state = fixture()
	add(state, "duplicate", "practice_blade")
	state.equipment_stock.bag.append("duplicate")
	invalid(state, "袋重複")
	state = fixture()
	wear(state, "shared", "practice_blade", "weapon")
	state.first_region.reserve[0].equipment.weapons = ["shared"]
	invalid(state, "party/reserve二重所有")
	state = fixture()
	wear(state, "shared", "practice_blade", "weapon")
	state.party[0].equipped_abilities = ["twin_grip"]
	state.party[0].equipment.weapons.append("shared")
	invalid(state, "同一個体二枠")
	state = fixture()
	state.party[0].equipment.accessories = ["", ""]
	invalid(state, "装飾枠数")
	state = fixture()
	state.party[0].equipment.extra = ""
	invalid(state, "余分装備枠")
	state = fixture()
	state.party[0].equipment.weapons = [3]
	invalid(state, "不正所有型")
	state = fixture()
	wear(state, "bad", "vitality_braid", "accessory", 2)
	invalid(state, "人間の3枠目")
	state = fixture("slime")
	wear(state, "bad", "practice_blade", "weapon")
	invalid(state, "魔物武器")
	state = fixture("beast")
	wear(state, "bad", "cotton_travel_clothes", "armor")
	invalid(state, "魔物防具")
	state = fixture()
	state.party[0].equipped_abilities = ["twin_grip", "two_handed"]
	invalid(state, "保存にも能力排他")
	state = fixture()
	state.first_region.reserve[0].id = "a"
	invalid(state, "人物二重ID")
	state = fixture()
	state.party[0].job_id = 3
	invalid(state, "職の型")
	state = fixture()
	state.party[0].integrated = {"weapons": ["practice_blade"]}
	invalid(state, "旧新武器混在")
	for field in ["instances", "bag"]:
		state = fixture()
		state.equipment_stock[field] = 3
		invalid(state, "台帳型 " + field)
	state = fixture()
	state.first_region.reserve = 3
	invalid(state, "reserve型")
	state = fixture()
	state.party = [3]
	invalid(state, "人物型")

func test_bonuses() -> void:
	for item in ["vitality_braid", "thought_clasp", "guard_stitched_bracelet"]:
		for count in range(1, 4):
			var state := fixture("slime" if count == 3 else "warrior")
			for index in range(count):
				wear(state, "acc%d" % index, item, "accessory", index)
			var before := state.duplicate(true)
			var result: Dictionary = rules.equipment_bonuses(state, "a")
			var expected := {"hp": 10 * count if item == "vitality_braid" else 0, "mp": 2 * count if item == "thought_clasp" else 0, "attack": 0, "defense": count if item == "guard_stitched_bracelet" else 0}
			check(result.ok and result.bonuses == expected, "同名%d個補正 " % count + item)
			check(state == before, "補正導出の副作用なし")
	var state := fixture()
	state.party[0].equipped_abilities = ["twin_grip"]
	wear(state, "main", "iron_blade", "weapon")
	wear(state, "second", "iron_blade", "weapon")
	wear(state, "armor", "iron_plate_armor", "armor")
	wear(state, "hp", "vitality_braid", "accessory", 0)
	wear(state, "def", "guard_stitched_bracelet", "accessory", 1)
	check(rules.equipment_bonuses(state, "a").bonuses == {"hp": 10, "mp": 0, "attack": 3, "defense": 4}, "主武器だけ加算・防具装飾合算")
	check(rules.equipment_bonuses(state, "b").bonuses == {"hp": 0, "mp": 0, "attack": 0, "defense": 0}, "他人へ補正漏れなし")
	state.party[0].equipment.accessories[1] = "hp"
	check(not rules.equipment_bonuses(state, "a").ok, "補正も同一個体重複拒否")


func test_extra_boundaries() -> void:
	var state := fixture()
	wear(state, "old_armor", "cotton_travel_clothes", "armor")
	add(state, "z_armor", "cotton_travel_clothes")
	var result := plan(state, {"kind": "change_job", "job_id": "knight"}, "同率防具")
	check(result.ok and result.candidate.party[0].equipment.armor == "old_armor", "防具の従前優先")
	add(state, "strong_armor", "iron_plate_armor")
	result = plan(state, {"kind": "change_job", "job_id": "knight"}, "強い袋防具")
	check(result.ok and result.candidate.party[0].equipment.armor == "strong_armor", "袋のより強い防具選択")
	state = fixture("slime")
	wear(state, "a1", "vitality_braid", "accessory", 0)
	wear(state, "a2", "thought_clasp", "accessory", 1)
	wear(state, "a3", "guard_stitched_bracelet", "accessory", 2)
	result = plan(state, {"kind": "equip", "slot": "accessory", "index": 0, "instance_id": "a3"}, "魔物装飾手動交換")
	check(result.ok and result.candidate.party[0].equipment.accessories == ["a3", "a2", "a1"], "装飾本人枠交換")
	result = plan(state, {"kind": "equip", "slot": "accessory", "index": 2, "instance_id": ""}, "魔物第3装飾解除")
	check(result.ok and result.candidate.equipment_stock.bag == ["a3"], "魔物第3装飾は袋へ")
	state = fixture()
	state.party[0].equipped_abilities = ["twin_grip"]
	wear(state, "weapon", "practice_blade", "weapon")
	wear(state, "second", "iron_blade", "weapon")
	result = plan(state, {"kind": "change_job", "job_id": "mage", "equipped_abilities": []}, "整理済み能力付き転職")
	check(result.ok and result.candidate.party[0].equipment.weapons.is_empty() and result.candidate.equipment_stock.bag == ["weapon", "second"], "転職も装備を消さず返却")
	state = fixture()
	state.party[0].equipped_abilities = ["twin_grip"]
	add(state, "second", "iron_blade")
	reject(state, {"kind": "equip", "slot": "weapon", "index": 1, "instance_id": "second"}, "invalid_slot", "主武器なしの第2指定")
	state = fixture()
	add(state, "one", "practice_blade")
	var before := state.duplicate(true)
	result = rules.plan_equipment_change(state, "r", {"kind": "equip", "slot": "weapon", "index": 0, "instance_id": "one"})
	check(result.ok and result.candidate.first_region.reserve[0].equipment.weapons == ["one"] and result.candidate.party == state.party and state == before, "明示reserve対象だけ手動変更")
	for field in ["weapons", "armor", "accessories"]:
		state = fixture()
		state.party[0].equipment[field] = 0
		invalid(state, "装備型 " + field)
	state = fixture()
	state.integrated = {"armory": []}
	invalid(state, "旧新armory混在")
	state = fixture()
	state.party[0].monster_form = "warrior"
	invalid(state, "人間職を形態指定")
	state = fixture()
	state.progress_flags.midgame_slots = 1
	invalid(state, "能力枠フラグ型")
	state = fixture()
	state.party[0].equipped_abilities = [7]
	invalid(state, "能力配列要素型")
	state = fixture()
	state.equipment_stock.instances["bad"] = 4
	state.equipment_stock.bag = ["bad"]
	invalid(state, "個体参照値型")
	# 合成品は検査内だけ。採用商品や本番データを増やさずitem_id最終同点順を実証。
	var original_rules: RefCounted = rules
	rules = Rules.new()
	for identifier in ["test_z_blade", "test_a_blade"]:
		rules._items[identifier] = {"id": identifier, "name": "検査用", "kind": "weapon", "weapon_category": "blade", "bonuses": {"attack": 3}, "provisional": true}
	state = fixture()
	add(state, "a_instance", "test_z_blade")
	add(state, "z_instance", "test_a_blade")
	for attempt in range(5):
		result = plan(state, {"kind": "change_job", "job_id": "warrior"}, "item_id安定順%d" % attempt)
		check(result.ok and result.candidate.party[0].equipment.weapons == ["z_instance"], "instance_idよりitem_id順を優先")
	rules = original_rules

func _initialize() -> void:
	rules = Rules.new()
	check(Engine.get_version_info().major == 4 and Engine.get_version_info().minor == 7 and Engine.get_version_info().patch == 2 and Engine.get_version_info().status == "stable", "指定Godot4.7.2")
	test_catalog()
	test_permissions()
	test_invalid_states()
	test_transitions()
	test_selection()
	test_manual_and_abilities()
	test_bonuses()
	test_extra_boundaries()
	var result := {"status": "PASS" if failures.is_empty() else "FAIL", "checks": checks, "transitions": transitions, "failures": failures, "engine": Engine.get_version_info().string, "command": "timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd"}
	var output := FileAccess.open("res://docs/verification/equipment-core/checks.json", FileAccess.WRITE)
	output.store_string(JSON.stringify(result, "\t") + "\n")
	output.close()
	print("EQUIPMENT_CORE_" + result.status + ": checks=%d transitions=%d failures=%d" % [checks, transitions, failures.size()])
	for failure in failures:
		print("EQUIPMENT_CORE_FAIL: " + failure)
	quit(0 if failures.is_empty() else 1)
