extends SceneTree

var failures: Array[String] = []
var cases: Array = []
var latency: Dictionary = {}
var objective_count := 0
var checked_controls := 0
var diagnostics := RuntimeDiagnostics.new()
var native := false

func check(value: bool, message: String) -> bool:
	if not value:failures.append(message)
	return value

func _initialize() -> void:
	OS.add_logger(diagnostics)
	call_deferred("_run")

func _run() -> void:
	native = "--native" in OS.get_cmdline_user_args()
	if native and DisplayServer.get_name() == "headless":
		printerr("PREPLAY_UI_ERROR: 実描画検査をheadlessで代用できません")
		quit(2)
		return
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	await _layout(main,"title")
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	await _guidance(main)
	await _screens(main)
	if native:await _timings(main)
	failures.append_array(diagnostics.messages())
	var report := {"kind":"native_preplay_ui" if native else "headless_preplay_ui","status":"PASS" if failures.is_empty() else "FAIL","cases":cases,"objectives":objective_count,"controls_checked":checked_controls,"latency":latency,"failures":failures,"build":BuildIdentity.current(),"runner_sha256":FileAccess.get_sha256("res://tools/check_preplay_ui.gd"),"os":OS.get_name(),"display_server":DisplayServer.get_name(),"video_adapter":RenderingServer.get_video_adapter_name() if native else "NOT_RUN","native_timing":"MEASURED" if native else "NOT_RUN","human_playtest":"NOT_RUN","fixture_scope":"表示検査は有効な進行状態を配置して行う。実時間の全編完走・人間の理解とは区別する。"}
	check(PlaySessionMetrics.write_json("res://docs/verification/preplay-ui-%s.json" % ("native" if native else "headless"),report),"結果を書き出す")
	for message in failures:printerr("PREPLAY_UI_FAIL: "+message)
	print("PREPLAY_UI_RESULT: cases=%d objectives=%d failures=%d native=%s" % [cases.size(),objective_count,failures.size(),str(native)])
	main.queue_free()
	await process_frame
	OS.remove_logger(diagnostics)
	quit(0 if failures.is_empty() else 1)

func _guidance(main: Node) -> void:
	check(main.game.story_audit().is_empty(),"物語の前提と経路が成立する")
	check(CampaignContent.audit(main.game.enemy_definitions).is_empty(),"追加区画の前提と経路が成立する")
	var fixtures: Array = []
	for index in range(StoryCampaign.total_steps()):
		var entry := StoryCampaign.step(index)
		fixtures.append({"label":"base_"+str(index),"entry":entry,"world_step":index})
	var branch_step := -1
	for index in range(StoryCampaign.total_steps()):
		if StoryCampaign.step(index).get("kind") == "choice":branch_step=index
	for branch in StoryCampaign.data()["branches"]:
		for index in range(StoryCampaign.data()["branches"][branch].size()):
			fixtures.append({"label":"branch_%s_%d" % [branch,index],"entry":StoryCampaign.step(branch_step,{"id":branch,"step":index}),"world_step":branch_step,"story_task":{"id":branch,"step":index}})
	for circuit in CampaignContent.data()["circuits"]:
		var solved: Array = []
		var base := StoryCampaign.step(circuit["trigger_step"])
		for index in range(circuit["steps"].size()):
			var entry: Dictionary = circuit["steps"][index]
			fixtures.append({"label":"section_%s_%d" % [circuit["id"],index],"entry":entry,"world_step":circuit["trigger_step"],"expedition":{"id":circuit["id"],"stage":index,"wave":0,"origin":{"location":base["location"],"player_cell":base["cell"],"quest_step":circuit["trigger_step"]},"solved":solved.duplicate()}})
			if entry["kind"] == "challenge":solved.append(entry["id"])
	for fixture in fixtures:
		main.start_new_game(4)
		main.game.play_metrics.set_source("automated")
		var state: Dictionary = main.game.export_state()
		for circuit in CampaignContent.data()["circuits"]:state["progress_flags"]["circuit_"+circuit["id"]+"_cleared"]=true
		var entry: Dictionary = fixture["entry"]
		state["world"] = {"location":entry["location"],"player_cell":entry["cell"],"quest_step":fixture["world_step"]}
		if fixture.has("story_task"):state["story_task"] = fixture["story_task"]
		if fixture.has("expedition"):
			state["expedition"] = fixture["expedition"]
			state["world"]["section"] = entry["section"]
			state["progress_flags"].erase("circuit_"+fixture["expedition"]["id"]+"_cleared")
		if not check(main.game.import_state(state),"案内検査の状態が有効: "+fixture["label"]):continue
		main.mode = main.Mode.FIELD
		main._notice = ""
		main._refresh()
		await process_frame
		await process_frame
		var snapshot: Dictionary = main.automation_snapshot()
		check(snapshot["objective_cell"] == entry["cell"],"目的座標の一致: "+fixture["label"])
		var displayed := false
		var marker := false
		for control in main.find_children("*","Control",true,false):
			if control is Label and str(entry.get("objective","")) in control.text and not str(entry.get("objective","")).is_empty():displayed=true
			if control is WorldView:marker = control.objective == Vector2i(entry["cell"][0],entry["cell"][1])
		check(displayed and marker,"案内文と地図の目印が一致: "+fixture["label"])
		objective_count += 1
		await _layout(main,fixture["label"])

