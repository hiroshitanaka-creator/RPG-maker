extends SceneTree
const Migration = preload("res://scripts/game/equipment_save_migration.gd")
const Validation = preload("res://scripts/game/equipment_save_validation.gd")
const View = preload("res://scripts/game/equipment_state_view.gd")
const Rules = preload("res://scripts/game/equipment_rules.gd")
const Fixtures = preload("res://tools/fixtures/equipment-save/fixtures.gd")
const SOURCE = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
var checks := 0
var failures: Array = []
var cases: Array = []
var observations: Array = []
var expected: Dictionary
var session: GameSession
var context: Dictionary
var migration: RefCounted

func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:failures.append(label)

func same(left: Variant, right: Variant) -> bool:
	return Validation.differences(left, right).is_empty()

func instance(number: int) -> String:
	return "eqm_%s_%06d" % [expected.stable_id.migration_id, number]

func persons(document: Dictionary) -> Array:
	return document.party + document.get("first_region", {}).get("reserve", [])

func person(document: Dictionary, identifier: String) -> Dictionary:
	for actor in persons(document):
		if actor.id == identifier:return actor
	return {}

func items(document: Dictionary) -> Dictionary:
	var totals: Dictionary = {}
	for item in document.equipment_stock.instances.values():totals[item] = totals.get(item, 0) + 1
	return totals

func run_case(source: Dictionary, label: String, code: String = "ok", custom: Dictionary = {}) -> Dictionary:
	check(label not in cases, label + " ケースID一意")
	cases.append(label)
	var ctx: Dictionary = context if custom.is_empty() else custom
	var before := source.duplicate(true)
	var abilities_before: Dictionary = ctx.get("abilities", {}).duplicate(true)
	var jobs_before := session.jobs.duplicate(true)
	var state_before := session.export_state()
	var metrics_before := session.play_metrics.snapshot()
	var result: Dictionary = migration.plan(source, SOURCE, ctx)
	check(same(source, before), label + " 元doc深い型・値不変")
	check(same(ctx.get("abilities", {}), abilities_before), label + " context能力不変")
	check(same(session.jobs, jobs_before), label + " context職定義不変")
	check(same(session.export_state(), state_before), label + " live state不変")
	check(same(session.play_metrics.snapshot(), metrics_before), label + " live metrics/history不変")
	check(result.reason_code == code and result.ok == (code == "ok"), label + " 固定成否理由:" + code + " 実際:" + str(result.reason_code))
	if not result.ok:
		check(not result.has("candidate_document") and not result.has("candidate"), label + " 失敗候補なし")
		check(not result.errors.is_empty() and result.errors.all(func(e: Dictionary) -> bool: return e.get("target") is String and not e.target.is_empty()), label + " パスあり")
		observations.append({"case": label, "reason_code": result.reason_code, "errors": result.errors})
		return result
	var candidate: Dictionary = result.candidate_document
	check(Validation.validate_new(candidate, source, SOURCE, ctx).is_empty(), label + " S1装備・許可差分有効")
	check(candidate.equipment_migration.migration_id == expected.stable_id.migration_id, label + " 固定ID")
	var again: Dictionary = migration.plan(source, SOURCE, ctx)
	check(again.ok and same(candidate, again.candidate_document), label + " IDと全候補の決定性")
	check(same(candidate.party.map(func(a: Dictionary):return a.id), source.party.map(func(a: Dictionary):return a.id)), label + " party順序保持")
	if source.has("first_region"):
		check(same(candidate.first_region.reserve.map(func(a: Dictionary):return a.id), source.first_region.reserve.map(func(a: Dictionary):return a.id)), label + " reserve順序保持")
	else:check(not candidate.has("first_region"), label + " 本編モード保持")
	for key in source:
		if key not in ["format_version", "integrated", "party", "first_region", "_saved_value_types"]:check(same(source[key], candidate[key]), label + " 非装備保存保持:" + key)
	for original in persons(source):
		var changed := person(candidate, original.id)
		for key in original:
			if key not in ["integrated", "jp", "learned_abilities"]:check(same(original[key], changed[key]), label + " 人物不変:" + original.id + "." + key)
	var copy := candidate.duplicate(true)
	candidate.inventory.potion += 1
	candidate.equipment_stock.bag.append("mutation")
	candidate.party[0].learned_abilities.append("mutation")
	check(same(source, before), label + " candidateと元の参照分離")
	candidate = copy
	result["candidate_document"] = copy
	result.equipment_audit.generated.append({"mutation": true})
	check(not candidate.equipment_migration.equipment_audit.generated.back().has("mutation"), label + " 戻り監査の参照分離")
	result["equipment_audit"] = candidate.equipment_migration.equipment_audit.duplicate(true)
	observations.append({"case": label, "reason_code": "ok", "items": items(candidate), "total": candidate.equipment_stock.instances.size(), "bag": candidate.equipment_stock.bag, "actors": persons(candidate).map(func(a: Dictionary):return {"id": a.id, "equipment": a.equipment}), "audit": result.equipment_audit, "legacy_format_audit": result.legacy_format_audit})
	return result

