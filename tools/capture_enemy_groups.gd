extends SceneTree
## 敵1〜4体と対象選択の本番描画。編成は撮影用で、ゲームの出現データは変更しない。
const OUTPUT := "res://docs/verification/enemy-groups-20260928/"
const GROUPS := [["slime"],["slime","shell_guard"],["ember_wisp","slime","shell_guard"],["bat","ember_wisp","slime","shell_guard"]]
var files: Array[String]=[]
var placements: Array=[]

func _initialize() -> void:
	if DisplayServer.get_name()=="headless":printerr("GROUP_CAPTURE_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.size=Vector2i(1024,576);call_deferred("run")

func screen(game: GameSession, target: bool = false) -> FirstRegionScreen:
	var panel := FirstRegionScreen.new();panel.game=game;panel.screen_mode="battle";panel.actor="pc_01"
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font();panel.battle_background="ruins"
	if target:panel.target_action={"kind":"attack","actor":"pc_01"}
	root.add_child(panel);return panel

func save_frame(name: String) -> void:
	await create_timer(0.2).timeout;await process_frame;await process_frame
	await RenderingServer.frame_post_draw;RenderingServer.force_draw(false);RenderingServer.force_sync()
	if root.get_texture().get_image().save_png(OUTPUT+name+".png")!=OK:
		printerr("GROUP_CAPTURE_FAIL: "+name);quit(1);return
	files.append(name)
	for panel in root.get_children():
		if not panel is FirstRegionScreen:continue
		for arena in panel.get_children():
			if not arena is RpgBattleView:continue
			var enemies: Array=[]
			for i in range(arena.enemy_ids.size()):
				var feet: Vector2=arena.enemy_feet(i)
				enemies.append({"id":arena.enemy_ids[i],"feet":[feet.x,feet.y]})
			placements.append({"file":name,"enemies":enemies})

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	for i in range(GROUPS.size()):
		var game := GameSession.new();game.new_game(4);game.start_battle(GROUPS[i],20260928)
		var panel := screen(game)
		await save_frame("0%d-enemies-%d" % [i+1,i+1])
		panel.queue_free();await process_frame
		if i==3:
			panel=screen(game,true);await save_frame("05-target-selection")
			panel.queue_free();await process_frame
	var bosses := GameSession.new();bosses.new_game(4);bosses.start_battle(["flood_beast","flood_beast"],20260928)
	var boss_panel := screen(bosses);await save_frame("06-large-enemies")
	boss_panel.queue_free();await process_frame
	PlaySessionMetrics.write_json(OUTPUT+"capture-record.json",{"files":files,"placements":placements,"build":BuildIdentity.current(),"scope":"共通戦闘処理と本番描画を使った配置見本。出現編成は変更しない。"})
	print("GROUP_CAPTURE_SAVED: files=%d" % files.size());quit()
