extends SceneTree
## 人工境界API検査。--routeは新規ゲームから通常APIだけで実進行する別測定。
const OUT := "res://docs/verification/task-085/"
const DIRS := [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]
var checks: Array = []
var battles: Array = []
var route_game: GameSession
var steps := 0
var route_complete := false

func check(ok: bool, label: String, detail: Variant=null) -> bool:
	checks.append({"ok":ok,"label":label,"detail":detail})
	if not ok:printerr("S11_FAIL: "+label+" "+str(detail))
	return ok

func fixture(cell: Array=[18,15], room: int=3) -> Dictionary:
	var game := GameSession.new();check(game.new_first_region(),"人工境界用新規開始")
	var saved := game.export_state()
	saved["party"].append_array(saved["first_region"]["reserve"]);saved["first_region"]["reserve"]=[]
	for flag in FirstRegionStory.FLAGS:saved["progress_flags"][flag]=true
	saved["progress_flags"][Region2ShrineStory.COMPLETE_FLAG]=true
	saved["progress_flags"]["job_change_unlocked"]=true
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":"region2_ruins","room":room,"cell":cell})
	return saved

func confirm_scene(game: GameSession, event: Dictionary) -> void:
	for page in range(22):
		check(not game.export_state()["progress_flags"].get(Region2RuinsStory.COMPLETE_FLAG,false),"最終確認までは未読",page)
		check(not game.confirm_region2_ruins_story(str(event.get("ruins_scene","")),int(event.get("ruins_run",0)),page).is_empty(),"採用22行を順番確認",page)
	check(game.export_state()["progress_flags"].get(Region2RuinsStory.COMPLETE_FLAG,false),"最終通常確認で読了")

func roundtrip(game: GameSession, label: String) -> void:
	var before := game.export_state()
	for suffix in ["manual","checkpoint"]:
		var path: String = "user://task085-"+label+suffix+".json"
		check(game.save_game(path),label+"通常保存",suffix)
		var loaded := GameSession.new()
		check(loaded.load_game(path) and not loaded.position_relocated and loaded.export_state()==before,label+"全保存値一致",suffix)
		check(loaded.take_region2_ruins_encounter().is_empty(),"ロードだけでは遭遇なし")

func combat_actions(battle: BattleState, policy: String="standard") -> Array[BattleAction]:
	var actions: Array[BattleAction]=[]
	var allies:=battle.living(Combatant.Team.PARTY);var foes:=battle.living(Combatant.Team.ENEMY)
	if foes.is_empty() or allies.is_empty():return actions
	var pending:=battle.pending()
	# 予告画面で公開される予定だけを使用。回復役を先に予約して道具の重複消費を防ぐ。
	pending.sort_custom(func(a:Combatant,b:Combatant)->bool:return int("heal" in a.equipped)>int("heal" in b.equipped))
	allies.sort_custom(func(a:Combatant,b:Combatant)->bool:return a.hp*b.max_hp<b.hp*a.max_hp)
	var healing: Dictionary={};var potions:=0;var incoming: Dictionary={};var guarding:=false
	for intent in battle.enemy_intents():
		if intent["ability"]=="firm_guard":guarding=true;continue
		var enemy:=battle.actor_by_id(intent["actor"]);var target:=battle.actor_by_id(intent["target"])
		var skill: Dictionary=battle.catalog.abilities.get(intent["ability"],{})
		var amount:=maxi(1,enemy.attack*2-target.defense)*int(skill.get("power",100))/100.0
		if skill.get("kind")=="magic":amount=maxi(1,int(skill["power"])+enemy.magic*2-target.resistance)
		incoming[target.id]=int(incoming.get(target.id,0))+ceili(amount)
	for actor in pending:
		var target: Combatant=allies[0]
		var action:=BattleAction.strike(actor.id,foes[0].id)
		var fallen: Array=battle.targets_for(actor.id,BattleAction.Kind.ABILITY,"revive") if "revive" in actor.equipped else []
		if policy=="lose":action=BattleAction.guard(actor.id)
		elif not fallen.is_empty() and actor.mp>=8:action=BattleAction.skill(actor.id,fallen[0].id,"revive")
		elif "heal" in actor.equipped and actor.mp>=4 and not healing.has(target.id) and target.hp<target.max_hp-25:
			action=BattleAction.skill(actor.id,target.id,"heal");healing[target.id]=true
		elif incoming.get(actor.id,0)>0 and actor.hp<=int(incoming[actor.id])*1.6:
			action=BattleAction.guard(actor.id)
		elif not healing.has(target.id) and target.hp*100<target.max_hp*45 and battle.potions>potions:
			action=BattleAction.potion(actor.id,target.id);healing[target.id]=true;potions+=1
		elif not guarding and policy!="physical" and "fire" in actor.equipped and actor.mp>=4:action=BattleAction.skill(actor.id,foes[0].id,"fire")
		elif not guarding and "power_strike" in actor.equipped and actor.mp>=3:action=BattleAction.skill(actor.id,foes[0].id,"power_strike")
		actions.append(action)
	return actions

