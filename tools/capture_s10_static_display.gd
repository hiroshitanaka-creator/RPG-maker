extends "res://tools/check_s10_static_display.gd"
## 人工境界保存を起点に本番UI・Godotの実描画を保存。静的合成ではない。
var main: Node
var captures: Array = []

func frames(count: int = 4) -> void:
	for i in range(count):await process_frame

func key(code: int) -> void:
	var event := InputEventKey.new()
	event.keycode=code;event.physical_keycode=code;event.pressed=true
	root.push_input(event,true)
	event=event.duplicate();event.pressed=false;root.push_input(event,true)
	await frames()

func walk(target: Vector2i) -> void:
	var saved: Dictionary=main.game.export_state()
	for p in route(saved,WorldExpedition.point(saved["overworld"]["cell"]),target):
		var delta: Vector2i=p-WorldExpedition.point(main.game.overworld_state()["cell"])
		await create_timer(0.16).timeout
		check(main.submit_player_action({"kind":"world_move","dx":delta.x,"dy":delta.y}),"撮影経路の通常移動入力",p)
		for frame in range(120):
			await process_frame
			if not main._world_mover.active():break
		check(main.game.overworld_state()["cell"]==([33,9] if p==Vector2i(8,11) else [p.x,p.y]),"通常移動・既存扉遷移完了",p)

func picture(name: String) -> void:
	await frames()
	await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var im := root.get_texture().get_image()
	check(DisplayServer.get_name()!="headless" and im.get_size()==Vector2i(512,288),"実Godot 512×288画面",name)
	check(im.save_png(OUT+name+".png")==OK,"実画面保存",name)
	var screen: FirstRegionScreen=main._region_screen
	var view: FirstRegionView=screen.map_view
	var saved: Dictionary=main.game.export_state()
	var state: Dictionary=saved["overworld"]
	var player := WorldExpedition.point(state["cell"])
	var actors: Array=[]
	for event in FirstRegion.residents_for(saved):
		var cell := FirstRegion.event_cell(saved,event)
		var texture: Texture2D=load("res://"+str(event["static_sprite"])) if event.has("static_sprite") else load("res://assets/characters/"+str(event["sprite"])+"/walk.png")
		var sprite := texture.get_image() if event.has("static_sprite") else texture.get_image().get_region(Rect2i(0,FirstRegion.event_facing(saved,event)*48,32,48))
		actors.append({"id":event["id"],"cell":cell,"sprite":sprite})
	var member: Dictionary=saved["party"].filter(func(a:Dictionary)->bool:return a["id"]==saved.get("leader_id","pc_01"))[0]
	var appearance := CharacterVisuals.appearance(member,"walk",view.walk_frame,int(state["facing"]))
	actors.append({"id":"player","cell":player,"sprite":(load(appearance["path"]) as Texture2D).get_image().get_region(Rect2i(appearance["region"]))})
	actors.sort_custom(func(a:Dictionary,b:Dictionary)->bool:return a["cell"].y<b["cell"].y)
	var overlay: Dictionary=view._map["overlays"]
	var atlas: Image=(load("res://"+str(overlay["path"])) as Texture2D).get_image()
	var windows: Array=[]
	for panel in screen.find_children("*","PanelContainer",true,false):
		if panel.is_visible_in_tree():windows.append(panel.get_global_rect())
	var record := {"image":name+".png","cell":state["cell"],"camera":[view._camera.x,view._camera.y],"mode":screen.screen_mode,"actors":[]}
	for index in range(actors.size()):
		var actor: Dictionary=actors[index]
		var cell: Vector2i=actor["cell"]
		var stats := {"id":actor["id"],"visible":0,"matched":0,"actor_hidden":0,"overlay_hidden":0,"ui_covered":0,"outside":0}
		for y in range(48):
			for x in range(32):
				var color: Color=actor["sprite"].get_pixel(x,y)
				if color.a<1:continue
				var world := cell*32+Vector2i(x,y-16)
				var pos := Vector2i(view._screen(Vector2(cell))+Vector2(x,y-16))
				if not Rect2i(Vector2i.ZERO,im.get_size()).has_point(pos):stats["outside"]+=1;continue
				var hidden := false
				for next in range(index+1,actors.size()):
					var local: Vector2i=world-(actors[next]["cell"]*32+Vector2i(0,-16))
					if Rect2i(0,0,32,48).has_point(local) and actors[next]["sprite"].get_pixelv(local).a>0:hidden=true;break
				if hidden:stats["actor_hidden"]+=1;continue
				for piece in overlay["pieces"]:
					if float(piece[6])-0.5<=cell.y+1:continue
					var local: Vector2i=world-Vector2i(piece[4],piece[5])
					if Rect2i(0,0,int(piece[2]),int(piece[3])).has_point(local) and atlas.get_pixel(int(piece[0])+local.x,int(piece[1])+local.y).a>0:hidden=true;break
				if hidden:stats["overlay_hidden"]+=1;continue
				for rect in windows:
					if rect.has_point(Vector2(pos)+Vector2(.5,.5)):hidden=true;break
				if hidden:stats["ui_covered"]+=1;continue
				stats["visible"]+=1
				var actual := im.get_pixelv(pos)
				if maxi(maxi(absi(actual.r8-color.r8),absi(actual.g8-color.g8)),absi(actual.b8-color.b8))<=1:stats["matched"]+=1
		check((stats["visible"]>0 or (actor["id"]=="player" and screen.screen_mode=="dialogue" and stats["ui_covered"]>0)) and stats["matched"]==stats["visible"],"人物の非遮蔽全画素一致: "+name,stats)
		if actor["id"]=="ner_static":
			check(stats["outside"]==0 and stats["ui_covered"]==0,"静止人物の欠落・画面境界・会話窓遮蔽なし",name)
			if name=="player-front":check(stats["actor_hidden"]>0,"主人公が手前の人物下部を遮蔽")
		if actor["id"]=="player" and name=="player-behind":check(stats["actor_hidden"]>0,"主人公が奥なら静止人物が前に重なる")
		if actor["id"]=="player" and name=="overlay-behind":check(stats["overlay_hidden"]>0,"既存上層による主人公の部分遮蔽")
		record["actors"].append(stats)
	captures.append(record)

