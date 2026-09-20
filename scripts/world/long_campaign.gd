class_name LongCampaign
extends RefCounted

const PATH: String="res://data/long_campaign_v1.json"
const REGIONS: Array[String]=["waterway","cave","school","records","gate"]
static var _source: Dictionary={}
static var _missions: Dictionary={}
static var _rooms: Dictionary={}

static func data()->Dictionary:
	if _source.is_empty() and FileAccess.file_exists(PATH):
		var parsed: Variant=JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if parsed is Dictionary:
			_source=CampaignContent._integers(parsed)
			for mission in _source.get("missions",[]):_missions[mission["id"]]=mission
			for room in _source.get("rooms",[]):_rooms[room["id"]]=room
	return _source

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

static func choice_flag(identifier: String, option: int)->String:
	return "journey_choice_"+identifier+"_"+str(option)

static func available(state: Dictionary)->Array[Dictionary]:
	var result: Array[Dictionary]=[]
	var flags: Dictionary=state.get("progress_flags",{})
	if not enabled() or not flags.get("long_campaign_started",false) or not state.get("expedition",{}).is_empty() or not state.get("return_point",{}).is_empty():return result
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
	if data().get("missions",[]).is_empty():return false
	for entry in data()["missions"]:
		if not flags.get(cleared_flag(entry["id"]),false):return false
	return true

static func is_walkable(identifier: String, cell: Vector2i)->bool:
	var definition:=room(identifier)
	return not definition.is_empty() and cell.x>=0 and cell.y>=0 and cell.y<definition["layout"].size() and cell.x<definition["layout"][cell.y].length() and definition["layout"][cell.y].substr(cell.x,1)=="."

static func walkable_cells(identifier: String)->Array:
	var definition:=room(identifier)
	var result: Array=[]
	if definition.is_empty():return result
	for y in range(definition["layout"].size()):
		for x in range(definition["layout"][y].length()):
			if is_walkable(identifier,Vector2i(x,y)):result.append([x,y])
	return result

static func validate_flags(flags: Dictionary)->bool:
	for entry in data().get("missions",[]):
		if flags.get(cleared_flag(entry["id"]),false):
			for prerequisite in entry.get("requires",[]):
				if not flags.get(cleared_flag(prerequisite),false):return false
		for task in entry["steps"]:
			if not task.get("choice",false):continue
			var selected:=0
			for option in range(task["options"].size()):selected+=1 if flags.get(choice_flag(task["id"],option),false) else 0
			if selected>1 or (flags.get(cleared_flag(entry["id"]),false) and selected!=1):return false
	return true

static func audit(abilities: Dictionary, enemies: Dictionary)->Array[String]:
	var errors: Array[String]=[]
	var document:=data()
	if document.is_empty():return ["長編のデータがない"]
	var room_ids: Dictionary={}
	var mission_ids: Dictionary={}
	var step_ids: Dictionary={}
	for area in document.get("rooms",[]):
		if room_ids.has(area.get("id")):errors.append("区画IDの重複")
		room_ids[area.get("id")]=true
		if area.get("location") not in REGIONS or area.get("layout",[]).size()!=18:errors.append("区画の場所または高さが不正")
		for row in area.get("layout",[]):
			if not row is String or row.length()!=32:errors.append("区画の幅が不正")
	for entry in document.get("missions",[]):
		if mission_ids.has(entry.get("id")):errors.append("冒険IDの重複")
		mission_ids[entry.get("id")]=true
		if entry.get("region") not in REGIONS or entry.get("trigger_step") not in [19,23,28,34,38]:errors.append("既存の章・土地へ接続されていない")
		var base:=StoryCampaign.step(int(entry.get("trigger_step",-1)))
		if entry.get("chapter")!=base.get("chapter"):errors.append("章の対応が不正")
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
				if task.get("choice",false):choices+=1
				if task.get("answer",-1) not in range(task["options"].size()):errors.append("自動経路の選択肢が無効")
			for skill in task.get("required_abilities",[]):
				if not abilities.has(skill):errors.append("未知の職業技")
		if battles!=6 or choices<1:errors.append("各冒険の戦闘と選択が不足")
		if texts.size()<6:errors.append("固有の会話場面が不足")
		if entry.get("steps",[]).is_empty() or entry["steps"][-1].get("kind")!="circuit_complete":errors.append("冒険の終端がない")
	return errors

static func _reachable(identifier: String, origin: Array, target: Array)->bool:
	var queue: Array=[origin]
	var seen: Dictionary={str(origin):true}
	var at:=0
	while at<queue.size():
		var current: Array=queue[at];at+=1
		if current==target:return true
		for delta in [[1,0],[-1,0],[0,1],[0,-1]]:
			var next: Array=[current[0]+delta[0],current[1]+delta[1]]
			if not seen.has(str(next)) and is_walkable(identifier,Vector2i(next[0],next[1])):seen[str(next)]=true;queue.append(next)
	return false