func fight(game: GameSession, event: Dictionary, policy: String="standard") -> bool:
	var before := game.export_state()
	var battle := game.start_first_region_battle(event)
	if not check(battle!=null,"本番通知から戦闘開始",event):return false
	var dead := 0
	for turn in range(100):
		if battle.phase!=BattleState.Phase.INPUT:break
		for action in combat_actions(battle,policy):
			check(battle.queue_action(action).is_empty(),"通常戦闘コマンド受理")
		battle.resolve_round()
		dead=maxi(dead,before["party"].size()-battle.living(Combatant.Team.PARTY).size())
	var won := battle.phase==BattleState.Phase.VICTORY
	var record := {"event":event,"policy":policy,"won":won,"turns":battle.round_number,"max_fallen":dead,"potions_used":int(before["inventory"]["potion"])-battle.potions,"before_party":before["party"],"after_combat":battle.snapshot()}
	check(game.finish_battle(),"実戦結果を確定")
	check(not game.finish_battle(),"二重結果拒否")
	record["after_party"]=game.export_state()["party"];battles.append(record)
	return won

func api_cases() -> void:
	var game := GameSession.new()
	var saved := fixture()
	check(game.import_state(saved),"未読地点上の旧保存受理")
	roundtrip(game,"unread")
	var event := game.resume_region2_ruins_story()
	check(event.get("text",[]).size()==22 and event.get("ruins_scene")==Region2RuinsStory.SCENE,"地点上のWORLD復帰は冒頭から")
	check(game.resume_region2_ruins_story().is_empty(),"重複開始拒否")
	for args in [["wrong",event.get("ruins_run",0),0],[Region2RuinsStory.SCENE,-1,0],[Region2RuinsStory.SCENE,event.get("ruins_run",0),21],[Region2RuinsStory.SCENE,event.get("ruins_run",0),-1]]:
		check(game.confirm_region2_ruins_story(args[0],args[1],args[2]).is_empty() and game.export_state()==saved,"不正ID/実行/ページで副作用なし",args)
	check(game.move_first_region(Vector2i(18,16)).is_empty() and game.interact_first_region().is_empty() and not game.advance_first_region_residents(),"会話排他")
	game.first_region_face(Vector2i.LEFT)
	check(game.export_state()==saved and game.start_battle(["slime"],1)==null and not game.save_game("user://task085-during.json"),"会話中の方向/戦闘/保存拒否")
	check(not game.confirm_region2_ruins_story(Region2RuinsStory.SCENE,event["ruins_run"],0).is_empty(),"1ページ確認")
	check(game.confirm_region2_ruins_story(Region2RuinsStory.SCENE,event["ruins_run"],0).is_empty(),"同ページ連打拒否")
	game.interrupt_region2_ruins_story()
	var restarted := game.resume_region2_ruins_story()
	check(restarted.get("ruins_run",0)!=event.get("ruins_run",0),"中断後は別実行の冒頭")
	check(game.confirm_region2_ruins_story(Region2RuinsStory.SCENE,event["ruins_run"],0).is_empty(),"旧実行の決定拒否")
	confirm_scene(game,restarted)
	var after := game.export_state();var expected := saved.duplicate(true);expected["progress_flags"][Region2RuinsStory.COMPLETE_FLAG]=true
	check(after==expected and game.current_battle()==null,"読了は既読だけ変更・強制戦闘なし")
	roundtrip(game,"read-before-win")
	check(game.resume_region2_ruins_story().is_empty(),"読了後自動再演なし")
	var revisit := game.interact_first_region()
	check(revisit.get("text",[]).size()==2 and game.export_state()==after,"短い再訪だけ・副作用なし")
	check(game.move_first_region(Vector2i(18,16)).get("kind")=="moved","記録後に引き返せる")
	check(game.take_region2_ruins_encounter().is_empty(),"最下層無遭遇")
	for offset in [Vector2i(18,16),Vector2i(18,17)]:
		check(game.move_first_region(offset).get("kind","") in ["moved", ""],"通常/静止の戻り値維持")
	# 旧保存が広間内にある場合も、勝利・既読を補完しない。
	saved=fixture([31,13]);saved["overworld"]["facing"]=3
	check(game.import_state(saved) and game.resume_region2_ruins_story().is_empty(),"広間の旧保存はワープ/既読補完なし")
	event=game.interact_first_region()
	check(event.get("ruins_scene")==Region2RuinsStory.SCENE and game.current_battle()==null,"旧広間のボス調査は記録を先行")
	confirm_scene(game,event)
	check(game.current_battle()==null and game.export_state()["inventory"].get(Region2RuinsStory.KEY,0)==0,"記録終了後も再操作が必要")
	# 境界戦力とは別に、勝敗と報酬種別を実ターンで検証。
	# 報酬境界は初期能力を直接増やさず、通常勝利8回で基本技を習得する人工測定。
	for n in range(8):
		var prior := game.export_state()
		check(fight(game,{"kind":"battle","id":"region2_ruins_encounter","enemies":["slime"],"seed":n}),"境界用の通常勝利で技を習得")
		var gained := game.export_state()
		for i in range(4):check(gained["party"][i]["integrated"]["exp"]==prior["party"][i]["integrated"]["exp"]+20 and gained["party"][i]["jp"].get(gained["party"][i]["job_id"],0)==prior["party"][i]["jp"].get(prior["party"][i]["job_id"],0)+1,"modern通常報酬20EXP/1JP",i)
		game.rest()
	for actor in game.export_state()["party"]:
		for ability in ["heal","fire","power_strike"]:
			if ability in actor["learned_abilities"]:game.equip_ability(actor["id"],ability)
	var before_boss := game.export_state()
	event=game.interact_first_region()
	check(event.get("id")==Region2RuinsStory.BOSS,"再操作でボス通知")
	check(fight(game,event),"通常勝利で基本技を得た人工人間4職のボス実勝利")
	var won := game.export_state()
	check(Region2RuinsStory.BOSS in won["overworld"]["cleared"] and won["inventory"].get(Region2RuinsStory.KEY,0)==0,"勝利と鍵は別")
	for i in range(4):
		check(won["party"][i]["integrated"]["exp"]==before_boss["party"][i]["integrated"]["exp"]+40 and won["party"][i]["jp"].get(won["party"][i]["job_id"],0)==before_boss["party"][i]["jp"].get(won["party"][i]["job_id"],0)+12,"modern boss報酬40EXP/12JP",i)
	roundtrip(game,"win-before-box")
	check(game.interact_first_region().is_empty(),"勝利後ボス再戦なし")
	var box := won.duplicate(true);box["overworld"]["cell"]=[31,9];box["overworld"]["facing"]=3
	check(game.import_state(box),"受取前の箱前保存")
	check(game.interact_first_region().get("text")==["遺跡の鍵を手に入れた。"],"別操作で鍵受取")
	var received := game.export_state()
	check(received["inventory"].get(Region2RuinsStory.KEY,0)==1 and Region2RuinsStory.BOX in received["overworld"]["opened"],"受取の永続事実")
	for i in range(3):game.interact_first_region()
	check(game.export_state()==received,"箱連打で二重付与なし")
	roundtrip(game,"received")
	check(game.import_state(before_boss),"敗北用起点を保持")
	check(not fight(game,event,"lose"),"ガードのみで実敗北")
	check(Region2RuinsStory.BOSS not in game.export_state()["overworld"]["cleared"] and game.export_state()["inventory"].get(Region2RuinsStory.KEY,0)==0,"敗北で勝利/鍵を付与しない")
	# 前提/誤位置、別会話、戦闘、侵蝕境界。
	for bad in ["prerequisite","wrong_room","wrong_cell"]:
		var probe := fixture()
		if bad=="prerequisite":probe["progress_flags"].erase(Region2ShrineStory.COMPLETE_FLAG)
		if bad=="wrong_room":probe["overworld"]["room"]=0;probe["overworld"]["cell"]=[18,19]
		if bad=="wrong_cell":probe["overworld"]["cell"]=[18,16]
		check(game.import_state(probe) and game.resume_region2_ruins_story().is_empty() and game.export_state()==probe,"前提/誤地点拒否",bad)
	for erosion in [89,90,91]:
		var probe := fixture()
		for actor in probe["party"]:
			actor["erosion"]=erosion;actor["irreversible"]=erosion>=90
			if erosion>=90:actor["job_id"]="slime"
			game._refresh_caps(actor)
		check(game.import_state(probe),"侵蝕境界の有効保存",erosion)
		var prior := game.export_state();event=game.resume_region2_ruins_story();confirm_scene(game,event)
		prior["progress_flags"][Region2RuinsStory.COMPLETE_FLAG]=true
		check(game.export_state()==prior,"侵蝕/不可逆性/職/HP/MPの不変",erosion)
	var legacy := fixture()
	legacy["format_version"]=1;legacy.erase("integrated")
	for actor in legacy["party"]:actor.erase("integrated")
	check(game.import_state(legacy),"形式1の旧保存を受理")
	event=game.resume_region2_ruins_story();confirm_scene(game,event)
	roundtrip(game,"legacy-read")
	for n in range(3):
		check(fight(game,{"kind":"battle","id":"region2_ruins_encounter","enemies":["slime"],"seed":n}),"旧形式の実JPで習得")
		game.rest()
	for actor in game.export_state()["party"]:
		for ability in ["power_strike","heal","fire"]:
			if ability in actor["learned_abilities"]:check(game.equip_ability(actor["id"],ability),"旧形式の習得技を通常装着")
	legacy=game.export_state();legacy["overworld"]["cell"]=[31,13];legacy["overworld"]["facing"]=3
	check(game.import_state(legacy),"旧形式の報酬境界配置")
	check(fight(game,game.interact_first_region()),"旧形式の本番ボス実勝利")
	var legacy_won := game.export_state()
	for i in range(4):check(legacy_won["party"][i]["jp"].get(legacy_won["party"][i]["job_id"],0)==legacy["party"][i]["jp"].get(legacy["party"][i]["job_id"],0)+50,"旧形式は敵の50JPを保持")
	var blocked := fixture([31,13]);blocked["overworld"]["facing"]=3
	check(game.import_state(blocked),"ボス開始の負例起点")
	var forged := {"kind":"battle","id":Region2RuinsStory.BOSS,"enemies":[Region2RuinsStory.ENEMY],"seed":1}
	check(game.start_first_region_battle(forged)==null and game.export_state()==blocked,"未読のボス直開始を拒否")
	check(game.start_battle(["slime"],85)!=null and game.resume_region2_ruins_story().is_empty(),"戦闘中の記録開始拒否")
	encounter_cases()
	ai_cases()

