extends "res://test/support/game_test.gd"


func test_victory_awards_jp_once_and_mastery_keeps_learned_abilities() -> void:
	var game: Variant = new_game()
	if game == null:
		return
	var actor_id := first_actor(game)
	var first_job := job_of_type(game, "human")
	var second_job := job_of_type(game, "human", first_job)
	assert_true(game.change_job(actor_id, first_job))
	var before := member(game, actor_id)
	win_battle(game)
	assert_gt(int(member(game, actor_id)["jp"].get(first_job, 0)), int(before["jp"].get(first_job, 0)))
	var after_win: Dictionary = game.export_state()
	assert_false(game.finish_battle(), "同じ勝利報酬を二重取得できない。")
	assert_eq_deep(game.export_state(), after_win)
	master_job(game, actor_id, first_job)
	var mastered := member(game, actor_id)
	for ability_id in game.jobs[first_job]["abilities"]:
		assert_true(ability_id in mastered["learned_abilities"])
	assert_true(game.change_job(actor_id, second_job))
	for ability_id in mastered["learned_abilities"]:
		assert_true(ability_id in member(game, actor_id)["learned_abilities"], "転職しても習得済みの技を失わない。")
	assert_true(first_job in member(game, actor_id)["mastered_jobs"])


func test_below_threshold_is_not_mastered_and_defeat_has_no_reward() -> void:
	var game: Variant = new_game()
	if game == null:
		return
	var actor_id := first_actor(game)
	var job_id := job_of_type(game, "human")
	assert_true(game.change_job(actor_id, job_id))
	assert_false(job_id in member(game, actor_id)["mastered_jobs"])
	var initial_jp: Dictionary = member(game, actor_id)["jp"].duplicate(true)
	var encounter: Variant = game.start_battle([weakest_enemy(game)], 18)
	assert_not_null(encounter)
	if encounter == null:
		return
	for actor in encounter.living(Combatant.Team.PARTY):
		actor.hp = 1
	for enemy in encounter.living(Combatant.Team.ENEMY):
		enemy.attack = 1000
	for turn in range(8):
		if encounter.phase != BattleState.Phase.INPUT:
			break
		for actor in encounter.living(Combatant.Team.PARTY):
			encounter.queue_action(BattleAction.guard(actor.id))
		encounter.resolve_round()
	assert_eq(encounter.phase, BattleState.Phase.DEFEAT)
	game.finish_battle()
	assert_eq_deep(member(game, actor_id)["jp"], initial_jp)
