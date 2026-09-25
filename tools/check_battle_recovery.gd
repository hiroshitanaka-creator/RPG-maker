extends SceneTree

var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)


func _run() -> void:
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	check(main.has_method("recovery_available"), "全滅から戦闘前へ戻る入口が存在する")
	if failures.is_empty():
		await _check_recovery(main)
	main.queue_free()
	await process_frame
	for message in failures:
		printerr("RECOVERY_FAIL: " + message)
	if failures.is_empty():
		print("RECOVERY_PASS: 手動保存の保持・戦闘前の復元・全滅計測の保持・3人/4人・連戦・区画・破損保存を検証")
	quit(0 if failures.is_empty() else 1)


func _check_recovery(main: Node) -> void:
	main.save_path = "user://qa_recovery_manual.json"
	main.checkpoint_path = "user://qa_recovery_battle.json"
	for size in [3,4]:
		main.start_new_game(size)
		main.game.play_metrics.set_source("automated")
		# マスター直前の状態から実戦闘のJPで魔物化し、空でない技・外見・侵蝕を往復する。
		check(main.game.change_job("pc_01","slime"),"魔物職へ転職する")
		var learning: Dictionary = main.game.export_state()
		learning["party"][0]["jp"]["slime"] = int(main.game.jobs["slime"]["mastery_cost"])-1
		# 保存・復帰検査の開始条件。修練の成立自体は専用テストで検証する。
		learning["party"][0]["integrated"]["mastery"]["counts"]["slime"] = int(main.game.jobs["slime"]["mastery_action"]["required"])
		check(main.game.import_state(learning),"マスター直前の検査用状態を設定する")
		var training: BattleState = main.game.start_battle(["slime"],7)
		for turn in range(30):
			if training.phase != BattleState.Phase.INPUT:
				break
			for actor in training.pending():
				training.queue_action(BattleAction.strike(actor.id,training.living(Combatant.Team.ENEMY)[0].id))
			training.resolve_round()
		check(training.phase == BattleState.Phase.VICTORY and main.game.finish_battle(),"実JPでマスターへ到達する")
		check(main.game.equip_ability("pc_01","acid"),"魔物の習得技を装着する")
		check(main.game.export_state()["party"][0]["monster_form"] == "slime","魔物化外見を含む状態を保存する")
		check(main.game.rest(),"検査準備でHP・MPを戻す")
		check(main.game.save_game(main.save_path),"手動保存を準備する")
		var manual_hash := FileAccess.get_sha256(main.save_path)
		check(main.game.set_world("waterway",[10,8],3),"任意戦闘を開始できる場所に立つ")
		var fixture: Dictionary = main.game.export_state()
		for member in fixture["party"]:
			member["hp"] = 1
		check(main.game.import_state(fixture),"全滅しやすいHPの検査用状態を設定する")
		var before: Dictionary = main.game.export_state()
		check(main.submit_player_action({"kind":"field_battle"}),"通常操作で任意戦闘を開始する")
		check(main.recovery_available(),"戦闘開始後だけ復帰記録がある")
		var persisted := GameSession.new()
		check(persisted.load_game(main.checkpoint_path) and persisted.export_state() == before,"戦闘前の全状態を自動保存する")
		await _lose(main)
		check(main.game.party_defeated(),"実ターンを解決して全員が戦闘不能になる")
		check(main.game.start_battle(["slime"],1) == null,"全滅したまま次の戦闘を開始しない")
		var failed_metrics: Dictionary = main.game.play_metrics.snapshot()
		check(failed_metrics["counters"].get("battles_lost",0) == 1,"全滅を一度記録する")
		check(persisted.load_game(main.checkpoint_path),"敗北後の自動保存を読み込める")
		var saved_metrics := persisted.play_metrics.snapshot()
		check(saved_metrics["counters"] == failed_metrics["counters"] and saved_metrics["events"] == failed_metrics["events"],"敗北後の回数と戦闘履歴もディスクに残す")
		check(saved_metrics["elapsed_ms"] >= failed_metrics["events"][-1]["elapsed_ms"] and saved_metrics["elapsed_ms"] <= failed_metrics["elapsed_ms"],"敗北が確定した時刻までを保存し、その後の画面待機時間と分ける")
		check(persisted.export_state() == before,"敗北後も自動保存の進行は戦闘前を保持する")
		await _capture(main,"defeat_recovery")
		main._to_menu()
		await _capture(main,"recovery_title")
		main._resume_current()
		check(main.automation_snapshot()["mode"] == "defeat","タイトルを経由して全滅状態の探索へ戻らない")
		check(main.submit_player_action({"kind":"retry_battle"}),"全滅から戦闘前へ戻る")
		check(main.game.export_state() == before,"HP・MP・所持品・職・技・魔物化・全進行が戦闘前と一致する")
		check(main.game.play_metrics.elapsed_ms >= failed_metrics["elapsed_ms"],"やり直しても経過時間が減らない")
		check(main.game.play_metrics.counters.get("battles_lost",0) == 1 and main.game.play_metrics.counters.get("battle_retries",0) == 1,"全滅とやり直しを別々に記録する")
		check(not main.submit_player_action({"kind":"retry_battle"}),"探索中の連打で繰り返し巻き戻さない")
		check(main.submit_player_action({"kind":"return_to_town"}),"復帰後は町へ帰還できる")
		check(main.submit_player_action({"kind":"rest"}),"再挑戦の前に回復できる")
		check(main.submit_player_action({"kind":"resume_exploration"}),"戦闘前の場所へ戻れる")
		check(main.submit_player_action({"kind":"field_battle"}),"準備後に再挑戦できる")
		await _win(main)
		check(main.automation_snapshot()["mode"] == "field","勝利の説明を読んで探索へ戻る")
		check(main.game.play_metrics.counters.get("battles_won",0) == 1,"再挑戦後の勝利を一度記録する")
		check(FileAccess.get_sha256(main.save_path) == manual_hash,"自動保存とやり直しで手動セーブを上書きしない")
	await _check_story_checkpoint(main)
	await _check_file_failures(main)