func encounter_cases() -> void:
	var game := GameSession.new()
	seed(85)
	var hits := [0,0,0,0];var groups: Array=[{}, {}, {}, {}]
	for room in range(4):
		var saved := fixture([18,15] if room==3 else Region2Ruins.landing(room),room)
		check(game.import_state(saved),"遭遇測定の人工起点",room)
		var start := WorldExpedition.point(saved["overworld"]["cell"])
		var neighbor := start
		for dir in DIRS:
			if game.first_region_walkable(start+dir):neighbor=start+dir;break
		for i in range(2000):
			var next: Vector2i = neighbor if i%2==0 else start
			var result := game.move_first_region(next)
			if result.get("kind")!="moved":continue
			var encounter := game.take_region2_ruins_encounter()
			if not encounter.is_empty():hits[room]+=1;groups[room][str(encounter["enemies"])]=true
			check(game.take_region2_ruins_encounter().is_empty(),"同じ移動通知は一度だけ消費")
		check((hits[room]>15 and hits[room]<90) if room<3 else hits[room]==0,"固定seed2000歩の遭遇/最下層0",[room,hits[room]])
		check(groups[room].size()==[2,3,3,0][room],"採用編成を全て観測",[room,groups[room]])
	for link in Region2Ruins.data()["stairs"]:
		var cell: Array=link["from_cell"];var saved := fixture(link["to_cell"],link["from_room"])
		var found := false
		for dir in DIRS:
			var prior: Vector2i = WorldExpedition.point(cell)+dir
			saved["overworld"]["cell"]=[prior.x,prior.y]
			if not FirstRegion.walkable(saved,prior):continue
			check(game.import_state(saved),"階段直前の有効状態")
			check(game.move_first_region(WorldExpedition.point(cell)).get("kind")=="moved" and game.take_region2_ruins_encounter().is_empty(),"全階段遷移歩無遭遇")
			found=true;break
		check(found,"階段前へ到達可能")
	PlaySessionMetrics.write_json(OUT+"encounters.json",{"steps_per_room":2000,"seed":85,"hits":hits,"groups":groups})

