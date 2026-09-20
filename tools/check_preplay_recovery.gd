extends "res://tools/check_battle_acceptance.gd"

func _run() -> void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var outcomes: Array=[]
	for size in [3,4]:
		for circuit in CampaignContent.data()["circuits"]:
			var base:=StoryCampaign.step(circuit["trigger_step"])
			for section in circuit["sections"]:
				var game:=GameSession.new()
				var state:=_initial_state(game,size,profile)
				var stage:=0
				var solved: Array=[]
				for index in range(circuit["steps"].size()):
					var entry: Dictionary=circuit["steps"][index]
					if entry["section"]==section["id"] and entry["kind"]=="battle":stage=index;break
					if entry["kind"]=="challenge":solved.append(entry["id"])
				var task: Dictionary=circuit["steps"][stage]
				state["world"]={"location":task["location"],"player_cell":task["cell"],"section":task["section"],"quest_step":circuit["trigger_step"]}
				state["expedition"]={"id":circuit["id"],"stage":stage,"wave":0,"origin":{"location":base["location"],"player_cell":base["cell"],"quest_step":circuit["trigger_step"]},"solved":solved}
				state["inventory"]["potion"]=0
				for actor in state["party"]:actor["hp"]=1;actor["mp"]=0
				if not game.import_state(state):errors.append("消耗した有効状態を用意できない");continue
				var origin:=game.world_state()
				var progress: Dictionary=game.export_state()["expedition"].duplicate(true)
				var flags: Dictionary=game.export_state()["progress_flags"].duplicate(true)
				if not game.return_to_town() or not game.rest():errors.append("全区画から帰還・休息できる");continue
				var file: String="user://qa_preplay_recovery_%d.json" % size
				if not game.save_game(file):errors.append("帰還中に保存できる");continue
				var loaded:=GameSession.new()
				if not loaded.load_game(file) or not loaded.resume_exploration():errors.append("保存後に同じ区画へ再開できる");continue
				var after:=loaded.export_state()
				var passed: bool=after["world"]==origin and after["expedition"]==progress and after["progress_flags"]==flags
				for actor in after["party"]:passed=passed and actor["hp"]==actor["max_hp"] and actor["mp"]==actor["max_mp"]
				if not passed:errors.append("帰還・休息で進行を変えずHP/MPを回復する")
				outcomes.append({"party_size":size,"section":section["id"],"restored":passed})
	if outcomes.size()!=50:errors.append("25区画×2編成を網羅していない")
	var result: Dictionary={"kind":"depleted_state_recovery","states":outcomes,"failures":errors,"status":"PASS" if errors.is_empty() else "FAIL","scope":"全25区画の有効な消耗状態から通常APIで帰還・休息・保存・再開。帰還なしの補給指標T07をPASSに置換しない。","build":BuildIdentity.current()}
	if not PlaySessionMetrics.write_json("res://docs/verification/preplay-recovery.json",result):errors.append("結果の保存失敗")
	for message in errors:printerr("PREPLAY_RECOVERY_FAIL: "+message)
	if errors.is_empty():print("PREPLAY_RECOVERY_PASS: 25区画×3人/4人、消耗から復帰、進行不変")
	quit(0 if errors.is_empty() else 1)
