extends "res://tools/check_long_ui.gd"

func _run() -> void:
	native = "--native" in OS.get_cmdline_user_args()
	check(not native or DisplayServer.get_name() != "headless","実描画をheadlessで代用しない")
	var main: Node = (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	var driver = preload("res://tools/long_play_driver.gd").new()
	var operations := 0
	for size in [3,4]:
		for mission in LongCampaign.data()["missions"]:
			if native and mission["arc"]!="w_ferry":continue
			var number := int(str(mission["id"]).get_slice("_",2))
			for support_enabled in [false,true]:
				main.start_new_game(size)
				main.game.play_metrics.set_source("automated")
				var activity: Dictionary = mission["activities"][0]
				var task: Dictionary = mission["steps"][activity["unlock_stage"]]
				var state := _journal_fixture(main.game.export_state(),{"mission":mission["id"],"step":task["id"]},false)
				state["party"][0]["learned_abilities"] = ["firm_guard"]
				state["party"][0]["equipped_abilities"] = ["firm_guard"]
				check(main.game.import_state(state),"表示単体検査の有効な途中状態")
				check(driver.walk(main.game,activity["cell"]),"未観察の操作台へ通常移動")
				main.mode = main.Mode.FIELD
				main._refresh()
				check(main.submit_player_action({"kind":"interact"}) and main.mode==main.Mode.JOURNEY_DEVICE,"通常の調査で装置画面を開く")
				var before: Dictionary = main.game.export_state()
				main.submit_player_action({"kind":"long_device_answer","option":activity["answer"]})
				check(main.game.export_state()==before,"画面からも未観察操作は成立しない")
				await _layout(main,"unseen_%d_%d_%s" % [size,number,str(support_enabled)])
				main.submit_player_action({"kind":"back"})
				for observation in activity["observations"]:
					check(driver.walk(main.game,observation["cell"]),"観察へ実移動")
					check(main.submit_player_action({"kind":"interact"}) and main.mode==main.Mode.DIALOGUE,"現地で観察を表示")
					while main.mode==main.Mode.DIALOGUE:main.submit_player_action({"kind":"confirm"})
				check(driver.walk(main.game,activity["cell"]),"観察後に操作台へ戻る")
				main.submit_player_action({"kind":"interact"})
				check(main.submit_player_action({"kind":"party"}) and main.mode==main.Mode.PARTY,"装置から装着画面へ進む")
				check(main.submit_player_action({"kind":"back"}) and main.mode==main.Mode.JOURNEY_DEVICE,"装着画面から装置へ戻る")
				var picker: OptionButton
				for child in main._body.get_children():
					if child is OptionButton:picker=child
				check(picker != null and picker.item_count>=2,"装着とMPを満たす担当者を表示する")
				if picker != null:
					picker.select(1 if support_enabled else 0)
					picker.item_selected.emit(1 if support_enabled else 0)
				before = main.game.export_state()
				main.submit_player_action({"kind":"long_device_answer","option":(activity["answer"]+1)%3})
				check(main.game.export_state()==before,"誤操作の画面入力でMPと進行を失わない")
				await _layout(main,"ready_%d_%d_%s" % [size,number,str(support_enabled)])
				if native and size==4 and support_enabled:
					await RenderingServer.frame_post_draw
					check(main.get_viewport().get_texture().get_image().save_png("res://.tools/long-device-"+str(number)+".png")==OK,"実画面を記録")
				main.submit_player_action({"kind":"long_device_answer","option":activity["answer"]})
				check(main.mode==main.Mode.DIALOGUE,"操作結果を画面で返す")
				var after: Dictionary = main.game.export_state()
				check(after["progress_flags"].get(LongCampaign.activity_flag(activity["id"],"done"),false),"操作完了を保存する")
				check(bool(after["progress_flags"].get(activity["support_flag"],false))==support_enabled,"画面の選択と近道が一致する")
				check(after["party"][0]["mp"]==before["party"][0]["mp"]-(int(main.game.abilities["firm_guard"]["cost"]) if support_enabled else 0),"画面で説明したMPだけを消費する")
				operations += 1
				if not failures.is_empty():break
			if not failures.is_empty():break
		if not failures.is_empty():break
	check(operations==(16 if native else 320),"全対象の画面操作を検査")
	failures.append_array(driver.errors)
	main.queue_free()
	await process_frame
	failures.append_array(diagnostics.messages())
	OS.remove_logger(diagnostics)
	PlaySessionMetrics.write_json("res://docs/verification/long-device-ui-%s.json" % ("native" if native else "headless"),{"status":"PASS" if failures.is_empty() else "FAIL","operations":operations,"layouts":cases.size(),"controls":checked_controls,"failures":failures,"build":BuildIdentity.current(),"human_judgment":"NOT_RUN"})
	for failure in failures:printerr("LONG_DEVICE_UI_FAIL: "+failure)
	if failures.is_empty():print("LONG_DEVICE_UI_PASS: operations=%d layouts=%d" % [operations,cases.size()])
	quit(0 if failures.is_empty() else 1)
