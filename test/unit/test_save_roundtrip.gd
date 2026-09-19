extends "res://test/support/game_test.gd"


func test_save_load_preserves_all_required_state_for_three_and_four_members() -> void:
	for size in [3, 4]:
		var game: Variant = new_game(size)
		if game == null:
			return
		var actor_id := first_actor(game)
		master_job(game, actor_id, job_of_type(game, "human"))
		master_job(game, actor_id, job_of_type(game, "monster"))
		var learned: Array = member(game, actor_id)["learned_abilities"]
		assert_false(learned.is_empty())
		if not learned.is_empty():
			game.equip_ability(actor_id, learned[0])
		var supplied: Dictionary = game.export_state()
		supplied["inventory"]["potion"] = 7
		supplied["progress_flags"]["save_roundtrip_fixture"] = true
		assert_true(game.import_state(supplied))
		var before: Dictionary = game.export_state()
		var path := "user://scope_lock_roundtrip_%d.json" % size
		assert_true(game.save_game(path), "実ファイルへ保存する。")
		assert_true(FileAccess.file_exists(path))
		var restored: Variant = new_game(size)
		assert_true(restored.load_game(path))
		# 全フィールドが往復で完全一致する。
		assert_eq_deep(restored.export_state(), before)
		assert_ne(member(restored, actor_id)["monster_form"], "")


func test_invalid_save_does_not_destroy_current_state() -> void:
	var game: Variant = new_game()
	if game == null:
		return
	var before: Dictionary = game.export_state()
	var path := "user://scope_lock_invalid_save.json"
	var file := FileAccess.open(path, FileAccess.WRITE)
	assert_not_null(file)
	if file == null:
		return
	file.store_string("{broken")
	file.close()
	assert_false(game.load_game(path))
	assert_eq_deep(game.export_state(), before)
