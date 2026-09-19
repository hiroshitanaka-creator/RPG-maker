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
var _rng := RandomNumberGenerator.new()
var _events: Array[Dictionary] = []
var _ability_uses: Dictionary = {}


func _init(party: Array[Combatant], enemies: Array[Combatant], definitions: BattleCatalog, random_seed: int = 20260919) -> void:
	catalog = definitions
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
		if actor.team == team and actor.is_alive():
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
	phase = Phase.RESOLVING
	var actions: Array[BattleAction] = []
	actions.assign(queued.values())
	for enemy in living(Combatant.Team.ENEMY):
		var choices := living(Combatant.Team.PARTY)
		var target := choices[_rng.randi_range(0, choices.size() - 1)]
		var action := BattleAction.strike(enemy.id, target.id)
		for ability_id in enemy.equipped:
			var definition: Dictionary = catalog.abilities[ability_id]
			if definition["kind"] in ["physical", "magic"] and enemy.mp >= int(definition["cost"]):
				action = BattleAction.skill(enemy.id, target.id, ability_id)
				break
		actions.append(action)
	for actor in actors:
		actor.guard_rate = 1.0
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
	queued.clear()
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


func _before(a: BattleAction, b: BattleAction) -> bool:
	var priority_a := _priority(a)
	var priority_b := _priority(b)
	if priority_a != priority_b:
		return priority_a > priority_b
	var speed_a := actor_by_id(a.actor_id).speed
	var speed_b := actor_by_id(b.actor_id).speed
	if speed_a != speed_b:
		return speed_a > speed_b
	return a.actor_id < b.actor_id


func _priority(action: BattleAction) -> int:
	if action.kind == BattleAction.Kind.ABILITY:
		return int(catalog.abilities[action.ability_id]["priority"])
	return 0


func _is_guard(action: BattleAction) -> bool:
	return action.kind == BattleAction.Kind.GUARD or (action.kind == BattleAction.Kind.ABILITY and catalog.abilities[action.ability_id]["kind"] == "guard")


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
			if actor.mp < int(ability["cost"]):
				return "MPが足りません。"
			mode = ability["target"]
			effect = ability["kind"]
		_:
			return "未対応の行動です。"
	if mode == "enemy" and (target.team == actor.team or not target.is_alive()):
		return "生存している敵を選んでください。"
	if mode in ["ally", "fallen_ally"] and target.team != actor.team:
		return "味方を選んでください。"
	if mode == "self" and target.id != actor.id:
		return "自分に使うアビリティです。"
	if mode == "fallen_ally" and target.is_alive():
		return "蘇生は戦闘不能の味方に使います。"
	if mode in ["self", "ally"] and not target.is_alive():
		return "戦闘不能の味方には蘇生が必要です。"
	if effect == "heal" and target.hp == target.max_hp:
		return "対象のHPは満タンです。"
	if effect == "steal" and not target.loot_available:
		return "この相手からはすでに盗んでいます。"
	return ""


