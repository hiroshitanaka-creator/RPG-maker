extends RefCounted
const Base=preload("res://tools/counterplay_policy.gd")
static func adjustments(battle: BattleState) -> Array[BattleAction]:
	var result: Array[BattleAction]=Base.adjustments(battle)
	for change in result:battle.queue_action(change)
	if battle.effects.rules.is_empty():return result
	for actor in battle.living(Combatant.Team.PARTY):
		if battle.forecast_damage(actor.id,false,-1,true)*2<actor.hp:continue
		var defense:=BattleAction.guard(actor.id)
		if "firm_guard" in actor.equipped:
			var firm:=BattleAction.skill(actor.id,actor.id,"firm_guard")
			if battle._action_error(firm).is_empty():defense=firm
		result.append(defense)
	return result
## 表示される装置・HP・装着だけを読む。シードと内部の防御値は読まない。
static func action(battle: BattleState,actor: Combatant) -> BattleAction:
	var projected: Dictionary={}
	var potions_left: int=battle.potions
	for ally in battle.living(Combatant.Team.PARTY):projected[ally.id]=ally.hp
	for queued in battle.queued.values():
		if not projected.has(queued.target_id):continue
		if queued.kind==BattleAction.Kind.ITEM:projected[queued.target_id]+=battle.catalog.potion_healing;potions_left-=1
		if queued.kind==BattleAction.Kind.ABILITY and battle.catalog.abilities[queued.ability_id]["kind"]=="heal":
			projected[queued.target_id]+=BattleMath.healing(battle.actor_by_id(queued.actor_id).magic,int(battle.catalog.abilities[queued.ability_id]["power"]))
	var allies:=battle.living(Combatant.Team.PARTY)
	allies.sort_custom(func(a:Combatant,b:Combatant)->bool:return projected[a.id]*b.max_hp<projected[b.id]*a.max_hp)
	for ally in allies:
		if projected[ally.id]*3>=ally.max_hp*2:continue
		for skill in actor.equipped:
			if battle.catalog.abilities[skill]["kind"]=="heal":
				var healing:=BattleAction.skill(actor.id,ally.id,skill)
				if battle._action_error(healing).is_empty():return healing
		if projected[ally.id]*5<ally.max_hp*2 and potions_left>0:
			var potion:=BattleAction.potion(actor.id,ally.id)
			if battle._action_error(potion).is_empty():return potion
	var fallback: BattleAction=Base.base_action(battle,actor)
	if fallback.kind==BattleAction.Kind.ITEM or (fallback.kind==BattleAction.Kind.ABILITY and battle.catalog.abilities[fallback.ability_id]["kind"]=="heal"):
		fallback=BattleAction.strike(actor.id,battle.living(Combatant.Team.ENEMY)[0].id)
	if not battle._action_error(fallback).is_empty():fallback=BattleAction.strike(actor.id,battle.living(Combatant.Team.ENEMY)[0].id)
	if fallback.kind in [BattleAction.Kind.ITEM,BattleAction.Kind.GUARD]:return fallback
	if fallback.kind==BattleAction.Kind.ABILITY and battle.catalog.abilities[fallback.ability_id]["kind"] in ["heal","revive"]:return fallback
	for target in battle.actors:
		if target.is_device and target.is_alive():return BattleAction.strike(actor.id,target.id)
	if not battle.effects.rules.is_empty():
		var rule: String=battle.effects.rules["id"]
		if rule=="residue" and "disarm" in actor.equipped:
			for target in battle.living(Combatant.Team.ENEMY):
				var remove:=BattleAction.skill(actor.id,target.id,"disarm")
				if battle._action_error(remove).is_empty():return remove
		var armed: bool=battle.living(Combatant.Team.ENEMY).any(func(foe:Combatant)->bool:return battle.effects.state(foe.id).get("death_armed",false))
		if rule=="residue" and armed:
			var party:=battle.living(Combatant.Team.PARTY)
			party.sort_custom(func(a:Combatant,b:Combatant)->bool:return a.hp>b.hp if a.hp!=b.hp else a.id<b.id)
			if projected[party[-1].id]<=25 and potions_left>0:return BattleAction.potion(actor.id,party[-1].id)
			var striker: String=party[0].id
			var best: int=-1
			var target:=battle.living(Combatant.Team.ENEMY)[0]
			for member in party:
				var damage:=BattleMath.physical(member.attack,target.defense)
				for id in member.equipped:
					var definition: Dictionary=battle.catalog.abilities[id]
					if member.mp<battle.effects.cost(member,definition):continue
					if definition["kind"]=="physical":damage=maxi(damage,BattleMath.physical(member.attack,target.defense,int(definition["power"]))*int(definition["hits"]))
					elif definition["kind"]=="magic":damage=maxi(damage,BattleMath.magical(member.magic,target.resistance,int(definition["power"]),definition["element"] in target.weaknesses))
				if damage>best:best=damage;striker=member.id
			if actor.id!=striker:return BattleAction.guard(actor.id)
	if "restore_mp" in actor.equipped and actor.mp<4:
		var restore:=BattleAction.skill(actor.id,actor.id,"restore_mp")
		if battle._action_error(restore).is_empty():return restore
	if not battle._action_error(fallback).is_empty():return BattleAction.guard(actor.id)
	return fallback
