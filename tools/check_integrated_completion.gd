extends "res://tools/check_integrated_progression.gd"

var measurements: Array[Dictionary] = []

func _initialize() -> void:
	var game := GameSession.new()
	game.new_game(4)
	# 未実装の入口を検査の成功として扱わない。
	if not game.has_method("mastery_bonus") or not game.has_method("mastery_bonus_text"):
		failures.append("D04: 常時特性の合計APIと表示が未実装")
	else:
		check_totals(game)
	check_erosion_profiles()
	var report := {"status":"PASS" if failures.is_empty() else "FAIL", "failures":failures,
		"cases":cases, "erosion_profiles":measurements,
		"scope":"D04の合計とD21の固定550戦。全編の遭遇分布・人間の選択頻度・60時間の実測の代用にはしない。"}
	PlaySessionMetrics.write_json("res://docs/verification/integrated-completion-current.json", report)
	for failure in failures: printerr("INTEGRATED_COMPLETION_FAIL: " + failure)
	print("INTEGRATED_COMPLETION_RESULT: cases=%d failures=%d" % [cases, failures.size()])
	quit(0 if failures.is_empty() else 1)

func check_totals(game: GameSession) -> void:
	var expected := {"hp":0,"mp":0,"attack":0,"defense":0,"magic":0,"resistance":0,"speed":0}
	check(game.call("mastery_bonus", "pc_01") == expected, "未取得の常時特性は全項目0")
	var baseline := game.base_effective_stats("pc_01")
	var fixture := game.export_state()
	# 到達性ではなく、全職の組合せにおける能力計算を検査する明示入力。
	for job_id in game.jobs:
		fixture["party"][0]["mastered_jobs"].append(job_id)
		fixture["party"][0]["jp"][job_id] = game.jobs[job_id]["mastery_cost"]
		for stat in game.jobs[job_id]["stat_growth"]:
			expected[stat] += int(game.jobs[job_id]["stat_growth"][stat])
		fixture["party"][0]["max_hp"] = baseline["hp"] + expected["hp"]
		fixture["party"][0]["max_mp"] = baseline["mp"] + expected["mp"]
		check(game.import_state(fixture), "累積マスター入力: " + job_id)
		check(game.call("mastery_bonus", "pc_01") == expected, "合計は取得済み職データの和: " + job_id)
		var actual := game.base_effective_stats("pc_01")
		for stat in expected:
			check(actual[stat] - baseline[stat] == expected[stat], "合計と戦闘用能力の寄与が一致: " + stat)
		cases += 1
	check(expected == {"hp":48,"mp":0,"attack":12,"defense":8,"magic":12,"resistance":8,"speed":0}, "既存20職の総予算を維持")
	var stable := game.export_state()
	check("HP +48" in game.call("mastery_bonus_text", "pc_01"), "表示に取得済みHP合計")
	check(game.export_state() == stable, "合計の参照は状態を変更しない")
	check(game.change_job("pc_01", "warrior"), "取得済み職へ転職")
	game.rest()
	fight(game)
	check(game.call("mastery_bonus", "pc_01") == expected and actor(game)["mastered_jobs"].size() == 20, "再転職・追加勝利で二重加算0")
	var path := "user://qa_integrated_totals_%d.json" % OS.get_process_id()
	check(game.save_game(path), "常時特性の保存")
	var loaded := GameSession.new()
	check(loaded.load_game(path) and loaded.call("mastery_bonus", "pc_01") == expected, "ロード後も同じ合計")
	cases += 1

func check_erosion_profiles() -> void:
	for profile in ["human", "monster_attack", "monster_skill"]:
		var game := GameSession.new()
		game.new_game(4)
		if profile != "human": check(game.choose_job("pc_01", "beast"), "通常転職で獣系を選ぶ")
		var crossings := {}
		var uses := 0
		for battle_index in range(1, 551):
			check(game.rest(), "各戦前の正規休息")
			var skill := ""
			if profile == "monster_skill" and "rending_claw" in actor(game)["learned_abilities"]:
				if "rending_claw" not in actor(game)["equipped_abilities"]:
					check(game.equip_ability("pc_01", "rending_claw"), "60JP習得後に通常装着")
				skill = "rending_claw"
				uses += 1
			fight(game, skill)
			var erosion := game.current_erosion("pc_01")
			var expected_tenths := mini(1000, (0 if profile == "human" else battle_index * 2) + uses)
			check(is_equal_approx(erosion, expected_tenths / 10.0), "実使用と戦闘加算の一致: %s/%d" % [profile, battle_index])
			for threshold in [30, 60, 90]:
				if erosion >= threshold and not crossings.has(str(threshold)):
					crossings[str(threshold)] = battle_index
		var expected_crossings: Dictionary = {"human":{},"monster_attack":{"30":150,"60":300,"90":450},"monster_skill":{"30":120,"60":220,"90":320}}[profile]
		check(crossings == expected_crossings, "固定方針の閾値到達戦数: " + profile)
		measurements.append({"profile":profile,"battles":550,"skill_uses":uses,"first_crossing_battle":crossings,"final_erosion":game.current_erosion("pc_01"),"seed":71,"enemy":"slime","party":4,"rest_before_each_battle":true})
		cases += 1