func baseline_cases() -> void:
	var source := Fixtures.region()
	var result := run_case(source, "M01-pending")
	if not result.ok:return
	var candidate: Dictionary = result.candidate_document
	check(items(candidate) == expected.M01.items_pending, "M01固定品別数量")
	check(candidate.equipment_stock.instances.size() == expected.M01.pending_total, "M01固定12")
	check(candidate.equipment_stock.bag == expected.M01.bag.map(func(n):return instance(int(n))), "M01固定袋順")
	for identifier in expected.M01.owners:
		var actor := person(candidate, identifier)
		var owner: Dictionary = expected.M01.owners[identifier]
		check(actor.equipment.weapons == owner.weapons.map(func(n):return instance(int(n))) and actor.equipment.armor == instance(int(owner.armor)) and actor.equipment.accessories == ["", "", ""], "M01固定所有:" + identifier)
	check(result.equipment_audit.generated.filter(func(e: Dictionary):return e.reason == "migration_support").map(func(e: Dictionary):return e.item_id) == expected.M01.support, "M01補填固定順")
	check(same(result.equipment_audit.source_armory, source.integrated.armory), "M01旧armory保持")
	check(result.legacy_format_audit.actors.is_empty(), "M01形式更新0")
	source["progress_flags"]["job_change_unlocked"] = true
	result = run_case(source, "M01-unlocked")
	if result.ok:
		check(result.candidate_document.equipment_stock.instances.size() == expected.M01.granted_total, "M01解放22")
		check(result.equipment_audit.generated.slice(-10).map(func(e: Dictionary):return e.item_id) == expected.common, "M01共通固定各1順")
	var main := Fixtures.base()
	main.progress_flags.erase("midgame_slots")
	result = run_case(main, "M01-main-no-reserve-no-capacity-key")
	if result.ok:check(not result.candidate_document.progress_flags.has("midgame_slots"), "ビューの容量既定を永続化しない")
	var reverse := Fixtures.region()
	reverse.first_region.reserve.reverse()
	result = run_case(reverse, "M01-array-order")
	if result.ok:
		check(items(result.candidate_document) == expected.M01.items_pending, "順序変更でも同数量")
		check(person(result.candidate_document, "pc_04").equipment.weapons == [instance(11)], "ID処理順は配列順に依存しない")

