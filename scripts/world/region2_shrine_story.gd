class_name Region2ShrineStory
extends RefCounted
## S10の本文と一時ページ。人物の初配置・演出はこの処理に含めない。
const SCENE := "region2_shrine_s10"
const COMPLETE_FLAG := "region2_shrine_seen"
const JOBS_FLAG := "region2_shrine_jobs_unlocked"
const INITIAL_JOBS := ["slime", "beast", "plant", "shell"]
var _page := -1
var _run := 0

static func in_room(saved: Dictionary) -> bool:
	var here: Dictionary = saved.get("overworld",{})
	return saved.has("first_region") and here.get("active",false) and here.get("layer")=="interior" and here.get("node")=="region2_village" and here.get("room")==4

static func eligible(saved: Dictionary) -> bool:
	return in_room(saved) and FirstRegionStory.complete(saved) and not saved.get("progress_flags",{}).get(COMPLETE_FLAG,false)

static func lines() -> Array:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/region2_shrine_scenes.json"))
	return data["lines"]

func active() -> bool:
	return _page >= 0

func interrupt() -> void:
	_page = -1

func begin(saved: Dictionary) -> Dictionary:
	if active() or not eligible(saved):return {}
	_run += 1
	_page = 0
	var text: Array = []
	var speakers: Array = []
	for line in lines():
		text.append(line["text"])
		speakers.append(line["speaker"])
	return {"kind":"dialogue","shrine_scene":SCENE,"shrine_run":_run,"text":text,"speakers":speakers}

func confirm(saved: Dictionary, identifier: String, run: int, page: int) -> Dictionary:
	if not active() or not eligible(saved) or identifier!=SCENE or run!=_run or page!=_page:return {}
	_page += 1
	if _page < lines().size():return {"kind":"story_page"}
	# 末尾の通常確認でだけ確定。全8職の共通ゲートには書き込まない。
	saved["progress_flags"][COMPLETE_FLAG] = true
	saved["progress_flags"][JOBS_FLAG] = true
	interrupt()
	return {"kind":"moved"}
