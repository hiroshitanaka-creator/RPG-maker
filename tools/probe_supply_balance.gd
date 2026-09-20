extends "res://tools/check_preplay_combat.gd"

func _run() -> void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var game:=GameSession.new()
	game.enemy_definitions["swift_beast"]["stats"]["attack"]=20
	game.enemy_definitions["mending_beast"]["stats"]["attack"]=23
	var rows: Array=[]
	for recovery in [60,70,75,80,90]:
		game.catalog.potion_healing=recovery
		for size in [3,4]:
			var initial:=_initial_state(game,size,profile)
			for room in ["gate_2","gate_3","gate_4","gate_5"]:
				var waves: Array=[]
				for entry in CampaignContent.circuit("gate")["steps"]:
					if entry["section"]==room and entry["kind"]=="battle":waves.append(entry["enemies"])
				var used: Array[int]=[]
				var wins:=0
				for seed_value in range(200):
					game.new_game(size);game.import_state(initial)
					var result:=_trial(game,waves,seed_value,true,false)
					if result.is_empty():break
					if result["victory"]:wins+=1;used.append(result["potions_used"])
				used.sort()
				var median: float=(float(used[(used.size()-1)/2])+float(used[used.size()/2]))/2.0 if not used.is_empty() else -1.0
				var p90:=used[ceili(used.size()*0.9)-1] if not used.is_empty() else -1
				rows.append({"healing":recovery,"party_size":size,"case":room,"wins":wins,"trials":200,"median":median,"p90":p90})
				print("SUPPLY_CANDIDATE: heal=%d party=%d case=%s wins=%d/200 median=%.1f p90=%d" % [recovery,size,room,wins,median,p90])
				if not errors.is_empty():break
			if not errors.is_empty():break
		if not errors.is_empty():break
	errors.append_array(diagnostics.messages())
	PlaySessionMetrics.write_json("res://docs/verification/supply-balance-candidates.json",{"kind":"calibration_only_not_acceptance","seeds":[0,199],"candidates":rows,"errors":errors,"production_data_changed":false,"normal_enemy_attack_candidates":[20,23]})
	OS.remove_logger(diagnostics)
	quit(0 if errors.is_empty() else 2)
