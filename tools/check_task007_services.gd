extends SceneTree
## 007の施設・住人。完成時の配置は--stage、継続サービスは最新コードでも検査する。
const OUTPUT := "res://docs/verification/task-007/latest/"
const IDS := ["water_keeper","date_farmer","innkeeper","camel_keeper","elder","child"]
const ROOMS := [0,2,1,3,4,0]
const CELLS := [[29,12],[8,4],[12,3],[8,4],[12,6],[17,19]]
const TEXTS := ["泉のそばでは、足元に気をつけてください。","店の品物は、まだ準備中です。","宿で休み、HPとMPが回復しました。","ここは武器屋です。品物は、まだ準備中です。","ここで旅の身支度を整えていってください。","風が吹くと、風車がよく回るんだ。"]
const DIRECTIONS := [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]
var failures: Array[String] = []
var checks := 0
var base: Dictionary
var records: Array = []
var stage := false
var started := Time.get_ticks_msec()

func check(ok: bool, reason: String) -> bool:
	checks+=1
	if not ok:failures.append(reason)
	return ok

func placed(index: int, cell: Array, node: String="region2_village") -> Dictionary:
	var saved := base.duplicate(true)
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":node,"room":index,"cell":cell})
	return saved

func session(saved: Dictionary) -> GameSession:
	var game := GameSession.new()
	check(game.import_state(saved),"検査境界の本番状態受理")
	return game

func reachable(saved: Dictionary) -> Dictionary:
	var start := WorldExpedition.point(saved["overworld"]["cell"])
	var found := {start:true};var queue: Array[Vector2i]=[start];var cursor := 0
	while cursor<queue.size():
		var cell := queue[cursor];cursor+=1
		for direction in DIRECTIONS:
			var next: Vector2i=cell+direction
			if found.has(next) or not FirstRegion.walkable(saved,next):continue
			found[next]=true;queue.append(next)
	return found

func _initialize() -> void:
	stage="--stage" in OS.get_cmdline_user_args()
	var initial := GameSession.new();check(initial.new_first_region(),"新規状態")
	base=initial.export_state()
	base["party"].append_array(base["first_region"]["reserve"]);base["first_region"]["reserve"]=[]
	base["inventory"]["gate_pass"]=1
	for flag in ["castle_north_permission","mountain_path_open","job_change_unlocked"]:base["progress_flags"][flag]=true
	base["overworld"]["cleared"]=["first_boss","forest_tower_boss"]
	base["overworld"]["transport"]="walk"
	base["first_region"]["travel"]={"version":1,"visited":["start_village","first_castle","first_port","brine_port"],"return_learned":true,"ship_owned":true,"ship_cell":[155,110]}
	base["first_region"]["coins"]=37
	for actor in base["party"]:actor["hp"]=0;actor["mp"]=0
	# 撮影の境界入力は通常保存した港内。以降の撮影は一切の状態注入をしない。
	var origin := placed(0,[4,2],"brine_port")
	for actor in origin["party"]:actor["hp"]=actor["max_hp"]-3;actor["mp"]=actor["max_mp"]-2
	var actor: Dictionary=origin["party"][0];actor["erosion"]=60
	var start := session(origin)
	check(start.save_game("user://task007_port-start.json"),"撮影起点の通常保存")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	var stored := FileAccess.open(OUTPUT+"port-start.json",FileAccess.WRITE)
	if check(stored!=null,"撮影起点の保管"):stored.store_buffer(FileAccess.get_file_as_bytes("user://task007_port-start.json"));stored.close()
	residents();inn();shrine();forms();saves();finish()

