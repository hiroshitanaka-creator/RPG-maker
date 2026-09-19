extends "res://test/support/game_test.gd"


func test_all_eight_masteries_transform_and_apply_defined_effects() -> void:
	var definitions: Variant = new_game()
	if definitions == null:
		return
	var tested := 0
	for identifier in definitions.jobs:
		var definition: Dictionary = definitions.jobs[identifier]
		if definition["type"] != "monster":
			continue
		tested += 1
		assert_has(definition, "monster_form", "魔物化と解除の定義を持つこと。")
		if not definition.has("monster_form"):
			continue
		var form: Dictionary = definition["monster_form"]
		for key in ["stat_modifiers", "abilities", "release"]:
			assert_has(form, key)
		if not form.has_all(["stat_modifiers", "abilities", "release"]):
			continue
		assert_false(form["stat_modifiers"].is_empty())
		assert_false(form["abilities"].is_empty())
		var game: Variant = new_game()
		var actor_id := first_actor(game)
		assert_true(game.change_job(actor_id, identifier))
		assert_eq(member(game, actor_id)["monster_form"], "")
		master_job(game, actor_id, identifier)
		assert_eq(member(game, actor_id)["monster_form"], identifier)
		var baseline: Dictionary = game.base_effective_stats(actor_id)
		var transformed: Dictionary = game.effective_stats(actor_id)
		for stat in form["stat_modifiers"]:
			assert_eq(int(transformed[stat]), int(baseline[stat]) + int(form["stat_modifiers"][stat]), "定義どおりの能力変化。")
		for ability_id in form["abilities"]:
			assert_true(ability_id in game.available_abilities(actor_id), "魔物化で使用可能になる技。")
		assert_ne_deep(transformed, baseline)
		var unchanged: Dictionary = game.export_state()
		assert_false(game.release_monster_form(actor_id, "__wrong_condition__"))
		assert_eq_deep(game.export_state(), unchanged)
		assert_has(form["release"], "event")
		if form["release"].has("event"):
			assert_true(game.release_monster_form(actor_id, form["release"]["event"]), "定義した解除条件で復帰する。")
		assert_eq(member(game, actor_id)["monster_form"], "")
		assert_eq_deep(game.effective_stats(actor_id), game.base_effective_stats(actor_id))
	assert_eq(tested, 8)
