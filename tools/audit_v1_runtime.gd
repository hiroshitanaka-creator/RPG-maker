extends SceneTree

# 企画監査用の観測。凍結受入テストの代替や、不足項目の合格判定には使わない。
var facts: Dictionary = {}
var errors: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func require(value: bool, message: String) -> void:
	if not value:
		errors.append(message)


func _run() -> void:
	facts["human_report_at_runtime_user_path"] = FileAccess.file_exists("user://playtest-human-latest.json")
	var game := GameSession.new()
	require(game.new_game(4),"監査用のゲームを開始できる")
	var initial := game.export_state()
	var allowed: Array[String] = []
	for identifier in game.jobs:
		require(game.import_state(initial),"転職検査の初期状態を戻せる")
		if game.change_job("pc_01",identifier):
			allowed.append(identifier)
	facts["programmatic_job_application"] = allowed
	var player_allowed: Array[String] = []
	for identifier in game.jobs:
		game.import_state(initial)
		if game.choose_job("pc_01",identifier):player_allowed.append(identifier)
	facts["initial_player_selectable_jobs"] = player_allowed
	require(game.import_state(initial),"侵蝕の比較用状態を戻せる")
	var stages: Dictionary = {}
	for erosion in [0,29,30,59,60,89]:
		var state := initial.duplicate(true)
		state["party"][0]["erosion"] = erosion
		require(game.import_state(state),"侵蝕の比較用状態を設定できる")
		var actor: Dictionary = game.export_state()["party"][0]
		var jobs: Array[String] = []
		for identifier in game.jobs:
			if game.job_unlocked("pc_01",identifier) and game.preview_job("pc_01",identifier)["allowed"]:
				jobs.append(identifier)
		stages[str(erosion)] = {"walk":CharacterVisuals.appearance(actor,"walk")["path"],"battle":CharacterVisuals.appearance(actor,"battle")["path"],"jobs":jobs,"stage":GameSession.erosion_stage(erosion)}
	facts["erosion_without_monster_form"] = stages
	var mastery: Dictionary = {}
	for identifier in ["warrior","thief","priest","beast"]:
		game.new_game(4)
		game.change_job("pc_01",identifier)
		var state := game.export_state()
		state["party"][0]["jp"][identifier] = int(game.jobs[identifier]["mastery_cost"])-1
		require(game.import_state(state),"マスター直前の有効状態を設定できる")
		var before := game.effective_stats("pc_01")
		var battle := game.start_battle(["slime"],7)
		require(_win_with_attacks(battle) and game.finish_battle(),"通常攻撃だけの実戦闘に勝利する")
		var actor: Dictionary = game.export_state()["party"][0]
		mastery[identifier] = {"mastered":identifier in actor["mastered_jobs"],"learned":actor["learned_abilities"],"form":actor["monster_form"],"before":before,"after":game.effective_stats("pc_01"),"actions":"attack_only","jp_fixture":"mastery_cost_minus_one"}
	facts["mastery_without_job_specific_actions"] = mastery
	await _observe_reload_metrics()
	await _observe_ui()
	facts["probe_errors"] = errors
	facts["meaning"] = "観測に成功したことと企画要件を満たしたことは別。人間の試遊は行っていない。"
	var destination := "res://docs/verification/v1-audit-runtime-latest.json"
	var file := FileAccess.open(destination,FileAccess.WRITE)
	if file == null:
		printerr("AUDIT_PROBE_ERROR: 記録を書き込めません")
		quit(1)
		return
	file.store_string(JSON.stringify(facts,"  "))
	file.close()
	for message in errors:
		printerr("AUDIT_PROBE_ERROR: "+message)
	print("AUDIT_PROBE_RECORDED: "+destination+" errors="+str(errors.size()))
	quit(0 if errors.is_empty() else 1)


func _win_with_attacks(battle: BattleState) -> bool:
	if battle == null:
		return false
	for turn in range(30):
		if battle.phase != BattleState.Phase.INPUT:
			break
		for actor in battle.pending():
			battle.queue_action(BattleAction.strike(actor.id,battle.living(Combatant.Team.ENEMY)[0].id))
		battle.resolve_round()
	return battle.phase == BattleState.Phase.VICTORY


func _wait_real(milliseconds: int) -> void:
	var end := Time.get_ticks_msec()+milliseconds
	while Time.get_ticks_msec() < end:
		await process_frame


