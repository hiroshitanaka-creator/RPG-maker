extends "res://tools/check_preplay_combat.gd"

func _run()->void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var game:=GameSession.new()
	game.catalog.potion_healing=150
	var results: Array=[]
	var cases: Array=[]
	for setup in profile["encounters"]:cases.append({"id":setup["id"],"waves":[setup["enemies"]],"reward":{}})
	for circuit in CampaignContent.data()["circuits"]:
		for section in circuit["sections"]:
			if section["id"] not in ["cave_3","cave_5","gate_3","gate_5"]:continue
			var waves: Array=[]
			var reward: Dictionary={}
			for entry in circuit["steps"]:
				if entry["section"]!=section["id"]:continue
				if entry["kind"]=="battle":waves.append(entry["enemies"])
				if entry["kind"]=="challenge":reward=entry
			cases.append({"id":section["id"],"waves":waves,"reward":reward})
	for setup in cases:
		for size in [3,4]:
			var initial:=_initial_state(game,size,profile)
			var wins:=0
			var used: Array[int]=[]
			for seed_value in range(200):
				game.new_game(size)
				game.import_state(initial)
				var result:=_trial(game,setup["waves"],seed_value,not setup["reward"].is_empty(),false,setup["reward"])
				if result["victory"]:wins+=1;used.append(result["potions_used"])
			used.sort()
			var entry: Dictionary={"id":setup["id"],"party_size":size,"wins":wins,"samples":200,"p50":used[(used.size()-1)/2] if not used.is_empty() else -1,"p90":used[ceili(used.size()*0.9)-1] if not used.is_empty() else -1}
			results.append(entry)
			print("POTION_150_PROBE: ",entry)
	errors.append_array(diagnostics.messages())
	OS.remove_logger(diagnostics)
	PlaySessionMetrics.write_json("res://docs/verification/potion-150-candidates.json",{"kind":"candidate_search_not_acceptance","potion_healing":150,"results":results,"errors":errors})
	quit(0 if errors.is_empty() else 1)
