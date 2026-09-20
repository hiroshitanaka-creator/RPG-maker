extends "res://tools/check_preplay_ui.gd"

func _run()->void:
	var was_enabled:=LongCampaign.enabled()
	LongCampaign._source["enabled"]=true
	var main: Node=(load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	var base:=StoryCampaign.step(19)
	for size in [3,4]:
		main.start_new_game(size)
		main.game.play_metrics.set_source("automated")
		var state: Dictionary=main.game.export_state()
		state["progress_flags"].merge({"chapter1_cleared":true,"long_campaign_started":true,"circuit_waterway_cleared":true},true)
		state["world"]={"location":base["location"],"player_cell":base["cell"],"quest_step":19}
		check(main.game.import_state(state),"長編の入口の有効状態")
		main.mode=main.Mode.FIELD;main._refresh()
		check(main.submit_player_action({"kind":"interact"}),"通常の調査操作で依頼一覧へ進む")
		check(main.automation_snapshot()["mode"]=="journeys","依頼一覧の状態を参照できる")
		await _layout(main,"journey_board_"+str(size))
		check(main.game.long_missions().size()>=2,"独立した依頼を複数選べる")
		var before_board: Dictionary=main.game.export_state()
		check(main.submit_player_action({"kind":"back"}) and main.game.export_state()==before_board,"依頼一覧を閉じても進行を変えない")
		check(main.submit_player_action({"kind":"interact"}),"依頼一覧を再度開く")
		check(main.submit_player_action({"kind":"begin_journey","id":"w_ferry_1"}),"一覧から通常操作で冒険を選ぶ")
		check(main.game.world_state().get("section")=="journey_w_ferry_a","最初の区画へ移動する")
		await _layout(main,"journey_field_"+str(size))
		main.start_new_game(size)
		check(main.game.import_state(before_board),"同じ入口へ検査状態を復元")
		main.mode=main.Mode.FIELD;main._refresh()
		check(main.submit_player_action({"kind":"interact"}) and main.submit_player_action({"kind":"begin_journey","id":"w_flute_1"}),"別の依頼も同じ通常操作で選べる")
		check(main.game.world_state().get("section")=="journey_w_flute_a","選んだ依頼の区画へ入る")
		for option in [0,1]:
			main.start_new_game(size)
			state=main.game.export_state()
			state["progress_flags"].merge({"chapter1_cleared":true,"long_campaign_started":true,"circuit_waterway_cleared":true},true)
			var mission:=LongCampaign.mission("w_ferry_1")
			var index:=0
			for at in range(mission["steps"].size()):
				if mission["steps"][at].get("choice",false):index=at;break
			var task: Dictionary=mission["steps"][index]
			state["world"]={"location":task["location"],"player_cell":task["cell"],"section":task["section"],"quest_step":19}
			state["expedition"]={"id":"w_ferry_1","stage":index,"wave":0,"solved":[],"origin":{"location":base["location"],"player_cell":base["cell"],"quest_step":19}}
			check(main.game.import_state(state),"選択画面の有効な途中状態")
			main.mode=main.Mode.FIELD;main._refresh()
			check(main.submit_player_action({"kind":"interact"}),"現地で選択画面を開く")
			check(main.automation_snapshot()["mode"]=="challenge","選択画面の状態を参照できる")
			await _layout(main,"journey_choice_%d_%d" % [size,option])
			check(main.submit_player_action({"kind":"challenge_answer","option":option}),"両方の選択肢を通常操作で確定できる")
			check(main.game.export_state()["progress_flags"].get(LongCampaign.choice_flag(task["id"],option),false),"画面の選択と保存される結果が一致する")
			await _layout(main,"journey_response_%d_%d" % [size,option])
			while main.mode==main.Mode.DIALOGUE:check(main.submit_player_action({"kind":"confirm"}),"会話を閉じる")
			check(main.mode==main.Mode.FIELD,"選択後の探索へ戻る")
	main.queue_free()
	await process_frame
	LongCampaign._source["enabled"]=was_enabled
	failures.append_array(diagnostics.messages())
	OS.remove_logger(diagnostics)
	PlaySessionMetrics.write_json("res://docs/verification/long-ui.json",{"status":"PASS" if failures.is_empty() else "FAIL","cases":cases,"failures":failures,"scope":"制作済みの最初の連作を有効にした入力によるUI接続検査。全80話の完成とは区別する。","build":BuildIdentity.current()})
	for message in failures:printerr("LONG_UI_FAIL: "+message)
	if failures.is_empty():print("LONG_UI_PASS: 依頼一覧・移動・両選択・結果表示を3人/4人で確認")
	quit(0 if failures.is_empty() else 1)
