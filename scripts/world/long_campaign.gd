class_name LongCampaign
extends RefCounted

const PATH: String="res://data/long_campaign_v1.json"
const REGIONS: Array[String]=["waterway","cave","school","records","gate"]
static var _source: Dictionary={}
static var _missions: Dictionary={}
static var _rooms: Dictionary={}
static var _audit_connectivity: Dictionary={}

static func data()->Dictionary:
	if _source.is_empty() and FileAccess.file_exists(PATH):
		var parsed: Variant=JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if parsed is Dictionary:
			_source=_integers(parsed)
			for mission in _source.get("missions",[]):_missions[mission["id"]]=mission
			for room in _source.get("rooms",[]):_rooms[room["id"]]=room
	return _source

static func _integers(value: Variant)->Variant:
	if value is Dictionary:
		var result: Dictionary={}
		for key in value:result[key]=_integers(value[key])
		return result
	if value is Array:
		var result: Array=[]
		for item in value:result.append(_integers(item))
		return result
	return int(value) if value is float and value==floor(value) else value

static func enabled()->bool:
	return bool(data().get("enabled",false))

static func mission(identifier: String)->Dictionary:
	data()
	return _missions.get(identifier,{})

static func room(identifier: String)->Dictionary:
	data()
	return _rooms.get(identifier,{})

static func cleared_flag(identifier: String)->String:
	return "journey_"+identifier+"_cleared"

static func activity_flag(identifier: String, suffix: String)->String:
	return "journey_activity_"+identifier+"_"+suffix

static func choice_flag(identifier: String, option: int)->String:
	return "journey_choice_"+identifier+"_"+str(option)

static func available(state: Dictionary)->Array[Dictionary]:
	var result: Array[Dictionary]=[]
	var flags: Dictionary=state.get("progress_flags",{})
	if not enabled() or not flags.get("long_campaign_enrolled",false) or not flags.get("long_campaign_started",false) or not state.get("expedition",{}).is_empty() or not state.get("return_point",{}).is_empty():return result
	for entry in data().get("missions",[]):
		if entry["trigger_step"]!=state.get("world",{}).get("quest_step") or flags.get(cleared_flag(entry["id"]),false):continue
		var ready:=true
		for prerequisite in entry.get("requires",[]):
			ready=ready and bool(flags.get(cleared_flag(prerequisite),false))
		if ready:result.append(entry)
	return result

static func pending(state: Dictionary, requested: String="")->Dictionary:
	for entry in available(state):
		if requested.is_empty() or entry["id"]==requested:return entry
	return {}

static func step(expedition: Dictionary, flags: Dictionary={})->Dictionary:
	var entry:=mission(str(expedition.get("id","")))
	var index:=int(expedition.get("stage",-1))
	if entry.is_empty() or index<0 or index>=entry["steps"].size():return {}
	var result: Dictionary=entry["steps"][index].duplicate(true)
	for reference in result.get("responses",[]):
		for option in range(reference["variants"].size()):
			if flags.get(choice_flag(reference["choice"],option),false):
				result["text"].append_array(reference["variants"][option])
	return result

static func all_cleared(flags: Dictionary)->bool:
	if data().get("missions",[]).size()!=80:return false
	for entry in data()["missions"]:
		if not flags.get(cleared_flag(entry["id"]),false):return false
	return true

static func clue_stage(identifier: String, state: Dictionary)->int:
	if not state.get("progress_flags",{}).get("long_campaign_started",false):return 0
	var clues: Dictionary={}
	for clue in data().get("clues",[]):clues[clue["id"]]=clue
	if not clues.has(identifier):return 0
	var clue: Dictionary=clues[identifier]
	if not _read_clue_point(clue["setup"],state):return 0
	if not _read_clue_point(clue["payoff"],state):return 1
	for prerequisite in clue.get("requires",[]):
		if not clues.has(prerequisite):return 1
		if not _read_clue_point(clues[prerequisite]["setup"],state) or not _read_clue_point(clues[prerequisite]["payoff"],state):return 1
	return 2

static func _read_clue_point(reference: Dictionary, state: Dictionary)->bool:
	if state.get("progress_flags",{}).get(cleared_flag(reference["mission"]),false):return true
	var current: Dictionary=state.get("expedition",{})
	if current.get("id")!=reference["mission"]:return false
	var steps: Array=mission(reference["mission"]).get("steps",[])
	for index in range(steps.size()):
		if steps[index]["id"]==reference["step"]:return int(current.get("stage",-1))>index
	return false