func _observe_reload_metrics() -> void:
	var game := GameSession.new()
	game.enable_recording("user://qa_audit_trials_"+str(Time.get_ticks_usec()))
	game.new_game(4)
	game.play_metrics.set_source("automated")
	game.play_metrics.update_clock("field",1,true)
	await _wait_real(50)
	game.play_metrics.update_clock("field",1,true)
	require(game.save_game("user://qa_whole_audit_metrics.json"),"監査用セーブを書ける")
	var saved := game.play_metrics.snapshot()
	await _wait_real(70)
	game.play_metrics.update_clock("field",1,true)
	game.play_metrics.record_event("audit_attempt",{"synthetic_observation":true})
	var before := game.play_metrics.snapshot()
	var whole_before := game.playtest_document()
	require(game.load_game("user://qa_whole_audit_metrics.json"),"監査用セーブを読み直せる")
	var after := game.play_metrics.snapshot()
	facts["manual_reload_metrics"] = {"saved_elapsed_ms":saved["elapsed_ms"],"before_reload_elapsed_ms":before["elapsed_ms"],"after_reload_elapsed_ms":after["elapsed_ms"],"events_before":before["events"].size(),"events_after":after["events"].size()}
	facts["whole_trial_reload_metrics"] = {"before":whole_before["elapsed_ms"],"after":game.playtest_document()["elapsed_ms"],"history_complete":game.playtest_document()["history_complete"]}
	game.close_recording()


func _observe_ui() -> void:
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	var built: Dictionary = main.game.export_state()
	built["progress_flags"]["midgame_slots"] = true
	built["party"][0]["learned_abilities"] = ["fire","ice","heal"]
	built["party"][0]["equipped_abilities"] = ["fire","ice","heal"]
	require(main.game.import_state(built),"3枠装着の画面検査用状態を設定できる")
	require(main.game.start_battle(["mire_slime","frost_slime","balm_slime"],7) != null,"3体編成の戦闘を開始できる")
	main.mode = main.Mode.BATTLE
	main._actor = "pc_01"
	main._notice = ""
	main._battle_log.assign(["相手の特徴と残りHPを見て、行動を選ぼう。"])
	main._choose_target("ability","fire")
	await _settle_layout()
	facts["battle_ui"] = _outside_controls(main)
	await _capture(main,"audit_battle_three_enemies")
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	for actor in main.game.export_state()["party"]:
		main.game.change_job(actor["id"],"slime")
	var near: Dictionary = main.game.export_state()
	for actor in near["party"]:
		actor["jp"]["slime"] = int(main.game.jobs["slime"]["mastery_cost"])-1
	require(main.game.import_state(near),"4人の魔物化直前の状態を準備する")
	require(_win_with_attacks(main.game.start_battle(["slime"],7)) and main.game.finish_battle(),"4人を実戦闘で魔物化する")
	built = main.game.export_state()
	built["progress_flags"]["midgame_slots"] = true
	for actor in built["party"]:
		for ability in ["fire","ice","heal","holy_light"]:
			if ability not in actor["learned_abilities"]:
				actor["learned_abilities"].append(ability)
		actor["equipped_abilities"] = ["fire","ice","heal","holy_light"]
	require(main.game.import_state(built),"4枠装着の有効状態を準備する")
	require(main.game.start_battle(["mire_slime","frost_slime","balm_slime"],7) != null,"4枠の検査用戦闘を開始する")
	main.mode = main.Mode.BATTLE
	main._actor = "pc_01"
	main._notice = ""
	main._battle_log.assign(["相手の特徴と残りHPを見て、行動を選ぼう。"])
	main._choose_target("ability","fire")
	await _settle_layout()
	facts["battle_ui_four_slots"] = _outside_controls(main)
	await _capture(main,"audit_battle_four_slots")
	# 新規開始は実行中の戦闘を破棄する既存API。監査用のセーブだけを使う。
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	main.submit_player_action({"kind":"review"})
	await _settle_layout()
	facts["review_ui"] = _outside_controls(main)
	await _capture(main,"audit_review")
	main.queue_free()
	await process_frame


func _settle_layout() -> void:
	for frame in range(5):
		await process_frame


func _outside_controls(main: Control) -> Dictionary:
	var visible := main.get_viewport_rect()
	var outside: Array[Dictionary] = []
	for node in main.find_children("*","Control",true,false):
		if not node.is_visible_in_tree() or not (node is BaseButton or node is Label or node is RichTextLabel or node is TextEdit):
			continue
		var bounds: Rect2 = node.get_global_rect()
		if not visible.encloses(bounds):
			outside.append({"class":node.get_class(),"text":node.text,"x":bounds.position.x,"y":bounds.position.y,"width":bounds.size.x,"height":bounds.size.y})
	return {"viewport":[visible.size.x,visible.size.y],"outside":outside}


func _capture(main: Node, name: String) -> void:
	if "--capture" not in OS.get_cmdline_user_args():
		return
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	require(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/"+name+".png") == OK,"監査画面を保存できる")