func weapon_cases() -> void:
	var source := Fixtures.region()
	source["party"][0]["learned_abilities"] = ["twin_grip"]
	source["party"][0]["equipped_abilities"] = ["twin_grip"]
	source["party"][0]["integrated"]["weapons"] = ["practice_blade", "practice_blade"]
	source.integrated.armory.append("iron_blade")
	var result := run_case(source, "M02-duplicate-slots-and-unheld")
	if result.ok:
		var candidate: Dictionary = result.candidate_document
		check(candidate.party[0].equipment.weapons == [instance(1), instance(2)], "M02同名2枠は別ID")
		check(items(candidate).practice_blade == 5 and items(candidate).iron_blade == 1, "M02N =5と未装備解放1")
		check(candidate.equipment_stock.instances.size() == 14, "M02固定14副武器補填0")
		source.integrated.armory.erase("iron_blade")
		result = run_case(source, "M02-not-released")
		if result.ok:check(not items(result.candidate_document).has("iron_blade"), "M02未解放0")
	source = Fixtures.region()
	source.integrated.armory.append("iron_blade")
	result = run_case(source, "M03-keep-weaker-legal")
	if result.ok:
		var candidate: Dictionary = result.candidate_document
		check(candidate.party[0].equipment.weapons == [instance(1)], "M03合法従前0保持")
		var changed: Dictionary = Rules.new().plan_equipment_change(View.project(candidate).view, "pc_01", {"kind": "change_job", "job_id": "warrior"})
		check(changed.ok and changed.candidate.equipment_stock.instances[changed.candidate.party[0].equipment.weapons[0]] == "iron_blade", "M03通常同職change_jobは最強へ")
	source = Fixtures.region()
	source["first_region"]["reserve"][1]["integrated"]["weapons"] = ["practice_staff"]
	result = run_case(source, "M03-negative-staff-owner-exclusion")
	if result.ok:
		check(person(result.candidate_document, "pc_03").equipment.weapons == [instance(3)], "M03負値合法従前保持")
		check(person(result.candidate_document, "pc_04").equipment.weapons == [instance(10)], "M03reserve既所有を奪わず杖補填")
	source = Fixtures.region()
	source["party"][0]["learned_abilities"] = ["twin_grip"]
	source["party"][0]["equipped_abilities"] = ["twin_grip"]
	source["party"][0]["integrated"]["weapons"] = ["practice_blade", "practice_bow"]
	source["first_region"]["reserve"][0]["job_id"] = "beast"
	Fixtures.caps(source.first_region.reserve[0], session)
	result = run_case(source, "M04-invalid-offhand-and-monster")
	if result.ok:
		var candidate: Dictionary = result.candidate_document
		check(candidate.party[0].equipment.weapons == [instance(1)], "M04不適合副武器空きの補填0")
		check(person(candidate, "pc_02").equipment == {"weapons": [], "armor": "", "accessories": ["", "", ""]}, "M04魔物武器防具0")
		check(candidate.equipment_grants.actor_support.pc_02 == [], "M04魔物処理済み0補填")
		check(result.equipment_audit.returned.map(func(e: Dictionary):return e.instance_id) == [instance(2), instance(3), instance(4), instance(5)], "M04全返却順")
		check(items(candidate).practice_blade == 4 and items(candidate).practice_bow == 1 and not items(candidate).has("cloth_fist_wrap"), "M04旧個体全数・新拳0")
	# 主武器が不適合、合法副武器があるときも、副枠を保ち主だけ袋から埋める。
	source = Fixtures.region()
	source["party"][0]["learned_abilities"] = ["twin_grip"]
	source["party"][0]["equipped_abilities"] = ["twin_grip"]
	source["party"][0]["integrated"]["weapons"] = ["practice_bow", "practice_blade"]
	result = run_case(source, "M04-invalid-main-valid-offhand")
	if result.ok:check(result.candidate_document.party[0].equipment.weapons == [instance(3), instance(2)], "M04副武器従前保持と主袋選択")

func legacy_cases() -> void:
	var old_mastery := Fixtures.region()
	old_mastery.integrated.erase("mastery_rules_version")
	for actor in persons(old_mastery):actor.integrated.erase("mastery")
	var mastery_result := run_case(old_mastery, "M05-format2-unrecorded-mastery")
	if mastery_result.ok:
		check(mastery_result.legacy_format_audit.mastery_initialized.size() == 4, "旧形式2未記録修練を全人物に初期化")
		for actor in persons(mastery_result.candidate_document):check(actor.integrated.mastery == {"counts": {}, "legacy_masters": []} and actor.jp == {}, "未記録成功回数の創作0・JP換算0")
	for count in [3, 4]:
		var source := Fixtures.legacy(false, count)
		var result := run_case(source, "M05-party%d" % count)
		if result.ok:
			check(result.equipment_audit.generated.filter(func(e: Dictionary):return e.reason == "format1_supply").size() == int(expected.M05["supply%d" % count]), "M05P+2")
			check(result.candidate_document.equipment_stock.instances.size() == int(expected.M05["total%d" % count]), "M05数量固定")
			check(result.equipment_audit.source_armory == [] and result.equipment_audit.actor_slots.all(func(e: Dictionary):return e.weapons == []), "M05旧形式2数量を二重付与しない")
	for index in range(3):
		var source := Fixtures.legacy()
		source["party"][0]["jp"]["warrior"] = int(expected.M05.legacy_jp[index])
		if index == 1:source["party"][0]["mastered_jobs"] = ["warrior"]
		source["party"][1]["jp"]["beast"] = 18
		Fixtures.caps(source.party[0], session)
		var result := run_case(source, "M05-jp%d" % index)
		if result.ok:
			check(result.candidate_document.party[0].jp.warrior == int(expected.M05.modern_jp[index]), "M05手書きJP換算")
			check(result.candidate_document.party[1].integrated.forgotten == expected.M05.forgotten and result.candidate_document.party[1].integrated.relearn == expected.M05.relearn, "M05手書き忘却とrelearn")
	var source := Fixtures.legacy(true)
	source["first_region"]["reserve"][2]["jp"]["warrior"] = 12
	var result := run_case(source, "M06-legacy-reserve")
	if result.ok:
		check(person(result.candidate_document, "pc_04").jp.warrior == 60, "M06reserveもJP換算")
		check(result.legacy_format_audit.actors.size() == 4, "M06記録4人だけ更新")
		source.first_region.reserve.resize(2)
		result = run_case(source, "M06-no-missing-actor-generation")
		if result.ok:check(person(result.candidate_document, "pc_04").is_empty(), "M06欠落人物生成0")
	for field in ["mixed", "duplicate", "job", "hp", "mastery"]:
		source = Fixtures.legacy(true) if field != "mastery" else Fixtures.region()
		match field:
			"mixed":source["first_region"]["reserve"][0]["integrated"] = IntegratedProgression.initial_actor()
			"duplicate":source["first_region"]["reserve"][0]["id"] = "pc_01"
			"job":source["first_region"]["reserve"][0]["job_id"] = "unknown"
			"hp":source["first_region"]["reserve"][0]["hp"] = -1
			"mastery":source.first_region.reserve[0].integrated.erase("mastery")
		run_case(source, "M06-reject-" + field, "invalid_reserve")

