extends SceneTree
## 段階と職業の異なる4人を、本番の戦闘描画で確認する。
const OUTPUT := "res://docs/verification/erosion-costumes/"
const Fixture := preload("res://tools/mastery_action_fixture.gd")
const CASES := [
	{"name":"mixed-1-plains","background":"plains","jobs":["warrior","mage","knight","slime"],"stages":[0,30,60,90]},
	{"name":"mixed-2-cave","background":"cave","jobs":["hunter","priest","bard","shaman"],"stages":[60,0,30,60]},
	{"name":"mixed-3-underworld","background":"underworld","jobs":["slime","swordsman","sage","thief"],"stages":[90,60,30,0]},
]
var failures: Array[String]=[]
var checks := 0
var draft := false

func check(ok: bool, reason: String) -> void:
	checks+=1
	if not ok:failures.append(reason)

func _initialize() -> void:
	draft="--draft" in OS.get_cmdline_user_args()
	if DisplayServer.get_name()=="headless":printerr("MIXED_EROSION_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.size=Vector2i(1024,576)
	call_deferred("run")

func run() -> void:
	if draft:
		# 本番データを書き換えず、確認用プロセス内だけで下書きの参照へ差し替える。
		var source := CharacterVisuals.data().duplicate(true)
		var records: Array=JSON.parse_string(FileAccess.get_file_as_string(OUTPUT+"prepared-records.json"))
		for r in records:
			var signs: Dictionary=source["actors"][r["actor"]]["erosion_signs"]
			if not signs.has("jobs"):signs["jobs"]={}
			if not signs["jobs"].has(r["job"]):signs["jobs"][r["job"]]={}
			var key := str(int(r["stage"]))
			if not signs["jobs"][r["job"]].has(key):signs["jobs"][r["job"]][key]={}
			signs["jobs"][r["job"]][key][r["kind"]]=r["prepared"]["composite"]
		CharacterVisuals._source=source
	for example in CASES:
		var game := GameSession.new();check(game.new_game(4),"4人の見本開始")
		var state := game.export_state()
		for i in range(4):
			var actor: Dictionary=state["party"][i];var job: String=example["jobs"][i];var stage: int=example["stages"][i]
			actor["job_id"]=job;actor["erosion"]=stage
			if stage>=90:
				actor["jp"][job]=int(game.jobs[job]["mastery_cost"]);actor["mastered_jobs"].append(job);actor["monster_form"]=job;actor["irreversible"]=true
				game._learn_form(actor,job)
			else:actor["last_human_job"]=job
		state=Fixture.complete_state(state,game.jobs)
		for actor in state["party"]:
			var stats := game._compute_stats(actor,true);actor["hp"]=stats["hp"];actor["max_hp"]=stats["hp"];actor["mp"]=stats["mp"];actor["max_mp"]=stats["mp"]
		check(game.import_state(state),"職業・段階の混在入力")
		var save_path := "user://erosion_mixed_%s_%d.json" % [example["name"],OS.get_process_id()]
		check(game.save_game(save_path),"保存");var loaded := GameSession.new();check(loaded.load_game(save_path),"復元");check(loaded.export_state()==game.export_state(),"状態完全一致")
		check(loaded.start_battle(["slime","shell_guard"],20260929)!=null,"戦闘開始")
		var panel := FirstRegionScreen.new();panel.game=loaded;panel.actor="pc_01";panel.screen_mode="battle";panel.battle_background=example["background"]
		panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font();root.add_child(panel)
		await create_timer(.15).timeout;await process_frame;await process_frame;await RenderingServer.frame_post_draw
		RenderingServer.force_draw(false);RenderingServer.force_sync()
		for i in range(4):
			var mark := panel.find_child("ErosionStage_pc_%02d" % (i+1),true,false) as ErosionStageMark
			check(mark!=null and mark.stage_name()==GameSession.erosion_stage(int(example["stages"][i])),"段階印の一致")
		var image := root.get_texture().get_image();check(image.get_size()==Vector2i(1024,576),"標準ウィンドウの実寸")
		check(image.save_png(OUTPUT+example["name"]+".png")==OK,"画像保存")
		panel.queue_free();await process_frame
	PlaySessionMetrics.write_json(OUTPUT+"mixed-checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","draft_mode":draft,"checks":checks,"failures":failures,"examples":CASES,"scope":"素材確認用の明示入力による本番戦闘描画・保存復元・段階印。本編での到達を証明するものではない。","build":BuildIdentity.current()})
	for failure in failures:printerr("MIXED_EROSION_FAIL: "+failure)
	print("MIXED_EROSION_PASS: checks=%d draft=%s" % [checks,draft] if failures.is_empty() else "MIXED_EROSION_FAIL")
	quit(0 if failures.is_empty() else 1)