func residents() -> void:
	var all: Array=[]
	for index in range(5):
		var events: Array=FirstRegion.room(placed(index,[4,15] if index==0 else [8,10])["overworld"])["events"]
		for event in events:all.append({"room":index,"event":event})
	if stage:check(all.size()==6,"完成時は住人6人だけ")
	for index in range(6):
		var entries := all.filter(func(row:Dictionary)->bool:return row["event"]["id"]=="oasis_"+IDS[index])
		if not check(entries.size()==1,"各住人は1か所だけ: "+IDS[index]):continue
		var room: int=entries[0]["room"];var event: Dictionary=entries[0]["event"]
		check(room==ROOMS[index] and event["kind"]==("rest" if index==2 else "npc"),"施設担当の役割と販売なし: "+IDS[index])
		if stage:
			check(event["cell"]==CELLS[index] and event["sprite"]=="npc_oasis_"+IDS[index],"完成時の配置・専用素材")
			check(event["text"]==[TEXTS[index]],"完成時の短い非ネタバレ会話")
		var saved := placed(room,[4,15] if room==0 else [8,10]);var cell := WorldExpedition.point(event["cell"])
		check(FirstRegion.room(saved["overworld"])["layout"][cell.y][cell.x]=="." and not FirstRegion.walkable(saved,cell),"床と人物の占有を区別")
		var connected := reachable(saved);var approach := Vector2i(-1,-1)
		for direction in DIRECTIONS:
			for distance in range(1,int(event.get("reach",1))+1):
				if connected.has(cell+direction*distance):approach=cell+direction*distance;break
			if approach.x>=0:break
		if not check(approach.x>=0,"入口から受付・住人の話しかけ位置に到達"):continue
		var game := session(placed(room,[approach.x,approach.y]))
		var delta := cell-approach;var face := Vector2i(signi(delta.x),signi(delta.y))
		game.first_region_face(-face);var before := game.export_state()
		check(game.interact_first_region().is_empty() and game.export_state()==before,"逆向きでは会話・回復なし")
		game.first_region_face(face);before=game.export_state()
		var result := game.interact_first_region()
		check(result.get("kind")=="dialogue" and result.get("text",[]).size()>0,"6人の本番会話")
		if stage:check(result.get("text")==[TEXTS[index]],"完成時の本番会話文一致")
		var after := game.export_state()
		check(after["first_region"]["coins"]==before["first_region"]["coins"] and after["inventory"]==before["inventory"] and after["integrated"]==before["integrated"] and after["progress_flags"]==before["progress_flags"],"会話・宿泊で取引・解放・料金を追加しない")
		check(FirstRegion.event_facing(after,event)==DIRECTIONS.find(-face),"話しかけた人物はこちらを向く")
		records.append({"id":event["id"],"room":room,"cell":event["cell"],"approach":[approach.x,approach.y],"result":result})

func inn() -> void:
	var game := session(placed(1,[12,5]));game.first_region_face(Vector2i.UP)
	var before := game.export_state();var result := game.interact_first_region();var after := game.export_state()
	check(result.get("kind")=="dialogue" and result.get("sound")=="heal","受付台越しに既存宿処理")
	for index in range(4):
		check(after["party"][index]["hp"]==after["party"][index]["max_hp"] and after["party"][index]["mp"]==after["party"][index]["max_mp"],"倒れた人も含め全員HP/MP回復")
	var expected := before.duplicate(true)
	for actor in expected["party"]:actor["hp"]=actor["max_hp"];actor["mp"]=actor["max_mp"]
	expected["overworld"]["residents"]=after["overworld"]["residents"].duplicate(true)
	check(after==expected,"回復と対面以外の全状態不変・料金なし")
	var healthy := placed(1,[12,5])
	for actor in healthy["party"]:actor["hp"]=actor["max_hp"]
	var battle_game := session(healthy);check(battle_game.start_battle([str(battle_game.enemy_definitions.keys()[0])] ,7007)!=null,"宿の戦闘負例は実戦闘を開始")
	before=battle_game.export_state()
	check(not battle_game.rest() and battle_game.interact_first_region().is_empty() and battle_game.export_state()==before,"戦闘中の宿・回復拒否")

func make_irreversible(saved: Dictionary) -> void:
	var actor: Dictionary=saved["party"][0]
	actor["irreversible"]=true;actor["job_id"]="beast"
	var template := GameSession.new()
	var caps := template._compute_stats(actor,true)
	actor["max_hp"]=caps["hp"];actor["max_mp"]=caps["mp"];actor["hp"]=0;actor["mp"]=0

func shrine() -> void:
	for room in range(5):
		var game := session(placed(room,[4,15] if room==0 else [8,10]))
		check(game.at_purification_shrine()==(room==4),"祠の場所を室4に限定")
	for erosion in [0,29,30,60,89,90,100]:
		for room in [0,4]:
			var saved := placed(room,[4,15] if room==0 else [8,10]);saved["party"][0]["erosion"]=erosion
			if erosion>=90:make_irreversible(saved)
			var game := session(saved);var before := game.export_state()
			var result := game.release_monster_form("pc_01","purification_shrine")
			var expected: bool=room==4 and erosion>0 and erosion<=89
			check(result==expected,"既存の正負境界: 室%d 値%d" % [room,erosion])
			if expected:check(game.export_state()["party"][0]["erosion"]==maxi(0,erosion-30),"既存低下30")
			else:check(game.export_state()==before,"拒否時に全状態不変")
			# 従来の第2港の祠と場所を除く全状態が一致する。
			var port := saved.duplicate(true);FirstRegion.place(port["overworld"],{"layer":"interior","node":"brine_port","room":5,"cell":[8,10]})
			var existing := session(port);var port_result := existing.release_monster_form("pc_01","purification_shrine")
			if room==4:
				var left := game.export_state();var right := existing.export_state();left.erase("overworld");right.erase("overworld")
				check(port_result==result and left==right,"従来祠との同条件・同全状態")
	for negative in ["irreversible","wrong_event","unknown_actor","battle"]:
		var saved := placed(4,[8,10]);saved["party"][0]["erosion"]=60
		for actor in saved["party"]:actor["hp"]=actor["max_hp"]
		if negative=="irreversible":make_irreversible(saved)
		var game := session(saved)
		if negative=="battle":check(game.start_battle([str(game.enemy_definitions.keys()[0])] ,7007)!=null,"祠の戦闘負例は実戦闘を開始")
		var before := game.export_state()
		check(not game.release_monster_form("missing" if negative=="unknown_actor" else "pc_01","wrong" if negative=="wrong_event" else "purification_shrine") and game.export_state()==before,"既存祠の拒否条件: "+negative)

