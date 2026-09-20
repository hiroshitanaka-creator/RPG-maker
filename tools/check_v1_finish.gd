extends SceneTree

var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)

func _run() -> void:
	var game := GameSession.new()
	check(game.has_method("enable_recording"),"進行とは独立した試遊保存が必要")
	check(FileAccess.file_exists("res://scripts/game/build_identity.gd"),"実行版全体の指紋が必要")
	if failures.is_empty():
		await _recording()
		await _battle_layout()
		_signs_and_traits()
		await _player_jobs()
		await _capture_signs()
	var result := {"failures":failures,"build":BuildIdentity.current(),"human_playtest":"NOT_RUN"}
	check(PlaySessionMetrics.write_json("res://docs/verification/nonhuman-v1-checks.json",result),"追加検査の結果を書き込む")
	for message in failures:
		printerr("V1_FINISH_FAIL: "+message)
	if failures.is_empty():
		print("V1_FINISH_PASS: 試遊履歴の独立保存・復帰・版識別・画面領域を確認")
	quit(0 if failures.is_empty() else 1)

func _wait_real(milliseconds: int) -> void:
	var end := Time.get_ticks_msec()+milliseconds
	while Time.get_ticks_msec() < end:
		await process_frame

func _recording() -> void:
	var directory := "user://qa_recording_"+str(Time.get_ticks_usec())
	var game := GameSession.new()
	check(game.enable_recording(directory) and game.new_game(4),"独立した記録を有効にする")
	game.play_metrics.set_source("automated")
	var identifier := game.playthrough_id()
	check(PlaythroughArchive.valid_id(identifier),"一試行に固有IDを付ける")
	game.play_metrics.update_clock("field",1,true)
	await _wait_real(40)
	game.play_metrics.update_clock("field",1,true)
	var progress := game.export_state()
	check(game.save_game("user://qa_v1_trial_save.json"),"進行と試行IDを保存する")
	var saved_time := game.play_metrics.elapsed_ms
	await _wait_real(70)
	game.play_metrics.update_clock("field",1,true)
	game.play_metrics.record_event("test_attempt",{"synthetic":true})
	game.play_metrics.mark("test_attempts")
	var elapsed: int = game.playtest_document()["elapsed_ms"]
	check(game.load_game("user://qa_v1_trial_save.json"),"同じ試行の前の進行を読む")
	var report := game.playtest_document()
	check(game.export_state() == progress and game.play_metrics.elapsed_ms == saved_time,"進行スナップショットは保存時点へ戻る")
	check(report["elapsed_ms"] == elapsed and report["counters"].get("test_attempts") == 1,"試行全体の時間・失敗履歴は戻さない")
	check(game.playthrough_id() == identifier and report["history_complete"],"同じ試行IDの連続性を保持する")
	check(game.save_playtest_report("user://qa_v1_whole_report.json"),"全試行と進行スナップショットを出力する")
	check(not report["human_review_received"] and not report["target_duration_observed"],"自動操作を人間の完走とはしない")
	var restarted := GameSession.new()
	check(game.close_recording(),"通常終了の境界を記録する")
	restarted.enable_recording(directory)
	check(restarted.load_game("user://qa_v1_trial_save.json"),"別インスタンスで進行を再開する")
	check(restarted.playtest_document()["elapsed_ms"] == elapsed and restarted.playtest_document()["counters"].get("test_attempts") == 1,"再起動相当でも過去の試行時間を失わない")
	check(restarted.playtest_document()["history_complete"],"正常終了した試行は完全性を保つ")
	check(restarted.new_game(3) and restarted.playthrough_id() != identifier,"新規開始は別IDにする")
	var archived: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join(identifier+".json")))
	check(archived["elapsed_ms"] == elapsed and archived["counters"].get("test_attempts") == 1,"新規開始で前の記録を消さない")
	var missing := GameSession.new()
	missing.enable_recording(directory+"_missing")
	check(missing.load_game("user://qa_v1_trial_save.json"),"履歴が別環境に無くても進行はロードできる")
	check(not missing.playtest_document()["history_complete"],"履歴不明を完全な実測として扱わない")
	archived["builds"] = ["0".repeat(64)]
	check(PlaySessionMetrics.write_json(directory.path_join(identifier+".json"),archived),"異なる版からの継続を模擬する")
	var changed := GameSession.new()
	changed.enable_recording(directory)
	check(changed.load_game("user://qa_v1_trial_save.json"),"異なる版でも進行の互換性を保つ")
	check(changed.playtest_document()["game"]["mixed_builds"],"複数版の混在を隠さない")
	var invalid := PlaySessionMetrics.new()
	invalid.set_source("automated")
	var blocked_path := directory+"_blocked"
	check(PlaySessionMetrics.write_json(blocked_path,{}),"書込不能な親を検査用ファイルで作る")
	var blocked := GameSession.new()
	blocked.enable_recording(blocked_path)
	check(blocked.new_game(4),"履歴書込失敗でゲーム進行を捨てない")
	check(not blocked.recording_issue().is_empty() and not blocked.playtest_document()["history_complete"],"履歴の保存失敗を明示する")
	var ended := PlaySessionMetrics.new()
	var archive := PlaythroughArchive.new(directory+"_ended")
	archive.start(ended)
	ended.update_clock("field",6,true)
	await _wait_real(40)
	ended.update_clock("field",6,true)
	ended.completed = true
	archive.flush(ended,{"content_revision":1,"circuits_completed":["waterway","cave","school","records","gate"]})
	var ended_at := archive.lifetime.elapsed_ms
	ended.completed = false
	await _wait_real(40)
	ended.update_clock("field",6,true)
	check(archive.lifetime.elapsed_ms == ended_at,"初回の結末後に前の保存を読んでも、1周目の尺を水増ししない")

