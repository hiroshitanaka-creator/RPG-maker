extends SceneTree
## 009 最新HEADの継続条件。期待値は固定006の独立fixture。007の施設受入は別検査へ引き継ぐ。
const OUT := "res://docs/verification/task-009/latest/"
const DIRECTIONS := [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]
const ROLES := ["exterior","inn","item","weapon","shrine"]
const LIMIT_MS := 180000
var started := Time.get_ticks_msec()
var checks := 0
var failures: Array[String] = []
var results: Dictionary = {}
var section := "1"
var contract: Dictionary
var base: Dictionary
var save_states: Array = []
var route_log: Array = []

func check(ok: bool, message: String) -> bool:
	checks+=1
	if not results.has(section):results[section]={"checks":0,"failures":[]}
	results[section]["checks"]+=1
	if not ok:
		failures.append(message);results[section]["failures"].append(message)
	return ok

func preserve_save(source: String) -> void:
	var directory := OUT+"saved-inputs/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(directory))
	var target := directory+source.get_file()
	var file := FileAccess.open(target,FileAccess.WRITE)
	if not check(file!=null,"通常保存の実ファイルを006証拠へ保管"):return
	file.store_buffer(FileAccess.get_file_as_bytes(source));file.close()
	check(FileAccess.get_sha256(source)==FileAccess.get_sha256(target),"保管した通常保存の全バイト一致")

