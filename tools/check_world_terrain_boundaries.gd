extends SceneTree
var failures: Array[String] = []
var max_reverse_unchanged := 0.0

func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)

func _initialize() -> void:
	var point := Vector2i.ZERO
	for y in range(15,40):
		for x in range(15,40):
			var cell := Vector2i(x,y)
			if WorldTerrain.passable(cell,"walk") and WorldTerrain.passable(cell+Vector2i.RIGHT,"walk") and WorldTerrain.passable(cell+Vector2i(1,1),"walk"):
				point = cell
				break
		if point != Vector2i.ZERO:
			break
	check(point != Vector2i.ZERO,"検査用の連続した歩行可能セル")
	var mover := WorldMovement.new()
	var diagonal: Array[Vector2i] = [point,point+Vector2i(1,1)]
	check(not mover.begin(diagonal,"walk"),"対角移動を距離1として数えない")
	var teleport: Array[Vector2i] = [point,point+Vector2i(2,0)]
	check(not mover.begin(teleport,"walk"),"飛び越しを通常移動として認めない")
	var route: Array[Vector2i] = [point,point+Vector2i.RIGHT]
	check(mover.begin(route,"walk"),"隣接する通常経路を受理")
	check(mover.advance(-1) == 0 and mover.advance(INF) == 0 and mover.cell == point,"負の時間と無限時間を拒否")
	check(mover.advance(0.14) == 0 and mover.cell == point,"150ms未満では次のセルへ進まない")
	check(mover.advance(0.01) == 1 and mover.cell == route[1] and not mover.active(),"150msで1セル移動")
	check(absf(mover.elapsed_seconds-0.15) < 0.00001,"ゲーム内の計測時間を保存")
	check(not WorldTerrain.passable(Vector2i(-1,0),"flight") and not WorldTerrain.passable(Vector2i(256,255),"flight"),"飛行でもマップ境界を越えない")
	check(not WorldTerrain.passable(point,"unknown"),"未定義の移動手段を拒否")
	var target := WorldTerrain.cell_of("town")
	var original: Dictionary = WorldTerrain.data().duplicate(true)
	var row: String = WorldTerrain._data["rows"][target.y]
	WorldTerrain._data["rows"][target.y] = row.substr(0,target.x)+"m"+row.substr(target.x+1)
	WorldTerrain._grids = {}
	check(WorldTerrain.path(point,target,"walk").is_empty(),"拠点が山で塞がれた地形の経路探索は失敗")
	var blocked: Array[Vector2i] = [target]
	check(not mover.begin(blocked,"walk"),"移動処理も通行不能な終点を拒否")
	WorldTerrain._data = original
	WorldTerrain._grids = {}
	var restored := WorldTerrain.path(point,target,"walk")
	check(not restored.is_empty(),"地形を復元すると経路探索も復元")
	var return_path := WorldTerrain.path(target,point,"walk")
	check(not return_path.is_empty() and return_path.size() == restored.size(),"復路も同じ距離で実際に通れる")
	var graph: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://world/map_graph.json"))
	var reverse_checked := 0
	for edge in graph["edges"]:
		if edge["one_way"]:
			continue
		var path := WorldTerrain.path(WorldTerrain.cell_of(edge["to"]),WorldTerrain.cell_of(edge["from"]),edge["required_transport"])
		if not check_path(path,edge):
			continue
		reverse_checked += 1
	check(reverse_checked == 61,"双方向61接続すべての逆方向を検査")
	WorldTerrain.clear_cache()
	var output := FileAccess.open("res://docs/verification/world-terrain-boundaries.json",FileAccess.WRITE)
	if output != null:
		output.store_string(JSON.stringify({"status":"PASS" if failures.is_empty() else "FAIL","errors":failures,"reverse_edges":reverse_checked,"max_unchanged_seconds":snappedf(max_reverse_unchanged,0.001),"time_source":"production_movement_fixed_delta_60hz","scope":"blocked_terrain_movement_clock_and_reverse_routes"},"  ",true)+"\n")
		output.close()
	for error in failures:
		printerr("WORLD_TERRAIN_BOUNDARY_FAIL: "+error)
	if failures.is_empty():
		print("WORLD_TERRAIN_BOUNDARY_PASS: reverse_edges=%d errors=0" % reverse_checked)
	quit(0 if failures.is_empty() else 1)

func check_path(path: Array[Vector2i], edge: Dictionary) -> bool:
	if path.is_empty():
		check(false,edge["id"]+": 復路なし")
		return false
	var mover := WorldMovement.new()
	check(mover.begin(path,edge["required_transport"]),"復路を本番移動処理へ渡す")
	while mover.active():
		mover.advance(1.0/60.0)
	check(mover.elapsed_seconds >= float(edge["expected_travel_seconds"])*0.5 and mover.elapsed_seconds <= float(edge["expected_travel_seconds"])*1.5,edge["id"]+": 復路の秒数が±50%以内")
	var previous := ""
	var same := 0.0
	var longest := 0.0
	for cell in path:
		var scenery := WorldTerrain.scenery(cell)
		same = same+WorldTerrain.seconds_per_step(edge["required_transport"]) if previous == scenery and WorldTerrain.node_at(cell).is_empty() else 0.0
		longest = maxf(longest,same)
		previous = scenery
	check(longest < 20,edge["id"]+": 復路も地形変化と拠点がない連続区間は20秒未満")
	max_reverse_unchanged = maxf(max_reverse_unchanged,longest)
	return true
