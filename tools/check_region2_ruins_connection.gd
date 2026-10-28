extends SceneTree
## 人工境界保存から本番APIの正負例。キー入力は別の実描画検査で行う。
const OUT := "res://docs/verification/task-084/"
const DIRS := [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]
var checks: Array = []

func check(ok: bool, label: String, detail: Variant = null) -> void:
	checks.append({"ok":ok,"label":label,"detail":detail})
	if not ok:printerr("RUINS_CONNECTION_FAIL: "+label+" "+str(detail))

func fixture(complete: bool = false, layer: String = "world", cell: Array = [176,92]) -> Dictionary:
	var game := GameSession.new()
	check(game.new_first_region(),"通常新ゲームから人工境界を作成")
	var saved := game.export_state()
	for flag in FirstRegionStory.FLAGS:saved["progress_flags"][flag]=true
	if complete:saved["progress_flags"][Region2ShrineStory.COMPLETE_FLAG]=true
	FirstRegion.place(saved["overworld"],{"layer":layer,"node":"region2_ruins" if layer=="interior" else "","room":0,"cell":cell})
	return saved

func unchanged(before: Dictionary, after: Dictionary, label: String) -> void:
	var expected := before.duplicate(true)
	for key in ["layer","node","room","cell","facing","entry_lock"]:
		expected["overworld"][key]=after["overworld"][key]
	check(expected==after,label+"：位置以外の全保存値不変")

func position(game: GameSession, layer: String, cell: Array, facing: int, lock: String) -> bool:
	var state := game.overworld_state()
	return state["layer"]==layer and state["node"]==("region2_ruins" if layer=="interior" else "") and state["room"]==0 and state["cell"]==cell and state["facing"]==facing and state["entry_lock"]==lock

func roundtrip(game: GameSession, label: String) -> void:
	var expected := game.export_state()
	for suffix in ["manual","checkpoint"]:
		var path: String = "user://task084-"+suffix+".json"
		check(game.save_game(path),label+"：通常保存/同じcheckpoint保存経路",suffix)
		var loaded := GameSession.new()
		check(loaded.load_game(path) and not loaded.position_relocated and loaded.export_state()==expected,label+"：別インスタンス全値一致",suffix)
		check(loaded.resume_region2_shrine_story().is_empty(),label+"：ロードで会話・入場の自動発火なし")
		check(loaded.move_first_region(WorldExpedition.point(expected["overworld"]["cell"])).is_empty() and loaded.export_state()==expected,label+"：静止再通知拒否")

func route(saved: Dictionary, goal: Vector2i) -> Array[Vector2i]:
	var start := WorldExpedition.point(saved["overworld"]["cell"])
	var seen := {start:start};var queue: Array[Vector2i]=[start];var cursor := 0
	var triggers: Array[Vector2i]=[]
	for link in Region2Ruins.data()["stairs"]:
		if link["from_room"]==saved["overworld"]["room"]:triggers.append(WorldExpedition.point(link["from_cell"]))
	triggers.append(Vector2i(18,20))
	while cursor<queue.size() and not seen.has(goal):
		var here := queue[cursor];cursor+=1
		for dir in DIRS:
			var next: Vector2i=here+dir
			if seen.has(next) or (next in triggers and next!=goal) or not FirstRegion.walkable(saved,next):continue
			seen[next]=here;queue.append(next)
	var result: Array[Vector2i]=[]
	if not seen.has(goal):return result
	var cell := goal
	while cell!=start:result.push_front(cell);cell=seen[cell]
	return result

