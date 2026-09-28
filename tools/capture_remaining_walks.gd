extends SceneTree
## 本番の移動・衣装参照・マップ描画を確認する。物語の転職解放は変更しない。
const OUTPUT := "res://docs/verification/sprint3-walk-eight/runtime/"
const JOBS := ["warrior","martial_artist","priest","mage","thief","hunter","apothecary","bard","knight","sage","swordsman","shaman"]
const DIRECTIONS := [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]
var failures: Array[String]=[]
var checks := 0
var native := false
var captures: Array[String]=[]
var movement_records: Array=[]

func check(ok: bool, reason: String) -> void:
	checks+=1
	if not ok:failures.append(reason)

func _initialize() -> void:
	native="--capture" in OS.get_cmdline_user_args()
	if native and DisplayServer.get_name()=="headless":printerr("WALK_CAPTURE_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.size=Vector2i(1024,576)
	call_deferred("run")

func route(game: GameSession, target: Vector2i) -> Array:
	var start := WorldExpedition.point(game.export_state()["overworld"]["cell"])
	var queue: Array[Vector2i]=[start]
	var previous := {start:start}
	var index := 0
	while index<queue.size():
		var here := queue[index];index+=1
		if here==target:break
		for direction in DIRECTIONS:
			var next: Vector2i=here+direction
			if not previous.has(next) and game.first_region_walkable(next):previous[next]=here;queue.append(next)
	if not previous.has(target):check(false,"歩行経路: "+str(target));return []
	var result: Array=[]
	var cursor := target
	while cursor!=start:result.push_front(cursor);cursor=previous[cursor]
	return result

func walk_to(game: GameSession, target: Vector2i) -> void:
	for cell in route(game,target):
		var before := WorldExpedition.point(game.export_state()["overworld"]["cell"])
		game.first_region_face(cell-before)
		check(not game.move_first_region(cell).is_empty(),"通常移動: "+str(cell))

func recruit(game: GameSession, id: String) -> void:
	for event in FirstRegion.residents_for(game.export_state()):
		if event.get("actor","")!=id:continue
		var destination := FirstRegion.event_cell(game.export_state(),event)
		for direction in DIRECTIONS:
			var neighbor: Vector2i=destination-direction
			if not game.first_region_walkable(neighbor):continue
			walk_to(game,neighbor);game.first_region_face(direction)
			var dialogue := game.interact_first_region()
			check(dialogue.get("join_actor","")==id,"加入会話: "+id)
			if id=="pc_03":
				check(game.help_first_region_bandage("hold_bandage"),"包帯を押さえる")
				check(game.help_first_region_bandage("release_bandage"),"包帯から手を離す")
			check(game.finish_first_region_recruit(id),"加入完了: "+id)
			return
	check(false,"加入対象が見つからない: "+id)

func save_frame(panel: Control, name: String) -> void:
	if not native:return
	await process_frame;await process_frame;await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := root.get_texture().get_image()
	check(not image.is_empty() and image.save_png(OUTPUT+name+".png")==OK,"撮影: "+name)
	captures.append(name+".png")

func capture_walk(game: GameSession, job: String, place: String) -> void:
	var panel := FirstRegionScreen.new();panel.game=game;panel.walk_frame=1
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font()
	root.add_child(panel);await process_frame
	check(panel.map_view!=null,"本番のマップ描画")
	var leader: Dictionary=game.export_state()["party"][0]
	var expected := "res://assets/characters/%s/jobs/%s/walk.png" % [leader["id"],job]
	check(CharacterVisuals.appearance(leader,"walk")["path"]==expected,"マップの職業参照: "+job)
	var first: Image
	for frame in range(4):
		panel.map_view.walk_frame=frame;panel.map_view.queue_redraw()
		if native:
			await process_frame;await RenderingServer.frame_post_draw
			var image := root.get_texture().get_image()
			if frame==0:first=image
			if frame==1:check(image.get_data()!=first.get_data(),"移動コマで実画面が変わる: "+job+"/"+place)
		if frame==1:await save_frame(panel,place+"-"+job)
	panel.queue_free();await process_frame

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	for job in JOBS:
		var game := GameSession.new();check(game.new_game(4),"4人編成")
		for actor in game.export_state()["party"]:check(game.change_job(actor["id"],job),"職業適用")
		for actor in game.export_state()["party"]:
			for facing in range(4):
				for frame in range(4):
					var visual := CharacterVisuals.appearance(actor,"walk",frame,facing)
					check(visual["available"] and visual["path"]=="res://assets/characters/%s/jobs/%s/walk.png" % [actor["id"],job],"歩行参照")
					check(visual["region"]==Rect2([0,1,0,2][frame]*32,facing*48,32,48),"4方向と再生順")
		var path := "user://walk_twelve_%s_%d.json" % [job,OS.get_process_id()]
		check(game.save_game(path),"保存")
		var loaded := GameSession.new();check(loaded.load_game(path),"読込")
		check(loaded.export_state()==game.export_state(),"保存復元一致")
		for actor in loaded.export_state()["party"]:check(CharacterVisuals.appearance(actor,"walk")["path"]=="res://assets/characters/%s/jobs/%s/walk.png" % [actor["id"],job],"読込後の歩行衣装")
	var village := GameSession.new();check(village.new_first_region(),"村で開始")
	check(not village.choose_job("pc_01","thief"),"通常の転職解放条件を維持")
	walk_to(village,Vector2i(8,8))
	check(village.export_state()["overworld"]["room"]==1,"家から村へ通常移動")
	recruit(village,"pc_02");recruit(village,"pc_03")
	walk_to(village,Vector2i(17,14))
	for job in JOBS:
		check(village.change_job("pc_01",job),"村で衣装を適用")
		var before: Array=village.export_state()["overworld"]["cell"].duplicate()
		var target := Vector2i(18,14) if before[0]==17 else Vector2i(17,14)
		walk_to(village,target)
		movement_records.append({"place":"village","job":job,"from":before,"to":village.export_state()["overworld"]["cell"]})
		await capture_walk(village,job,"village")
	walk_to(village,Vector2i(17,23))
	check(village.export_state()["overworld"]["layer"]=="world","村から世界マップへ通常移動")
	for job in JOBS:
		check(village.change_job("pc_01",job),"世界マップで衣装を適用")
		var before := WorldExpedition.point(village.export_state()["overworld"]["cell"])
		for direction in [Vector2i.LEFT,Vector2i.RIGHT]:
			if village.first_region_walkable(before+direction):walk_to(village,before+direction);break
		check(WorldExpedition.point(village.export_state()["overworld"]["cell"])!=before,"世界マップで実移動")
		await capture_walk(village,job,"world")
	var battle := GameSession.new();battle.new_game(4);battle.start_battle(["slime","shell_guard"],20260928)
	var panel := FirstRegionScreen.new();panel.game=battle;panel.screen_mode="battle";panel.actor="pc_01";panel.battle_background="plains"
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font();root.add_child(panel)
	await process_frame;await process_frame
	var left_edges: Array=[]
	for button in panel.find_children("*","Button",true,false):
		if button.text in ["攻撃","回復薬","ターン実行","技の効果を確認"]:
			check(button.alignment==HORIZONTAL_ALIGNMENT_LEFT,"コマンド左寄せ: "+button.text)
			left_edges.append(button.global_position.x+button.get_theme_stylebox("normal").content_margin_left)
	check(left_edges.size()==4,"左列の4行を確認")
	for edge in left_edges:check(is_equal_approx(edge,left_edges[0]),"文字描画の左端一致")
	await save_frame(panel,"command-left-aligned")
	panel.queue_free();await process_frame
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"jobs":12,"actors":4,"directions":4,"frames":3,"save_roundtrips":12,"captures":captures,"movements":movement_records,"command_left_edges":left_edges,"failures":failures,"native_render":native,"scope":"職業適用APIによる撮影用衣装。移動・加入・描画は本番処理。物語の転職解放を証明するものではない。","build":BuildIdentity.current()})
	for failure in failures:printerr("WALK_RUNTIME_FAIL: "+failure)
	print("WALK_RUNTIME_PASS: checks=%d jobs=12 actors=4 directions=4 saves=12" % checks if failures.is_empty() else "WALK_RUNTIME_FAIL")
	quit(0 if failures.is_empty() else 1)
