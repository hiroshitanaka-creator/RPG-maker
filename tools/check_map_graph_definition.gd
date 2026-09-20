extends SceneTree
## Phase 1の定義検査。到達性・詰み・地形の合格を代用しない。

const GRAPH_PATH := "res://world/map_graph.json"
const KINDS := ["town", "dungeon", "outpost"]
const MODES := ["walk", "ship", "flight"]
var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)

func integer(value: Variant, minimum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) == floor(float(value)) and value >= minimum

func identifier(value: Variant) -> bool:
	if not value is String or value.is_empty():
		return false
	var pattern := RegEx.new()
	pattern.compile("^[a-z][a-z0-9_]*$")
	return pattern.search(value) != null

func indexed(items: Variant, label: String) -> Dictionary:
	var result: Dictionary = {}
	if not items is Array:
		check(false, label + ": 配列が必要")
		return result
	for item in items:
		if not item is Dictionary or not identifier(item.get("id")):
			check(false, label + ": 辞書と有効なIDが必要")
			continue
		check(not result.has(item["id"]), label + ": ID重複 " + item["id"])
		result[item["id"]] = item
	return result

func references(values: Variant, targets: Dictionary, label: String) -> void:
	if not values is Array:
		check(false, label + ": 配列が必要")
		return
	var seen: Array = []
	for value in values:
		check(value is String and targets.has(value), label + ": 未定義参照 " + str(value))
		check(value not in seen, label + ": 参照重複")
		seen.append(value)

func no_coordinates(value: Variant) -> void:
	if value is Dictionary:
		for key in value:
			check(key not in ["x", "y", "cell", "spawn", "position", "coordinates", "layout", "tiles", "waypoints"], "Phase 1への座標・地形混入: " + str(key))
			no_coordinates(value[key])
	elif value is Array:
		for item in value:
			no_coordinates(item)

