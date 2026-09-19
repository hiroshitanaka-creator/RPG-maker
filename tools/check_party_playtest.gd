extends SceneTree

var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)


func _run() -> void:
	var game: Variant = GameSession.new()
	game.new_game(4)
	check(game.has_method("set_party_leader"),"4人の先頭切替と歩行表示が未接続")
	check(game.has_method("save_playtest_report"),"実測と評価の保存が未接続")
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	check(main.has_method("presentation_snapshot"),"戦闘コマの再生が未接続")
	if not failures.is_empty():
		main.queue_free()
		await process_frame
		_finish()
		return
	_check_visual_coverage(game)
	await _check_metrics(game)
	await _check_walking_and_battle(main)
	await _check_transform(main)
	main.queue_free()
	await process_frame
	_finish()


func _finish() -> void:
	for message in failures:
		printerr("PARTY_PLAYTEST_FAIL: "+message)
	if failures.is_empty():
		print("PARTY_PLAYTEST_PASS: 4人歩行・先頭保存・32魔物外見・実戦闘の攻撃/被弾・計測/評価/保存を検証")
	quit(0 if failures.is_empty() else 1)


func _check_visual_coverage(game: GameSession) -> void:
	for actor in game.export_state()["party"]:
		var forms: Array = [""]
		for job in game.jobs.values():
			if job["type"] == "monster":
				forms.append(job["id"])
		for form in forms:
			var visual_actor: Dictionary = actor.duplicate(true)
			visual_actor["monster_form"] = form
			for kind in ["walk","battle"]:
				var visual := CharacterVisuals.appearance(visual_actor,kind,2,1)
				check(visual["available"],"外見を参照できる: %s/%s/%s" % [actor["id"],form,kind])
				if visual["available"]:
					check(visual["region"].size == (Vector2(32,48) if kind == "walk" else Vector2(48,48)),"規定の1コマだけを表示する")
				if not form.is_empty() and visual["available"]:
					check(visual["path"] != "res://assets/characters/%s/%s.png" % [actor["id"],kind],"魔物化中に通常画像を完成外見として代用しない")
	check(not CharacterVisuals.appearance({"id":"pc_99","monster_form":""},"walk")["available"],"未定義の人物を既存人物で代用しない")


