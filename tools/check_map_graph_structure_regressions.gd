extends SceneTree
## 検査器へ壊したコピーを渡す。本体JSONや既存の保護テストは書き換えない。
var failures: Array[String] = []
var cases := 0

func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)

func detects(data: Dictionary, code: String, name: String) -> Dictionary:
	cases += 1
	var report := WorldMapGraphAudit.audit(data)
	var codes: Array = []
	for item in report["errors"]:
		codes.append(item["code"])
	check(report["status"] == "FAIL" and code in codes, name + ": " + code + "を検出する")
	return report

func tiny_graph() -> Dictionary:
	# 手で数えられる4拠点・2フラグ。通常到達9状態、不整合込み12状態。
	return {
		"start_node": "a", "completion_node": "d",
		"transports": [
			{"id": "walk", "stage": 0, "unlock_flags": [], "retains": []},
			{"id": "ship", "stage": 1, "unlock_flags": ["s"], "retains": ["walk"]},
			{"id": "flight", "stage": 2, "unlock_flags": ["f"], "retains": ["walk", "ship"]}],
		"flags": [
			{"id": "s", "initial": false, "persistent": true, "consumable": false, "producer_node": "b", "requires": []},
			{"id": "f", "initial": false, "persistent": true, "consumable": false, "producer_node": "c", "requires": ["s"]}],
		"nodes": [
			{"id": "a", "progression_index": 1, "recommended_level": 1, "required_transport": "walk", "unlock_flags": []},
			{"id": "b", "progression_index": 2, "recommended_level": 2, "required_transport": "walk", "unlock_flags": []},
			{"id": "c", "progression_index": 3, "recommended_level": 3, "required_transport": "ship", "unlock_flags": ["s"]},
			{"id": "d", "progression_index": 4, "recommended_level": 4, "required_transport": "flight", "unlock_flags": ["f"]}],
		"edges": [
			{"id": "ab", "from": "a", "to": "b", "required_transport": "walk", "unlock_flags": [], "one_way": false},
			{"id": "bc", "from": "b", "to": "c", "required_transport": "ship", "unlock_flags": ["s"], "one_way": false},
			{"id": "cd", "from": "c", "to": "d", "required_transport": "flight", "unlock_flags": ["s", "f"], "one_way": false},
			{"id": "ad", "from": "a", "to": "d", "required_transport": "flight", "unlock_flags": ["f"], "one_way": false}]
	}

func _initialize() -> void:
	var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://world/map_graph.json"))
	var before := JSON.stringify(original)
	var report := WorldMapGraphAudit.audit(original)
	cases += 1
	check(report["status"] == "PASS" and report["warnings"].is_empty(), "実際のグラフを合格させる")
	check(report["state_count"] == 392 and report["admissible_state_count"] == 224 and report["rejected_state_count"] == 168, "全8組合せ×49拠点を分類する")
	check(report["initial_reachable_state_count"] == 106 and report["reachable_nodes"].size() == 49, "正規の解放順も探索する")
	check(report["flag_cycles"].is_empty() and report["deadlocks"].is_empty(), "実際の循環・詰みは0")
	check(JSON.stringify(original) == before, "検査で入力データを書き換えない")

	var broken := original.duplicate(true)
	broken["edges"] = broken["edges"].filter(func(e: Dictionary) -> bool: return e["from"] != "river_watch" and e["to"] != "river_watch")
	detects(broken, "unreachable_nodes", "孤立拠点")

	broken = original.duplicate(true)
	broken["flags"][0]["requires"] = ["world_flight_unlocked"]
	detects(broken, "flag_cycle", "三つのフラグの循環")

	broken = original.duplicate(true)
	broken["flags"][1]["producer_node"] = "brine_port"
	detects(broken, "flag_cycle", "船が必要な場所で船を解放する自己依存")

	broken = original.duplicate(true)
	for edge in broken["edges"]:
		if edge["from"] == "shipyard" or edge["to"] == "shipyard":
			edge["unlock_flags"].append("world_ship_unlocked")
	detects(broken, "flag_cycle", "設定場所への全経路が同じフラグを要求")

	broken = original.duplicate(true)
	for edge in broken["edges"]:
		if edge["to"] == "river_watch":
			edge["one_way"] = true
	var trapped := detects(broken, "deadlock", "入れるが戻れない一方通行")
	check(trapped["reachable_deadlock_count"] > 0, "通常進行で到達する閉じ込めを検出")
	check(not trapped["deadlocks"][0]["witness_from_start"].is_empty(), "閉じ込めへの具体的な到達経路を残す")

	broken = original.duplicate(true)
	broken["edges"] = broken["edges"].filter(func(e: Dictionary) -> bool: return "incomplete_flags_recovery" not in e.get("roles", []))
	var partial := detects(broken, "deadlock", "Phase 1の不整合フラグ時の閉じ込め")
	check(partial["deadlocks"].size() == 80 and partial["reachable_deadlock_count"] == 0, "通常進行外の80状態も除外せず検出")

	broken = original.duplicate(true)
	broken["nodes"][10]["recommended_level"] = 1
	detects(broken, "progression_order", "推奨レベルの逆行")

	broken = original.duplicate(true)
	broken["nodes"][10]["progression_index"] = 1
	detects(broken, "progression_order", "進行順の重複")

	broken = original.duplicate(true)
	broken["nodes"][10]["unlock_flags"] = ["missing_flag"]
	detects(broken, "schema", "未定義フラグ")

	broken = original.duplicate(true)
	broken["edges"][0]["to"] = "missing_node"
	detects(broken, "schema", "未定義拠点")

	broken = original.duplicate(true)
	broken["nodes"][10]["recommended_level"] = 2.5
	detects(broken, "schema", "整数への勝手な丸め")

	broken = original.duplicate(true)
	broken["transports"][0]["retains"] = ["flight"]
	detects(broken, "schema", "徒歩による飛行の先取り")

	broken = original.duplicate(true)
	broken["flags"][0]["consumable"] = true
	detects(broken, "unsupported_transition", "未対応のフラグ消費を成功扱いしない")

	cases += 1
	var reordered := original.duplicate(true)
	reordered["nodes"].reverse()
	reordered["flags"].reverse()
	reordered["edges"].reverse()
	var reversed := WorldMapGraphAudit.audit(reordered)
	check(reversed["status"] == "PASS" and reversed["admissible_state_count"] == 224 and reversed["initial_reachable_state_count"] == 106, "格納順を変更しても同じ状態集合")

	cases += 1
	var tiny := WorldMapGraphAudit.audit(tiny_graph())
	check(tiny["status"] == "PASS" and tiny["state_count"] == 16 and tiny["admissible_state_count"] == 12 and tiny["initial_reachable_state_count"] == 9, "手計算した4拠点モデルと一致")
	check(tiny["warnings"].size() == 3, "解放後5拠点未満なら徒歩・船・飛行それぞれ警告")
	for warning in tiny["warnings"]:
		check(warning["code"] == "weak_transport_unlock", "警告理由を区別")
	check(tiny["flag_cycles"].is_empty(), "地理の周回経路をフラグ循環と誤認しない")

	for message in failures:
		printerr("MAP_GRAPH_REGRESSION_FAIL: " + message)
	if failures.is_empty():
		print("MAP_GRAPH_REGRESSION_PASS: cases=%d errors=0" % cases)
	quit(0 if failures.is_empty() else 1)
