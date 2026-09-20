extends "res://tools/check_battle_acceptance.gd"

var diagnostics := RuntimeDiagnostics.new()

func _initialize() -> void:
	OS.add_logger(diagnostics)
	call_deferred("_run")

func _run() -> void:
	var normal_only := "--normal-only" in OS.get_cmdline_user_args()
	var source_build := BuildIdentity.current()
	var profile: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var normal: Array = []
	for index in range(StoryCampaign.total_steps()):
		var entry := StoryCampaign.step(index)
		var waves := StoryCampaign.battle_waves(entry)
		if waves.is_empty():continue
		if index < ChapterOne.STEPS.size():
			if waves[0] != ["gate_beast"]:normal.append({"id":"normal_"+str(index),"waves":[waves[0]]})
		else:
			for wave in range(waves.size()-1):normal.append({"id":"normal_%d_%d" % [index,wave],"waves":[waves[wave]]})
	var resources: Array = []
	for circuit in CampaignContent.data()["circuits"]:
		for section in circuit["sections"]:
			var waves: Array = []
			var reward_definition: Dictionary={}
			for entry in circuit["steps"]:
				if entry["section"] == section["id"] and entry["kind"] == "battle":waves.append(entry["enemies"])
				if entry["section"] == section["id"] and entry["kind"] == "challenge":reward_definition=entry
			if waves.size() != 2:errors.append("区画の戦闘数が2ではない")
			if reward_definition.is_empty():errors.append("区画に課題の報酬定義がない")
			resources.append({"id":section["id"],"waves":waves,"reward":reward_definition})
	if normal.size() != 14 or resources.size() != 25:errors.append("通常戦14・補給区画25を網羅できない")
	var game := GameSession.new()
	var reports: Array = []
	var first_action_defeats := 0
	var total := 0
	var normal_pass := true
	var supply_pass := true
	for group in (["normal"] if normal_only else ["normal","resources","deterministic"]):
		var cases: Array = normal if group == "normal" else (resources if group == "resources" else [{"id":"fixed_a","waves":[["night_bat"]]},{"id":"fixed_b","waves":[["core_wisp"]]}])
		for setup in cases:
			for size in [3,4]:
				var initial := _initial_state(game,size,profile)
				var wins := 0
				var stalled := 0
				var potions: Array[int] = []
				var loss_potions: Array[int] = []
				var traces: Dictionary = {}
				var rng_used := 0
				for seed_value in range(1000):
					if not game.new_game(size) or not game.import_state(initial):
						errors.append("固定状態を初期化できない")
						break
					var result := _trial(game,setup["waves"],seed_value,group == "resources",group == "deterministic",setup.get("reward",{}))
					if result.is_empty():break
					total += 1
					wins += 1 if result["victory"] else 0
					stalled += result["cutoffs"]
					first_action_defeats += result["before_action_defeats"]
					if result["victory"]:potions.append(result["potions_used"])
					else:loss_potions.append(result["potions_used"])
					if group == "deterministic":
						traces[result["trace_hash"]] = int(traces.get(result["trace_hash"],0))+1
						rng_used += 1 if result["rng_used"] else 0
				if not errors.is_empty():break
				potions.sort()
				var median: float = (float(potions[(potions.size()-1)/2])+float(potions[potions.size()/2]))/2.0 if not potions.is_empty() else -1.0
				var p90 := potions[ceili(potions.size()*0.9)-1] if not potions.is_empty() else -1
				var ok := wins >= 950 if group == "normal" else (not potions.is_empty() and median <= 1 and p90 <= 2)
				if group == "normal":normal_pass = normal_pass and ok
				if group == "resources":supply_pass = supply_pass and ok
				var histogram: Dictionary = {}
				for count in potions:histogram[str(count)] = int(histogram.get(str(count),0))+1
				var reward_data: Dictionary=setup.get("reward",{})
				reports.append({"group":group,"case":setup["id"],"party_size":size,"wins":wins,"trials":1000,"cutoffs":stalled,"victory_potion_median":median,"victory_potion_p90":p90,"victory_potion_counts":histogram,"defeat_potion_samples":loss_potions,"distinct_traces":traces.size(),"trace_counts":traces,"rng_used_trials":rng_used,"constant_across_seeds":traces.size()==1 and rng_used==0,"passed":ok if group != "deterministic" else null,"challenge_reward":{"potions":reward_data.get("reward_potions",0),"hp_percent":reward_data.get("reward_hp_percent",0),"mp_percent":reward_data.get("reward_mp_percent",0)}})
				print("PREPLAY_COMBAT_CASE: %s %s party=%d wins=%d median=%.1f p90=%d" % [group,setup["id"],size,wins,median,p90])
			if not errors.is_empty():break
		if not errors.is_empty():break
	errors.append_array(diagnostics.messages())
	BuildIdentity._cached.clear()
	if source_build != BuildIdentity.current():errors.append("検査中にゲームのソースが変更された")
	if total != (28000 if normal_only else 82000):errors.append("予定した試行数を完了していない")
	var report := {"kind":"automated_preplay_combat","build":source_build,"profile_sha256":FileAccess.get_sha256(PROFILE),"runner_sha256":FileAccess.get_sha256("res://tools/check_preplay_combat.gd"),"trials":total,"T04":"PASS" if normal_pass else "FAIL","T05":"PASS" if first_action_defeats==0 else "FAIL","T07":"NOT_RUN" if normal_only else ("PASS" if supply_pass else "FAIL"),"before_action_defeats":first_action_defeats,"results":reports,"errors":errors,"human_playtest":"NOT_RUN","resource_policy":"各区画で全快・薬3、途中帰還なし。第1戦勝利後に本番の課題報酬処理を実行。薬と休息の定義値を各ケースに記録。第2戦へHP/MP・所持品を持ち越す。種はseed、seed+1000。敗北消費は別集計。シード間の同一性は診断値であり合否条件にしない。"}
	var output_path := "res://docs/verification/preplay-normal-combat.json" if normal_only else "res://docs/verification/preplay-combat.json"
	if not PlaySessionMetrics.write_json(output_path,report):errors.append("結果を書き出せない")
	for error in errors:printerr("PREPLAY_COMBAT_ERROR: "+error)
	OS.remove_logger(diagnostics)
	print("PREPLAY_COMBAT_RESULT: trials=%d T04=%s T05=%s T07=%s errors=%d" % [total,report["T04"],report["T05"],report["T07"],errors.size()])
	quit(2 if not errors.is_empty() else (0 if normal_pass and supply_pass and first_action_defeats==0 else 1))

