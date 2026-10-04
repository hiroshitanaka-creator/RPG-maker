extends "res://tools/capture_castle_town.gd"
## 009 最新の通常入力・上層画素回帰。受付サービスの正負例は007の専用検査へ引継ぐ。
const DIR := "res://docs/verification/task-009/latest/"
var shots: Array = []
var poses: Array = []
var mode := "journey"
var source_sha := ""

func point(index: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":"region2_village","room":index,"cell":cell}

func _trigger_points() -> Array:
	var points := super._trigger_points()
	if _definition.has("region2_village_exits"):
		for exit_link in _definition["region2_village_exits"]:points.append(exit_link["from"])
		points.append(_world_point(_definition["region2_village_entrance"]["cell"]))
		points.append(_definition["second_port_exit"])
		points.append(_world_point(_definition["second_port_entrance"]["cell"]))
	return points

func _step_direction(delta: Vector2i) -> bool:
	var ok := await super._step_direction(delta)
	poses.append({"direction":[delta.x,delta.y],"pose":_pose(),"mode":_snapshot().get("mode")})
	return ok

func picture(name: String) -> void:
	await _frames(4);await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := _main.get_viewport().get_texture().get_image()
	castle_check(DisplayServer.get_name()!="headless" and image.get_size()==Vector2i(1024,576),"本番UI・実レンダラー: "+name)
	castle_check(image.save_png(OUTPUT+name+".png")==OK,"本番画面保存: "+name)
	castle_images.append(name+".png")
	var shot := {"image":name+".png","pose":_pose(),"camera":[],"visible":0,"hidden":0,"matched":0,"ui_covered":0}
	if _snapshot().get("mode")=="world" and _pose().get("node")=="region2_village":
		var screen: FirstRegionScreen=_main.get("_region_screen");var view := screen.map_view
		var saved := _state();var state: Dictionary=saved["overworld"]
		var actor: Dictionary=saved["party"].filter(func(a:Dictionary)->bool:return a["id"]==saved.get("leader_id","pc_01"))[0]
		var appearance := CharacterVisuals.appearance(actor,"walk",view.walk_frame,int(state["facing"]))
		var sprite := (load(appearance["path"]) as Texture2D).get_image().get_region(Rect2i(appearance["region"]))
		var map: Dictionary=view._map;var atlas := (load("res://"+str(map["overlays"]["path"])) as Texture2D).get_image()
		var cell := WorldExpedition.point(state["cell"]);var pos := view._screen(Vector2(cell))+Vector2(0,-16)
		var windows: Array=[]
		for panel in screen.find_children("*","PanelContainer",true,false):
			if panel.is_visible_in_tree():windows.append(panel.get_global_rect())
		for y in range(48):
			for x in range(32):
				var color := sprite.get_pixel(x,y)
				if color.a<1:continue
				var pixel := cell*32+Vector2i(x,y-16);var covered := false
				for piece in map["overlays"]["pieces"]:
					if float(piece[6])-0.5<=cell.y+1:continue
					var local := pixel-Vector2i(piece[4],piece[5])
					if local.x>=0 and local.y>=0 and local.x<int(piece[2]) and local.y<int(piece[3]) and atlas.get_pixel(int(piece[0])+local.x,int(piece[1])+local.y).a>0:covered=true;break
				if covered:shot["hidden"]+=1;continue
				var under_window := false
				for window in windows:
					if window.has_point(pos+Vector2(x,y)+Vector2(.5,.5)):under_window=true;break
				if under_window:shot["ui_covered"]+=1;continue
				shot["visible"]+=1
				var sample := Vector2i((pos+Vector2(x,y))*2)+Vector2i.ONE
				if not Rect2i(Vector2i.ZERO,image.get_size()).has_point(sample):continue
				var actual := image.get_pixelv(sample)
				if maxi(maxi(absi(actual.r8-color.r8),absi(actual.g8-color.g8)),absi(actual.b8-color.b8))<=1:shot["matched"]+=1
		shot["camera"]=[view._camera.x,view._camera.y]
		castle_check(shot["visible"]>0 and shot["matched"]==shot["visible"],"足元順で上層外の人物全画素一致: "+name)
		if name.contains("behind"):castle_check(shot["hidden"]>=8 and shot["visible"]>=8,"奥の上層による部分遮蔽: "+name)
	shots.append(shot)

func held(code: int, seconds: float) -> void:
	_input_log.append("held:"+str(code))
	var event := InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true
	_main.get_viewport().push_input(event,true)
	await create_timer(seconds).timeout
	event=event.duplicate();event.pressed=false;_main.get_viewport().push_input(event,true)
	await _frames(4);await _settle()
	poses.append({"held_key":code,"seconds":seconds,"pose":_pose()})

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	mode="details" if "--details" in args else ("restart-%s" % args[args.find("--restart")+1] if "--restart" in args else "journey")
	OUTPUT=DIR+mode+"/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.min_size=Vector2i(1024,576);root.max_size=Vector2i(1024,576);root.size=Vector2i(1024,576)
	root.position=Vector2i(-32000,-32000)
	var source := "user://village009_port-start.json" if mode=="journey" else ("user://village009_0_0.json" if mode=="details" else "user://village009_%s_0.json" % args[args.find("--restart")+1])
	if not castle_check(FileAccess.file_exists(source),"本番save_gameで作られた開始保存"):finish();return
	source_sha=FileAccess.get_sha256(source)
	castle_check(source_sha==FileAccess.get_sha256(DIR+"saved-inputs/"+source.get_file()),"撮影起点がリポジトリの保管済み通常保存と全バイト一致")
	var destination := "user://qa_"+OS.get_environment("RPG_QA_SAVE_PREFIX")+"_save.json"
	var file := FileAccess.open(destination,FileAccess.WRITE);file.store_buffer(FileAccess.get_file_as_bytes(source));file.close()
	castle_check(FileAccess.get_sha256(destination)==source_sha,"開始保存の無編集コピー")
	var scene: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	_main=scene.instantiate();root.add_child(_main);process_frame.connect(_watch);await _frames()
	if not castle_check(await _button(["手動セーブから再開"]) and await _settle(),"タイトルの通常ロード"):finish();return
	FirstRegion.data();_definition=FirstRegion.data().duplicate(true);_sites=FirstRegion._data["sites"].duplicate(true)
	_definition["doors"].append_array(_definition["region2_village_doors"])
	_definition["doors"].append_array(_definition["second_port_doors"])
	if mode=="journey":await journey()
	elif mode=="details":await details()
	else:await restart_route(int(args[args.find("--restart")+1]))
	finish()

func coast_to_village() -> bool:
	if not castle_check(_at(_world_point([169,99])),"既存港外を起点にする"):return false
	if not await _step_direction(Vector2i.LEFT):return false
	for y in range(11):
		if not await _step_direction(Vector2i.UP):return false
	if not castle_check(_at(_world_point([168,88])),"港外から指定の13歩経路で村入口前へ"):return false
	await picture("02-world-village-entrance")
	return await _walk(_world_point([169,88]),point(0,[4,15]))

func to_port() -> bool:
	if _pose().get("room",0)>0:
		if not await _walk(point(_pose()["room"],[8,11]),Region2Village.data()["definition"]["region2_village_doors"][_pose()["room"]*2-1]["to"]):return false
	if not await _walk(point(0,[3,13]),_world_point([168,88])):return false
	for y in range(11):
		if not await _step_direction(Vector2i.DOWN):return false
	if not await _step_direction(Vector2i.RIGHT):return false
	return await _walk(_world_point([169,98]),_definition["second_port_spawn"])

func journey() -> void:
	castle_check(_at({"layer":"interior","node":"brine_port","room":0,"cell":[4,2]}),"人工境界保存の港内起点を明示")
	await picture("01-port-start")
	if not castle_check(await _walk(_definition["second_port_exit"],_world_point([169,99])),"通常入力で港出口へ"):return
	if not castle_check(await coast_to_village(),"通常キー13歩で村へ入場"):return
	await create_timer(2.2).timeout;await picture("03-west-landing")
	var stationary := _state();await create_timer(.35).timeout
	castle_check(_state()==stationary,"入場後の入力なしでは再遷移しない")
	var visited: Array = _state()["first_region"]["travel"]["visited"].duplicate()
	castle_check(visited.count("region2_village")==1,"初訪問を既存visitedへ1件")
	var native: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/region2-village-backdrops/native-checks.json")))
	for index in range(5):
		if index>0:
			if not castle_check(await _walk(point(index,[8,10])),"扉から通常入室: "+str(index)):return
			await create_timer(2.2).timeout
		await picture("04-room-%d-entrance" % index)
		var samples: Array=[]
		for entry in native["captures"]:
			if str(entry["path"]).contains("/"+["exterior","inn","item","weapon","shrine"][index]+"/") and str(entry["path"]).ends_with("native-behind.png"):samples.append(entry["cell"])
		var front: Array=[[16,9],[12,5],[8,6],[8,6],[8,5]][index]
		if not castle_check(await _walk(point(index,front)),"受付・祭壇・扉前へ通常歩行"):return
		await picture("05-room-%d-front" % index)
		if index==1:
			if not castle_check(await _walk(point(0,[16,9])),"押し続け試験の扉前へ通常退出"):return
			await held(KEY_UP,.65)
			castle_check(_pose().get("room")==1,"扉の上入力を押し続けても室内で進み、往復しない")
			if not castle_check(await _walk(point(1,[8,10])),"出口の押し続け試験へ通常歩行"):return
			await held(KEY_DOWN,.65)
			castle_check(_pose().get("room")==0,"退出の下入力を押し続けても外観にとどまる")
			if not castle_check(await _walk(point(index,front)),"押し続け試験後に通常再入室"):return
		if not castle_check(samples.size()==1 and await _walk(point(index,[samples[0][0],samples[0][1]+1])) and await _step_direction(Vector2i.UP) and _at(point(index,samples[0])),"家具・手前壁の奥へ通常歩行し北向きに立つ"):return
		await picture("06-room-%d-behind" % index)
		if index>0:
			if not castle_check(await _walk(point(index,[8,11]),Region2Village.data()["definition"]["region2_village_doors"][index*2-1]["to"]),"対応扉前へ通常退出"):return
			await picture("07-room-%d-return" % index)
	# 東アーチ→東着地、西アーチ→西着地を通常入力で確認。
	if not castle_check(await _walk(point(0,[42,13]),_world_point([170,88])),"東アーチから退出"):return
	await picture("08-east-outside")
	await held(KEY_RIGHT,.45)
	castle_check(_pose().get("layer")=="world","アーチ退出後の同方向押し続けで往復しない")
	if not castle_check(await _walk(_world_point([169,88]),point(0,[41,15])),"東側から再入場"):return
	await picture("09-east-landing-camera-edge")
	if not castle_check(await _walk(point(0,[3,13]),_world_point([168,88])),"西アーチから退出"):return
	if not castle_check(await _walk(_world_point([169,88]),point(0,[4,15])),"西側から再入場"):return
	castle_check(_state()["first_region"]["travel"]["visited"]==visited,"再訪問で重複なし")
	var before_save := _state()
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["セーブ"]) and await _button(["現在の冒険に戻る"]),"通常メニューの保存"):return
	if not castle_check(await _walk(point(0,[4,16])),"保存後に一歩移動"):return
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["手動セーブから再開"]) and await _settle(),"通常メニューの再読込"):return
	castle_check(_state()==before_save,"通常保存の全状態復元")
	await picture("10-menu-restored")
	if not castle_check(await to_port(),"読込後に通常徒歩で港へ帰着"):return
	await picture("11-port-returned")
	var before_return := _state();var actor: Dictionary=before_return["party"].filter(func(a:Dictionary)->bool:return a["hp"]>0 and a["mp"]>=2)[0]
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["帰還の風"]) and await _button(["%s MP %d" % [actor["name"],actor["mp"]]]),"既存メニューで帰還と生存者を選択"):return
	await picture("12-return-destinations")
	if not castle_check(await _button(["オアシスの村（仮）"]),"訪問済み村を選択"):return
	var after := _state();var member: Dictionary=after["party"].filter(func(a:Dictionary)->bool:return a["id"]==actor["id"])[0]
	castle_check(member["mp"]==actor["mp"]-2 and _at(_world_point([168,88])) and after["first_region"]["travel"]["ship_cell"]==[155,110],"港側から村へMP2・既存第2港の船")
	await picture("13-returned-to-village")