func ai_cases() -> void:
	var expected := {"ruins_sandstone_doll":["attack","attack","attack","attack","attack","attack","attack"],"ruins_cursed_beetle":["firm_guard","shell_bash","firm_guard","attack","attack","attack","attack"],"ruins_sand_spirit":["wind_blade","wind_blade","wind_blade","wind_blade","attack","attack","attack"],"ruins_tomb_hound":["fang","fang","attack","attack","attack","attack","attack"],"ruins_sandstone_colossus":["firm_guard","power_strike","power_strike","firm_guard","power_strike","power_strike","attack"]}
	var game := GameSession.new();check(game.import_state(fixture()),"AI用人工状態")
	for id in expected:
		var battle := game.start_battle([id],85)
		for turn in range(7):
			var planned: BattleAction = battle._choose_enemy_action(battle.living(Combatant.Team.ENEMY)[0])
			check((planned.ability_id if planned.kind==BattleAction.Kind.ABILITY else "attack")==expected[id][turn],"既存AIの予定列",[id,turn])
			for actor in battle.pending():battle.queue_action(BattleAction.guard(actor.id))
			battle.resolve_round()
		check(battle.living(Combatant.Team.ENEMY)[0].mp==[0,2,0,0,0][expected.keys().find(id)],"MP枯渇後の通常攻撃",id)
		# AIの独立境界測定。HPを書き換えず保存済み起点の別セッションへ戻す。
		game=GameSession.new();check(game.import_state(fixture()),"次AIの独立起点")

