extends SceneTree
## 独立した地形を検査入力として既存API・描画器へ渡す。本番データや保存へ登録しない。
const NODE_ID := "first_port"
const DIR := "res://docs/verification/region2-village-backdrops/"
var failures: Array[String] = []
var checks := 0
var capture := false
var previous_rooms: Dictionary
var previous_maps: Dictionary
var images: Array = []
var first_qa_room := 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:failures.append(message)

func _initialize() -> void:
	capture="--capture" in OS.get_cmdline_user_args()
	call_deferred("run")

func state_for(room_index: int, cell: Array) -> Dictionary:
	var game := GameSession.new()
	game.new_first_region()
	var saved := game.export_state()
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":NODE_ID,"room":first_qa_room+room_index,"cell":cell})
	saved["overworld"]["transport"]="walk"
	return saved

func reachable(saved: Dictionary, start: Vector2i) -> Dictionary:
	var found := {start:true}
	var queue: Array[Vector2i]=[start]
	var at := 0
	while at<queue.size():
		var p := queue[at];at+=1
		for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var q: Vector2i=p+d
			if not found.has(q) and FirstRegion.walkable(saved,q):found[q]=true;queue.append(q)
	return found

func screenshot(saved: Dictionary, name: String) -> void:
	var view := FirstRegionView.new()
	view.saved=saved;view.size=Vector2(512,288)
	root.add_child(view)
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_viewport().get_texture().get_image()
	check(image.get_size()==Vector2i(512,288),"実描画の解像度: "+name)
	var path := DIR+name+".png"
	check(image.save_png(path)==OK,"実描画の保存: "+name)
	var camera := view._camera
	var sprite_path := ""
	for actor in saved["party"]:
		if actor["id"]==saved.get("leader_id","pc_01"):sprite_path=CharacterVisuals.appearance(actor,"walk")["path"]
	images.append({"path":path.trim_prefix("res://"),"camera":[camera.x,camera.y],"cell":saved["overworld"]["cell"],"party_visible":not saved["party"].is_empty(),"sprite":sprite_path.trim_prefix("res://"),"facing":saved["overworld"]["facing"],"frame":0})
	view.queue_free()
	await process_frame

func occlusion(map: Dictionary, atlas: Image, sprite: Image, cell: Vector2i) -> Vector2i:
	var hidden := 0
	var visible := 0
	for y in range(48):
		for x in range(32):
			if sprite.get_pixel(x,3*48+y).a==0:continue
			var point := cell*32+Vector2i(x,y-16)
			var covered := false
			for piece in map["overlays"]["pieces"]:
				if float(piece[6])-0.5<=cell.y+1:continue
				var local := point-Vector2i(piece[4],piece[5])
				if local.x>=0 and local.y>=0 and local.x<int(piece[2]) and local.y<int(piece[3]) and atlas.get_pixel(int(piece[0])+local.x,int(piece[1])+local.y).a>0:covered=true;break
			if covered:hidden+=1
			else:visible+=1
	return Vector2i(hidden,visible)

