extends "res://tools/capture_port_town.gd"
## 建物の中を、通常操作（方向キー・決定キー・画面のボタン）だけで確かめて撮影する。
## 環境変数：INTERIOR_TOWN=village|castle|port（必須）、INTERIOR_OUTPUT=保存先（既定 res://docs/verification/interior-backdrops/runtime/）、
## INTERIOR_ROOMS=部屋番号のカンマ区切り（空なら町の全部屋）。
## 町の入口へ置いた保存（tools/prepare_interior_saves.py が .tools/interior-<町>.json に作る）から始め、
## 各部屋について：扉から入る→通行地図と実判定の全マス一致→住人に話しかける（買い物・宿泊・会話）→扉から出る、を行う。
const REGION_DATA := "res://world/first_region.json"
const OUTDOOR := {"start_village":1,"first_castle":0,"first_port":0}
const KEYS := {Vector2i.DOWN:KEY_DOWN,Vector2i.LEFT:KEY_LEFT,Vector2i.RIGHT:KEY_RIGHT,Vector2i.UP:KEY_UP}
const NODES := {"village":"start_village","castle":"first_castle","port":"first_port"}
var interior_summary: Array=[]
var legacy_notes: Array[String]=[]

func _run() -> void:
	var town := OS.get_environment("INTERIOR_TOWN")
	if not NODES.has(town):
		printerr("INTERIOR_CAPTURE_FAIL: INTERIOR_TOWN=village|castle|port を指定してください")
		quit(2);return
	OUTPUT=OS.get_environment("INTERIOR_OUTPUT") if not OS.get_environment("INTERIOR_OUTPUT").is_empty() else "res://docs/verification/interior-backdrops/runtime/"
	OUTPUT+=town+"/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.min_size=Vector2i(1024,576);root.max_size=Vector2i(1024,576);root.size=Vector2i(1024,576)
	var raw := FileAccess.get_file_as_bytes("res://.tools/interior-%s.json" % town)
	if not castle_check(not raw.is_empty(),"撮影用の保存がある（tools/prepare_interior_saves.py）"):finish_interior(town);return
	var copy_path := "user://qa_"+OS.get_environment("RPG_QA_SAVE_PREFIX")+"_save.json"
	var file := FileAccess.open(copy_path,FileAccess.WRITE);file.store_buffer(raw);file.close()
	var packed: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	_main=packed.instantiate();root.add_child(_main);process_frame.connect(_watch);await _frames()
	if not castle_check(await _button(["手動セーブから再開"]),"タイトルから保存を再開"):finish_interior(town);return
	if not castle_check(_load_definition(),"本番定義の読取"):finish_interior(town);return
	_definition["doors"].append_array(_definition["castle_doors"])
	_definition["doors"].append_array(_definition["port_doors"])
	castle_check(_state()["overworld"]["node"]==NODES[town],"町の入口から開始")
	await interior_route(town)
	finish_interior(town)

func room_point(node: String, index: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":node,"room":index,"cell":cell}

func region_site(node: String) -> Dictionary:
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(REGION_DATA))
	for site in data["sites"]:
		if site["id"]==node:return site
	return {}

func has_backdrop(node: String, index: int) -> bool:
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://world/first_region_visuals.json"))
	return data["maps"].get("%s:%d" % [node,index],{}).has("backdrop")

func blocking_cells(room: Dictionary) -> Array:
	# 住人・店員のいるマスは通れない。宝箱のマスは歩いて乗れる。
	return room["events"].filter(func(e:Dictionary)->bool:return e["kind"]!="treasure").map(func(e:Dictionary)->Vector2i:return Vector2i(int(e["cell"][0]),int(e["cell"][1])))

func cells_equal(a: Array, b: Array) -> bool:
	return int(a[0])==int(b[0]) and int(a[1])==int(b[1])

func entry_link(node: String, index: int) -> Dictionary:
	for link in _definition["doors"]:
		if link["to"]["node"]==node and link["to"]["room"]==index and link["from"]["room"]!=index and link["from"]["node"]==node:return link
	return {}

func leave_link(node: String, index: int, back_room: int) -> Dictionary:
	for link in _definition["doors"]:
		if link["from"]["node"]==node and link["from"]["room"]==index and link["to"]["room"]==back_room:return link
	return {}

func layout_matches(node: String, index: int, room: Dictionary) -> bool:
	# 通行地図（layout）と実ゲームの歩ける判定が1マスずつ一致するか。住人のいるマスは通れない。
	var event_cells: Array=blocking_cells(room)
	var saved := _state();var probe: Dictionary=saved.duplicate(true)
	probe["overworld"]["node"]=node;probe["overworld"]["room"]=index;probe["overworld"]["layer"]="interior"
	var total := 0
	for y in range(room["layout"].size()):
		var row: String=room["layout"][y]
		for x in range(row.length()):
			probe["overworld"]["cell"]=[x,y]
			var expected: bool=row.substr(x,1)=="." and Vector2i(x,y) not in event_cells
			if FirstRegion.walkable(probe,Vector2i(x,y))!=expected:
				_blocker="通行地図と実判定の不一致: %s:%d (%d,%d)" % [node,index,x,y]
				return false
			total+=1
	interior_summary.append({"room":room["title"],"cells":total})
	return true