func _execute(original: BattleAction) -> void:
	var actor := actor_by_id(original.actor_id)
	if not actor.is_alive():
		_log("skip", "%sは戦闘不能のため行動できない。" % actor.display_name, actor.id)
		return
	var action := BattleAction.new(original.kind, original.actor_id, original.target_id, original.ability_id)
	var mode := "enemy"
	if action.kind == BattleAction.Kind.ABILITY:
		mode = catalog.abilities[action.ability_id]["target"]
	elif action.kind in [BattleAction.Kind.GUARD, BattleAction.Kind.ITEM]:
		mode = "ally"
	var target := actor_by_id(action.target_id)
	if mode == "enemy" and not target.is_alive():
		var opponents := living(Combatant.Team.ENEMY if actor.team == Combatant.Team.PARTY else Combatant.Team.PARTY)
		if opponents.is_empty():
			return
		target = opponents[0]
		action.target_id = target.id
		_log("retarget", "%sは対象を%sへ変更。" % [actor.display_name, target.display_name], actor.id, target.id)
	var error := _action_error(action)
	if not error.is_empty():
		_log("fizzle", "%s: %s 消費なし。" % [actor.display_name, error], actor.id, action.target_id)
		return
	match action.kind:
		BattleAction.Kind.GUARD:
			actor.guard_rate = 0.5
			_log("guard", "%sは防御。" % actor.display_name, actor.id, actor.id)
		BattleAction.Kind.ATTACK:
			_hit(actor, target, BattleMath.physical(actor.attack, target.defense, 100, target.guard_rate), "攻撃")
		BattleAction.Kind.ITEM:
			potions -= 1
			var amount := target.heal(50)
			_log("heal", "%sの回復薬: %sのHPが%d回復。" % [actor.display_name, target.display_name, amount], actor.id, target.id, amount)
		BattleAction.Kind.ABILITY:
			_use_ability(actor, target, catalog.abilities[action.ability_id])


func _use_ability(actor: Combatant, target: Combatant, ability: Dictionary) -> void:
	actor.mp -= int(ability["cost"])
	if not _ability_uses.has(actor.id):
		_ability_uses[actor.id] = []
	_ability_uses[actor.id].append(ability["id"])
	var title: String = ability["name"]
	var power: int = int(ability["power"])
	match ability["kind"]:
		"physical":
			for hit in range(int(ability["hits"])):
				if not target.is_alive():
					break
				_hit(actor, target, BattleMath.physical(actor.attack, target.defense, power, target.guard_rate), title)
		"magic":
			var weak: bool = ability["element"] in target.weaknesses
			_hit(actor, target, BattleMath.magical(actor.magic, target.resistance, power, weak, target.guard_rate), title + (" 弱点！" if weak else ""))
		"heal":
			var amount := target.heal(BattleMath.healing(actor.magic, power))
			_log("heal", "%sの%s: %sのHPが%d回復。" % [actor.display_name, title, target.display_name, amount], actor.id, target.id, amount)
		"revive":
			target.hp = clampi(ceili(float(target.max_hp) * float(power) / 100.0), 1, target.max_hp)
			_log("revive", "%sの蘇生: %sがHP%dで復帰。" % [actor.display_name, target.display_name, target.hp], actor.id, target.id, target.hp)
		"guard":
			actor.guard_rate = float(power) / 100.0
			_log("guard", "%sは堅守。" % actor.display_name, actor.id, actor.id)
		"steal":
			target.loot_available = false
			potions += 1
			_log("steal", "%sは%sから回復薬を盗んだ。" % [actor.display_name, target.display_name], actor.id, target.id, 1)


func _hit(actor: Combatant, target: Combatant, amount: int, title: String) -> void:
	var actual := target.damage(amount)
	_log("damage", "%sの%s: %sに%dダメージ。" % [actor.display_name, title, target.display_name, actual], actor.id, target.id, actual)
	if not target.is_alive():
		_log("fallen", "%sは倒れた。" % target.display_name, actor.id, target.id)


func _update_outcome() -> void:
	if living(Combatant.Team.ENEMY).is_empty():
		phase = Phase.VICTORY
	elif living(Combatant.Team.PARTY).is_empty():
		phase = Phase.DEFEAT


func snapshot() -> Dictionary:
	var members: Array[Dictionary] = []
	for actor in actors:
		members.append(actor.snapshot())
	return {"round": round_number, "phase": phase, "potions": potions, "actors": members}


func successful_abilities(actor_id: String) -> Array[String]:
	var result: Array[String] = []
	result.assign(_ability_uses.get(actor_id, []))
	return result


func _log(code: String, message: String, actor_id: String = "", target_id: String = "", amount: int = 0) -> void:
	_events.append({"code": code, "message": message, "actor": actor_id, "target": target_id, "amount": amount, "snapshot": snapshot()})