func _battle_layout() -> void:
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	if "--expanded-font" in OS.get_cmdline_user_args():
		var expanded := FontVariation.new()
		expanded.base_font = main.theme.default_font
		expanded.spacing_top = 2
		expanded.spacing_bottom = 2
		main.theme.default_font = expanded
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	var fixture: Dictionary = main.game.export_state()
	fixture["progress_flags"]["midgame_slots"] = true
	fixture["party"][0]["learned_abilities"] = ["fire","ice","heal"]
	fixture["party"][0]["equipped_abilities"] = ["fire","ice","heal"]
	check(main.game.import_state(fixture),"画面検査の有効な装着状態を用意する")
	check(main.game.start_battle(["mire_slime","frost_slime","balm_slime"],7) != null,"画面検査の戦闘を開始する")
	main.mode = main.Mode.BATTLE
	main._actor = "pc_01"
	main._notice = ""
	main._battle_log.assign(["相手の特徴と残りHPを見て、行動を選ぼう。"])
	main._choose_target("ability","fire")
	await _assert_layout(main)
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	for actor in main.game.export_state()["party"]:
		main.game.change_job(actor["id"],"slime")
	fixture = main.game.export_state()
	for actor in fixture["party"]:
		actor["jp"]["slime"] = int(main.game.jobs["slime"]["mastery_cost"])-1
	check(main.game.import_state(fixture),"4人の魔物化直前の有効状態")
	var training: BattleState = main.game.start_battle(["slime"],23)
	for turn in range(30):
		if training.phase != BattleState.Phase.INPUT:break
		for actor in training.pending():
			training.queue_action(BattleAction.strike(actor.id,training.living(Combatant.Team.ENEMY)[0].id))
		training.resolve_round()
	check(training.phase == BattleState.Phase.VICTORY and main.game.finish_battle(),"4人を実戦闘で魔物化する")
	fixture = main.game.export_state()
	fixture["progress_flags"]["midgame_slots"] = true
	for actor in fixture["party"]:
		actor["erosion"] = 89
		for ability in ["fire","ice","heal","holy_light"]:
			if ability not in actor["learned_abilities"]:actor["learned_abilities"].append(ability)
		actor["equipped_abilities"] = ["fire","ice","heal","holy_light"]
	check(main.game.import_state(fixture),"最大枠と長い侵蝕見込みの状態")
	var encounter: BattleState = main.game.start_battle(["balm_slime","mending_beast","lamp_wisp"],23)
	check(encounter != null,"敵の回復予定を表示する戦闘を開始")
	encounter.actor_by_id("enemy_01").hp = 1
	main.mode = main.Mode.BATTLE
	main._actor = "pc_01"
	main._notice = ""
	main._battle_log.assign(["対象を選ぶ。敵の番号は各カードのHP欄に表示される。"])
	main._choose_target("ability","fire")
	await _assert_layout(main)
	if "--capture" in OS.get_cmdline_user_args():
		RenderingServer.force_draw(false)
		RenderingServer.force_sync()
		check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/finished_battle_layout.png") == OK,"実画面を保存する")
	main.queue_free()
	await process_frame

