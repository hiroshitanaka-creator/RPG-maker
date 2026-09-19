extends SceneTree


func _initialize() -> void:
	var game := GameSession.new()
	if not game.new_game(4):
		quit(1)
		return
	var state := game.export_state()
	var actor_id: String = state["party"][0]["id"]
	state["party"][0]["hp"] = 1
	if not game.import_state(state):
		quit(1)
		return
	for identifier in game.jobs:
		if not game.change_job(actor_id, identifier) or int(game.export_state()["party"][0]["hp"]) < 1:
			printerr("RUNTIME_EDGE_FAIL: 転職だけで戦闘不能になりました。")
			quit(1)
			return
	state = game.export_state()
	state["party"][0]["hp"] = 0
	if not game.import_state(state) or not game.change_job(actor_id, "warrior") or game.export_state()["party"][0]["hp"] != 0:
		printerr("RUNTIME_EDGE_FAIL: 転職だけで復活しました。")
		quit(1)
		return
	print("RUNTIME_EDGE_PASS: 20職の変更で生存を維持し、戦闘不能も勝手に解除しない。")
	quit(0)
