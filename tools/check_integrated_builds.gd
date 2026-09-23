extends "res://tools/check_integrated_progression.gd"
const Policy=preload("res://tools/integrated_play_policy.gd")
func _initialize()->void:
	var rows: Array=[]
	var builds: Dictionary={"human":["martial_artist","warrior","mage","priest"],"mixed":["beast","warrior","mage","slime"],"monster":["beast","shell","undead","slime"]}
	for label in builds:
		var game:=GameSession.new();game.new_game(4)
		for stage in range(2):
			if stage==1:
				for i in range(4):check(game.choose_job("pc_%02d" % (i+1),builds[label][i]),"比較の2職目へ通常転職")
			for victory in range(120):game.rest();fight(game)
		var initial:=game.export_state();initial["progress_flags"]["midgame_slots"]=true
		check(game.import_state(initial),"比較時点の3枠解放を明示した入力")
		for member in game.export_state()["party"]:
			for id in member["equipped_abilities"]:game.unequip_ability(member["id"],id)
			var choices: Array=["heal","revive","rending_claw","four_strike","disarm","fire","power_strike","cover","conduct","seal","restore_mp"]
			for id in choices:
				if id in game.available_abilities(member["id"]) and game.export_state()["party"][int(member["id"].trim_prefix("pc_"))-1]["equipped_abilities"].size()<game.slot_limit(member["id"]):game.equip_ability(member["id"],id)
		game.rest();initial=game.export_state()
		for member in initial["party"]:
			var jp:=0
			for value in member["jp"].values():jp+=int(value)
			check(jp==240 and member["integrated"]["exp"]==4800,"全員同一240JP・4800EXPの予算")
		for rule in game.catalog.integration["enemy_rules"]:
			var wins:=0;var turns:=0;var mp:=0;var fast:=0
			for seed_value in range(100):
				check(game.import_state(initial),"試行ごとに初期状態を完全復元")
				var b:=game.start_battle(["elder_slime"],seed_value)
				if b==null:check(false,"比較戦闘を開始");continue
				b.effects.configure(rule,{})
				for turn in range(40):
					if b.phase!=BattleState.Phase.INPUT:break
					for member in b.pending():check(b.queue_action(Policy.action(b,member)).is_empty(),"使用可能なコマンドだけを予約")
					for adjustment in Policy.adjustments(b):check(b.queue_action(adjustment).is_empty(),"予告に対する防御を予約")
					b.resolve_round();turns+=1
				wins+=1 if b.phase==BattleState.Phase.VICTORY else 0
				fast+=1 if b.phase!=BattleState.Phase.INPUT and b.round_number<=11 else 0
				for member in b.living(Combatant.Team.PARTY):mp+=member.mp
				if b.phase!=BattleState.Phase.INPUT:check(game.finish_battle(),"試行の戦闘を終了")
				else:game=GameSession.new()
			rows.append({"build":label,"rule":rule["id"],"seeds":[0,99],"trials":100,"wins":wins,"within10":fast,"mean_rounds":turns/100.0,"mean_remaining_mp":mp/100.0,"initial":initial})
	PlaySessionMetrics.write_json("res://docs/verification/integrated-builds-current.json",{"status":"PASS" if failures.is_empty() else "FAIL","trials":1800,"rows":rows,"failures":failures,"scope":"同一予算の固定構成・固定方針の比較。最適解探索、面白さ、AC-01勝率帯の検証ではない。全滅と40ターン打切りは敗北。"})
	for row in rows:print("INTEGRATED_BUILD: %s/%s wins=%d/100 mean_rounds=%.2f" % [row["build"],row["rule"],row["wins"],row["mean_rounds"]])
	for error in failures:printerr("INTEGRATED_BUILD_FAIL: "+error)
	quit(0 if failures.is_empty() else 1)
