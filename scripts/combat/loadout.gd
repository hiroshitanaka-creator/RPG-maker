class_name Loadout
extends RefCounted


static func capacity(midgame_unlocked: bool, monster_form: bool) -> int:
	return mini(4, (3 if midgame_unlocked else 2) + (1 if monster_form else 0))


static func validate(learned: Array[String], equipped: Array[String], slots: int) -> String:
	if equipped.size() > slots:
		return "装着できるのは%d個までです。" % slots
	var used: Array[String] = []
	for ability_id in equipped:
		if not ability_id in learned:
			return "習得していないアビリティです。"
		if ability_id in used:
			return "同じアビリティは重複して装着できません。"
		used.append(ability_id)
	return ""
