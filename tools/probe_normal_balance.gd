extends "res://tools/check_preplay_combat.gd"

func _run() -> void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var game:=GameSession.new()
	var initial:=_initial_state(game,3,profile)
	var candidates: Array=[]
	for speed_attack in [24,22,20,18]:
		for recovery_attack in [27,25,23,21]:
			game.enemy_definitions["swift_beast"]["stats"]["attack"]=speed_attack
			game.enemy_definitions["mending_beast"]["stats"]["attack"]=recovery_attack
			var wins:=0
			var used: Array[int]=[]
			for seed_value in range(1000):
				game.new_game(3)
				if not game.import_state(initial):errors.append("固定状態の復元失敗");break
				var result:=_trial(game,[["swift_beast","mending_beast"]],seed_value,false,false)
				if result.is_empty():break
				wins+=1 if result["victory"] else 0
				if result["victory"]:used.append(result["potions_used"])
			used.sort()
			candidates.append({"swift_attack":speed_attack,"mending_attack":recovery_attack,"wins":wins,"potion_p90":used[ceili(used.size()*0.9)-1] if not used.is_empty() else -1})
			print("BALANCE_CANDIDATE: attack=%d/%d wins=%d/1000" % [speed_attack,recovery_attack,wins])
			if not errors.is_empty():break
		if not errors.is_empty():break
	errors.append_array(diagnostics.messages())
	PlaySessionMetrics.write_json("res://docs/verification/normal-balance-candidates.json",{"kind":"in_memory_enemy_stat_experiment","candidates":candidates,"errors":errors,"production_data_changed":false,"profile_sha256":FileAccess.get_sha256(PROFILE),"source_build":BuildIdentity.current()})
	OS.remove_logger(diagnostics)
	quit(0 if errors.is_empty() else 2)
