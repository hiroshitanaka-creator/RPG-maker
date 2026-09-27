extends SceneTree
## 目標画像との比較用に、本番画面と共通戦闘処理で見本を撮影する。
const OUTPUT := "res://docs/verification/battle-layout-target/"
var captured: Array[String] = []

func _initialize() -> void:
	if DisplayServer.get_name()=="headless":printerr("TARGET_CAPTURE_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.size=Vector2i(1024,576)
	call_deferred("run")

func show_panel(game: GameSession, event: Dictionary = {}, target: bool = false) -> FirstRegionScreen:
	var panel := FirstRegionScreen.new()
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font();panel.theme.default_font_size=11
	panel.game=game;panel.screen_mode="battle";panel.actor="pc_01";panel.battle_background="temple"
	panel.replay=event;panel.replay_members=game.export_state()["party"];panel.replay_enemies=game.current_enemy_ids()
	if target:panel.target_action={"kind":"potion","actor":"pc_01"}
	root.add_child(panel)
	return panel

func capture(name: String) -> void:
	await create_timer(0.2).timeout
	await process_frame;await process_frame
	await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var frame := root.get_texture().get_image()
	if frame.is_empty() or frame.save_png(OUTPUT+name+".png")!=OK:
		printerr("TARGET_CAPTURE_FAIL: "+name);quit(1);return
	captured.append(name)

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	for count in [4,3]:
		var game := GameSession.new();game.new_game(count)
		var jobs := ["warrior","martial_artist","priest","mage"]
		for i in range(count):game.choose_job("pc_%02d" % (i+1),jobs[i])
		var battle := game.start_battle(["slime","shell_guard"],20260927)
		var panel := show_panel(game)
		await capture("01-party-four" if count==4 else "02-party-three")
		panel.queue_free();await process_frame
		if count==3:continue
		for actor in battle.pending():battle.queue_action(BattleAction.guard(actor.id))
		battle.resolve_round()
		panel=show_panel(game,{},true)
		await process_frame;await process_frame
		var commands := panel.find_child("BattleCommands",true,false)
		for member in game.export_state()["party"]:
			for button in commands.find_children("*","Button",true,false):
				if button.text==member["name"]:button.grab_focus()
		await capture("04-target-selection")
		panel.queue_free();await process_frame
		for actor in battle.pending():battle.queue_action(BattleAction.strike(actor.id,"enemy_01"))
		for event in battle.resolve_round():
			if event["code"]!="damage" or not str(event["actor"]).begins_with("pc_"):continue
			panel=show_panel(game,event)
			await capture("03-attack")
			panel.queue_free();await process_frame
			break
	PlaySessionMetrics.write_json(OUTPUT+"capture-record.json",{"files":captured,"build":BuildIdentity.current(),"scope":"共通APIによる本番描画の見本。物語の加入・転職解放を示すものではない"})
	print("TARGET_CAPTURE_SAVED: files=%d" % captured.size())
	quit()