func run() -> void:
	var source: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/region2_village_backdrops.json")))
	var record: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://assets/source_records/region2-village-backdrops.json")))
	FirstRegion.data();FirstRegionPresentation.data()
	previous_rooms=FirstRegion._data.duplicate(true)
	previous_maps=FirstRegionPresentation._data.duplicate(true)
	var roles: Array=["exterior","inn","item","weapon","shrine"]
	var rooms: Array=[]
	for site in FirstRegion._data["sites"]:
		if site["id"]==NODE_ID:first_qa_room=site["rooms"].size();break
	for i in range(roles.size()):
		var map: Dictionary=source["maps"][roles[i]]
		rooms.append({"layout":map["layout"],"events":[]})
		FirstRegionPresentation._data["maps"]["%s:%d" % [NODE_ID,first_qa_room+i]]=map
	# 既存の非戦闘拠点IDを検査プロセス内だけ借りる。遭遇ルールや本番保存は追加しない。
	for site in FirstRegion._data["sites"]:
		if site["id"]==NODE_ID:site["rooms"].append_array(rooms);break
	for i in range(roles.size()):
		var role: String=roles[i]
		var map: Dictionary=source["maps"][role]
		var info: Dictionary=record["maps"][role]
		var saved := state_for(i,info["start"])
		var start := WorldExpedition.point(info["start"])
		var found := reachable(saved,start)
		var all_walk := 0
		for y in range(map["height"]):
			for x in range(map["width"]):
				var expected: bool=str(map["layout"][y]).substr(x,1)=="."
				check(FirstRegion.walkable(saved,Vector2i(x,y))==expected,"通行API: %s %d,%d" % [role,x,y])
				if expected:all_walk+=1
		check(all_walk==found.size(),"全歩行マスが入口から到達: "+role)
		check(not FirstRegion.walkable(saved,Vector2i(-1,0)) and not FirstRegion.walkable(saved,Vector2i(map["width"],map["height"]-1)),"地図外を拒否: "+role)
		for label in info["doors"]:check(found.has(WorldExpedition.point(info["doors"][label])),"扉へ到達: "+role+"/"+label)
		for label in info["targets"]:check(found.has(WorldExpedition.point(info["targets"][label])),"確認点へ到達: "+role+"/"+label)
		for direction in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var moving := state_for(i,info["start"])
			var target: Vector2i=start+direction
			var valid := FirstRegion.walkable(moving,target)
			var outcome := FirstRegion.move(moving,target)
			check((outcome.get("kind","")=="moved" and moving["overworld"]["cell"]==[target.x,target.y]) if valid else (outcome.is_empty() and moving["overworld"]["cell"]==info["start"]),"既存の1歩移動: "+role+str(direction))
		if capture:
			check(DisplayServer.get_name()!="headless","実レンダラーを使用")
			root.size=Vector2i(512,288)
			root.position=Vector2i(-32000,-32000)
			var empty := saved.duplicate(true);empty["party"]=[]
			await screenshot(empty,role+"/native-empty")
			await screenshot(saved,role+"/native-start")
			var target: Array=info["doors"].values()[0] if role=="exterior" else info["targets"].values()[0]
			var front := state_for(i,target)
			await screenshot(front,role+"/native-detail")
			var atlas := (load("res://"+str(map["overlays"]["path"])) as Texture2D).get_image()
			var sprite := (load(CharacterVisuals.appearance(saved["party"][0],"walk")["path"]) as Texture2D).get_image()
			var tested := false
			for piece in map["overlays"]["pieces"]:
				for y in range(maxi(0,int(piece[6])-3),mini(map["height"],int(piece[6])-1)):
					for x in range(maxi(0,floori(float(piece[4])/32.0)),mini(map["width"],ceili(float(piece[4]+piece[2])/32.0))):
						if not FirstRegion.walkable(saved,Vector2i(x,y)):continue
						var counts := occlusion(map,atlas,sprite,Vector2i(x,y))
						if counts.x<8 or counts.y<8:continue
						var behind := state_for(i,[x,y]);behind["overworld"]["facing"]=3
						await screenshot(behind,role+"/native-behind")
						var blank := behind.duplicate(true);blank["party"]=[]
						await screenshot(blank,role+"/native-behind-empty")
						tested=true;break
					if tested:break
				if tested:break
			check(tested,"上層が人物を部分的に隠す実描画地点: "+role)
	FirstRegion._data=previous_rooms
	FirstRegionPresentation._data=previous_maps
	for failure in failures:printerr("VILLAGE_RUNTIME_FAIL: "+failure)
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"native_render":capture,"captures":images,"scope":"独立した地形を検査入力として既存の通行・移動・描画APIで検証。本番の施設機能・保存接続は検証対象外。"}
	PlaySessionMetrics.write_json(DIR+("native-checks.json" if capture else "runtime-checks.json"),report)
	print("VILLAGE_RUNTIME_PASS: checks=%d" % checks if failures.is_empty() else "VILLAGE_RUNTIME_FAIL")
	quit(0 if failures.is_empty() else 1)
