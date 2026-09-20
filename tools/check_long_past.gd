extends SceneTree

var errors: Array[String]=[]
var scenes:=0

func check(condition: bool,message: String)->void:
	if not condition:errors.append(message)

func _initialize()->void:
	var catalog: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://data/long_campaign_v1.json"))
	var missions: Dictionary={}
	for mission in catalog["missions"]:missions[mission["id"]]=mission
	var files:=DirAccess.get_files_at("res://data/long_campaign/arcs")
	files.sort()
	for file in files:
		if not file.ends_with(".json"):continue
		var source: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://data/long_campaign/arcs/"+file))
		for episode in source["episodes"]:
			check(missions.has(episode["id"]),str(episode["id"])+": 台本が本番データに存在する")
			if not missions.has(episode["id"]):continue
			var mission: Dictionary=missions[episode["id"]]
			for room_number in episode.get("past_scene_indices",[]):
				scenes+=1
				var section: String=mission["sections"][int(room_number)]["id"]
				var lines: Array=episode["scenes"][int(room_number)]
				var past_blocks: Array=[]
				var past_index: int=-1
				var last_battle: int=-1
				var battle_count:=0
				for index in range(mission["steps"].size()):
					var entry: Dictionary=mission["steps"][index]
					if entry["section"]!=section:continue
					if entry["kind"]=="battle":
						last_battle=index
						battle_count+=1
					if entry.get("past",false):
						past_blocks.append(entry)
						past_index=index
						check(entry["kind"]=="dialogue",str(episode["id"])+": 過去の提示は会話である")
					else:
						for line in lines:
							check(line not in entry.get("text",[]),str(episode["id"])+": 過去の本文を現在へ混ぜない")
				check(past_blocks.size()==1,str(episode["id"])+": 過去の場面は一つの連続した会話である")
				if past_blocks.size()==1:
					check(past_blocks[0]["text"]==lines,str(episode["id"])+": 全文と順序を保持し、省略・分割しない")
				check(battle_count>0 and last_battle<past_index,str(episode["id"])+": 現在の戦闘を終えてから過去を読み切る")
	check(scenes>0,"過去の場面を最低一つ検査する")
	for error in errors:printerr("LONG_PAST_FAIL: "+error)
	if errors.is_empty():print("LONG_PAST_PASS: scenes=%d 過去の本文を一括表示し、現在の戦闘を挟まない" % scenes)
	quit(0 if errors.is_empty() else 1)