func restart_route(index: int) -> void:
	var expected: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("user://village009_expected_%d.json" % index)))
	castle_check(_state()==expected,"別プロセスのタイトル再開で全状態復元")
	await create_timer(2.2).timeout;await picture("01-restart-room-%d" % index)
	var corrected_source := "user://village009_relocation_%d.json" % index
	var manual := "user://qa_"+OS.get_environment("RPG_QA_SAVE_PREFIX")+"_save.json"
	var copy := FileAccess.open(manual,FileAccess.WRITE);copy.store_buffer(FileAccess.get_file_as_bytes(corrected_source));copy.close()
	castle_check(await _key(KEY_ESCAPE) and await _button(["手動セーブから再開"]) and await _settle(),"本番メニューで壁保存を読み込む")
	castle_check(_session().position_relocated and str(_main.get("_notice")).contains("安全な入口へ移動しました。") and _pose()["cell"]==FirstRegion.entrance_landing("region2_village",index),"既存の安全補正通知と入口への置き直し")
	await picture("03-position-relocation-notice")
	castle_check(await to_port(),"別プロセス再起動後に通常キーだけで港へ戻る")
	await picture("02-port-after-restart")

func details() -> void:
	await create_timer(2.2).timeout
	if not castle_check(await _walk(point(0,[3,14])),"西アーチ下へ通常歩行"):return
	await picture("01-west-arch-under")
	if not castle_check(await _walk(point(0,[42,14])),"東アーチ下へ通常歩行"):return
	await picture("02-east-arch-under")
	for index in range(1,5):
		if not castle_check(await _walk(point(index,[7,8])),"高い手前壁の客側へ通常歩行"):return
		await create_timer(2.2).timeout
		await picture("03-room-%d-high-front-wall" % index)
		if not castle_check(await _walk(point(index,[8,11]),Region2Village.data()["definition"]["region2_village_doors"][index*2-1]["to"]),"高い壁の開口部から通常退出"):return
	castle_check(await to_port(),"詳細撮影後も港へ通常帰路")