func ability_and_grant_cases() -> void:
	var source := Fixtures.region()
	var actors := persons(source)
	for index in [0, 1]:
		actors[index]["jp"]["warrior"] = 120
		actors[index]["mastered_jobs"] = ["warrior"]
		actors[index]["integrated"]["mastery"]["legacy_masters"] = ["warrior"]
		actors[index]["learned_abilities"] = ["power_strike"]
		actors[index]["equipped_abilities"] = ["power_strike"]
		Fixtures.caps(actors[index], session)
	actors[2]["jp"]["warrior"] = 120
	actors[2]["integrated"]["mastery"]["counts"]["warrior"] = 19
	actors[3]["jp"]["priest"] = 120
	actors[3]["mastered_jobs"] = ["priest"]
	actors[3]["integrated"]["mastery"]["legacy_masters"] = ["priest"]
	Fixtures.caps(actors[3], session)
	var result := run_case(source, "M07-warrior-master-party-reserve")
	if result.ok:
		var candidate: Dictionary = result.candidate_document
		check(result.equipment_audit.learned_added.size() == 2, "M07既得2人だけ追加")
		for index in range(4):
			var actor := person(candidate, actors[index].id)
			check(actor.learned_abilities == (["power_strike", "two_handed"] if index < 2 else []), "M07追加末尾/非master0")
			check(same(actor.equipped_abilities, actors[index].equipped_abilities) and same(actor.jp, actors[index].jp) and same(actor.integrated.mastery, actors[index].integrated.mastery), "M07装着JPcountslegacy不変")
		var ctx := context.duplicate()
		ctx["source_document"] = source
		run_case(candidate, "M07-already-migrated", "already_migrated", ctx)
		ctx["abilities"] = context.abilities.duplicate(true)
		ctx.abilities.erase("two_handed")
		run_case(source, "M07-missing-ability-context", "unknown_ability", ctx)
		check(not session._valid_state(candidate), "M07現GameSessionは新保存を拒否")
	source = Fixtures.region()
	result = run_case(source, "M08-pending")
	if not result.ok:return
	var pending: Dictionary = result.candidate_document
	pending.progress_flags["job_change_unlocked"] = true
	var snapshot := pending.duplicate(true)
	var ctx := context.duplicate()
	ctx["job_change_unlocked"] = true
	var grant: Dictionary = migration.grant_common(pending, source, SOURCE, ctx)
	check(grant.ok and same(pending, snapshot), "M08支給純粋・入力不変")
	if not grant.ok:return
	var granted: Dictionary = grant.candidate_document
	check(granted.equipment_stock.instances.size() == 22 and granted.equipment_grants.common_set == "granted", "M08最初だけ10追加")
	check(granted.equipment_migration.equipment_audit.generated.slice(-10).map(func(e: Dictionary):return e.item_id) == expected.common, "M08固定共通10順・各1")
	check(same(granted.progress_flags, pending.progress_flags), "M08純粋支給は解放済みフラグを保持")
	check(Validation.validate_new(granted, source, SOURCE, ctx).is_empty(), "M08支給後台帳・許可差分有効")
	for index in range(3):
		var repeated: Dictionary = migration.grant_common(granted, source, SOURCE, ctx)
		check(not repeated.ok and repeated.reason_code == "already_granted" and not repeated.has("candidate_document"), "M08再読込/再解放二重支給0:%d" % index)
	var rejected: Dictionary = migration.grant_common(pending, source, SOURCE, context)
	check(not rejected.ok and rejected.reason_code == "grant_not_unlocked", "M08未解放拒否")
	ctx["source_document"] = source
	run_case(granted, "M08-granted-already-migrated", "already_migrated", ctx)
	var joined := granted.duplicate(true)
	joined.party.append(joined.first_region.reserve.pop_front())
	check(Rules.new().validate_equipment_state(View.project(joined).view).is_empty() and same(joined.equipment_stock, granted.equipment_stock), "M08既存reserve加入の新生成0")
	var changed: Dictionary = Rules.new().plan_equipment_change(View.project(joined).view, "pc_01", {"kind": "change_job", "job_id": "warrior"})
	check(changed.ok and same(changed.candidate.equipment_stock.instances, granted.equipment_stock.instances), "M08加入後同職再転職の個数不変")
	check(not migration.grant_common(joined, source, SOURCE, ctx).ok, "M08進行後入力を旧移行候補と偽って再支給しない")