static func journal(state: Dictionary)->Array[Dictionary]:
	var result: Array[Dictionary]=[]
	for clue in data().get("clues",[]):
		var level:=clue_stage(clue["id"],state)
		if level==0:continue
		var entry: Dictionary={"id":clue["id"],"title":clue["title"],"stage":level,
			"observation":clue["setup"]["text"],"first":clue["first"]}
		if level==2:entry["resolved"]=clue["resolved"]+"\nそのときの問い: "+clue["next_question"]
		result.append(entry)
	return result

static func is_walkable(identifier: String, cell: Vector2i, flags: Dictionary={})->bool:
	var definition:=room(identifier)
	if definition.is_empty() or cell.x<0 or cell.y<0 or cell.y>=definition["layout"].size() or cell.x>=definition["layout"][cell.y].length():return false
	if definition["layout"][cell.y].substr(cell.x,1)==".":return true
	for passage in definition.get("passages",[]):
		if passage["cell"]==[cell.x,cell.y] and flags.get(passage["flag"],false):return true
	if IntegratedCampaign.route_open(identifier,cell,flags):return true
	return false

static func walkable_cells(identifier: String, flags: Dictionary={})->Array:
	var definition:=room(identifier)
	var result: Array=[]
	if definition.is_empty():return result
	for y in range(definition["layout"].size()):
		for x in range(definition["layout"][y].length()):
			if is_walkable(identifier,Vector2i(x,y),flags):result.append([x,y])
	return result

static func validate_flags(flags: Dictionary, active: Dictionary={})->bool:
	if flags.get("long_campaign_started",false) and (not flags.get("long_campaign_enrolled",false) or not flags.get("chapter1_cleared",false)):return false
	var known: Dictionary={}
	for entry in data().get("missions",[]):
		known[cleared_flag(entry["id"])]=true
		for activity in entry.get("activities",[]):
			var touched := false
			for suffix in ["seen_0","seen_1","done","supported"]:
				var key := activity_flag(activity["id"],suffix)
				known[key] = true
				touched = touched or flags.get(key,false)
			var done: bool = flags.get(activity_flag(activity["id"],"done"),false)
			if done and (not flags.get(activity_flag(activity["id"],"seen_0"),false) or not flags.get(activity_flag(activity["id"],"seen_1"),false)):return false
			if flags.get(activity["support_flag"],false) and not done:return false
			if flags.get(cleared_flag(entry["id"]),false) and not done:return false
			if touched:
				if not flags.get("long_campaign_started",false):return false
				if not flags.get(cleared_flag(entry["id"]),false) and (active.get("id")!=entry["id"] or int(active.get("stage",-1))<int(activity["unlock_stage"])):return false
		if flags.get(cleared_flag(entry["id"]),false):
			if not flags.get("long_campaign_started",false):return false
			for prerequisite in entry.get("requires",[]):
				if not flags.get(cleared_flag(prerequisite),false):return false
		for task in entry["steps"]:
			if not task.get("choice",false):continue
			var selected:=0
			for option in range(task["options"].size()):
				var key:=choice_flag(task["id"],option)
				known[key]=true
				selected+=1 if flags.get(key,false) else 0
				var effects: Array=task.get("choice_effects",[])
				if option<effects.size():
					for effect in effects[option].get("flags",[]):
						known[effect]=true
						if bool(flags.get(effect,false))!=bool(flags.get(key,false)):return false
			if selected>1 or (flags.get(cleared_flag(entry["id"]),false) and selected!=1):return false
			if selected>0 and not flags.get(cleared_flag(entry["id"]),false) and active.get("id")!=entry["id"]:return false
	for key in flags:
		if str(key).begins_with("journey_") and not known.has(key):return false
	return true

