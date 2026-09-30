extends SceneTree
## 境界用の人工状態。通常航行の撮影記録とは分ける。
var checks := 0
var failures: Array[String] = []
func check(ok: bool, message: String) -> bool:
	checks += 1
	if not ok:failures.append(message)
	return ok
func finish() -> void:
	PlaySessionMetrics.write_json("res://docs/verification/sprint6-coast/boundary-checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"method":"人工状態の境界検査。通常到達はruntimeの記録を参照。"})
	for message in failures:printerr("SECOND_COAST_FAIL: "+message)
	print("SECOND_COAST_PASS: checks=%d" % checks if failures.is_empty() else "SECOND_COAST_FAIL")
	quit(0 if failures.is_empty() else 1)
func roundtrip(saved: Dictionary, label: String) -> void:
	var game := GameSession.new()
	if not check(game.import_state(saved),label+"の状態を受理"):return
	var path := "user://second_coast_%d.json" % OS.get_process_id()
	check(game.save_game(path),label+"の保存")
	var restored := GameSession.new()
	check(restored.load_game(path) and restored.export_state()==saved,label+"の完全復元")
func reachable(saved: Dictionary, start: Vector2i, goal: Vector2i) -> bool:
	var seen := {start:true};var queue: Array[Vector2i]=[start];var index := 0
	while index<queue.size():
		var p := queue[index];index+=1
		if p==goal:return true
		for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var q: Vector2i=p+d
			if not seen.has(q) and FirstRegion.walkable(saved,q):seen[q]=true;queue.append(q)
	return false
func _initialize() -> void:
	if not check(FileAccess.file_exists("res://world/second_region_coast.json"),"第2地方の沿岸データがある"):finish();return
	var config: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/second_region_coast.json")))
	var raw: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://world/first_region_visuals.json"))
	# 63241bcの全72×40マス。将来の範囲を作業ツリーに合わせて縮めない。
	check("\n".join(raw["maps"]["world"]["terrain"]).sha256_text()=="6e3f95b03e1572a8569b741138b22221e7f52b180fe7ab7ec8c84a14e462c47b","第1地方の地形不変")
	check("\n".join(raw["maps"]["world"]["layout"]).sha256_text()=="362e854f86603a454f2f2d44884d6592433ff7d551af9f7430b1cae2f8eb23a1","第1地方の徒歩判定不変")
	check(FirstRegionTravel.data()["docks"].size()==2,"第1地方の乗降2か所を維持")
	var game := GameSession.new()
	if not check(game.new_first_region(),"新規状態: "+str(game.errors)):finish();return
	var saved := game.export_state()
	saved["party"].append_array(saved["first_region"]["reserve"]);saved["first_region"]["reserve"]=[]
	saved["inventory"]["gate_pass"]=1;saved["progress_flags"]["castle_north_permission"]=true;saved["progress_flags"]["mountain_path_open"]=true
	saved["overworld"]["cleared"]=["first_boss","forest_tower_boss"]
	saved["first_region"]["travel"]={"version":1,"visited":["start_village","first_castle","first_port"],"return_learned":true,"ship_owned":true,"ship_cell":[59,48]}
	FirstRegion.place(saved["overworld"],{"layer":"world","node":"","room":0,"cell":[59,48]});saved["overworld"]["transport"]="ship"
	var dock: Dictionary=config["docks"][0];var water := WorldExpedition.point(dock["ship_cell"]);var land := WorldExpedition.point(dock["land"]["cell"])
	check(reachable(saved,Vector2i(59,48),water),"第1地方から第2地方の海上経路")
	check(reachable(saved,water,Vector2i(59,48)),"第2地方から帰航可能")
	check(not FirstRegion.walkable(saved,land),"船は岸へ乗り上げない")
	check(not FirstRegion.walkable(saved,Vector2i(255,255)),"未開放海域へ入れない")
	saved["overworld"]["cell"]=dock["ship_cell"].duplicate();saved["first_region"]["travel"]["ship_cell"]=dock["ship_cell"].duplicate()
	roundtrip(saved,"第2地方の航行")
	check(FirstRegionTravel.board_or_land(saved),"浅瀬で下船")
	check(saved["overworld"]["transport"]=="walk" and FirstRegion.at(saved["overworld"],dock["land"]),"指定した岸へ着地")
	check(not FirstRegion.walkable(saved,water),"徒歩は海へ入れない")
	check(reachable(saved,land,WorldExpedition.point(config["walk_goal"])),"沿岸の徒歩経路")
	check(FirstRegion.walkable_cells(saved).has(config["walk_goal"]),"通常経路探索に第2地方の岸を含む")
	roundtrip(saved,"第2地方へ上陸")
	check(FirstRegionTravel.board_or_land(saved) and saved["overworld"]["transport"]=="ship","再乗船")
	saved["overworld"]["cell"]=[140,100];saved["first_region"]["travel"]["ship_cell"]=[140,100]
	var before := saved.duplicate(true)
	check(not FirstRegionTravel.board_or_land(saved) and saved==before,"沖では下船拒否・状態不変")
	check(game.import_state(saved),"沖の保存を読込")
	var prior := game.export_state()
	check(game.cast_first_region_return("pc_01","first_port"),"第2地方の沖から既存の港へ帰還")
	var after := game.export_state()
	check(after["party"][0]["mp"]==prior["party"][0]["mp"]-2,"帰還の消費MP2")
	check(after["first_region"]["travel"]["ship_cell"]==[59,48],"船も第1地方へ帰港")
	roundtrip(after,"帰還後")
	var invalid := saved.duplicate(true);invalid["first_region"]["travel"]["ship_cell"]=dock["land"]["cell"].duplicate()
	check(not GameSession.new().import_state(invalid),"陸上の船の保存は拒否")
	var catalog := BattleCatalog.new();check(catalog.errors.is_empty(),"敵の戦闘データが有効")
	var baseline := "res://docs/verification/sprint6-coast/legacy-enemies-63241bc.json"
	check(FileAccess.get_sha256(baseline)=="14c595a401d846060d185c54ef3222d9f28adfbfc233b1d6673bfc0e07caad6c","既存30種の比較原本は63241bcに固定")
	var old: Array=JSON.parse_string(FileAccess.get_file_as_string(baseline))
	check(old.size()==30 and catalog.enemies.size()==36,"既存30種と海3種・地上3種の総数36")
	for entry in old:check(catalog.enemies.get(entry["id"])==entry,"既存の敵定義不変: "+str(entry["id"]))
	for group in config["sea_encounter"]["groups"]:
		for id in group:check(catalog.enemies.has(id),"海の控え敵を戦闘へ登録: "+id)
	check(config["ground_encounter_status"]=="registered","依頼者指定の地上3種を通常登録")
	var ground_ids: Array[String]=[]
	for group in config["ground_encounter"]["groups"]:
		for id in group:
			check(catalog.enemies.has(id),"地上の敵の参照: "+str(id))
			if id not in ground_ids:ground_ids.append(id)
	ground_ids.sort()
	check(ground_ids==["coast_scorpion","coast_thorn_cactus","coast_worm"],"通常遭遇の地上3種が依頼者指定と完全一致")
	for group in config["ground_encounter"]["groups"]+config["sea_encounter"]["groups"]:
		for id in group:check(catalog.enemies[id]["sprite_id"] not in ["amber_droplet","desert_mummy","stone_gargoyle"],"不採用・保留の3体を通常遭遇へ登録しない")
	var source := "res://assets/_incoming/owner-2026-09-30-interiors/IMG_1183.png"
	check(FileAccess.get_sha256(source)=="d812496d505273e10868813813cde4f4bd970c1a2a74a4a74ec4c4a80b10fa50","IMG_1183原本のバイト不変")
	var record: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/source_records/owner-desert-monsters-20260930.json"))
	check(record["source_sha256"]==FileAccess.get_sha256(source) and FileAccess.get_sha256("res://"+record["archive_copy"])==record["source_sha256"],"原本・保管コピー・変換記録の対応")
	check(record["imported"].size()==3,"新原画の3体すべてを記録")
	for entry in record["imported"]:
		var path: String="res://"+entry["path"]
		var image := (load(path) as Texture2D).get_image();var colors: Dictionary={};var binary := true
		check(image.get_size()==Vector2i(96,96),"敵の寸法96px: "+entry["id"])
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var color := image.get_pixel(x,y)
				if color.a!=0.0 and color.a!=1.0:binary=false
				if color.a>0.0:colors[color.to_rgba32()]=true
		check(binary and colors.size()>0 and colors.size()<=32,"32色以内・二値透過: "+entry["id"])
		check(FileAccess.get_sha256(path)==entry["output_sha256"],"変換結果のハッシュ: "+entry["id"])
	check(config["sea_background"]=="sea" and config["ground_background"]=="desert","海と砂漠の採用済み背景")
	check(not FirstRegionTravel.snapshot(after)["visited"].has("brine_port"),"原画未提供の町へ訪問した扱いにしない")
	finish()
