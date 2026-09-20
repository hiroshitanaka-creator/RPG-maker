class_name WorldTerrain
extends RefCounted

static var _data: Dictionary = {}
static var _nodes: Dictionary = {}
static var _docks: Dictionary = {}
static var _grids: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = JSON.parse_string(FileAccess.get_file_as_string("res://world/terrain.json"))
		for node in _data["nodes"]:
			_nodes[node["id"]] = Vector2i(int(node["cell"][0]), int(node["cell"][1]))
			if node["dock"]:
				_docks[_nodes[node["id"]]] = true
	return _data

static func size_tiles() -> Vector2i:
	return Vector2i(int(data()["width"]), int(data()["height"]))

static func cell_of(id: String) -> Vector2i:
	data()
	return _nodes.get(id, Vector2i(-1, -1))

static func node_at(cell: Vector2i) -> String:
	data()
	for id in _nodes:
		if _nodes[id] == cell:
			return id
	return ""

static func tile(cell: Vector2i) -> String:
	var extent := size_tiles()
	if cell.x < 0 or cell.y < 0 or cell.x >= extent.x or cell.y >= extent.y:
		return ""
	return data()["rows"][cell.y].substr(cell.x, 1)

static func passable(cell: Vector2i, transport: String) -> bool:
	var kind := tile(cell)
	if kind.is_empty():
		return false
	match transport:
		"walk": return kind in ["g", "f", "r", "b", "n"]
		"ship": return kind in ["~", "b"] or _docks.has(cell)
		"flight": return true
	return false

static func seconds_per_step(transport: String) -> float:
	return float(data()["step_seconds"].get(transport, 0.15))

static func path(start: Vector2i, finish: Vector2i, transport: String) -> Array[Vector2i]:
	var empty: Array[Vector2i] = []
	if not passable(start, transport) or not passable(finish, transport):
		return empty
	if not _grids.has(transport):
		var grid := AStarGrid2D.new()
		grid.region = Rect2i(Vector2i.ZERO, size_tiles())
		grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
		grid.default_estimate_heuristic = AStarGrid2D.HEURISTIC_MANHATTAN
		grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_MANHATTAN
		grid.update()
		for y in range(size_tiles().y):
			for x in range(size_tiles().x):
				var cell := Vector2i(x, y)
				grid.set_point_solid(cell, not passable(cell, transport))
		_grids[transport] = grid
	return _grids[transport].get_id_path(start, finish)

static func scenery(cell: Vector2i) -> String:
	var kinds: Array[String] = []
	for y in range(cell.y - 2, cell.y + 3):
		for x in range(cell.x - 2, cell.x + 3):
			var kind := tile(Vector2i(x, y))
			if not kind.is_empty() and kind not in kinds:
				kinds.append(kind)
	kinds.sort()
	return "".join(kinds)

static func clear_cache() -> void:
	_data = {}
	_nodes = {}
	_docks = {}
	_grids = {}