static func valid_state(state: Dictionary)->bool:
	var current: Dictionary=state.get("expedition",{})
	var flags: Dictionary=state["progress_flags"]
	if not enabled() or not flags.get("long_campaign_started",false) or not validate_flags(flags,current):return false
	if not current.has_all(["id","stage","wave","origin","solved"]):return false
	if not current["stage"] is int or not current["wave"] is int or not current["origin"] is Dictionary or not current["solved"] is Array:return false
	var source:=mission(current["id"])
	var task:=step(current,flags)
	if source.is_empty() or task.is_empty() or flags.get(cleared_flag(current["id"]),false):return false
	for prerequisite in source.get("requires",[]):
		if not flags.get(cleared_flag(prerequisite),false):return false
	var base:=StoryCampaign.step(source["trigger_step"])
	var origin: Dictionary=current["origin"]
	if origin.get("location")!=base["location"] or origin.get("player_cell")!=base["cell"] or origin.get("quest_step")!=source["trigger_step"] or not str(origin.get("section","")).is_empty():return false
	var world: Dictionary=state["world"] if state.get("return_point",{}).is_empty() else state["return_point"]
	if world.get("quest_step")!=source["trigger_step"] or world.get("location")!=task["location"] or world.get("section")!=task["section"]:return false
	if current["wave"]<0 or current["wave"]>(1 if task["kind"]=="battle" else 0):return false
	var solved: Array=[]
	for index in range(source["steps"].size()):
		var previous: Dictionary=source["steps"][index]
		if previous["kind"]=="challenge" and index<current["stage"]:solved.append(previous["id"])
		if index<current["stage"] and previous.has("required_activity") and not flags.get(activity_flag(previous["required_activity"],"done"),false):return false
		if not previous.get("choice",false):continue
		var count:=0
		for option in range(previous["options"].size()):count+=1 if flags.get(choice_flag(previous["id"],option),false) else 0
		if count!=(1 if index<current["stage"] else 0):return false
	return current["solved"]==solved

static func audit(abilities: Dictionary, enemies: Dictionary)->Array[String]:
	var errors: Array[String]=[]
	var document:=data()
	if document.is_empty():return ["長編のデータがない"]
	var room_ids: Dictionary={}
	var mission_ids: Dictionary={}
	var step_ids: Dictionary={}
	var passage_flags: Dictionary={}
	for area in document.get("rooms",[]):
		if room_ids.has(area.get("id")):errors.append("区画IDの重複")
		room_ids[area.get("id")]=true
		if area.get("location") not in REGIONS or area.get("layout",[]).size()!=18:errors.append("区画の場所または高さが不正")
		for row in area.get("layout",[]):
			if not row is String or row.length()!=32:errors.append("区画の幅が不正")
		var spawn: Array=area.get("spawn",[])
		if spawn.size()!=2 or not is_walkable(area["id"],Vector2i(spawn[0],spawn[1])):errors.append("区画の開始地点が不正")
		for passage in area.get("passages",[]):
			var at: Array=passage.get("cell",[])
			if at.size()!=2 or at[0]<=0 or at[0]>=31 or at[1]<=0 or at[1]>=17:errors.append("近道の位置が不正");continue
			if is_walkable(area["id"],Vector2i(at[0],at[1]),{}):errors.append("近道が最初から開いている")
			if passage_flags.has(passage.get("flag")):errors.append("近道フラグの重複")
			passage_flags[passage.get("flag")]=true
	for entry in document.get("missions",[]):
		if mission_ids.has(entry.get("id")):errors.append("冒険IDの重複")
		mission_ids[entry.get("id")]=true
		if entry.get("region") not in REGIONS or entry.get("trigger_step") not in [19,23,28,34,38]:errors.append("既存の章・土地へ接続されていない")
		var base:=StoryCampaign.step(int(entry.get("trigger_step",-1)))
		if entry.get("chapter")!=base.get("chapter"):errors.append("章の対応が不正")
		if entry.get("activities",[]).is_empty():errors.append("現地の観察・操作がない")
		for activity in entry.get("activities",[]):
			if activity.get("observations",[]).size()!=2 or activity.get("kind") not in ["sequence","perspective","allocation","route"]:errors.append("現地課題の観察または種別が不正")
			if activity.get("answer",-1) not in range(activity.get("options",[]).size()):errors.append("現地課題の解法が不正")
			if not abilities.has(activity.get("support_ability")) or not passage_flags.has(activity.get("support_flag")):errors.append("装着を使う支援または近道が未定義")
			for marker in activity.get("observations",[])+[activity]:
				if not _reachable(activity["section"],room(activity["section"])["spawn"],marker.get("cell",[])):errors.append("現地課題へ歩いて到達できない")
			if activity.get("unlock_stage",-1) not in range(entry.get("steps",[]).size()) or entry["steps"][int(activity["unlock_stage"])]["section"]!=activity["section"]:errors.append("現地課題の解放時期が不正")
		for prerequisite in entry.get("requires",[]):
			if prerequisite==entry["id"] or not mission_ids.has(prerequisite):errors.append("前提が未定義または循環する")
		var previous_room: String=""
		var position: Array=[]
		var battles:=0
		var choices:=0
		var texts: Dictionary={}
		for task in entry.get("steps",[]):
			if step_ids.has(task.get("id")):errors.append("進行IDの重複")
			step_ids[task.get("id")]=true
			var room_id: String=task.get("section","")
			if not room_ids.has(room_id):errors.append("未知の区画を参照");continue
			if task.get("location")!=room(room_id)["location"]:errors.append("地点と区画の土地が不一致")
			var cell: Array=task.get("cell",[])
			if cell.size()!=2 or not is_walkable(room_id,Vector2i(cell[0],cell[1])):errors.append("通行できない目標地点");continue
			if room_id!=previous_room:position=room(room_id)["spawn"];previous_room=room_id
			if not _reachable(room_id,position,cell):errors.append("通常の移動で到達できない目標")
			position=cell
			if task.get("kind") not in ["dialogue","battle","challenge","section_travel","circuit_complete"]:errors.append("未知の進行種別")
			for line in task.get("text",[]):
				if not line is String or line.is_empty():errors.append("空の台詞")
				else:texts[line]=true
			if task.get("kind")=="battle":
				battles+=1
				if task.get("enemies",[]).is_empty() or task["enemies"].size()>3:errors.append("敵の編成数が不正")
				var reactive:=0
				for enemy in task.get("enemies",[]):
					if not enemies.has(enemy):errors.append("未知の敵");continue
					reactive+=1 if int(enemies[enemy].get("tactics",{}).get("reaction_power",0))>0 else 0
				if reactive>1:errors.append("高反応の敵を同じ戦闘に複数配置しない")
			if task.get("kind")=="challenge":
				if task.get("options",[]).size()<2 or task["options"].size()>3:errors.append("選択肢が2〜3件ではない")
				if task.get("choice",false):
					choices+=1
					var effects: Array=task.get("choice_effects",[])
					if effects.size()!=task["options"].size():errors.append("選択肢と結果の数が合わない")
					var unique: Dictionary={}
					for effect in effects:
						unique[JSON.stringify(effect)]=true
						if not BattleCatalog._is_integer(effect.get("potion_bonus",0),0):errors.append("選択の追加補給が不正")
						for flag in effect.get("flags",[]):
							if not passage_flags.has(flag):errors.append("選択が未知の近道を開く")
					if unique.size()<2:errors.append("選択による状態の違いがない")
				if task.get("answer",-1) not in range(task["options"].size()):errors.append("自動経路の選択肢が無効")
			for response in task.get("responses",[]):
				if not step_ids.has(response.get("choice")):errors.append("結果の会話が先行する選択を参照していない")
				if response.get("variants",[]).size()<2:errors.append("選択結果の会話が不足")
			for skill in task.get("required_abilities",[]):
				if not abilities.has(skill):errors.append("未知の職業技")
		if battles!=6 or choices<1:errors.append("各冒険の戦闘と選択が不足")
		if texts.size()<6:errors.append("固有の会話場面が不足")
		if entry.get("steps",[]).is_empty() or entry["steps"][-1].get("kind")!="circuit_complete":errors.append("冒険の終端がない")
	return errors

