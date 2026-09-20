extends SceneTree
const AUDITOR_PATH := "res://tools/map_graph_audit.gd"
const GRAPH_PATH := "res://world/map_graph.json"

func _initialize() -> void:
	if not FileAccess.file_exists(AUDITOR_PATH):
		printerr("MAP_GRAPH_STRUCTURE_FAIL: Phase 2の検査器が未実装")
		quit(1)
		return
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(GRAPH_PATH)) != OK or not parser.data is Dictionary:
		printerr("MAP_GRAPH_STRUCTURE_FAIL: グラフをJSON辞書として読めない")
		quit(1)
		return
	var auditor = load(AUDITOR_PATH)
	var report: Dictionary = auditor.audit(parser.data)
	report["graph_sha256"] = FileAccess.get_file_as_string(GRAPH_PATH).sha256_text()
	var output := FileAccess.open("res://docs/verification/world-map-phase2.json", FileAccess.WRITE)
	if output == null:
		printerr("MAP_GRAPH_STRUCTURE_FAIL: 検査結果を保存できない")
		quit(1)
		return
	output.store_string(JSON.stringify(report, "  ", true) + "\n")
	output.close()
	for error in report["errors"]:
		printerr("MAP_GRAPH_STRUCTURE_FAIL: " + JSON.stringify(error))
	for warning in report["warnings"]:
		print("MAP_GRAPH_STRUCTURE_NOTICE: " + JSON.stringify(warning))
	if report["status"] == "PASS":
		print("MAP_GRAPH_STRUCTURE_PASS: nodes=%d reachable=%d masks=%d states=%d admissible=%d rejected=%d reachable_states=%d cycles=%d deadlocks=%d warnings=%d" % [report["node_count"], report["reachable_nodes"].size(), report["flag_combination_count"], report["state_count"], report["admissible_state_count"], report["rejected_state_count"], report["initial_reachable_state_count"], report["flag_cycles"].size(), report["deadlocks"].size(), report["warnings"].size()])
	quit(0 if report["status"] == "PASS" and report["warnings"].is_empty() else 1)