func p(index: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":"region2_village","room":index,"cell":cell}

func world(cell: Array) -> Dictionary:
	return {"layer":"world","node":"","room":0,"cell":cell}

func placed(index: int, cell: Array) -> Dictionary:
	var saved := base.duplicate(true)
	FirstRegion.place(saved["overworld"],p(index,cell))
	return saved

func game_for(saved: Dictionary) -> GameSession:
	var game := GameSession.new()
	check(game.import_state(saved),"本番セッションへ受理: "+str(saved["overworld"]))
	return game

func triggers(index: int) -> Array:
	var cells: Array=[]
	for link in Region2Village.data()["definition"]["region2_village_doors"]+contract["definition"]["region2_village_exits"]:
		if link["from"]["room"]==index:cells.append(WorldExpedition.point(link["from"]["cell"]))
	return cells

func path(saved: Dictionary, goal: Vector2i, avoid_links: bool=true) -> Array[Vector2i]:
	var from := WorldExpedition.point(saved["overworld"]["cell"])
	var seen := {from:from};var queue: Array[Vector2i]=[from];var cursor := 0
	var blocked := triggers(saved["overworld"]["room"]) if saved["overworld"]["node"]=="region2_village" and avoid_links else []
	while cursor<queue.size() and not seen.has(goal):
		var here := queue[cursor];cursor+=1
		for dir in DIRECTIONS:
			var next: Vector2i=here+dir
			if seen.has(next) or (next in blocked and next!=goal) or not FirstRegion.walkable(saved,next):continue
			seen[next]=here;queue.append(next)
	var route: Array[Vector2i]=[]
	if not seen.has(goal):return route
	var cell := goal
	while cell!=from:route.push_front(cell);cell=seen[cell]
	return route

func walk(game: GameSession, goal: Vector2i) -> bool:
	var before := game.export_state();var route := path(before,goal)
	if WorldExpedition.point(before["overworld"]["cell"])!=goal and not check(not route.is_empty(),"本番移動経路: "+str(goal)):return false
	for cell in route:
		var delta := cell-WorldExpedition.point(game.export_state()["overworld"]["cell"])
		game.first_region_face(delta)
		if not check(game.move_first_region(cell).get("kind")=="moved","一歩移動: "+str(cell)):return false
	return true

func leave(game: GameSession) -> void:
	var index: int=game.export_state()["overworld"]["room"]
	if index>0:
		walk(game,Vector2i(8,11))
		check(game.export_state()["overworld"]["room"]==0,"保存復帰後の室外退出")
	walk(game,Vector2i(3,13))
	check(FirstRegion.at(game.export_state()["overworld"],world([168,88])),"保存復帰後に世界へ退出")

func make_base() -> void:
	var game := GameSession.new();check(game.new_first_region(),"新規状態")
	base=game.export_state()
	base["party"].append_array(base["first_region"]["reserve"]);base["first_region"]["reserve"]=[]
	base["inventory"]["gate_pass"]=1
	for flag in ["castle_north_permission","mountain_path_open","job_change_unlocked"]:base["progress_flags"][flag]=true
	base["overworld"]["cleared"]=["first_boss","forest_tower_boss"]
	base["overworld"]["transport"]="walk"
	base["first_region"]["travel"]={"version":1,"visited":["start_village","first_castle","first_port","brine_port"],"return_learned":true,"ship_owned":true,"ship_cell":[155,110]}
	base["first_region"]["coins"]=37

func _initialize() -> void:
	contract=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/task-009/continuing-contract.json")))
	check(contract["source_sha"]=="5f1c2ba231191b25b9b32a814b616a9f8d0a54ce","期待値の固定006完全SHA")
	make_base()
	var args := OS.get_cmdline_user_args()
	if "--restart" in args:
		restart(int(args[args.find("--restart")+1]));return
	contract_checks();connections();maps();saves();growth_saves();invalid_saves();nonconnecting_doors();returns();finish()

func connections() -> void:
	section="1"
	var saved := base.duplicate(true)
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":"brine_port","room":0,"cell":[4,2]})
	var game := game_for(saved)
	check(game.save_game("user://village009_port-start.json"),"人工開始状態を通常保存（港からの撮影起点）")
	preserve_save("user://village009_port-start.json")
	check(game.move_first_region(Vector2i(4,1)).get("kind")=="moved" and FirstRegion.at(game.export_state()["overworld"],world([169,99])),"既存港出口から世界へ")
	var route: Array[Vector2i]=[Vector2i(168,99)]
	for y in range(98,87,-1):route.append(Vector2i(168,y))
	route.append(Vector2i(169,88));check(route.size()==13,"既存陸地13歩")
	seed(6006)
	for cell in route:
		check(FirstRegion.walkable(game.export_state(),cell),"指定沿岸セル通行: "+str(cell))
		var result := game.move_first_region(cell)
		check(result.get("kind") in ["moved","battle"],"港から通常一歩: "+str(cell))
		route_log.append({"target":[cell.x,cell.y],"result":result.get("kind"),"pose":game.export_state()["overworld"].duplicate(true)})
	var arrived := game.export_state()
	check(FirstRegion.at(arrived["overworld"],p(0,[4,15])) and arrived["overworld"]["facing"]==0,"西側から内側へ南向き着地")
	check(arrived["first_region"]["travel"]["visited"]==base["first_region"]["travel"]["visited"]+["region2_village"],"初訪問の1件だけ追加")
	var unchanged := arrived.duplicate(true);unchanged.erase("overworld");unchanged["first_region"]["travel"]["visited"].erase("region2_village")
	var baseline := base.duplicate(true);baseline.erase("overworld")
	check(unchanged==baseline,"初訪問で他の進行・人物・品不変")
	for exit_link in contract["definition"]["region2_village_exits"]:
		walk(game,WorldExpedition.point(exit_link["from"]["cell"]))
		var state: Dictionary=game.export_state()["overworld"]
		check(FirstRegion.at(state,exit_link["to"]) and state["facing"]==exit_link["facing"],"アーチ退出と外向き: "+str(exit_link["facing"]))
		var before := game.export_state()
		check(game.move_first_region(WorldExpedition.point(state["cell"])).is_empty() and game.export_state()==before,"入力なしの再遷移なし")
		check(game.move_first_region(Vector2i(169,88)).get("kind")=="moved","退出直後の逆移動で再入村")
		var landing := [4,15] if exit_link["facing"]==1 else [41,15]
		check(game.export_state()["overworld"]["cell"]==landing and game.export_state()["overworld"]["facing"]==0,"東西着地と向き")
		check(game.export_state()["first_region"]["travel"]["visited"].count("region2_village")==1,"再訪問の重複なし")
		check(game.move_first_region(Vector2i(landing[0],landing[1]-1)).get("kind")=="moved" and game.export_state()["overworld"]["node"]=="region2_village","入場方向の継続で退出ループなし")
	leave(game)
	var back: Array[Vector2i]=[]
	for y in range(89,100):back.append(Vector2i(168,y))
	back.append(Vector2i(169,99));back.append(Vector2i(169,98))
	for cell in back:check(game.move_first_region(cell).get("kind") in ["moved","battle"],"同じ既存地上領域を徒歩帰路: "+str(cell))
	check(game.export_state()["overworld"]["node"]=="brine_port","港へ通常徒歩入場")
	section="2"
	for link in contract["definition"]["region2_village_doors"]:
		var from: Dictionary=link["from"];var before_cell: Array=from["cell"].duplicate();before_cell[1]+=1 if from["room"]==0 else -1
		game=game_for(placed(from["room"],before_cell))
		check(game.move_first_region(WorldExpedition.point(from["cell"])).get("kind")=="moved" and FirstRegion.at(game.export_state()["overworld"],link["to"]),"8本の扉リンク: "+str(from))
		check(game.export_state()["overworld"]["facing"]==link["facing"],"扉の着地方向")
		var target: Vector2i = WorldExpedition.point(link["to"]["cell"])+DIRECTIONS[link["facing"]]
		var before := game.export_state()
		var can_move := game.first_region_walkable(target)
		var continued := game.move_first_region(target)
		check((continued.get("kind")=="moved" and game.export_state()["overworld"]["room"]==link["to"]["room"]) if can_move else (continued.is_empty() and game.export_state()==before),"同じ方向の継続で往復せず、採用済みの壁ならその場で止まる")

func maps() -> void:
	var record: Dictionary=contract["targets"]
	for index in range(5):
		section="3"
		var map: Dictionary=contract["maps"][ROLES[index]]
		var saved := placed(index,[4,15] if index==0 else [8,10])
		var floors := 0
		for y in range(map["height"]):
			for x in range(map["width"]):
				var floor_cell: bool=map["layout"][y][x]=="."
				var expected: bool=floor_cell and not occupied(saved,Vector2i(x,y))
				check(FirstRegion.walkable(saved,Vector2i(x,y))==expected,"全セルの固定地形とNPC占有を区別: %d %d,%d" % [index,x,y])
				if floor_cell:floors+=1
				if not expected:
					if floor_cell:check(approachable(saved,Vector2i(x,y)),"NPC占有床の隣接セルへ到達")
					continue
				check(WorldExpedition.point(saved["overworld"]["cell"])==Vector2i(x,y) or not path(saved,Vector2i(x,y),false).is_empty(),"リンク判定を除いたBFSで全床連結")
				for direction in DIRECTIONS:
					var cell: Vector2i = Vector2i(x,y)+direction
					if not FirstRegion.walkable(saved,cell):continue
					var probe := placed(index,[x,y])
					check(FirstRegion.move(probe,cell).get("kind")=="moved","村の全床・全隣接で非戦闘")
		check(floors==[636,84,78,78,87][index],"採用済み床数")
		var actual: Dictionary=FirstRegionPresentation.map_for(saved["overworld"])
		for key in ["layout","width","height","background","overlays"]:
			check(actual.get(key)==map.get(key),"本番表示の固定背景・上層: "+ROLES[index]+" "+key)
		section="2"
		for target in record[ROLES[index]].values():
			check(not path(saved,WorldExpedition.point(target),false).is_empty(),"リンク判定を除いたBFSの客側・家具前後到達")
			var game := game_for(saved)
			# アーチは退出点なので、目標への最終歩だけで外へ戻る。
			walk(game,WorldExpedition.point(target))

func saves() -> void:
	section="4"
	for index in range(5):
		for facing in range(4):
			var saved := placed(index,[4,15] if index==0 else [8,10])
			saved["overworld"]["facing"]=facing;saved["overworld"]["entry_lock"]="region2_village_door"
			FirstRegionTravel.visit(saved,"region2_village")
			var game := game_for(saved)
			var filename := "user://village009_%d_%d.json" % [index,facing]
			check(game.save_game(filename),"通常保存: "+filename)
			preserve_save(filename)
			var restored := GameSession.new()
			check(restored.load_game(filename) and restored.export_state()==saved,"20状態の別セッション完全復元: "+filename)
			check(not restored.position_relocated,"正常保存は補正しない")
			save_states.append({"room":index,"facing":facing,"cell":saved["overworld"]["cell"],"entry_lock":saved["overworld"]["entry_lock"],"save_sha256":FileAccess.get_sha256(filename),"full_state_equal":restored.export_state()==saved})
			section="5";check(restored.export_state()==saved,"船・visited・編成・HP/MP・品・職・修練・侵蝕・マスター・物語フラグ全一致");section="4"
			leave(restored)
			check(restored.export_state()["overworld"]["layer"]=="world","20状態の読込後歩行・退出")
			if facing==0:PlaySessionMetrics.write_json("user://village009_expected_%d.json" % index,saved)

func growth_saves() -> void:
	section="5"
	# 保存領域の欠落を空配列だけの一致で見逃さず、既存の数値・マスター済み状態も保存する。
	var template := game_for(base)
	for index in range(5):
		var saved := placed(index,[4,15] if index==0 else [8,10]);FirstRegionTravel.visit(saved,"region2_village")
		var actor: Dictionary=saved["party"][0]
		actor["jp"]["warrior"]=IntegratedProgression.cost(template.jobs["warrior"],true)
		actor["integrated"]["mastery"]["counts"]["warrior"]=int(template.jobs["warrior"]["mastery_action"]["required"])
		actor["mastered_jobs"]=["warrior"];actor["erosion"]=30
		var stats := template._compute_stats(actor,true)
		actor["max_hp"]=stats["hp"];actor["max_mp"]=stats["mp"]
		actor["hp"]=actor["max_hp"]-3;actor["mp"]=actor["max_mp"]-2
		saved["first_region"]["coins"]=31;saved["inventory"]["potion"]=2
		var game := game_for(saved);var file := "user://village009_growth_%d.json" % index
		check(game.save_game(file),"村5マップの修練・マスター・侵蝕・消耗状態を通常保存")
		preserve_save(file)
		var restored := GameSession.new()
		check(restored.load_game(file) and restored.export_state()==saved,"非初期値のJP・成功回数・マスター・侵蝕30・HP/MP・所持金・品も全一致")

func restart(index: int) -> void:
	section="4"
	var game := GameSession.new()
	var expected: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("user://village009_expected_%d.json" % index)))
	check(game.load_game("user://village009_%d_0.json" % index) and game.export_state()==expected,"別プロセス再起動後の完全復元")
	leave(game)
	check(game.export_state()["overworld"]["cell"]==[168,88],"別プロセス読込後の徒歩退出")
	finish("restart-%d.json" % index)