func run() -> void:
	if DisplayServer.get_name()=="headless":printerr("S10_CAPTURE_FAIL: 実描画が必要");quit(2);return
	root.min_size=Vector2i(512,288);root.max_size=Vector2i(512,288);root.size=Vector2i(512,288)
	main=(load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main);await frames()
	main.save_path="user://task083-capture-save.json";main.checkpoint_path="user://task083-capture-checkpoint.json"
	var outside := fixture([33,9],false)
	FirstRegion.place(outside["overworld"],{"layer":"interior","node":"region2_village","room":0,"cell":[33,9]})
	check(main.game.import_state(outside),"撮影用の入口人工境界状態")
	main.mode=main.Mode.WORLD;main._refresh()
	await key(KEY_UP)
	for frame in range(120):
		await process_frame
		if main.mode==main.Mode.DIALOGUE:break
	check(main.mode==main.Mode.DIALOGUE and main._message_index==0,"通常方向キーの初入室・冒頭自動会話")
	await picture("entry-dialogue")
	await key(KEY_ENTER);await picture("conversation")
	check(main.game.save_game(main.save_path),"会話途中を通常保存")
	main._region_ui_action({"kind":"ui_title"});main._load_save();await frames()
	check(main.mode==main.Mode.DIALOGUE and main._message_index==0,"タイトル中断・通常ロードで冒頭復帰")
	await picture("interrupted-resume")
	for page in range(9):await key(KEY_ENTER)
	check(main.mode==main.Mode.WORLD,"通常決定キーで082完了")
	await picture("completed")
	await walk(Vector2i(8,7));await picture("player-front")
	await key(KEY_UP);await key(KEY_ENTER)
	check(main.mode==main.Mode.WORLD and main.game.export_state()["overworld"]["cell"]==[8,7],"通常キーで人物占有を通過せず新会話なし")
	# 通常に到達可能な北隣。前後の重なりを同じ描画経路で確認。
	await walk(Vector2i(8,5));await picture("player-behind")
	await walk(Vector2i(8,11));await frames()
	check(main.game.overworld_state()["room"]==0,"通常経路で退出")
	await create_timer(.2).timeout
	await key(KEY_UP)
	for frame in range(120):
		await process_frame
		if not main._world_mover.active():break
	check(main.mode==main.Mode.WORLD and main.game.overworld_state()["room"]==4,"通常再入室は非再演")
	await picture("reentry")
	# API検査が保存した占有位置の旧形式を本番ロード経路で読み込む。
	var file := FileAccess.open(main.save_path,FileAccess.WRITE)
	file.store_buffer(FileAccess.get_file_as_bytes(OUT+"occupied-true.json"));file.close()
	main._load_save();await frames()
	check(main.game.position_relocated and main.game.overworld_state()["cell"]==[8,10],"本番UIの旧占有保存復帰")
	await picture("old-save-relocated")
	# 上層は採用セルから離れている。主人公を既存燭台の後ろへ通常歩行させる。
	await walk(Vector2i(3,4));await picture("overlay-behind")
	var failed := checks.filter(func(c:Dictionary)->bool:return not c["ok"])
	var out := FileAccess.open(OUT+"capture-checks.json",FileAccess.WRITE)
	out.store_string(JSON.stringify({"status":"PASS" if failed.is_empty() else "FAIL","checks":checks,"captures":captures,"renderer":RenderingServer.get_current_rendering_method(),"driver":DisplayServer.get_name(),"fixture":"人工境界の通常保存・本番UI入力。実プレイヤーの初見プレイ記録ではない。"},"\t")+"\n");out.close()
	print("S10_CAPTURE_%s: checks=%d images=%d failures=%d"%["PASS" if failed.is_empty() else "FAIL",checks.size(),captures.size(),failed.size()])
	main.queue_free();await frames();quit(0 if failed.is_empty() else 1)
