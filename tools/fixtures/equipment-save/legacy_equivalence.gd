extends SceneTree
## 同じ固定入力を抽出前後の実GameSession/upgradeで実行する。
const Fixtures = preload("res://tools/fixtures/equipment-save/fixtures.gd")
var failures: Array = []
var validation: Array = []
var upgrades: Array = []
var session: GameSession

func same(left: Variant, right: Variant) -> bool:
	return left == right and SavedValueTypes.same_types(left, right)

func evaluate(document: Dictionary, label: String) -> void:
	var before := document.duplicate(true)
	var state := session.export_state()
	var metrics := session.play_metrics.snapshot()
	var valid: bool = session._valid_state(document)
	var unchanged := same(document, before) and same(state, session.export_state()) and same(metrics, session.play_metrics.snapshot())
	if not unchanged:failures.append(label + "旧検証の入力/状態/計測副作用")
	validation.append({"case": label, "valid": valid, "unchanged": unchanged})

func upgrade_case(document: Dictionary, label: String) -> void:
	var before := document.duplicate(true)
	var pure: Dictionary = IntegratedProgression.upgrade(document, session.jobs) if document.format_version == 1 else document.duplicate(true)
	if not same(before, document):failures.append(label + "純粋upgrade入力不変")
	var imported: bool = session.import_state(document)
	var previous := session.export_state()
	var metrics := session.play_metrics.snapshot()
	var upgraded: bool = session.upgrade_rules()
	var result := session.export_state()
	var after_metrics := session.play_metrics.snapshot()
	var second: bool = session.upgrade_rules()
	if not same(result, session.export_state()) or not same(after_metrics, session.play_metrics.snapshot()):failures.append(label + "再更新不変")
	var path := "user://task041-legacy-equivalence.json"
	var saved: bool = session.save_game(path)
	var load_session := GameSession.new()
	var loaded: bool = load_session.load_game(path)
	var roundtrip := same(result, load_session.export_state()) and same(after_metrics, load_session.play_metrics.snapshot())
	if not imported or not saved or not loaded or not roundtrip:failures.append(label + "既存I/O往復")
	if persons(result).any(func(actor: Dictionary):return "two_handed" in actor.learned_abilities):failures.append(label + "旧入口で新能力追加")
	upgrades.append({"case": label, "input": before, "input_types": SavedValueTypes.describe(before), "pure_upgrade": pure, "pure_types": SavedValueTypes.describe(pure), "imported": imported, "before": previous, "metrics_before": metrics, "upgraded": upgraded, "after": result, "after_types": SavedValueTypes.describe(result), "metrics_after": after_metrics, "second": second, "saved": saved, "loaded": loaded, "roundtrip": roundtrip})

func persons(document: Dictionary) -> Array:
	return document.party + document.get("first_region", {}).get("reserve", [])

func _initialize() -> void:
	session = GameSession.new()
	for document in [Fixtures.base(), Fixtures.region(), Fixtures.legacy(), Fixtures.legacy(false, 3), Fixtures.legacy(true)]:
		var label := "%d-%d-%s" % [document.format_version, document.party.size(), document.has("first_region")]
		evaluate(document, "normal-" + label)
		upgrade_case(document, "normal-" + label)
	for field in Fixtures.base().party[0]:
		var missing := Fixtures.base()
		missing.party[0].erase(field)
		evaluate(missing, "missing-actor-" + field)
		for value in [null, false, 1, 1.5, "unknown", [], {}]:
			var changed := Fixtures.base()
			changed.party[0][field] = value
			evaluate(changed, "actor-type-" + field + "-%d" % typeof(value))
	for index in range(3):
		var source := Fixtures.legacy()
		source.party[0].jp["warrior"] = [12, 24, 36][index]
		if index == 1:source.party[0]["mastered_jobs"] = ["warrior"]
		source.party[1].jp["beast"] = 18
		Fixtures.caps(source.party[0], session)
		upgrade_case(source, "legacy-jp%d" % index)
	var old_mastery := Fixtures.base()
	old_mastery.integrated.erase("mastery_rules_version")
	for actor in old_mastery.party:actor.integrated.erase("mastery")
	upgrade_case(old_mastery, "format2-unrecorded-mastery")
	var duplicate := Fixtures.base()
	duplicate.party[1]["id"] = duplicate.party[0].id
	evaluate(duplicate, "duplicate-id")
	var typed := Fixtures.legacy()
	var people: Array[Dictionary] = []
	people.assign(typed.party)
	typed["party"] = people
	var skills: Array[String] = []
	typed.party[0]["learned_abilities"] = skills
	upgrade_case(typed, "typed-party-skills")
	var report := {"validation_count": validation.size(), "upgrade_count": upgrades.size(), "validation": validation, "upgrades": upgrades, "failures": failures}
	var output := OS.get_environment("RPG_LEGACY_EQ_OUTPUT")
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file == null:failures.append("証拠作成")
		else:file.store_string(JSON.stringify(report, "\t") + "\n");file.close()
	print("LEGACY_EQUIVALENCE_%s: validation=%d upgrade=%d failures=%d" % ["PASS" if failures.is_empty() else "FAIL", validation.size(), upgrades.size(), failures.size()])
	for failure in failures:print(failure)
	quit(0 if failures.is_empty() else 1)
