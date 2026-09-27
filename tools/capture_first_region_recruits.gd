extends "res://tools/capture_first_region_entrance.gd"
## 通常操作中の会話・手伝いの場面を、既存の通し撮影に追加する。
var _recruit_images: Dictionary = {}
var _observations: Array = []

func _watch() -> void:
	super._watch()
	if _capture_busy or _finished or not is_instance_valid(_main):return
	var saved := _state()
	if saved.has("first_region"):
		var observed := {"party":saved["party"].map(func(actor:Dictionary)->String:return actor["id"]),"haldo":saved["first_region"].get("errands",{}).get("haldo","not_started")}
		if _observations.is_empty() or _observations[-1]!=observed:_observations.append(observed)
	if _snapshot().get("mode")!="dialogue":return
	var screen: FirstRegionScreen=_main.get("_region_screen")
	if not is_instance_valid(screen):return
	var name := ""
	if screen.speaker=="リオネ" and screen.message.begins_with("なら、あたしも"):name="16-rione-offer"
	if screen.dialogue_prompt=="包帯の端を押さえる":name="17-haldo-bandage"
	if screen.dialogue_prompt=="合図に合わせて手を離す":name="18-haldo-release"
	if name.is_empty() or _recruit_images.has(name):return
	_recruit_images[name]=true
	_capture_busy=true
	call_deferred("_capture",name)

func _finish() -> void:
	if _recruit_images.size()!=3:
		printerr("RECRUIT_CAPTURE_FAIL: images="+str(_recruit_images.size()))
		quit(1)
		return
	print("RECRUIT_CAPTURE_PASS: images=3")
	var file := FileAccess.open("res://docs/verification/first-region/recruit-observations.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"observations":_observations},"\t")+"\n")
	file.close()
	await super._finish()
