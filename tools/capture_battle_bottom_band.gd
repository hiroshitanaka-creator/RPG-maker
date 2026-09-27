extends SceneTree
## 目標画像との比較用に、本番画面と共通戦闘処理で見本を撮影する。
const OUTPUT := "res://docs/verification/battle-layout-exact/"
var captured: Array[String] = []

func _initialize() -> void:
	if DisplayServer.get_name()=="headless":printerr("TARGET_CAPTURE_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.size=Vector2i(1024,576)
	call_deferred("run")

func show_panel(game: GameSession, event: Dictionary = {}, target: bool = false, background: String = "ruins") -> FirstRegionScreen:
	var panel := FirstRegionScreen.new()
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font();panel.theme.default_font_size=11
	panel.game=game;panel.screen_mode="battle";panel.actor="pc_01";panel.battle_background=background
	panel.replay=event;panel.replay_members=game.export_state()["party"];panel.replay_enemies=game.current_enemy_ids()
	if target:panel.target_action={"kind":"attack","actor":"pc_01"}
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
		var game := preload("res://tools/battle_five_enemy_preview.gd").new();game.prepare(count)
		var battle := game.current_battle()
		var panel := show_panel(game)
		await capture("01-party-four" if count==4 else "04-party-three")
		panel.queue_free();await process_frame
		if count==3:continue
		panel=show_panel(game,{},true)
		await capture("06-target-details")
		panel.queue_free();await process_frame
		for actor in battle.pending():battle.queue_action(BattleAction.strike(actor.id,"enemy_01"))
		for event in battle.resolve_round():
			if event["code"]!="damage" or event["actor"]!="pc_02":continue
			panel=show_panel(game,event)
			await capture("02-attack")
			panel.queue_free();await process_frame
			break
	# 魔法名は通常の装着・入力・解決で生じたイベントから撮影する。
	var magic_game := GameSession.new();magic_game.new_game(4)
	var jobs := ["warrior","martial_artist","priest","mage"]
	for i in range(4):magic_game.choose_job("pc_%02d" % (i+1),jobs[i])
	for training in range(30):
		if "fire" in magic_game.available_abilities("pc_04"):break
		var practice := magic_game.start_battle(["slime"],20260927+training)
		for turn in range(20):
			if practice.phase!=BattleState.Phase.INPUT:break
			for unit in practice.pending():practice.queue_action(BattleAction.strike(unit.id,practice.living(Combatant.Team.ENEMY)[0].id))
			practice.resolve_round()
		if practice.phase!=BattleState.Phase.VICTORY:printerr("BOTTOM_CAPTURE_FAIL: 通常戦闘の育成に失敗");quit(1);return
		magic_game.finish_battle();magic_game.rest()
	if not magic_game.equip_ability("pc_04","fire"):
		printerr("BOTTOM_CAPTURE_FAIL: 火の魔法を通常APIで装着できない");quit(1);return
	var magic_battle := magic_game.start_battle(["slime","slime","shell_guard"],20260927)
	for unit in magic_battle.pending():
		magic_battle.queue_action(BattleAction.skill(unit.id,"enemy_01","fire") if unit.id=="pc_04" else BattleAction.guard(unit.id))
	for event in magic_battle.resolve_round():
		if event["code"]!="ability" or event["actor"]!="pc_04":continue
		var panel := show_panel(magic_game,event)
		await capture("03-skill-name")
		panel.queue_free();await process_frame
		break
	var five := preload("res://tools/battle_five_enemy_preview.gd").new();five.prepare()
	var five_panel := show_panel(five)
	await capture("05-five-enemies")
	five_panel.queue_free();await process_frame
	var two := GameSession.new();two.new_game(4);two.start_battle(["slime","shell_guard"],20260927)
	var two_panel := show_panel(two)
	await capture("07-two-enemies")
	two_panel.queue_free();await process_frame
	var background_game := GameSession.new();background_game.new_game(4)
	background_game.start_battle(["slime","slime","shell_guard"],20260927)
	for background in RpgBattleView.BACKGROUND_LAYOUT:
		var panel := show_panel(background_game,{},false,background)
		await capture("background-"+background)
		panel.queue_free();await process_frame
	PlaySessionMetrics.write_json(OUTPUT+"capture-record.json",{"files":captured,"build":BuildIdentity.current(),"scope":"共通APIによる本番描画の見本。物語の加入・転職解放を示すものではない"})
	if captured.size()!=21:printerr("BOTTOM_CAPTURE_FAIL: 指定5場面・対象詳細・14背景の記録が不足");quit(1);return
	print("TARGET_CAPTURE_SAVED: files=%d" % captured.size())
	quit()
