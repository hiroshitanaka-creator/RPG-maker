extends "res://tools/check_battle_acceptance.gd"

const Counterplay=preload("res://tools/counterplay_policy.gd")

func _run()->void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var game:=GameSession.new()
	var results: Array=[]
	for setup in profile["encounters"]:
		for size in [3,4]:
			var initial:=_initial_state(game,size,profile)
			var wins:=0
			var capped:=0
			for seed_value in range(1000):
				game.new_game(size)
				if not game.import_state(initial):errors.append("固定状態の復元失敗");break
				var battle:=game.start_battle(setup["enemies"],seed_value)
				for turn in range(30):
					if battle.phase!=BattleState.Phase.INPUT:break
					for actor in battle.pending():
						var error:=battle.queue_action(_action(battle,actor))
						if not error.is_empty():errors.append(error)
					for change in Counterplay.adjustments(battle):
						var error:=battle.queue_action(change)
						if not error.is_empty():errors.append(error)
					battle.resolve_round()
				wins+=1 if battle.phase==BattleState.Phase.VICTORY else 0
				capped+=1 if battle.phase==BattleState.Phase.INPUT else 0
			results.append({"encounter":setup["id"],"party_size":size,"wins":wins,"trials":1000,"cutoffs":capped})
			print("COUNTERPLAY_CASE: %s party=%d wins=%d cutoff=%d" % [setup["id"],size,wins,capped])
			if wins<800:errors.append("対処方針の暫定勝率80%未達: "+str(setup["id"])+"/"+str(size))
	PlaySessionMetrics.write_json("res://docs/verification/battle-counterplay.json",{"kind":"counterplay_diagnostic_not_AC01","policy":"一つの攻撃技と予告による防御。危険なら通常攻撃へ変更。未来乱数は不使用。","results":results,"errors":errors,"build":BuildIdentity.current(),"human_playtest":"NOT_RUN"})
	for message in errors:printerr("COUNTERPLAY_FAIL: "+message)
	if errors.is_empty():print("COUNTERPLAY_PASS: 固定状態と1000シードで対処方針の全ケース80%以上")
	quit(0 if errors.is_empty() else 1)
