extends SceneTree
## 人工境界状態のAPI検査と通常UI操作を区別する。配置の採否検査ではない。
const OUT := "res://docs/verification/task-082/"
const OPTIONAL := ["undead","bird","spirit","dragon"]
var checks: Array = []
var main: Node

func check(ok: bool, label: String, detail: Variant = null) -> void:
	checks.append({"ok":ok,"label":label,"detail":detail})
	if not ok:printerr("SHRINE_RUNTIME_FAIL: "+label+" "+str(detail))

func _initialize() -> void:
	OS.set_environment("RPG_QA_SAVE_PREFIX","task082_"+str(OS.get_process_id()))
	call_deferred("run")

func fixture(room: int = 0, cell: Array = [33,9]) -> Dictionary:
	var game := GameSession.new()
	check(game.new_first_region(),"人工境界の初期状態を通常APIで作成")
	var saved := game.export_state()
	saved["party"].append_array(saved["first_region"]["reserve"])
	saved["first_region"]["reserve"]=[]
	saved["inventory"]["gate_pass"]=1
	saved["overworld"]["cleared"]=["first_boss","forest_tower_boss"]
	for flag in FirstRegionStory.FLAGS:saved["progress_flags"][flag]=true
	for flag in ["job_change_unlocked","castle_north_permission","mountain_path_open"]:saved["progress_flags"][flag]=true
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":"region2_village","room":room,"cell":cell})
	return saved

func opened(game: GameSession) -> Array:
	var result: Array = []
	for identifier in ["slime","beast","plant","shell","undead","bird","spirit","dragon"]:
		if game.job_unlocked("pc_01",identifier):result.append(identifier)
	return result

func recalculate(saved: Dictionary) -> Dictionary:
	# 人工保存も既存のJP下限・能力上限に従う。境界検査のため検証契約を緩めない。
	var game := GameSession.new()
	for actor in saved["party"]+saved["first_region"]["reserve"]:
		for id in actor["mastered_jobs"]:
			actor["jp"][id]=IntegratedProgression.cost(game.jobs[id],saved["format_version"]==2)
			if saved["format_version"]==2:actor["integrated"]["mastery"]["counts"][id]=int(game.jobs[id]["mastery_action"]["required"])
		game._refresh_caps(actor)
	return saved

func confirm(game: GameSession, event: Dictionary, page: int) -> Dictionary:
	return game.confirm_region2_shrine_story(event.get("shrine_scene",""),int(event.get("shrine_run",0)),page)

func finish(game: GameSession, event: Dictionary) -> void:
	for page in range(9):check(not confirm(game,event,page).is_empty(),"全ページの通常確認",page)