func _initialize() -> void:
	if not FileAccess.file_exists(GRAPH_PATH):
		printerr("MAP_GRAPH_DEFINITION_FAIL: world/map_graph.json が存在しない")
		quit(1)
		return
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(GRAPH_PATH)) != OK or not parser.data is Dictionary:
		printerr("MAP_GRAPH_DEFINITION_FAIL: JSON辞書として読めない")
		quit(1)
		return
	var data: Dictionary = parser.data
	no_coordinates(data)
	check(data.get("version") == 1, "定義版は1")
	check(data.get("status") in ["phase_1_proposal","runtime_graph"], "提案と実行時接続の状態を明示")
	check(data.get("runtime_connected") is bool, "実行時接続は真偽値")
	if data.get("runtime_connected") == true:
		check(data.get("status") == "runtime_graph" and FileAccess.file_exists("res://world/terrain.json") and FileAccess.file_exists("res://world/interiors.json"), "接続済み表示には地形と内部データが必要")
	var regions := indexed(data.get("regions"), "地方")
	var nodes := indexed(data.get("nodes"), "拠点")
	var edges := indexed(data.get("edges"), "接続")
	var flags := indexed(data.get("flags"), "フラグ")
	var transports := indexed(data.get("transports"), "移動手段")
	check(regions.size() >= 3 and regions.size() <= 4, "地方3〜4")
	check(transports.size() == 3, "移動手段3")
	check(nodes.has(data.get("start_node")), "開始拠点の参照")
	check(nodes.has(data.get("completion_node")), "構造上の終点の参照")
	var counts := {"town": 0, "dungeon": 0, "outpost": 0}
	var tiers := {"walk": 0, "ship": 0, "flight": 0}
	var indices: Array = []
	for mode in MODES:
		check(transports.has(mode), "移動手段不足: " + mode)
		if transports.has(mode):
			var transport: Dictionary = transports[mode]
			check(transport.get("stage") == MODES.find(mode), "移動段階の対応")
			references(transport.get("unlock_flags"), flags, "乗り物解放")
	for id in nodes:
		var node: Dictionary = nodes[id]
		check(node.has_all(["id", "name", "type", "region", "recommended_level", "progression_index", "required_transport", "unlock_flags", "story_role", "origin"]), id + ": 必須項目不足")
		check(node.get("name") is String and not str(node.get("name", "")).is_empty(), id + ": 名称")
		check(node.get("type") in KINDS, id + ": 種別")
		check(regions.has(node.get("region")), id + ": 地方参照")
		check(integer(node.get("recommended_level"), 1), id + ": 推奨レベルは正整数")
		check(integer(node.get("progression_index"), 1), id + ": 進行順は正整数")
		check(node.get("progression_index") not in indices, id + ": 進行順重複")
		indices.append(node.get("progression_index"))
		check(node.get("required_transport") in MODES, id + ": 移動手段")
		references(node.get("unlock_flags"), flags, id + ": 解放条件")
		check(node.get("story_role") is String and not str(node.get("story_role", "")).is_empty(), id + ": 物語の役割")
		check(node.get("origin") in ["existing", "proposed"], id + ": 既存と提案の区別")
		if node.get("type") in KINDS:
			counts[node["type"]] += 1
		if node.get("required_transport") in MODES:
			tiers[node["required_transport"]] += 1
	check(counts["town"] >= 10 and counts["town"] <= 12, "町村10〜12")
	check(counts["dungeon"] >= 14 and counts["dungeon"] <= 18, "ダンジョン14〜18")
	check(counts["outpost"] >= 20 and counts["outpost"] <= 25, "小拠点20〜25")
	var existing_count := 0
	for node in nodes.values():
		if node.get("origin") == "existing":
			existing_count += 1
			check(ChapterOne.TITLES.has(node["id"]), "未知の既存拠点")
	check(existing_count == ChapterOne.TITLES.size(), "既存8拠点を保持")
	for id in ChapterOne.TITLES:
		check(nodes.has(id), "既存拠点不足: " + id)
		if nodes.has(id):
			check(nodes[id].get("name") == ChapterOne.TITLES[id], "既存名を保持: " + id)
			check(nodes[id].get("type") == ("town" if id in ChapterOne.TOWNS else "dungeon"), "既存種別を保持: " + id)
	for id in flags:
		var flag: Dictionary = flags[id]
		check(flag.get("initial") == false, id + ": 初期値")
		check(flag.get("persistent") == true and flag.get("consumable") == false, id + ": 永続・非消費")
		check(nodes.has(flag.get("producer_node")), id + ": 設定元の拠点")
		check(flag.get("trigger") is String and not str(flag.get("trigger", "")).is_empty(), id + ": 設定契機")
		references(flag.get("requires"), flags, id + ": 前提フラグ")
	var edge_pairs: Array = []
	for id in edges:
		var edge: Dictionary = edges[id]
		check(edge.has_all(["id", "from", "to", "required_transport", "expected_travel_seconds", "one_way", "unlock_flags"]), id + ": 接続項目不足")
		check(nodes.has(edge.get("from")) and nodes.has(edge.get("to")), id + ": 接続先不足")
		check(edge.get("from") != edge.get("to"), id + ": 自己接続")
		check(edge.get("required_transport") in MODES, id + ": 移動手段")
		check(integer(edge.get("expected_travel_seconds"), 1), id + ": 想定秒数")
		check(edge.get("one_way") is bool, id + ": 一方通行は真偽値")
		references(edge.get("unlock_flags"), flags, id + ": 接続条件")
		var pair := str(edge.get("from")) + ">" + str(edge.get("to"))
		check(pair not in edge_pairs, id + ": 接続重複")
		edge_pairs.append(pair)
		if edge.get("one_way") == false:
			edge_pairs.append(str(edge.get("to")) + ">" + str(edge.get("from")))
	var legacy: Array = ChapterOne.STEPS.duplicate(true)
	legacy.append_array(StoryCampaign.data()["route"])
	for branch in StoryCampaign.data()["branches"].values():
		legacy.append_array(branch)
	var legacy_pairs: Array = []
	for entry in legacy:
		if entry.get("kind") != "travel":
			continue
		var pair: String = entry["location"] + ">" + entry["destination"]
		check(pair in edge_pairs, "既存接続不足: " + pair)
		if pair not in legacy_pairs:
			legacy_pairs.append(pair)
	for message in failures:
		printerr("MAP_GRAPH_DEFINITION_FAIL: " + message)
	if failures.is_empty():
		print("MAP_GRAPH_DEFINITION_PASS: regions=%d nodes=%d towns=%d dungeons=%d outposts=%d edges=%d legacy_edges=%d walk=%d ship=%d flight=%d flags=%d errors=0 coordinates=0 scope=definition_only" % [regions.size(), nodes.size(), counts["town"], counts["dungeon"], counts["outpost"], edges.size(), legacy_pairs.size(), tiers["walk"], tiers["ship"], tiers["flight"], flags.size()])
	quit(0 if failures.is_empty() else 1)
