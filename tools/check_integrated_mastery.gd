extends SceneTree
var failures: Array[String]=[]
var checks:=0

func check(value: bool, message: String) -> void:
	checks+=1
	if not value:failures.append(message)

func _initialize() -> void:
	var game:=GameSession.new()
	game.new_game(4)
	game.choose_job("pc_01","beast");game.choose_job("pc_02","beast")
	var fixture:=game.export_state()
	for actor in fixture["party"]:
		if actor["id"] in ["pc_01","pc_02"]:
			actor["learned_abilities"]=["intimidate","seal"]
			actor["equipped_abilities"]=["intimidate","seal"]
	check(game.import_state(fixture),"効果と同時予約の検査入力")
	var battle:=game.start_battle(["slime"],91)
	var foe:=battle.actor_by_id("enemy_01")
	foe.hp=10000;foe.max_hp=10000;foe.attack=50;foe.mp=0;foe.speed=0
	for actor in battle.living(Combatant.Team.PARTY):
		actor.hp=1000;actor.max_hp=1000;actor.mp=100;actor.max_mp=100
	var first:=battle.actor_by_id("pc_01")
	var second:=battle.actor_by_id("pc_02")
	first.speed=100;second.speed=99
	var physical:={"kind":"physical","power":100,"hits":1,"element":"none"}
	var original_damage:=battle.effects.damage(foe,first,physical)
	var before:=battle.snapshot()
	battle.preview_action(BattleAction.skill(first.id,foe.id,"intimidate"))
	check(battle.snapshot()==before,"予測で修練回数・状態を変更しない")
	for actor in battle.pending():
		check(battle.queue_action(BattleAction.skill(actor.id,foe.id,"intimidate") if actor.id in [first.id,second.id] else BattleAction.guard(actor.id)).is_empty(),"同じ対象への同時予約")
	battle.resolve_round()
	check(battle.effects.damage(foe,first,physical)==ceili(original_damage*0.75),"威嚇で実計算が25%減る")
	check(battle.mastery_counts.get(first.id,0)==1 and battle.mastery_counts.get(second.id,0)==0,"先に成立した状態異常だけを数える")
	check(second.mp==100 and battle.successful_abilities(second.id).is_empty(),"重複で不発になった技は消費しない")
	check(not battle.queue_action(BattleAction.skill(first.id,foe.id,"intimidate")).is_empty(),"効果中の付与を拒否")
	for actor in battle.pending():battle.queue_action(BattleAction.guard(actor.id))
	battle.resolve_round()
	first.guard_rate=1.0
	check(battle.effects.damage(foe,first,physical)==original_damage,"付与ラウンドと次ラウンドが終われば失効")
	for stage in range(3):
		for actor in battle.pending():
			check(battle.queue_action(BattleAction.skill(actor.id,foe.id,"seal") if actor.id==first.id else BattleAction.guard(actor.id)).is_empty(),"借りた封緘技を通常実行")
		battle.resolve_round()
		check(battle.mastery_counts.get(first.id,0)==(2 if stage==2 else 1),"封緘は完成した防御低下を1回の状態異常として数える")
	var report:={"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"build":BuildIdentity.current(),"scope":"威嚇の実計算・期限・同時予約の不発・借用技による封緘完成。制御された戦闘初期状態を使用。"}
	PlaySessionMetrics.write_json("res://docs/verification/integrated-mastery-current.json",report)
	for failure in failures:printerr("INTEGRATED_MASTERY_FAIL: "+failure)
	print("INTEGRATED_MASTERY_RESULT: checks=%d failures=%d" % [checks,failures.size()])
	quit(0 if failures.is_empty() else 1)