func _initialize() -> void:
	OS.set_environment("RPG_QA_SAVE_PREFIX","task085")
	call_deferred("run")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	if "--resupply" in OS.get_cmdline_user_args():resupply_case()
	elif "--balance" in OS.get_cmdline_user_args():balance_cases()
	elif "--route" in OS.get_cmdline_user_args():
		real_route()
		check(route_complete,"新規開始から取得・徒歩帰還まで到達")
	else:api_cases()
	var failed := checks.filter(func(c:Dictionary)->bool:return not c["ok"])
	var name := "resupply" if "--resupply" in OS.get_cmdline_user_args() else "balance" if "--balance" in OS.get_cmdline_user_args() else "route" if "--route" in OS.get_cmdline_user_args() else "runtime"
	PlaySessionMetrics.write_json(OUT+name+"-checks.json",{"status":"PASS" if failed.is_empty() else "FAIL","checks":checks,"battles":battles,"steps":steps,"method":"通常新規からAPI実進行" if name=="route" else "人工境界API・実ターン"})
	print("S11_%s: %s checks=%d failures=%d"%["PASS" if failed.is_empty() else "FAIL",name,checks.size(),failed.size()])
	quit(0 if failed.is_empty() else 1)

func point(node: String, room: int, cell: Array) -> Dictionary:
	return {"layer":"world" if node.is_empty() else "interior","node":node,"room":room,"cell":cell}

func same_room(a: Dictionary,b: Dictionary) -> bool:
	return a["layer"]==b["layer"] and a["node"]==b["node"] and a["room"]==b["room"]