func invalid_saves() -> void:
	section="6"
	for index in range(5):
		var game := game_for(placed(index,[4,15] if index==0 else [8,10]))
		var file := "user://village009_boundary.json"
		check(game.save_game(file),"補正入力の通常保存")
		var original: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(file))
		var relocation := original.duplicate(true);relocation["overworld"]["cell"]=[0,0]
		check(PlaySessionMetrics.write_json("user://village009_relocation_%d.json" % index,relocation),"本番UIの補正通知用入力を保存")
		preserve_save("user://village009_relocation_%d.json" % index)
		var map: Dictionary=Region2Village.data()["maps"]["region2_village:%d" % index]
		var blocked: Array=[0,0]
		for y in range(1,map["height"]-1):
			for x in range(1,map["width"]-1):
				if map["layout"][y][x]=="#":blocked=[x,y];break
			if blocked!=[0,0]:break
		for cell in [[0,0],blocked,[-1,0],[map["width"],map["height"]]]:
			var doc := original.duplicate(true);doc["overworld"]["cell"]=cell
			check(PlaySessionMetrics.write_json(file,doc),"壁・家具・範囲外の保存入力")
			var restored := GameSession.new()
			check(restored.load_game(file) and restored.position_relocated and restored.export_state()["overworld"]["cell"]==FirstRegion.entrance_landing("region2_village",index),"既存の入口安全補正")
			var expected := game.export_state();expected["overworld"]["cell"]=FirstRegion.entrance_landing("region2_village",index);expected["overworld"]["entry_lock"]=""
			check(restored.export_state()==expected,"補正以外の全状態不変")
			check(restored.save_game(file) and restored.load_game(file) and not restored.position_relocated,"再保存後に補正通知が残らない")
		for change in [{"node":"unknown"},{"room":-1},{"room":5},{"room":"1"},{"room":true},{"cell":["8",10]},{"cell":[8]},{"facing":"0"}]:
			var doc := original.duplicate(true);doc["overworld"].merge(change,true)
			PlaySessionMetrics.write_json(file,doc)
			var before := game.export_state()
			check(not game.load_game(file) and game.export_state()==before,"不正保存拒否と現在状態保持: "+str(change))
	var old := base.duplicate(true);FirstRegion.place(old["overworld"],world([169,99]));old["first_region"].erase("travel")
	var game := game_for(old);var file := "user://village009_old.json"
	check(game.save_game(file),"旅情報なし旧保存")
	var restored := GameSession.new();check(restored.load_game(file) and restored.export_state()==old,"旧保存を旧保存のまま復元")
	FirstRegionTravel.ensure(old)
	check("region2_village" not in old["first_region"]["travel"]["visited"],"未訪問旧保存に村訪問を捏造しない")

