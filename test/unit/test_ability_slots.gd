extends "res://test/support/game_test.gd"


func test_capacity_unknown_ability_and_effect_removal() -> void:
	var game: Variant = new_game()
	if game == null:
		return
	var actor_id := first_actor(game)
	assert_false(game.equip_ability(actor_id, "__not_learned__"))
	var human_jobs: Array[String] = []
	for identifier in game.jobs:
		if game.jobs[identifier]["type"] == "human":
			human_jobs.append(identifier)
	for identifier in human_jobs.slice(0, 3):
		master_job(game, actor_id, identifier)
	var state: Dictionary = game.export_state()
	for actor in state["party"]:
		actor["hp"] = actor["max_hp"]
		if actor["id"] == actor_id:
			actor["equipped_abilities"] = []
	assert_true(game.import_state(state))
	var learned: Array = member(game, actor_id)["learned_abilities"]
	var limit: int = game.slot_limit(actor_id)
	assert_gt(limit, 0)
	assert_gt(learned.size(), limit, "上限超過を実際に試せる習得状態を作る。")
	if learned.size() <= limit:
		return
	for i in range(limit):
		assert_true(game.equip_ability(actor_id, learned[i]))
	var full: Dictionary = game.export_state()
	assert_false(game.equip_ability(actor_id, learned[limit]))
	# 失敗時に装着状態が変わらない。
	assert_eq_deep(game.export_state(), full)
	for ability_id in member(game, actor_id)["equipped_abilities"].duplicate():
		assert_true(game.unequip_ability(actor_id, ability_id))
	var damaging_ability := ""
	for ability_id in learned:
		if game.abilities[ability_id]["kind"] in ["physical", "magic"]:
			damaging_ability = ability_id
			break
	assert_ne(damaging_ability, "", "戦闘効果のある習得技が必要です。")
	if damaging_ability.is_empty():
		return
	assert_true(game.equip_ability(actor_id, damaging_ability))
	var equipped_battle: Variant = game.start_battle([weakest_enemy(game)], 33)
	var enemy_id: String = equipped_battle.living(Combatant.Team.ENEMY)[0].id
	var action := BattleAction.skill(actor_id, enemy_id, damaging_ability)
	assert_eq(equipped_battle.queue_action(action), "", "装着した技は戦闘で使用できる。")
	for actor in equipped_battle.pending():
		equipped_battle.queue_action(BattleAction.guard(actor.id))
	var events: Array = equipped_battle.resolve_round()
	assert_true(events.any(func(event: Dictionary) -> bool: return event["code"] == "damage" and event["actor"] == actor_id), "実際のダメージへ効果が現れる。")
	for turn in range(100):
		if equipped_battle.phase != BattleState.Phase.INPUT:
			break
		var targets: Array = equipped_battle.living(Combatant.Team.ENEMY)
		for actor in equipped_battle.pending():
			equipped_battle.queue_action(BattleAction.strike(actor.id, targets[0].id))
		equipped_battle.resolve_round()
	assert_eq(equipped_battle.phase, BattleState.Phase.VICTORY)
	assert_true(game.finish_battle())
	assert_true(game.unequip_ability(actor_id, damaging_ability))
	var plain_battle: Variant = game.start_battle([weakest_enemy(game)], 33)
	var enemy_before: int = plain_battle.actor_by_id(enemy_id).hp
	var mp_before: int = plain_battle.actor_by_id(actor_id).mp
	assert_ne(plain_battle.queue_action(action), "", "外した技は戦闘計算へ入れない。")
	assert_false(plain_battle.queued.has(actor_id))
	assert_eq(plain_battle.actor_by_id(enemy_id).hp, enemy_before)
	assert_eq(plain_battle.actor_by_id(actor_id).mp, mp_before)


func test_slot_capacity_is_bounded_and_equipment_is_not_duplicated() -> void:
	assert_eq(Loadout.capacity(false, false), 2)
	assert_eq(Loadout.capacity(true, false), 3)
	assert_eq(Loadout.capacity(false, true), 3)
	assert_eq(Loadout.capacity(true, true), 4)
	var learned: Array[String] = ["a", "b", "c"]
	var too_many: Array[String] = ["a", "b", "c"]
	var duplicate: Array[String] = ["a", "a"]
	var unknown: Array[String] = ["unknown"]
	assert_ne(Loadout.validate(learned, too_many, 2), "")
	assert_ne(Loadout.validate(learned, duplicate, 2), "")
	assert_ne(Loadout.validate(learned, unknown, 2), "")