func enter(game: GameSession) -> Dictionary:
	var event := game.move_first_region(Vector2i(33,8))
	check(event.get("shrine_scene")=="region2_shrine_s10","成功した祠入室で自動開始")
	return event

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	api_cases()
	await ui_cases()
	var failed := checks.filter(func(item:Dictionary)->bool:return not item["ok"])
	var file := FileAccess.open(OUT+"runtime-checks.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"status":"PASS" if failed.is_empty() else "FAIL","checks":checks,"coverage":"人工境界API・通常UI入力。新規人物の配置・視覚統合の完成は未検証。"},"\t")+"\n")
	file.close()
	if failed.is_empty():print("SHRINE_RUNTIME_PASS: checks=%d failures=0"%checks.size())
	quit(0 if failed.is_empty() else 1)

func api_cases() -> void:
	var game := GameSession.new()
	var outside := fixture()
	check(game.import_state(outside),"対象入口の人工境界保存を受理")
	check(game.resume_region2_shrine_story().is_empty(),"外観では発火しない")
	check(game.move_first_region(Vector2i(0,0)).is_empty() and game.export_state()==outside,"失敗移動で発火・変更なし")
	check(opened(game).is_empty(),"開始前は全8職を通常選択で拒否")
	for id in Region2ShrineStory.INITIAL_JOBS+OPTIONAL:check(not game.choose_job("pc_01",id),"未解放のchoose_job拒否",id)
	var event := enter(game)
	var entry := game.export_state()
	check(entry["overworld"]["cell"]==[8,10] and entry["overworld"]["facing"]==3 and entry["overworld"]["entry_lock"]=="region2_village_door","既存の着地・向き・entry_lockを保持")
	check(game.resume_region2_shrine_story().is_empty(),"開始の重複通知を拒否")
	check(game.move_first_region(Vector2i(8,11)).is_empty() and game.interact_first_region().is_empty() and not game.advance_first_region_residents(),"会話中の移動・NPC・住人更新を拒否")
	game.first_region_face(Vector2i.DOWN)
	check(game.export_state()==entry and game.start_battle(["slime"],7)==null,"会話中の向き変更・戦闘開始を拒否")
	check(game.begin_first_region_intro().is_empty(),"既存導入の重複開始を拒否")
	for invalid in [["wrong",event.get("shrine_run",0),0],["region2_shrine_s10",-1,0],["region2_shrine_s10",event.get("shrine_run",0),8],["region2_shrine_s10",event.get("shrine_run",0),-1]]:
		check(game.confirm_region2_shrine_story(invalid[0],invalid[1],invalid[2]).is_empty() and game.export_state()==entry,"誤場面・誤実行・先送り・負ページ拒否",invalid)
	for page in range(8):
		check(confirm(game,event,page).get("kind")=="story_page","中間確認",page)
		check(confirm(game,event,page).is_empty(),"古いページ再確認を拒否",page)
		check(game.export_state()==entry and opened(game).is_empty(),"開始・途中では保存状態も職業解放も不変",page)
	check(confirm(game,event,8).get("kind")=="moved","最終の通常確認で完了")
	var completed := game.export_state()
	var expected := entry.duplicate(true)
	expected["progress_flags"]["region2_shrine_seen"]=true
	expected["progress_flags"]["region2_shrine_jobs_unlocked"]=true
	check(completed==expected,"完了の副作用はboolフラグ2件だけ・アイテム/侵蝕/職/成長不変")
	check(opened(game)==["slime","beast","plant","shell"],"初期4職だけが利用可能・任意4職は閉鎖")
	for id in Region2ShrineStory.INITIAL_JOBS:
		check(game.choose_job("pc_01",id),"初期4職を通常選択で利用",id)
		check(game.choose_job("pc_01","warrior"),"人間職へ戻る既存条件",id)
	for id in OPTIONAL:check(not game.choose_job("pc_01",id),"最終確認後も任意4職の通常選択を拒否",id)
	check(game._member("pc_01")["unlocked_jobs"].is_empty(),"初期4職をadvanced専用配列へ入れない")
	var once := game.export_state()
	check(confirm(game,event,8).is_empty() and game.resume_region2_shrine_story().is_empty() and game.export_state()==once,"最終確認の重複通知・完了後の開始で副作用なし")
	check(game.move_first_region(Vector2i(8,11)).get("kind")=="moved","完了後の既存退出")
	check(game.overworld_state()["room"]==0 and game.move_first_region(Vector2i(33,8)).get("kind")=="moved","再入室で再演なし")
	check(game.save_game("user://task082-complete.json"),"完了状態の通常保存")
	var loaded := GameSession.new()
	check(loaded.load_game("user://task082-complete.json") and loaded.export_state()==game.export_state() and loaded.resume_region2_shrine_story().is_empty(),"完了保存を全値往復・再演なし")
	for page in range(9):
		check(game.import_state(outside),"中断試験の再準備",page)
		event=enter(game)
		for prior in range(page):confirm(game,event,prior)
		var interrupted := game.export_state()
		check(game.save_game("user://task082-interrupted.json"),"各ページの中断保存",page)
		check(loaded.load_game("user://task082-interrupted.json") and loaded.export_state()==interrupted,"各中断保存の全値往復",page)
		var restarted := loaded.resume_region2_shrine_story()
		check(restarted.get("shrine_scene")=="region2_shrine_s10" and confirm(loaded,restarted,1).is_empty() and confirm(loaded,restarted,0).get("kind")=="story_page","室内ロードは必ず冒頭から",page)
		check(game.load_game("user://task082-interrupted.json"),"同一sessionで中断保存を読込",page)
		var next := game.resume_region2_shrine_story()
		check(confirm(game,event,0).is_empty() and confirm(game,next,0).get("kind")=="story_page","旧実行の冒頭通知も拒否",page)
	# 中断→退出→再入室。ページを保存せず完了も付けない。
	game.interrupt_region2_shrine_story()
	check(game.move_first_region(Vector2i(8,11)).get("kind")=="moved","中断後に通常退出")
	event=enter(game)
	check(confirm(game,event,1).is_empty() and confirm(game,event,0).get("kind")=="story_page","安全な再入室も冒頭から")
	# 導入未見を捏造せず、既存の補完後に安全な同室へ復帰する。
	var missing := fixture(4,[8,10])
	for flag in FirstRegionStory.FLAGS:missing["progress_flags"].erase(flag)
	check(game.import_state(missing) and game.resume_region2_shrine_story().is_empty(),"導入未見なら未完了のまま開始しない")
	check(game.require_first_region_intro().get("kind")=="intro_required","既存の導入補完導線を保持")
	var intro := game.begin_first_region_intro()
	for index in range(6):
		if not intro.has("story_scene"):break
		var id: String=intro["story_scene"]
		for page in FirstRegionStory.scene(id)["lines"].size():intro=game.confirm_first_region_story(id,page)
	check(intro.get("shrine_scene")=="region2_shrine_s10","導入補完の通常終了後に同室で開始")
	for room in [0,1,2,3]:
		var other := fixture(room,[8,10] if room>0 else [33,9])
		check(game.import_state(other) and game.resume_region2_shrine_story().is_empty(),"外観・別室ロードでは開始しない",room)
	check(game.import_state(fixture(4,[8,10])) and game.start_battle(["slime"],7)!=null,"戦闘中負例の準備")
	check(game.resume_region2_shrine_story().is_empty(),"戦闘中は開始しない")
	game=GameSession.new()
	var defeated := fixture(4,[8,10])
	for actor in defeated["party"]:actor["hp"]=0
	check(game.import_state(defeated) and game.resume_region2_shrine_story().is_empty(),"全滅中は開始しない")
	for pending in ["travel","recruit","audience"]:
		check(game.import_state(fixture(4,[8,10])),"他会話保留の人工状態",pending)
		if pending=="travel":game._pending_region_travel="ship"
		elif pending=="recruit":game._pending_region_recruit="pc_04"
		else:game._pending_region_audience=true
		check(game.resume_region2_shrine_story().is_empty(),"他会話の確定待ちに重ねない",pending)
	# 実在する追加前の祠保存を無編集コピー。未見の導入も補完で通す。
	var original := "res://docs/verification/task-009/latest/saved-inputs/village009_4_0.json"
	var copied := FileAccess.open("user://task082-actual-old.json",FileAccess.WRITE)
	copied.store_buffer(FileAccess.get_file_as_bytes(original));copied.close()
	game=GameSession.new()
	check(FileAccess.get_sha256(original)==FileAccess.get_sha256("user://task082-actual-old.json") and game.load_game("user://task082-actual-old.json"),"実在する追加前の祠保存をバイト不変で受理")
	check(not game.export_state()["progress_flags"].get("region2_shrine_seen",false) and game.require_first_region_intro().get("kind")=="intro_required","旧訪問履歴を新会話の既読にしない")
	intro=game.begin_first_region_intro()
	for index in range(6):
		if not intro.has("story_scene"):break
		var id: String=intro["story_scene"]
		for page in FirstRegionStory.scene(id)["lines"].size():intro=game.confirm_first_region_story(id,page)
	check(intro.get("shrine_scene")=="region2_shrine_s10","実在旧保存も導入補完後に未読会話の対象")
	finish(game,intro)
	check(game.save_game("user://task082-actual-old-complete.json"),"実在旧保存からの完了後も通常保存")
	check(game.load_game("user://task082-actual-old-complete.json") and game.resume_region2_shrine_story().is_empty(),"実在旧保存の完了後は再演しない")
	legacy_jobs()

func legacy_jobs() -> void:
	# 旧共通ゲートと4種類の既使用維持を改変しない。任意受取の移行は未決。
	for evidence in ["current","jp","mastered","advanced"]:
		var saved := fixture(4,[8,10])
		saved["progress_flags"]["monster_jobs_unlocked"]=true
		saved["progress_flags"]["advanced_jobs_unlocked"]=true
		var actor: Dictionary=saved["party"][0]
		match evidence:
			"current":actor["job_id"]="spirit"
			"jp":actor["jp"]["spirit"]=1
			"mastered":actor["mastered_jobs"].append("spirit")
			"advanced":actor["unlocked_jobs"].append("spirit")
		var game := GameSession.new()
		check(game.import_state(recalculate(saved)) and game.save_game("user://task082-used.json") and game.load_game("user://task082-used.json") and game.choose_job("pc_01","spirit"),"旧保存の既使用維持を往復して保持",evidence)
	var game := GameSession.new()
	var saved := fixture(4,[8,10])
	saved["progress_flags"]["advanced_jobs_unlocked"]=true
	saved["party"][0]["erosion"]=60
	saved["party"][0]["mastered_jobs"]=["undead","priest"]
	check(game.import_state(recalculate(saved)) and game.choose_job("pc_01","warrior"),"修練による精霊取得の既存条件を準備")
	check("spirit" in game._member("pc_01")["unlocked_jobs"],"修練達成と任意受取を区別する観測")
	finish(game,game.resume_region2_shrine_story())
	check(not game.choose_job("pc_01","spirit"),"精霊の修練達成だけで任意受取済みとしない")
	for erosion in [59,60]:
		for masters in [[],["undead"],["priest"],["undead","priest"]]:
			var prior := fixture()
			prior["progress_flags"]["monster_jobs_unlocked"]=true
			prior["progress_flags"]["advanced_jobs_unlocked"]=true
			prior["party"][0]["erosion"]=erosion
			prior["party"][0]["mastered_jobs"]=masters
			check(game.import_state(recalculate(prior)) and game.job_unlocked("pc_01","spirit")==(erosion==60 and masters.size()==2),"既存の精霊前提を変更しない",[erosion,masters])
	var no_change := fixture(4,[8,10])
	no_change["progress_flags"].erase("job_change_unlocked")
	check(game.import_state(no_change),"転職未解放の人工状態")
	finish(game,game.resume_region2_shrine_story())
	check(not game.choose_job("pc_01","slime"),"会話完了は転職共通条件を置換しない")
	for version in [1,2]:
		var old := fixture(4,[8,10])
		old["format_version"]=version
		if version==1:
			old.erase("integrated")
			for actor in old["party"]:actor.erase("integrated")
		check(game.import_state(old) and game.save_game("user://task082-version.json") and game.load_game("user://task082-version.json"),"追加前の保存形式を変更せず受理",version)
		check(game.resume_region2_shrine_story().get("shrine_scene")=="region2_shrine_s10","旧版未読保存も対象",version)
	check(game.new_game(4),"旧本編を通常開始")
	var legacy := game.export_state()
	check(game.resume_region2_shrine_story().is_empty(),"first_regionのない旧本編は対象外")
	for id in ["slime","beast","plant","shell","undead","bird","dragon"]:check(game.choose_job("pc_01",id),"旧本編の職業判定を保持",id)
	check(game.import_state(legacy) and game.save_game("user://task082-legacy.json") and game.load_game("user://task082-legacy.json") and game.export_state()==legacy,"旧本編の保存も全値往復")
	var invalid := fixture()
	invalid["progress_flags"]["region2_shrine_seen"]=1
	check(not game.import_state(invalid),"progress_flagsのbool契約を維持")
	invalid=fixture();invalid["party"][0]["unlocked_jobs"]=["slime"]
	check(not game.import_state(invalid),"unlocked_jobsのadvanced専用検証を維持")

func ui_cases() -> void:
	main=(load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.save_path="user://task082-ui-manual.json"
	main.checkpoint_path="user://task082-ui-checkpoint.json"
	check(main.game.import_state(fixture()),"UI試験は入口の人工境界から")
	main.mode=main.Mode.WORLD
	main._refresh()
	check(main.submit_player_action({"kind":"world_move","dx":0,"dy":-1}),"通常の方向入力で扉へ移動開始")
	for frame in range(120):
		if main.mode==main.Mode.DIALOGUE:break
		await process_frame
	check(main.mode==main.Mode.DIALOGUE and main._message_index==0 and not main._world_mover.active(),"成功した遷移の後に自動会話・移動終了")
	check(main._shrine_story_id=="region2_shrine_s10" and main._region_line_speakers[0]=="状況","UIで専用場面IDと話者を保持")
	check(not main.submit_player_action({"kind":"world_move","dx":0,"dy":1}) and not main.submit_player_action({"kind":"world_interact"}),"会話中の通常移動/NPC入力を拒否")
	var echo := InputEventKey.new();echo.keycode=KEY_ENTER;echo.pressed=true;echo.echo=true
	main._input(echo)
	check(main._message_index==0,"キーのリピートでページを飛ばさない")
	var active_id: String=main._shrine_story_id
	var active_run: int=main._shrine_story_run
	for stale in ["ui_menu","ui_items","party","ui_resume"]:
		main._region_ui_action({"kind":stale})
		check(main.mode==main.Mode.DIALOGUE and main._shrine_story_id==active_id and main._shrine_story_run==active_run and main._message_index==0,"古いメニュー操作で会話のUI・実行番号を失わない",stale)
		# 負例失敗時にも後続の独立した検査を実行できるようUIだけ戻す。
		main.mode=main.Mode.DIALOGUE;main._shrine_story_id=active_id;main._shrine_story_run=active_run;main._refresh()
	main._region_ui_action({"kind":"confirm"})
	check(main.mode==main.Mode.DIALOGUE and main._message_index==1,"通常確認で1ページだけ進む")
	check(main.game.save_game(main.save_path),"途中状態を通常codecで保存")
	var raw := FileAccess.get_file_as_string(main.save_path)
	check(not raw.contains("shrine_run") and not raw.contains("shrine_scene") and not raw.contains("region2_shrine_seen"),"一時ページ・実行番号・未完了フラグを保存しない")
	main._region_ui_action({"kind":"ui_load"})
	check(main.mode==main.Mode.DIALOGUE and main._message_index==0,"通常ロードが安全なWORLD復帰後に冒頭から自動再開")
	check(main.submit_player_action({"kind":"confirm"}),"再開後に通常確認")
	main._region_ui_action({"kind":"ui_title"});main._resume_current()
	check(main.mode==main.Mode.DIALOGUE and main._message_index==0,"タイトルからの同室復帰も冒頭から")
	for page in range(9):check(main.submit_player_action({"kind":"confirm"}),"通常UIで全文を確認",page)
	check(main.mode==main.Mode.WORLD and main.game.export_state()["progress_flags"].get("region2_shrine_seen",false),"通常UIの最終確認で一度だけ完了")
	check(main.submit_player_action({"kind":"save"}),"完了後の通常UI保存")
	main._load_save()
	check(main.mode==main.Mode.WORLD and main._shrine_story_id.is_empty(),"完了後ロードは再演しない")
	# 既存長老を別人物のまま通常APIで確認。
	var elder: Dictionary = main.game.export_state()
	FirstRegion.place(elder["overworld"],{"layer":"interior","node":"region2_village","room":4,"cell":[12,7]})
	elder["overworld"]["facing"]=3
	check(main.game.import_state(elder),"長老の手前の人工境界")
	var reply: Dictionary=main.game.interact_first_region()
	check(reply.get("speaker")=="村の長老" and not reply.has("shrine_scene"),"既存長老をネルに置換せず会話を保持",reply.get("speaker"))
	# チェックポイント読込と起動中の再試行の双方を同じ復帰経路で確認。
	var checkpoint := GameSession.new()
	check(checkpoint.import_state(fixture(4,[8,10])) and checkpoint.save_game(main.checkpoint_path),"室内の未読チェックポイントを通常codecで準備")
	main._to_menu()
	check(main._load_checkpoint() and main.mode==main.Mode.DIALOGUE and main._message_index==0,"チェックポイント読込も冒頭から自動開始")
	main._checkpoint=fixture(4,[8,10])
	main._to_menu()
	check(main._retry_battle() and main.mode==main.Mode.DIALOGUE and main._message_index==0,"起動中の戦闘前復帰も冒頭から自動開始")
	for page in range(9):main.submit_player_action({"kind":"confirm"})
	main._checkpoint=main.game.export_state()
	main._to_menu()
	check(main._retry_battle() and main.mode==main.Mode.WORLD,"完了済みチェックポイントは再演しない")
	# 読込/入室以外の描画・更新は発火源にならない。
	check(main.game.import_state(fixture(4,[8,10])),"発火源負例の人工状態")
	main.mode=main.Mode.WORLD
	for frame in range(4):main._refresh();await process_frame
	check(main.mode==main.Mode.WORLD and main._shrine_story_id.is_empty(),"描画フレームだけで会話を発火しない")
	main.queue_free()
	await process_frame
