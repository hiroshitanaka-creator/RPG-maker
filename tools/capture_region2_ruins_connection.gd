extends "res://tools/check_region2_ruins_connection.gd"
## 人工境界から実Godot・Viewport実キーで往復を記録。状態を直接移して撮影を代用しない。
var main: Node
var trace: Array = []
var captures: Array = []

func frames(count: int = 4) -> void:
	for i in range(count):await process_frame

func key_event(code: int, pressed: bool, echo_event: bool = false) -> void:
	var event := InputEventKey.new()
	event.keycode=code;event.physical_keycode=code;event.pressed=pressed;event.echo=echo_event
	trace.append({"msec":Time.get_ticks_msec(),"key":OS.get_keycode_string(code),"pressed":pressed,"echo":echo_event,"before":main.game.overworld_state().duplicate(true),"mode":main.mode})
	root.push_input(event,true)

func step(code: int, repeat_input: bool = false) -> void:
	await create_timer(.17).timeout
	key_event(code,true)
	if repeat_input:
		for i in range(4):
			await process_frame
			key_event(code,true,true)
	key_event(code,false)
	for i in range(120):
		await process_frame
		if not main._world_mover.active():break
	await frames()
	check(main.mode==main.Mode.WORLD,"実方向キーの歩行は通常WORLDへ戻る",code)

func picture(name: String) -> void:
	await frames()
	await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := root.get_texture().get_image()
	check(DisplayServer.get_name()!="headless" and image.get_size()==Vector2i(512,288),"実Godotの512×288画面",name)
	check(image.save_png(OUT+name+".png")==OK,"実画面保存",name)
	captures.append({"file":name+".png","state":main.game.overworld_state().duplicate(true),"input_count":trace.size(),"mode":main.mode})

func checkpoint(label: String) -> void:
	var expected: Dictionary=main.game.export_state()
	main._checkpoint=expected.duplicate(true)
	check(main._persist_checkpoint(),"本番checkpoint永続化",label)
	check(main._load_checkpoint() and main.game.export_state()==expected,"本番checkpointロードで全位置/向き/lock/編成/所持品/職/進行を保持",label)
	await frames()

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	if DisplayServer.get_name()=="headless":printerr("RUINS_CAPTURE_FAIL: 実描画が必要");quit(2);return
	root.min_size=Vector2i(512,288);root.max_size=Vector2i(512,288);root.size=Vector2i(512,288)
	main=(load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main);await frames()
	main.save_path="user://task084-capture-manual.json";main.checkpoint_path="user://task084-capture-checkpoint.json"
	seed(8400)
	var saved := fixture(false)
	check(main.game.import_state(saved),"未完了の人工境界保存を通常APIで準備")
	main.mode=main.Mode.WORLD;main._refresh();await frames()
	await checkpoint("未完了世界")
	await step(KEY_UP,true)
	check(position(main.game,"world",[176,91],3,""),"未完了入口を実キーで通過・内部へ行かない")
	await picture("before-complete")
	await step(KEY_DOWN)
	check(main.game.overworld_state()["cell"]==[176,92],"未完了入口から実キーで戻る")
	# S10会話の完了を本番キーで作る。入口までの長距離移動はこの集中撮影の対象外。
	saved=fixture(false,"interior",[8,10]);saved["overworld"]["node"]="region2_village";saved["overworld"]["room"]=4
	check(main.game.import_state(saved),"S10人工境界を準備")
	main.mode=main.Mode.WORLD;main._resume_region2_shrine();main._refresh();await frames()
	check(main.mode==main.Mode.DIALOGUE,"既存S10開始")
	for page in range(9):
		key_event(KEY_ENTER,true);key_event(KEY_ENTER,false);await frames()
	check(main.mode==main.Mode.WORLD and main.game.export_state()["progress_flags"].get(Region2ShrineStory.COMPLETE_FLAG,false),"実決定キー全9ページで完了")
	saved=main.game.export_state()
	FirstRegion.place(saved["overworld"],{"layer":"world","node":"","room":0,"cell":[176,92]})
	check(main.game.import_state(saved),"完了後の世界入口直前を人工境界として再開")
	main.mode=main.Mode.WORLD;main._refresh();await frames()
	await checkpoint("完了世界")
	await step(KEY_UP,true)
	check(position(main.game,"interior",[18,19],3,"region2_ruins_entrance"),"完了後の実キー入場・連打で二重遷移なし")
	await picture("after-complete-entry")
	main._region_ui_action({"kind":"ui_atlas"});await frames()
	check(main.mode==main.Mode.WORLD_ATLAS,"内部から既存世界地図を表示")
	await picture("interior-atlas")
	main._region_ui_action({"kind":"ui_back"});await frames()
	main._region_ui_action({"kind":"ui_resume"});await frames()
	await checkpoint("内部着地")
	check(main.submit_player_action({"kind":"save"}),"本番手動保存アクション")
	var internal: Dictionary=main.game.export_state()
	await step(KEY_DOWN,true)
	check(position(main.game,"world",[176,92],0,"region2_ruins_entrance"),"実キー出口・入力保持で即再入場なし")
	await picture("interior-return")
	await checkpoint("帰着直後")
	main._region_ui_action({"kind":"ui_title"});main._load_save();await frames()
	check(main.mode==main.Mode.WORLD and main.game.export_state()==internal,"本番タイトル/手動ロードで内部全値復帰・自動退出なし")
	await step(KEY_DOWN,true)
	check(position(main.game,"world",[176,92],0,"region2_ruins_entrance"),"保存復帰後も実キーで帰着")
	await picture("loaded-return")
	await step(KEY_DOWN,true)
	check(main.game.overworld_state()["layer"]=="world" and main.game.overworld_state()["cell"]==[176,93],"帰着後の下入力保持は世界を歩き即再入場しない")
	# 復帰後のAtlasも実際に描画し、世界セル/内部入口はAPI固定期待値で別検証。
	main._region_ui_action({"kind":"ui_atlas"});await frames()
	check(main.mode==main.Mode.WORLD_ATLAS,"帰着後の既存世界地図を表示")
	await picture("returned-atlas")
	var failed := checks.filter(func(c:Dictionary)->bool:return not c["ok"])
	var file := FileAccess.open(OUT+"input-trace.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"fixture":"人工境界保存。本番キー入力と本番保存/復帰。初見プレイではない。","trace":trace,"captures":captures,"driver":DisplayServer.get_name(),"renderer":RenderingServer.get_current_rendering_method()},"\t")+"\n");file.close()
	file=FileAccess.open(OUT+"capture-checks.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"status":"PASS" if failed.is_empty() else "FAIL","checks":checks,"captures":captures},"\t")+"\n");file.close()
	print("RUINS_CAPTURE_%s: checks=%d images=%d failures=%d"%["PASS" if failed.is_empty() else "FAIL",checks.size(),captures.size(),failed.size()])
	main.queue_free();await frames();quit(0 if failed.is_empty() else 1)
