extends SceneTree
const Policy=preload("res://tools/integrated_play_policy.gd")

func _initialize() -> void:
	var input: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/mastery-charger-replay-input.json"))
	var rows: Array=[]
	for stock in [0,1,3,6,12,24]:
		for variant in ["original", "guard_and_ice", "seal_and_guard"]:
			var game:=GameSession.new()
			game.new_game(3)
			var fixture:=game.export_state()
			fixture["party"]=input["party"].duplicate(true)
			fixture["inventory"]["potion"]=stock
			fixture["progress_flags"]["midgame_slots"]=true
			if variant!="original":
				fixture["party"][0]["equipped_abilities"]=["four_strike","firm_guard"]
				fixture["party"][1]["equipped_abilities"]=["ice","fire","firm_guard"]
			if variant=="seal_and_guard":
				# 既得JPの60を僧侶へ配分した比較入力。主経路での習得は別に実行検証する。
				var caster: Dictionary=fixture["party"][1]
				caster["jp"]["mage"]-=60;caster["jp"]["priest"]=int(caster["jp"].get("priest",0))+60
				for id in ["heal","revive","seal"]:
					if id not in caster["learned_abilities"]:caster["learned_abilities"].append(id)
				caster["equipped_abilities"]=["seal","ice","firm_guard"]
				fixture["party"][2]["equipped_abilities"]=["seal","heal","revive"]
			if not game.import_state(fixture):printerr("CHARGER_PROBE_FAIL: 検査入力");quit(1);return
			var battle:=game.start_battle(input["enemies"],int(input["seed"]))
			for rule in game.catalog.integration["enemy_rules"]:
				if rule["id"]=="charger":battle.effects.configure(rule,{"charger":{"facts":[0,1],"confirmed":true}})
			var start:=game.export_state()
			for turn in range(80):
				if battle.phase!=BattleState.Phase.INPUT:break
				for actor in battle.pending():
					var action: BattleAction=Policy.action(battle,actor)
					if variant=="seal_and_guard" and "seal" in actor.equipped:
						var seal:=BattleAction.skill(actor.id,"enemy_01","seal")
						if battle._action_error(seal).is_empty():action=seal
					if not battle.queue_action(action).is_empty():printerr("CHARGER_PROBE_FAIL: 行動入力");quit(1);return
				for change in Policy.adjustments(battle):battle.queue_action(change)
				battle.resolve_round()
			rows.append({"potions":stock,"variant":variant,"victory":battle.phase==BattleState.Phase.VICTORY,"rounds":battle.round_number,"initial":start,"final":battle.snapshot()})
			print("CHARGER_PROBE: stock=%d %s victory=%s rounds=%d" % [stock,variant,str(battle.phase==BattleState.Phase.VICTORY),battle.round_number])
	var selected: Array=rows.filter(func(r:Dictionary)->bool:return r["variant"]=="guard_and_ice")
	var passed: bool=selected.size()==6 and selected.all(func(r:Dictionary)->bool:return r["victory"])
	PlaySessionMetrics.write_json("res://docs/verification/mastery-charger-probe.json",{"status":"PASS" if passed else "FAIL","selected":"guard_and_ice","scope":input["scope"],"rows":rows,"human":"NOT_RUN","build":BuildIdentity.current()})
	if not passed:printerr("CHARGER_POLICY_FAIL: 採用する装着の6条件に未達")
	quit(0 if passed else 1)