func _initialize() -> void:
	OS.set_environment("RPG_QA_SAVE_PREFIX","task084")
	call_deferred("run")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	api_cases()
	var failed := checks.filter(func(c:Dictionary)->bool:return not c["ok"])
	var file := FileAccess.open(OUT+"runtime-checks.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"status":"PASS" if failed.is_empty() else "FAIL","checks":checks,"fixture":"人工境界保存・本番API。実キーはcapture別記録。"},"\t")+"\n");file.close()
	print("RUINS_CONNECTION_%s: checks=%d failures=%d"%["PASS" if failed.is_empty() else "FAIL",checks.size(),failed.size()])
	quit(0 if failed.is_empty() else 1)

func api_cases() -> void:
	var game := GameSession.new()
	var atlas_expected := {"start_village":[38,64],"region2_ruins":[176,91],"region2_village":[169,88],"brine_port":[169,98]}
	# 第1地方の既存入口は基点データと照合。第2地方は依頼の独立固定座標。
	atlas_expected["start_village"]=FirstRegion.data()["village_entrance"]["cell"].duplicate()
	for node in ["start_village","first_cave","first_castle","first_forest_tower","first_port","brine_port","region2_village","region2_ruins","region3_port"]:
		var key: String={"start_village":"village_entrance","first_cave":"cave_entrance","first_castle":"castle_entrance","first_forest_tower":"tower_entrance","first_port":"port_entrance","brine_port":"second_port_entrance","region2_village":"region2_village_entrance","region2_ruins":"region2_ruins_entrance","region3_port":"region3_port_entrance"}[node]
		var expected: Array=atlas_expected.get(node,FirstRegion.data()[key]["cell"])
		check(FirstRegionAtlas.current_cell({"layer":"interior","node":node,"cell":[1,1]})==WorldExpedition.point(expected),"Atlasは内部siteの世界入口を示す",node)
	check(FirstRegionAtlas.current_cell({"layer":"world","node":"","cell":[176,92]})==Vector2i(176,92),"Atlasの世界現在地を保持")
	for complete in [false,true]:
		for old_cell in [[176,91],[176,92]]:
			var saved := fixture(complete,"world",old_cell)
			check(game.import_state(saved) and game.export_state()==saved,"入口上/隣の旧世界保存を拒否・消失・自動入場しない",[complete,old_cell])
			roundtrip(game,"旧世界"+str(complete)+str(old_cell))
	for flags in [{},{"monster_jobs_unlocked":true},{"region2_shrine_jobs_unlocked":true}]:
		var saved := fixture();saved["progress_flags"].merge(flags,true)
		check(game.import_state(saved),"未完了境界保存",flags)
		check(game.first_region_walkable(Vector2i(176,91)),"未完了でも入口床は通行可")
		var event := game.move_first_region(Vector2i(176,91))
		check(event.get("kind") in ["moved","battle"] and game.overworld_state()["layer"]=="world" and game.overworld_state()["cell"]==[176,91],"職業権・共通ゲートを入場完了の代用にしない",flags)
		unchanged(saved,game.export_state(),"未完了入口通過")
		check(not game.export_state()["progress_flags"].get(Region2ShrineStory.COMPLETE_FLAG,false),"未完了フラグを補完しない")
	var saved := fixture(true)
	check(game.import_state(saved),"完了だけの境界保存を受理")
	var before := game.export_state()
	check(game.move_first_region(Vector2i(176,91)).get("kind")=="moved" and position(game,"interior",[18,19],3,"region2_ruins_entrance"),"完了後の通常歩行で指定着地・北向き・entry_lock")
	unchanged(before,game.export_state(),"入場")
	if game.overworld_state()["layer"]=="interior":
		roundtrip(game,"入場直後")
		before=game.export_state()
		for i in range(4):check(game.move_first_region(Vector2i(176,91)).is_empty() and game.export_state()==before,"古い世界画面の反復入力拒否")
		check(game.move_first_region(Vector2i(18,20)).get("kind")=="moved" and position(game,"world",[176,92],0,"region2_ruins_entrance"),"通常退出で指定世界帰着・下向き・lock")
		unchanged(before,game.export_state(),"退出")
		roundtrip(game,"退出直後")
		before=game.export_state()
		for i in range(4):check(game.move_first_region(Vector2i(18,20)).is_empty() and game.export_state()==before,"古い内部画面の反復入力拒否")
		check(game.move_first_region(Vector2i(176,93)).get("kind") in ["moved","battle"] and game.overworld_state()["layer"]=="world" and game.overworld_state()["entry_lock"]=="","退出方向の保持は世界を歩く・即再入場なし")
	for complete in [false,true]:
		for old_cell in [[18,19],[18,20],[18,5]]:
			saved=fixture(complete,"interior",old_cell)
			check(game.import_state(saved) and game.export_state()==saved,"S10未完了を含む旧内部保存を受理",[complete,old_cell])
			roundtrip(game,"旧内部"+str(complete)+str(old_cell))
			if old_cell==[18,20]:check(game.move_first_region(Vector2i(18,19)).get("kind")=="moved","出口上のロードで自動退出せず一歩戻れる")
			var path := route(game.export_state(),Vector2i(18,20))
			check(not path.is_empty(),"旧内部保存から通常出口へ到達",old_cell)
			for step in path:check(game.move_first_region(step).get("kind")=="moved","出口まで通常歩行")
			check(position(game,"world",[176,92],0,"region2_ruins_entrance"),"旧内部保存から完了不要で退場")
			unchanged(saved,game.export_state(),"旧内部帰還")
	# S10会話の途中と古い確認通知では入口へ進行しない。
	saved=fixture(false,"interior",[8,10]);saved["overworld"]["node"]="region2_village";saved["overworld"]["room"]=4
	check(game.import_state(saved),"会話途中の境界準備")
	var scene := game.resume_region2_shrine_story()
	for page in range(9):
		before=game.export_state()
		check(game.move_first_region(Vector2i(176,91)).is_empty() and game.move_first_region(Vector2i(8,11)).is_empty() and game.export_state()==before,"会話中の移動と古い世界入力を拒否",page)
		check(not game.confirm_region2_shrine_story(scene.get("shrine_scene",""),int(scene.get("shrine_run",0)),page).is_empty(),"既存通常確認",page)
	check(game.export_state()["progress_flags"].get(Region2ShrineStory.COMPLETE_FLAG,false),"末尾の通常確認でだけ完了")
	before=game.export_state()
	check(game.confirm_region2_shrine_story(scene.get("shrine_scene",""),int(scene.get("shrine_run",0)),8).is_empty() and game.export_state()==before,"古い最終確認の再送は無変更")
	# 旧壁保存補正は北の従来spawnを保持。
	saved=fixture(false,"interior",[18,19]);check(game.import_state(saved),"補正試験の通常保存")
	check(game.save_game("user://task084-legacy-wall.json"),"壁負例の元保存")
	var decoded := SavedDocument.decode(JSON.parse_string(FileAccess.get_file_as_string("user://task084-legacy-wall.json")))
	decoded["overworld"]["cell"]=[18,21]
	var file := FileAccess.open("user://task084-legacy-wall.json",FileAccess.WRITE);file.store_string(SavedDocument.encode(decoded));file.close()
	check(game.load_game("user://task084-legacy-wall.json") and game.position_relocated and game.overworld_state()["cell"]==[18,5] and game.overworld_state()["entry_lock"]=="","旧spawn[18,5]へ補正・南着地へ変更しない")
	check(not Region2Ruins.data()["encounters_enabled"] and not Region2Ruins.data()["boss_enabled"],"内部遭遇・ボス無効を保持")
	check(float(SecondRegionCoast.data()["ground_encounter"]["chance"])==0.025,"世界の既存遭遇率0.025を保持")
