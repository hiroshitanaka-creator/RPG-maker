extends SceneTree
## 人工境界状態のAPI検査。通常入力の到達証拠とは分ける。
const OUT := "res://docs/verification/task-081-implementation/"
const OLD := "res://docs/verification/coastal-fixture-fix-2026-10-22/results/user-data/godot/app_userdata/RPG-maker/region2_port_old_1752_"
var checks: Array = []
var base: Dictionary

func old_copy(index: int) -> String:
	var path := "user://task081-old-%d.json"%index
	var file := FileAccess.open(path,FileAccess.WRITE)
	file.store_buffer(FileAccess.get_file_as_bytes(OLD+str(index)+".json"));file.close()
	return path

func check(ok: bool, label: String, detail: Variant = null) -> bool:
	checks.append({"ok":ok,"label":label,"detail":detail})
	if not ok:printerr("TASK081_RUNTIME_FAIL: "+label+" "+str(detail))
	return ok

func placed(index: int, cell: Array) -> Dictionary:
	var candidate := base.duplicate(true)
	FirstRegion.place(candidate["overworld"],{"layer":"interior","node":"region3_port","room":index,"cell":cell})
	candidate["overworld"]["transport"]="walk"
	return candidate

func reach(saved: Dictionary, start: Array) -> Dictionary:
	var first := WorldExpedition.point(start)
	var seen := {first:true}
	var queue := [first]
	var cursor := 0
	while cursor<queue.size():
		var cell: Vector2i=queue[cursor];cursor+=1
		for delta in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
			var next: Vector2i=cell+delta
			if not seen.has(next) and FirstRegion.walkable(saved,next):seen[next]=true;queue.append(next)
	return seen

func roundtrip(game: GameSession, label: String) -> void:
	var expected := game.export_state()
	var path := "user://task081-"+label+".json"
	check(game.save_game(path),"通常codecで保存",label)
	var loaded := GameSession.new()
	check(loaded.load_game(path) and loaded.export_state()==expected,"型・全保存値の完全往復",label)
	var copy := FileAccess.open(OUT+"saves/"+label+".json",FileAccess.WRITE)
	copy.store_buffer(FileAccess.get_file_as_bytes(path));copy.close()

