extends "res://tools/smoke_first_region.gd"
## 081。本番sceneを通常保存から起動し、既存の入力と戦闘操作だけで到達する。
const OUT081 := "res://docs/verification/task-081-implementation/"
const PROBES081 := {
	"inn":{"behind":[7,4],"front":[9,5],"occluder":0},
	"item_shop":{"behind":[6,7],"front":[6,9],"occluder":0},
	"weapon_shop":{"behind":[6,4],"front":[6,6],"occluder":0},
	"shrine":{"behind":[8,2],"front":[6,5],"occluder":0},
	"armor_shop":{"behind":[10,4],"front":[10,5],"occluder":2}}
var phase081 := ""
var checks081: Array = []
var visited081: Dictionary = {}
var observed081: Array = []
var images081: Array = []
var binding081: Dictionary = {}
var reference081: Dictionary = {}

func check081(ok: bool, label: String, details: Variant = null) -> bool:
	checks081.append({"ok":ok,"label":label,"details":details})
	if not ok:printerr("TASK081_INPUT_FAIL: "+label+" "+str(details)+" "+_blocker)
	return ok

func _trigger_points() -> Array:
	var points: Array = []
	for link in _definition.get("doors",[]):points.append(link["from"])
	if _definition.has("region3_port_exit"):
		points.append(_definition["region3_port_exit"])
		points.append(_world_point(_definition["region3_port_entrance"]["cell"]))
	return points

