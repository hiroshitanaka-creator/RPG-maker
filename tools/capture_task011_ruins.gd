extends "res://tools/check_task011_runtime.gd"
## 本番画面を使う直接読込みの確認用状態。歩行・階段は通常キー。通常保存は使わない。
const OUTPUT := "res://docs/verification/task-011/latest/images/"
var main
var shots: Array = []
var key_steps := 0

func _initialize() -> void:
	call_deferred("capture_run")

func frames(count: int = 3) -> void:
	for _frame in range(count):await process_frame

func capture_run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	check(DisplayServer.get_name() != "headless","実レンダラー必須")
	check(OS.get_environment("RPG_QA_SAVE_PREFIX").begins_with("task011-"),"専用保存接頭辞必須")
	root.size=Vector2i(1024,576);DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var scene: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	main=scene.instantiate();root.add_child(main);await frames()
	var start := GameSession.new();check(start.new_first_region(),"本番新ゲーム")
	walk_enemies=start.enemy_definitions
	base=start.export_state();base["party"].append_array(base["first_region"]["reserve"]);base["first_region"]["reserve"]=[]
	for index in range(4):
		check(main.game.import_state(placed(index,Region2Ruins.landing(index))),"直接読込みの確認用状態")
		main.mode=main.Mode.WORLD;main._refresh();await frames()
		await picture("floor%d-landing" % (index+1))
		var before: Dictionary = main.game.export_state()
		var probes := find_probes(before)
		if check(probes.size()==2,"柱や壁の奥・手前で歩ける場所を実画素から選ぶ"):
			await walk(probes[0]);await picture("floor%d-behind" % (index+1))
			await walk(probes[1]);await picture("floor%d-front" % (index+1))
		var save_path: String=main.save_path
		check(save_path.contains("task011-"),"撮影は検査用通常保存のみ")
		var expected: Dictionary=main.game.export_state()
		check(main.game.save_game(save_path),"確認用状態の本番保存")
		var resumed := GameSession.new();check(resumed.load_game(save_path) and resumed.export_state()==expected,"撮影用保存の別インスタンス再開")
		var here := WorldExpedition.point(expected["overworld"]["cell"])
		var stepped := false
		for dir in DIRS:
			var next: Vector2i=here+dir
			if not FirstRegion.walkable(expected,next):continue
			await walk([next.x,next.y],"floor%d-walking" % (index+1));stepped=true;break
		check(stepped,"歩行コマを通常入力で撮影")
	# 状態の注入は起点だけ。その後はキー操作で1階→最下層→1階を往復。
	check(main.game.import_state(placed(0,Region2Ruins.landing(0))),"階段撮影の確認用起点")
	main.mode=main.Mode.WORLD;main._refresh();await frames()
	for link_index in [0,2,4,5,3,1]:
		var link: Dictionary=Region2Ruins.data()["stairs"][link_index]
		await walk(link["from_cell"])
		var state: Dictionary=main.game.export_state()["overworld"]
		check(state["room"]==link["to_room"] and state["cell"]==link["to_cell"] and state["facing"]==link["facing"],"通常キーによる階段着地")
		await picture("stairs-%d-to-%d" % [link["from_room"]+1,link["to_room"]+1])
	await battle_shots()
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","execution_sha":OS.get_environment("TASK011_EXECUTION_SHA"),"confirmation_state":true,"renderer":DisplayServer.get_name(),"window_size":[root.size.x,root.size.y],"key_steps":key_steps,"encounter_returns":encounter_returns,"encounter_return_policy":"通知後の全状態を保持した確認用探索。実戦・報酬検証ではない","images":shots,"failures":failures}
	var file := FileAccess.open(OUTPUT+"checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"));file.close()
	for failure in failures:print("TASK011_FAIL: "+failure)
	print("TASK011_CAPTURE_%s: images=%d key_steps=%d" % [report["status"],shots.size(),key_steps])
	main.queue_free();await frames();quit(0 if failures.is_empty() else 1)

