extends SceneTree
## 素材確認用のマスター済み入力。本編での魔物化解放や到達を証明する検査ではない。
const OUTPUT := "res://docs/verification/sprint4-kaina/runtime/"
const FORMS := ["slime","beast","undead","plant","shell","spirit","dragon","bird"]
const BACKGROUNDS := ["plains","cave","underworld"]
const Fixture := preload("res://tools/mastery_action_fixture.gd")
var failures: Array[String]=[]
var checks := 0
var captures: Array[String]=[]
var native := false

func check(ok: bool, reason: String) -> void:
	checks+=1
	if not ok:failures.append(reason)

func _initialize() -> void:
	native="--capture" in OS.get_cmdline_user_args()
	if native and DisplayServer.get_name()=="headless":printerr("KAINA_CAPTURE_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.size=Vector2i(1024,576)
	call_deferred("run")

func game_for(form: String) -> GameSession:
	var game := GameSession.new();check(game.new_game(4),"4人の撮影用初期状態")
	var state := game.export_state()
	var actor: Dictionary=state["party"][0]
	actor["jp"][form]=int(game.jobs[form]["mastery_cost"])
	actor["mastered_jobs"].append(form)
	state=Fixture.complete_state(state,game.jobs)
	# マスター済みの素材確認入力に能力値を合わせる。回数や到達の実測とは区別する。
	var stats := game._compute_stats(actor,true)
	actor["hp"]=stats["hp"];actor["max_hp"]=stats["hp"]
	actor["mp"]=stats["mp"];actor["max_mp"]=stats["mp"]
	check(game.import_state(state),"マスター済み素材確認入力: "+form)
	check(game.change_job("pc_01",form),"共通APIで魔物職を適用: "+form)
	check(game.export_state()["party"][0]["monster_form"]==form,"魔物化の姿を適用: "+form)
	return game

func capture(game: GameSession, form: String, background: String) -> void:
	if not native:return
	var panel := FirstRegionScreen.new();panel.game=game;panel.screen_mode="battle";panel.actor="pc_01";panel.battle_background=background
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font()
	root.add_child(panel)
	await create_timer(0.15).timeout;await process_frame;await process_frame;await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := root.get_texture().get_image()
	var name := form+"-"+background+".png"
	check(not image.is_empty() and image.save_png(OUTPUT+name)==OK,"本番描画保存: "+name)
	captures.append(name)
	panel.queue_free();await process_frame

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	for form in FORMS:
		var game := game_for(form)
		var actor: Dictionary=game.export_state()["party"][0]
		for pose in range(3):
			var visual := CharacterVisuals.appearance(actor,"battle",pose)
			check(visual["available"] and visual["form"]==form,"戦闘素材参照: "+form)
			check(visual["region"]==Rect2(pose*96,0,96,96),"戦闘96px: "+form)
		for direction in range(4):
			for pose in range(4):
				var visual := CharacterVisuals.appearance(actor,"walk",pose,direction)
				check(visual["available"] and visual["form"]==form,"歩行素材参照: "+form)
				check(visual["region"]==Rect2([0,1,0,2][pose]*32,direction*48,32,48),"歩行32×48・4方向3コマ: "+form)
		var path := "user://kaina_form_%s_%d.json" % [form,OS.get_process_id()]
		check(game.save_game(path),"保存: "+form)
		var loaded := GameSession.new();check(loaded.load_game(path),"復元: "+form)
		check(game.export_state()==loaded.export_state(),"保存復元完全一致: "+form)
		var view := RpgBattleView.new();view.members=loaded.export_state()["party"]
		check(view.actor_rect("pc_01").size==Vector2(72,72),"本番表示72px: "+form)
		view.free()
		check(loaded.start_battle(["slime","shell_guard"],20260929)!=null,"実戦闘の開始: "+form)
		for background in BACKGROUNDS:await capture(loaded,form,background)
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"forms":8,"captures":captures,"native_render":native,"scope":"マスター済みの明示入力による本番描画・素材参照・保存復元。物語の解放や修練回数の実測ではない。","build":BuildIdentity.current()})
	for failure in failures:printerr("KAINA_FORM_FAIL: "+failure)
	print("KAINA_FORM_PASS: forms=8 checks=%d" % checks if failures.is_empty() else "KAINA_FORM_FAIL: "+str(failures.size()))
	quit(0 if failures.is_empty() else 1)