func _trial(game: GameSession, waves: Array, seed_value: int, reward: bool, trace_enabled: bool, reward_definition: Dictionary = {"reward_potions":1}) -> Dictionary:
	var used := 0
	var first_defeats := 0
	var rng_used := false
	var trace: Array = []
	for wave_index in range(waves.size()):
		var battle := game.start_battle(waves[wave_index],seed_value+1000*wave_index)
		if battle == null:
			errors.append("戦闘を開始できない")
			return {}
		var rng_before: int = battle._rng.state
		var item_before := battle.potions
		var turns := 0
		var actions := 0
		while battle.phase == BattleState.Phase.INPUT and turns < 30:
			for actor in battle.pending():
				var error := battle.queue_action(_action(battle,actor))
				if not error.is_empty():errors.append(error)
			if not errors.is_empty() or not battle.can_resolve():
				if errors.is_empty():errors.append("ターンの入力が不足")
				return {}
			var events := battle.resolve_round()
			if not battle.last_error.is_empty() or events.is_empty():
				errors.append("ターン実行エラー")
				return {}
			turns += 1
			for event in events:
				if str(event.get("actor","")).begins_with("pc_") and event["code"] in ["damage","heal","revive","guard","steal"]:actions+=1
			if trace_enabled:trace.append({"events":events,"state":battle.snapshot()})
		used += item_before-battle.potions
		rng_used = rng_used or battle._rng.state != rng_before
		var won := battle.phase == BattleState.Phase.VICTORY
		first_defeats += 1 if battle.phase == BattleState.Phase.DEFEAT and actions == 0 else 0
		if not won:
			if battle.phase not in [BattleState.Phase.DEFEAT,BattleState.Phase.INPUT]:errors.append("不正な終了状態")
			return {"victory":false,"cutoffs":1 if battle.phase==BattleState.Phase.INPUT else 0,"potions_used":used,"before_action_defeats":first_defeats,"rng_used":rng_used,"trace_hash":JSON.stringify(trace).sha256_text()}
		if not game.finish_battle():
			errors.append("勝利を確定できない")
			return {}
		if reward and wave_index == 0:
			var state := game.export_state()
			GameSession.apply_challenge_reward(state,reward_definition)
			if not game.import_state(state):
				errors.append("課題報酬の固定状態を適用できない")
				return {}
	return {"victory":true,"cutoffs":0,"potions_used":used,"before_action_defeats":first_defeats,"rng_used":rng_used,"trace_hash":JSON.stringify(trace).sha256_text()}
