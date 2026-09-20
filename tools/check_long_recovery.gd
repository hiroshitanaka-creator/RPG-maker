extends "res://tools/check_long_ui.gd"
func _run() -> void:
	var main: Node = (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.save_path = "user://qa_long_recovery_manual_%d.json" % OS.get_process_id()
	main.checkpoint_path = "user://qa_long_recovery_battle_%d.json" % OS.get_process_id()
	var recoveries := 0
	for size in [3,4]:
		for mission in LongCampaign.data()["missions"]:
			main.start_new_game(size)
			main.game.play_metrics.set_source("automated")
			var task: Dictionary = mission["steps"][16]
			check(task["kind"]=="battle","観察・判断後の戦闘を検査")
			var state := _journal_fixture(main.game.export_state(),{"mission":mission["id"],"step":task["id"]},false)
			# 敗北復元だけを検査する局所入力。新規開始の完走には使わない。
			for actor in state["party"]:actor["hp"]=1
			check(main.game.import_state(state),"選択・装置を終えた有効な途中状態")
			check(main.game.save_game(main.save_path),"独立した手動保存を作る")
			var manual_hash := FileAccess.get_sha256(main.save_path)
			var before: Dictionary = main.game.export_state()
			main.mode=main.Mode.FIELD
			main._refresh()
			check(main.submit_player_action({"kind":"interact"}) and main.mode==main.Mode.BATTLE,"現地の通常操作で戦闘開始")
			for turn in range(100):
				if main.mode != main.Mode.BATTLE:break
				var battle: BattleState = main.game.current_battle()
				for actor in battle.pending():check(main.submit_player_action({"kind":"guard","actor":actor.id}),"実コマンドで防御")
				check(main.submit_player_action({"kind":"resolve_round"}),"実ターンで敵の攻撃を受ける")
				main.submit_player_action({"kind":"skip_presentation"})
				await process_frame
			check(main.mode==main.Mode.DEFEAT and main.game.party_defeated(),"実戦闘で全滅し復帰画面へ入る")
			var checkpoint := GameSession.new()
			check(checkpoint.load_game(main.checkpoint_path),"別インスタンスで自動保存を読める")
			check(preload("res://tools/save_state_comparison.gd").differences(before,checkpoint.export_state(),"$",[]).is_empty(),"長編の全状態を戦闘前のまま保持")
			check(main.submit_player_action({"kind":"retry_battle"}),"通常の再挑戦ボタンで戦闘前へ戻る")
			check(main.game.export_state()==before,"選択・装置・通路・報酬・章進行を巻き戻しすぎない")
			check(main.game.play_metrics.counters.get("battles_lost",0)==1 and main.game.play_metrics.counters.get("battle_retries",0)==1,"敗北と再挑戦の履歴を消さない")
			check(main.submit_player_action({"kind":"return_to_town"}) and main.submit_player_action({"kind":"rest"}) and main.submit_player_action({"kind":"resume_exploration"}),"敗北復帰後に帰還・補給・現地再開を実操作")
			check(main.game.world_state()==before["world"] and main.game.export_state()["progress_flags"]==before["progress_flags"],"元の現地と既得フラグに戻る")
			check(FileAccess.get_sha256(main.save_path)==manual_hash,"手動保存を上書きしない")
			recoveries+=1
			if not failures.is_empty():break
		if not failures.is_empty():break
	check(recoveries==160,"全80話を3人と4人で検査")
	main.queue_free()
	await process_frame
	failures.append_array(diagnostics.messages())
	OS.remove_logger(diagnostics)
	PlaySessionMetrics.write_json("res://docs/verification/long-recovery.json",{"status":"PASS" if failures.is_empty() else "FAIL","recoveries":recoveries,"failures":failures,"build":BuildIdentity.current(),"scope":"HP1の途中状態で実戦闘の全滅と本番画面の再挑戦を検査。新規開始の完走とは別。"})
	for failure in failures:printerr("LONG_RECOVERY_FAIL: "+failure)
	if failures.is_empty():print("LONG_RECOVERY_PASS: recoveries=%d" % recoveries)
	quit(0 if failures.is_empty() else 1)
