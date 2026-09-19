extends "res://test/support/game_test.gd"


func test_exact_job_counts_and_schema() -> void:
	assert_true(DirAccess.dir_exists_absolute("res://data/jobs"), "data/jobsに実データが必要です。")
	if not DirAccess.dir_exists_absolute("res://data/jobs"):
		return
	var files := DirAccess.get_files_at("res://data/jobs")
	var ids: Array[String] = []
	var counts := {"human": 0, "monster": 0}
	var required := ["id", "name", "type", "stat_growth", "abilities", "mastery_cost"]
	for filename in files:
		if not filename.ends_with(".json"):
			continue
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/jobs/" + filename))
		assert_typeof(parsed, TYPE_DICTIONARY, filename)
		if not parsed is Dictionary:
			continue
		var job: Dictionary = parsed
		for key in required:
			assert_has(job, key, "%sの必須キー: %s" % [filename, key])
		if not required.all(func(key: String) -> bool: return job.has(key)):
			continue
		assert_typeof(job["id"], TYPE_STRING)
		assert_false(str(job["id"]).is_empty())
		assert_false(str(job["id"]) in ids, "IDを重複させない。")
		ids.append(str(job["id"]))
		assert_false(str(job["name"]).is_empty())
		assert_has(counts, job["type"], "区分はhumanまたはmonster。")
		if counts.has(job["type"]):
			counts[job["type"]] += 1
		assert_typeof(job["stat_growth"], TYPE_DICTIONARY)
		if job["stat_growth"] is Dictionary:
			assert_false(job["stat_growth"].is_empty())
			for growth in job["stat_growth"].values():
				assert_true((growth is int or growth is float) and float(growth) >= 0.0 and float(growth) == floor(float(growth)))
		assert_typeof(job["abilities"], TYPE_ARRAY)
		if job["abilities"] is Array:
			assert_false(job["abilities"].is_empty())
			var skill_ids: Array[String] = []
			for ability in job["abilities"]:
				assert_typeof(ability, TYPE_STRING)
				assert_false(str(ability).is_empty())
				assert_false(str(ability) in skill_ids)
				skill_ids.append(str(ability))
		assert_true((job["mastery_cost"] is int or job["mastery_cost"] is float) and float(job["mastery_cost"]) > 0.0 and float(job["mastery_cost"]) == floor(float(job["mastery_cost"])))
	assert_eq(ids.size(), 20, "人間12＋モンスター8を定義する。")
	assert_eq(counts["human"], 12)
	assert_eq(counts["monster"], 8)


func test_runtime_uses_all_job_definitions_and_valid_abilities() -> void:
	var game: Variant = new_game()
	if game == null:
		return
	assert_eq(game.jobs.size(), 20)
	for job in game.jobs.values():
		for ability_id in job["abilities"]:
			assert_has(game.abilities, ability_id, "定義した職業の技を実際の戦闘で参照できること。")
