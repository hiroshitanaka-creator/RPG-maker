extends "res://tools/capture_task009_village_regression.gd"
## 007の追加撮影。通常港保存からロードし、キー・画面ボタン・スクロールだけで遊ぶ。
var task_mode := "outside"
var task_source_sha := ""
const SERVICE_POSITION = preload("res://tools/task021_service_position.gd")

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	task_mode="rooms" if "--rooms" in args else "outside"
	OUTPUT="res://docs/verification/task-007/latest/"+task_mode+"/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.min_size=Vector2i(1024,576);root.max_size=Vector2i(1024,576);root.size=Vector2i(1024,576)
	root.position=Vector2i(-32000,-32000)
	var source := "user://task007_port-start.json"
	if not castle_check(FileAccess.file_exists(source),"専用検査が本番save_gameで作った港保存"):finish();return
	task_source_sha=FileAccess.get_sha256(source)
	castle_check(task_source_sha==FileAccess.get_sha256("res://docs/verification/task-007/latest/port-start.json"),"撮影起点の保存全バイト一致")
	var destination := "user://qa_"+OS.get_environment("RPG_QA_SAVE_PREFIX")+"_save.json"
	var file := FileAccess.open(destination,FileAccess.WRITE);file.store_buffer(FileAccess.get_file_as_bytes(source));file.close()
	var scene: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	_main=scene.instantiate();root.add_child(_main);process_frame.connect(_watch);await _frames()
	if not castle_check(await _button(["手動セーブから再開"]) and await _settle(),"タイトルの通常ロード"):finish();return
	FirstRegion.data();_definition=FirstRegion.data().duplicate(true);_sites=FirstRegion._data["sites"].duplicate(true)
	_definition["doors"].append_array(_definition["region2_village_doors"]);_definition["doors"].append_array(_definition["second_port_doors"])
	if not castle_check(await _walk(_definition["second_port_exit"],_world_point([169,99])) and await coast_to_village(),"港を出て沿岸13歩で入村"):finish();return
	await create_timer(2.2).timeout
	if task_mode=="outside":await outdoors()
	else:await facilities()
	finish()

func talk(room: int, id: String) -> bool:
	var position := SERVICE_POSITION.find(_state(),room,id)
	if not castle_check(not position.is_empty(),"住人IDの床・占有・reach・入口到達: "+id):return false
	var cell: Array=position["approach"];var facing: Vector2i=position["facing"]
	if not castle_check(await _walk(point(room,cell)),"住人へ通常歩行: "+id):return false
	var keys := [KEY_DOWN,KEY_LEFT,KEY_RIGHT,KEY_UP]
	if not await _key(keys[DIRECTIONS.find(facing)]):return false
	await _frames(3)
	if not castle_check(await _key(KEY_ENTER) and _snapshot().get("mode")=="dialogue","通常決定キーの会話: "+id):return false
	await picture("talk-"+id)
	return castle_check(await _settle(),"通常決定キーで会話終了: "+id)

func menu_roundtrip(index: int) -> bool:
	var saved := _state()
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["セーブ"]) and await _button(["現在の冒険に戻る"]),"通常メニュー保存: "+str(index)):return false
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["手動セーブから再開"]) and await _settle(),"通常メニュー再読込: "+str(index)):return false
	castle_check(_state()==saved,"通常メニュー全状態復元: "+str(index))
	await picture("saved-room-%d" % index)
	return true

func outdoors() -> void:
	await picture("west-landing")
	if not await menu_roundtrip(0):return
	if not await _walk(point(0,[3,14])):castle_check(false,"西門の下へ");return
	await picture("west-gate-under")
	if not await talk(0,"water_keeper"):return
	if not await talk(0,"child"):return
	if not await _walk(point(0,[38,12])):castle_check(false,"屋根の奥へ");return
	await picture("roof-behind")
	if not await _walk(point(0,[31,6])) or not await _step_direction(Vector2i.UP):castle_check(false,"木の葉の奥へ");return
	await picture("leaves-behind")
	if not await _walk(point(0,[42,14])):castle_check(false,"東門の下へ");return
	await picture("east-gate-under")
	castle_check(await _walk(point(0,[42,13]),_world_point([170,88])),"東門から通常退出")
	await picture("east-world-exit")
	castle_check(await _walk(_world_point([169,88]),point(0,[41,15])),"東から通常再入村")
	castle_check(await _walk(point(0,[3,13]),_world_point([168,88])),"西門から通常退出")
	await picture("west-world-exit")

