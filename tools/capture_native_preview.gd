extends "res://tools/smoke_chapter1.gd"

var _captured: Dictionary = {}


func _capture(main: Node, name: String) -> void:
	if _captured.has(name):
		return
	await process_frame
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var destination := "res://docs/verification/screens/" + name + ".png"
	var error := main.get_viewport().get_texture().get_image().save_png(destination)
	if error != OK:
		_fail("画面保存に失敗しました: " + destination)
		return
	_captured[name] = true
	print("CAPTURE: " + destination)


func _run() -> void:
	DirAccess.make_dir_recursive_absolute("res://docs/verification/screens")
	var packed: PackedScene = load(ProjectSettings.get_setting("application/run/main_scene"))
	var main := packed.instantiate()
	root.add_child(main)
	await process_frame
	await _capture(main, "title")
	main.start_new_game(4)
	await _capture(main, "field")
	main.submit_player_action({"kind":"party"})
	await _capture(main, "party")
	main.submit_player_action({"kind":"back"})
	for step in range(MAX_STEPS):
		await process_frame
		var state: Dictionary = main.automation_snapshot()
		if state.get("chapter1_cleared", false):
			await _capture(main, "chapter1_clear")
			print("NATIVE_PREVIEW_PASS")
			quit(0)
			return
		var mode: String = state.get("mode", "")
		match mode:
			"dialogue":
				await _capture(main, "dialogue")
				main.submit_player_action({"kind":"confirm"})
			"battle":
				await _capture(main, "battle")
				var input: Dictionary = state.get("battle_input", {})
				if input.get("ready", false):
					main.submit_player_action({"kind":"resolve_round"})
				elif not str(input.get("actor", "")).is_empty() and not str(input.get("enemy", "")).is_empty():
					main.submit_player_action({"kind":"attack", "actor":input["actor"], "target":input["enemy"]})
			"field":
				var here: Array = state.get("player_cell", [])
				var goal: Array = state.get("objective_cell", [])
				if here == goal:
					main.submit_player_action({"kind":"interact"})
				else:
					var route := _route(here, goal, state.get("walkable_cells", []))
					if route.is_empty():
						_fail("撮影中の経路がありません。")
						return
					main.submit_player_action({"kind":"move", "dx":route[0][0]-here[0], "dy":route[0][1]-here[1]})
			_:
				_fail("撮影中に未知の進行状態: " + mode)
				return
	_fail("撮影が最大操作数に到達しました。")