func _check_story_checkpoint(main: Node) -> void:
	# 連戦途中の既得報酬と、追加区画で解いた課題の両方を検査する。
	for section in [false,true]:
		main.start_new_game(4)
		main.game.play_metrics.set_source("automated")
		check(main.game.set_world("waterway",[17,12],19),"第2章の検査用入口を設定する")
		if section:
			check(main.game.begin_expedition("waterway"),"追加区画へ入る")
			var record: Dictionary = main.game.current_story_step()
			main.game.set_world(record["location"],record["cell"],19,record["section"])
			check(main.game.advance_story_step(),"区画の記録を読む")
		else:
			var ready: Dictionary = main.game.export_state()
			ready["progress_flags"]["circuit_waterway_cleared"] = true
			check(main.game.import_state(ready),"点検を終えた本編連戦の前提を設定する")
		var task: Dictionary = main.game.current_story_step()
		main.game.set_world(task["location"],task["cell"],19,task.get("section",""))
		check(main.submit_player_action({"kind":"interact"}),"本編または区画の戦闘を開始する")
		await _win(main)
		if section:
			task = main.game.current_story_step()
			main.game.set_world(task["location"],task["cell"],19,task["section"])
			check(main.game.answer_challenge(task["answer"]),"区画の課題報酬を得る")
		task = main.game.current_story_step()
		main.game.set_world(task["location"],task["cell"],19,task.get("section",""))
		var weak: Dictionary = main.game.export_state()
		for member in weak["party"]:
			member["hp"] = 1
		check(main.game.import_state(weak),"次戦の敗北を再現するHPにする")
		var before: Dictionary = main.game.export_state()
		check(main.submit_player_action({"kind":"interact"}),"報酬取得後の次の敵へ進む")
		await _lose(main)
		check(main.submit_player_action({"kind":"retry_battle"}),"次戦の開始前へ戻る")
		check(main.game.export_state() == before,"連戦の勝利済み段階・既得JP・正答済み課題・報酬を失わず増やさない")
		var fresh := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
		root.add_child(fresh)
		await process_frame
		fresh.checkpoint_path = main.checkpoint_path
		check(fresh.submit_player_action({"kind":"load_checkpoint"}),"新規起動相当のタイトルから自動保存を読める")
		check(fresh.game.export_state() == before,"再起動相当でも区画・連戦段階を保持する")
		check(fresh.game.play_metrics.counters.get("battles_lost",0) == 1,"再起動相当でも全滅を消さない")
		fresh.queue_free()
		await process_frame


