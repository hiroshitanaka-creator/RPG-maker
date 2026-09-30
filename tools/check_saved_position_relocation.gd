extends SceneTree
## 保存を読み込んだとき、立ち位置が「その部屋の歩けないマス」になっていたら、部屋の入口の扉の前へ置き直す仕組みを確かめる。
## 部屋の作りを変えたあと、以前の保存が読み込めなくなるのを防ぐ共通の仕組み（FirstRegion.relocate_unwalkable / GameSession.load_game）。
var failures: Array[String] = []
var checks := 0

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:failures.append(message)

func region_state() -> Dictionary:
	var game := GameSession.new()
	check(game.new_first_region(),"最初の地方を新規開始")
	return game.export_state()

func write_case(path: String, base: Dictionary, node: String, room: int, cell: Array) -> void:
	# 通常の保存を一度書き、立ち位置だけを書き換える（補助情報の型の記録はそのまま）。
	var game := GameSession.new()
	var state := base.duplicate(true)
	state["inventory"]["gate_pass"] = 1
	state["overworld"]["cleared"].append("first_boss")
	state["overworld"]["layer"] = "interior";state["overworld"]["node"] = "first_castle";state["overworld"]["room"] = 3
	state["overworld"]["cell"] = [8,10]
	check(game.import_state(state),"歩ける位置の状態を読み込める")
	check(game.save_game(path),"保存を書く")
	var document: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	document["overworld"]["node"] = node;document["overworld"]["room"] = room;document["overworld"]["cell"] = cell
	check(PlaySessionMetrics.write_json(path,document),"立ち位置を書き換えた保存を用意")

func load_case(label: String, node: String, room: int, cell: Array, expected_relocated: bool, expected_cell: Array) -> void:
	var path := "user://qa_relocation_%s.json" % label
	write_case(path,region_state(),node,room,cell)
	var loaded := GameSession.new()
	var ok := loaded.load_game(path)
	check(ok,"読み込める: "+label)
	if not ok:return
	var here: Dictionary = loaded.export_state()["overworld"]
	check(loaded.position_relocated == expected_relocated,"置き直しの有無: "+label)
	check(here["cell"] == expected_cell,"読み込み後の位置 %s: %s" % [str(expected_cell),label])
	check(here["node"] == node and here["room"] == room,"部屋は変わらない: "+label)
	check(loaded.first_region_walkable(Vector2i(here["cell"][0],here["cell"][1])),"読み込み後の位置は歩ける: "+label)
	# 置き直した保存を保存し直して読み直しても、もう置き直さない。
	var again := "user://qa_relocation_%s_again.json" % label
	check(loaded.save_game(again),"置き直した状態を保存: "+label)
	var second := GameSession.new()
	check(second.load_game(again) and not second.position_relocated and second.export_state() == loaded.export_state(),"再保存した保存はそのまま読める: "+label)

func _initialize() -> void:
	var definition := FirstRegion.data()
	# 1. 部屋の入口の扉の前（着地マス）が、全部屋に定義されていて歩ける。
	var rooms := 0
	for site in FirstRegion._data["sites"]:
		# 最初の地方として保存できる場所（FirstRegion.valid が許す node）だけを対象にする。
		if site["id"] not in ["start_village","first_cave","first_castle","first_forest_tower","first_port"]:continue
		for index in range(site["rooms"].size()):
			rooms += 1
			var landing := FirstRegion.entrance_landing(site["id"],index)
			check(not landing.is_empty(),"入口の着地マスがある: %s:%d" % [site["id"],index])
			if landing.is_empty():continue
			var probe := {"overworld":{"layer":"interior","node":site["id"],"room":index,"cell":landing,"transport":"walk","entry_lock":"x"},"first_region":{},"party":[]}
			check(FirstRegion.walkable(probe,Vector2i(landing[0],landing[1])),"入口の着地マスは歩ける: %s:%d" % [site["id"],index])
			# どの部屋でも、部屋の外の座標に立つ保存は入口の扉の前へ戻る。歩ける位置はそのまま。
			var outside := probe.duplicate(true);outside["overworld"]["cell"] = [-5,-5]
			check(FirstRegion.relocate_unwalkable(outside) and outside["overworld"]["cell"] == landing and outside["overworld"]["entry_lock"] == "","部屋の外の座標は入口へ: %s:%d" % [site["id"],index])
			check(not FirstRegion.relocate_unwalkable(probe),"歩ける位置は動かさない: %s:%d" % [site["id"],index])
	# 2. 部屋がない・世界マップ・船の保存は置き直さない。
	var missing := {"overworld":{"layer":"interior","node":"first_castle","room":99,"cell":[0,0],"transport":"walk","entry_lock":""},"first_region":{},"party":[]}
	check(not FirstRegion.relocate_unwalkable(missing) and missing["overworld"]["cell"] == [0,0],"存在しない部屋は置き直さない")
	var world := {"overworld":{"layer":"world","node":"","room":0,"cell":[0,0],"transport":"walk","entry_lock":""},"first_region":{},"party":[]}
	check(not FirstRegion.relocate_unwalkable(world),"世界マップの保存は置き直さない")
	var broken := {"overworld":{"layer":"interior","node":"first_castle","room":3,"cell":["a",0],"transport":"walk","entry_lock":""},"first_region":{},"party":[]}
	check(not FirstRegion.relocate_unwalkable(broken),"壊れた位置は置き直さない")
	# 3. 実際の保存の読み込み（型情報つき保存・整数化を通る）。
	load_case("throne_wall","first_castle",2,[1,1],true,FirstRegion.entrance_landing("first_castle",2))
	load_case("throne_old_door","first_castle",2,[16,20],true,FirstRegion.entrance_landing("first_castle",2))
	load_case("throne_king","first_castle",2,[12,5],true,FirstRegion.entrance_landing("first_castle",2))
	load_case("throne_walkable","first_castle",2,[12,6],false,[12,6])
	load_case("treasury_wall","first_castle",3,[0,0],true,FirstRegion.entrance_landing("first_castle",3))
	load_case("kaina_home_wall","start_village",0,[0,0],true,FirstRegion.entrance_landing("start_village",0))
	# 4. 存在しない部屋の保存は従来どおり読み込めない（現在の状態は変わらない）。
	var path := "user://qa_relocation_missing_room.json"
	write_case(path,region_state(),"first_castle",99,[0,0])
	var before := GameSession.new()
	check(before.new_first_region(),"読み込み前の状態")
	var snapshot := before.export_state()
	check(not before.load_game(path) and before.export_state() == snapshot,"存在しない部屋の保存は拒否し、現在の状態を壊さない")
	for message in failures:printerr("SAVED_POSITION_RELOCATION_FAIL: "+message)
	if failures.is_empty():print("SAVED_POSITION_RELOCATION_PASS: rooms=%d checks=%d" % [rooms,checks])
	quit(0 if failures.is_empty() else 1)
