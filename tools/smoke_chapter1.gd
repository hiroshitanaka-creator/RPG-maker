extends SceneTree

const MAX_STEPS := 30000


func _initialize() -> void:
	call_deferred("_run")


func _fail(message: String) -> void:
	printerr("CHAPTER1_FAIL: " + message)
	quit(1)


func _run() -> void:
	var main_path: String = ProjectSettings.get_setting("application/run/main_scene")
	var packed: PackedScene = load(main_path)
	if packed == null:
		_fail("起動シーンが読み込めません。")
		return
	var main := packed.instantiate()
	root.add_child(main)
	await process_frame
	if not main.has_method("start_new_game") or not main.has_method("automation_snapshot") or not main.has_method("submit_player_action"):
		_fail("実ゲームの開始・状態参照・通常操作の入口が未実装です。")
		return
	main.start_new_game(4)
	var moved := 0
	var battles := 0
	var interactions := 0
	var previous_state := ""
	var stalled := 0
	for step in range(MAX_STEPS):
		await process_frame
		var state: Dictionary = main.automation_snapshot()
		if state.get("chapter1_cleared", false):
			if moved == 0 or battles == 0 or interactions == 0:
				_fail("移動・会話・戦闘を通らずにクリア扱いになりました。")
				return
			print("CHAPTER1_PASS: steps=%d moved=%d battles=%d interactions=%d" % [step, moved, battles, interactions])
			quit(0)
			return
		var serial := JSON.stringify(state)
		stalled = stalled + 1 if serial == previous_state else 0
		previous_state = serial
		if stalled > 600:
			_fail("同じ状態で600フレーム停止しました。")
			return
		var mode: String = state.get("mode", "")
		match mode:
			"dialogue":
				if main.submit_player_action({"kind": "confirm"}):
					interactions += 1
			"battle":
				var input: Dictionary = state.get("battle_input", {})
				if input.get("ready", false):
					if main.submit_player_action({"kind": "resolve_round"}):
						battles += 1
				elif not str(input.get("actor", "")).is_empty() and not str(input.get("enemy", "")).is_empty():
					main.submit_player_action({"kind": "attack", "actor": input["actor"], "target": input["enemy"]})
			"field":
				# 経路探索はゲームが公開する通行可能セルだけを使う。
				var here: Array = state.get("player_cell", [])
				var goal: Array = state.get("objective_cell", [])
				if here.size() != 2 or goal.size() != 2:
					_fail("プレイヤーと目的地の位置がありません。")
					return
				if here == goal:
					if main.submit_player_action({"kind": "interact"}):
						interactions += 1
				else:
					var path := _route(here, goal, state.get("walkable_cells", []))
					if path.is_empty():
						_fail("通常の移動で目的地へ到達できません。")
						return
					if main.submit_player_action({"kind": "move", "dx": path[0][0] - here[0], "dy": path[0][1] - here[1]}):
						moved += 1
			"defeat":
				_fail("自動プレイ中に全滅しました。")
				return
			_:
				_fail("未知の進行状態: " + mode)
				return
	_fail("最大操作数までに第1章へ到達できませんでした。")


func _route(start: Array, goal: Array, cells: Array) -> Array:
	var allowed: Dictionary = {}
	for cell in cells:
		allowed[Vector2i(int(cell[0]), int(cell[1]))] = true
	var origin := Vector2i(int(start[0]), int(start[1]))
	var target := Vector2i(int(goal[0]), int(goal[1]))
	var pending: Array[Vector2i] = [origin]
	var parents: Dictionary = {origin: origin}
	var at := 0
	while at < pending.size():
		var current := pending[at]
		at += 1
		if current == target:
			var route: Array = []
			while current != origin:
				route.push_front([current.x, current.y])
				current = parents[current]
			return route
		for delta in [Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT, Vector2i.UP]:
			var next: Vector2i = current + delta
			if allowed.has(next) and not parents.has(next):
				parents[next] = current
				pending.append(next)
	return []