func preservation_cases() -> void:
	var rich := Fixtures.region()
	rich["party"] = persons(rich).duplicate(true)
	rich.first_region["reserve"] = []
	rich.progress_flags["mountain_path_open"] = true
	rich.overworld["cleared"] = ["forest_tower_boss"]
	rich.overworld["residents"] = {"fixture": {"cell": [4, 5], "facing": 2}}
	rich.first_region["travel"] = {"version": 1, "visited": ["start_village", "first_port"], "return_learned": true, "ship_owned": true, "ship_cell": [59, 48]}
	rich.first_region["errands"] = {"haldo": "requested"}
	rich.integrated["knowledge"] = {"conductor": {"facts": [1, 0], "confirmed": true}}
	rich.integrated["outcomes"] = {"w_ferry_1": {"rule": "conductor", "methods": ["field_break", "electric"]}}
	rich.integrated["claimed"] = ["w_ferry_1"]
	rich.integrated["job_notes"] = ["hunter/rumor"]
	rich.party[0]["learned_abilities"] = ["focus_vow", "power_strike"]
	rich.party[0]["equipped_abilities"] = ["focus_vow", "power_strike"]
	rich.party[0].integrated["focus_binding"] = "power_strike"
	rich.party[0].integrated["forgotten"] = ["fang"]
	rich.party[0].integrated["relearn"] = {"fang": 2}
	rich.party[0].integrated["jp_remainders"] = {"warrior": 1}
	rich.party[0].integrated.mastery.counts["warrior"] = 19
	var rich_result := run_case(rich, "M10-rich-progress")
	if rich_result.ok:
		for area in ["overworld", "first_region", "integrated"]:
			var canonical: Dictionary = rich_result.candidate_document
			var scope: Dictionary = rich[area]
			for key in scope:
				if key not in ["armory", "reserve"]:check(same(canonical[area][key], scope[key]), "M10既存領域保持:" + area + "." + key)
		var paths: Array = []
		collect_paths(rich_result.candidate_document, [], paths)
		for path in paths:
			var changed: Dictionary = rich_result.candidate_document.duplicate(true)
			var parent: Variant = changed
			for part in path.slice(0, -1):parent = parent[part]
			var key: Variant = path.back()
			match typeof(parent[key]):
				TYPE_INT:parent[key] += 1
				TYPE_BOOL:parent[key] = not parent[key]
				TYPE_STRING:parent[key] += "x"
			check(not Validation.compare_transition(rich, changed, SOURCE, context).is_empty(), "M10進捗単独leaf拒否:" + str(path))
		observations.append({"case": "M10-rich-leaf-mutations", "count": paths.size()})
	var source := Fixtures.region()
	var names: Array[String] = ["practice_blade", "practice_staff", "practice_bow"]
	source["integrated"]["armory"] = names
	var weapons: Array[String] = ["practice_blade"]
	source["party"][0]["integrated"]["weapons"] = weapons
	var people: Array[Dictionary] = []
	people.assign(source.first_region.reserve)
	source["first_region"]["reserve"] = people
	var cell: Array[int] = [6, 7]
	source["overworld"]["cell"] = cell
	source["party"][0]["hp"] = 0
	var metrics := PlaySessionMetrics.new().snapshot()
	var nested: Array[float] = [1.0, 1.5, 1.0 / 3.0]
	var empty: Array[int] = []
	metrics["events"] = [{"kind": "fixture", "chapter": "R01", "elapsed_ms": 0, "details": {"values": nested, "empty": empty, "arbitrary_key": {"ratio": 1.0 / 3.0}}}]
	source["_play_session"] = metrics
	source["_trial_id"] = "0123456789abcdef0123456789abcdef"
	source["_saved_value_types"] = SavedValueTypes.describe(source)
	var result := run_case(source, "M10-types-progress-history")
	if not result.ok:return
	var candidate: Dictionary = result.candidate_document
	check(same(candidate._play_session, source._play_session), "M10履歴任意details・float・空typed配列保持")
	check(candidate.first_region.reserve.is_typed() and candidate.first_region.reserve.get_typed_builtin() == TYPE_DICTIONARY, "M10reserve型保持")
	check(candidate.equipment_migration.equipment_audit.source_armory.is_typed() and candidate.equipment_migration.equipment_audit.actor_slots[0].weapons.is_typed(), "M10退避旧装備配列型保持")
	var without := candidate.duplicate(true)
	without.erase("_saved_value_types")
	check(same(candidate._saved_value_types, SavedValueTypes.describe(without)), "M10移動先の型metadata再生成")
	# 既知の全leafを一つずつ変え、元との許可差分検査が検出する。
	var paths: Array = []
	collect_paths(candidate, [], paths)
	var changed_count := 0
	for path in paths:
		var changed := candidate.duplicate(true)
		var parent: Variant = changed
		for part in path.slice(0, -1):parent = parent[part]
		var key: Variant = path.back()
		match typeof(parent[key]):
			TYPE_INT:parent[key] += 1
			TYPE_FLOAT:parent[key] += 0.25
			TYPE_BOOL:parent[key] = not parent[key]
			TYPE_STRING:parent[key] += "x"
			_:check(false, "M10未対応leaf型")
		check(not Validation.compare_transition(source, changed, SOURCE, context).is_empty(), "M10単独leaf改変拒否:" + str(path))
		changed_count += 1
	check(changed_count == paths.size() and changed_count == 311, "M10固定311leafの検査・省略0")
	observations.append({"case": "M10-all-leaf-mutations", "count": changed_count})
	for scope in ["root", "party", "reserve"]:
		var unknown := Fixtures.region()
		if scope == "root":unknown["unknown"] = 1
		elif scope == "party":unknown["party"][0]["unknown"] = 1
		else:unknown["first_region"]["reserve"][0]["unknown"] = 1
		run_case(unknown, "M10-unknown-" + scope, "unknown_field")