func nonconnecting_doors() -> void:
	section="7"
	for cell in [[6,8],[10,14],[12,21],[34,21]]:
		var game := game_for(placed(0,[cell[0],cell[1]+1]))
		check(game.move_first_region(WorldExpedition.point(cell)).get("kind")=="moved" and FirstRegion.at(game.export_state()["overworld"],p(0,cell)),"非接続4扉は別室へ飛ばない")
		for direction in DIRECTIONS:
			game.first_region_face(direction)
			var before := game.export_state()
			check(game.interact_first_region().is_empty() and game.export_state()==before,"非接続4扉の調べる操作で遷移・状態変更なし")

func returns() -> void:
	section="9"
	for index in range(5):
		var saved := placed(index,[4,15] if index==0 else [8,10]);FirstRegionTravel.visit(saved,"region2_village")
		for destination in contract["destinations"]:
			var game := game_for(saved);var before := game.export_state()
			check(game.cast_first_region_return("pc_02",destination["id"]),"村5マップから訪問済み既存先へ帰還: "+destination["id"])
			var after := game.export_state();var expected := before.duplicate(true)
			expected["party"][1]["mp"]-=2;expected["overworld"]=after["overworld"].duplicate(true);expected["first_region"]["travel"]["ship_cell"]=after["first_region"]["travel"]["ship_cell"].duplicate()
			check(after==expected and FirstRegion.at(after["overworld"],world(contract["return_landings"][destination["id"]])),"選択した生存者だけMP2・位置・船以外不変")
			if destination["id"]=="region2_village":check(after["overworld"]["cell"]==[168,88] and after["overworld"]["facing"]==1 and after["first_region"]["travel"]["ship_cell"]==[155,110],"村入口前と既存第2港の船")
		for negative in ["unvisited","unlearned","dead","mp","battle","unknown_actor","unknown_target"]:
			var probe := saved.duplicate(true)
			if negative=="unvisited":probe["first_region"]["travel"]["visited"].erase("region2_village")
			if negative=="unlearned":probe["first_region"]["travel"]["return_learned"]=false
			if negative=="dead":probe["party"][1]["hp"]=0
			if negative=="mp":probe["party"][1]["mp"]=1
			var game := game_for(probe)
			if negative=="battle":check(game.start_first_region_battle({"kind":"battle","id":"first_region_encounter","enemies":["slime"],"seed":6006})!=null,"負例の本番戦闘開始")
			var before := game.export_state()
			check(not game.cast_first_region_return("missing" if negative=="unknown_actor" else "pc_02","missing" if negative=="unknown_target" else "region2_village") and game.export_state()==before,"帰還負例の状態不変: "+negative)
	var saved := base.duplicate(true);FirstRegion.place(saved["overworld"],world([169,99]));FirstRegionTravel.visit(saved,"region2_village")
	var game := game_for(saved)
	check(game.cast_first_region_return("pc_01","region2_village") and game.export_state()["overworld"]["cell"]==[168,88],"港側から訪問済み村へ帰還")
	check(game.move_first_region(Vector2i(169,88)).get("kind")=="moved" and game.export_state()["overworld"]["node"]=="region2_village","帰還後に通常入村")

