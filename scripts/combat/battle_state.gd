class_name BattleState
extends RefCounted

enum Phase { INPUT, RESOLVING, VICTORY, DEFEAT, INVALID }

var phase: Phase = Phase.INPUT
var round_number: int = 1
var potions: int = 3
var last_error: String = ""
var actors: Array[Combatant] = []
var queued: Dictionary[String, BattleAction] = {}
var catalog: BattleCatalog
var effects: EncounterEffects
var _rng := RandomNumberGenerator.new()
var _events: Array[Dictionary] = []
var _ability_uses: Dictionary = {}
var _enemy_plan: Array[BattleAction] = []
var _enemy_plan_round: int = 0


func _init(party: Array[Combatant], enemies: Array[Combatant], definitions: BattleCatalog, random_seed: int = 20260919) -> void:
	catalog = definitions
	effects = EncounterEffects.new(self)
	actors.append_array(party)
	actors.append_array(enemies)
	_rng.seed = random_seed
	var identities: Array[String] = []
	for actor in actors:
		if actor.id in identities:
			phase = Phase.INVALID
			last_error = "戦闘参加者のIDが重複しています。"
		identities.append(actor.id)
	if party.is_empty() or enemies.is_empty() or not catalog.errors.is_empty():
		phase = Phase.INVALID
		last_error = "戦闘の初期データが不足しています。"


func actor_by_id(identifier: String) -> Combatant:
	for actor in actors:
		if actor.id == identifier:
			return actor
	return null


func living(team: Combatant.Team) -> Array[Combatant]:
	var result: Array[Combatant] = []
	for actor in actors:
		if actor.team == team and actor.is_alive() and not actor.is_device:
			result.append(actor)
	return result


func pending() -> Array[Combatant]:
	var result: Array[Combatant] = []
	for actor in living(Combatant.Team.PARTY):
		if not queued.has(actor.id):
			result.append(actor)
	return result


func can_resolve() -> bool:
	return phase == Phase.INPUT and not living(Combatant.Team.PARTY).is_empty() and pending().is_empty()


func queue_action(action: BattleAction) -> String:
	if phase != Phase.INPUT:
		return "現在は行動を選べません。"
	var actor := actor_by_id(action.actor_id)
	if actor == null or actor.team != Combatant.Team.PARTY:
		return "味方の行動を選んでください。"
	var error := _action_error(action)
	if not error.is_empty():
		return error
	# 同じ仲間の再選択は置換し、1ターンに二度行動させない。
	queued[action.actor_id] = BattleAction.new(action.kind, action.actor_id, action.target_id, action.ability_id)
	return ""


func clear_queue() -> void:
	if phase == Phase.INPUT:
		queued.clear()


func targets_for(actor_id: String, kind: BattleAction.Kind, ability_id: String = "") -> Array[Combatant]:
	var result: Array[Combatant] = []
	for target in actors:
		var action := BattleAction.new(kind, actor_id, target.id, ability_id)
		if _action_error(action).is_empty():
			result.append(target)
	return result


func resolve_round() -> Array[Dictionary]:
	_events = []
	if not can_resolve():
		last_error = "生存している仲間全員の行動を選んでください。"
		return _events
	last_error = ""
	_prepare_enemy_plan()
	phase = Phase.RESOLVING
	var actions: Array[BattleAction] = []
	actions.assign(queued.values())
	actions.append_array(_enemy_plan)
	for actor in actors:
		actor.guard_rate = 1.0
		if actor.team==Combatant.Team.ENEMY and reaction_count()>=3:
			actor.guard_rate=float(actor.tactics.get("chorus_guard",100))/100.0
	_log("round_start", "第%dターン" % round_number)
	actions.sort_custom(_before)
	# 防御は素早さに依存させず、攻撃の解決前に有効化する。
	for action in actions:
		if _is_guard(action):
			_execute(action)
	for action in actions:
		if _is_guard(action) or phase != Phase.RESOLVING:
			continue
		_execute(action)
		_update_outcome()
	effects.end_round()
	queued.clear()
	_enemy_plan_round = 0
	_enemy_plan.clear()
	for actor in actors:
		actor.guard_rate = 1.0
	if phase == Phase.RESOLVING:
		phase = Phase.INPUT
		round_number += 1
		_log("round_end", "次の行動を選んでください。")
	elif phase == Phase.VICTORY:
		_log("victory", "勝利！ 編成を変えて同じ相手と試せます。")
	elif phase == Phase.DEFEAT:
		_log("defeat", "全員が戦闘不能になりました。編成を見直せます。")
	return _events