func _screens(main: Node) -> void:
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	var state: Dictionary = main.game.export_state()
	state["party"][0]["learned_abilities"] = ["power_strike","firm_guard"]
	state["party"][0]["erosion"] = 30
	check(main.game.import_state(state),"画面検査の有効な状態")
	for mode_name in ["FIELD","PARTY","JOB_LORE","JOURNAL","REVIEW","VISITS","GATE","DEFEAT","COMPLETE"]:
		main.mode = main.Mode[mode_name]
		main._notice = ""
		main._refresh()
		await _layout(main,"screen_"+mode_name)
	main._show_dialogue(["表示検査用の文章です。これは物語の解答を含まない合成文です。"],false)
	await _layout(main,"dialogue")
	main.mode = main.Mode.PARTY
	main._purify_actor = "pc_01"
	main._refresh()
	await _layout(main,"purify")
	main._purify_actor = ""
	main.mode = main.Mode.REVIEW
	main._notice = "記録の保存結果を確認します。".repeat(6)
	main._refresh()
	await _layout(main,"review_notice")
	main._notice = ""
	for circuit in CampaignContent.data()["circuits"]:
		var solved: Array = []
		var base := StoryCampaign.step(circuit["trigger_step"])
		for index in range(circuit["steps"].size()):
			var task: Dictionary = circuit["steps"][index]
			if task["kind"] != "challenge":continue
			main.start_new_game(4)
			state=main.game.export_state()
			state["world"]={"location":task["location"],"player_cell":task["cell"],"section":task["section"],"quest_step":circuit["trigger_step"]}
			state["expedition"]={"id":circuit["id"],"stage":index,"wave":0,"origin":{"location":base["location"],"player_cell":base["cell"],"quest_step":circuit["trigger_step"]},"solved":solved.duplicate()}
			check(main.game.import_state(state),"課題表示用の有効状態")
			main.mode=main.Mode.CHALLENGE
			main._refresh()
			await _layout(main,"challenge_"+task["id"])
			solved.append(task["id"])
	# 操作候補が多い設備と、4人同時の不可逆確認を表示する。
	main.start_new_game(4)
	state=main.game.export_state()
	for actor in state["party"]:
		actor["learned_abilities"]=["power_strike","firm_guard","acid"]
		actor["equipped_abilities"]=["power_strike","firm_guard"]
	state["world"]={"location":"waterway","player_cell":[10,8],"quest_step":5}
	check(main.game.import_state(state),"設備の全員選択用状態")
	main.mode=main.Mode.EXPLORATION
	main._refresh()
	await _layout(main,"exploration_all_options")
	main.start_new_game(4)
	state=main.game.export_state()
	for actor in state["party"]:
		actor["erosion"]=89
		actor["integrated"]["erosion_fraction"]=9
		actor["learned_abilities"]=["acid"]
		actor["equipped_abilities"]=["acid"]
	check(main.game.import_state(state),"4人同時の確認用状態")
	check(main.game.start_battle(["gate_beast"],47)!=null,"確認用戦闘を開始")
	main.mode=main.Mode.BATTLE
	main._actor="pc_01"
	for actor in main.game.export_state()["party"]:
		check(main.submit_player_action({"kind":"ability","actor":actor["id"],"target":"enemy_01","ability":"acid"}),"不可逆境界の技を予約")
	check(main.submit_player_action({"kind":"resolve_round"}) and main.mode==main.Mode.EROSION_CONFIRMATION,"通常操作で4人の確認画面を表示")
	await _layout(main,"erosion_four")
	var original_font: Font=main.theme.default_font
	var expanded:=FontVariation.new()
	expanded.base_font=original_font
	expanded.spacing_top=2
	expanded.spacing_bottom=2
	main.theme.default_font=expanded
	main._refresh()
	await _layout(main,"erosion_four_expanded")
	main.theme.default_font=original_font
	main.start_new_game(4)
	state=main.game.export_state()
	var flags: Dictionary=state["progress_flags"]
	for pass_index in range(12):
		for identifier in StoryCampaign.data()["events"]:
			var candidate:=StoryCampaign.apply_event(flags,identifier)
			if not candidate.is_empty():flags=candidate
	state["progress_flags"]=flags
	state["progress_flags"]["story_v1_cleared"]=true
	state["gate_team"]=["pc_01","pc_02","pc_03"]
	state["world"]={"location":"town","player_cell":[2,4],"quest_step":StoryCampaign.total_steps()}
	check(main.game.import_state(state),"完了後表示の有効状態")
	main.mode=main.Mode.COMPLETE
	main._refresh()
	await _layout(main,"complete_full_fixture")
	for index in range(8):
		main.mode=main.Mode.JOURNAL
		main._journal_index=index
		main._refresh()
		await _layout(main,"journal_full_"+str(index))

