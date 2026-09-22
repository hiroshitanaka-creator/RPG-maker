extends RefCounted
## 通常の移動・現地操作・戦闘APIを使う自動入力。所要時間の実測には使わない。
var errors: Array[String] = []
var moved := 0
var activities := 0
var battles := 0
var rounds := 0
var saves := 0
var save_bytes := 0
var max_save_ms := 0
var max_load_ms := 0
var restored: GameSession

func check(value: bool, message: String) -> bool:
	if not value:errors.append(message)
	return value

func walk(game: GameSession, target: Array) -> bool:
	var world := game.world_state()
	var allowed: Dictionary = {}
	for point in game.world_walkable_cells():
		allowed[Vector2i(point[0],point[1])] = true
	var start := Vector2i(world["player_cell"][0],world["player_cell"][1])
	var goal := Vector2i(target[0],target[1])
	var queue: Array[Vector2i] = [start]
	var parents := {start:start}
	var at := 0
	while at < queue.size() and not parents.has(goal):
		var point := queue[at]
		at += 1
		for direction in [Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT,Vector2i.UP]:
			var next: Vector2i = point+direction
			if allowed.has(next) and not parents.has(next):
				parents[next] = point
				queue.append(next)
	if not check(parents.has(goal),"実際の通行可能セルで目標へ到達する"):return false
	var path: Array[Vector2i] = []
	while goal != start:
		path.push_front(goal)
		goal = parents[goal]
	for point in path:
		if not check(game.set_world(world["location"],[point.x,point.y],world["quest_step"],world.get("section","")),"隣接する通常移動を受理"):return false
		moved += 1
	return true

func field_task(game: GameSession, support: bool) -> bool:
	var activity := game.long_activity()
	if activity.is_empty():return check(false,"現地課題が存在する")
	var initial := game.export_state()
	check(not game.answer_challenge(0) and game.export_state() == initial,"現地操作前の意思決定を拒否")
	if not walk(game,activity["cell"]):return false
	var before := game.export_state()
	check(not game.complete_long_activity(activity["answer"]) and game.export_state() == before,"未観察での正解入力を拒否")
	for i in range(2):
		if not walk(game,activity["observations"][i]["cell"]):return false
		check(game.read_long_observation() == [activity["observations"][i]["text"]],"現地の観察を読む")
	if not walk(game,activity["cell"]):return false
	before = game.export_state()
	check(not game.complete_long_activity((activity["answer"]+1)%activity["options"].size()) and game.export_state() == before,"誤操作で状態とMPを変えない")
	var actor_id := ""
	var old_mp := 0
	var old_equipped: Array = []
	if support:
		check(game.return_to_town() and game.rest() and game.resume_exploration(),"装着とMPを準備して同じ現地へ戻る")
		var actor: Dictionary = game.export_state()["party"][0]
		actor_id = actor["id"]
		old_equipped = actor["equipped_abilities"].duplicate()
		for skill in actor["equipped_abilities"]:
			game.unequip_ability(actor_id,skill)
		if not check(game.equip_ability(actor_id,"firm_guard"),"習得した堅守を装着"):return false
		old_mp = game.export_state()["party"][0]["mp"]
		before = game.export_state()
		check(not game.complete_long_activity(activity["answer"],"missing_actor") and game.export_state() == before,"存在しない担当者を拒否")
	if not check(game.complete_long_activity(activity["answer"],actor_id),"観察した条件で現地の操作を完了"):return false
	var after := game.export_state()
	check(not game.complete_long_activity(activity["answer"],actor_id) and game.export_state() == after,"MP消費と装置完了の二重実行を拒否")
	check(bool(after["progress_flags"].get(activity["support_flag"],false)) == support,"支援の有無で近道が変わる")
	if support:
		check(after["party"][0]["mp"] == old_mp-int(game.abilities["firm_guard"]["cost"]),"装着した技のMPを一度だけ消費")
		game.unequip_ability(actor_id,"firm_guard")
		for skill in old_equipped:check(game.equip_ability(actor_id,skill),"現地支援の後に戦闘用の装着へ戻せる")
	activities += 1
	return errors.is_empty()