func enemy_intents() -> Array[Dictionary]:
	if phase != Phase.INPUT:
		return []
	_prepare_enemy_plan()
	var result: Array[Dictionary] = []
	for action in _enemy_plan:
		var actor := actor_by_id(action.actor_id)
		var target := actor_by_id(action.target_id)
		result.append({"actor":actor.id,"name":actor.display_name,"target":target.id,
			"target_name":"味方全体" if catalog.abilities.get(action.ability_id,{}).get("target")=="enemies" else target.display_name,"ability":action.ability_id,
			"reaction_count":reaction_count(),"reaction_power":int(actor.tactics.get("reaction_power",0)),
			"reaction_speed":int(actor.tactics.get("reaction_speed",0)),
			"chorus_guard":int(actor.tactics.get("chorus_guard",100)),
			"guard_percent":enemy_guard_percent(actor),
			"action":"攻撃" if action.kind == BattleAction.Kind.ATTACK else str(catalog.abilities[action.ability_id]["name"])})
	return result


func _prepare_enemy_plan() -> void:
	if _enemy_plan_round == round_number or living(Combatant.Team.PARTY).is_empty():
		return
	_enemy_plan.clear()
	for enemy in living(Combatant.Team.ENEMY):
		_enemy_plan.append(_choose_enemy_action(enemy))
	_enemy_plan_round = round_number


func _choose_enemy_action(enemy: Combatant) -> BattleAction:
	var profile: String = enemy.tactics["profile"]
	if profile in ["healer","reviver","mixed"]:
		for kind in ["revive","heal"]:
			for identifier in enemy.equipped:
				var definition: Dictionary = catalog.abilities[identifier]
				if definition["kind"] != kind or enemy.mp < int(definition["cost"]):
					continue
				var targets := targets_for(enemy.id,BattleAction.Kind.ABILITY,identifier)
				targets.sort_custom(func(a: Combatant,b: Combatant) -> bool:
					var left := a.hp * b.max_hp
					var right := b.hp * a.max_hp
					return a.id < b.id if left == right else left < right)
				for target in targets:
					if kind == "revive" or target.hp * 100 <= target.max_hp * int(enemy.tactics["heal_below"]):
						return BattleAction.skill(enemy.id,target.id,identifier)
	if profile == "guardian" and (round_number-1) % int(enemy.tactics["guard_every"]) == 0:
		for identifier in enemy.equipped:
			var definition: Dictionary = catalog.abilities[identifier]
			if definition["kind"] == "guard" and enemy.mp >= int(definition["cost"]):
				return BattleAction.skill(enemy.id,enemy.id,identifier)
	var opponents := living(Combatant.Team.PARTY)
	var target: Combatant
	var focus: String=enemy.tactics["focus"]
	if focus!="random" and int(enemy.tactics.get("focus_variation",0))>0 and _rng.randi_range(1,100)<=int(enemy.tactics["focus_variation"]):focus="random"
	match focus:
		"lowest_hp":
			opponents.sort_custom(func(a: Combatant,b: Combatant) -> bool: return a.id < b.id if a.hp == b.hp else a.hp < b.hp)
			target = opponents[0]
		"highest_magic":
			opponents.sort_custom(func(a: Combatant,b: Combatant) -> bool: return a.id < b.id if a.magic == b.magic else a.magic > b.magic)
			target = opponents[0]
		_:
			target = opponents[_rng.randi_range(0,opponents.size()-1)]
	var offensive: Array[String] = []
	for identifier in enemy.equipped:
		var definition: Dictionary = catalog.abilities[identifier]
		if definition["kind"] in ["physical","magic"] and enemy.mp >= int(definition["cost"]):
			offensive.append(identifier)
	if not offensive.is_empty():
		var index := (round_number-1) % offensive.size() if profile == "caster" else 0
		return BattleAction.skill(enemy.id,target.id,offensive[index])
	return BattleAction.strike(enemy.id,target.id)


func reaction_count() -> int:
	var count:=0
	for action in queued.values():
		if action.kind==BattleAction.Kind.ABILITY and catalog.abilities[action.ability_id]["kind"] in ["physical","magic"]:count+=1
	return count


func effective_speed(actor: Combatant, count: int = -1) -> int:
	var declared:=reaction_count() if count<0 else count
	return actor.speed + (int(actor.tactics.get("reaction_speed",0))*declared if actor.team==Combatant.Team.ENEMY else 0)


func reaction_multiplier(actor: Combatant, count: int = -1) -> float:
	var declared:=reaction_count() if count<0 else count
	return 1.0 + (float(actor.tactics.get("reaction_power",0))*declared/100.0 if actor.team==Combatant.Team.ENEMY else 0.0)


