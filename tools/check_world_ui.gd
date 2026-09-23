extends SceneTree
var failures: Array[String] = []
var captures: Array[String] = []

func check(value: bool, message: String) -> bool:
	if not value:
		failures.append(message)
	return value

func _initialize() -> void:
	call_deferred("_run")

func capture(main: Node, name: String) -> void:
	await process_frame
	await process_frame
	check(main.automation_snapshot()["mode"] != "error","画面の実行時エラーがない: "+name)
	if DisplayServer.get_name() == "headless":
		return
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	var image := main.get_viewport().get_texture().get_image()
	if check(not image.is_empty(),"実描画の画像が空でない"):
		var path := "res://docs/verification/screens/"+name+".png"
		check(image.save_png(path) == OK,"実描画の保存")
		captures.append(path)

func check_buttons(node: Node, bounds: Rect2, in_scroll: bool = false) -> void:
	in_scroll = in_scroll or node is ScrollContainer
	if node is Button and node.is_visible_in_tree() and not in_scroll:
		check(bounds.encloses(node.get_global_rect()),"操作ボタンが画面内: "+node.text)
	for child in node.get_children():
		check_buttons(child,bounds,in_scroll)

func leave_interior(main: Node) -> void:
	while main.game.overworld_state()["layer"] == "interior":
		var state: Dictionary = main.game.overworld_state()
		var definition := WorldExpedition.current_room(state)
		var grid := AStarGrid2D.new()
		grid.region = Rect2i(0,0,32,18)
		grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
		grid.update()
		for y in range(18):
			for x in range(32):
				grid.set_point_solid(Vector2i(x,y),not WorldExpedition.walkable_room(definition,Vector2i(x,y)))
		var path := grid.get_id_path(WorldExpedition.point(state["cell"]),WorldExpedition.point(definition["exit"]))
		if not check(not path.is_empty(),"内部から戻る経路"):
			return
		for i in range(1,path.size()):
			check(main.game.move_overworld(path[i]),"通常APIで出口へ歩く")
		check(main.game.interact_overworld().get("kind") == "moved","内部から地形へ戻る")

