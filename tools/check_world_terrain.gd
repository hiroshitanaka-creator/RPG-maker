extends SceneTree
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var graph: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://world/map_graph.json"))
	var terrain := WorldTerrain.data()
	check(WorldTerrain.size_tiles() == Vector2i(256, 256), "地形は256×256タイル")
	check(terrain["graph_sha256"] == FileAccess.get_file_as_string("res://world/map_graph.json").sha256_text(), "グラフの版が一致")
	var route_results: Array = []
	for edge in graph["edges"]:
		var path := WorldTerrain.path(WorldTerrain.cell_of(edge["from"]), WorldTerrain.cell_of(edge["to"]), edge["required_transport"])
		check(not path.is_empty(), edge["id"] + ": 実地形に経路が存在")
		if path.is_empty():
			continue
		var mover := WorldMovement.new()
		check(mover.begin(path, edge["required_transport"]), edge["id"] + ": 本番移動処理で経路を受理")
		while mover.active():
			mover.advance(1.0 / 60.0)
		check(mover.cell == WorldTerrain.cell_of(edge["to"]), edge["id"] + ": 終点へ到達")
		var measured := mover.elapsed_seconds
		var expected := float(edge["expected_travel_seconds"])
		check(measured >= expected * 0.5 and measured <= expected * 1.5, edge["id"] + ": 移動秒数 %.2f / 想定%.2f" % [measured, expected])
		var longest := 0.0
		var segment := 0.0
		var previous := ""
		for cell in path:
			var signature := WorldTerrain.scenery(cell)
			if signature != previous or not WorldTerrain.node_at(cell).is_empty():
				segment = 0
			else:
				segment += WorldTerrain.seconds_per_step(edge["required_transport"])
			longest = maxf(longest, segment)
			previous = signature
		check(longest < 20.0, edge["id"] + ": 地形変化・拠点なしの区間 %.2f秒" % longest)
		route_results.append({"id": edge["id"], "steps": path.size()-1, "transport": edge["required_transport"], "expected_seconds": expected, "movement_seconds": snappedf(measured, 0.001), "longest_unchanged_seconds": snappedf(longest, 0.001)})
	var visited: Dictionary = {}
	var land := 0
	var unused := 0
	var components := 0
	for y in range(256):
		for x in range(256):
			var origin := Vector2i(x, y)
			if visited.has(origin) or WorldTerrain.tile(origin) == "~":
				continue
			components += 1
			var queue: Array[Vector2i] = [origin]
			visited[origin] = true
			var at := 0
			var useful := false
			while at < queue.size():
				var cell := queue[at]
				at += 1
				useful = useful or not WorldTerrain.node_at(cell).is_empty()
				for direction in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
					var next: Vector2i = cell + direction
					if not visited.has(next) and WorldTerrain.tile(next) not in ["", "~"]:
						visited[next] = true
						queue.append(next)
			land += queue.size()
			if not useful:
				unused += queue.size()
	var orphan_land := unused
	# 飛行で上を通れるだけでは利用可能な陸地に数えない。
	# 全edge到達が成立した拠点入口から、徒歩で入れる陸地を実際に探索する。
	var ground_queue: Array[Vector2i] = []
	var accessible: Dictionary = {}
	for node in terrain["nodes"]:
		var cell := WorldTerrain.cell_of(node["id"])
		ground_queue.append(cell)
		accessible[cell] = true
	var ground_at := 0
	while ground_at < ground_queue.size():
		var cell := ground_queue[ground_at]
		ground_at += 1
		for direction in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
			var next: Vector2i = cell + direction
			if not accessible.has(next) and WorldTerrain.passable(next, "walk"):
				accessible[next] = true
				ground_queue.append(next)
	unused = land - accessible.size()
	check(land > 0 and float(unused) / land < 0.05, "拠点入口から入れない陸地が総陸地の5%未満")
	var result := {"status": "PASS" if failures.is_empty() else "FAIL", "errors": failures, "graph_sha256": terrain["graph_sha256"], "terrain_sha256": FileAccess.get_file_as_string("res://world/terrain.json").sha256_text(), "width":256, "height":256, "nodes": terrain["nodes"].size(), "edges":route_results.size(), "routes":route_results, "land_tiles":land, "unused_land_tiles":unused, "orphan_island_tiles":orphan_land, "land_components":components, "time_source":"production_movement_fixed_delta_60hz", "wall_clock_trials":"NOT_RUN"}
	var output := FileAccess.open("res://docs/verification/world-terrain.json", FileAccess.WRITE)
	check(output != null, "地形検査結果の保存先を開く")
	if output != null:
		output.store_string(JSON.stringify(result, "  ", true) + "\n")
		output.close()
	for message in failures:
		printerr("WORLD_TERRAIN_FAIL: " + message)
	if failures.is_empty():
		print("WORLD_TERRAIN_PASS: tiles=65536 nodes=%d edges=%d unused_land=%d/%d errors=0" % [terrain["nodes"].size(), route_results.size(), unused, land])
	quit(0 if failures.is_empty() else 1)