func has_reactive_enemy() -> bool:
	for actor in living(Combatant.Team.ENEMY):
		if int(actor.tactics.get("reaction_power",0))>0 or int(actor.tactics.get("chorus_guard",100))<100:return true
	return false


func enemy_guard_percent(actor: Combatant) -> int:
	var rate:=int(actor.tactics.get("chorus_guard",100)) if reaction_count()>=3 else 100
	for action in _enemy_plan:
		if action.actor_id!=actor.id:continue
		if action.kind==BattleAction.Kind.GUARD:rate=mini(rate,50)
		elif action.kind==BattleAction.Kind.ABILITY and catalog.abilities[action.ability_id]["kind"]=="guard":rate=mini(rate,int(catalog.abilities[action.ability_id]["power"]))
	return rate


func forecast_damage(target_id: String, guarded: bool = false, count: int = -1, before_action_only: bool = true, attacker_id: String = "") -> int:
	_prepare_enemy_plan()
	var target:=actor_by_id(target_id)
	if target==null:return 0
	var total:=0
	var defense_rate:=0.5 if guarded else 1.0
	for action in _enemy_plan:
		if action.target_id!=target_id and catalog.abilities.get(action.ability_id,{}).get("target")!="enemies":continue
		if not attacker_id.is_empty() and action.actor_id!=attacker_id:continue
		var enemy:=actor_by_id(action.actor_id)
		var skill: Dictionary=catalog.abilities.get(action.ability_id,{})
		var speed:=effective_speed(enemy,count)
		if before_action_only and int(skill.get("priority",0))<=0 and (speed<target.speed or (speed==target.speed and enemy.id>target.id)):continue
		var amount:=0
		var hits:=int(skill.get("hits",1))
		match skill.get("kind","physical"):
			"physical":amount=BattleMath.physical(enemy.attack,target.defense,int(skill.get("power",100)),defense_rate)
			"magic":amount=BattleMath.magical(enemy.magic,target.resistance,int(skill["power"]),str(skill["element"]) in target.weaknesses,defense_rate)
		total+=ceili(amount*reaction_multiplier(enemy,count))*hits
	return total


func _before(a: BattleAction, b: BattleAction) -> bool:
	var priority_a := _priority(a)
	var priority_b := _priority(b)
	if priority_a != priority_b:
		return priority_a > priority_b
	var speed_a := effective_speed(actor_by_id(a.actor_id))
	var speed_b := effective_speed(actor_by_id(b.actor_id))
	if speed_a != speed_b:
		return speed_a > speed_b
	return a.actor_id < b.actor_id


func _priority(action: BattleAction) -> int:
	if action.kind == BattleAction.Kind.ABILITY:
		return int(catalog.abilities[action.ability_id]["priority"])
	return 0


func _is_guard(action: BattleAction) -> bool:
	return action.kind == BattleAction.Kind.GUARD or (action.kind == BattleAction.Kind.ABILITY and catalog.abilities[action.ability_id]["kind"] in ["guard","deflect_physical","deflect_magic","cover"])


func _action_error(action: BattleAction) -> String:
	var actor := actor_by_id(action.actor_id)
	if actor == null or not actor.is_alive():
		return "戦闘不能の仲間は行動できません。"
	var target := actor_by_id(action.target_id)
	if target == null:
		return "対象が見つかりません。"
	var mode := "enemy"
	var effect := "physical"
	match action.kind:
		BattleAction.Kind.ATTACK:
			pass
		BattleAction.Kind.OBSERVE:
			mode = "enemy"
			effect = "observe"
		BattleAction.Kind.GUARD:
			mode = "self"
			effect = "guard"
		BattleAction.Kind.ITEM:
			mode = "ally"
			effect = "heal"
			if potions <= 0:
				return "回復薬がありません。"
		BattleAction.Kind.ABILITY:
			if not catalog.abilities.has(action.ability_id) or not action.ability_id in actor.equipped or not action.ability_id in actor.learned:
				return "装着していないアビリティです。"
			var ability: Dictionary = catalog.abilities[action.ability_id]
			if actor.mp < effects.cost(actor,ability):
				return "MPが足りません。"
			mode = ability["target"]
			effect = ability["kind"]
		_:
			return "未対応の行動です。"
	if mode in ["enemy","enemies"] and (target.team == actor.team or not target.is_alive()):
		return "生存している敵を選んでください。"
	if mode in ["ally", "allies", "fallen_ally"] and target.team != actor.team:
		return "味方を選んでください。"
	if mode == "self" and target.id != actor.id:
		return "自分に使うアビリティです。"
	if mode == "fallen_ally" and target.is_alive():
		return "蘇生は戦闘不能の味方に使います。"
	if mode in ["self", "ally", "allies"] and not target.is_alive():
		return "戦闘不能の味方には蘇生が必要です。"
	if effect == "heal" and target.hp == target.max_hp:
		return "対象のHPは満タンです。"
	if effect == "steal" and (not target.loot_available or target.is_device):
		return "この相手からはすでに盗んでいます。"
	return effects.validate(action)