func _run() -> void:
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	main.save_path = "user://qa_world_ui.json"
	main.checkpoint_path = "user://qa_world_ui_checkpoint.json"
	main._to_menu()
	check(main.submit_player_action({"kind":"open_world"}),"メニューから世界地図へ入る")
	await capture(main,"world_field")
	check(main.automation_snapshot()["mode"] == "world","広域画面を表示")
	check_buttons(main,main.get_viewport_rect())
	var state: Dictionary = main.game.overworld_state()
	var start := WorldExpedition.point(state["cell"])
	var destination := start
	for direction in [Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP,Vector2i.DOWN]:
		if WorldTerrain.passable(start+direction,"walk"):
			destination = start+direction
			break
	check(main.submit_player_action({"kind":"world_target","x":destination.x,"y":destination.y}),"地図クリックの移動入力")
	var started := Time.get_ticks_msec()
	while WorldExpedition.point(main.game.overworld_state()["cell"]) != destination and Time.get_ticks_msec()-started < 3000:
		await process_frame
	check(WorldExpedition.point(main.game.overworld_state()["cell"]) == destination,"フレーム更新で実際に1セル移動")
	var direction := destination-start
	check(main._facing == (1 if direction.x < 0 else 2 if direction.x > 0 else 3 if direction.y < 0 else 0),"自動移動の方向へ歩行画像が向く")
	await create_timer(0.22).timeout
	check(main._walk_frame == 0,"移動停止後に静止コマへ戻る")
	check(main.submit_player_action({"kind":"save"}),"画面操作による広域保存")
	var saved: Dictionary = main.game.export_state()
	main._to_menu()
	main._load_save()
	check(main.automation_snapshot()["mode"] == "world" and main.game.export_state() == saved,"保存した広域位置へ画面ごと戻る")
	check(main.submit_player_action({"kind":"world_atlas"}),"全図を開く")
	await capture(main,"world_atlas")
	check_buttons(main,main.get_viewport_rect())
	check(main.submit_player_action({"kind":"back"}),"全図を閉じる")
	check(main.submit_player_action({"kind":"party"}),"広域から編成を開く")
	check(main.submit_player_action({"kind":"back"}) and main.automation_snapshot()["mode"] == "world","編成から広域へ戻る")
	# 前の通し検査で実際に到達して保存した戦闘前。能力・フラグの合成で代用しない。
	main.save_path = "user://qa_world_battle_before.json"
	main._load_save()
	main.save_path = "user://qa_world_ui.json"
	main.game.play_metrics.set_source("automated")
	check(main.automation_snapshot()["mode"] == "world" and main.game.overworld_state()["layer"] == "interior","通し操作で作った内部セーブを画面へ復元")
	await capture(main,"world_interior")
	check(main.submit_player_action({"kind":"world_interact"}) and main.automation_snapshot()["mode"] == "battle","拠点内部の印から戦闘を開始")
	await capture(main,"world_battle")
	var turns := 0
	while main.automation_snapshot()["mode"] == "battle" and turns < 60:
		var battle: BattleState = main.game.current_battle()
		for actor in battle.pending():
			var action: BattleAction = preload("res://tools/integrated_play_policy.gd").action(battle,actor)
			var kinds := {BattleAction.Kind.ATTACK:"attack",BattleAction.Kind.GUARD:"guard",BattleAction.Kind.ABILITY:"ability",BattleAction.Kind.ITEM:"potion"}
			check(main.submit_player_action({"kind":kinds[action.kind],"actor":action.actor_id,"target":action.target_id,"ability":action.ability_id}),"画面の戦闘入力を受理")
		for action in preload("res://tools/integrated_play_policy.gd").adjustments(battle):
			var kinds := {BattleAction.Kind.ATTACK:"attack",BattleAction.Kind.GUARD:"guard",BattleAction.Kind.ABILITY:"ability",BattleAction.Kind.ITEM:"potion"}
			check(main.submit_player_action({"kind":kinds[action.kind],"actor":action.actor_id,"target":action.target_id,"ability":action.ability_id}),"予告に応じた入力修正")
		check(main.submit_player_action({"kind":"resolve_round"}),"画面からターンを解決")
		main.submit_player_action({"kind":"skip_presentation"})
		turns += 1
	while main.automation_snapshot()["mode"] == "dialogue":
		main.submit_player_action({"kind":"confirm"})
	check(main.automation_snapshot()["mode"] == "world","戦闘後に旧本編ではなく拠点内部へ復帰")
	check(main.submit_player_action({"kind":"save"}),"戦闘後の内部進行を画面から保存")
	await capture(main,"world_after_battle")
	check_buttons(main,main.get_viewport_rect())
	main.save_path = "user://qa_world_battle_before.json"
	main._load_save()
	main.save_path = "user://qa_world_ui.json"
	var retry_before: Dictionary = main.game.export_state()
	check(main.submit_player_action({"kind":"world_interact"}),"復帰検査のため同じ戦闘前から開始")
	var defeat_turns := 0
	while main.automation_snapshot()["mode"] == "battle" and defeat_turns < 250:
		var battle: BattleState = main.game.current_battle()
		for actor in battle.pending():
			check(main.submit_player_action({"kind":"guard","actor":actor.id,"target":actor.id}),"全員防御による意図的な敗北検査")
		main.submit_player_action({"kind":"resolve_round"})
		main.submit_player_action({"kind":"skip_presentation"})
		defeat_turns += 1
		await process_frame
	check(main.automation_snapshot()["mode"] == "defeat","実際の戦闘計算で全滅判定に到達")
	check(main.submit_player_action({"kind":"retry_battle"}),"広域戦闘前へ復帰")
	check(main.automation_snapshot()["mode"] == "world" and main.game.export_state() == retry_before,"全滅後も内部位置・編成・薬・進行が戦闘前と一致")
	await capture(main,"world_after_retry")
	leave_interior(main)
	check(main.game.change_world_transport("flight"),"獲得済みの飛行を入口で使用")
	var route := WorldTerrain.path(WorldExpedition.point(main.game.overworld_state()["cell"]),WorldTerrain.cell_of("town"),"flight")
	for i in range(1,route.size()):
		check(main.game.move_overworld(route[i]),"飛行で船着場へ戻る")
	check(main.game.change_world_transport("ship"),"獲得済みの船を船着場で使用")
	main._resume_current()
	await capture(main,"world_ship")
	check(main.game.change_world_transport("flight"),"船から飛行へ切替")
	for actor in main.game.export_state()["party"]:
		check(main.game.set_party_leader(actor["id"]),"各人物を先頭にできる")
		main._resume_current()
		await capture(main,"world_flight_"+actor["id"])
	var output := FileAccess.open("res://docs/verification/world-ui%s.json" % ("-headless" if DisplayServer.get_name() == "headless" else "-native"),FileAccess.WRITE)
	if output != null:
		output.store_string(JSON.stringify({"status":"PASS" if failures.is_empty() else "FAIL","errors":failures,"captures":captures,"battle_rounds":turns,"deliberate_defeat_rounds":defeat_turns,"display":DisplayServer.get_name(),"source":"automated_ui_inputs_and_real_play_save","transport_preview_movement":"adjacent_cell_api_without_ui_wait"},"  ",true)+"\n")
		output.close()
	for error in failures:
		printerr("WORLD_UI_FAIL: "+error)
	if failures.is_empty():
		print("WORLD_UI_PASS: captures=%d errors=0" % captures.size())
	main.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)
