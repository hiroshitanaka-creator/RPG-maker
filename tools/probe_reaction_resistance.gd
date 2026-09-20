extends "res://tools/probe_reaction_balance.gd"

func _run() -> void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	probe_hp=640
	var night: Array=[]
	for size in [3,4]:night.append(_sample("night_bat",70,3,5,size,1000))
	print("NIGHT_FINAL_1000: ",night)
	var candidates: Array=[]
	for resistance in [20,30,40,50,60,80,100]:
		probe_resistance=resistance
		var rate:=_sample("ancient_shell",55,4,1,4,1000)
		var entry: Dictionary={"enemy":"ancient_shell","hp":640,"power":55,"speed":4,"shield":1,"resistance":resistance,"four_rate":rate}
		candidates.append(entry)
		print("RESISTANCE_1000: ",entry)
	PlaySessionMetrics.write_json("res://docs/verification/reaction-resistance-candidates.json",{"kind":"candidate_search_not_production_acceptance","night_rates":night,"candidates":candidates,"errors":errors})
	quit(0 if errors.is_empty() else 1)
