extends SceneTree
## 既存の侵蝕条件は変更せず、戦士で成立する0・30・60の明示入力を本番描画する。
const OUTPUT := "res://docs/verification/erosion-pattern-preview/runtime/"
var failures: Array[String]=[]
var captures: Array[String]=[]
var checks := 0
const DIRECTIONS := [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]

func check(ok: bool, reason: String) -> void:
	checks+=1
	if not ok:failures.append(reason)

func _initialize() -> void:
	if DisplayServer.get_name()=="headless":printerr("EROSION_PREVIEW_INVALID: 実描画が必要");quit(2);return
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


func apply_stage(game: GameSession, stage: int) -> void:
	var state := game.export_state();state["party"][0]["erosion"]=stage
	check(game.import_state(state),"戦士の侵蝕入力: "+str(stage))
	var actor: Dictionary=game.export_state()["party"][0]
	check(actor["job_id"]=="warrior" and actor["monster_form"]=="","人間の戦士を維持")
	for kind in ["walk","battle"]:
		var visual := CharacterVisuals.appearance(actor,kind)
		var expected: String = "res://assets/characters/pc_01/jobs/warrior/"+kind+".png" if stage<30 else "res://assets/characters/pc_01/erosion_signs/jobs/warrior/"+str(stage)+"/"+kind+".png"
		check(visual["available"] and visual["path"]==expected,"職業別合成素材: "+kind)

func capture(game: GameSession, stage: int, battle: bool) -> void:
	var panel := FirstRegionScreen.new();panel.game=game;panel.actor="pc_01"
	if battle:panel.screen_mode="battle";panel.battle_background="plains"
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font();root.add_child(panel)
	await create_timer(.15).timeout
	if not battle:panel.map_view.walk_frame=1;panel.map_view.queue_redraw()
	await process_frame;await process_frame;await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var name := ("battle-" if battle else "walk-")+str(stage)+".png"
	check(root.get_texture().get_image().save_png(OUTPUT+name)==OK,"撮影: "+name);captures.append(name)
	panel.queue_free();await process_frame

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	for stage in [0,30,60]:
		var battle := GameSession.new();check(battle.new_game(4),"戦闘用開始");apply_stage(battle,stage)
		var path := "user://erosion_pattern_%d_%d.json" % [stage,OS.get_process_id()]
		check(battle.save_game(path),"保存");var loaded := GameSession.new();check(loaded.load_game(path),"再読込");check(loaded.export_state()==battle.export_state(),"保存復元一致")
		check(loaded.start_battle(["slime","shell_guard"],20260929)!=null,"戦闘開始")
		await capture(loaded,stage,true)
		var village := GameSession.new();check(village.new_first_region(),"村の開始")
		walk_to(village,Vector2i(8,8));walk_to(village,Vector2i(17,14));apply_stage(village,stage)
		village.first_region_face(Vector2i.DOWN);check(not village.move_first_region(Vector2i(17,15)).is_empty(),"村で通常移動")
		await capture(village,stage,false)
	# 90以上で人間職を維持する入力は成立しない。受入条件を変更しない。
	var invalid := GameSession.new();invalid.new_game(4);var state := invalid.export_state()
	state["party"][0]["erosion"]=90;state["party"][0]["irreversible"]=true
	check(not invalid.import_state(state),"90で戦士の入力を拒否する既存条件")
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"captures":captures,"stages":[0,30,60],"irreversible_warrior_rejected":true,"scope":"本番の衣装参照・戦闘・村の描画。侵蝕値は素材確認用の明示入力。90の見本は依頼者へ確認中。","build":BuildIdentity.current()})
	for failure in failures:printerr("EROSION_PREVIEW_FAIL: "+failure)
	print("EROSION_PREVIEW_PASS: checks=%d" % checks if failures.is_empty() else "EROSION_PREVIEW_FAIL")
	quit(0 if failures.is_empty() else 1)
