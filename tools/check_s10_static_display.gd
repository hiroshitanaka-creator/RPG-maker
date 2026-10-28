extends SceneTree
## 083：既存占有・保存補正・表示専用操作の正負例。本文は082検査で照合する。
const OUT := "res://docs/verification/task-083/"
var checks: Array = []

func check(ok: bool, label: String, detail: Variant = null) -> void:
	checks.append({"ok":ok,"label":label,"detail":detail})
	if not ok:printerr("S10_STATIC_FAIL: "+label+" "+str(detail))

func fixture(cell: Array = [8,10], complete: bool = true) -> Dictionary:
	var game := GameSession.new()
	game.new_first_region()
	var saved := game.export_state()
	saved["party"].append_array(saved["first_region"]["reserve"])
	saved["first_region"]["reserve"]=[]
	saved["inventory"]["gate_pass"]=1
	saved["overworld"]["cleared"]=["first_boss","forest_tower_boss"]
	for flag in FirstRegionStory.FLAGS:saved["progress_flags"][flag]=true
	for flag in ["job_change_unlocked","castle_north_permission","mountain_path_open"]:saved["progress_flags"][flag]=true
	if complete:
		saved["progress_flags"]["region2_shrine_seen"]=true
		saved["progress_flags"]["region2_shrine_jobs_unlocked"]=true
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":"region2_village","room":4,"cell":cell})
	return saved

func route(saved: Dictionary, start: Vector2i, target: Vector2i) -> Array:
	var todo := [start]
	var seen := {start:true}
	var paths := {start:[]}
	while not todo.is_empty():
		var here: Vector2i=todo.pop_front()
		if here==target:return paths[here]
		for d in [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]:
			var p: Vector2i=here+d
			if seen.has(p) or not FirstRegion.walkable(saved,p):continue
			seen[p]=true
			paths[p]=paths[here]+[p]
			todo.append(p)
	return []

func _initialize() -> void:
	OS.set_environment("RPG_QA_SAVE_PREFIX","task083_"+str(OS.get_process_id()))
	call_deferred("run")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var saved := fixture()
	var events: Array=FirstRegion.residents_for(saved)
	var static_events: Array=events.filter(func(e:Dictionary)->bool:return e.get("display_only",false))
	check(static_events.size()==1,"表示専用NPCはroom4に1件")
	if static_events.size()==1:
		var e: Dictionary=static_events[0]
		check(e["kind"]=="npc" and e["cell"]==[8,6] and e.get("static_sprite")=="assets/characters/ner/event_standing.png","Bの採用配置と静止素材")
		check(not e.has("text") and not e.has("patrol") and not e.has("sprite"),"台詞・歩行シート・巡回を追加しない")
	check(not FirstRegion.walkable(saved,Vector2i(8,6)),"採用セルは既存npc占有で通行不可")
	check(not FirstRegion.walkable(saved,Vector2i(12,6)),"既存長老の占有維持")
	for p in [Vector2i(8,10),Vector2i(8,11),Vector2i(12,7)]:
		check(FirstRegion.walkable(saved,p),"入口・出口・長老の正面は歩行可",p)
		check(p==Vector2i(8,10) or not route(saved,Vector2i(8,10),p).is_empty(),"入口から出口・長老へ到達",p)
	var game := GameSession.new()
	for approach in [[8,7,3],[7,6,2],[9,6,1],[8,5,0]]:
		check(game.import_state(fixture(approach.slice(0,2))),"表示専用への接近状態を通常APIで受理",approach)
		game.first_region_face([Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP][approach[2]])
		var before := game.export_state()
		for i in range(5):check(game.interact_first_region().is_empty() and game.export_state()==before,"決定反復で本文・向き保存・進行変更なし",approach)
		check(not game.advance_first_region_residents() and game.export_state()==before,"静止位置の更新なし")
	check(game.import_state(fixture([8,7])),"衝突試験の準備")
	game.first_region_face(Vector2i.UP)
	var blocked := game.export_state()
	check(game.move_first_region(Vector2i(8,6)).is_empty() and game.export_state()==blocked,"通常移動でも人物すり抜け拒否")
	check(game.import_state(fixture()),"通常経路の準備")
	for p in route(saved,Vector2i(8,10),Vector2i(12,7)):check(game.move_first_region(p).get("kind")=="moved","通常移動で長老へ迂回",p)
	game.first_region_face(Vector2i.UP)
	var talk := game.interact_first_region()
	check(talk.get("kind")=="dialogue" and talk.get("speaker")=="村の長老" and talk.get("text")==["旅の身支度は、整いましたか。","慌てず、確かめていってください。"],"既存長老の本文と向き処理を維持")
	# 旧版で有効だった占有セル保存。通常保存の型情報を保ち、位置のみ旧セルへ変える。
	for completed in [false,true]:
		var initial := fixture([8,10],completed)
		check(game.import_state(initial),"旧保存作成の安全な基点",completed)
		var path := "user://task083-occupied-%s.json"%str(completed)
		check(game.save_game(path),"通常保存を作成")
		var doc: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path))
		doc["overworld"]["cell"]=[8,6]
		check(PlaySessionMetrics.write_json(path,doc),"型契約を保持した旧占有位置保存")
		var copy := FileAccess.open(OUT+"occupied-%s.json"%str(completed),FileAccess.WRITE)
		copy.store_buffer(FileAccess.get_file_as_bytes(path));copy.close()
		var loaded := GameSession.new()
		check(loaded.load_game(path) and loaded.position_relocated,"占有セルの旧保存を入口に補正",completed)
		var expected := initial.duplicate(true)
		expected["overworld"]["entry_lock"]=""
		check(loaded.export_state()==expected,"補正後の位置[8,10]と全所持品・編成・進行不変",completed)
		check(loaded.save_game(path) and game.load_game(path) and not game.position_relocated and game.export_state()==expected,"補正の再保存・通常ロードは安定")
		var event := game.resume_region2_shrine_story()
		check(event.is_empty() if completed else event.get("shrine_scene")=="region2_shrine_s10","未完了は冒頭復帰・完了後は再演なし",completed)
		if not completed:
			for page in range(9):check(not game.confirm_region2_shrine_story(event["shrine_scene"],event["shrine_run"],page).is_empty(),"補正後も082を通常確認で完了",page)
		check(game.move_first_region(Vector2i(8,11)).get("kind")=="moved" and game.overworld_state()["room"]==0,"補正後も通常退出")
		check(game.move_first_region(Vector2i(33,8)).get("kind")=="moved" and game.overworld_state()["room"]==4 and game.overworld_state()["entry_lock"]=="region2_village_door","再入室は既存扉とentry_lock維持・再演なし")
	var failed := checks.filter(func(c:Dictionary)->bool:return not c["ok"])
	var f := FileAccess.open(OUT+"runtime-checks.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"status":"PASS" if failed.is_empty() else "FAIL","checks":checks},"\t")+"\n");f.close()
	print("S10_STATIC_%s: checks=%d failures=%d"%["PASS" if failed.is_empty() else "FAIL",checks.size(),failed.size()])
	quit(0 if failed.is_empty() else 1)
