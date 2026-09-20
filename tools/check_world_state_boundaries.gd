extends SceneTree
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)

func _initialize() -> void:
	var game := GameSession.new()
	check(game.new_game(4) and game.open_world_exploration(),"境界検査用の初期状態")
	var base := game.export_state()
	var graph := WorldExpedition.data()
	var proof: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/world-map-phase2.json"))
	check(proof["status"] == "PASS" and proof["graph_sha256"] == FileAccess.get_file_as_string("res://world/map_graph.json").sha256_text(),"独立したPhase 2の検証結果と同じグラフ")
	var excluded: Dictionary = {}
	for state in proof["rejected_states"]:
		excluded["%d:%s" % [int(state["mask"]),state["node"]]] = true
	var accepted := 0
	var rejected := 0
	for mask in range(8):
		for node in graph["nodes"]:
			var candidate := base.duplicate(true)
			var state: Dictionary = candidate["overworld"]
			for f in range(graph["flags"].size()):
				state["flags"][graph["flags"][f]["id"]] = (mask & (1 << f)) != 0
			state["layer"] = "interior"
			state["node"] = node["id"]
			state["room"] = 0
			state["cell"] = WorldExpedition.room(node["id"],0)["spawn"].duplicate()
			var entrance := WorldTerrain.cell_of(node["id"])
			state["world_cell"] = [entrance.x,entrance.y]
			var expected := not excluded.has("%d:%s" % [mask,node["id"]])
			var previous := game.export_state()
			var actual := game.import_state(candidate)
			check(actual == expected,"全フラグ組合せで入場条件と読込結果が一致")
			if actual:
				accepted += 1
				check(game.export_state() == candidate,"受理した状態を変更せず復元")
			else:
				rejected += 1
				check(game.export_state() == previous,"拒否した読込で現在の状態を壊さない")
	check(accepted == 224 and rejected == 168,"Phase 2の全392組合せと本番の読込境界が一致")
	var corruption_cases: Array = []
	var broken := base.duplicate(true)
	broken["overworld"]["flags"].erase("world_ship_unlocked")
	corruption_cases.append(broken)
	broken = base.duplicate(true)
	broken["overworld"]["room"] = 999
	corruption_cases.append(broken)
	broken = base.duplicate(true)
	broken["overworld"]["cell"] = [0.5,4]
	corruption_cases.append(broken)
	broken = base.duplicate(true)
	broken["overworld"]["transport"] = "unknown"
	corruption_cases.append(broken)
	broken = base.duplicate(true)
	broken["overworld"]["origin"] = "garden"
	corruption_cases.append(broken)
	broken = base.duplicate(true)
	var highland := WorldTerrain.cell_of("ridgehearth")
	broken["overworld"]["cell"] = [highland.x,highland.y]
	broken["overworld"]["world_cell"] = [highland.x,highland.y]
	corruption_cases.append(broken)
	broken = base.duplicate(true)
	broken["overworld"]["visited"] = ["town","town"]
	corruption_cases.append(broken)
	broken = base.duplicate(true)
	broken["overworld"]["choices"] = {"town":0}
	corruption_cases.append(broken)
	for candidate in corruption_cases:
		check(not game.import_state(candidate),"欠落・型・位置・未達報酬の不正な読込を拒否")
	var recovered := 0
	for mask in [2,4,5,6]:
		var candidate := base.duplicate(true)
		var state: Dictionary = candidate["overworld"]
		for f in range(graph["flags"].size()):
			state["flags"][graph["flags"][f]["id"]] = (mask & (1 << f)) != 0
		var entry := "brine_port" if mask == 2 else "ridgehearth"
		var cell := WorldTerrain.cell_of(entry)
		state["cell"] = [cell.x,cell.y]
		state["world_cell"] = [cell.x,cell.y]
		check(game.import_state(candidate),"前提が欠けても入場可能な位置の障害注入")
		var mode := "ship" if mask == 2 else "flight"
		check(game.change_world_transport(mode),"所持済みの移動手段で帰還")
		var path := WorldTerrain.path(cell,WorldTerrain.cell_of("town"),mode)
		check(not path.is_empty(),"実地形上の帰還経路")
		var reached := not path.is_empty()
		for i in range(1,path.size()):
			reached = game.move_overworld(path[i]) and reached
		check(reached,"フラグを補完せず通常の移動APIで出発地点へ帰還")
		if reached:
			recovered += 1
		check(game.overworld_state()["flags"] == state["flags"],"帰還で欠落フラグを自動補完しない")
	var output := FileAccess.open("res://docs/verification/world-state-boundaries.json",FileAccess.WRITE)
	if output != null:
		output.store_string(JSON.stringify({"status":"PASS" if failures.is_empty() else "FAIL","errors":failures,"flag_combinations":8,"state_inputs":392,"accepted":accepted,"rejected":rejected,"malformed_inputs":corruption_cases.size(),"physical_fault_recoveries":recovered,"source":"synthetic_fault_injection_not_normal_play"},"  ",true)+"\n")
		output.close()
	for error in failures:
		printerr("WORLD_STATE_FAIL: "+error)
	if failures.is_empty():
		print("WORLD_STATE_PASS: inputs=392 accepted=%d rejected=%d malformed=%d recoveries=%d errors=0" % [accepted,rejected,corruption_cases.size(),recovered])
	quit(0 if failures.is_empty() else 1)
