extends SceneTree
var failures: Array[String] = []
func check(ok: bool, message: String) -> void:
	if not ok:failures.append(message)
func _initialize() -> void:
	var game: Variant = GameSession.new()
	check(game.new_game(4),"本番の新規開始が成立する")
	check(game.export_state().get("format_version")==2,"通常の新規開始に新ルールと保存形式を適用")
	for method in ["integrated_preview","bind_focus","equip_weapon","integration_knowledge","upgrade_rules"]:
		check(game.has_method(method),"本番API: "+method)
	for path in ["data/integrated_rules.json","scripts/combat/encounter_effects.gd","scripts/game/integrated_progression.gd"]:
		check(FileAccess.file_exists("res://"+path),"本番データ・状態所有者: "+path)
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","failures":failures,"scope":"実装入口の基準。戦闘・保存・UI・全編の実行検証は別の検査で必須。","build":BuildIdentity.current()}
	PlaySessionMetrics.write_json("res://docs/verification/integrated-entry-current.json",report)
	for failure in failures:printerr("INTEGRATED_ENTRY_FAIL: "+failure)
	if failures.is_empty():print("INTEGRATED_ENTRY_PASS: 通常開始と本番の新機構入口")
	quit(0 if failures.is_empty() else 1)
