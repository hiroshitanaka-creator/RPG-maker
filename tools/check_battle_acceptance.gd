extends SceneTree

const PROFILE := "res://data/acceptance_battle_profile_v1.json"
var errors: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var profile: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	if not profile.has_all(["id","status","seeds","party_sizes","jobs","mastery","hp_mp","potions","erosion","midgame_slots","loadouts","policy","turn_limit","win_rate","fast_finish","encounters"]):
		printerr("BATTLE_ACCEPTANCE_ERROR: 検証入力が不足")
		quit(2)
		return
	if profile["seeds"].get("first") != 0 or profile["seeds"].get("last") != 999 or profile["party_sizes"].map(func(value: Variant) -> int: return int(value)) != [3,4] or profile["jobs"] != ["warrior","martial_artist","priest","mage"] or profile["mastery"] != "initial_job_once" or profile["hp_mp"] != "full" or profile["policy"] != "revive_then_half_hp_heal_then_quarter_hp_potion_then_max_damage_v1" or int(profile["turn_limit"]) <= 10 or profile["encounters"].is_empty() or profile["win_rate"]["min"] != 0.4 or profile["win_rate"]["max"] != 0.6 or profile["fast_finish"]["max_turns"] != 10 or profile["fast_finish"]["min_rate"] != 0.8:
		printerr("BATTLE_ACCEPTANCE_ERROR: 未対応または不正な検証入力")
		quit(2)
		return
	var results: Array = []
	var game := GameSession.new()
	var all_fast := 0
	var all_trials := 0
	var rates_ok := true
	var names: Dictionary = {}
	var started := Time.get_ticks_msec()
	for setup in profile["encounters"]:
		if names.has(setup["id"]):
			errors.append("対象戦闘IDが重複")
			break
		names[setup["id"]] = true
		for size in profile["party_sizes"]:
			var initial := _initial_state(game,int(size),profile)
			if initial.is_empty():break
			var outcomes: Array = []
			var rounds: Array[int] = []
			var wins := 0
			var fast := 0
			var cutoffs := 0
			for seed_value in range(1000):
				if not game.new_game(int(size)) or not game.import_state(initial) or game.export_state() != initial:
					errors.append("初期状態を完全復元できない")
					break
				var battle := game.start_battle(setup["enemies"],seed_value)
				if battle == null:
					errors.append("戦闘を開始できない")
					break
				var turns := 0
				while battle.phase == BattleState.Phase.INPUT and turns < int(profile["turn_limit"]):
					for actor in battle.pending():
						var error := battle.queue_action(_action(battle,actor))
						if not error.is_empty():errors.append(error)
					if not errors.is_empty() or not battle.can_resolve():
						if errors.is_empty():errors.append("ターンを解決できない")
						break
					var events := battle.resolve_round()
					if not battle.last_error.is_empty() or events.is_empty():
						errors.append("戦闘実行エラー: "+battle.last_error)
						break
					turns += 1
				if not errors.is_empty():break
				if battle.phase not in [BattleState.Phase.VICTORY,BattleState.Phase.DEFEAT,BattleState.Phase.INPUT]:
					errors.append("戦闘状態が不正")
					break
				var won := battle.phase == BattleState.Phase.VICTORY
				var ended := battle.phase in [BattleState.Phase.VICTORY,BattleState.Phase.DEFEAT]
				wins += 1 if won else 0
				fast += 1 if ended and turns <= int(profile["fast_finish"]["max_turns"]) else 0
				cutoffs += 0 if ended else 1
				rounds.append(turns)
				outcomes.append({"seed":seed_value,"victory":won,"turns":turns,"cutoff":not ended})
			if outcomes.size() != 1000:errors.append("試行数が1000ではない")
			var passed := wins >= 400 and wins <= 600 and outcomes.size() == 1000
			rates_ok = rates_ok and passed
			rounds.sort()
			results.append({"encounter":setup["id"],"party_size":size,"initial_state":initial,"outcomes":outcomes,"trials":outcomes.size(),"wins":wins,"defeats":outcomes.size()-wins,"cutoffs":cutoffs,"win_rate":float(wins)/1000.0,"within_10":fast,"median_turns":rounds[rounds.size()/2] if not rounds.is_empty() else 0,"max_turns":rounds.back() if not rounds.is_empty() else 0,"AC-01":"PASS" if passed else "FAIL"})
			all_fast += fast
			all_trials += outcomes.size()
			print("BATTLE_SAMPLE: %s party=%d wins=%d/1000 within10=%d cutoff=%d" % [setup["id"],size,wins,fast,cutoffs])
			if not errors.is_empty():break
		if not errors.is_empty():break
	var fast_ok := all_trials > 0 and float(all_fast)/float(all_trials) >= 0.8
	var report := {"profile":profile,"profile_sha256":FileAccess.get_sha256(PROFILE),"runner_sha256":FileAccess.get_sha256("res://tools/check_battle_acceptance.gd"),"build":BuildIdentity.current(),"threshold_status":"PROVISIONAL_INPUTS_APPROVED_NUMERIC_LIMITS","trials":all_trials,"within_10":all_fast,"errors":errors,"elapsed_ms":Time.get_ticks_msec()-started,"AC-01":"ERROR" if not errors.is_empty() else ("PASS" if rates_ok else "FAIL"),"AC-02":"ERROR" if not errors.is_empty() else ("PASS" if fast_ok else "FAIL"),"results":results}
	if not PlaySessionMetrics.write_json("res://docs/verification/provisional-battle-acceptance.json",report):
		printerr("BATTLE_ACCEPTANCE_ERROR: 記録を保存できない")
		quit(2)
		return
	print("BATTLE_ACCEPTANCE: AC-01=%s AC-02=%s errors=%d" % [report["AC-01"],report["AC-02"],errors.size()])
	for error in errors:printerr("BATTLE_ACCEPTANCE_ERROR: "+error)
	quit(2 if not errors.is_empty() else (0 if rates_ok and fast_ok else 1))

