extends "res://tools/check_battle_acceptance.gd"

const Compare=preload("res://tools/save_state_comparison.gd")
const Counterplay=preload("res://tools/counterplay_policy.gd")
var moved:=0
var battles:=0
var cases:=0
var arc_id: String="w_ferry"
var build_at_start: Dictionary={}
var catalog_at_start: String=""
var checks_at_start: Dictionary={}
var started_ms: int=0
var saves:=0
var field_driver = preload("res://tools/long_play_driver.gd").new()

func check(value: bool,message: String)->bool:
	if not value:errors.append(message)
	return value

func _run()->void:
	started_ms=Time.get_ticks_msec()
	build_at_start=BuildIdentity.current()
	catalog_at_start=FileAccess.get_sha256(LongCampaign.PATH)
	checks_at_start=_check_hashes()
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--arc="):arc_id=argument.trim_prefix("--arc=")
	if not check(arc_id.is_valid_identifier(),"連作IDがファイル名に使える識別子である"):
		_finish();return
	print("LONG_INTEGRATION_START: arc=%s build=%s catalog=%s" % [arc_id,build_at_start["id"],catalog_at_start])
	var game: Variant=GameSession.new()
	if not check(game.has_method("long_missions"),"本番の長編選択APIがある"):
		_finish();return
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var was_enabled:=LongCampaign.enabled()
	# 未完成の全80話を合格にはしない。現在書かれた4話の接続を検査する入力。
	LongCampaign._source["enabled"]=true
	var legacy_game:=GameSession.new()
	legacy_game.new_game(4)
	var legacy: Dictionary=legacy_game.export_state()
	legacy["progress_flags"].erase("long_campaign_enrolled")
	legacy["progress_flags"]["chapter1_cleared"]=true
	var old_entry:=StoryCampaign.step(17)
	legacy["world"]={"location":old_entry["location"],"player_cell":old_entry["cell"],"quest_step":17}
	check(legacy_game.import_state(legacy) and legacy_game.advance_story_step(),"旧保存は従来の進行を継続する")
	check(not legacy_game.export_state()["progress_flags"].get("long_campaign_started",false),"旧保存へ必須の長編を後付けしない")
	for size in [3,4]:
		for option in [0,1]:
			game=GameSession.new()
			var initial:=_initial_state(game,size,profile)
			initial["progress_flags"]["chapter1_cleared"]=true
			initial["progress_flags"]["circuit_waterway_cleared"]=true
			var entry:=StoryCampaign.step(17)
			initial["world"]={"location":entry["location"],"player_cell":entry["cell"],"quest_step":17}
			if not check(game.import_state(initial),"第1章後の有効な検査状態"):break
			check(game.long_missions().is_empty(),"開始イベント前は解放しない")
			check(game.advance_story_step(),"既存の開始イベントを通る")
			entry=game.current_story_step()
			if not _walk(game,entry["cell"]):break
			check(game.advance_story_step(),"本編の通常移動で入口へ進む")
			var first_mission:=LongCampaign.mission(arc_id+"_1")
			if not first_mission.is_empty() and first_mission["trigger_step"]!=19:
				# 後章の連作も、その章の入口状態から接続を検査する。全章通しとは区別する。
				var routed: Dictionary=game.export_state()
				var base:=StoryCampaign.step(first_mission["trigger_step"])
				routed["world"]={"location":base["location"],"player_cell":base["cell"],"quest_step":first_mission["trigger_step"]}
				for circuit in CampaignContent.data()["circuits"]:
					if circuit["trigger_step"]==first_mission["trigger_step"]:
						routed["progress_flags"]["circuit_"+circuit["id"]+"_cleared"]=true
				if not check(game.import_state(routed),"対象章の入口状態を読み込む"):break
			for number in range(1,5):
				var id: String=arc_id+"_"+str(number)
				entry=game.current_story_step()
				if not _walk(game,entry["cell"]):break
				if not check(game.begin_expedition(id),"入口から長編へ入れる"):break
				while not game.export_state()["expedition"].is_empty():
					entry=game.current_story_step()
					if entry.has("responses"):
						var lines: Array=game.story_lines(entry)
						for response in entry["responses"]:
							for line in response["variants"][option]:check(line in lines,"選んだ内容の結果が会話へ出る")
							for line in response["variants"][1-option]:check(line not in lines,"選ばなかった結果を混ぜない")
					if not _walk(game,entry["cell"]):break
					if entry["kind"]=="battle":
						# 局所検査は一職マスターから開始。通常の補給と公開された敵情報を使う。
						check(game.return_to_town() and game.rest() and game.resume_exploration(),"部分経路の戦闘前に通常の帰還・補給で再開")
						var fight: BattleState=game.start_story_battle()
						if not check(fight!=null,"実際の戦闘を開始する"):break
						for turn in range(60):
							if fight.phase!=BattleState.Phase.INPUT:break
							for actor in fight.pending():check(fight.queue_action(_branch_action(fight,actor)).is_empty(),"技を通常の入力で予約する")
							for change in Counterplay.adjustments(fight):check(fight.queue_action(change).is_empty(),"予告に対処する")
							fight.resolve_round()
						if fight.phase!=BattleState.Phase.VICTORY:
							printerr("LONG_BATTLE_DIAGNOSTIC: "+JSON.stringify({"step":entry["id"],"party":size,"option":option,"phase":fight.phase,"round":fight.round_number,"snapshot":fight.snapshot()}))
						if not check(fight.phase==BattleState.Phase.VICTORY and game.finish_battle(),"戦闘の勝利が進行へ反映される"):break
						battles+=1
					if entry["kind"]=="dialogue" and entry.get("rest",false):check(game.rest(),"定義された休息を実行する")
					if entry["kind"]=="challenge":
						if not field_driver.field_task(game,option==0):
							for failure in field_driver.errors:errors.append(failure)
							break
						if not _walk(game,entry["cell"]):break
						var inventory_before: int=game.export_state()["inventory"]["potion"]
						check(game.answer_challenge(option),"どちらの選択も成立する")
						check(game.export_state()["progress_flags"].get(LongCampaign.choice_flag(entry["id"],option),false),"選択を保存対象へ記録する")
						var after: Dictionary=game.export_state()
						var effect: Dictionary=entry["choice_effects"][option]
						check(after["inventory"]["potion"]==inventory_before+int(entry["reward_potions"])+int(effect.get("potion_bonus",0)),"選択に応じた補給を受け取る")
						for flag in effect.get("flags",[]):
							for room in LongCampaign.data()["rooms"]:
								for passage in room.get("passages",[]):
									if passage["flag"]!=flag:continue
									var cell:=Vector2i(passage["cell"][0],passage["cell"][1])
									check(not CampaignContent.is_walkable(room["id"],cell,{}) and CampaignContent.is_walkable(room["id"],cell,after["progress_flags"]),"選択で実際の近道が開通する")
						var broken: Dictionary=after.duplicate(true)
						broken["progress_flags"][LongCampaign.choice_flag(entry["id"],1-option)]=true
						check(not game.import_state(broken) and game.export_state()==after,"相反する選択の保存を拒否し現在状態を守る")
						check(not game.answer_challenge(option) and game.export_state()==after,"選び直して報酬を重複取得しない")
					else:check(game.advance_story_step(),"通常の進行APIで次へ進む")
					if not _save_resume(game,size,option):break
					if not errors.is_empty():break
				check(game.export_state()["progress_flags"].get(LongCampaign.cleared_flag(id),false),"冒険の終端が確定する")
				cases+=1
				print("LONG_INTEGRATION_PROGRESS: arc=%s cases=%d/16 battles=%d/96" % [arc_id,cases,battles])
				if not errors.is_empty():break
			if not errors.is_empty():break
		if not errors.is_empty():break
	LongCampaign._source["enabled"]=was_enabled
	check(not LongCampaign.all_cleared({}),"未完成の全80話を完走扱いにしない")
	check(cases==16 and battles==96,"4話×2編成×2選択で全96戦を通る")
	_finish()

