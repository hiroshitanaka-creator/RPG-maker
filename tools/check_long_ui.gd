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
	for size in [3,4]:
		var visited: Dictionary={19:true}
		for mission in LongCampaign.data().get("missions",[]):
			var chapter_index: int=mission["trigger_step"]
			if visited.has(chapter_index):continue
			visited[chapter_index]=true
			main.start_new_game(size)
			var scene_state: Dictionary=main.game.export_state()
			var entry:=StoryCampaign.step(chapter_index)
			scene_state["progress_flags"].merge({"chapter1_cleared":true,"long_campaign_started":true},true)
			for circuit in CampaignContent.data()["circuits"]:
				if circuit["trigger_step"]==chapter_index:scene_state["progress_flags"]["circuit_"+circuit["id"]+"_cleared"]=true
			scene_state["world"]={"location":entry["location"],"player_cell":entry["cell"],"quest_step":chapter_index}
			check(main.game.import_state(scene_state),"後の章の依頼入口も有効な状態である")
			main.mode=main.Mode.FIELD;main._refresh()
			check(main.submit_player_action({"kind":"interact"}) and main.mode==main.Mode.JOURNEYS,"後の章でも通常操作で依頼一覧へ入る")
			await _layout(main,"journey_board_at_%d_%d" % [chapter_index,size])
			check(main.submit_player_action({"kind":"begin_journey","id":mission["id"]}),"対象章の依頼を選んで現地へ入れる")
			await _layout(main,"journey_entry_at_%d_%d" % [chapter_index,size])
		for clue in LongCampaign.data().get("clues",[]):
			for after in [false,true]:
				main.start_new_game(size)
				var state:=_journal_fixture(main.game.export_state(),clue["payoff"],after)
				check(main.game.import_state(state),"手帳の回収直前・直後の有効な検査状態")
				main.mode=main.Mode.FIELD;main._refresh()
				check(main.submit_player_action({"kind":"journal"}),"通常の手帳操作で新しい手掛かりを読める")
				var entries: Array=main.game.journal_entries()
				var found:=false
				for at in range(entries.size()):
					if entries[at]["id"]!=clue["id"]:continue
					found=true;main._journal_index=at
					check(entries[at].has("resolved")==after,"回収を読んだ後だけ手帳に解答が出る")
				check(found,"既に見た設置を手帳から参照できる")
				main._refresh()
				await _layout(main,"journey_journal_%s_%d_%s" % [clue["id"],size,str(after)])
				check(main.submit_player_action({"kind":"back"}) and main.mode==main.Mode.FIELD,"手帳を閉じて探索へ戻れる")
		for mission in LongCampaign.data().get("missions",[]):
			for step in mission["steps"]:
				if not step.get("past",false):continue
				main.start_new_game(size)
				var state:=_journal_fixture(main.game.export_state(),{"mission":mission["id"],"step":step["id"]},false)
				check(main.game.import_state(state),"過去の会話の直前へ有効な状態を置く")
				main.mode=main.Mode.FIELD;main._refresh()
				check(main.submit_player_action({"kind":"interact"}),"過去の会話を通常操作で開く")
				var generic_heading:=false
				for child in main._body.get_children():
					if child is Label and child.text=="過去の記録":generic_heading=true
				check(generic_heading,"過去の時期を、本文にない特定の災害へ固定しない")
				await _layout(main,"journey_past_%s_%d" % [mission["id"],size])
	main.queue_free()
	await process_frame
	LongCampaign._source["enabled"]=was_enabled
	failures.append_array(diagnostics.messages())
	OS.remove_logger(diagnostics)
	PlaySessionMetrics.write_json("res://docs/verification/long-ui.json",{"status":"PASS" if failures.is_empty() else "FAIL","cases":cases,"failures":failures,"scope":"制作済み部分を有効にした入力によるUI接続・手帳既読境界の検査。全80話の完成とは区別する。","build":BuildIdentity.current()})
	for message in failures:printerr("LONG_UI_FAIL: "+message)
	if failures.is_empty():print("LONG_UI_PASS: 依頼一覧・移動・両選択・結果・手帳の既読境界を3人/4人で確認")
	quit(0 if failures.is_empty() else 1)

func _journal_fixture(state: Dictionary, reference: Dictionary, after: bool)->Dictionary:
	var mission:=LongCampaign.mission(reference["mission"])
	var base:=StoryCampaign.step(mission["trigger_step"])
	var stage:=0
	for at in range(mission["steps"].size()):
		if mission["steps"][at]["id"]==reference["step"]:stage=at+(1 if after else 0);break
	state["progress_flags"].merge({"chapter1_cleared":true,"long_campaign_started":true,"circuit_waterway_cleared":true},true)
	var solved: Array=[]
	for previous in LongCampaign.data()["missions"]:
		if previous["arc"]!=mission["arc"] or previous["id"]>mission["id"]:continue
		var complete: bool=previous["id"]!=mission["id"]
		if complete:state["progress_flags"][LongCampaign.cleared_flag(previous["id"])]=true
		for at in range(previous["steps"].size()):
			var task: Dictionary=previous["steps"][at]
			if not task.get("choice",false) or (not complete and at>=stage):continue
			state["progress_flags"][LongCampaign.choice_flag(task["id"],0)]=true
			for flag in task["choice_effects"][0].get("flags",[]):state["progress_flags"][flag]=true
			if not complete:solved.append(task["id"])
	var current: Dictionary=mission["steps"][stage]
	state["world"]={"location":current["location"],"player_cell":current["cell"],"section":current["section"],"quest_step":mission["trigger_step"]}
	state["expedition"]={"id":mission["id"],"stage":stage,"wave":0,"solved":solved,
		"origin":{"location":base["location"],"player_cell":base["cell"],"quest_step":mission["trigger_step"]}}
	return state