func walk(cell: Array, walking_picture: String="") -> void:
	var saved: Dictionary=main.game.export_state()
	var path := route(saved,WorldExpedition.point(cell))
	if not check(not path.is_empty() or saved["overworld"]["cell"]==cell,"撮影の通常歩行経路 "+str(cell)):return
	for next in path:
		var current := WorldExpedition.point(main.game.export_state()["overworld"]["cell"])
		var step_before: Dictionary=main.game.export_state()
		var dir := next-current
		var keys := [KEY_DOWN,KEY_LEFT,KEY_RIGHT,KEY_UP]
		var event := InputEventKey.new();event.keycode=keys[DIRS.find(dir)];event.physical_keycode=event.keycode;event.pressed=true
		root.push_input(event,true);event=event.duplicate();event.pressed=false;root.push_input(event,true);await frames(3)
		var deadline := Time.get_ticks_msec()+2000
		while main._world_mover.active() and Time.get_ticks_msec()<deadline:await process_frame
		check(not main._world_mover.active(),"通常一歩の時間内終了")
		if main.mode==main.Mode.BATTLE:
			var observed_walk_frame: int=main._walk_frame
			main.game=resume_confirmation_encounter(main.game)
			check(main._walk_frame==observed_walk_frame,"本番入力の歩行コマを確認用復帰でも保持")
			# 戦闘確認中の時間を探索の表示時間に含めない。入力で得たコマ値は変更しない。
			main._world_motion_ms=Time.get_ticks_msec()
			main.mode=main.Mode.WORLD;main._refresh();await frames(3)
		check(main.mode==main.Mode.WORLD,"確認用の道中通知後に探索画面へ戻る")
		if next==path[-1] and not walking_picture.is_empty():await picture(walking_picture)
		await create_timer(0.16).timeout
		key_steps += 1
		var step_after: Dictionary=main.game.export_state()
		var stair := {}
		for link in Region2Ruins.data()["stairs"]:
			if step_before["overworld"]["room"]==link["from_room"] and [next.x,next.y]==link["from_cell"]:stair=link
		if not stair.is_empty():check_stair(step_before,step_after,stair)
		else:check(step_after["overworld"]["layer"]==step_before["overworld"]["layer"] and step_after["overworld"]["node"]==step_before["overworld"]["node"] and step_after["overworld"]["room"]==step_before["overworld"]["room"] and step_after["overworld"]["cell"]==[next.x,next.y],"キー歩行の位置 "+str(next)+" actual="+str(step_after["overworld"]["cell"]))

func sprite_for(saved: Dictionary) -> Image:
	var member: Dictionary=saved["party"].filter(func(a:Dictionary)->bool:return a["id"]==saved.get("leader_id","pc_01"))[0]
	var appearance := CharacterVisuals.appearance(member,"walk",0,int(saved["overworld"]["facing"]))
	return (load(appearance["path"]) as Texture2D).get_image().get_region(Rect2i(appearance["region"]))

func hidden_count(map: Dictionary, sprite: Image, cell: Vector2i, only_column: bool=false) -> int:
	var atlas := (load("res://"+str(map["overlays"]["path"])) as Texture2D).get_image()
	var count := 0
	for y in range(48):
		for x in range(32):
			if sprite.get_pixel(x,y).a<1:continue
			var pixel := cell*32+Vector2i(x,y-16)
			for piece in map["overlays"]["pieces"]:
				if only_column and not (str(piece[7]).contains("柱") or str(piece[7]).contains("巨像")):continue
				if float(piece[6])-0.5<=cell.y+1:continue
				var local := pixel-Vector2i(piece[4],piece[5])
				if local.x>=0 and local.y>=0 and local.x<piece[2] and local.y<piece[3] and atlas.get_pixel(piece[0]+local.x,piece[1]+local.y).a>0:count+=1;break
	return count

