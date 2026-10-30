class_name Region2RuinsStory
extends RefCounted
## S11の永続事実は読了・勝利・受取を分離。一時ページは保存しない。
const SCENE := "region2_ruins_s11"
const COMPLETE_FLAG := "region2_ruins_record_seen"
const BOSS := "region2_ruins_boss"
const ENEMY := "ruins_sandstone_colossus"
const BOX := "region2_ruins_key_box"
const KEY := "ruins_key"
var _page := -1
var _run := 0

static func data() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://data/region2_ruins_scenes.json"))

static func in_room(saved: Dictionary) -> bool:
	var here: Dictionary = saved.get("overworld",{})
	return saved.has("first_region") and here.get("active",false) and here.get("layer")=="interior" and here.get("node")=="region2_ruins" and here.get("room")==3

static func eligible(saved: Dictionary) -> bool:
	return in_room(saved) and FirstRegionStory.complete(saved) and saved.get("progress_flags",{}).get(Region2ShrineStory.COMPLETE_FLAG,false) and not saved.get("progress_flags",{}).get(COMPLETE_FLAG,false)

static func near(saved: Dictionary, cell: Array) -> bool:
	if not in_room(saved):return false
	var here: Dictionary = saved["overworld"]
	var current := WorldExpedition.point(here["cell"])
	var target: Vector2i = current+[Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP][here["facing"]]
	return WorldExpedition.point(cell) in [current,target]

static func dialogue(lines: Array) -> Dictionary:
	var text: Array = [];var speakers: Array = []
	for line in lines:
		text.append(line["text"]);speakers.append(line["speaker"])
	return {"kind":"dialogue","text":text,"speakers":speakers}

func active() -> bool:
	return _page>=0

func interrupt() -> void:
	_page=-1

func begin(saved: Dictionary, inspected: bool=false) -> Dictionary:
	if active() or not eligible(saved):return {}
	if not inspected and saved["overworld"]["cell"]!=Region2Ruins.data()["record"]["trigger"]:return {}
	_run+=1;_page=0
	return dialogue(data()["lines"]).merged({"ruins_scene":SCENE,"ruins_run":_run})

func confirm(saved: Dictionary, identifier: String, run: int, page: int) -> Dictionary:
	if not active() or not eligible(saved) or identifier!=SCENE or run!=_run or page!=_page:return {}
	_page+=1
	if _page<data()["lines"].size():return {"kind":"story_page"}
	saved["progress_flags"][COMPLETE_FLAG]=true
	interrupt()
	return {"kind":"moved"}

func interact(saved: Dictionary) -> Dictionary:
	if not in_room(saved) or active():return {}
	var config := Region2Ruins.data()
	if near(saved,config["record"]["trigger"]) or near(saved,config["record"]["display_cell"]):
		if eligible(saved):return begin(saved,true)
		if saved["progress_flags"].get(COMPLETE_FLAG,false):return dialogue(data()["revisit"])
	if near(saved,config["boss"]["cell"]):
		if eligible(saved):return begin(saved,true)
		if not saved["progress_flags"].get(COMPLETE_FLAG,false):return {}
		if BOSS not in saved["overworld"]["cleared"]:
			return {"kind":"battle","id":BOSS,"enemies":[ENEMY],"seed":randi()}
	if near(saved,config["reward_box"]["cell"]):
		if BOSS not in saved["overworld"]["cleared"]:return dialogue([{"speaker":"状況","text":"箱はまだ開かない。"}])
		if BOX in saved["overworld"]["opened"]:return dialogue([{"speaker":"状況","text":"宝箱は空です。"}])
		saved["overworld"]["opened"].append(BOX)
		saved["inventory"][KEY]=1
		return dialogue([{"speaker":"状況","text":"遺跡の鍵を手に入れた。"}]).merged({"sound":"chest"})
	return {}
