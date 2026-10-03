extends SceneTree
## 新港の境界・機能検査。人工状態と通常撮影を混同しない。
const LIMIT_MS := 180000
var started := Time.get_ticks_msec()
var checks := 0
var failures: Array[String] = []
var base: Dictionary

func check(ok: bool, message: String) -> bool:
	checks += 1
	if not ok:failures.append(message)
	return ok

func placed(room_index: int, cell: Array) -> Dictionary:
	var saved := base.duplicate(true)
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":"brine_port","room":room_index,"cell":cell})
	saved["overworld"]["transport"]="walk"
	return saved

func reach(saved: Dictionary, start: Array) -> Dictionary:
	var seen := {Vector2i(start[0],start[1]):true}
	var queue: Array[Vector2i]=[Vector2i(start[0],start[1])]
	var index := 0
	while index<queue.size():
		var p := queue[index];index+=1
		for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var q: Vector2i = p+d
			if not seen.has(q) and FirstRegion.walkable(saved,q):seen[q]=true;queue.append(q)
	return seen

func roundtrip(game: GameSession, name: String) -> void:
	var saved := game.export_state()
	var path := "user://region2_port_%d_%s.json" % [OS.get_process_id(),name]
	check(game.save_game(path),name+" 保存")
	var restored := GameSession.new()
	check(restored.load_game(path) and restored.export_state()==saved,name+" 全状態の復元")

