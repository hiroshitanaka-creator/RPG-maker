extends SceneTree
## 時間を加速せず、61接続を本番の移動処理で走る。途中結果はRUNNINGのまま保存。
var _edges: Array = []
var _results: Array = []
var _errors: Array[String] = []
var _mover := WorldMovement.new()
var _at := -1
var _start_usec := 0
var _skip_start := true
var _hashes: Dictionary = {}

func _initialize() -> void:
	Engine.max_fps = 60
	var graph: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://world/map_graph.json"))
	_edges = graph["edges"]
	for path in ["res://world/map_graph.json", "res://world/terrain.json", "res://scripts/world/world_movement.gd", "res://scripts/world/world_terrain.gd"]:
		_hashes[path] = FileAccess.get_file_as_string(path).sha256_text()
	_next_edge()

func _next_edge() -> void:
	_at += 1
	if _at >= _edges.size():
		for path in _hashes:
			if _hashes[path] != FileAccess.get_file_as_string(path).sha256_text():
				_errors.append("実測中に対象が変更された: " + path)
		_save("PASS" if _errors.is_empty() else "FAIL")
		for error in _errors:
			printerr("WORLD_REALTIME_FAIL: " + error)
		if _errors.is_empty():
			print("WORLD_REALTIME_PASS: edges=%d errors=0" % _results.size())
		quit(0 if _errors.is_empty() else 1)
		return
	var edge: Dictionary = _edges[_at]
	var path := WorldTerrain.path(WorldTerrain.cell_of(edge["from"]), WorldTerrain.cell_of(edge["to"]), edge["required_transport"])
	if not _mover.begin(path, edge["required_transport"]):
		_errors.append(edge["id"] + ": 経路なし")
		_save("FAIL")
		quit(1)
		return
	_skip_start = true

func _process(delta: float) -> bool:
	if _at >= _edges.size():
		return false
	if _skip_start:
		_start_usec = Time.get_ticks_usec()
		_skip_start = false
		return false
	_mover.advance(delta)
	if _mover.active():
		return false
	var wall := (Time.get_ticks_usec() - _start_usec) / 1000000.0
	var edge: Dictionary = _edges[_at]
	var expected := float(edge["expected_travel_seconds"])
	if wall < expected * 0.5 or wall > expected * 1.5 or _mover.cell != WorldTerrain.cell_of(edge["to"]):
		_errors.append(edge["id"] + ": 実時間%.3f秒 / 想定%.3f秒" % [wall, expected])
	_results.append({"id":edge["id"], "expected_seconds":expected, "wall_seconds":wall, "movement_seconds":_mover.elapsed_seconds, "arrival":[_mover.cell.x, _mover.cell.y]})
	print("WORLD_REALTIME_PROGRESS: %d/%d %.3fs" % [_results.size(), _edges.size(), wall])
	_save("RUNNING")
	_next_edge()
	return false

func _save(status: String) -> void:
	var file := FileAccess.open("res://docs/verification/world-terrain-realtime.json", FileAccess.WRITE)
	if file == null:
		_errors.append("実測記録の保存先を開けない")
		return
	file.store_string(JSON.stringify({"status":status, "time_source":"monotonic_wall_clock_no_acceleration", "hashes":_hashes, "edges_measured":_results.size(), "edges_required":_edges.size(), "routes":_results, "errors":_errors}, "  ", true) + "\n")
	file.close()