func p081(index: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":"region3_port","room":index,"cell":cell}

func capture081(name: String) -> Image:
	await create_timer(0.35).timeout
	await _frames(3)
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var path := phase081+"-"+name+".png"
	check081(image.save_png(OUT081+path)==OK,"実画面PNG保存",path)
	images081.append(path)
	return image

func difference081(a: Image, b: Image) -> int:
	var count := 0
	for y in range(a.get_height()):
		for x in range(a.get_width()):
			if a.get_pixel(x,y)!=b.get_pixel(x,y):count+=1
	return count

func occlusion081(label: String, probes: Dictionary) -> void:
	if not check081(await _walk(p081(int(_pose()["room"]),probes[label])),"家具の前後へ通常歩行",label):return
	var normal := await capture081(label)
	var panel: FirstRegionScreen=_main.get("_region_screen")
	var view := panel.map_view
	var original := view._map
	var diagnostic := original.duplicate(true)
	diagnostic["overlays"]["pieces"].remove_at(int(probes["occluder"]))
	view._map=diagnostic;view.queue_redraw()
	var no_overlay := await capture081(label+"-diagnostic-without-target-overlay")
	var delta := difference081(normal,no_overlay)
	check081(delta>0 if label=="behind" else delta==0,"家具の遮蔽画素",{"label":label,"changed_pixels":delta})
	view._map=original
	var saved := view.saved
	view.saved=saved.duplicate(true);view.saved["party"]=[];view.queue_redraw()
	var no_player := await capture081(label+"-diagnostic-without-player")
	check081(difference081(normal,no_player)>0,"人物の可視画素あり",label)
	view.saved=saved;view.queue_redraw()

func step081(delta: Vector2i, expected: Array, label: String) -> bool:
	var before := _pose()
	var success := await _step_direction(delta)
	observed081.append({"before":before,"delta":[delta.x,delta.y],"after":_pose(),"expected":expected})
	return check081(success and _pose().get("cell")==expected,label)

func floor081(cell: Vector2i) -> bool:
	return cell.x>=0 and cell.x<14 and cell.y>=0 and cell.y<12 and reference081["layout"][cell.y].substr(cell.x,1)=="."

func walk_all081(cell: Vector2i) -> void:
	visited081[cell]=true
	for delta in DIRECTIONS:
		var next: Vector2i=cell+delta
		if next==Vector2i(6,11):continue
		if not floor081(next):
			if not await step081(delta,[cell.x,cell.y],"本番入力で壁・家具衝突"):return
		elif not visited081.has(next):
			if not await step081(delta,[next.x,next.y],"本番入力で全床巡回"):return
			await walk_all081(next)
			if not await step081(-delta,[cell.x,cell.y],"同経路を本番入力で戻る"):return

func ui_save081(label: String) -> bool:
	var before := _state()
	var ok := await _key(KEY_ESCAPE) and await _button(["セーブ"]) and await _button(["現在の冒険に戻る"])
	if not check081(ok,"通常メニューで保存",label):return false
	var loaded := GameSession.new()
	var load_ok := loaded.load_game(str(_main.get("save_path")))
	check081(load_ok and loaded.export_state()==before,"通常保存の全状態復元",label)
	return true

func _run() -> void:
	phase081=OS.get_environment("TASK081_PHASE")
	root.min_size=Vector2i(512,288);root.max_size=Vector2i(512,288);root.size=Vector2i(512,288)
	var source := "res://.tools/region2-port-departure.json" if phase081=="arrival" else OUT081+"arrival-save.json"
	if not check081(FileAccess.file_exists(source),"無編集の通常到達保存が存在",source):finish081();return
	var source_sha := FileAccess.get_sha256(source)
	var copy := FileAccess.open("user://qa_"+OS.get_environment("RPG_QA_SAVE_PREFIX")+"_save.json",FileAccess.WRITE)
	copy.store_buffer(FileAccess.get_file_as_bytes(source));copy.close()
	_main=(load(str(ProjectSettings.get_setting("application/run/main_scene"))) as PackedScene).instantiate()
	root.add_child(_main);process_frame.connect(_watch);await _frames()
	if not check081(await _button(["手動セーブから再開"]),"本編タイトルから通常再開"):finish081();return
	_definition=FirstRegion.data().duplicate(true)
	for key in ["castle_doors","tower_doors","port_doors","second_port_doors","region2_village_doors","region3_port_doors"]:_definition["doors"].append_array(_definition.get(key,[]))
	_sites=FirstRegion._data["sites"].duplicate(true)
	check081(FileAccess.get_sha256(source)==source_sha,"開始保存のbytes不変",source_sha)
	if phase081=="arrival":await arrival081()
	else:await room081()
	finish081()

func arrival081() -> void:
	var dock: Dictionary=Region3Port.data()["docks"][0]
	if not check081(_state()["overworld"]["transport"]=="ship" and FirstRegionTravel.snapshot(_state())["ship_owned"],"第1港で通常取得・乗船した保存から開始"):return
	if not check081(await _walk(_world_point(dock["ship_cell"])),"現在海域を通常航行して新桟橋へ到達"):return
	await capture081("before-landing")
	await _key(KEY_ENTER);await _settle()
	if not check081(_at(dock["land"]) and _state()["overworld"]["transport"]=="walk","決定キーで通常下船"):return
	await create_timer(2.4).timeout
	await capture081("pier")
	if not check081(await ui_save081("到着"),"到着保存"):return
	var file := FileAccess.open(OUT081+"arrival-save.json",FileAccess.WRITE)
	file.store_buffer(FileAccess.get_file_as_bytes(str(_main.get("save_path"))))
	file.close()
	var viewport := SubViewport.new();viewport.size=Vector2i(1312,864);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var view := FirstRegionView.new();view.saved=_state();view.size=Vector2(1312,864);viewport.add_child(view)
	await _frames(4);await RenderingServer.frame_post_draw
	check081(viewport.get_texture().get_image().save_png(OUT081+"exterior-full-runtime.png")==OK,"本番rendererの全体図")
	viewport.queue_free();await _frames()
	await occlusion081("behind",{"behind":[12,12],"front":[11,15],"occluder":1})
	await occlusion081("front",{"behind":[12,12],"front":[11,15],"occluder":1})
	var outside := FirstRegion.outside("region3_port_entrance")
	if not check081(await _walk(_definition["region3_port_exit"],outside),"石門から既存方式で世界の入口前へ退出"):return
	check081(_pose()["facing"]==1,"世界への退出は外向き")
	await capture081("gate-outside")
	if not check081(await _walk(_world_point(_definition["region3_port_entrance"]["cell"]),_definition["region3_port_gate_spawn"]),"世界の入口前から石門へ再入場"):return
	var actor: Dictionary=_state()["party"].filter(func(member:Dictionary)->bool:return member["hp"]>0 and member["mp"]>=2)[0]
	if not check081(await _key(KEY_ESCAPE) and await _button(["帰還の風"]) and await _button(["%s MP %d"%[actor["name"],actor["mp"]]]) and await _button(["第3地方の港町（仮）"]),"通常メニューで訪問済み新港へ帰還"):return
	await _settle()
	check081(_at(outside) and FirstRegionTravel.snapshot(_state())["ship_cell"]==dock["ship_cell"],"人物は入口前・船は新港へ帰還")
	var after_actor: Dictionary=_state()["party"].filter(func(member:Dictionary)->bool:return member["id"]==actor["id"])[0]
	check081(after_actor["mp"]==actor["mp"]-2,"通常帰還は既存MP2消費")
	await capture081("spell-outside")
	if not check081(await _walk(_world_point(_definition["region3_port_entrance"]["cell"]),_definition["region3_port_gate_spawn"]),"帰還後も石門へ通常再入場"):return
	if not check081(await _walk(dock["land"]),"通常歩行で桟橋へ戻る"):return
	await _key(KEY_ENTER);await _settle()
	check081(_at(_world_point(dock["ship_cell"])) and _state()["overworld"]["transport"]=="ship","通常乗船で同じ海セルへ復帰")
	if not check081(await _walk(_world_point([179,45])),"通常再出航"):return
	check081(await _walk(_world_point(dock["ship_cell"])),"通常再航行")
	await _key(KEY_ENTER);await _settle()
	check081(_at(dock["land"]),"通常再下船で同じ桟橋")
	await capture081("returned-pier")

func room081() -> void:
	var foundation: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/adopted_room_foundation.json")))
	for item in foundation["rooms"]:
		if item["id"]==phase081:reference081=item
	for item in Region3Port.data()["bindings"]:
		if item["id"]==phase081:binding081=item
	if not check081(not binding081.is_empty(),"室の識別",phase081):return
	var index := int(binding081["room"])
	if not check081(await _walk(p081(0,binding081["return_cell"])),"桟橋から扉前へ通常歩行"):return
	await capture081("entrance")
	if not check081(await _walk(p081(0,binding081["door"]),p081(index,[6,9])),"本編外観から通常入室"):return
	var panel: FirstRegionScreen=_main.get("_region_screen")
	check081(panel.map_view._map["backdrop"]["path"]==reference081["path"],"採用済み室内背景を本編で識別")
	await create_timer(2.4).timeout
	await capture081("entered")
	await walk_all081(Vector2i(6,9))
	var count := 0
	for row in reference081["layout"]:count+=str(row).count(".")
	check081(visited081.size()==count-1,"敷居以外の全床を本番入力で巡回",{"visited":visited081.size(),"expected":count-1})
	for position in ["behind","front"]:await occlusion081(position,PROBES081[phase081])
	if not await ui_save081("室内"):return
	var saved_pose := _pose()
	if not check081(await _walk(p081(index,[6,10])),"保存後に別位置へ通常歩行"):return
	await _key(KEY_ESCAPE)
	check081(await _button(["手動セーブから再開"]),"メニューから再読込")
	await _settle()
	check081(_pose()==saved_pose,"位置と向きが保存位置へ戻る")
	await capture081("reloaded")
	for repeat in range(3):
		if not check081(await _walk(p081(index,[6,11]),p081(0,binding081["return_cell"])),"元の扉の一歩手前へ通常退出",repeat):return
		check081(_pose()["facing"]==0,"退出時は外向き")
		await _frames(5)
		check081(_at(p081(0,binding081["return_cell"])),"待機して再突入しない")
		if repeat<2:
			if not check081(await _walk(p081(0,binding081["door"]),p081(index,[6,9])),"同じ扉へ通常再入室",repeat):return
	await capture081("returned")
	if not await ui_save081("外観復帰"):return
	check081(await _walk(Region3Port.data()["docks"][0]["land"]),"退室後に桟橋へ通常帰路")
	await _key(KEY_ENTER);await _settle()
	check081(_state()["overworld"]["transport"]=="ship","退室後の再出航")

func finish081() -> void:
	check081(_active() and not _input_violation,"180秒・600歩・3000入力の既存上限内")
	var failed := checks081.filter(func(item:Dictionary)->bool:return not item["ok"]).size()
	PlaySessionMetrics.write_json(OUT081+phase081+"-input.json",{"phase":phase081,"checks":checks081,"failed":failed,"inputs":_input_log,"moves":_moves,"turns":_turns,"observed":observed081,"images":images081,"final_pose":_pose(),"rendering":DisplayServer.get_name(),"scope":"本番scene・無編集保存再開・通常入力。位置やフラグの直接設定なし。"})
	print("TASK081_INPUT_RESULT: phase=%s checks=%d moves=%d failed=%d" % [phase081,checks081.size(),_moves,failed])
	_finished=true
	quit(0 if failed==0 else 1)
