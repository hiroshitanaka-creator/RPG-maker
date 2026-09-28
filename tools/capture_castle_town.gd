extends "res://tools/smoke_first_region.gd"
## 保護済みの最初の地方を通常操作で通過し、その続きの城下町・城を追加確認する。
const OUTPUT := "res://docs/verification/sprint5-castle-town/runtime/"
var castle_failures: Array[String]=[]
var castle_checks := 0
var castle_started := false
var castle_images: Array[String]=[]
var visible_pixels: Array=[]

func castle_check(ok: bool, reason: String) -> bool:
	castle_checks+=1
	if not ok:castle_failures.append(reason+" / "+_blocker)
	return ok

func castle_point(room_id: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":"first_castle","room":room_id,"cell":cell}

func picture(name: String) -> void:
	if DisplayServer.get_name()=="headless":return
	await _frames(3);await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var im := _main.get_viewport().get_texture().get_image()
	if _snapshot().get("mode")=="world":
		var screen: FirstRegionScreen=_main.get("_region_screen")
		var view := screen.map_view
		var saved := _state()
		var member: Dictionary=saved["party"].filter(func(a:Dictionary)->bool:return a["id"]==saved.get("leader_id","pc_01"))[0]
		var appearance := CharacterVisuals.appearance(member,"walk",view.walk_frame,int(saved["overworld"]["facing"]))
		var texture := load(appearance["path"]) as Texture2D
		var sprite := texture.get_image().get_region(Rect2i(appearance["region"]))
		var origin := WorldExpedition.point(view._map.get("origin",[0,0]))
		var pos := view._screen(Vector2(WorldExpedition.point(saved["overworld"]["cell"])-origin)+view.movement_offset)+Vector2(0,-16)
		var matched := 0;var opaque := 0
		for y in range(48):
			for x in range(32):
				var color := sprite.get_pixel(x,y)
				if color.a<1.0:continue
				opaque+=1
				var sample := Vector2i((pos+Vector2(x,y))*2)+Vector2i.ONE
				if sample.x>=0 and sample.y>=0 and sample.x<im.get_width() and sample.y<im.get_height() and im.get_pixelv(sample).is_equal_approx(color):matched+=1
		visible_pixels.append({"image":name,"matched":matched,"opaque":opaque})
		castle_check(opaque>0 and float(matched)/opaque>=0.90,"本番画面の人物画素が90%以上見える: "+name)
	castle_check(not im.is_empty() and im.save_png(OUTPUT+name+".png")==OK,"実画面保存: "+name)
	castle_images.append(name+".png")

func _run() -> void:
	root.min_size=Vector2i(1024,576);root.max_size=Vector2i(1024,576);root.size=Vector2i(1024,576)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	await super._run()

func _trigger_points() -> Array:
	var points := super._trigger_points()
	if castle_started:
		points.append(_definition["castle_exit"])
		points.append(_world_point(_definition["castle_entrance"]["cell"]))
	return points

func _castle_route() -> void:
	_definition["doors"].append_array(_definition["castle_doors"])
	if not castle_check(await _walk(_outside(_definition["castle_entrance"])),"関所から城下町前へ歩行"):return
	await picture("01-world-entrance")
	if not castle_check(await _walk(_world_point(_definition["castle_entrance"]["cell"]),_definition["castle_spawn"]),"城下町へ通常入場"):return
	if not castle_check(await _walk(castle_point(0,[20,14])),"広場へ歩行"):return
	await picture("02-town-plaza")
	var state_before := _state()
	castle_check(not state_before["progress_flags"].get("job_change_unlocked",false),"謁見前は転職未解放")
	castle_check(not _session().choose_job("pc_01","thief"),"解放前の転職拒否")
	if not castle_check(await _walk(castle_point(1,[16,13])),"城の中庭へ歩行"):return
	await picture("03-castle-court")
	if not castle_check(await _walk(castle_point(1,[8,6])),"城の外観を見渡す位置へ歩行"):return
	await picture("03b-castle-exterior")
	if not castle_check(await _walk(castle_point(2,[16,6])),"玉座の前へ歩行"):return
	await picture("04-throne-hall")
	if not castle_check(await _key(KEY_UP),"王の方を向く"):return
	if not castle_check(await _key(KEY_ENTER),"王と会話"):return
	castle_check(_snapshot().get("mode")=="dialogue","謁見会話が表示された")
	castle_check(not _state()["progress_flags"].get("job_change_unlocked",false),"会話開始だけでは解放しない")
	await picture("05-royal-audience")
	if not castle_check(await _settle(),"謁見の会話を最後まで送る"):return
	castle_check(_state()["progress_flags"].get("job_change_unlocked",false),"基本職と技の装着を解放")
	castle_check(_state()["progress_flags"].get("castle_north_permission",false),"北の森への許可を記録")
	castle_check(not _session().choose_job("pc_01","slime"),"魔物職は節目6まで未解放")
	castle_check(not _session().choose_job("pc_01","sage"),"上級職は節目8まで未解放")
	if not castle_check(await _key(KEY_ESCAPE),"メニューを開く"):return
	if not castle_check(await _button(["じょうたい・そうび・へんせい"]),"編成を開く"):return
	castle_check(_main.submit_player_action({"kind":"choose_job","actor":"pc_01","job":"thief"}),"通常の職業選択で盗賊へ転職")
	await picture("06-job-change")
	if not castle_check(await _button(["戻る"]),"編成から戻る"):return
	await picture("07-new-costume")
	var save_path: String="user://castle_roundtrip_%d.json" % OS.get_process_id()
	castle_check(_session().save_game(save_path),"城内で保存")
	var loaded := GameSession.new()
	castle_check(loaded.load_game(save_path) and loaded.export_state()==_state(),"場所・向き・転職・進行の保存復元")
	for entry in [[3,[8,6],"08-treasury"],[10,[8,8],"09-library"],[4,[7,6],"10-inn"],[5,[7,6],"11-item-shop"],[6,[7,6],"12-weapon-shop"],[8,[8,6],"13-shrine"]]:
		if not castle_check(await _walk(castle_point(entry[0],entry[1])),"各建物へ通常出入り: "+entry[2]):return
		await picture(entry[2])
		if entry[0] in [3,4,5,6,8]:
			var before_service := _state()
			await _step_direction(Vector2i.UP);await _key(KEY_ENTER)
			if entry[0] in [5,6]:
				await picture(entry[2]+"-counter")
				var label := "回復薬を買う　5" if entry[0]==5 else "補強剣を買う　15"
				castle_check(await _button([label]),"店の通常購入: "+label)
				if entry[0]==5:castle_check(_state()["inventory"]["potion"]==before_service["inventory"]["potion"]+1 and _state()["first_region"]["coins"]==before_service["first_region"]["coins"]-5,"道具の受取と支払い")
				else:castle_check("iron_blade" in _state()["integrated"]["armory"] and _state()["first_region"]["coins"]==before_service["first_region"]["coins"]-15,"武器の受取と支払い")
				castle_check(await _button(["やめる"]),"店から通常退出")
			else:
				castle_check(await _settle(),"施設の会話を終了")
				if entry[0]==3:
					castle_check(_state()["inventory"]["potion"]==before_service["inventory"]["potion"]+3,"宝物庫の補給を受取")
					var received: int=_state()["inventory"]["potion"]
					await _key(KEY_ENTER);await _settle()
					castle_check(_state()["inventory"]["potion"]==received,"宝箱の二重受取なし")
				if entry[0]==4:castle_check(_state()["party"].all(func(a:Dictionary)->bool:return a["hp"]==a["max_hp"] and a["mp"]==a["max_mp"]),"宿でHP・MP回復")
	if not castle_check(await _walk(_definition["castle_exit"],_outside(_definition["castle_entrance"])),"城下町から世界マップへ戻る"):return
	castle_check(_outward(_definition["castle_entrance"]),"出口の一歩手前・外向き")
	await picture("14-return-world")

func _finish() -> void:
	if castle_started:return
	if not _route_finished:super._finish();return
	castle_started=true
	_blocker="城下町・城の追加確認"
	await _castle_route()
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if castle_failures.is_empty() else "FAIL","checks":castle_checks,"failures":castle_failures,"images":castle_images,"visible_pixels":visible_pixels,"native_render":DisplayServer.get_name()!="headless","input_source":"新規開始から保護済みR-07の通常入力経路を通り、その続きから歩行・会話・職業選択。位置や所持品の注入なし。","moves":_moves,"inputs":_input_log.size(),"build":BuildIdentity.current()})
	for failure in castle_failures:printerr("CASTLE_RUNTIME_FAIL: "+failure)
	if not castle_failures.is_empty():quit(1);return
	print("CASTLE_RUNTIME_PASS: checks=%d images=%d" % [castle_checks,castle_images.size()])
	super._finish()