func _layout(main: Node, label: String) -> void:
	await process_frame
	await process_frame
	var scrolls: Array = []
	for node in main.find_children("*","Control",true,false):
		if not node.is_visible_in_tree():continue
		if node is ScrollContainer:
			check(main.get_viewport_rect().encloses(node.get_global_rect()),label+": スクロール領域が画面外")
			scrolls.append(node)
		if not (node is BaseButton or node is Label or node is RichTextLabel or node is TextEdit):continue
		checked_controls += 1
		var parent: Node = node.get_parent()
		var scroll: ScrollContainer
		while parent != null and parent != main:
			if parent is ScrollContainer:
				scroll=parent
				break
			parent=parent.get_parent()
		var rect: Rect2 = node.get_global_rect()
		if scroll == null:
			check(main.get_viewport_rect().encloses(rect),"%s: %sの領域が画面外 %s" % [label,node.get_class(),str(rect)])
		else:
			check(rect.size.x <= scroll.size.x,label+": スクロール内で横幅が超過")
			if node is BaseButton and not node.disabled:
				scroll.ensure_control_visible(node)
				await process_frame
				await process_frame
				check(scroll.get_global_rect().encloses(node.get_global_rect()),label+": スクロールしても操作部品が見えない")
	for scroll in scrolls:scroll.scroll_vertical=0
	cases.append(label)

func _timings(main: Node) -> void:
	for kind in ["move","select","cancel","equip"]:
		main.start_new_game(4)
		main.game.play_metrics.set_source("automated")
		var state: Dictionary = main.game.export_state()
		state["party"][0]["learned_abilities"] = ["power_strike","firm_guard"]
		check(main.game.import_state(state),"応答計測の有効状態")
		var times: Array[float] = []
		var cold: Array[float] = []
		for index in range(105):
			if kind == "select":
				main.mode=main.Mode.FIELD;main._refresh()
			elif kind == "cancel":
				main.mode=main.Mode.FIELD;main._refresh();main.submit_player_action({"kind":"journal"})
			elif kind == "equip":
				main.mode=main.Mode.FIELD;main._refresh();main.submit_player_action({"kind":"party"})
			else:
				while Time.get_ticks_msec()-main._last_move_ms < 160:await process_frame
			await process_frame
			await process_frame
			var equip_button: Button
			if kind == "equip":
				var equipped_now: Array=main.game.export_state()["party"][0]["equipped_abilities"]
				var label: String="装着" if equipped_now.is_empty() else str(main.game.abilities["power_strike"]["name"])+"を外す"
				for candidate in main.find_children("*","Button",true,false):
					if candidate.text == label and not candidate.disabled:equip_button=candidate;break
				if equip_button != null:
					var parent: Node=equip_button.get_parent()
					while parent != null:
						if parent is ScrollContainer:parent.ensure_control_visible(equip_button);break
						parent=parent.get_parent()
					await process_frame
					await process_frame
			var before_pixels := _pixels(main)
			var started := Time.get_ticks_usec()
			if kind == "move":check(main.submit_player_action({"kind":"move","dx":1 if index%2==0 else -1,"dy":0}),"移動入力を受理")
			elif kind == "select":check(main.submit_player_action({"kind":"party"}),"選択入力を受理")
			elif kind == "cancel":check(main.submit_player_action({"kind":"back"}),"取消入力を受理")
			else:
				if equip_button != null:equip_button.pressed.emit()
				check(equip_button != null,"装着の実ボタンを操作")
				check(("power_strike" in main.game.export_state()["party"][0]["equipped_abilities"]) == (index%2==0),"装着状態が操作に対応")
			await process_frame
			await process_frame
			var after_pixels := _pixels(main)
			check(not before_pixels.is_empty() and not after_pixels.is_empty() and before_pixels!=after_pixels,"入力に対応して実描画が更新された")
			var elapsed := float(Time.get_ticks_usec()-started)/1000.0
			if index < 5:cold.append(elapsed)
			else:times.append(elapsed)
		times.sort()
		latency[kind]={"samples":times.size(),"sorted_samples_ms":times,"p95_ms":times[94],"max_ms":times.back(),"initial_five_ms":cold,"includes_render_readback":true}
		check(times[94]<=100.0 and times.back()<=200.0,"表示応答の閾値: "+kind)

func _pixels(main: Node) -> String:
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	var rendered: Image=main.get_viewport().get_texture().get_image()
	if rendered.is_empty():return ""
	var hashing:=HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	hashing.update(rendered.get_data())
	return hashing.finish().hex_encode()