func prepare(game: GameSession, train_jobs: bool) -> void:
	var base_jobs := ["warrior","martial_artist","priest","mage","thief"]
	var index := 0
	for actor in game.export_state()["party"]:
		if train_jobs and actor["job_id"] in actor["mastered_jobs"]:
			var next_job: String = base_jobs[index]
			for offset in range(base_jobs.size()):
				var job: String = base_jobs[(index+offset)%base_jobs.size()]
				if job not in actor["mastered_jobs"]:
					next_job = job
					break
			if actor["job_id"] != next_job:check(game.choose_job(actor["id"],next_job),"修練の次の職か、戦闘の担当職を選ぶ")
		var available: Array = game.available_abilities(actor["id"])
		var desired: Array = ["heal","revive","firm_guard"] if index == 2 else ["fire","power_strike","double_strike"]
		var target: Array = []
		for skill in desired:
			if skill in available and target.size() < game.slot_limit(actor["id"]):target.append(skill)
		var equipped: Array = game.export_state()["party"][index]["equipped_abilities"]
		if equipped != target:
			for skill in equipped:game.unequip_ability(actor["id"],skill)
			for skill in target:game.equip_ability(actor["id"],skill)
		index += 1

func battle(game: GameSession) -> bool:
	var encounter := game.start_story_battle()
	if not check(encounter != null,"本番の敵編成とシードで戦闘を開始"):return false
	var policy = preload("res://tools/counterplay_policy.gd")
	for turn in range(80):
		if encounter.phase != BattleState.Phase.INPUT:break
		for actor in encounter.pending():
			check(encounter.queue_action(preload("res://tools/integrated_play_policy.gd").action(encounter,actor)).is_empty(),"使える技と道具だけで行動")
		for action in policy.adjustments(encounter):
			check(encounter.queue_action(action).is_empty(),"公開された予告へ対処")
		encounter.resolve_round()
		rounds += 1
	if not check(encounter.phase == BattleState.Phase.VICTORY,"通常の戦闘計算で勝利: "+str(game.current_story_step().get("id",""))):return false
	check(game.finish_battle(),"勝利のJP・習得・進行を一度反映")
	battles += 1
	return true

func save_resume(game: GameSession, label: String) -> bool:
	var path := "user://qa_long_full_%s_%d.json" % [label,OS.get_process_id()]
	var before := game.export_state()
	var started := Time.get_ticks_msec()
	if not check(game.save_game(path),"進行中の状態を保存"):return false
	max_save_ms = maxi(max_save_ms,Time.get_ticks_msec()-started)
	var file := FileAccess.open(path,FileAccess.READ)
	save_bytes = maxi(save_bytes,file.get_length())
	file.close()
	var loaded := GameSession.new()
	started = Time.get_ticks_msec()
	if not check(loaded.load_game(path),"別インスタンスへロード"):return false
	max_load_ms = maxi(max_load_ms,Time.get_ticks_msec()-started)
	var differences: Array = preload("res://tools/save_state_comparison.gd").differences(before,loaded.export_state(),"$",[])
	check(differences.is_empty(),"キー・型・値・配列順序の不一致0")
	check(preload("res://tools/save_state_comparison.gd").unlisted(before).is_empty(),"保存対象一覧の列挙漏れ0")
	check(preload("res://tools/save_state_comparison.gd").differences(game.play_metrics.snapshot(),loaded.play_metrics.snapshot(),"$metrics",[]).is_empty(),"独立した操作履歴もキー・型・値・順序が一致")
	check(game.journal_entries() == loaded.journal_entries(),"既読情報の公開範囲も一致")
	restored = loaded
	saves += 1
	return errors.is_empty()