func _check_metrics(game: GameSession) -> void:
	var before := game.export_state()
	game.play_metrics.set_source("automated")
	game.play_metrics.update_clock("field",1,true)
	await _wait_wall_time(40)
	game.play_metrics.update_clock("field",1,true)
	check(game.play_metrics.active_ms > 0,"実時間の経過を記録する")
	var active := game.play_metrics.active_ms
	await _wait_wall_time(40)
	game.play_metrics.update_clock("menu",1,true)
	check(game.play_metrics.active_ms == active and game.play_metrics.pause_ms > 0,"メニューの時間を操作中の時間へ加算しない")
	check(game.export_state() == before,"時計の参照や計測で進行状態を変更しない")
	check(not game.play_metrics.add_review(3,3,3,"自動操作"),"自動操作を人間の評価として保存できない")
	check(game.save_game("user://qa_metrics_save.json"),"計測付きセーブを保存する")
	var restored := GameSession.new()
	check(restored.load_game("user://qa_metrics_save.json"),"計測付きセーブを読み込む")
	check(restored.play_metrics.snapshot() == game.play_metrics.snapshot() and restored.export_state() == before,"計測と進行の両方が往復で一致する")
	check(game.save_playtest_report("user://qa_metrics_report.json"),"試遊レポートを出力する")
	var report: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("user://qa_metrics_report.json"))
	check(report["source"] == "automated" and not report["target_duration_observed"] and not report["human_review_received"],"自動試験を5〜6時間達成や人間評価に数えない")
	var original := restored.export_state()
	var bad := original.duplicate(true)
	bad["_play_session"] = game.play_metrics.snapshot()
	bad["_play_session"]["chapters"]["1"] = []
	var file := FileAccess.open("user://qa_metrics_invalid.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(bad));file.close()
	check(not restored.load_game("user://qa_metrics_invalid.json") and restored.export_state() == original,"破損した計測で現在の進行を壊さない")
	var survey := PlaySessionMetrics.new()
	survey.set_source("human")
	check(not survey.add_review(0,3,3,"未選択"),"未選択の評価を提出しない")
	check(survey.add_review(2,3,4,"検査用の回答。人間の試遊結果ではない。"),"選択した評価と自由記述を保持する")
	check(survey.answers.size() == 1 and survey.answers[0]["difficulty"] == 4,"評価を別の値へ書き換えない")
	# 保存の検査で作った回答を、人間の試遊記録として残さない。
	survey.set_source("automated")
	var review_game := GameSession.new()
	review_game.new_game(4)
	review_game.play_metrics = survey
	check(review_game.save_game("user://qa_review_roundtrip.json"),"評価回答をセーブする")
	var review_loaded := GameSession.new()
	check(review_loaded.load_game("user://qa_review_roundtrip.json") and review_loaded.play_metrics.answers == survey.answers,"評価回答が保存往復で一致する")
	check(review_loaded.play_metrics.source == "automated" and review_loaded.play_metrics.source_changed,"検査回答を人間の結果へ混ぜない")


func _check_walking_and_battle(main: Node) -> void:
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	for identifier in ["pc_01","pc_02","pc_03","pc_04"]:
		main.submit_player_action({"kind":"party"})
		check(main.submit_player_action({"kind":"set_leader","actor":identifier}),"各人物を先頭にできる")
		main.submit_player_action({"kind":"back"})
		check(main.game.walking_party()[0]["id"] == identifier,"先頭の歩行画像が選択した人物に対応する")
	check(main.game.save_game("user://qa_party_leader.json"),"先頭の選択を保存する")
	var loaded := GameSession.new()
	check(loaded.load_game("user://qa_party_leader.json") and loaded.walking_party()[0]["id"] == "pc_04","ロード後も選んだ先頭が残る")
	for move in range(5):
		await create_timer(0.16).timeout
		check(main.submit_player_action({"kind":"move","dx":1,"dy":0}),"通常の歩行操作で進む")
	check(main._trail.size() == 3,"後続3人へ実際に通ったマスを渡す")
	await _capture(main,"party_walk")
	main.game.set_world("gate",[19,10],12)
	main._resume_current()
	main.submit_player_action({"kind":"interact"})
	var encounter: BattleState = main.game.current_battle()
	for actor in encounter.pending():
		main.submit_player_action({"kind":"attack","actor":actor.id,"target":"enemy_01"})
	check(main.submit_player_action({"kind":"resolve_round"}),"実戦闘を1ターン解決する")
	var attack_seen := false
	var hurt_seen := false
	for frame in range(400):
		var showing: Dictionary = main.presentation_snapshot()
		if not showing["active"]:
			break
		if not attack_seen and 1 in showing["frames"].values():
			attack_seen = true
			await _capture(main,"party_attack")
		if not hurt_seen and 2 in showing["frames"].values():
			hurt_seen = true
			await _capture(main,"party_hurt")
		await process_frame
	check(attack_seen and hurt_seen,"実際の攻撃と被ダメージに対応するコマを再生する")
	main.submit_player_action({"kind":"skip_presentation"})
	main.start_new_game(3)
	main.game.play_metrics.set_source("automated")
	check(main.game.walking_party().size() == 3,"3人編成で4人目を表示しない")
	main.submit_player_action({"kind":"review"})
	await _capture(main,"playtest_review")
	main.submit_player_action({"kind":"back"})


func _check_transform(main: Node) -> void:
	var game := GameSession.new()
	game.new_game(4)
	game.change_job("pc_01","undead")
	for training in range(30):
		var actor: Dictionary = game.export_state()["party"][0]
		if actor["monster_form"] == "undead":
			break
		var battle := game.start_battle(["slime"],51)
		for turn in range(50):
			if battle.phase != BattleState.Phase.INPUT:
				break
			for member in battle.pending():
				battle.queue_action(BattleAction.strike(member.id,"enemy_01"))
			battle.resolve_round()
		check(battle.phase == BattleState.Phase.VICTORY,"育成戦に勝利する")
		game.finish_battle();game.rest()
	var transformed: Dictionary = game.export_state()["party"][0]
	check(transformed["monster_form"] == "undead","実戦闘のJPで不死系をマスターする")
	check(CharacterVisuals.appearance(transformed,"walk")["available"] and CharacterVisuals.appearance(transformed,"battle")["available"],"魔物化後は歩行と戦闘の専用素材へ切り替わる")
	if "--capture" in OS.get_cmdline_user_args():
		main.game.import_state(game.export_state())
		main._resume_current()
		for movement in range(4):
			await _wait_wall_time(160)
			main.submit_player_action({"kind":"move","dx":1,"dy":0})
		await _capture(main,"party_monster_walk")
		main.game.set_world("gate",[19,10],12)
		main._resume_current()
		main.submit_player_action({"kind":"interact"})
		await _capture(main,"party_monster_battle")
	check(game.release_monster_form("pc_01","purification_shrine"),"祠の条件で魔物化を解除する")
	check(CharacterVisuals.appearance(game.export_state()["party"][0],"battle")["path"] == "res://assets/characters/pc_01/battle.png","解除後は元の戦闘シートへ戻る")


func _capture(main: Node, name: String) -> void:
	if not "--capture" in OS.get_cmdline_user_args():
		return
	await process_frame
	await process_frame
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/"+name+".png") == OK,"実画面を保存する")


func _wait_wall_time(milliseconds: int) -> void:
	# 初回フレームのシミュレーション時間と実時計を混同しない。
	var deadline := Time.get_ticks_msec()+milliseconds
	while Time.get_ticks_msec() < deadline:
		await process_frame