func collect_paths(value: Variant, path: Array, output: Array) -> void:
	if value is Dictionary:
		for key in value:collect_paths(value[key], path + [key], output)
	elif value is Array:
		for index in range(value.size()):collect_paths(value[index], path + [index], output)
	elif typeof(value) in [TYPE_INT, TYPE_FLOAT, TYPE_BOOL, TYPE_STRING]:output.append(path)

func rejection_cases() -> void:
	for key in ["first_region", "midgame_slots", "job_change_unlocked"]:
		var source := Fixtures.region()
		if key == "first_region":source["first_region"]["reserve"] = null
		else:source["progress_flags"][key] = null
		run_case(source, "M11-bad-existing-" + key, "invalid_capacity_input" if key == "midgame_slots" else ("invalid_state_view" if key == "first_region" else "invalid_source"))
	var source := Fixtures.legacy()
	source["party"][0]["jp"]["warrior"] = 9223372036854775807
	run_case(source, "M11-jp-overflow", "numeric_overflow")
	source = Fixtures.region()
	source["party"][0]["learned_abilities"] = ["unknown"]
	run_case(source, "M11-unknown-old-ability", "invalid_source")
	source = Fixtures.region()
	source["equipment_stock"] = {}
	run_case(source, "M11-new-key-without-version", "unsupported_version")
	var result := run_case(Fixtures.region(), "M11-canonical")
	if not result.ok:return
	var candidate: Dictionary = result.candidate_document
	var source_doc := Fixtures.region()
	var ctx := context.duplicate()
	ctx["source_document"] = source_doc
	for label in ["unknown-version", "missing-ledger", "mixed-world", "mixed-actor", "orphan", "duplicate-owner", "float-bag", "null-bag", "policy", "audit", "extra-instance", "learned", "support-ledger"]:
		var changed := candidate.duplicate(true)
		var code := "unexpected_difference"
		match label:
			"unknown-version":changed["equipment_rules_version"] = 2; code = "unsupported_version"
			"missing-ledger":changed.erase("equipment_migration")
			"mixed-world":changed["integrated"]["armory"] = ["practice_blade"]; code = "mixed_legacy_state"
			"mixed-actor":changed["party"][0]["integrated"]["weapons"] = ["practice_blade"]; code = "mixed_legacy_state"
			"orphan":changed.equipment_stock.bag.pop_back(); code = "orphan_instance"
			"duplicate-owner":changed.equipment_stock.bag.append(changed.party[0].equipment.weapons[0]); code = "duplicate_owner"
			"float-bag":changed["equipment_stock"]["bag"][0] = 1.0; code = "invalid_instance_type"
			"null-bag":changed["equipment_stock"]["bag"][0] = null; code = "invalid_instance_type"
			"policy":changed["equipment_migration"]["policy_id"] = "unknown"
			"audit":changed["equipment_migration"]["equipment_audit"]["generated"][0]["item_id"] = "iron_blade"
			"extra-instance":changed["equipment_stock"]["instances"]["extra"] = "practice_blade";changed.equipment_stock.bag.append("extra")
			"learned":changed.party[0].learned_abilities.append("unknown");code = "unknown_ability"
			"support-ledger":changed["equipment_grants"]["actor_support"]["pc_01"] = []
		run_case(changed, "M11-tamper-" + label, code, ctx)
	# 型と構造を壊す入力は実行時エラーへ頼らない。
	for value in [null, false, 1, 1.5, "bad", [], {}]:
		var changed := candidate.duplicate(true)
		changed["equipment_stock"] = value
		run_case(changed, "M11-stock-type-" + str(typeof(value)), "invalid_stock_type", ctx)
	ctx["source_document"] = candidate
	run_case(candidate, "M11-new-source-context", "invalid_context", ctx)

