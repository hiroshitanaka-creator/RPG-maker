extends SceneTree
## 2字体と14背景の本番画面を撮影する。Noto Sans JPは正式採用済み。後続地方には接続しない。
const OUTPUT := "res://docs/verification/battle-fonts/"
const BACKGROUNDS := ["plains","forest","cave","tower","desert","sea","sky","castle","snowfield","volcano","ruins","underworld","temple","final_land"]
var outputs: Array[String] = []

func panel_for(game: GameSession, font: String, background: String, event: Dictionary = {}, target: bool = false) -> FirstRegionScreen:
	var panel := FirstRegionScreen.new()
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font(font);panel.theme.default_font_size=11
	panel.game=game;panel.screen_mode="battle";panel.actor="pc_01";panel.battle_background=background
	panel.replay=event;panel.replay_members=game.export_state()["party"];panel.replay_enemies=game.current_enemy_ids()
	if target:panel.target_action={"kind":"potion","actor":"pc_01"}
	root.add_child(panel)
	return panel

func save_frame(name: String) -> void:
	await create_timer(0.2).timeout
	await process_frame;await process_frame
	await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var path := OUTPUT+name+".png"
	var frame := root.get_texture().get_image()
	if frame.is_empty() or frame.save_png(path)!=OK:
		printerr("FONT_CAPTURE_FAIL: "+path);quit(1);return
	outputs.append(path)

func _initialize() -> void:
	if DisplayServer.get_name()=="headless":printerr("FONT_CAPTURE_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.size=Vector2i(1024,576)
	call_deferred("run")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	var game := GameSession.new()
	game.new_game(4)
	var jobs := ["warrior","martial_artist","priest","mage"]
	for i in range(4):game.choose_job("pc_%02d" % (i+1),jobs[i])
	game.start_battle(["slime"],20260927)
	for font in RpgFonts.PATHS:
		for background in BACKGROUNDS if font=="notosansjp" else ["plains"]:
			var panel := panel_for(game,font,background)
			await save_frame(font+"-"+background)
			panel.queue_free();await process_frame
	var battle := game.current_battle()
	for actor in battle.pending():battle.queue_action(BattleAction.guard(actor.id))
	battle.resolve_round()
	var targets := panel_for(game,"notosansjp","plains",{},true)
	await process_frame;await process_frame
	for member in game.export_state()["party"]:
		for button in targets.find_children("*","Button",true,false):
			if button.text==member["name"]:button.grab_focus()
	await save_frame("plains-target")
	targets.queue_free();await process_frame
	for actor in battle.pending():battle.queue_action(BattleAction.strike(actor.id,"enemy_01"))
	for event in battle.resolve_round():
		if event["code"]!="damage" or not str(event["actor"]).begins_with("pc_"):continue
		var attack := panel_for(game,"notosansjp","plains",event)
		await save_frame("plains-attack")
		attack.queue_free();await process_frame
		break
	PlaySessionMetrics.write_json(OUTPUT+"capture-record.json",{"files":outputs,"background_layout":RpgBattleView.BACKGROUND_LAYOUT,"build":BuildIdentity.current(),"scope":"共通APIで準備した本番描画の見本。Noto Sans JPは依頼者採用済み。後続地方の進行記録ではない"})
	print("FONT_CAPTURE_SAVED: files=%d backgrounds=14 fonts=2" % outputs.size())
	quit()