static func _reachable(identifier: String, origin: Array, target: Array)->bool:
	if origin.size()!=2 or target.size()!=2:return false
	for coordinate in origin+target:
		if not BattleCatalog._is_integer(coordinate,0):return false
	var start:=Vector2i(origin[0],origin[1])
	var finish:=Vector2i(target[0],target[1])
	if not is_walkable(identifier,start) or not is_walkable(identifier,finish):return false
	var groups:=_closed_components(identifier)
	return groups.get(start,-1)==groups.get(finish,-2)

static func _closed_components(identifier: String)->Dictionary:
	var layout: Array=room(identifier)["layout"]
	var previous: Dictionary=_audit_connectivity.get(identifier,{})
	if not previous.is_empty() and previous["layout"]==layout:return previous["groups"]
	# 定義監査では、開通前の地形でつながる領域を調べる。地形配列が一致する時だけ再利用する。
	var groups: Dictionary={}
	var number:=0
	for y in range(layout.size()):
		for x in range(layout[y].length()):
			var start:=Vector2i(x,y)
			if groups.has(start) or not is_walkable(identifier,start):continue
			number+=1
			groups[start]=number
			var queue: Array[Vector2i]=[start]
			var at:=0
			while at<queue.size():
				var cell:=queue[at];at+=1
				for delta in [Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT,Vector2i.UP]:
					var next: Vector2i=cell+delta
					if not groups.has(next) and is_walkable(identifier,next):groups[next]=number;queue.append(next)
	_audit_connectivity[identifier]={"layout":layout.duplicate(),"groups":groups}
	return groups