func all_links() -> Array:
	var d := FirstRegion.data();var result: Array=[]
	for key in ["doors","castle_doors","tower_doors","port_doors","second_port_doors","region2_village_doors","region3_port_doors"]:result.append_array(d.get(key,[]))
	for key in ["stairs_down","stairs_up"]:result.append(d[key])
	for pair in [["village_entrance","village_spawn","village_exit"],["cave_entrance","cave_spawn","cave_exit"],["castle_entrance","castle_spawn","castle_exit"],["tower_entrance","tower_spawn","tower_exit"],["port_entrance","port_spawn","port_exit"],["second_port_entrance","second_port_spawn","second_port_exit"]]:
		result.append({"from":point("",0,d[pair[0]]["cell"]),"to":d[pair[1]]})
		result.append({"from":d[pair[2]],"to":FirstRegion.outside(pair[0])})
	result.append({"from":point("",0,d["region2_village_entrance"]["cell"]),"to":d["region2_village_spawn"]})
	result.append_array(d["region2_village_exits"])
	var c: Dictionary=Region2Ruins.data()["world_connection"]
	result.append({"from":point("",0,c["world_cell"]),"to":point("region2_ruins",0,c["landing"])})
	result.append({"from":point("region2_ruins",0,c["exit_cell"]),"to":point("",0,c["return_cell"])})
	for link in Region2Ruins.data()["stairs"]:result.append({"from":point("region2_ruins",link["from_room"],link["from_cell"]),"to":point("region2_ruins",link["to_room"],link["to_cell"])})
	return result

func path_to(saved: Dictionary, goal: Vector2i) -> Array[Vector2i]:
	var here: Dictionary=saved["overworld"];var start:=WorldExpedition.point(here["cell"])
	var blocked: Dictionary={}
	for link in all_links():
		if same_room(here,link["from"]) and WorldExpedition.point(link["from"]["cell"])!=goal:blocked[WorldExpedition.point(link["from"]["cell"])]=true
	var seen: Dictionary={start:start};var todo: Array[Vector2i]=[start];var cursor:=0
	while cursor<todo.size() and not seen.has(goal):
		var current:=todo[cursor];cursor+=1
		for dir in DIRS:
			var next: Vector2i=current+dir
			if seen.has(next) or blocked.has(next) or not FirstRegion.walkable(saved,next):continue
			seen[next]=current;todo.append(next)
	var result: Array[Vector2i]=[]
	if not seen.has(goal):return result
	var current:=goal
	while current!=start:result.push_front(current);current=seen[current]
	return result

func settle(game: GameSession, event: Dictionary) -> bool:
	for guard in range(100):
		if event.is_empty() or event.get("kind")=="moved":return true
		if event.get("kind")=="battle":
			if not check(fight(game,event),"通常実進行の戦闘勝利",event):return false
			for actor in game.export_state()["party"]:
				for ability in ["heal","fire","power_strike","revive"]:
					if ability in actor["learned_abilities"] and ability not in actor["equipped_abilities"] and actor["equipped_abilities"].size()<2:game.equip_ability(actor["id"],ability)
			return true
		if event.has("story_scene"):
			var identifier: String=event["story_scene"]
			for page in range(FirstRegionStory.scene(identifier)["lines"].size()):event=game.confirm_first_region_story(identifier,page)
			continue
		if event.has("shrine_scene"):
			var identifier: String=event["shrine_scene"];var run: int=event["shrine_run"]
			for page in range(9):event=game.confirm_region2_shrine_story(identifier,run,page)
			continue
		if event.has("ruins_scene"):
			confirm_scene(game,event);return true
		if event.get("kind")=="dialogue":
			for action in event.get("line_actions",[]):
				if not str(action).is_empty():check(game.help_first_region_bandage(action),"通常台詞で包帯作業")
			if event.has("join_actor"):check(game.finish_first_region_recruit(event["join_actor"]),"通常会話で仲間加入",event["join_actor"])
			if event.get("audience",false):check(game.finish_first_region_audience(),"通常謁見で許可")
			if event.has("travel_lesson"):check(game.finish_first_region_travel(event["travel_lesson"]),"通常会話で船/帰還")
			return true
		return check(false,"未知の進行通知",event)
	return check(false,"進行通知の上限")

func walk_local(game: GameSession, cell: Array) -> bool:
	var saved:=game.export_state();var goal:=WorldExpedition.point(cell)
	var path:=path_to(saved,goal)
	if not check(not path.is_empty() or saved["overworld"]["cell"]==cell,"実進行の床経路",[saved["overworld"],cell]):return false
	for next in path:
		var before:=game.overworld_state()
		game.first_region_face(next-WorldExpedition.point(before["cell"]))
		var event:=game.move_first_region(next);steps+=1
		if event.is_empty():return check(false,"実進行一歩拒否",next)
		if event.get("kind")=="moved":
			var scene:=game.resume_region2_ruins_story()
			if not scene.is_empty():event=scene
			else:
				var encounter:=game.take_region2_ruins_encounter()
				if not encounter.is_empty():event=encounter
		if not settle(game,event):return check(false,"実進行戦闘/会話を通過できない",game.overworld_state())
	return true