func find_probes(saved: Dictionary) -> Array:
	var map := FirstRegionPresentation.map_for(saved["overworld"]);var sprite := sprite_for(saved)
	for y in range(map["height"]):
		for x in range(map["width"]):
			var cell := Vector2i(x,y)
			if not FirstRegion.walkable(saved,cell) or route(saved,cell).is_empty() or hidden_count(map,sprite,cell,true)<8:continue
			for delta in range(1,5):
				var front := cell+Vector2i(0,delta)
				if FirstRegion.walkable(saved,front) and not route(saved,front).is_empty() and hidden_count(map,sprite,front)==0:return [[x,y],[x,y+delta]]
	return []

func picture(name: String) -> void:
	await frames(4);await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := root.get_texture().get_image()
	check(image.get_size()==Vector2i(1024,576),"撮影寸法")
	check(image.save_png(OUTPUT+name+".png")==OK,"実画面保存")
	var shot := {"image":name+".png","confirmation_state":true}
	if main.mode==main.Mode.WORLD:
		var screen: FirstRegionScreen=main._region_screen;var view := screen.map_view
		var saved: Dictionary=main.game.export_state();var state: Dictionary=saved["overworld"]
		var sprite := sprite_for(saved);var cell := WorldExpedition.point(state["cell"])
		# 本番の歩行フレームを照合する。
		var member: Dictionary=saved["party"].filter(func(a:Dictionary)->bool:return a["id"]==saved.get("leader_id","pc_01"))[0]
		var appearance := CharacterVisuals.appearance(member,"walk",view.walk_frame,int(state["facing"]))
		sprite=(load(appearance["path"]) as Texture2D).get_image().get_region(Rect2i(appearance["region"]))
		var map: Dictionary=view._map;var atlas := (load("res://"+str(map["overlays"]["path"])) as Texture2D).get_image()
		if name.contains("walking"):check(view.walk_frame!=0,"通常一歩の直後の歩行コマ")
		var pos := view._screen(Vector2(cell))+Vector2(0,-16)
		var visible := 0;var hidden := 0;var matched := 0;var hidden_matched := 0
		for y in range(48):
			for x in range(32):
				var expected := sprite.get_pixel(x,y)
				if expected.a<1:continue
				var pixel := cell*32+Vector2i(x,y-16);var covered := false;var last_bottom := -1.0
				for piece in map["overlays"]["pieces"]:
					if float(piece[6])-0.5<=cell.y+1:continue
					var local := pixel-Vector2i(piece[4],piece[5])
					if local.x>=0 and local.y>=0 and local.x<piece[2] and local.y<piece[3]:
						var color := atlas.get_pixel(piece[0]+local.x,piece[1]+local.y)
						if color.a>0 and piece[6]>=last_bottom:covered=true;expected=color;last_bottom=piece[6]
				var sample := Vector2i((pos+Vector2(x,y))*2)+Vector2i.ONE
				if not Rect2i(Vector2i.ZERO,image.get_size()).has_point(sample):continue
				var actual := image.get_pixelv(sample)
				var same := maxi(maxi(absi(actual.r8-expected.r8),absi(actual.g8-expected.g8)),absi(actual.b8-expected.b8))<=1
				if covered:hidden+=1;hidden_matched+=int(same)
				else:visible+=1;matched+=int(same)
		check(visible>0 and visible==matched and hidden==hidden_matched,"人物と上層の実描画全画素一致: "+name)
		if name.contains("behind"):check(hidden>=8 and visible>=8,"奥で部分遮蔽")
		if name.contains("front"):check(hidden==0,"手前では人物を隠さない")
		shot.merge({"room":state["room"],"cell":state["cell"],"facing":state["facing"],"walk_frame":view.walk_frame,"camera":[view._camera.x,view._camera.y],"visible":visible,"hidden":hidden,"matched":matched,"hidden_matched":hidden_matched})
	shots.append(shot)

