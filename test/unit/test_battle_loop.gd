extends "res://test/support/game_test.gd"


func test_three_and_four_member_battles_are_reproducible() -> void:
	for size in [3, 4]:
		var first: Variant = new_game(size)
		var second: Variant = new_game(size)
		if first == null or second == null:
			return
		var enemy_id := weakest_enemy(first)
		var a: Variant = first.start_battle([enemy_id, enemy_id], 123456)
		var b: Variant = second.start_battle([enemy_id, enemy_id], 123456)
		assert_eq(a.living(Combatant.Team.PARTY).size(), size)
		for turn in range(100):
			assert_eq(a.phase, b.phase)
			if a.phase != BattleState.Phase.INPUT:
				break
			for encounter in [a, b]:
				var targets: Array = encounter.living(Combatant.Team.ENEMY)
				for actor in encounter.living(Combatant.Team.PARTY):
					assert_eq(encounter.queue_action(BattleAction.strike(actor.id, targets[0].id)), "")
			var events_a: Array = a.resolve_round()
			var events_b: Array = b.resolve_round()
			# 同じ入力とシードで同じ行動順・ダメージを返す。
			assert_eq_deep(events_a, events_b)
			assert_eq_deep(a.snapshot(), b.snapshot())
		assert_eq(a.phase, BattleState.Phase.VICTORY)
		assert_false(a.can_resolve(), "勝利後は戦闘を続けない。")


func test_guard_damage_action_order_and_defeat() -> void:
	assert_eq(BattleMath.physical(20, 8), 32)
	assert_eq(BattleMath.physical(20, 8, 100, 0.5), 16)
	assert_eq(BattleMath.physical(1, 100), 1)
	var game: Variant = new_game(3)
	if game == null:
		return
	var encounter: Variant = game.start_battle([weakest_enemy(game)], 44)
	var enemy: Combatant = encounter.living(Combatant.Team.ENEMY)[0]
	enemy.attack = 1000
	enemy.speed = 999
	for actor in encounter.living(Combatant.Team.PARTY):
		actor.hp = 1
	for turn in range(5):
		if encounter.phase != BattleState.Phase.INPUT:
			break
		for actor in encounter.living(Combatant.Team.PARTY):
			encounter.queue_action(BattleAction.guard(actor.id))
		var events: Array = encounter.resolve_round()
		var first_damage := -1
		var last_guard := -1
		for i in range(events.size()):
			if events[i]["code"] == "guard":
				last_guard = i
			if first_damage < 0 and events[i]["code"] == "damage":
				first_damage = i
		assert_gt(first_damage, last_guard, "遅い味方の防御も攻撃より前に有効になる。")
	assert_eq(encounter.phase, BattleState.Phase.DEFEAT)
	assert_true(encounter.living(Combatant.Team.PARTY).is_empty())
