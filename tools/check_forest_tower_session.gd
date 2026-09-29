extends SceneTree
## 旧保存形式と加入条件の境界検査。通常到達は別の実操作撮影で確かめる。
var checks := 0
var failures: Array[String]=[]
func check(ok: bool, reason: String) -> void:
	checks+=1
	if not ok:failures.append(reason)
func _initialize() -> void:
	var game := GameSession.new()
	check(game.new_first_region(),"新規開始")
	var state := game.export_state()
	check(state["party"].size()==1,"村の開始は主人公だけ")
	check(state["first_region"]["reserve"].size()==3,"待機に3人を用意")
	# 塔追加前に村の2人だけ加入済みの保存を再現する。待機にスイナはいない。
	for actor in state["first_region"]["reserve"]:
		if actor["id"]!="pc_04":state["party"].append(actor)
	state["first_region"]["reserve"]=[]
	state["inventory"]["gate_pass"]=1
	state["overworld"]["cleared"]=["first_boss"]
	state["progress_flags"]["castle_north_permission"]=true
	state["progress_flags"]["job_change_unlocked"]=true
	FirstRegion.place(state["overworld"],{"layer":"interior","node":"first_forest_tower","room":2,"cell":[11,6]})
	state["overworld"]["facing"]=3
	check(game.import_state(state),"4人目のない旧保存状態を読める")
	check(game.interact_first_region().get("kind")=="dialogue","ボス前の会話")
	check(not game.finish_first_region_recruit("pc_04"),"ボス前の加入を拒否")
	check(game.export_state()["party"].size()==3,"ボス前は3人")
	state["overworld"]["cleared"].append("forest_tower_boss")
	check(game.import_state(state),"ボス撃破後の旧保存状態を読める")
	check(not game.finish_first_region_recruit("pc_04"),"会話開始前の加入を拒否")
	var dialogue := game.interact_first_region()
	check(dialogue.get("text",[]).size()==10 and dialogue.get("join_actor")=="pc_04","採用済み会話10行")
	check(game.export_state()["first_region"]["reserve"].size()==1,"旧保存へ加入候補だけ補充")
	check(game.finish_first_region_recruit("pc_04"),"会話終了で加入")
	check(game.export_state()["party"].size()==4,"4人になる")
	check(game.export_state()["first_region"]["reserve"].is_empty(),"待機から除く")
	check(game.export_state()["progress_flags"].get("mountain_path_open",false),"山道解放")
	check(not game.finish_first_region_recruit("pc_04"),"二重加入を拒否")
	var save_path := "user://forest_tower_legacy_%d.json" % OS.get_process_id()
	check(game.save_game(save_path),"加入後を保存")
	var loaded := GameSession.new()
	check(loaded.load_game(save_path) and loaded.export_state()==game.export_state(),"新旧保存からの加入後を完全復元")
	var forged := state.duplicate(true);forged["progress_flags"]["mountain_path_open"]=true
	check(not loaded.import_state(forged),"スイナ未加入での山道解放状態を拒否")
	check(loaded.export_state()==game.export_state(),"不正な保存の読込で状態を壊さない")
	PlaySessionMetrics.write_json("res://docs/verification/sprint5-forest-tower/session-checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"scope":"旧保存互換と加入条件の人工状態検査。通常到達の証明ではない。"})
	for failure in failures:printerr("FOREST_TOWER_SESSION_FAIL: "+failure)
	print("FOREST_TOWER_SESSION_PASS: checks=%d" % checks if failures.is_empty() else "FOREST_TOWER_SESSION_FAIL")
	quit(0 if failures.is_empty() else 1)