func _execute(original: BattleAction) -> void:
	var actor := actor_by_id(original.actor_id)
	if not actor.is_alive():
		effects.begin_action(actor,original)
		_log("skip", "%sは戦闘不能のため行動できない。" % actor.display_name, actor.id)
		return
	var action := BattleAction.new(original.kind,original.actor_id,original.target_id,original.ability_id)
	var mode: String = catalog.abilities[action.ability_id]["target"] if action.kind==BattleAction.Kind.ABILITY else "enemy"
	if action.kind in [BattleAction.Kind.GUARD,BattleAction.Kind.ITEM]:mode="ally"
	var target := actor_by_id(action.target_id)
	if mode in ["enemy","enemies"] and not target.is_alive():
		var opponents := living(Combatant.Team.ENEMY if actor.team==Combatant.Team.PARTY else Combatant.Team.PARTY)
		if opponents.is_empty():return
		target=opponents[0];action.target_id=target.id
		_log("retarget","%sは対象を%sへ変更。" % [actor.display_name,target.display_name],actor.id,target.id)
	var error := _action_error(action)
	if not effects.begin_action(actor,action):return
	if not error.is_empty():
		_log("fizzle", "%s: %s 消費なし。" % [actor.display_name,error],actor.id,action.target_id)
		effects.finish_action(actor,action)
		return
	effects.current["executed"]=true
	match action.kind:
		BattleAction.Kind.GUARD:
			actor.guard_rate=minf(actor.guard_rate,0.5)
			_log("guard","%sは防御。" % actor.display_name,actor.id,actor.id)
		BattleAction.Kind.OBSERVE:effects.observe(target)
		BattleAction.Kind.ATTACK:_attack(actor,target,{"kind":"physical","power":100,"hits":1,"element":"none","target":"enemy"},"攻撃")
		BattleAction.Kind.ITEM:
			potions-=1
			var amount:=target.heal(catalog.potion_healing)
			_log("heal","%sの回復薬: %sのHPが%d回復。" % [actor.display_name,target.display_name,amount],actor.id,target.id,amount)
		BattleAction.Kind.ABILITY:_use_ability(actor,target,catalog.abilities[action.ability_id])
	effects.finish_action(actor,action)


func _attack(actor: Combatant,target: Combatant,ability: Dictionary,title: String) -> void:
	var area: bool=ability.get("target")=="enemies"
	var targets: Array[Combatant]=[]
	if area:targets.assign(living(Combatant.Team.ENEMY if actor.team==Combatant.Team.PARTY else Combatant.Team.PARTY))
	else:targets.append(target)
	for original in targets:
		var receiver:=effects.redirect(original,ability["kind"]=="physical",area)
		var weapons: Array=actor.weapons if ability["kind"]=="physical" and not ability.get("natural",false) and not actor.weapons.is_empty() else [{}]
		if "twin_grip" not in actor.equipped:weapons=weapons.slice(0,1)
		for weapon in weapons:
			effects.current["on_hit"]=weapon.get("on_hit",ability.get("on_hit",{}))
			for hit in range(int(ability.get("hits",1))):
				if not receiver.is_alive():break
				_hit(actor,receiver,effects.damage(actor,receiver,ability,weapon),title)


func _use_ability(actor: Combatant,target: Combatant,ability: Dictionary) -> void:
	var paid:=effects.cost(actor,ability)
	actor.mp-=paid
	effects.current["paid"]=paid
	if not _ability_uses.has(actor.id):_ability_uses[actor.id]=[]
	_ability_uses[actor.id].append(ability["id"])
	if effects.apply(actor,target,ability):return
	var title: String=ability["name"]
	var power: int=int(ability["power"])
	match ability["kind"]:
		"physical","magic":_attack(actor,target,ability,title)
		"heal":
			var amount:=target.heal(BattleMath.healing(actor.magic,power))
			_log("heal","%sの%s: %sのHPが%d回復。" % [actor.display_name,title,target.display_name,amount],actor.id,target.id,amount)
		"revive":
			target.hp=clampi(ceili(float(target.max_hp)*float(power)/100.0),1,target.max_hp)
			_log("revive","%sの蘇生: %sがHP%dで復帰。" % [actor.display_name,target.display_name,target.hp],actor.id,target.id,target.hp)
		"guard":
			actor.guard_rate=minf(actor.guard_rate,float(power)/100.0)
			_log("guard","%sは堅守。" % actor.display_name,actor.id,actor.id)
		"steal":
			target.loot_available=false
			potions+=1
			_log("steal","%sは%sから回復薬を盗んだ。" % [actor.display_name,target.display_name],actor.id,target.id,1)


