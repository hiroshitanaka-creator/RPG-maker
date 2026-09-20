extends "res://tools/probe_reaction_balance.gd"

func _run()->void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	probe_resistance=100
	probe_guard_every=3
	for hp in [175,180,185,190]:
		probe_hp=hp
		var values: Array=[]
		for size in [3,4]:
			var rate:=_sample("ancient_shell",400,0,40,size,1000)
			values.append({"party_size":size,"rate":rate,"fast":last_fast,"p50":last_p50,"p90":last_p90})
		var entry: Dictionary={"hp":hp,"power":400,"speed":0,"shield":40,"resistance":100,"guard_every":3,"values":values}
		results.append(entry)
		print("GUARDIAN_FINAL_1000: ",entry)
		PlaySessionMetrics.write_json("res://docs/verification/guardian-final-candidates.json",{"kind":"candidate_search_not_acceptance","results":results,"errors":errors})
	quit(0 if errors.is_empty() else 1)
