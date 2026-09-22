extends RefCounted
const Base=preload("res://tools/counterplay_policy.gd")
## 表示される装置・HP・装着だけを読む。シードと内部の防御値は読まない。
static func action(battle: BattleState,actor: Combatant) -> BattleAction:
	var fallback: BattleAction=Base.base_action(battle,actor)
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
		if rule=="residue":
			var party:=battle.living(Combatant.Team.PARTY)
			party.sort_custom(func(a:Combatant,b:Combatant)->bool:return a.hp>b.hp if a.hp!=b.hp else a.id<b.id)
			if party[-1].hp<=25 and battle.potions>0:return BattleAction.potion(actor.id,party[-1].id)
			if actor.id!=party[0].id:return BattleAction.guard(actor.id)
	if not battle._action_error(fallback).is_empty():return BattleAction.guard(actor.id)
	return fallback