func _initialize() -> void:
	expected = GameSession._normalize_numbers(JSON.parse_string(FileAccess.get_file_as_string("res://tools/fixtures/equipment-save/expectations.json")))
	session = GameSession.new()
	session.new_first_region()
	context = Fixtures.context(session)
	migration = Migration.new()
	check(Engine.get_version_info().string == "4.7.2-stable (official)", "指定Godot版")
	check(Migration.migration_id(SOURCE) == expected.stable_id.migration_id, "独立計算固定ID")
	baseline_cases()
	weapon_cases()
	legacy_cases()
	ability_and_grant_cases()
	preservation_cases()
	rejection_cases()
	check(cases.size() == 61, "固定61ケース完走")
	var output := {"checks": checks, "case_count": cases.size(), "cases": cases, "failures": failures, "observations": observations, "engine": Engine.get_version_info(), "source_sha": OS.get_environment("RPG_EQUIPMENT_SAVE_EXECUTION_SHA"), "stage": "S1", "not_verified": ["codec", "new_full_state_stats", "save_io", "normal_runtime", "real_user_saves"]}
	var destination := OS.get_environment("RPG_EQUIPMENT_SAVE_OUTPUT")
	if not destination.is_empty():
		var file := FileAccess.open(destination, FileAccess.WRITE)
		if file == null:check(false, "証拠ファイル作成")
		else:file.store_string(JSON.stringify(output, "\t") + "\n");file.close()
	print("EQUIPMENT_SAVE_MIGRATION_%s: cases=%d checks=%d failed=%d" % ["PASS" if failures.is_empty() else "FAIL", cases.size(), checks, failures.size()])
	for failure in failures:print(failure)
	quit(0 if failures.is_empty() else 1)
