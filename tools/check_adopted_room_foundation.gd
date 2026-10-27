extends SceneTree
## 通常InputEventから本番移動を実測する追加検査。fixture配置と歩行を区別する。
const DIRS := [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]
const ARROWS := [KEY_UP,KEY_RIGHT,KEY_DOWN,KEY_LEFT]
const WASD := [KEY_W,KEY_D,KEY_S,KEY_A]
var main: Control
var out := ""
var room: Dictionary
var checks: Array = []
var inputs: Array = []
var visited: Dictionary = {}
var rendering := false
var run_id := ""
var original_state: Dictionary
var pictures: Array = []

func _initialize() -> void:
	_run.call_deferred()

func check(ok: bool, label: String, detail: Variant = null) -> bool:
	checks.append({"ok":ok,"label":label,"detail":detail})
	if not ok:printerr("ADOPTED_ROOM_FAIL: "+label+" "+str(detail))
	return ok

func state() -> Dictionary:
	return main.game.overworld_state()

func here() -> Vector2i:
	return WorldExpedition.point(state()["cell"])

func key(code: int) -> void:
	for pressed in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = pressed
		inputs.append({"key":code,"pressed":pressed,"before":state()})
		Input.parse_input_event(event)
		await process_frame
	await create_timer(0.20).timeout

func move(delta: Vector2i, expected: Vector2i, label: String) -> void:
	var codes: Array = ARROWS if inputs.size()%4==0 else WASD
	await key(codes[DIRS.find(delta)])
	check(here()==expected,label,{"expected":[expected.x,expected.y],"actual":state()})

func floor_at(cell: Vector2i) -> bool:
	return cell.x>=0 and cell.x<14 and cell.y>=0 and cell.y<12 and room["layout"][cell.y].substr(cell.x,1)=="."

func walk_all(cell: Vector2i) -> void:
	visited[cell] = true
	for delta in DIRS:
		var next: Vector2i = cell+delta
		if next == Vector2i(6,11):continue # 出入口は専用の往復検査で踏む。
		if not floor_at(next):
			await move(delta,cell,"壁家具への通常入力拒否")
		elif not visited.has(next):
			await move(delta,next,"通常入力で床へ移動")
			if here()!=next:return
			await walk_all(next)
			await move(-delta,cell,"同じ経路を通常入力で戻れる")

func route(target: Vector2i) -> void:
	var start := here()
	var previous := {start:start}
	var queue: Array = [start]
	while not queue.is_empty() and not previous.has(target):
		var cell: Vector2i = queue.pop_front()
		for delta in DIRS:
			var next: Vector2i = cell+delta
			if next==Vector2i(6,11) or not floor_at(next) or previous.has(next):continue
			previous[next]=cell
			queue.append(next)
	if not check(previous.has(target),"撮影位置へ入口から接続",target):return
	var path: Array = []
	var at := target
	while at!=start:
		path.push_front(at)
		at=previous[at]
	for next in path:await move(next-here(),next,"撮影位置へ通常入力")

func capture(label: String) -> Image:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var filename := run_id+"-"+label+".png"
	check(image.save_png(out+"/"+filename)==OK,"通常描画PNG保存",filename)
	pictures.append(filename)
	return image

func pixel_difference(a: Image, b: Image) -> int:
	var count := 0
	for y in range(a.get_height()):
		for x in range(a.get_width()):
			if a.get_pixel(x,y)!=b.get_pixel(x,y):count+=1
	return count

func occlusion(probes: Dictionary, label: String) -> void:
	await route(WorldExpedition.point(probes[label]))
	# 向き・歩行アニメの自然停止を待ち、通常画面をまず保存。
	await create_timer(0.3).timeout
	var normal := await capture(label)
	var original: Dictionary = main.view._map
	var diagnostic: Dictionary = original.duplicate(true)
	var pieces: Array = diagnostic["overlays"]["pieces"]
	pieces.remove_at(int(probes["occluder"]))
	diagnostic["overlays"]["pieces"] = pieces
	main.view._map = diagnostic
	main.view.queue_redraw()
	var no_furniture := await capture(label+"-diagnostic-without-target-overlay")
	var difference := pixel_difference(normal,no_furniture)
	check(difference>0 if label=="behind" else difference==0,"家具の前後の遮蔽",{"position":label,"changed_pixels":difference})
	main.view._map = original
	var saved: Dictionary = main.view.saved
	main.view.saved = saved.duplicate(true)
	main.view.saved["party"] = []
	main.view.queue_redraw()
	var empty := await capture(label+"-diagnostic-without-player")
	check(pixel_difference(normal,empty)>0,"人物が完全に隠れていない",pixel_difference(normal,empty))
	main.view.saved = saved
	main.view.queue_redraw()