func travel_to(game: GameSession, destination: Dictionary) -> bool:
	for count in range(30):
		var here:=game.overworld_state()
		if same_room(here,destination):return walk_local(game,destination["cell"])
		var queue: Array=[{"at":here,"route":[]}];var seen: Dictionary={str([here["layer"],here["node"],here["room"]]):true};var cursor:=0;var selected: Array=[]
		while cursor<queue.size():
			var item: Dictionary=queue[cursor];cursor+=1
			if same_room(item["at"],destination):selected=item["route"];break
			for link in all_links():
				if not same_room(item["at"],link["from"]):continue
				var key:=str([link["to"]["layer"],link["to"]["node"],link["to"]["room"]])
				if seen.has(key):continue
				seen[key]=true;queue.append({"at":link["to"],"route":item["route"]+[link]})
		if not check(not selected.is_empty(),"部屋間の既存経路",destination):return false
		if not walk_local(game,selected[0]["from"]["cell"]):return false
		if not check(same_room(game.overworld_state(),selected[0]["to"]),"通常歩行で扉/階段遷移",selected[0]):return false
	return check(false,"部屋間遷移の上限")

func interact_event(game: GameSession,node: String,room: int,id: String) -> bool:
	var destination:=point(node,room,FirstRegion.entrance_landing(node,room))
	if not travel_to(game,destination):return false
	for event in FirstRegion.residents_for(game.export_state()):
		if event["id"]!=id:continue
		var cell:=FirstRegion.event_cell(game.export_state(),event)
		for distance in range(1,int(event.get("reach",1))+1):
			for dir in DIRS:
				var stand: Vector2i=cell-dir*distance
				if not game.first_region_walkable(stand) or path_to(game.export_state(),stand).is_empty():continue
				if not walk_local(game,[stand.x,stand.y]):return false
				game.first_region_face(dir)
				return settle(game,game.interact_first_region())
	return check(false,"通常調査の相手へ届かない",[node,room,id])

func real_route() -> void:
	seed(20261029)
	route_game=GameSession.new();var game:=route_game
	if not check(game.new_first_region(),"実進行の通常新規開始"):return
	if not settle(game,game.interact_first_region()):return
	for id in ["join_pc_02","join_pc_03"]:
		if not interact_event(game,"start_village",1,id):return
	if not check(game.export_state()["party"].size()==3,"実加入で3人"):return
	if not travel_to(game,FirstRegion.data()["cave_spawn"]):return
	if not travel_to(game,FirstRegion.data()["boss"]["point"]):return
	if not travel_to(game,FirstRegion.data()["village_spawn"]):return
	if not interact_event(game,"start_village",2,"village_inn"):return
	if not interact_event(game,"first_castle",2,"king"):return
	if not interact_event(game,"first_castle",4,"castle_inn"):return
	if not interact_event(game,"first_castle",3,"castle_supplies"):return
	if not travel_to(game,FirstRegion.data()["tower_boss"]["point"]):return
	if not interact_event(game,"first_forest_tower",2,"recruit_suina"):return
	if not check(game.export_state()["party"].size()==4,"通常進行で4人目加入"):return
	if not interact_event(game,"first_port",1,"port_inn"):return
	if not interact_event(game,"first_port",5,"port_shrine"):return
	if not interact_event(game,"first_port",7,"harbor_keeper"):return
	var first_dock: Dictionary=FirstRegionTravel.data()["docks"][0]
	if not travel_to(game,first_dock["land"]):return
	if not check(game.board_first_region_ship(),"通常桟橋から乗船"):return
	var dock: Dictionary=SecondRegionCoast.data()["docks"][0]
	if not walk_local(game,dock["ship_cell"]):return
	if not check(game.board_first_region_ship(),"通常航路から第2地方へ下船"):return
	if not interact_event(game,"region2_village",1,"oasis_innkeeper"):return
	if not travel_to(game,point("region2_village",4,[8,10])):return
	if not settle(game,game.resume_region2_shrine_story()):return
	if not check(game.export_state()["progress_flags"].get(Region2ShrineStory.COMPLETE_FLAG,false),"通常進行でS10読了"):return
	if not travel_to(game,point("region2_ruins",0,[18,19])):return
	PlaySessionMetrics.write_json(OUT+"real-arrival-state.json",game.export_state())
	if not check(game.save_game("user://task085-real-arrival.json"),"実到達戦力の通常保存"):return
	if not travel_to(game,point("region2_ruins",3,[18,15])):return
	if not check(game.export_state()["progress_flags"].get(Region2RuinsStory.COMPLETE_FLAG,false),"実経路で記録読了"):return
	if not walk_local(game,[31,13]):return
	game.first_region_face(Vector2i.UP)
	PlaySessionMetrics.write_json(OUT+"real-before-boss-state.json",game.export_state())
	if not settle(game,game.interact_first_region()):return
	if not check(Region2RuinsStory.BOSS in game.overworld_state()["cleared"],"実到達人間4職でボス勝利"):return
	if not walk_local(game,[31,9]):return
	game.first_region_face(Vector2i.UP)
	if not settle(game,game.interact_first_region()):return
	if not check(game.export_state()["inventory"].get(Region2RuinsStory.KEY,0)==1,"実経路の別箱取得"):return
	if not interact_event(game,"region2_village",1,"oasis_innkeeper"):return
	PlaySessionMetrics.write_json(OUT+"real-returned-state.json",game.export_state())
	route_complete=check(game.save_game("user://task085-real-return.json"),"実帰還の通常保存")

