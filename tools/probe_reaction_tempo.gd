extends "res://tools/probe_reaction_balance.gd"

func _run()->void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	var selected: Array=[]
	for enemy in ["elder_slime","night_bat","ancient_shell"]:
		var preliminary: Array=[]
		probe_resistance=-1
		for hp in [200,260,320]:
			probe_hp=hp
			for power in [25,50,75,100,150,200,300,500,750]:
				for speed in [0,2,4]:
					for timing in [2,3]:
						probe_guard_every=timing if enemy=="ancient_shell" else 0
						probe_heal_below=25 if timing==2 else 50
						var rate:=_sample(enemy,power,speed,100,3,64)
						preliminary.append({"enemy":enemy,"hp":hp,"power":power,"speed":speed,"guard_every":probe_guard_every,"heal_below":probe_heal_below,"three_rate":rate,"three_fast":last_fast,"score":absf(rate-0.5)+maxf(0.0,0.85-last_fast)*2.0})
		preliminary.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return a["score"]<b["score"])
		var paired: Array=[]
		for candidate in preliminary.slice(0,6):
			probe_hp=candidate["hp"]
			probe_guard_every=candidate["guard_every"]
			probe_heal_below=candidate["heal_below"]
			for resistance in [-1,30,50,70,90]:
				probe_resistance=resistance
				for shield in [20,50,80,100]:
					var rate:=_sample(enemy,candidate["power"],candidate["speed"],shield,4,96)
					var item: Dictionary=candidate.duplicate()
					item["resistance"]=resistance
					item["shield"]=shield
					item["four_rate"]=rate
					item["four_fast"]=last_fast
					item["score"]+=absf(rate-0.5)+maxf(0.0,0.85-last_fast)*2.0
					paired.append(item)
		paired.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return a["score"]<b["score"])
		selected.append(paired[0])
		print("TEMPO_SELECTED: ",paired[0])
		results.append({"enemy":enemy,"three_candidates":preliminary,"paired_candidates":paired})
		PlaySessionMetrics.write_json("res://docs/verification/reaction-tempo-candidates.json",{"kind":"candidate_search_not_acceptance","selected":selected,"results":results,"errors":errors})
	quit(0 if errors.is_empty() else 1)
