extends RefCounted

# 検査用方針。画面にある予告・能力値・予約コマンドだけを使い、乱数の先読みはしない。
static func adjustments(battle: BattleState)->Array[BattleAction]:
	var result: Array[BattleAction]=[]
	if not battle.has_reactive_enemy():return result
	var plan: Dictionary=battle.queued.duplicate()
	var keep: String=""
	var best_gain: int=-1
	for identifier in plan:
		var action: BattleAction=plan[identifier]
		if not _offensive(battle,action):continue
		var actor:=battle.actor_by_id(identifier)
		var target:=battle.actor_by_id(action.target_id)
		var skill: Dictionary=battle.catalog.abilities[action.ability_id]
		var amount:=BattleMath.physical(actor.attack,target.defense,int(skill["power"]))*int(skill["hits"]) if skill["kind"]=="physical" else BattleMath.magical(actor.magic,target.resistance,int(skill["power"]),str(skill["element"]) in target.weaknesses)
		var gain:=amount-BattleMath.physical(actor.attack,target.defense)
		if gain>best_gain:best_gain=gain;keep=identifier
	for identifier in plan:
		if identifier!=keep and _offensive(battle,plan[identifier]):plan[identifier]=BattleAction.strike(identifier,plan[identifier].target_id)
	for repeat in range(2):
		var count:=_count(battle,plan)
		for actor in battle.living(Combatant.Team.PARTY):
			if battle.forecast_damage(actor.id,true,count,false)>=actor.hp:
				for identifier in plan:
					if _offensive(battle,plan[identifier]):plan[identifier]=BattleAction.strike(identifier,plan[identifier].target_id)
				count=0
		for actor in battle.living(Combatant.Team.PARTY):
			if battle.forecast_damage(actor.id,false,count,false)*2>=actor.hp:plan[actor.id]=BattleAction.guard(actor.id)
	for identifier in plan:
		var before: BattleAction=battle.queued[identifier]
		var after: BattleAction=plan[identifier]
		if before.kind!=after.kind or before.target_id!=after.target_id or before.ability_id!=after.ability_id:result.append(after)
	return result

static func _offensive(battle: BattleState, action: BattleAction)->bool:
	return action.kind==BattleAction.Kind.ABILITY and battle.catalog.abilities[action.ability_id]["kind"] in ["physical","magic"]

static func _count(battle: BattleState, plan: Dictionary)->int:
	var count:=0
	for action in plan.values():count+=1 if _offensive(battle,action) else 0
	return count

static func base_action(battle: BattleState, actor: Combatant) -> BattleAction:
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
