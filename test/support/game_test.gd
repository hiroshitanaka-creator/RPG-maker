extends GutTest

const GAME_PATH := "res://scripts/game/game_session.gd"


func new_game(size: int = 4) -> Variant:
	# 実ゲームの状態管理が必要。
	assert_file_exists(GAME_PATH)
	if not FileAccess.file_exists(GAME_PATH):
		return null
	var source: Script = load(GAME_PATH)
	assert_not_null(source, "実ゲームのスクリプトが読み込めること。")
	if source == null:
		return null
	var game: Variant = source.new()
	assert_true(game.new_game(size), "新規ゲームを開始できること。")
	assert_eq(game.export_state()["party"].size(), size, "パーティ人数を維持すること。")
	return game


func job_of_type(game: Variant, kind: String, except_id: String = "") -> String:
	for identifier in game.jobs:
		if game.jobs[identifier]["type"] == kind and identifier != except_id:
			return identifier
	assert_true(false, "条件を満たす職業が必要です: " + kind)
	return ""


func first_actor(game: Variant) -> String:
	return game.export_state()["party"][0]["id"]


func member(game: Variant, actor_id: String) -> Dictionary:
	for actor in game.export_state()["party"]:
		if actor["id"] == actor_id:
			return actor
	assert_true(false, "対象の仲間が存在すること。")
	return {}


func weakest_enemy(game: Variant) -> String:
	var found := ""
	var least_hp := 2147483647
	for identifier in game.enemy_definitions:
		var hp := int(game.enemy_definitions[identifier]["stats"]["hp"])
		if hp < least_hp:
			found = identifier
			least_hp = hp
	assert_ne(found, "", "実際に戦える敵データが必要です。")
	return found


func win_battle(game: Variant, seed_value: int = 17) -> void:
	var enemy_id := weakest_enemy(game)
	if enemy_id.is_empty():
		return
	var encounter: Variant = game.start_battle([enemy_id], seed_value)
	assert_not_null(encounter, "本番の戦闘処理を開始すること。")
	if encounter == null:
		return
	for turn in range(100):
		if encounter.phase != BattleState.Phase.INPUT:
			break
		var targets: Array = encounter.living(Combatant.Team.ENEMY)
		assert_false(targets.is_empty(), "行動入力中は敵が存在すること。")
		if targets.is_empty():
			return
		for actor in encounter.living(Combatant.Team.PARTY):
			assert_eq(encounter.queue_action(BattleAction.strike(actor.id, targets[0].id)), "")
		encounter.resolve_round()
	assert_eq(encounter.phase, BattleState.Phase.VICTORY, "実際のターン解決で勝利すること。")
	assert_true(game.finish_battle(), "勝利結果をゲーム状態へ反映すること。")


func master_job(game: Variant, actor_id: String, job_id: String) -> void:
	assert_true(game.change_job(actor_id, job_id), "対象職へ転職できること。")
	var state: Dictionary = game.export_state()
	for actor in state["party"]:
		if actor["id"] == actor_id:
			actor["jp"][job_id] = int(game.jobs[job_id]["mastery_cost"]) - 1
	assert_true(game.import_state(state), "閾値直前の有効なセーブ状態を読み込めること。")
	win_battle(game)
	assert_true(job_id in member(game, actor_id)["mastered_jobs"], "戦闘報酬でマスターへ遷移すること。")
