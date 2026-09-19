extends "res://tools/smoke_chapter1.gd"

var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)

func _run() -> void:
	var game := GameSession.new()
	game.new_game(4)
	game.play_metrics.set_source("automated")
	check(CampaignContent.audit(game.enemy_definitions).is_empty(),"追加区画の定義を検査する")
	var sections := 0
	var challenges := 0
	var battles := 0
	for circuit in CampaignContent.data()["circuits"]:
		for room in circuit["sections"]:
			sections += 1
			var position: Array = room["spawn"]
			for task in circuit["steps"]:
				if task["section"] != room["id"]:
					continue
				var route := _route(position,task["cell"],CampaignContent.walkable_cells(room["id"]))
				check(not route.is_empty(),"通常の通行マスで全課題へ到達できる: "+task["id"])
				position = task["cell"]
				challenges += 1 if task["kind"] == "challenge" else 0
				battles += 1 if task["kind"] == "battle" else 0
	check(sections == 25 and challenges == 25 and battles == 50,"25区画・25課題・50戦を維持する")
	var original := game.export_state()
	check(not game.begin_expedition("waterway") and game.export_state() == original,"町から離れた入口を遠隔操作しない")
	game.set_world("waterway",[17,12],19)
	var origin := game.world_state()
	check(game.begin_expedition("waterway"),"本編の入口から点検区画へ入る")
	check(not game.begin_expedition("waterway"),"点検中に入口を重ねない")
	check(not game.advance_story_step(),"目標へ歩く前に進行できない")
	var task := game.current_story_step()
	game.set_world(task["location"],task["cell"],19,task["section"])
	check(game.advance_story_step(),"最初の記録を確定する")
	task = game.current_story_step()
	game.set_world(task["location"],task["cell"],19,task["section"])
	check(not game.advance_story_step(),"戦闘前の進行を拒否する")
	var encounter := game.start_story_battle()
	check(encounter != null and _win(encounter),"区画の戦闘に実際に勝利する")
	check(game.finish_battle() and game.story_battle_cleared(),"勝利を区画の進捗に記録する")
	check(game.advance_story_step(),"勝利後に課題へ進む")
	task = game.current_story_step()
	game.set_world(task["location"],task["cell"],19,task["section"])
	var before := game.export_state()
	check(not game.answer_challenge((int(task["answer"])+1)%3) and game.export_state() == before,"誤答では進行と報酬を変更しない")
	check(game.answer_challenge(task["answer"]),"正答で課題を確定する")
	var rewarded := game.export_state()
	check(rewarded["inventory"]["potion"] == before["inventory"]["potion"]+1,"課題報酬を一度だけ得る")
	check(not game.answer_challenge(task["answer"]) and game.export_state() == rewarded,"連打で報酬を重複取得しない")
	check(game.return_to_town(),"区画の途中から町へ帰還する")
	check(game.save_game("user://qa_content_checkpoint.json"),"区画・課題・帰還先を保存する")
	var loaded := GameSession.new()
	check(loaded.load_game("user://qa_content_checkpoint.json") and loaded.export_state() == game.export_state(),"点検の途中状態が保存往復で一致する")
	check(loaded.resume_exploration(),"保存された区画へ戻る")
	check(loaded.world_state()["section"] == "waterway_1" and loaded.current_story_step()["kind"] == "battle","解いた課題を戻さず出口の戦闘から続ける")
	var valid := loaded.export_state()
	for field in ["section","solved","origin"]:
		var broken := valid.duplicate(true)
		if field == "section":broken["world"]["section"] = "records_5"
		elif field == "solved":broken["expedition"]["solved"] = []
		else:broken["expedition"]["origin"]["quest_step"] = 0
		check(not loaded.import_state(broken) and loaded.export_state() == valid,"不整合な点検保存を拒否する: "+field)
	var legacy := original.duplicate(true)
	legacy.erase("content_revision");legacy.erase("expedition")
	legacy["world"] = origin
	check(loaded.import_state(legacy) and loaded.current_story_step()["kind"] == "battle","従来保存に追加点検を後付けして進行を戻さない")
	for message in failures:printerr("CONTENT_BOUNDARY_FAIL: "+message)
	if failures.is_empty():print("CONTENT_BOUNDARY_PASS: 全25区画の到達性・戦闘前提・誤答・一度だけの報酬・途中帰還保存・従来保存を検証")
	quit(0 if failures.is_empty() else 1)

func _win(encounter: BattleState) -> bool:
	if encounter == null:return false
	for turn in range(50):
		if encounter.phase != BattleState.Phase.INPUT:break
		for actor in encounter.pending():
			encounter.queue_action(BattleAction.strike(actor.id,encounter.living(Combatant.Team.ENEMY)[0].id))
		encounter.resolve_round()
	return encounter.phase == BattleState.Phase.VICTORY