func _run() -> void:
	out=OS.get_environment("ADOPTED_ROOM_OUTPUT")
	if out.is_empty():printerr("ADOPTED_ROOM_OUTPUT required");quit(2);return
	DirAccess.make_dir_recursive_absolute(out)
	rendering=DisplayServer.get_name()!="headless"
	root.size=Vector2i(512,288)
	var normal_game := GameSession.new()
	check(normal_game.new_first_region(),"既存ニューゲーム")
	original_state=normal_game.export_state()
	var region_before := FirstRegion._data.duplicate(true)
	var visuals_before := FirstRegionPresentation.data().duplicate(true)
	var packed: PackedScene=load("res://tools/adopted_room_foundation.tscn")
	main=packed.instantiate()
	root.add_child(main)
	await process_frame
	var index := int(OS.get_environment("ADOPTED_ROOM_INDEX"))
	await key(KEY_1+index)
	room=main.rooms[index]
	run_id=("render-" if rendering else "headless-")+str(room["id"])
	check(main.selected==index and state()["node"]==room["node"],"5室の番号入力による識別",room["id"])
	check(main.view._map["backdrop"]["path"]==room["path"],"背景の識別")
	var probes: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string(out+"/probes.json")))[room["id"]]
	for kind in ["floor","solid"]:
		for cell in probes[kind]:check(main.game.first_region_walkable(WorldExpedition.point(cell))==(kind=="floor"),"目視由来の独立固定座標",{"kind":kind,"cell":cell})
	var rejected := GameSession.new()
	check(not rejected.import_state(main.game.export_state()),"開発位置を本番保存として受理しない")
	var before: Dictionary=main.game.export_state()
	check(not main.submit_player_action({"kind":"save"}),"開発起動の保存操作拒否")
	check(not main.submit_player_action({"kind":"world_interact"}),"開発起動の物語操作拒否")
	check(main.game.export_state()==before,"拒否後に進行状態不変")
	if rendering:await capture("entry")
	await walk_all(here())
	var count := 0
	for row in room["layout"]:count+=str(row).count(".")
	check(visited.size()==count-1,"入口以外の全床を通常入力で訪問・復帰",{"visited":visited.size(),"floors":count})
	check(here()==WorldExpedition.point(room["spawn"]),"全床巡回後に入口へ戻る")
	await move(Vector2i.DOWN,Vector2i(6,10),"敷居へ")
	await move(Vector2i.DOWN,Vector2i(6,11),"通常door処理で入口確認領域へ")
	check(state()["room"]==1,"退出を実測")
	await move(Vector2i.DOWN,Vector2i(6,11),"入口確認領域の外を拒否")
	await move(Vector2i.UP,Vector2i(6,10),"通常door処理で再入室")
	check(state()["room"]==0,"再入室を実測")
	await move(Vector2i.UP,Vector2i(6,9),"入室後も歩行可能")
	if rendering:
		await occlusion(probes,"behind")
		await occlusion(probes,"front")
	var after: Dictionary=main.game.export_state()
	for field in before:
		if field!="overworld":check(after[field]==before[field],"歩行後の進行・保存対象不変",field)
	check(after["overworld"]["cleared"]==before["overworld"]["cleared"] and after["overworld"]["opened"]==before["overworld"]["opened"],"踏破・開封フラグ不変")
	check(normal_game.export_state()==original_state,"別の既存ゲーム状態不変")
	var save_path := "user://task080-normal-"+str(OS.get_process_id())+".json"
	check(normal_game.save_game(save_path),"既存ゲームの保存")
	var loaded := GameSession.new()
	check(loaded.load_game(save_path) and loaded.export_state()==original_state,"既存保存の全状態往復")
	main.queue_free()
	await process_frame
	check(FirstRegion._data==region_before,"開発scene終了で室内登録を復元")
	check(FirstRegionPresentation._data==visuals_before,"開発scene終了で描画登録を復元")
	var failed := checks.filter(func(x:Dictionary)->bool:return not x["ok"]).size()
	var file := FileAccess.open(out+"/"+run_id+".json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"room":room["id"],"rendering":rendering,"checks":checks,"inputs":inputs,"pictures":pictures,"failed":failed},"\t"))
	file.close()
	print("ADOPTED_ROOM_RESULT: room=%s checks=%d inputs=%d failed=%d" % [room["id"],checks.size(),inputs.size(),failed])
	quit(0 if failed==0 else 1)