func finish() -> void:
	castle_check(Time.get_ticks_msec()< _deadline and _moves<=LIMIT_MOVES and _input_log.size()<LIMIT_INPUTS and not _input_violation,"既存の180秒・移動・入力予算と禁止操作を維持")
	var report := {"status":"PASS" if castle_failures.is_empty() else "FAIL","checks":castle_checks,"failures":castle_failures,"images":castle_images,"shots":shots,"moves":_moves,"inputs":_input_log,"poses":poses,"turns":_turns,"execution_sha":OS.get_environment("RPG009_EXECUTION_SHA"),"source_sha256":source_sha,"limits":{"milliseconds":LIMIT_MS,"moves":LIMIT_MOVES,"inputs":LIMIT_INPUTS,"turns":LIMIT_TURNS},"renderer":DisplayServer.get_name(),"method":"港内の人工境界保存（通常save_game）から開始。以後は本番キー・画面ボタン・既存戦闘入力だけ。村へのワープ・状態注入・遭遇変更なし。"}
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",report)
	for failure in castle_failures:printerr("VILLAGE_REGRESSION_CAPTURE_FAIL: "+failure)
	print("VILLAGE_REGRESSION_CAPTURE_PASS: checks=%d images=%d" % [castle_checks,castle_images.size()] if castle_failures.is_empty() else "VILLAGE_REGRESSION_CAPTURE_FAIL")
	_finished=true;quit(0 if castle_failures.is_empty() else 1)