func battle_shots() -> void:
	main.hide()
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/source_records/task011-enemies.json"))
	var definitions := {}
	for enemy in data["enemies"]:definitions[enemy["id"]]=enemy
	var pages := [["ruins_sandstone_doll","ruins_cursed_beetle","ruins_sand_spirit"],["ruins_tomb_hound","desert_mummy","stone_gargoyle"],["ruins_sandstone_colossus"]]
	for i in range(3):
		var arena := RpgBattleView.new();arena.size=Vector2(512,288);arena.members=base["party"];arena.enemy_ids=pages[i];arena.definitions=definitions;arena.background="region2_ruins"
		root.add_child(arena)
		var label := Label.new();label.text="確認用状態 / 遺跡の素材見本（戦闘は未有効化）";label.position=Vector2(8,250);label.add_theme_font_override("font",RpgFonts.get_font());label.add_theme_font_size_override("font_size",12);arena.add_child(label)
		await frames(4);await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image();check(image.save_png(OUTPUT+"battle-%d.png" % (i+1))==OK,"本番戦闘描画器の素材見本")
		var rendered := []
		var background := (load("res://assets/backgrounds/region2_ruins.png") as Texture2D).get_image()
		for j in range(pages[i].size()):
			var region := arena.enemy_region(pages[i][j]);var rect := arena.actor_rect("enemy_%02d" % (j+1))
			var source := arena._enemy_texture(pages[i][j]).get_image();var opaque := 0;var matched := 0;var samples := 0;var boundaries := 0
			for y in range(ceili(rect.position.y*2),floori(rect.end.y*2)):
				for x in range(ceili(rect.position.x*2),floori(rect.end.x*2)):
					var uv := region.position+(Vector2(x+0.5,y+0.5)/2-rect.position)/(1.125 if pages[i][j]=="ruins_sandstone_colossus" else 0.75)
					var xs := [floori(uv.x)];var ys := [floori(uv.y)]
					# 最近傍の境界そのものだけはGPUの浮動小数点丸めで左右いずれにもなる。
					# 色の許容差は1、座標候補は境界の両側だけ。非境界は1画素に固定する。
					if absf(uv.x-roundf(uv.x))<0.0001:xs=[roundi(uv.x)-1,roundi(uv.x)]
					if absf(uv.y-roundf(uv.y))<0.0001:ys=[roundi(uv.y)-1,roundi(uv.y)]
					boundaries+=int(xs.size()*ys.size()>1);samples+=1
					var actual := image.get_pixel(x,y);var same := false;var solid := false
					for sy in ys:
						for sx in xs:
							var point := Vector2i(sx,sy)
							if not Rect2i(region).has_point(point):continue
							var expected := source.get_pixelv(point);solid=solid or expected.a==1
							if expected.a<1:expected=background.get_pixelv(Vector2i(x/2,y/2))
							same=same or maxi(maxi(absi(actual.r8-expected.r8),absi(actual.g8-expected.g8)),absi(actual.b8-expected.b8))<=1
					opaque+=int(solid);matched+=int(same)
			check(opaque>=20 and samples==matched,"戦闘見本の敵・透明部の実画素一致 "+pages[i][j])
			rendered.append({"id":pages[i][j],"opaque":opaque,"samples":samples,"matched":matched,"nearest_boundaries":boundaries,"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"region":[region.position.x,region.position.y,region.size.x,region.size.y]})
		for point in [Vector2i(10,10),Vector2i(1000,10)]:check(image.get_pixelv(point).is_equal_approx(background.get_pixelv(point/2)),"戦闘見本の背景実画素")
		shots.append({"image":"battle-%d.png" % (i+1),"confirmation_state":true,"enemies":pages[i],"rendered":rendered,"enabled_battle":false})
		arena.queue_free();await frames()
	main.show()
