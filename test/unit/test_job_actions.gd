extends "res://test/support/game_test.gd"

func test_action_mastery_entry_and_fixed_original_conditions() -> void:
	var game: Variant = new_game()
	assert_true(game.has_method("mastery_progress"), "職別行動進捗を本番APIで参照できること")
	if not game.has_method("mastery_progress"):return
	for pair in [["thief",10],["priest",5],["beast",20]]:
		var progress: Dictionary = game.mastery_progress(first_actor(game),pair[0])
		assert_eq(progress["required"],pair[1],"元企画の回数を緩和しない")
		assert_eq(progress["count"],0,"新規開始で行動履歴を捏造しない")

func test_jp_alone_never_masters_any_job() -> void:
	var definitions: Variant = new_game()
	if not definitions.has_method("mastery_progress"):
		assert_true(false,"新規行動条件が未実装")
		return
	for job_id in definitions.jobs:
		var game: Variant = new_game()
		assert_true(game.change_job(first_actor(game),job_id))
		var state: Dictionary=game.export_state()
		state["party"][0]["jp"][job_id]=int(game.jobs[job_id]["mastery_cost"])
		assert_true(game.import_state(state))
		var encounter: Variant=game.start_battle([weakest_enemy(game)],41)
		# 回数が閾値未満のまま勝利。JP到達だけでマスターしない。
		for turn in range(30):
			if encounter.phase!=BattleState.Phase.INPUT:break
			for a in encounter.pending():
				encounter.queue_action(BattleAction.guard(a.id) if a.id==first_actor(game) else BattleAction.strike(a.id,encounter.living(Combatant.Team.ENEMY)[0].id))
			encounter.resolve_round()
		assert_eq(encounter.phase,BattleState.Phase.VICTORY)
		assert_true(game.finish_battle())
		assert_false(job_id in member(game,first_actor(game))["mastered_jobs"],"JPだけではマスターしない: "+job_id)
		assert_eq(member(game,first_actor(game))["monster_form"],"","行動未達で魔物化しない")

func test_every_job_requires_both_conditions_and_preserves_action_progress() -> void:
	var definitions: Variant=new_game()
	if not definitions.has_method("mastery_progress"):
		assert_true(false,"行動進捗APIが必要")
		return
	for job_id in definitions.jobs:
		var game: Variant=new_game()
		var id:=first_actor(game)
		assert_true(game.change_job(id,job_id))
		var issues: Array=preload("res://tools/mastery_action_fixture.gd").exercise(game,id,job_id)
		assert_eq(issues.size(),0,str(issues))
		assert_true(game.mastery_progress(id,job_id)["met"],"実行結果が必要回数に到達")
		assert_false(job_id in member(game,id)["mastered_jobs"],"行動だけではマスターしない")
		var snapshot: Dictionary=game.export_state()
		assert_false(game.finish_battle())
		assert_eq_deep(game.export_state(),snapshot)
		var path: String="user://qa_job_actions_"+job_id+".json"
		assert_true(game.save_game(path))
		var loaded: Variant=new_game()
		assert_true(loaded.load_game(path))
		assert_eq_deep(loaded.export_state(),snapshot)
		assert_true(loaded.change_job(id,"warrior"))
		assert_true(loaded.change_job(id,job_id))
		assert_eq(loaded.mastery_progress(id,job_id)["count"],game.mastery_progress(id,job_id)["count"],"転職で修練を失わない")
		master_job(loaded,id,job_id)

func test_preview_queue_replacement_and_multihits_do_not_multiply_counts() -> void:
	var game: Variant=new_game()
	var id:=first_actor(game)
	assert_true(game.change_job(id,"martial_artist"))
	var fixture: Dictionary=game.export_state()
	fixture["party"][0]["learned_abilities"]=["double_strike"]
	fixture["party"][0]["equipped_abilities"]=["double_strike"]
	assert_true(game.import_state(fixture))
	var b: Variant=game.start_battle(["slime"],19)
	b.actor_by_id("enemy_01").hp=1000;b.actor_by_id("enemy_01").max_hp=1000
	var action:=BattleAction.skill(id,"enemy_01","double_strike")
	var before: Dictionary=b.snapshot()
	b.preview_action(action);b.preview_action(action)
	assert_eq_deep(b.snapshot(),before)
	assert_eq(b.queue_action(action),"");assert_eq(b.queue_action(action),"")
	b.clear_queue()
	assert_eq(b.mastery_counts.get(id,0),0,"予約・再選択・取消で回数を増やさない")
	assert_eq(b.queue_action(action),"")
	for a in b.pending():b.queue_action(BattleAction.guard(a.id))
	b.resolve_round()
	assert_eq(b.mastery_counts.get(id,0),1,"複数打でも1行動")
	b.actor_by_id(id).mp=0
	assert_ne(b.queue_action(action),"","MP不足の不発")
	assert_eq(b.mastery_counts.get(id,0),1)

func test_legacy_load_is_unchanged_and_explicit_upgrade_preserves_mastery_without_fabricating_counts() -> void:
	var game: Variant=new_game()
	master_job(game,first_actor(game),"beast")
	var legacy: Dictionary=game.export_state()
	legacy["integrated"].erase("mastery_rules_version")
	for a in legacy["party"]:a["integrated"].erase("mastery")
	var loaded: Variant=new_game()
	assert_true(loaded.import_state(legacy))
	assert_eq_deep(loaded.export_state(),legacy)
	assert_false(loaded.mastery_progress(first_actor(loaded),"beast")["active"])
	assert_true(loaded.upgrade_rules())
	assert_eq(loaded.mastery_progress(first_actor(loaded),"beast")["count"],0)
	assert_true(loaded.mastery_progress(first_actor(loaded),"beast")["legacy"])
	assert_eq(member(loaded,first_actor(loaded))["monster_form"],"beast")
	var stable: Dictionary=loaded.export_state()
	assert_false(loaded.upgrade_rules())
	assert_eq_deep(loaded.export_state(),stable)
	var invalid: Dictionary=stable.duplicate(true)
	invalid["party"][0]["integrated"].erase("mastery")
	assert_false(loaded.import_state(invalid),"新形式の修練項目欠落を旧保存と誤認しない")
	invalid=stable.duplicate(true)
	invalid["party"][0]["integrated"]["mastery"]["counts"]["beast"]=-1
	assert_false(loaded.import_state(invalid))
	assert_eq_deep(loaded.export_state(),stable)