func balance_cases() -> void:
	var source: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string(OUT+"real-before-boss-state.json")))
	check(not source.is_empty(),"通常実到達の保存を比較基準にする")
	for policy in ["standard","physical","no_heal","initial_monsters"]:
		for number in range(1,10):
			var game:=GameSession.new()
			if not check(game.import_state(source),"実到達戦力を全値復元",[policy,number]):continue
			if policy=="no_heal":
				for actor in game.export_state()["party"]:
					for ability in ["heal","revive"]:
						if ability in actor["equipped_abilities"]:check(game.unequip_ability(actor["id"],ability),"通常操作で回復を外す")
			if policy=="initial_monsters":
				var jobs: Array=["slime","beast","plant","shell"]
				for i in range(4):check(game.choose_job(game.export_state()["party"][i]["id"],jobs[i]),"S10で解放済みの初期4職を通常選択",jobs[i])
			var event:=game.interact_first_region();event["seed"]=number
			var won:=fight(game,event,"physical" if policy=="physical" else "standard")
			if policy=="standard":check(won,"実到達全人間4職・9seedの勝利",number)
			check(game.save_game("user://task085-balance.json"),"試行後も通常保存が有効",[policy,number,won])
			battles[-1]["scenario"]=policy

func resupply_case() -> void:
	seed(85)
	var source: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string(OUT+"real-arrival-state.json")))
	var game:=GameSession.new()
	if not check(game.import_state(source),"途中帰還は通常実到達保存から開始"):return
	if not travel_to(game,point("region2_ruins",2,[3,6])):return
	if not interact_event(game,"region2_village",1,"oasis_innkeeper"):return
	check(not game.export_state()["progress_flags"].get(Region2RuinsStory.COMPLETE_FLAG,false) and game.export_state()["inventory"].get(Region2RuinsStory.KEY,0)==0,"途中補給で未見/未取得を補完しない")
	for actor in game.export_state()["party"]:check(actor["hp"]==actor["max_hp"] and actor["mp"]==actor["max_mp"],"通常宿屋で補給")
	if not travel_to(game,point("region2_ruins",3,[18,15])):return
	if not walk_local(game,[31,13]):return
	game.first_region_face(Vector2i.UP)
	if not check(settle(game,game.interact_first_region()),"再訪後に実攻略"):return
	if not walk_local(game,[31,9]):return
	game.first_region_face(Vector2i.UP);settle(game,game.interact_first_region())
	if not interact_event(game,"region2_village",1,"oasis_innkeeper"):return
	check(Region2RuinsStory.BOSS in game.overworld_state()["cleared"] and game.export_state()["inventory"].get(Region2RuinsStory.KEY,0)==1,"途中補給・再訪・攻略・徒歩帰還が成立")
