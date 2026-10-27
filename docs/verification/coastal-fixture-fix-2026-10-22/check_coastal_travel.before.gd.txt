extends SceneTree
## 人工状態で境界・保存を確認する。通常到達と実画面撮影とは区別する。
var checks := 0
var failures: Array[String]=[]
func check(ok: bool, message: String) -> void:
	checks+=1
	if not ok:failures.append(message)
func fixture() -> Dictionary:
	var game := GameSession.new();check(game.new_first_region(),"新規状態")
	var state := game.export_state()
	state["party"].append_array(state["first_region"]["reserve"]);state["first_region"]["reserve"]=[]
	state["inventory"]["gate_pass"]=1
	state["progress_flags"]["castle_north_permission"]=true;state["progress_flags"]["mountain_path_open"]=true
	state["overworld"]["cleared"]=["first_boss","forest_tower_boss"]
	FirstRegion.place(state["overworld"],{"layer":"interior","node":"first_port","room":5,"cell":[8,6]});state["overworld"]["facing"]=3
	FirstRegionTravel.ensure(state)
	return state
func session(state: Dictionary) -> GameSession:
	var game := GameSession.new();check(game.import_state(state),"境界検査用の状態が有効")
	return game
func rejected(game: GameSession, destination: String, actor: String, reason: String) -> void:
	var before := game.export_state()
	check(not game.cast_first_region_return(actor,destination),reason)
	check(game.export_state()==before,reason+"で状態不変")
func roundtrip(game: GameSession, label: String) -> void:
	var path := "user://coastal_boundary_%s_%d.json" % [label,OS.get_process_id()]
	check(game.save_game(path),label+"の通常保存")
	var loaded := GameSession.new();check(loaded.load_game(path) and loaded.export_state()==game.export_state(),label+"の完全復元")
func _initialize() -> void:
	var initial := fixture();var game := session(initial)
	rejected(game,"first_port","pc_01","未習得を拒否")
	check(not game.finish_first_region_travel("return"),"会話前の習得を拒否")
	check(game.interact_first_region().get("travel_lesson")=="return","祠で教わる会話")
	check(not FirstRegionTravel.snapshot(game.export_state())["return_learned"],"会話開始だけでは習得しない")
	check(game.finish_first_region_travel("return"),"会話終了で習得")
	var ready := game.export_state()
	for destination in ["start_village","first_castle","first_port"]:
		var state := ready.duplicate(true);state["party"][1]["mp"]=2
		var t: Dictionary=state["first_region"]["travel"];t["ship_owned"]=true;t["ship_cell"]=[65,50]
		game=session(state);var before:=game.export_state()
		check(game.cast_first_region_return("pc_02",destination),"訪問済みの転移: "+destination)
		var after:=game.export_state();check(after["party"][1]["mp"]==0,"選んだ人のMP2消費")
		for i in [0,2,3]:check(after["party"][i]["mp"]==before["party"][i]["mp"],"他の仲間のMP不変")
		var entry: Dictionary=FirstRegionTravel.data()["destinations"].filter(func(v:Dictionary)->bool:return v["id"]==destination)[0]
		check(FirstRegion.at(after["overworld"],FirstRegion.outside(entry["entrance"])) and after["overworld"]["transport"]=="walk","入口前・徒歩")
		check(after["first_region"]["travel"]["ship_cell"]==[59,48],"船も港へ移動")
		roundtrip(game,destination)
	var state:=ready.duplicate(true);state["first_region"]["travel"]["visited"].erase("first_castle")
	rejected(session(state),"first_castle","pc_01","未訪問を拒否")
	state=ready.duplicate(true);state["party"][0]["mp"]=1;rejected(session(state),"first_port","pc_01","MP不足を拒否")
	state=ready.duplicate(true);state["party"][0]["hp"]=0;rejected(session(state),"first_port","pc_01","戦闘不能を拒否")
	for location in [{"layer":"interior","node":"first_cave","room":0,"cell":[17,22]},{"layer":"interior","node":"first_forest_tower","room":0,"cell":[10,14]}]:
		state=ready.duplicate(true);FirstRegion.place(state["overworld"],location);rejected(session(state),"first_port","pc_01","洞窟・塔からの転移を拒否")
	game=session(ready);check(game.start_first_region_battle({"kind":"battle","id":"coastal_encounter","enemies":["river_beast"],"seed":23})!=null,"海の戦闘の境界状態")
	rejected(game,"first_port","pc_01","戦闘中を拒否")
	game=session(ready);check(not game.board_first_region_ship(),"船を借りる前の乗船拒否")
	state=ready.duplicate(true);FirstRegion.place(state["overworld"],{"layer":"interior","node":"first_port","room":7,"cell":[9,7]});state["overworld"]["facing"]=2
	game=session(state);check(game.interact_first_region().get("travel_lesson")=="ship","荷受け所で借用")
	check(game.finish_first_region_travel("ship"),"会話終了で船を取得")
	var owned:=game.export_state();check(not game.finish_first_region_travel("ship") and game.export_state()==owned,"船の二重取得なし")
	for dock in FirstRegionTravel.data()["docks"]:
		state=owned.duplicate(true);FirstRegion.place(state["overworld"],dock["land"]);state["first_region"]["travel"]["ship_cell"]=dock["ship_cell"].duplicate()
		game=session(state);check(game.board_first_region_ship(),"港・浅瀬から乗船")
		check(game.overworld_state()["transport"]=="ship","乗船状態")
		roundtrip(game,"乗船"+dock["id"])
		check(game.board_first_region_ship(),"港・浅瀬で下船")
		check(FirstRegion.at(game.overworld_state(),dock["land"]) and game.overworld_state()["transport"]=="walk","下船位置・徒歩")
		roundtrip(game,"下船"+dock["id"])
	state=owned.duplicate(true);FirstRegion.place(state["overworld"],{"layer":"world","node":"","room":0,"cell":[65,50]});state["overworld"]["transport"]="ship";state["first_region"]["travel"]["ship_cell"]=[65,50]
	game=session(state);check(not game.board_first_region_ship() and game.export_state()==state,"港・浅瀬以外で下船拒否")
	check(not game.change_world_transport("flight"),"飛行手段を使えない")
	check(not game.first_region_walkable(Vector2i(32,53)),"船が陸地を通れない")
	check(is_equal_approx(WorldTerrain.seconds_per_step("ship"),.15),"船の移動速度150ms")
	roundtrip(game,"航行")
	var invalid:=state.duplicate(true);invalid["overworld"]["transport"]="flight";check(not game.import_state(invalid),"飛行状態の保存を拒否")
	invalid=state.duplicate(true);invalid["first_region"]["travel"]["ship_cell"]=[32,53];check(not game.import_state(invalid),"船の陸上保存を拒否")
	var old:=initial.duplicate(true);old["first_region"].erase("travel");game=session(old);roundtrip(game,"追加状態のない旧保存")
	PlaySessionMetrics.write_json("res://docs/verification/sprint5-travel/boundary-checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"method":"人工状態の境界検査。通常操作の到達証拠とは別。"})
	for failure in failures:printerr("COASTAL_BOUNDARY_FAIL: "+failure)
	print("COASTAL_BOUNDARY_PASS: checks=%d" % checks if failures.is_empty() else "COASTAL_BOUNDARY_FAIL")
	quit(0 if failures.is_empty() else 1)
