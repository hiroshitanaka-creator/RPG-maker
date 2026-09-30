extends "res://tools/capture_castle_town.gd"
## 新規開始→凍結R-07→城の謁見→塔3階→スイナ加入を通常操作で確かめる。
var tower_shots: Dictionary={}
var joining_observations: Array=[]
var tower_capture_busy := false

func _key(code: int) -> bool:
	while tower_capture_busy:
		if not _active():return false
		await process_frame
	return await super._key(code)

func _combat_command(action: Dictionary) -> bool:
	while tower_capture_busy:
		if not _active():return false
		await process_frame
	return await super._combat_command(action)

func capture_tower_moment(name: String) -> void:
	await picture(name)
	if name=="07-suina-offer":
		var screen: FirstRegionScreen=_main.get("_region_screen")
		castle_check(is_instance_valid(screen) and screen.speaker=="スイナ" and screen.message.begins_with("ええ、同行"),"撮影中に同行の申し出の行を保持")
	tower_capture_busy=false

func _run() -> void:
	OUTPUT="res://docs/verification/sprint5-forest-tower/runtime/"
	# 撮影時だけ垂直同期の待ちを外す。歩行の150ms、時計、検査の上限は変えない。
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	await super._run()

func tower_point(floor_index: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":"first_forest_tower","room":floor_index,"cell":cell}

func _trigger_points() -> Array:
	var points := super._trigger_points()
	if castle_started:
		points.append(_world_point(_definition["tower_entrance"]["cell"]))
		points.append(_definition["tower_exit"])
		points.append(_definition["tower_boss"]["point"])
		for link in _definition["tower_doors"]:points.append(link["from"])
	return points

func _watch() -> void:
	super._watch()
	if not castle_started or not is_instance_valid(_main):return
	var screen: FirstRegionScreen=_main.get("_region_screen")
	if not is_instance_valid(screen) or screen.screen_mode not in ["battle","dialogue"]:return
	var state := _state()
	if state.get("overworld",{}).get("node")!="first_forest_tower":return
	var name := ""
	if screen.screen_mode=="battle":
		name="05-tower-boss" if _session().current_encounter_id()=="forest_tower_boss" else "09-four-party-battle" if state["party"].size()==4 else ""
	if screen.screen_mode=="dialogue":
		if is_instance_valid(screen) and screen.speaker=="スイナ" and screen.message.begins_with("ええ、同行"):
			name="07-suina-offer"
			joining_observations.append({"line":screen.message,"party_size":state["party"].size()})
	if not name.is_empty() and not tower_shots.has(name):
		tower_shots[name]=true
		tower_capture_busy=true
		capture_tower_moment.call_deferred(name)

func roundtrip(label: String) -> void:
	var path := "user://forest_tower_%s_%d.json" % [label,OS.get_process_id()]
	castle_check(_session().save_game(path),label+"で保存")
	var loaded := GameSession.new()
	castle_check(loaded.load_game(path) and loaded.export_state()==_state(),label+"の位置・仲間・宝箱・進行を完全復元")

func _castle_route() -> void:
	_definition["doors"].append_array(_definition["castle_doors"])
	castle_check(not FirstRegion.walkable(_state(),WorldExpedition.point(_definition["tower_entrance"]["cell"])),"謁見前に塔へ入れない")
	if not castle_check(await _walk(_world_point(_definition["castle_entrance"]["cell"]),_definition["castle_spawn"]),"城下町へ通常入場"):return
	if not castle_check(await _walk(castle_point(2,[12,6])),"謁見の間へ通常歩行"):return
	await _key(KEY_UP);await _key(KEY_ENTER);await _settle()
	castle_check(_state()["progress_flags"].get("castle_north_permission",false),"謁見で森への許可")
	if not castle_check(await _walk(_definition["castle_exit"],_outside(_definition["castle_entrance"])),"城下町から外へ"):return
	castle_check(not FirstRegion.walkable(_state(),Vector2i(47,43)),"塔の攻略前は山道が閉じている")
	if not castle_check(await _walk(_outside(_definition["tower_entrance"])),"塔の入口へ通常歩行"):return
	await picture("01-world-tower")
	if not castle_check(await _walk(_world_point(_definition["tower_entrance"]["cell"]),_definition["tower_spawn"]),"森の塔へ入場"):return
	await picture("02-floor-1")
	for floor_index in range(3):
		if not castle_check(await _walk(tower_point(floor_index,[7,10])),"宝箱の前へ"):return
		var before := int(_state()["inventory"]["potion"])
		if not castle_check(await _step_direction(Vector2i.UP),"宝箱の位置で歩行を完了"):return
		await _key(KEY_ENTER);await _settle()
		castle_check(_state()["inventory"]["potion"]==before+2,"各階の宝箱を取得")
		await _key(KEY_ENTER);await _settle()
		castle_check(_state()["inventory"]["potion"]==before+2,"宝箱の二重取得なし")
		if floor_index==1:
			await picture("03-floor-2")
			if not castle_check(await _walk(tower_point(1,[14,8])),"東階段の崩れ跡へ"):return
			await _key(KEY_RIGHT);await _key(KEY_ENTER);await _settle()
		if floor_index<2:
			if not castle_check(await _transition(_definition["tower_doors"][floor_index*2]),"階段で上階へ"):return
	await picture("04-floor-3")
	roundtrip("加入前")
	# ボス前は会話をしても加入できない。
	if not castle_check(await _walk(tower_point(2,[12,5])),"スイナの横へ"):return
	await _key(KEY_LEFT);await _key(KEY_ENTER);await _settle()
	castle_check(_state()["party"].size()==3,"ボス前は3人のまま")
	if not castle_check(await _walk(_definition["tower_boss"]["point"]),"最上階ボスへ通常接触"):return
	if not castle_check(await _settle(),"最上階ボスに勝利"):return
	castle_check("forest_tower_boss" in _state()["overworld"]["cleared"],"ボス撃破を保存")
	if not castle_check(await _walk(tower_point(2,[11,6])),"スイナの正面へ"):return
	await _key(KEY_UP);await _key(KEY_ENTER)
	await picture("06-suina-conversation")
	castle_check(_state()["party"].size()==3,"会話開始では加入しない")
	await _settle()
	castle_check(_state()["party"].map(func(a:Dictionary)->String:return a["id"])==["pc_01","pc_02","pc_03","pc_04"],"会話終了で4人目が加入")
	castle_check(_state()["progress_flags"].get("mountain_path_open",false),"加入後に山道を解放")
	castle_check(not joining_observations.is_empty() and joining_observations.all(func(v:Dictionary)->bool:return v["party_size"]==3),"同行を申し出る行ではまだ3人")
	roundtrip("加入後")
	await picture("08-four-party-exploration")
	await _key(KEY_ENTER);await _settle()
	castle_check(_state()["party"].size()==4,"再操作で二重加入しない")
	# 通常の歩行遭遇で4人の戦闘画面を撮る。
	for i in range(40):
		if tower_shots.has("09-four-party-battle"):break
		if not castle_check(await _walk(tower_point(2,[12 if i%2==0 else 11,6])),"加入後の通常歩行"):return
	castle_check(tower_shots.has("09-four-party-battle"),"4人の通常遭遇を撮影")
	for floor_index in [2,1]:
		if not castle_check(await _transition(_definition["tower_doors"][(floor_index-1)*2+1]),"帰路の下り階段"):return
	if not castle_check(await _walk(_definition["tower_exit"],_outside(_definition["tower_entrance"])),"塔から通常退出"):return
	castle_check(_outward(_definition["tower_entrance"]),"塔の出口の一歩手前・外向き")
	if not castle_check(await _walk(_world_point([50,41])),"解放された山道を通常歩行"):return
	await picture("10-mountain-path")
	roundtrip("山道")