func _assert_layout(main: Node) -> void:
	for frame in range(5):
		await process_frame
	for node in main.find_children("*","Control",true,false):
		if node.is_visible_in_tree() and (node is BaseButton or node is Label or node is RichTextLabel):
			check(main.get_viewport_rect().encloses(node.get_global_rect()),"画面に収まる: %s %s %s" % [node.get_class(),str(node.get_global_rect()),str(node.get("text"))])

func _signs_and_traits() -> void:
	var game := GameSession.new()
	game.new_game(4)
	for actor in game.export_state()["party"]:
		var normal: Dictionary = actor.duplicate(true)
		normal["erosion"] = 29
		var changed: Dictionary = actor.duplicate(true)
		changed["erosion"] = 30
		for kind in ["walk","battle"]:
			check(CharacterVisuals.appearance(normal,kind)["path"] != CharacterVisuals.appearance(changed,kind)["path"],"4人の侵蝕29/30で外見を切り替える")
			check(CharacterVisuals.appearance(changed,kind)["available"],"兆候の素材が存在する")
		check(CharacterVisuals.battle_line(normal).is_empty() and not CharacterVisuals.battle_line(changed).is_empty(),"兆候の戦闘台詞を境界で切り替える")
		changed["monster_form"] = "slime"
		check("forms/slime" in CharacterVisuals.appearance(changed,"walk")["path"],"魔物化済みなら専用の姿を優先する")
		changed["monster_form"] = ""
		changed["erosion"] = 0
		check(CharacterVisuals.appearance(changed,"walk")["path"] == CharacterVisuals.appearance(normal,"walk")["path"],"低下後は通常外見へ戻る")
	for job_id in game.jobs:
		check(game.mastery_trait(job_id)["stat_growth"] == game.jobs[job_id]["stat_growth"],"常時特性の説明が実際の成長と一致する")
	check(game.mastery_traits("pc_01").is_empty(),"未マスターの特性を得ない")
	var state := game.export_state()
	state["party"][0]["jp"]["warrior"] = int(game.jobs["warrior"]["mastery_cost"])-1
	check(game.import_state(state),"マスター直前の状態を用意する")
	var battle := game.start_battle(["slime"],23)
	for turn in range(30):
		if battle.phase != BattleState.Phase.INPUT:break
		for actor in battle.pending():
			battle.queue_action(BattleAction.strike(actor.id,battle.living(Combatant.Team.ENEMY)[0].id))
		battle.resolve_round()
	check(battle.phase == BattleState.Phase.VICTORY and game.finish_battle(),"実戦闘で特性を得る")
	check(game.mastery_traits("pc_01").size() == 1,"マスターした職の特性は1件")
	game.change_job("pc_01","mage")
	check(game.mastery_traits("pc_01").size() == 1,"転職後も特性は残る")
	check(game.save_game("user://qa_v1_traits.json"),"特性を支えるマスター状態を保存する")
	var loaded := GameSession.new()
	check(loaded.load_game("user://qa_v1_traits.json") and loaded.mastery_traits("pc_01") == game.mastery_traits("pc_01"),"保存後も特性が一致する")
	var eroded := loaded.export_state()
	eroded["party"][0]["erosion"] = 30
	check(loaded.import_state(eroded),"未魔物化の兆候状態を用意する")
	check(loaded.release_monster_form("pc_01","purification_shrine") and loaded.current_erosion("pc_01") == 0,"未魔物化でも祠で侵蝕を30下げられる")
	var crossing := GameSession.new()
	crossing.new_game(4)
	state = crossing.export_state()
	state["party"][0]["erosion"] = 29
	state["party"][0]["learned_abilities"] = ["acid"]
	state["party"][0]["equipped_abilities"] = ["acid"]
	check(crossing.import_state(state),"侵蝕29と専用技の有効な状態")
	battle = crossing.start_battle(["slime"],23)
	battle.actor_by_id("enemy_01").hp = 1
	for actor in battle.pending():
		battle.queue_action(BattleAction.skill(actor.id,"enemy_01","acid") if actor.id == "pc_01" else BattleAction.guard(actor.id))
	battle.resolve_round()
	check(crossing.finish_battle() and crossing.current_erosion("pc_01") == 30,"専用技の実使用で29から30へ進む")
	check("erosion_signs" in CharacterVisuals.appearance(crossing.export_state()["party"][0],"walk")["path"],"実戦闘後に兆候の外見へ切り替わる")

