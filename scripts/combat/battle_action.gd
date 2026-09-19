class_name BattleAction
extends RefCounted

enum Kind { ATTACK, GUARD, ABILITY, ITEM }

var kind: Kind
var actor_id: String
var target_id: String
var ability_id: String


func _init(action_kind: Kind, actor: String, target: String = "", ability: String = "") -> void:
	kind = action_kind
	actor_id = actor
	target_id = target
	ability_id = ability


static func strike(actor: String, target: String) -> BattleAction:
	return BattleAction.new(Kind.ATTACK, actor, target)


static func guard(actor: String) -> BattleAction:
	return BattleAction.new(Kind.GUARD, actor, actor)


static func skill(actor: String, target: String, ability: String) -> BattleAction:
	return BattleAction.new(Kind.ABILITY, actor, target, ability)


static func potion(actor: String, target: String) -> BattleAction:
	return BattleAction.new(Kind.ITEM, actor, target)