func _initial_state(game: GameSession, size: int, profile: Dictionary) -> Dictionary:
	if not game.new_game(size):return {}
	var state := game.export_state()
	state["inventory"]["potion"] = int(profile["potions"])
	state["progress_flags"]["midgame_slots"] = profile["midgame_slots"]
	for actor in state["party"]:
		var job: Dictionary = game.jobs[actor["job_id"]]
		actor["jp"][job["id"]] = int(job["mastery_cost"])
		actor["mastered_jobs"] = [job["id"]]
		actor["learned_abilities"] = job["abilities"].duplicate()
		actor["equipped_abilities"] = profile["loadouts"][job["id"]].duplicate()
		actor["erosion"] = int(profile["erosion"])
		actor["max_hp"] = int(job["stats"]["hp"])+int(job["stat_growth"].get("hp",0))
		actor["hp"] = actor["max_hp"]
		actor["max_mp"] = int(job["stats"]["mp"])+int(job["stat_growth"].get("mp",0))
		actor["mp"] = actor["max_mp"]
	if not game.import_state(state):
		errors.append("事前定義した初期状態が無効")
		return {}
	return game.export_state()

func _action(battle: BattleState, actor: Combatant) -> BattleAction:
	for skill in actor.equipped:
		var definition: Dictionary = battle.catalog.abilities[skill]
		if definition["kind"] == "revive" and actor.mp >= int(definition["cost"]):
			var targets := battle.targets_for(actor.id,BattleAction.Kind.ABILITY,skill)
			if not targets.is_empty():return BattleAction.skill(actor.id,targets[0].id,skill)
	var hurt := battle.living(Combatant.Team.PARTY)
	hurt.sort_custom(func(a: Combatant,b: Combatant) -> bool: return a.id < b.id if a.hp*b.max_hp == b.hp*a.max_hp else a.hp*b.max_hp < b.hp*a.max_hp)
	for target in hurt:
		if target.hp*2 >= target.max_hp:continue
		for skill in actor.equipped:
			var definition: Dictionary = battle.catalog.abilities[skill]
			if definition["kind"] == "heal" and actor.mp >= int(definition["cost"]) and target in battle.targets_for(actor.id,BattleAction.Kind.ABILITY,skill):
				return BattleAction.skill(actor.id,target.id,skill)
	if battle.potions > 0 and hurt[0].hp*4 < hurt[0].max_hp:
		return BattleAction.potion(actor.id,hurt[0].id)
	var target := battle.living(Combatant.Team.ENEMY)[0]
	var best := BattleAction.strike(actor.id,target.id)
	var damage := BattleMath.physical(actor.attack,target.defense)
	for skill in actor.equipped:
		var definition: Dictionary = battle.catalog.abilities[skill]
		if actor.mp < int(definition["cost"]):continue
		var score := 0
		if definition["kind"] == "physical":score = BattleMath.physical(actor.attack,target.defense,int(definition["power"]))*int(definition["hits"])
		elif definition["kind"] == "magic":score = BattleMath.magical(actor.magic,target.resistance,int(definition["power"]),definition["element"] in target.weaknesses)
		if score > damage:
			damage = score
			best = BattleAction.skill(actor.id,target.id,skill)
	return best