func _save_resume(game: GameSession,size: int,option: int)->bool:
	var expected:=game.export_state()
	var path: String="user://qa_long_%s_%d_%d_%d.json" % [arc_id,OS.get_process_id(),size,option]
	if not check(game.save_game(path),"進行の各地点で保存できる"):return false
	var loaded:=GameSession.new()
	if not check(loaded.load_game(path),"別インスタンスへロードできる"):return false
	if not check(Compare.differences(expected,loaded.export_state(),"$",[]).is_empty(),"長編状態のキー・型・値・順序が一致する"):return false
	check(game.journal_entries()==loaded.journal_entries(),"保存復帰で既読の意味が一致し、先の解答を解放しない")
	saves+=1
	if not expected["expedition"].is_empty():
		check(loaded.return_to_town() and loaded.rest() and loaded.resume_exploration(),"長編の途中から帰還・休息・再開できる")
		check(loaded.world_state()==expected["world"],"元の区画・位置へ戻る")
	return errors.is_empty()

func _walk(game: GameSession,target: Array)->bool:
	var world:=game.world_state()
	var origin: Array=world["player_cell"]
	var allowed: Dictionary={}
	for cell in game.world_walkable_cells():allowed[Vector2i(cell[0],cell[1])]=true
	var start:=Vector2i(origin[0],origin[1]);var goal:=Vector2i(target[0],target[1])
	var queue: Array[Vector2i]=[start];var parents: Dictionary={start:start};var at:=0
	while at<queue.size():
		var cell:=queue[at];at+=1
		if cell==goal:break
		for delta in [Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT,Vector2i.UP]:
			var next: Vector2i=cell+delta
			if allowed.has(next) and not parents.has(next):parents[next]=cell;queue.append(next)
	if not check(parents.has(goal),"通行可能マスで目標へ到達できる"):return false
	var route: Array[Vector2i]=[]
	while goal!=start:route.push_front(goal);goal=parents[goal]
	for cell in route:
		var current: Array=game.world_state()["player_cell"]
		check(absi(current[0]-cell.x)+absi(current[1]-cell.y)==1,"移動でマスを飛ばさない")
		if not check(game.set_world(world["location"],[cell.x,cell.y],world["quest_step"],world.get("section","")),"移動先の通行判定を通る"):return false
		moved+=1
	return true

