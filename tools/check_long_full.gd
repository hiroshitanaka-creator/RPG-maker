extends SceneTree
const Driver = preload("res://tools/long_play_driver.gd")
const Audit=preload("res://tools/long_audit_checkpoint.gd")
var errors: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var size := 3 if "--party=3" in OS.get_cmdline_user_args() else 4
	var reverse_order := "--reverse" in OS.get_cmdline_user_args()
	var option := 1 if reverse_order else 0
	var label := "%d_%s" % [size,"reverse" if reverse_order else "forward"]
	var resume_path := ""
	var audit_session:=""
	var checkpoint_limit:=0
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--resume-qa="):resume_path = argument.trim_prefix("--resume-qa=")
		if argument.begins_with("--audit-session="):audit_session=argument.trim_prefix("--audit-session=")
		if argument.begins_with("--checkpoint-limit="):checkpoint_limit=int(argument.trim_prefix("--checkpoint-limit="))
	if (not audit_session.is_empty() and (not audit_session.is_valid_identifier() or audit_session.length()>40 or not resume_path.is_empty())) or (checkpoint_limit>0 and audit_session.is_empty()):
		printerr("LONG_FULL_FAIL: 検査再開の引数が不正");quit(2);return
	if not resume_path.is_empty():label += "_resume_diagnostic"
	var driver = Driver.new()
	var build := BuildIdentity.current()
	var check_hashes := _check_hashes()
	var started := Time.get_ticks_msec()
	var game := GameSession.new()
	driver.check(LongCampaign.enabled(),"全長編が通常の開始で有効")
	driver.check(game.new_game(size),"通常の初期パーティで新規開始")
	game.play_metrics.set_source("automated")
	driver.check(game.export_state()["progress_flags"].get("long_campaign_enrolled",false),"新規開始は長編を含む")
	var first_save := game.export_state()
	var missions := 0
	var checkpoints := 0
	var world_detour := false
	if not resume_path.is_empty():
		driver.check(resume_path.begins_with("user://qa_long_full_") and game.load_game(resume_path),"実際の検査で保存した状態からの診断再開")
		for mission in LongCampaign.data()["missions"]:
			if game.export_state()["progress_flags"].get(LongCampaign.cleared_flag(mission["id"]),false):missions+=1
			for activity in mission["activities"]:
				if game.export_state()["progress_flags"].get(LongCampaign.activity_flag(activity["id"],"done"),false):driver.activities+=1
		world_detour = true
	var seen_chapters: Dictionary = {}
	var audit: RefCounted
	var start_iteration:=0
	var prior_elapsed:=0.0
	var resumptions:=0
	if not audit_session.is_empty():
		audit=Audit.new(audit_session,label,build,check_hashes,first_save)
		var receipt: Dictionary=audit.load_latest(game,driver)
		if receipt.has("error"):printerr("LONG_FULL_FAIL: "+str(receipt["error"]));quit(2);return
		if not receipt.is_empty():
			missions=receipt["missions"];checkpoints=receipt["checkpoints"];world_detour=receipt["world_detour"]
			start_iteration=receipt["sequence"];prior_elapsed=receipt["elapsed_seconds"];resumptions=receipt["resumptions"]+1
			print("LONG_FULL_RESUME: missions=%d battles=%d checkpoint=%d" % [missions,driver.battles,checkpoints])
	var segment_checkpoints:=0
	for iteration in range(start_iteration,5000):
		if not driver.errors.is_empty() or game.story_complete():break
		if game.chapter_one_pause():
			driver.check(game.continue_story(),"第1章から本編を続ける")
		var entry := game.current_story_step()
		if not driver.check(not entry.is_empty(),"次の進行地点が存在する"):break
		var chapter: int = entry.get("chapter",1)
		if not seen_chapters.has(chapter):
			seen_chapters[chapter] = true
			print("LONG_FULL_PROGRESS: party=%d order=%s chapter=%d missions=%d" % [size,label,chapter,missions])
		var activity := game.long_activity()
		if not activity.is_empty() and not game.export_state()["progress_flags"].get(LongCampaign.activity_flag(activity["id"],"done"),false):
			# まず現在の会話を読み、休息を済ませてから現地を巡る。
			if entry["kind"] != "dialogue" or not entry.get("rest",false):
				if not driver.field_task(game,option==0):break
		if not driver.walk(game,entry["cell"]):break
		match entry["kind"]:
			"expedition":
				var available := game.long_missions()
				var id: String = entry["expedition_id"]
				if not available.is_empty():
					id = available[-1 if reverse_order else 0]["id"]
				driver.check(game.begin_expedition(id),"解放済みの依頼を通常APIで選択")
			"dialogue":
				driver.check(not game.story_lines(entry).is_empty(),"前提を満たした本文を読む")
				if entry.get("rest",false):driver.check(game.rest(),"現地に定義された休息")
				driver.check(game.advance_story_step(),"会話を読んで進行")
			"battle":
				driver.prepare(game,true)
				# 現地の休息だけでは不足する時、通常の帰還操作で準備し直せる。
				if game.world_state()["location"] not in ChapterOne.TOWNS:
					driver.check(game.return_to_town() and game.rest() and game.resume_exploration(),"戦闘前に担当職とMPを通常の帰還・休息で整える")
				else:game.rest()
				while not game.story_battle_cleared():
					if game.story_wave_index()>0:
						driver.check(game.return_to_town() and game.rest() and game.resume_exploration(),"連戦の既得勝利を保持して補給")
					if not driver.battle(game):break
				if not driver.errors.is_empty():break
				driver.check(game.advance_story_step(),"実際の勝利後に進む")
			"challenge":
				driver.check(game.answer_challenge(option if entry.get("choice",false) else int(entry["answer"])),"条件を満たして判断を確定")
			"choice":
				if StoryCampaign.stage(game.export_state()["progress_flags"],"R05")==2 and StoryCampaign.stage(game.export_state()["progress_flags"],"R08")==2:
					driver.check(game.advance_story_step(),"両方の再訪を終えて進む")
				else:
					var first := "teaching" if reverse_order else "reply"
					var clue := "R08" if first=="teaching" else "R05"
					if StoryCampaign.stage(game.export_state()["progress_flags"],clue)==2:first="reply" if first=="teaching" else "teaching"
					driver.check(game.start_revisit_task(first),"本編の再訪順も選ぶ")
			"gate":
				driver.check(game.return_to_town() and game.rest() and game.resume_exploration(),"操作前の補給と帰還")
				var team: Array = []
				for actor in game.export_state()["party"]:
					if team.size() >= 3:break
					for skill in actor["equipped_abilities"]:game.unequip_ability(actor["id"],skill)
					driver.check(game.equip_ability(actor["id"],"firm_guard") and game.equip_ability(actor["id"],"sound_wave"),"習得済みの必要技を実際に装着")
					team.append(actor["id"])
				driver.check(game.advance_story_step(team),"現在の編成で本編の操作を終える")
			"circuit_complete":
				var id: String = game.export_state()["expedition"]["id"]
				driver.check(game.advance_story_step(),"依頼の終端を実際に通る")
				if not LongCampaign.mission(id).is_empty():
					missions += 1
					print("LONG_FULL_PROGRESS: party=%d order=%s missions=%d/80 battles=%d saves=%d" % [size,label,missions,driver.battles,driver.saves])
			_:
				driver.check(game.advance_story_step(),"移動・完了イベントを進める")
		if not driver.errors.is_empty():break
		if not driver.save_resume(game,label):break
		game = driver.restored
		checkpoints += 1
		if checkpoints%30==0:
			var saved := game.export_state()
			if game.world_state()["location"] not in ChapterOne.TOWNS and not game.story_complete():
				driver.check(game.return_to_town() and game.rest() and game.resume_exploration(),"長い経路の途中帰還と再開")
				driver.check(game.world_state()==saved["world"],"帰還前の位置へ復帰")
		if missions==8 and not world_detour and game.export_state()["expedition"].is_empty():
			var before_world := game.world_state()
			driver.check(game.return_to_town() and game.rest(),"長編途中から広域へ寄り道する準備")
			driver.check(game.open_world_exploration(),"長編の途中状態を保持して広域へ出る")
			driver.check(driver.save_resume(game,label+"_world"),"広域・長編・履歴を一緒に保存復元")
			game = driver.restored
			driver.check(game.close_world_exploration() and game.resume_exploration(),"広域から長編へ復帰")
			driver.check(game.world_state()==before_world,"寄り道前の位置と進行へ復帰")
			world_detour = true
		if audit!=null:
			var progress:={"sequence":iteration+1,"missions":missions,"checkpoints":checkpoints,"world_detour":world_detour,"elapsed_seconds":prior_elapsed+(Time.get_ticks_msec()-started)/1000.0,"resumptions":resumptions}
			if not driver.check(audit.store(game,driver,progress),"版・ゲーム保存・実行集計を一緒に記録"):break
			segment_checkpoints+=1
			if checkpoint_limit>0 and segment_checkpoints>=checkpoint_limit:
				print("LONG_FULL_CHECKPOINTED: 未完了の検査を再開可能な状態で保存");quit(75);return
		if iteration%20==0:await process_frame
	driver.check(game.story_complete() and missions==80 and LongCampaign.all_cleared(game.export_state()["progress_flags"]),"全80話を経て本編の結末へ到達")
	driver.check(driver.activities==80,"全80話の現地操作を完了")
	if resume_path.is_empty():driver.check(driver.battles==550,"既存70戦と長編480戦を全て通常計算で勝利")
	driver.check(game.journal_entries().size()==54,"既存8件と長編46件を保持")
	for entry in game.journal_entries():driver.check(entry["stage"]==2,"未回収を残さない")
	driver.check(game.recording_context()["long_campaign_complete"],"記録にも実際の完走を渡す")
	driver.check(first_save["party"].size()==size,"検査中に編成を増やさない")
	driver.check(driver.max_save_ms<2000 and driver.max_load_ms<2000 and driver.save_bytes<1048576,"長編保存は暫定2秒・1MiB以内")
	BuildIdentity._cached.clear()
	driver.check(BuildIdentity.current()==build,"検査中にコード・データ・素材を変更していない")
	driver.check(_check_hashes()==check_hashes,"検査中に検査コードを変更していない")
	var report := {"status":"PASS" if driver.errors.is_empty() else "FAIL","failures":driver.errors,"party":size,"order":label,"missions":missions,"activities":driver.activities,"battles":driver.battles,"rounds":driver.rounds,"moved":driver.moved,"save_roundtrips":driver.saves,"save_max_bytes":driver.save_bytes,"save_max_ms":driver.max_save_ms,"load_max_ms":driver.max_load_ms,"elapsed_seconds":(Time.get_ticks_msec()-started)/1000.0,"build":build,"source":"new_game_normal_api_no_progress_or_stat_injection","human_duration":"NOT_RUN"}
	report["check_sha256"] = check_hashes
	if audit!=null:
		report["source"]="new_game_with_verified_saved_continuation"
		report["resumptions"]=resumptions;report["audit_session"]=audit_session
		report["elapsed_seconds"]+=prior_elapsed
	if not resume_path.is_empty():report["source"] = "saved_real_run_diagnostic_not_new_game_proof"
	report["last_step"] = game.current_story_step()
	PlaySessionMetrics.write_json("res://docs/verification/long-full-"+label+".json",report)
	for failure in driver.errors:printerr("LONG_FULL_FAIL: "+failure)
	if driver.errors.is_empty():print("LONG_FULL_PASS: party=%d missions=%d activities=%d battles=%d saves=%d" % [size,missions,driver.activities,driver.battles,driver.saves])
	quit(0 if driver.errors.is_empty() else 1)

func _check_hashes() -> Dictionary:
	var result := {}
	for path in ["tools/check_long_full.gd","tools/long_play_driver.gd","tools/counterplay_policy.gd","tools/integrated_play_policy.gd","tools/save_state_comparison.gd","tools/long_audit_checkpoint.gd"]:
		result[path] = FileAccess.get_sha256("res://"+path)
	return result
