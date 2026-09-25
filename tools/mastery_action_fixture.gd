extends RefCounted
## 単体検査用の明示入力。回数は注入せず、実際の技・戦闘結果から取得する。

static func exercise(game: GameSession, actor_id: String, job_id: String, attempts: int = -1) -> Array[String]:
	var errors: Array[String]=[]
	var condition: Dictionary=game.jobs[job_id]["mastery_action"]
	var skill: String=condition["training_ability"]
	var amount:=int(condition["required"]) if attempts<0 else attempts
	for iteration in range(amount):
		game.rest()
		var fixture:=game.export_state()
		for actor in fixture["party"]:
			if actor["id"]==actor_id:
				if skill not in actor["learned_abilities"]:actor["learned_abilities"].append(skill)
				actor["equipped_abilities"]=[skill]
		if not game.import_state(fixture):errors.append("修練単体検査の技装着入力");return errors
		var battle:=game.start_battle(["slime"],17+iteration)
		if battle==null:errors.append("修練単体検査の実戦開始");return errors
		var subject:=battle.actor_by_id(actor_id)
		var foe:=battle.living(Combatant.Team.ENEMY)[0]
		# 効果の成否を分けるための戦闘初期入力。回数や勝敗は書き換えない。
		foe.attack=0;foe.magic=0;foe.mp=0;foe.speed=0
		subject.speed=100
		var target:=foe
		if condition["metric"]=="revive":
			for ally in battle.living(Combatant.Team.PARTY):
				if ally.id!=actor_id:target=ally;break
			target.hp=0
		elif condition["metric"]=="heal":target=subject;target.hp=maxi(1,target.max_hp-1)
		elif condition["metric"]=="guard":target=subject
		for actor in battle.pending():
			var action:=BattleAction.skill(actor.id,target.id,skill) if actor.id==actor_id else BattleAction.guard(actor.id)
			var error:=battle.queue_action(action)
			if not error.is_empty():errors.append(error)
		battle.resolve_round()
		for turn in range(100):
			if battle.phase!=BattleState.Phase.INPUT:break
			for actor in battle.pending():battle.queue_action(BattleAction.strike(actor.id,battle.living(Combatant.Team.ENEMY)[0].id))
			battle.resolve_round()
		if battle.phase!=BattleState.Phase.VICTORY or not game.finish_battle():errors.append("修練後の実勝利と報酬反映")
	return errors

static func complete_state(state: Dictionary, jobs: Dictionary) -> Dictionary:
	# 他機能の境界検査が明示的に配置するマスター済み状態の前提。
	# この入力を、行動回数の実測や新規開始からの到達証拠には用いない。
	for actor in state["party"]:
		if not JobMastery.active(actor):continue
		for id in actor["mastered_jobs"]:
			actor["integrated"]["mastery"]["counts"][id]=int(jobs[id]["mastery_action"]["required"])
	return state
