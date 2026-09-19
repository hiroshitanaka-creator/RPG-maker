extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var game := GameSession.new()
	if not game.new_game(4):
		printerr("WORLD_DATA_FAIL: ゲーム状態を作成できません。")
		quit(1)
		return
	var location := "town"
	var cell := Vector2i(2,4)
	var distances := 0
	var battles := 0
	for index in range(ChapterOne.STEPS.size()):
		var step := ChapterOne.step(index)
		if location != step["location"]:
			printerr("WORLD_DATA_FAIL: 地域の接続が不正です。")
			quit(1)
			return
		var goal := Vector2i(int(step["cell"][0]), int(step["cell"][1]))
		var distance := _distance(location, cell, goal)
		if distance < 0:
			printerr("WORLD_DATA_FAIL: 目標へ歩いて到達できません。")
			quit(1)
			return
		distances += distance
		cell = goal
		if step.get("rest", false):
			game.rest()
		if step["kind"] == "battle":
			var encounter := game.start_battle(step["enemies"], 20260919+index)
			for round_index in range(100):
				if encounter.phase != BattleState.Phase.INPUT:
					break
				var target := encounter.living(Combatant.Team.ENEMY)[0]
				for actor in encounter.pending():
					encounter.queue_action(BattleAction.strike(actor.id, target.id))
				encounter.resolve_round()
			if encounter.phase != BattleState.Phase.VICTORY:
				printerr("WORLD_DATA_FAIL: 連続戦闘で勝利できません。")
				quit(1)
				return
			game.finish_battle()
			battles += 1
		if step["kind"] == "travel":
			location = step["destination"]
			cell = Vector2i(int(step["spawn"][0]), int(step["spawn"][1]))
	print("WORLD_DATA_PASS: steps=%d walk_cells=%d battles=%d" % [ChapterOne.STEPS.size(), distances, battles])
	print("これは経路と連続戦闘の追加検査です。画像・画面操作・R-07の通し検証の代わりにはなりません。")
	quit(0)


func _distance(location: String, start: Vector2i, goal: Vector2i) -> int:
	var frontier: Array[Vector2i] = [start]
	var distances := {start: 0}
	var index := 0
	while index < frontier.size():
		var current := frontier[index]
		index += 1
		if current == goal:
			return distances[current]
		for direction in [Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT, Vector2i.UP]:
			var next: Vector2i = current+direction
			if ChapterOne.is_walkable(location, next) and not distances.has(next):
				distances[next] = int(distances[current])+1
				frontier.append(next)
	return -1