func _check_file_failures(main: Node) -> void:
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	check(not main.submit_player_action({"kind":"field_battle"}) and not main.recovery_available(),"無効な戦闘要求では復帰地点を作らない")
	main.game.set_world("waterway",[10,8],3)
	# 存在しない親ディレクトリへの保存失敗を再現し、通常の保存は触らない。
	main.checkpoint_path = "user://qa_missing_" + str(Time.get_ticks_usec()) + "/checkpoint.json"
	var before: Dictionary = main.game.export_state()
	check(main.submit_player_action({"kind":"field_battle"}),"ディスク保存失敗でも戦闘を開始できる")
	check(not main._checkpoint_error.is_empty() and main.recovery_available(),"失敗を明示し、メモリ上の復帰地点は保持する")
	await _lose(main)
	check(main.submit_player_action({"kind":"retry_battle"}) and main.game.export_state() == before,"保存失敗時も起動中のやり直しはできる")
	main.checkpoint_path = "user://qa_recovery_broken.json"
	var file := FileAccess.open(main.checkpoint_path,FileAccess.WRITE)
	file.store_string("{broken")
	file.close()
	main._to_menu()
	before = main.game.export_state()
	var metrics: Dictionary = main.game.play_metrics.snapshot()
	check(not main.submit_player_action({"kind":"load_checkpoint"}),"破損した自動保存は拒否する")
	check(main.game.export_state() == before and main.game.play_metrics.snapshot() == metrics,"読込失敗で進行と計測を破壊しない")
	var dead := GameSession.new()
	check(dead.import_state(before),"不正な復帰候補の準備")
	var dead_state := dead.export_state()
	for actor in dead_state["party"]:
		actor["hp"] = 0
	check(dead.import_state(dead_state) and dead.save_game(main.checkpoint_path),"全員戦闘不能のセーブ自体は作れる")
	check(not main.submit_player_action({"kind":"load_checkpoint"}) and main.game.export_state() == before,"全員戦闘不能の保存を再挑戦地点として読み込まない")


func _lose(main: Node) -> void:
	for index in range(400):
		if main.automation_snapshot()["mode"] != "battle":
			break
		var encounter: BattleState = main.game.current_battle()
		for actor in encounter.pending():
			check(main.submit_player_action({"kind":"guard","actor":actor.id}),"全滅検査の防御を選ぶ")
		check(main.submit_player_action({"kind":"resolve_round"}),"全滅検査のターンを解決する")
		await process_frame
	main.submit_player_action({"kind":"skip_presentation"})
	check(main.automation_snapshot()["mode"] == "defeat","ターン上限内に実戦闘で全滅する")


func _win(main: Node) -> void:
	for index in range(400):
		var mode_name: String = main.automation_snapshot()["mode"]
		if mode_name == "field":
			return
		if mode_name == "dialogue":
			check(main.submit_player_action({"kind":"confirm"}),"勝利後の説明を確定する")
		elif mode_name == "battle":
			var encounter: BattleState = main.game.current_battle()
			for actor in encounter.pending():
				check(main.submit_player_action({"kind":"attack","actor":actor.id,"target":encounter.living(Combatant.Team.ENEMY)[0].id}),"通常攻撃を選ぶ")
			check(main.submit_player_action({"kind":"resolve_round"}),"勝利検査のターンを解決する")
		else:
			break
		await process_frame
	check(false,"ターン上限内に再挑戦で勝利する")


func _capture(main: Node, name: String) -> void:
	if "--capture" not in OS.get_cmdline_user_args():
		return
	for frame in range(3):
		await process_frame
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/" + name + ".png") == OK,"実画面を保存する")