func _player_jobs() -> void:
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	main.submit_player_action({"kind":"party"})
	for job_id in main.game.job_progression["advanced"]:
		var state: Dictionary = main.game.export_state()
		check(not main.submit_player_action({"kind":"choose_job","actor":"pc_01","job":job_id}),"未解放の上級職を通常操作で選べない")
		check(main.game.export_state() == state,"転職拒否時に状態を変えない")
	check(main.submit_player_action({"kind":"job_lore"}),"通常操作から噂・図鑑を読める")
	if "--capture" in OS.get_cmdline_user_args():
		for frame in range(4):await process_frame
		RenderingServer.force_draw(false)
		RenderingServer.force_sync()
		check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/finished_job_lore.png") == OK,"噂と図鑑の画面を保存する")
	main.submit_player_action({"kind":"back"})
	for job_id in main.game.job_progression["advanced"]:
		main.start_new_game(4)
		main.game.play_metrics.set_source("automated")
		var rule: Dictionary = main.game.job_progression["advanced"][job_id]
		for prerequisite in rule["masters"]:
			check(main.game.change_job("pc_01",prerequisite),"検査用に前提の職を適用する")
			var fixture: Dictionary = main.game.export_state()
			fixture["party"][0]["jp"][prerequisite] = int(main.game.jobs[prerequisite]["mastery_cost"])-1
			check(main.game.import_state(fixture),"前提職マスター直前の状態を用意する")
			main.game.rest()
			var encounter: BattleState = main.game.start_battle(["slime"],23)
			for turn in range(30):
				if encounter.phase != BattleState.Phase.INPUT:break
				for actor in encounter.pending():
					encounter.queue_action(BattleAction.strike(actor.id,encounter.living(Combatant.Team.ENEMY)[0].id))
				encounter.resolve_round()
			check(encounter.phase == BattleState.Phase.VICTORY and main.game.finish_battle(),"前提の職を実戦闘でマスターする")
		if int(rule["erosion"]) > 0:
			var before: Dictionary = main.game.export_state()
			before["party"][0]["erosion"] = 59
			main.game.import_state(before)
			check(not main.game.choose_job("pc_01",job_id),"侵蝕59では魔物上位職を選べない")
			before["party"][0]["erosion"] = 60
			main.game.import_state(before)
		check(main.game.job_unlocked("pc_01",job_id),"二つのマスターと侵蝕条件で解放する")
		main.submit_player_action({"kind":"party"})
		check(main.submit_player_action({"kind":"choose_job","actor":"pc_01","job":job_id}),"解放済みなら通常操作で選べる")
		if job_id == "spirit":
			check(main.game.release_monster_form("pc_01","purification_shrine"),"解放後に侵蝕を下げる")
			check(main.game.current_erosion("pc_01") == 30 and main.game.job_unlocked("pc_01",job_id),"一度解放した職は侵蝕低下で取り上げない")
		check(main.game.save_game("user://qa_v1_job_unlock.json"),"上級職の到達状態を保存する")
		var restored := GameSession.new()
		check(restored.load_game("user://qa_v1_job_unlock.json") and restored.job_unlocked("pc_01",job_id),"ロード後も選べた職を取り上げない")
	main.queue_free()
	await process_frame

func _capture_signs() -> void:
	if "--capture" not in OS.get_cmdline_user_args():return
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	var state: Dictionary = main.game.export_state()
	for actor in state["party"]:actor["erosion"] = 30
	check(main.game.import_state(state),"兆候の画面検査用状態")
	main._resume_current()
	for index in range(4):
		await _wait_real(160)
		main.submit_player_action({"kind":"move","dx":1,"dy":0})
	for frame in range(4):await process_frame
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/finished_erosion_walk.png") == OK,"兆候の4人歩行を保存")
	main.game.set_world("waterway",[7,12],2)
	main._resume_current()
	main.submit_player_action({"kind":"interact"})
	var lines := 0
	for line in main._battle_log:
		if "「" in line:lines+=1
	check(lines == 4,"通常の戦闘開始で4人の兆候台詞を接続する")
	for frame in range(4):await process_frame
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/finished_erosion_battle.png") == OK,"兆候の戦闘と台詞を保存")
	main.queue_free()
	await process_frame
