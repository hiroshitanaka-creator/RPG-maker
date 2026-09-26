extends "res://tools/smoke_first_region.gd"
## 固定受入と同じ通常操作を実描画で実行し、依頼された9場面を保存する。
signal capture_done
var _captured: Dictionary = {}
var _capture_busy := false
var _capture_errors: Array[String] = []

func _watch() -> void:
	super._watch()
	if _capture_busy or _finished or not is_instance_valid(_main):return
	var state := _state()
	if not state.has("first_region"):return
	var pose := _pose()
	var snapshot := _snapshot()
	var name := ""
	if pose.get("node") == "start_village":
		if snapshot.get("mode") == "world" and state["party"].size() == 1:name = "01-village-start"
		if snapshot.get("mode") == "dialogue" and state["party"].size() == 2:name = "02-companion-conversation"
	elif pose.get("layer") == "world":
		if not _definition.is_empty():
			if _at(_outside(_definition["village_entrance"])):name = "03-village-exit-world"
			if _at(_definition["gate"]["before"]) and not _has_pass() and str(_main.get("_notice")).contains("通行証"):name = "04-closed-gate"
			if _at(_outside(_definition["cave_entrance"])) and _has_pass():name = "08-cave-exit-world"
			if _at(_definition["gate"]["beyond"]) and _has_pass():name = "09-gate-passed"
	elif pose.get("node") == "first_cave":
		if _floor_at(pose) == 1 and snapshot.get("mode") == "world":name = "05-cave-floor-1"
		if _floor_at(pose) == 2 and snapshot.get("mode") == "world" and not _has_pass():
			var cell: Array = pose["cell"]
			var boss: Array = _definition["boss"]["point"]["cell"]
			if absi(int(cell[0])-int(boss[0]))+absi(int(cell[1])-int(boss[1])) == 1:name = "06-cave-floor-2-boss"
		if snapshot.get("mode") == "battle" and snapshot.get("battle_input",{}).get("encounter_id") == "first_boss":name = "07-boss-battle"
	if name.is_empty() or _captured.has(name):return
	_captured[name] = true
	_capture_busy = true
	call_deferred("_capture",name)

func _capture(name: String) -> void:
	# 歩行停止時の本番UI再配置が終わるまで、次の入力を送らず待つ。
	await create_timer(0.3).timeout
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	var destination := "res://docs/verification/first-region/"+name+".png"
	var frame := _main.get_viewport().get_texture().get_image()
	if frame.is_empty() or frame.save_png(destination) != OK:_capture_errors.append(destination)
	else:print("FIRST_REGION_CAPTURE: "+destination)
	_capture_busy = false
	capture_done.emit()

func _key(code: int) -> bool:
	if _capture_busy:await capture_done
	return await super._key(code)

func _button(labels: Array) -> bool:
	if _capture_busy:await capture_done
	return await super._button(labels)

func _combat_command(action: Dictionary) -> bool:
	if _capture_busy:await capture_done
	return await super._combat_command(action)

func _finish() -> void:
	if _capture_busy:await capture_done
	if _captured.size() != 9 or not _capture_errors.is_empty():
		printerr("FIRST_REGION_CAPTURE_FAIL: count=%d errors=%s" % [_captured.size(),str(_capture_errors)])
		quit(1)
		return
	print("FIRST_REGION_CAPTURE_PASS: images=9 renderer="+DisplayServer.get_name())
	super._finish()

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		printerr("FIRST_REGION_CAPTURE_FAIL: 実描画が必要です。")
		quit(2)
		return
	root.min_size = Vector2i(1024,576)
	root.max_size = Vector2i(1024,576)
	root.size = Vector2i(1024,576)
	DirAccess.make_dir_recursive_absolute("res://docs/verification/first-region")
	await super._run()
