extends SceneTree
## 新しい画面の通常入力を検査する。保護されたR-07の入力・判定は変更しない。
var main: Node
var failures: Array[String] = []
var checks := 0

func _initialize() -> void:
	OS.set_environment("RPG_QA_SAVE_PREFIX","region_screen_"+str(OS.get_process_id()))
	if "--capture" in OS.get_cmdline_user_args():
		if DisplayServer.get_name()=="headless":printerr("REGION_UI_INVALID: 実描画でキャプチャを実行する");quit(2);return
		root.size=Vector2i(1024,576)
	call_deferred("run")

func check(id: String, ok: bool, reason: String) -> void:
	checks+=1
	print("REGION_UI_CHECK: %s %s %s" % [id,"PASS" if ok else "FAIL",reason])
	if not ok:failures.append(id+": "+reason)

func frames() -> void:
	await process_frame
	await process_frame

func key(code: int) -> void:
	var event := InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true
	main.get_viewport().push_input(event,true)
	event=event.duplicate();event.pressed=false;main.get_viewport().push_input(event,true)
	await frames()

func click(label: String) -> bool:
	for button in main.find_children("*","Button",true,false):
		if button.text!=label or not button.is_visible_in_tree() or button.disabled:continue
		if not button.get_viewport_rect().has_point(button.get_global_rect().get_center()):continue
		var event := InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.button_mask=MOUSE_BUTTON_MASK_LEFT;event.position=button.get_global_rect().get_center();event.pressed=true
		main.get_viewport().push_input(event,true)
		event=event.duplicate();event.pressed=false;event.button_mask=0;main.get_viewport().push_input(event,true)
		await frames();return true
	return false

func state() -> Dictionary:return main.game.export_state()
func mode() -> String:return main.automation_snapshot()["mode"]

func fully_visible(control: Control) -> bool:
	if not control.is_visible_in_tree():return false
	var original := control.get_global_rect()
	var visible := original.intersection(control.get_viewport_rect())
	var parent: Node=control.get_parent()
	while parent!=null:
		if parent is Control and parent.clip_contents:visible=visible.intersection(parent.get_global_rect())
		parent=parent.get_parent()
	return original.size.x>0 and original.size.y>0 and visible==original

func capture(name: String) -> void:
	if "--capture" not in OS.get_cmdline_user_args():return
	await create_timer(0.1).timeout
	await RenderingServer.frame_post_draw
	var result := main.get_viewport().get_texture().get_image().save_png("res://docs/verification/first-region/"+name+".png")
	if result!=OK:failures.append("画像保存: "+name)

func run() -> void:
	seed(20260927)
	main=load(str(ProjectSettings.get_setting("application/run/main_scene"))).instantiate()
	root.add_child(main);await frames()
	var started := await click("新しくはじめる")
	check("U01",started and mode()=="world" and state().get("overworld",{}).get("node")=="start_village","通常のニューゲームで村内開始")
	var screen: FirstRegionScreen=main.get("_region_screen")
	check("U02",is_instance_valid(screen) and is_instance_valid(screen.map_view) and screen.map_view.get_global_rect()==main.get_viewport_rect(),"マップが画面全体を占める")
	var visible_buttons: Array[String]=[]
	for button in main.find_children("*","Button",true,false):
		if button.is_visible_in_tree():visible_buttons.append(button.text)
	check("U03",visible_buttons.is_empty(),"探索中の常設ボタン0件。実際: "+str(visible_buttons))
	var before := state()
	await key(KEY_ESCAPE)
	await capture("10-command-window")
	check("U04",mode()=="menu" and await click("どうぐ") and mode()=="items","Escapeから道具の窓へ進める")
	await capture("11-item-window")
	var opened := await click("世界地図を見る")
	check("U05",opened and mode()=="world_atlas" and before==state(),"世界地図の表示で場所・所持品・進行を変更しない")
	await capture("12-world-map-item")
	var closed := await click("地図を閉じる")
	check("U06",closed and mode()=="items" and before==state(),"地図を閉じると元の道具画面へ戻る")
	await key(KEY_ESCAPE)
	var party_open := await click("じょうたい・そうび・へんせい")
	var actor_visible := false
	for selector in main.find_children("*","OptionButton",true,false):
		if selector.selected>=0 and selector.get_item_text(selector.selected)==before["party"][0]["name"] and fully_visible(selector):actor_visible=true
	await capture("13-party-window")
	await key(KEY_ESCAPE)
	check("U09",party_open and actor_visible and mode()=="world" and before==state(),"人物の選択欄が画面に収まり、Escapeで状態を変えず探索へ戻る")
	await key(KEY_ESCAPE)
	var saved := await click("セーブ")
	await click("現在の冒険に戻る")
	await key(KEY_RIGHT)
	await create_timer(0.18).timeout
	var moved: bool = before["overworld"]["cell"]!=state()["overworld"]["cell"]
	await key(KEY_ESCAPE)
	var loaded := await click("手動セーブから再開")
	check("U07",saved and moved and loaded and mode()=="world" and before==state(),"窓から保存し、実移動後のロードで全ゲーム状態が一致")
	var audio: RpgAudio=main.get("_rpg_audio")
	var playback := audio.snapshot()
	check("U08",playback["music"]=="village" and playback["music_players"]==2 and playback["effect_players"]==6 and playback["playing"],"村BGMの再生とBGM/効果音の分離")
	var model := GameSession.new()
	var old_save := before.duplicate(true)
	old_save["overworld"].erase("residents")
	var valid_old := model.import_state(old_save)
	var bad_save := before.duplicate(true)
	bad_save["overworld"]["residents"]="invalid"
	check("U10",valid_old and not model.import_state(bad_save),"住人情報のない旧保存を受け入れ、不正な住人情報を拒否する")
	var record := {"build":BuildIdentity.current(),"checks":checks,"failures":failures,"status":"PASS" if failures.is_empty() else "FAIL","native_render":DisplayServer.get_name()!="headless"}
	var file := FileAccess.open("res://docs/verification/first-region/screen-checks.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(record,"\t")+"\n");file.close()
	main.queue_free();await frames()
	print("REGION_UI_PASS: checks=%d" % checks if failures.is_empty() else "REGION_UI_FAIL: failed=%d/%d" % [failures.size(),checks])
	quit(0 if failures.is_empty() else 1)
