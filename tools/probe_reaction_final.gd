extends "res://tools/probe_reaction_balance.gd"

func _run() -> void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	var choices: Array=[
		{"enemy":"gate_beast","hp":320,"power":100,"speed":0,"shield":40},
		{"enemy":"elder_slime","hp":640,"power":125,"speed":3,"shield":90},
		{"enemy":"night_bat","hp":640,"power":75,"speed":3,"shield":10},
		{"enemy":"flood_beast","hp":440,"power":20,"speed":0,"shield":25}]
	for preset in [{"enemy":"ancient_shell","hp":640,"power":50,"speed":3},{"enemy":"core_wisp","hp":200,"power":300,"speed":0}]:
		var candidates: Array=[]
		probe_hp=preset["hp"]
		for shield in [1,3,5,7,10,15,20,30,40,50,70,90,100]:
			var item: Dictionary=preset.duplicate()
			item["shield"]=shield
			item["rate"]=_sample(item["enemy"],item["power"],item["speed"],shield,4,200)
			candidates.append(item)
		candidates.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return absf(a["rate"]-0.5)<absf(b["rate"]-0.5))
		choices.append(candidates[0])
		print("REFINED_REACTION: ",candidates)
	for candidate in choices:
		probe_hp=candidate["hp"]
		var rates: Array=[]
		for size in [3,4]:rates.append(_sample(candidate["enemy"],candidate["power"],candidate["speed"],candidate["shield"],size,1000))
		candidate["rates"]=rates
		print("REACTION_1000: ",candidate)
		PlaySessionMetrics.write_json("res://docs/verification/reaction-final-candidates.json",{"kind":"candidate_search_not_production_acceptance","choices":choices,"errors":errors,"profile_sha256":FileAccess.get_sha256(PROFILE)})
	quit(0 if errors.is_empty() else 1)
