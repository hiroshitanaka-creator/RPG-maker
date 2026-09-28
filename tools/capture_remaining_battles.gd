extends SceneTree
## 共通の職業適用処理・保存復元・本番描画で12職を確認する。物語の解放条件は変更しない。
const OUTPUT := "res://docs/verification/sprint3-battle-eight/runtime/"
const JOBS := ["warrior","martial_artist","priest","mage","thief","hunter","apothecary","bard","knight","sage","swordsman","shaman"]
var failures: Array[String]=[]
var captures: Array[String]=[]
var checks := 0
var native := false

func check(ok: bool, reason: String) -> void:
	checks+=1
	if not ok:failures.append(reason)

func _initialize() -> void:
	native="--capture" in OS.get_cmdline_user_args()
	if native and DisplayServer.get_name()=="headless":printerr("TWELVE_JOBS_INVALID: 撮影には実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.size=Vector2i(1024,576)
	call_deferred("run")

func capture(game: GameSession, job: String) -> void:
	if not native:return
	var panel := FirstRegionScreen.new();panel.game=game;panel.screen_mode="battle";panel.actor="pc_01";panel.battle_background="plains"
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font()
	root.add_child(panel)
	await create_timer(0.2).timeout;await process_frame;await process_frame;await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := root.get_texture().get_image()
	check(not image.is_empty() and image.save_png(OUTPUT+job+".png")==OK,"本番画面保存: "+job)
	captures.append(job+".png")
	panel.queue_free();await process_frame

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	for job in JOBS:
		var game := GameSession.new();check(game.new_game(4),"撮影用の4人開始")
		# 上級職も同じ適用処理で確認する。choose_jobの解放判定を変更・偽装しない。
		for member in game.export_state()["party"]:check(game.change_job(member["id"],job),"職業適用: "+member["id"]+"/"+job)
		for member in game.export_state()["party"]:
			for pose in range(3):
				var visual := CharacterVisuals.appearance(member,"battle",pose)
				check(visual["available"] and visual["path"]=="res://assets/characters/%s/jobs/%s/battle.png" % [member["id"],job],"職業と戦闘素材の参照")
				check(visual["region"]==Rect2(pose*96,0,96,96),"96pxの3動作")
		var path := "user://battle_eight_%s_%d.json" % [job,OS.get_process_id()]
		check(game.save_game(path),"保存: "+job)
		var loaded := GameSession.new();check(loaded.load_game(path),"再読込: "+job)
		check(game.export_state()==loaded.export_state(),"保存後の状態完全一致: "+job)
		for member in loaded.export_state()["party"]:check(CharacterVisuals.appearance(member,"battle")["path"]=="res://assets/characters/%s/jobs/%s/battle.png" % [member["id"],job],"再読込後の衣装")
		check(game.start_battle(["slime","shell_guard"],20260928)!=null,"通常戦闘を開始")
		await capture(game,job)
	var first := GameSession.new();first.new_first_region()
	check(not first.choose_job("pc_01","thief"),"最初の地方の転職未解放を維持")
	var locked := GameSession.new();locked.new_game(4)
	check(not locked.choose_job("pc_01","sage") and not locked.choose_job("pc_01","swordsman"),"上級職の解放条件を維持")
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","jobs":12,"actors":4,"poses":3,"save_roundtrips":12,"checks":checks,"failures":failures,"captures":captures,"native_render":native,"scope":"共通の職業適用APIによる本番描画。上級職の物語上の解放を証明するものではない。","build":BuildIdentity.current()})
	for failure in failures:printerr("TWELVE_JOBS_FAIL: "+failure)
	print("TWELVE_JOBS_PASS: jobs=12 actors=4 poses=3 saves=12 checks=%d" % checks if failures.is_empty() else "TWELVE_JOBS_FAIL: "+str(failures.size()))
	quit(0 if failures.is_empty() else 1)