func _hit(actor: Combatant, target: Combatant, amount: int, title: String, reactive: bool = true) -> void:
	var actual := target.damage(ceili(amount*reaction_multiplier(actor)))
	_log("damage", "%sの%s: %sに%dダメージ。" % [actor.display_name, title, target.display_name, actual], actor.id, target.id, actual)
	effects.after_hit(actor,target,actual,reactive)
	if not target.is_alive():
		_log("fallen", "%sは倒れた。" % target.display_name, actor.id, target.id)


func _update_outcome() -> void:
	effects.flush_reactions()
	if living(Combatant.Team.PARTY).is_empty():
		phase = Phase.DEFEAT
	elif living(Combatant.Team.ENEMY).is_empty():
		phase = Phase.VICTORY


func snapshot() -> Dictionary:
	var members: Array[Dictionary] = []
	for actor in actors:
		members.append(actor.snapshot())
	return {"round": round_number, "phase": phase, "potions": potions, "actors": members, "effects": effects.snapshot()}


func successful_abilities(actor_id: String) -> Array[String]:
	var result: Array[String] = []
	result.assign(_ability_uses.get(actor_id, []))
	return result


func _log(code: String, message: String, actor_id: String = "", target_id: String = "", amount: int = 0) -> void:
	_events.append({"code": code, "message": message, "actor": actor_id, "target": target_id, "amount": amount, "snapshot": snapshot()})


func preview_action(action: BattleAction) -> Dictionary:
	if phase!=Phase.INPUT:return {"allowed":false,"reason":"行動入力中ではありません。"}
	var error := _action_error(action)
	if not error.is_empty():return {"allowed":false,"reason":error}
	var party: Array[Combatant]=[]
	var foes: Array[Combatant]=[]
	for actor in actors:
		if actor.team==Combatant.Team.PARTY:party.append(actor.copy())
		else:foes.append(actor.copy())
	var simulated := BattleState.new(party,foes,catalog,0)
	simulated.round_number=round_number;simulated.potions=potions
	simulated._rng.state=_rng.state
	simulated.effects.states=effects.states.duplicate(true)
	simulated.effects.rules=effects.rules.duplicate(true)
	simulated.effects.knowledge=effects.knowledge.duplicate(true)
	simulated.effects.field=effects.field.duplicate(true)
	simulated.effects._deaths=effects._deaths.duplicate()
	simulated.effects.phase_index=effects.phase_index
	simulated._enemy_plan_round=_enemy_plan_round
	for planned in _enemy_plan:simulated._enemy_plan.append(BattleAction.new(planned.kind,planned.actor_id,planned.target_id,planned.ability_id))
	for actor in party:
		var planned: BattleAction=queued.get(actor.id,BattleAction.guard(actor.id))
		if actor.id==action.actor_id:planned=action
		simulated.queued[actor.id]=BattleAction.new(planned.kind,planned.actor_id,planned.target_id,planned.ability_id)
	var before_mp:=actor_by_id(action.actor_id).mp
	var events:=simulated.resolve_round()
	var damage:=0
	for event in events:
		if event["code"]=="damage" and event["actor"]==action.actor_id:damage+=int(event["amount"])
	var known: bool=effects.rules.is_empty() or effects.knowledge.get(effects.rules.get("id",""),{}).get("confirmed",false)
	return {"allowed":true,"reason":"","cost":effects.cost(actor_by_id(action.actor_id),catalog.abilities[action.ability_id]) if action.kind==BattleAction.Kind.ABILITY else 0,
		"predicted_damage":damage if known else -1,"knowledge_confirmed":known,"remaining_mp":simulated.actor_by_id(action.actor_id).mp,"mp_change":before_mp-simulated.actor_by_id(action.actor_id).mp,
		"condition":"予約と予兆がこの順で実行された場合。" if known else "敵の機構が未確認のため確定ダメージを伏せています。"}