func _initialize() -> void:
	var game := GameSession.new()
	if not check(game.new_first_region(),"新規状態生成"):finish();return
	base=game.export_state()
	base["party"].append_array(base["first_region"]["reserve"]);base["first_region"]["reserve"]=[]
	base["inventory"]["gate_pass"]=1
	for flag in ["castle_north_permission","mountain_path_open","job_change_unlocked"]:base["progress_flags"][flag]=true
	base["overworld"]["cleared"]=["first_boss","forest_tower_boss"]
	base["first_region"]["coins"]=50
	base["first_region"]["travel"]={"version":1,"visited":["start_village","first_castle","first_port"],"return_learned":true,"ship_owned":true,"ship_cell":[155,110]}
	var data := Region2Port.data()
	check(data["site"]["rooms"].size()==7 and data["maps"].size()==7,"外観と6室")
	check(data["definition"]["second_port_doors"].size()==12,"6室の往復扉")
	var exterior: Dictionary=data["maps"]["brine_port:0"]
	for id in ["inn","item","weapon","armor","shrine","harbor","home_a","home_b"]:
		check(exterior["tiles"].values().any(func(t:Dictionary)->bool:return t["path"]=="assets/objects/region2_"+id+".png"),"8棟の部品: "+id)
	var town := placed(0,[4,4]);var cells := reach(town,[4,4])
	for link in data["definition"]["second_port_doors"]:
		if link["from"]["room"]==0:
			check(cells.has(WorldExpedition.point(link["from"]["cell"])),"入口から建物へ: "+str(link["to"]["room"]))
	check(cells.has(Vector2i(34,21)),"入口から中央桟橋へ")
	check(not FirstRegion.walkable(town,Vector2i(41,27)),"海へ歩いて入れない")
	check(not FirstRegion.walkable(town,Vector2i(13,3)),"建物の壁へ入れない")
	for cell in cells:
		for direction in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var probe := placed(0,[cell.x,cell.y])
			if FirstRegion.walkable(probe,cell+direction):
				check(FirstRegion.move(probe,cell+direction).get("kind")!="battle","町内非戦闘");break
	var actor_ids: Array[String]=[]
	for index in range(7):
		for event in data["site"]["rooms"][index]["events"]:actor_ids.append(event["sprite"])
	actor_ids.sort()
	var expected: Array[String]=[]
	for id in ["innkeeper","item_clerk","weapon_clerk","armor_clerk","shrine_keeper","sailor","fisher","merchant","child","traveller"]:expected.append("npc_sand_"+id)
	expected.sort();check(actor_ids==expected,"指定した住人10人の配置")
	for index in range(1,7):
		var saved := placed(index,[8,10]);var room: Dictionary=data["site"]["rooms"][index]
		var positions: Dictionary=data["interaction_positions"][str(index)]
		if index==1:
			var clerk: Array=room["events"][0]["cell"]
			check(not Rect2i(340,120,140,56).has_point(Vector2i(clerk[0]*32+16,(clerk[1]+1)*32-1)),"宿の主人の足元が原画の受付台に乗らない")
		check(reach(saved,[8,10]).has(WorldExpedition.point(positions["cell"])),"室内入口から会話位置: "+str(index))
		check(not FirstRegion.walkable(saved,Vector2i(0,0)),"室内外周へ入れない: "+str(index))
		var blocked: Array = [[3,3],[6,4],[10,4],[8,4],[7,2],[10,5]][index-1]
		check(not FirstRegion.walkable(saved,WorldExpedition.point(blocked)),"家具・台へ入れない: "+str(index))
		for link in data["definition"]["second_port_doors"]:
			if link["to"]["room"]==index:
				var entering := placed(0,[link["from"]["cell"][0],link["from"]["cell"][1]+1])
				check(FirstRegion.move(entering,WorldExpedition.point(link["from"]["cell"])).get("kind")=="moved" and FirstRegion.at(entering["overworld"],link["to"]),"扉から通常入室: "+str(index))
			elif link["from"]["room"]==index:
				check(FirstRegion.move(saved,Vector2i(8,11)).get("kind")=="moved" and FirstRegion.at(saved["overworld"],link["to"]),"扉から通常退出: "+str(index))
		saved=placed(index,positions["cell"]);saved["overworld"]["facing"]=positions["facing"]
		if index==1:
			for member in saved["party"]:member["hp"]=1;member["mp"]=0
		if not check(game.import_state(saved),"室内状態受理: "+str(index)):continue
		var before := game.export_state();var result := game.interact_first_region()
		var expected_kind: String="shop" if index==2 else "weapon_shop" if index==3 else "dialogue"
		check(result.get("kind")==expected_kind,"店員へ会話: "+str(index)+" "+str(result.get("kind")))
		if index==1:check(game.export_state()["party"].all(func(a:Dictionary)->bool:return a["hp"]==a["max_hp"] and a["mp"]==a["max_mp"]),"宿泊で全員回復")
		if index==2:
			check(game.buy_first_region_potion(),"道具購入")
			var after := game.export_state()
			check(after["inventory"]["potion"]==before["inventory"]["potion"]+1 and after["first_region"]["coins"]==before["first_region"]["coins"]-5,"道具と代金5")
		if index==3:
			check(game.buy_first_region_weapon(),"武器購入")
			var after := game.export_state()
			check("iron_blade" in after["integrated"]["armory"] and after["first_region"]["coins"]==before["first_region"]["coins"]-15,"武器と代金15")
		if index==4:check(game.export_state()["integrated"]["armory"]==before["integrated"]["armory"] and game.export_state()["first_region"]["coins"]==before["first_region"]["coins"],"防具屋は会話のみ")
		check(game.at_purification_shrine()==(index==5),"祠の場所を限定: "+str(index))
		roundtrip(game,"room"+str(index))
		var old_path := "user://region2_port_old_%d_%d.json" % [OS.get_process_id(),index]
		check(game.save_game(old_path),"旧位置検査用の型情報つき保存: "+str(index))
		var document: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(old_path))
		document["overworld"]["cell"]=[0,0]
		check(PlaySessionMetrics.write_json(old_path,document),"壁の位置にいた旧保存を用意: "+str(index))
		var restored := GameSession.new()
		check(restored.load_game(old_path) and restored.position_relocated and restored.export_state()["overworld"]["cell"]==[8,10],"歩けない旧位置を入口前へ置き直す: "+str(index))
		roundtrip(restored,"relocated"+str(index))
		for cell in reach(placed(index,[8,10]),[8,10]):
			var probe := placed(index,[cell.x,cell.y])
			for dir in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
				if FirstRegion.walkable(probe,cell+dir):
					check(FirstRegion.move(probe,cell+dir).get("kind")!="battle","室内非戦闘: "+str(index));break
	var dock: Dictionary=data["docks"][0]
	var sailing := base.duplicate(true);FirstRegion.place(sailing["overworld"],{"layer":"world","node":"","room":0,"cell":[59,48]});sailing["overworld"]["transport"]="ship";sailing["first_region"]["travel"]["ship_cell"]=[59,48]
	check(reach(sailing,[59,48]).has(WorldExpedition.point(dock["ship_cell"])),"第1港から第2港までの海上経路")
	sailing["overworld"]["cell"]=dock["ship_cell"].duplicate();sailing["first_region"]["travel"]["ship_cell"]=dock["ship_cell"].duplicate()
	check(reach(sailing,dock["ship_cell"]).has(Vector2i(59,48)),"第2港から第1港まで帰航できる")
	check(not FirstRegionTravel.snapshot(sailing)["visited"].has("brine_port"),"訪問前は未訪問")
	check(FirstRegionTravel.board_or_land(sailing) and FirstRegion.at(sailing["overworld"],dock["land"]),"第2港へ下船")
	check(FirstRegionTravel.snapshot(sailing)["visited"].has("brine_port"),"下船で訪問記録")
	check(game.import_state(sailing),"下船状態を受理");roundtrip(game,"landed")
	check(FirstRegionTravel.board_or_land(sailing) and sailing["overworld"]["transport"]=="ship","中央桟橋から再乗船")
	check(game.import_state(sailing),"再乗船状態を受理");roundtrip(game,"sailing")
	var before_return := game.export_state()
	check(game.cast_first_region_return("pc_01","brine_port"),"訪問済みの第2港へ帰還")
	var after_return := game.export_state()
	check(after_return["party"][0]["mp"]==before_return["party"][0]["mp"]-2,"帰還MP2")
	check(FirstRegion.at(after_return["overworld"],FirstRegion.outside("second_port_entrance")) and FirstRegionTravel.snapshot(after_return)["ship_cell"]==dock["ship_cell"],"帰還で人物と船が第2港へ")
	roundtrip(game,"returned")
	var walking := base.duplicate(true);FirstRegion.place(walking["overworld"],FirstRegion.outside("second_port_entrance"));walking["overworld"]["transport"]="walk"
	check(FirstRegion.move(walking,Vector2i(169,98)).get("kind")=="moved" and FirstRegion.at(walking["overworld"],data["definition"]["second_port_spawn"]),"沿岸から徒歩入場")
	check(FirstRegionTravel.snapshot(walking)["visited"].has("brine_port"),"徒歩入場で訪問記録")
	check(FirstRegionTravel.data()["docks"].size()==2,"第1地方の乗降2か所を維持")
	finish()

func finish() -> void:
	check(Time.get_ticks_msec()-started<LIMIT_MS,"180秒以内")
	PlaySessionMetrics.write_json("res://docs/verification/region2-port/checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"elapsed_ms":Time.get_ticks_msec()-started,"limit_ms":LIMIT_MS,"method":"人工状態による境界と機能の検査。通常操作はruntimeの撮影記録で別に確認。"})
	for failure in failures:printerr("REGION2_PORT_FAIL: "+failure)
	print("REGION2_PORT_PASS: checks=%d" % checks if failures.is_empty() else "REGION2_PORT_FAIL")
	quit(0 if failures.is_empty() else 1)