func forms() -> void:
	var template := GameSession.new()
	var tested := 0
	var human_skills: Array=[]
	for job in template.jobs.values():
		if job["type"]=="human":human_skills.append_array(job["abilities"])
	for id in ["slime","beast","undead","bird","plant","shell","spirit","dragon"]:
		var saved := placed(4,[8,10]);var actor: Dictionary=saved["party"][0]
		var job: Dictionary=template.jobs[id]
		actor["jp"][id]=IntegratedProgression.cost(job,true)
		actor["integrated"]["mastery"]["counts"][id]=int(job["mastery_action"]["required"])
		actor["mastered_jobs"]=[id];actor["job_id"]=id;actor["monster_form"]=id;actor["erosion"]=60
		for skill in job["abilities"]+job["monster_form"]["abilities"]:
			if skill not in actor["learned_abilities"]:actor["learned_abilities"].append(skill)
		var stats := template._compute_stats(actor,true);actor["max_hp"]=stats["hp"];actor["max_mp"]=stats["mp"]
		var game := session(saved);var before := game.export_state()
		check(game.release_monster_form("pc_01","purification_shrine"),"既存の魔物化解除: "+id)
		var after: Dictionary=game.export_state()["party"][0]
		check(after["monster_form"]=="" and after["job_id"]==actor["last_human_job"] and after["erosion"]==30,"姿・職・低下30: "+id)
		check(after["mastered_jobs"]==actor["mastered_jobs"] and after["jp"]==actor["jp"] and after["integrated"]["mastery"]==actor["integrated"]["mastery"],"マスター成長と修練を保持: "+id)
		for skill in job["abilities"]+job["monster_form"]["abilities"]:
			check((skill in after["learned_abilities"])==(skill in human_skills),"専用技だけ忘却、人間職の共有技は保持: "+id+" "+skill)
		var port := before.duplicate(true);FirstRegion.place(port["overworld"],{"layer":"interior","node":"brine_port","room":5,"cell":[8,10]})
		var existing := session(port);check(existing.release_monster_form("pc_01","purification_shrine"),"従来祠の同じ姿の解除: "+id)
		var left := game.export_state();var right := existing.export_state();left.erase("overworld");right.erase("overworld")
		check(left==right,"全8系統で従来祠との全状態一致: "+id);tested+=1
	check(tested==8,"全8系統の祠回帰")

func saves() -> void:
	for record in records:
		var game := session(placed(record["room"],record["approach"]));game.first_region_face(Vector2i.UP)
		var file: String = "user://task007_"+record["id"]+".json";var before := game.export_state()
		check(game.save_game(file),"住人隣接位置の通常保存")
		var restored := GameSession.new();check(restored.load_game(file) and restored.export_state()==before,"6会話位置の全状態保存・再開")
		var raw: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(file));raw["overworld"]["cell"]=record["cell"]
		check(PlaySessionMetrics.write_json(file,raw),"追加NPCマスに立つ旧保存の再現")
		check(restored.load_game(file) and restored.position_relocated and restored.export_state()["overworld"]["cell"]==FirstRegion.entrance_landing("region2_village",record["room"]),"新NPC占有を既存の入口補正へ")

func finish() -> void:
	check(Time.get_ticks_msec()-started<180000,"既存180秒以内")
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"residents":records,"stage":stage,"execution_sha":OS.get_environment("TASK007_EXECUTION_SHA")}
	PlaySessionMetrics.write_json(OUTPUT+"services.json",report)
	for failure in failures:printerr("TASK007_SERVICES_FAIL: "+failure)
	print("TASK007_SERVICES_PASS: checks=%d residents=%d" % [checks,records.size()] if failures.is_empty() else "TASK007_SERVICES_FAIL")
	quit(0 if failures.is_empty() else 1)