func facilities() -> void:
	var healthy_before := _state()
	for index in range(1,5):
		if not castle_check(await _walk(point(index,[8,10])),"通常扉から入室: "+str(index)):return
		await create_timer(2.2).timeout;await picture("room-%d-entry" % index)
		if not await talk(index,["innkeeper","date_farmer","camel_keeper","elder"][index-1]):return
		if index==1:
			for actor in _state()["party"]:castle_check(actor["hp"]==actor["max_hp"] and actor["mp"]==actor["max_mp"],"通常会話で全員回復")
			castle_check(_state()["first_region"]["coins"]==healthy_before["first_region"]["coins"],"通常宿泊で料金追加なし")
		if index==4:
			if not await purification():return
		if not await menu_roundtrip(index):return
		if not castle_check(await _walk(point(index,[7,8])),"手前壁の客側へ通常歩行"):return
		await picture("room-%d-front-wall" % index)
		if not castle_check(await _walk(point(index,[8,11]),Region2Village.data()["definition"]["region2_village_doors"][index*2-1]["to"]),"通常出口から対応扉前へ"):return
		await picture("room-%d-return" % index)

func scroll_button(label: String) -> bool:
	for iteration in range(16):
		for button in _main.find_children("*","Button",true,false):
			if button.text!=label or not button.is_visible_in_tree() or button.disabled:continue
			var center: Vector2=button.get_global_rect().get_center()
			var visible: bool=button.get_viewport_rect().has_point(center)
			var parent: Node=button.get_parent()
			while parent!=null:
				if parent is Control and (parent.clip_contents or parent is ScrollContainer) and not parent.get_global_rect().has_point(center):visible=false
				parent=parent.get_parent()
			if visible:
				var clicked := await _button([label])
				# スクロール枠で隠れたボタンへの空クリックを成功扱いしない。
				if label=="町の祠で清める（魔物専用技を全消去）" and str(_main.get("_purify_actor")).is_empty():continue
				return clicked
		var scrolls := _main.find_children("*","ScrollContainer",true,false)
		var target: ScrollContainer
		for scroll in scrolls:
			if scroll.is_visible_in_tree():target=scroll;break
		if target==null:return false
		var center := target.get_global_rect().get_center()
		var motion := InputEventMouseMotion.new();motion.position=center
		_input_log.append("motion:scroll");_main.get_viewport().push_input(motion,true);await _frames()
		var event := InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_WHEEL_DOWN;event.pressed=true;event.position=center
		_input_log.append("wheel:down");_main.get_viewport().push_input(event,true);await _frames(3)
		event=event.duplicate();event.pressed=false;_main.get_viewport().push_input(event,true);await _frames()
	return false

func purification() -> bool:
	var before := _state()
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["じょうたい・そうび・へんせい"]) and await scroll_button("町の祠で清める（魔物専用技を全消去）"),"通常編成の既存祠ボタン"):return false
	await picture("shrine-existing-confirmation")
	if not castle_check(await _button(["やめる"]) and _state()==before,"既存祠の取消で状態不変"):return false
	if not castle_check(await scroll_button("町の祠で清める（魔物専用技を全消去）") and await _button(["専用技を消去して清める"]),"既存確認画面で実行"):return false
	castle_check(_state()["party"][0]["erosion"]==30,"既存祠の通常操作で60から30")
	castle_check(_state()["overworld"]==before["overworld"],"通常祠成功前後のoverworld全体不変")
	return castle_check(await scroll_button("探索へ戻る") and await _settle(),"編成から通常探索へ戻る")

func finish() -> void:
	castle_check(Time.get_ticks_msec()<_deadline and _moves<=LIMIT_MOVES and _input_log.size()<LIMIT_INPUTS and not _input_violation,"既存180秒・600歩・3000入力・300戦闘ターン以内")
	var report := {"status":"PASS" if castle_failures.is_empty() else "FAIL","checks":castle_checks,"failures":castle_failures,"images":castle_images,"shots":shots,"moves":_moves,"inputs":_input_log,"poses":poses,"turns":_turns,"execution_sha":OS.get_environment("TASK007_EXECUTION_SHA"),"source_sha256":task_source_sha,"limits":{"milliseconds":LIMIT_MS,"moves":LIMIT_MOVES,"inputs":LIMIT_INPUTS,"turns":LIMIT_TURNS},"renderer":DisplayServer.get_name(),"method":"人工境界の港保存を通常ロード。以後、方向・決定・メニューキー、画面ボタン、ホイール、既存戦闘入力だけ。瞬間移動・状態注入なし。"}
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",report)
	for failure in castle_failures:printerr("TASK007_CAPTURE_FAIL: "+failure)
	print("TASK007_CAPTURE_PASS: checks=%d images=%d" % [castle_checks,castle_images.size()] if castle_failures.is_empty() else "TASK007_CAPTURE_FAIL")
	_finished=true;quit(0 if castle_failures.is_empty() else 1)
