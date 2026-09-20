extends "res://tools/probe_reaction_balance.gd"

func _run() -> void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	var selected: Array=[]
	for enemy in ["night_bat","ancient_shell","core_wisp"]:
		var candidates: Array=[]
		var health: Array=[640] if enemy!="core_wisp" else [200,220,240,260]
		var powers: Array=[65,68,70,72,74] if enemy=="night_bat" else ([45,50,55] if enemy=="ancient_shell" else [250,300,350,400])
		var speeds: Array=[3] if enemy=="night_bat" else ([4,5] if enemy=="ancient_shell" else [0])
		var shields: Array=[1,5,10] if enemy=="night_bat" else ([1,20,40] if enemy=="ancient_shell" else [1])
		for hp in health:
			probe_hp=hp
			for power in powers:
				for speed in speeds:
					for shield in shields:
						var rates: Array=[]
						for size in [3,4]:rates.append(_sample(enemy,power,speed,shield,size,200))
						candidates.append({"enemy":enemy,"hp":hp,"power":power,"speed":speed,"shield":shield,"rates":rates,"distance":absf(rates[0]-0.5)+absf(rates[1]-0.5)})
		candidates.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return a["distance"]<b["distance"])
		var pick: Dictionary=candidates[0].duplicate()
		probe_hp=pick["hp"]
		var full: Array=[]
		for size in [3,4]:full.append(_sample(enemy,pick["power"],pick["speed"],pick["shield"],size,1000))
		pick["full_rates"]=full
		selected.append(pick)
		print("REACTION_REFINED_1000: ",pick)
		results.append({"enemy":enemy,"candidates":candidates})
		PlaySessionMetrics.write_json("res://docs/verification/reaction-refined-candidates.json",{"kind":"candidate_search_not_production_acceptance","selected":selected,"results":results,"errors":errors})
	quit(0 if errors.is_empty() else 1)