func _finish()->void:
	BuildIdentity._cached.clear()
	check(BuildIdentity.current()==build_at_start and FileAccess.get_sha256(LongCampaign.PATH)==catalog_at_start,"検査中に本番のコード・データ・素材を変更していない")
	check(_check_hashes()==checks_at_start,"検査中に検査コードを変更していない")
	if arc_id.is_valid_identifier():
		PlaySessionMetrics.write_json("res://docs/verification/long-integration-%s-%d.json" % [arc_id,OS.get_process_id()],{
			"status":"PASS" if errors.is_empty() else "FAIL","arc":arc_id,"cases":cases,"battles":battles,"moved":moved,"save_roundtrips":saves,
			"elapsed_seconds":float(Time.get_ticks_msec()-started_ms)/1000.0,"build":build_at_start,"catalog_sha256":catalog_at_start,"check_sha256":checks_at_start,
			"failures":errors,"scope":"対象章の入口からの部分通し。全80話の完走や人間の所要時間ではない。"})
	for message in errors:printerr("LONG_INTEGRATION_FAIL: "+message)
	if errors.is_empty():print("LONG_INTEGRATION_PASS: authored_cases=%d battles=%d moved=%d arc=%s" % [cases,battles,moved,arc_id])
	quit(0 if errors.is_empty() else 1)

func _check_hashes()->Dictionary:
	var result: Dictionary={}
	for path in ["tools/check_long_integration.gd","tools/check_battle_acceptance.gd","tools/counterplay_policy.gd","tools/save_state_comparison.gd","tools/long_play_driver.gd"]:
		result[path]=FileAccess.get_sha256("res://"+path)
	return result

func _branch_action(fight: BattleState, actor: Combatant) -> BattleAction:
	var action := _action(fight,actor)
	# 複数敵では公開HPが低い相手から数を減らす。固定勝率測定の方針は変更しない。
	if action.kind==BattleAction.Kind.ATTACK or (action.kind==BattleAction.Kind.ABILITY and fight.catalog.abilities[action.ability_id]["kind"] in ["physical","magic"]):
		var targets := fight.living(Combatant.Team.ENEMY)
		targets.sort_custom(func(a: Combatant,b: Combatant) -> bool: return a.id<b.id if a.hp==b.hp else a.hp<b.hp)
		action.target_id = targets[0].id
	return action
