extends "res://tools/probe_reaction_balance.gd"

func _run()->void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	var choices: Array=[
		{"enemy":"elder_slime","hp":200,"power":500,"speed":2,"shield":20,"resistance":50,"heal_below":25,"guard_every":2},
		{"enemy":"night_bat","hp":260,"power":300,"speed":0,"shield":20,"resistance":30,"heal_below":50,"guard_every":2}]
	for resistance in [70,80,90]:choices.append({"enemy":"ancient_shell","hp":200,"power":500,"speed":2,"shield":80,"resistance":resistance,"heal_below":25,"guard_every":2})
	for item in choices:
		probe_hp=item["hp"]
		probe_resistance=item["resistance"]
		probe_heal_below=item["heal_below"]
		probe_guard_every=item["guard_every"]
		var rates: Array=[]
		var fast: Array=[]
		for size in [3,4]:
			rates.append(_sample(item["enemy"],item["power"],item["speed"],item["shield"],size,1000))
			fast.append(last_fast)
		item["rates"]=rates
		item["fast"]=fast
		print("TEMPO_FINAL_1000: ",item)
		PlaySessionMetrics.write_json("res://docs/verification/reaction-tempo-final.json",{"kind":"candidate_search_not_acceptance","choices":choices,"errors":errors})
	quit(0 if errors.is_empty() else 1)
