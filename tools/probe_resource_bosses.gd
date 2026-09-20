extends "res://tools/probe_reaction_balance.gd"

func _run()->void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	var selected: Array=[]
	for enemy in ["ancient_shell","flood_beast"]:
		var preliminary: Array=[]
		probe_resistance=-1
		var health: Array=[150,170,190,210] if enemy=="ancient_shell" else [160,200,240,280]
		var powers: Array=[100,200,300,400,500,650] if enemy=="ancient_shell" else [0,10,20,30,40,60,100,200]
		for hp in health:
			probe_hp=hp
			for power in powers:
				for speed in [0,2,4]:
					for timing in ([2,3] if enemy=="ancient_shell" else [2]):
						probe_guard_every=timing
						var rate:=_sample(enemy,power,speed,100,3,96)
						var penalty:=maxf(0.0,last_p50-1)+maxi(0,last_p90-2)
						preliminary.append({"enemy":enemy,"hp":hp,"power":power,"speed":speed,"guard_every":timing,"three_rate":rate,"three_fast":last_fast,"three_p50":last_p50,"three_p90":last_p90,"score":absf(rate-0.5)+maxf(0.0,0.85-last_fast)*2+penalty*0.5})
		preliminary.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return a["score"]<b["score"])
		var paired: Array=[]
		for candidate in preliminary.slice(0,6):
			probe_hp=candidate["hp"]
			probe_guard_every=candidate["guard_every"]
			for resistance in [20,40,60,80,100]:
				probe_resistance=resistance
				for shield in [20,40,60,80,100]:
					var rate:=_sample(enemy,candidate["power"],candidate["speed"],shield,4,128)
					var item: Dictionary=candidate.duplicate()
					item["resistance"]=resistance;item["shield"]=shield
					item["four_rate"]=rate;item["four_fast"]=last_fast
					item["four_p50"]=last_p50;item["four_p90"]=last_p90
					item["score"]+=absf(rate-0.5)+maxf(0.0,0.85-last_fast)*2+(maxf(0.0,last_p50-1)+maxi(0,last_p90-2))*0.5
					paired.append(item)
		paired.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return a["score"]<b["score"])
		var pick: Dictionary=paired[0].duplicate()
		probe_hp=pick["hp"];probe_resistance=pick["resistance"];probe_guard_every=pick["guard_every"]
		var full: Array=[]
		for size in [3,4]:
			var rate:=_sample(enemy,pick["power"],pick["speed"],pick["shield"],size,1000)
			full.append({"rate":rate,"fast":last_fast,"p50":last_p50,"p90":last_p90})
		pick["full"]=full
		selected.append(pick)
		print("RESOURCE_BOSS_SELECTED: ",pick)
		results.append({"enemy":enemy,"preliminary":preliminary,"paired":paired})
		PlaySessionMetrics.write_json("res://docs/verification/resource-boss-candidates.json",{"kind":"candidate_search_not_acceptance","selected":selected,"results":results,"errors":errors})
	quit(0 if errors.is_empty() else 1)
