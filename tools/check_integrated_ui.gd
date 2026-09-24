extends "res://tools/check_preplay_ui.gd"

func _run() -> void:
	native="--native" in OS.get_cmdline_user_args()
	if native and DisplayServer.get_name()=="headless":quit(2);return
	var main: Node=(load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	var state: Dictionary=main.game.export_state()
	state["progress_flags"]["midgame_slots"]=true
	state["party"][0]["learned_abilities"]=["focus_vow","four_strike","twin_grip"]
	state["party"][0]["equipped_abilities"]=["focus_vow","four_strike","twin_grip"]
	# 全20職の特性がある場合も合計と個別内訳をスクロールして確認できる。
	for job_id in main.game.jobs:
		state["party"][0]["mastered_jobs"].append(job_id)
		state["party"][0]["jp"][job_id]=int(main.game.jobs[job_id]["mastery_cost"])
	state["party"][0]["max_hp"]+=48
	check(main.game.import_state(state),"実UI検査用の有効な装着")
	main.mode=main.Mode.PARTY;main._refresh()
	await _layout(main,"integrated_party")
	var total_visible:=false
	for label in main.find_children("*","Label",true,false):
		if label.text=="常時特性の合計: HP +48 / 攻撃 +12 / 防御 +8 / 魔力 +12 / 魔防 +8":
			total_visible=label.is_visible_in_tree()
	check(total_visible,"本番編成画面に全20職の特性合計を表示")
	var selected:=0
	for control in main.find_children("*","OptionButton",true,false):
		if control.item_count>0 and control.get_item_metadata(0)=="practice_blade":
			control.item_selected.emit(2);selected+=1;break
	await process_frame
	check(selected==1 and main.game.export_state()["party"][0]["integrated"]["weapons"][0]=="practice_bow","実際の武器選択シグナルで第1武器を更新")
	for control in main.find_children("*","OptionButton",true,false):
		if control.item_count>0 and control.get_item_text(0).begins_with("専心"):
			control.item_selected.emit(1);break
	await process_frame
	check(main.game.export_state()["party"][0]["integrated"]["focus_binding"]=="four_strike","実際の専心選択で技を結び付ける")
	check(main.submit_player_action({"kind":"mechanics"}),"パーティから覚え書きを開く")
	await _layout(main,"integrated_notebook")
	check(main.submit_player_action({"kind":"back"}),"覚え書きを閉じる")
	var battle: BattleState=main.game.start_battle(["slime"],21)
	battle.effects.configure(main.game.catalog.integration["enemy_rules"][0],{})
	main.mode=main.Mode.BATTLE;main._refresh()
	await _layout(main,"integrated_battle")
	check(main.submit_player_action({"kind":"mechanics"}),"通常戦闘から予測を開く")
	await _layout(main,"integrated_prediction")
	var before: Dictionary=battle.snapshot()
	var rng_before: int=battle._rng.state
	main._refresh();main._refresh()
	check(before==battle.snapshot() and rng_before==battle._rng.state,"予測画面の再表示で実状態を進めない")
	check(main.submit_player_action({"kind":"reserve_tactic"}),"画面の観察を実際の戦闘へ予約")
	check(battle.queued.has("pc_01") and battle.queued["pc_01"].kind==BattleAction.Kind.OBSERVE,"共通観察が予約された")
	for actor in battle.pending():battle.queue_action(BattleAction.guard(actor.id))
	battle.resolve_round()
	check(not battle.effects.knowledge.is_empty(),"観察の実行で知識を獲得")
	main.game.new_game(4)
	main.start_new_game(4)
	main.game.change_job("pc_01","beast")
	state=main.game.export_state();state["party"][0]["jp"]["beast"]=119
	check(main.game.import_state(state),"マスター直前の画面境界入力")
	check(main.game.set_world("waterway",[10,8],3),"任意戦闘の実施場所")
	main.mode=main.Mode.FIELD;main._refresh()
	var stable: Dictionary=main.game.export_state()
	check(main.submit_player_action({"kind":"field_battle"}) and main.mode==main.Mode.EROSION_CONFIRMATION and main.game.current_battle()==null,"勝利で魔物化する前に予告を表示")
	await _layout(main,"integrated_mastery_warning")
	check(main.submit_player_action({"kind":"cancel_erosion"}) and main.game.export_state()==stable,"魔物化予告の取消で状態不変")
	main.submit_player_action({"kind":"field_battle"})
	check(main.submit_player_action({"kind":"confirm_erosion"}) and main.game.current_battle()!=null,"確認後に本番戦闘へ入る")
	main.start_new_game(4)
	state=main.game.export_state();state["format_version"]=1;state.erase("integrated")
	for actor in state["party"]:actor.erase("integrated")
	check(main.game.import_state(state),"旧保存の実UI検査")
	main.mode=main.Mode.PARTY;main._refresh()
	check(main.submit_player_action({"kind":"preview_rule_upgrade"}),"旧保存の更新説明を開く")
	await _layout(main,"integrated_upgrade")
	check(main.submit_player_action({"kind":"back"}) and main.game.export_state()==state,"更新説明から取消で全状態を保持")
	main.submit_player_action({"kind":"preview_rule_upgrade"})
	check(main.submit_player_action({"kind":"confirm_rule_upgrade"}) and main.game.export_state()["format_version"]==2,"明示的な更新操作だけで形式2へ更新")
	if native:
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("res://.tools/integrated-ui-native.png")
	failures.append_array(diagnostics.messages())
	PlaySessionMetrics.write_json("res://docs/verification/integrated-ui-%s.json" % ("native" if native else "headless"),{"status":"PASS" if failures.is_empty() else "FAIL","controls":checked_controls,"screens":cases,"failures":failures,"native":native,"human":"NOT_RUN"})
	for message in failures:printerr("INTEGRATED_UI_FAIL: "+message)
	print("INTEGRATED_UI_RESULT: failures=%d controls=%d native=%s" % [failures.size(),checked_controls,str(native)])
	main.queue_free();await process_frame
	OS.remove_logger(diagnostics)
	quit(0 if failures.is_empty() else 1)