func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+"saves"))
	var old := GameSession.new()
	if not check(old.load_game(old_copy(1)),"実在する081以前の保存を無編集コピーして読込"):finish();return
	base=old.export_state()
	for index in range(1,7):
		var legacy := GameSession.new()
		if check(legacy.load_game(old_copy(index)),"旧6室保存を受理",index):roundtrip(legacy,"legacy-"+str(index))
	var plain := GameSession.new();plain.new_first_region();roundtrip(plain,"old-travel-missing")
	var data := Region3Port.data()
	check(data["site"]["rooms"].size()==6 and data["definition"]["region3_port_doors"].size()==10,"外観と採用5室の往復扉")
	var dock: Dictionary=data["docks"][0]
	check(FirstRegionTravel.ship_water(WorldExpedition.point(dock["ship_cell"])),"桟橋の海セルは現在の合成海域")
	var old_visuals: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/first_region_visuals.json")))
	var previous_world := SecondRegionCoast.extend_world(old_visuals["maps"]["world"])
	var current_world: Dictionary=FirstRegionPresentation.data()["maps"]["world"]
	var altered: Array=[];var lost_sea: Array=[]
	for y in range(previous_world["height"]):
		for x in range(previous_world["width"]):
			var before: String=previous_world["terrain"][y].substr(x,1)
			if previous_world["layout"][y].substr(x,1)!=current_world["layout"][y].substr(x,1) or before!=current_world["terrain"][y].substr(x,1):altered.append([x+previous_world["origin"][0],y+previous_world["origin"][1]])
			if before in ["~","b"] and current_world["terrain"][y].substr(x,1) not in ["~","b"]:lost_sea.append([x,y])
	check(altered==[[179,44],[180,44]] and lost_sea.is_empty(),"世界の変更は入口前の橋2セルだけ・旧船セル喪失なし",{"changed":altered,"lost_sea":lost_sea})
	var sea_seen: Dictionary={Vector2i(59,48):true}
	var sea_queue := [Vector2i(59,48)];var cursor := 0
	while cursor<sea_queue.size():
		var cell: Vector2i=sea_queue[cursor];cursor+=1
		for delta in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
			var next: Vector2i=cell+delta
			if not sea_seen.has(next) and FirstRegionTravel.ship_water(next):sea_seen[next]=true;sea_queue.append(next)
	check(sea_seen.has(WorldExpedition.point(dock["ship_cell"])),"第1港から既存海セルだけで到達",sea_seen.size())
	for position in data["world_entry_cells"]:
		check(FirstRegionTravel.ship_water(WorldExpedition.point(position)),"入口追加後も旧保存の船セルを保持",position)
		var prior_ship := base.duplicate(true)
		FirstRegion.place(prior_ship["overworld"],{"layer":"world","node":"","room":0,"cell":position})
		prior_ship["overworld"]["transport"]="ship";prior_ship["first_region"]["travel"]["ship_cell"]=position.duplicate()
		check(GameSession.new().import_state(prior_ship),"旧海セルにいた船保存も受理",position)
	var gate_game := GameSession.new();gate_game.import_state(placed(0,[7,5]))
	for repeat in range(8):
		gate_game.move_first_region(Vector2i(7,4));gate_game.move_first_region(Vector2i(7,3))
		check(FirstRegion.at(gate_game.overworld_state(),FirstRegion.outside("region3_port_entrance")) and gate_game.overworld_state()["facing"]==1,"石門から世界の入口前へ反復退出",repeat)
		gate_game.move_first_region(Vector2i(180,44))
		check(FirstRegion.at(gate_game.overworld_state(),data["definition"]["region3_port_gate_spawn"]),"世界の入口前から石門へ反復再入場",repeat)
	var definition: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/adopted_room_foundation.json")))
	for index in range(6):
		var landing := FirstRegion.entrance_landing("region3_port",index)
		var candidate := placed(index,landing)
		var game := GameSession.new()
		if not check(game.import_state(candidate),"本番IDと室を受理",index):continue
		var expected_layout: Array=data["site"]["rooms"][index]["layout"]
		if index>0:
			check(expected_layout==definition["rooms"][index-1]["layout"],"080の通行をそのまま再使用",index)
			check(data["maps"]["region3_port:%d"%index]["overlays"]["pieces"]==definition["rooms"][index-1]["overlays"],"080の家具遮蔽をそのまま再使用",index)
		var connected := reach(candidate,landing)
		var floor_count := 0
		for y in range(expected_layout.size()):
			for x in range(str(expected_layout[y]).length()):
				var floor_cell := str(expected_layout[y]).substr(x,1)=="."
				if floor_cell:floor_count+=1
				check(FirstRegion.walkable(candidate,Vector2i(x,y))==floor_cell,"全セルの通行・家具衝突",[index,x,y])
		check(connected.size()==floor_count,"全床が入口から連結",{"room":index,"floors":floor_count,"connected":connected.size()})
		for position in connected:
			for delta in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
				if FirstRegion.walkable(candidate,position+delta):continue
				var blocked := placed(index,[position.x,position.y]);var before := blocked.duplicate(true)
				check(FirstRegion.move(blocked,position+delta).is_empty() and blocked==before,"全境界・家具隣接の移動拒否",[index,position.x,position.y,delta.x,delta.y])
		for facing in range(4):
			var state := placed(index,landing);state["overworld"]["facing"]=facing
			game.import_state(state);roundtrip(game,"room-%d-facing-%d"%[index,facing])
		var blocked_save := placed(index,[0,0])
		check(not FirstRegion.valid(blocked_save),"壁に保存位置を置いた境界は拒否",index)
		var moved := GameSession.new()
		var document := blocked_save.duplicate(true)
		document["_play_session"]=moved.play_metrics.snapshot()
		document["_saved_value_types"]=SavedValueTypes.describe(document)
		var path := "user://task081-relocate-%d.json"%index
		var file := FileAccess.open(path,FileAccess.WRITE);file.store_string(SavedDocument.encode(document));file.close()
		check(moved.load_game(path) and moved.overworld_state()["cell"]==landing,"壁・変更後の旧位置を入口前へ補正",index)
	for binding in data["bindings"]:
		var index := int(binding["room"])
		var game := GameSession.new()
		game.import_state(placed(0,binding["return_cell"]))
		for repeat in range(12):
			game.move_first_region(WorldExpedition.point(binding["door"]))
			check(game.overworld_state()["room"]==index and game.overworld_state()["cell"]==[6,9],"扉別の反復入室",[binding["id"],repeat])
			game.move_first_region(Vector2i(6,10));game.move_first_region(Vector2i(6,11))
			check(game.overworld_state()["room"]==0 and game.overworld_state()["cell"]==binding["return_cell"] and game.overworld_state()["facing"]==0,"扉別の反復復帰",[binding["id"],repeat])
	for node in ["mist_market","region3_port_unknown","dev_adopted_inn","dev_adopted_item_shop","dev_adopted_weapon_shop","dev_adopted_shrine","dev_adopted_armor_shop",""]:
		var unknown := placed(0,dock["land"]["cell"]);unknown["overworld"]["node"]=node
		check(not GameSession.new().import_state(unknown),"未知・旧・開発ID拒否維持",node)
	for index in [-1,6,999]:check(not GameSession.new().import_state(placed(index,[6,9])),"未知室番号拒否",index)
	var unowned := plain.export_state();FirstRegion.place(unowned["overworld"],dock["land"])
	check(not GameSession.new().import_state(unowned),"船未所有の新港保存を拒否")
	check(FirstRegionTravel.dock_for(unowned).is_empty() and not FirstRegionTravel.board_or_land(unowned),"船未所有の乗降を拒否")
	var landed := placed(0,dock["land"]["cell"]);landed["first_region"]["travel"]["ship_cell"]=dock["ship_cell"]
	check(not FirstRegionTravel.return_to(landed,"pc_01","region3_port"),"未訪問の新港への帰還拒否")
	check(FirstRegionTravel.board_or_land(landed),"新港の通常方式で乗船")
	check(FirstRegionTravel.board_or_land(landed) and "region3_port" in landed["first_region"]["travel"]["visited"],"下船で訪問済み追加")
	var invalid_visited := landed.duplicate(true);invalid_visited["first_region"]["travel"]["visited"].append("unknown_port")
	check(not GameSession.new().import_state(invalid_visited),"未知の訪問先保存を拒否")
	var member: Dictionary=landed["party"][0];member["mp"]=5;var old_mp: int=member["mp"]
	check(FirstRegionTravel.return_to(landed,str(member["id"]),"region3_port") and member["mp"]==old_mp-2 and FirstRegion.at(landed["overworld"],FirstRegion.outside("region3_port_entrance")),"訪問済み港への帰還はMP2・入口前・船も同伴")
	check(FirstRegion.valid(landed),"帰還直後の保存は有効")
	var insufficient := landed.duplicate(true);insufficient["party"][0]["mp"]=1
	check(not FirstRegionTravel.return_to(insufficient,str(member["id"]),"region3_port"),"MP不足拒否維持")
	var dead := landed.duplicate(true);dead["party"][0]["hp"]=0
	check(not FirstRegionTravel.return_to(dead,str(member["id"]),"region3_port"),"戦闘不能の帰還拒否維持")
	finish()

func finish() -> void:
	var failed := checks.filter(func(item:Dictionary)->bool:return not item["ok"]).size()
	PlaySessionMetrics.write_json(OUT+"api-runtime.json",{"checks":checks,"failed":failed,"scope":"人工境界状態。通常到達証拠は別のinput記録。"})
	print("TASK081_RUNTIME_RESULT: checks=%d failed=%d"%[checks.size(),failed])
	quit(0 if failed==0 else 1)