func reachable_cells(layout: Array, start: Vector2i, blocked: Array) -> Dictionary:
	var seen := {start:true};var queue: Array=[start]
	while not queue.is_empty():
		var current: Vector2i=queue.pop_front()
		for delta in [Vector2i.RIGHT,Vector2i.LEFT,Vector2i.DOWN,Vector2i.UP]:
			var next: Vector2i=current+delta
			if next.y<0 or next.y>=layout.size() or next.x<0 or next.x>=String(layout[0]).length():continue
			if String(layout[next.y]).substr(next.x,1)!="." or seen.has(next) or next in blocked:continue
			seen[next]=true;queue.append(next)
	return seen

func stand_for(room: Dictionary, event: Dictionary, start: Vector2i) -> Dictionary:
	# 住人へ話しかけられるマスと向き。カウンター越し（reach）の住人は、いちばん遠い側から話す。
	var cell := Vector2i(int(event["cell"][0]),int(event["cell"][1]))
	var reach := int(event.get("reach",1))
	var blocked: Array=blocking_cells(room)
	var found := reachable_cells(room["layout"],start,blocked)
	for distance in range(reach,0,-1):
		for delta in [Vector2i.UP,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.DOWN]:
			var stand: Vector2i=cell-delta*distance
			if found.has(stand):return {"cell":[stand.x,stand.y],"key":KEYS[delta],"distance":distance}
	return {}

func interior_route(town: String) -> void:
	var node: String=NODES[town]
	var site := region_site(node)
	var outdoor: int=OUTDOOR[node]
	var wanted: Array=[]
	if not OS.get_environment("INTERIOR_ROOMS").is_empty():
		for part in OS.get_environment("INTERIOR_ROOMS").split(","):wanted.append(int(part))
	for index in range(site["rooms"].size()):
		var room: Dictionary=site["rooms"][index]
		if index==outdoor or (not wanted.is_empty() and index not in wanted):continue
		var entry := entry_link(node,index)
		if entry.is_empty():continue
		var back: int=entry["from"]["room"]
		var leave := leave_link(node,index,back)
		if leave.is_empty():continue
		var name := "%s-%02d" % [town,index]
		if not castle_check(await _walk(room_point(node,index,entry["to"]["cell"])),"扉から入る: "+room["title"]):return
		castle_check(_state()["overworld"]["room"]==index and cells_equal(_state()["overworld"]["cell"],entry["to"]["cell"]),"入口（扉の内側）に着く: "+room["title"])
		var failures_before := castle_failures.size()
		await picture(name+"-1-entered")
		# 一枚絵の背景へ置き換えていない部屋（画像がない部屋・謁見の間）は、旧来の扉の絵が人物にかかることがある。
		# 失敗にせず、変更していない部屋の記録として分けて残す。
		if not has_backdrop(node,index):
			while castle_failures.size()>failures_before:legacy_notes.append(castle_failures.pop_back())
		castle_check(layout_matches(node,index,room),"通行地図と実判定が全マス一致: "+room["title"])
		for event in room["events"]:
			if event["kind"]=="recruit":continue
			var stand := stand_for(room,event,Vector2i(int(entry["to"]["cell"][0]),int(entry["to"]["cell"][1])))
			if not castle_check(not stand.is_empty(),"住人に話しかけられる場所がある: "+str(event["id"])):continue
			if not castle_check(await _walk(room_point(node,index,stand["cell"])),"住人の前へ歩く: "+str(event["id"])):return
			var before := _state()
			await _key(stand["key"]);await create_timer(.17).timeout
			await _key(KEY_ENTER);await create_timer(.05).timeout
			var mode := str(_snapshot().get("mode",""))
			var served := mode!="world" and mode!="field"
			if not served:served=_state()["inventory"]!=before["inventory"] or _state()["party"]!=before["party"]
			castle_check(served,"住人に話しかけられる: %s（%s）" % [str(event["id"]),mode])
			if mode!="world" and mode!="field":await picture(name+"-2-talk-"+str(event["id"]))
			if event["kind"] in ["shop","weapon_shop"]:
				castle_check(await _button(["やめる"]),"買い物の画面から戻る: "+str(event["id"]))
			elif mode=="dialogue":
				castle_check(await _settle(),"会話を最後まで送る: "+str(event["id"]))
			if event["kind"]=="rest":castle_check(_state()["party"].all(func(a:Dictionary)->bool:return a["hp"]==a["max_hp"] and a["mp"]==a["max_mp"]),"宿で全員が回復")
			castle_check(_snapshot().get("mode","") in ["world","field"],"会話・買い物のあと歩行に戻る: "+str(event["id"]))
		if not castle_check(await _walk(room_point(node,back,leave["to"]["cell"])),"扉から出る: "+room["title"]):return
		castle_check(_state()["overworld"]["room"]==back and cells_equal(_state()["overworld"]["cell"],leave["to"]["cell"]),"外へ出た位置: "+room["title"])
		castle_check(not port_battle_seen,"建物の出入りで戦闘が起きない: "+room["title"])

func finish_interior(town: String) -> void:
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if castle_failures.is_empty() else "FAIL","town":town,"checks":castle_checks,"failures":castle_failures,"images":castle_images,"visible_pixels":visible_pixels,"cells":interior_summary,"unchanged_room_notes":legacy_notes,"native_render":DisplayServer.get_name()!="headless"})
	for failure in castle_failures:printerr("INTERIOR_RUNTIME_FAIL: "+failure)
	print("INTERIOR_RUNTIME_PASS: town=%s checks=%d images=%d" % [town,castle_checks,castle_images.size()] if castle_failures.is_empty() else "INTERIOR_RUNTIME_FAIL: town="+town)
	quit(0 if castle_failures.is_empty() else 1)