func finish(filename: String="runtime-checks.json") -> void:
	check(Time.get_ticks_msec()-started<LIMIT_MS,"180秒の検査上限")
	for value in results.values():value["status"]="PASS" if value["failures"].is_empty() else "FAIL"
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"sections":results,"save_states":save_states,"port_route":route_log,"execution_sha":OS.get_environment("RPG009_EXECUTION_SHA"),"elapsed_ms":Time.get_ticks_msec()-started,"limit_ms":LIMIT_MS,"service_acceptance":"007未着手。6人会話・宿回復・祠の機能成功は009の判定対象に含めず、引継ぎ表に正負例を記録。固定側では006の無反応を全件検査。","method":"最新本番APIの一歩移動・全セル・境界状態・通常保存。固定006fixtureを独立期待値に使用。通常キー入力と描画は別の最新capture証拠。"}
	check(PlaySessionMetrics.write_json(OUT+filename,report),"検査JSON保存")
	for failure in failures:printerr("VILLAGE_REGRESSION_FAIL: "+failure)
	print("VILLAGE_REGRESSION_PASS: checks=%d" % checks if failures.is_empty() else "VILLAGE_REGRESSION_FAIL")
	quit(0 if failures.is_empty() else 1)

func occupied(saved: Dictionary, cell: Vector2i) -> bool:
	# 地形の床をNPCの足元だけで壁と誤判定しない。既存の占有種別は独立の検査条件。
	for event in FirstRegion.room(saved["overworld"]).get("events",[]):
		if event["kind"] in ["recruit","rest","shop","weapon_shop","npc","story"] and FirstRegion.event_cell(saved,event)==cell:
			if event["kind"]=="recruit" and FirstRegion.joined(saved,event["actor"]):continue
			return true
	return false

func approachable(saved: Dictionary, cell: Vector2i) -> bool:
	for direction in DIRECTIONS:
		var target: Vector2i=cell+direction
		if FirstRegion.walkable(saved,target) and (WorldExpedition.point(saved["overworld"]["cell"])==target or not path(saved,target,false).is_empty()):return true
	return false

func contract_checks() -> void:
	section="1"
	check(Region2Village.data()["definition"]==contract["definition"],"村の世界接続・東西出口・8扉の固定対応")
	check(FirstRegionTravel.destinations()==contract["destinations"],"既存帰還先の全件と村の船先")
	for index in range(5):
		check(FirstRegion.room(p(index,[4,15] if index==0 else [8,10]))["layout"]==contract["maps"][ROLES[index]]["layout"],"採用済み地形の固定床壁: "+ROLES[index])
