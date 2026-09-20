extends "res://tools/probe_reaction_balance.gd"

func _run() -> void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	var selected: Array=[]
	for enemy in ["elder_slime","night_bat","ancient_shell","core_wisp"]:
		var candidates: Array=[]
		for hp in [320,480,640]:
			probe_hp=hp
			var at_hp: Array=[]
			for power in [0,5,10,15,20,25,30,40,50,60,75,100,125,150,200,300,400,600]:
				for speed in [0,3,6]:
					var rate:=_sample(enemy,power,speed,100,3,64)
					at_hp.append({"enemy":enemy,"hp":hp,"power":power,"speed":speed,"three_rate":rate})
			at_hp.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return absf(a["three_rate"]-0.5)<absf(b["three_rate"]-0.5))
			candidates.append_array(at_hp.slice(0,2))
		var paired: Array=[]
		for candidate in candidates:
			probe_hp=candidate["hp"]
			for shield in [100,90,80,70,60,50,40,30,20,10]:
				var rate:=_sample(enemy,candidate["power"],candidate["speed"],shield,4,96)
				var item: Dictionary=candidate.duplicate()
				item["shield"]=shield
				item["four_rate"]=rate
				item["distance"]=absf(item["three_rate"]-0.5)+absf(rate-0.5)
				paired.append(item)
		paired.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return a["distance"]<b["distance"])
		selected.append(paired[0])
		print("ENDURANCE_SELECTED: ",paired[0])
		results.append({"enemy":enemy,"paired_candidates":paired})
		PlaySessionMetrics.write_json("res://docs/verification/reaction-endurance-candidates.json",{"kind":"candidate_search_not_acceptance","results":results,"selected":selected,"errors":errors,"profile_sha256":FileAccess.get_sha256(PROFILE)})
	quit(0 if errors.is_empty() else 1)
