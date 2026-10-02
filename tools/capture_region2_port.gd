extends "res://tools/capture_coastal_travel.gd"
## --prepareも本番撮影も各180秒。既存の通常入力・戦闘処理をそのまま使う。
var preparation := false
var port_started_at := 0
var new_port_battle := false
var source_hash := ""
var port_shots: Array = []
const DEPARTURE := "res://.tools/region2-port-departure.json"
const ORIGIN := "res://docs/verification/region2-port/preparation/save-origin.json"

func p(room_id: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":"brine_port","room":room_id,"cell":cell}

func _trigger_points() -> Array:
	var points := super._trigger_points()
	if _definition.has("second_port_exit"):
		points.append(_definition["second_port_exit"])
		points.append(_world_point(_definition["second_port_entrance"]["cell"]))
	return points

func _watch() -> void:
	super._watch()
	if is_instance_valid(_main) and _state().get("overworld",{}).get("node")=="brine_port" and _battle()!=null:new_port_battle=true

func capture_sea_battle() -> void:
	await picture("02-first-sea-battle")
	capture_busy=false

func picture(name: String) -> void:
	if name.begins_with("06-room-"):
		# 場所名の表示を通常どおり待つ。ゲームの状態や表示フラグを書き換えない。
		await create_timer(2.3).timeout
	await super.picture(name)
	if name.begins_with("06-room-"):
		var panel: FirstRegionScreen=_main.get("_region_screen")
		var view := panel.map_view
		var saved := _state();var image := _main.get_viewport().get_texture().get_image()
		for event in FirstRegion.residents_for(saved):
			var texture := load("res://assets/characters/"+str(event["sprite"])+"/walk.png") as Texture2D
			var sprite := texture.get_image().get_region(Rect2i(0,FirstRegion.event_facing(saved,event)*48,32,48))
			var pos := view._screen(Vector2(FirstRegion.event_cell(saved,event)))+Vector2(0,-16)
			var opaque := 0;var matched := 0
			for y in range(24):
				for x in range(32):
					var color := sprite.get_pixel(x,y)
					if color.a<1.0:continue
					opaque+=1
					var sample := Vector2i((pos+Vector2(x,y))*2)+Vector2i.ONE
					if Rect2i(Vector2i.ZERO,image.get_size()).has_point(sample) and image.get_pixelv(sample).is_equal_approx(color):matched+=1
			castle_check(opaque>0 and opaque==matched,"店員の頭・顔（上24pxの不透明画素）が全て見える: "+name)
			visible_pixels.append({"image":name,"subject":"clerk_head","region":[0,0,32,24],"opaque":opaque,"matched":matched})
	port_shots.append({"image":name+".png","pose":_pose(),"mode":_snapshot().get("mode")})

func _run() -> void:
	preparation="--prepare" in OS.get_cmdline_user_args()
	port_started_at=_deadline-LIMIT_MS
	OUTPUT="res://docs/verification/region2-port/"+("preparation/" if preparation else "runtime/")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.min_size=Vector2i(1024,576);root.max_size=Vector2i(1024,576);root.size=Vector2i(1024,576)
	var source: String="res://.tools/port-departure.json" if preparation else DEPARTURE
	var origin_path: String="res://docs/verification/sprint5-port-town/departure/save-origin.json" if preparation else ORIGIN
	if not castle_check(FileAccess.file_exists(source) and FileAccess.file_exists(origin_path),"未編集の通常到達保存と出所記録がある"):finish_port();return
	var origin: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(origin_path))
	source_hash=FileAccess.get_sha256(source)
	if not castle_check(source_hash==origin["sha256"],"開始保存のバイト不変"):finish_port();return
	var copy_path := "user://qa_"+OS.get_environment("RPG_QA_SAVE_PREFIX")+"_save.json"
	var file := FileAccess.open(copy_path,FileAccess.WRITE);file.store_buffer(FileAccess.get_file_as_bytes(source));file.close()
	var scene: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	_main=scene.instantiate();root.add_child(_main);process_frame.connect(_watch);await _frames()
	if not castle_check(await _button(["手動セーブから再開"]),"タイトルから未編集保存を再開"):finish_port();return
	if not castle_check(_load_definition(),"本番の部屋と入口の定義"):finish_port();return
	_definition.merge(Region2Port.data()["definition"].duplicate(true))
	_definition["doors"].append_array(_definition["port_doors"])
	_definition["doors"].append_array(_definition["second_port_doors"])
	FirstRegion.data();_sites=FirstRegion._data["sites"].duplicate(true)
	if preparation:await prepare_departure()
	else:await visit_port()
	finish_port()

func prepare_departure() -> void:
	castle_check(not FirstRegionTravel.snapshot(_state()).get("ship_owned",false),"通常到達の山道保存は船取得前")
	if not castle_check(await _walk(_world_point(_definition["port_entrance"]["cell"]),_definition["port_spawn"]),"第1港へ徒歩入場"):return
	if not castle_check(await _walk(port_point(1,[11,9])),"第1港の宿へ"):return
	await talk(KEY_UP)
	if not castle_check(await _walk(port_point(5,[8,7])),"祠で帰還の風を教わる"):return
	await talk(KEY_UP)
	if not castle_check(await _walk(port_point(7,[8,5])),"港務所で船を借りる"):return
	await talk(KEY_UP)
	var dock: Dictionary=FirstRegionTravel.data()["docks"][0]
	if not castle_check(await _walk(dock["land"]),"第1港の乗船位置へ"):return
	await _key(KEY_ENTER);await _settle()
	if not castle_check(_state()["overworld"]["transport"]=="ship" and FirstRegionTravel.snapshot(_state())["ship_owned"] and FirstRegionTravel.snapshot(_state())["return_learned"],"通常操作で船を取得して乗船"):return
	await picture("01-departure")
	var path := "user://region2_departure_%d.json" % OS.get_process_id()
	if not castle_check(_session().save_game(path),"通常取得直後の保存"):return
	var copy := FileAccess.open(DEPARTURE,FileAccess.WRITE);copy.store_buffer(FileAccess.get_file_as_bytes(path));copy.close()
	castle_check(FileAccess.get_sha256(DEPARTURE)==FileAccess.get_sha256(path),"船取得後の保存を無編集コピー")
	PlaySessionMetrics.write_json(ORIGIN,{"sha256":FileAccess.get_sha256(DEPARTURE),"upstream_sha256":source_hash,"producer":"capture_region2_port.gd --prepare","method":"prepare_port_departureの通常到達保存から、キーと画面のボタンで宿泊・習得・借用・乗船。保存の位置・所持品・フラグを変更しない。","pose":_pose(),"ship_owned":true,"return_learned":true})

func full_town() -> void:
	var viewport := SubViewport.new();viewport.size=Vector2i(1536,1024);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var view := FirstRegionView.new();view.saved=_state().duplicate(true);view.size=Vector2(1536,1024)
	viewport.add_child(view)
	await _frames(6);await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	castle_check(image.get_size()==Vector2i(1536,1024) and image.save_png(OUTPUT+"04-full-town.png")==OK,"本番描画クラスによる町全体の保存")
	castle_images.append("04-full-town.png")
	port_shots.append({"image":"04-full-town.png","pose":_pose(),"method":"到達後の状態の読み取り専用コピーを、本番FirstRegionViewで全体表示。通常のゲーム窓とは別の全体図。"})
	viewport.queue_free();await _frames()

func visit_port() -> void:
	castle_check(_state()["overworld"]["transport"]=="ship" and FirstRegionTravel.snapshot(_state()).get("ship_owned",false),"船取得後の未編集保存から開始")
	await picture("01-departure")
	var dock: Dictionary=Region2Port.data()["docks"][0]
	if not castle_check(await _walk(_world_point(dock["ship_cell"])),"第1港から第2港へ通常航行"):return
	await picture("02-arrival-at-second-port")
	await _key(KEY_ENTER);await _settle()
	if not castle_check(FirstRegion.at(_state()["overworld"],dock["land"]) and _state()["overworld"]["transport"]=="walk","中央桟橋へ通常下船"):return
	castle_check(FirstRegionTravel.snapshot(_state())["visited"].has("brine_port"),"訪問済み記録")
	await picture("03-central-pier")
	await full_town()
	if not castle_check(await _walk(p(0,[22,17])),"井戸の広場へ歩行"):return
	await picture("05-well-market")
	for entry in [[1,"inn"],[2,"item"],[3,"weapon"],[4,"armor"],[5,"shrine"],[6,"harbor"]]:
		var index: int=entry[0];var position: Dictionary=Region2Port.data()["interaction_positions"][str(index)]
		if not castle_check(await _walk(p(index,position["cell"])),"町を歩いて入室: "+entry[1]):return
		await picture("06-room-%02d-%s" % [index,entry[1]])
		var before := _state()
		await _key([KEY_DOWN,KEY_LEFT,KEY_RIGHT,KEY_UP][position["facing"]]);await _key(KEY_ENTER)
		if index in [2,3]:
			await picture("07-service-%02d-%s" % [index,entry[1]])
			var label: String="回復薬を買う　5" if index==2 else "補強剣を買う　15"
			if not castle_check(await _button([label]),"通常購入: "+entry[1]):return
			if index==2:castle_check(_state()["inventory"]["potion"]==before["inventory"]["potion"]+1 and _state()["first_region"]["coins"]==before["first_region"]["coins"]-5,"道具と代金")
			else:castle_check("iron_blade" in _state()["integrated"]["armory"] and _state()["first_region"]["coins"]==before["first_region"]["coins"]-15,"武器と代金")
			if not castle_check(await _button(["やめる"]),"店から戻る"):return
		else:
			castle_check(_snapshot().get("mode")=="dialogue","会話が表示される: "+entry[1])
			await picture("07-service-%02d-%s" % [index,entry[1]])
			await _settle()
			if index==1:castle_check(_state()["party"].all(func(a:Dictionary)->bool:return a["hp"]==a["max_hp"] and a["mp"]==a["max_mp"]),"通常宿泊で4人回復")
			if index==4:castle_check(_state()["first_region"]["coins"]==before["first_region"]["coins"] and _state()["integrated"]["armory"]==before["integrated"]["armory"],"防具屋は会話だけ")
			if index==5:castle_check(_session().at_purification_shrine(),"祠として認識")
		save_check("第2港"+entry[1])
	# 通常の保存・読込メニューでも場所を復元する。
	var before_save := _state()
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["セーブ"]) and await _button(["現在の冒険に戻る"]),"通常メニューで保存"):return
	if not castle_check(await _walk(p(6,[8,10])),"保存後に別の位置へ移動"):return
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["手動セーブから再開"]) and await _settle(),"通常メニューから保存再開"):return
	castle_check(_state()==before_save,"保存前の全ゲーム状態を復元")
	await picture("08-save-restored")
	if not castle_check(await _walk(dock["land"]),"中央桟橋まで戻る"):return
	await _key(KEY_ENTER);await _settle()
	castle_check(_state()["overworld"]["transport"]=="ship","再乗船")
	await picture("09-reboarded")
	if not castle_check(await _walk(_world_point([155,111])),"第2港の沖へ"):return
	var before_return := _state();var actor: Dictionary=before_return["party"].filter(func(a:Dictionary)->bool:return a["hp"]>0 and a["mp"]>=2)[0]
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["帰還の風"]) and await _button(["%s MP %d" % [actor["name"],actor["mp"]]]),"帰還の風と使う仲間を選ぶ"):return
	await picture("10-return-destination")
	if not castle_check(await _button(["第2地方の港町（仮）"]),"訪問済みの第2港を選ぶ"):return
	var after := _state();var after_actor: Dictionary=after["party"].filter(func(a:Dictionary)->bool:return a["id"]==actor["id"])[0]
	castle_check(after_actor["mp"]==actor["mp"]-2 and FirstRegion.at(after["overworld"],FirstRegion.outside("second_port_entrance")) and FirstRegionTravel.snapshot(after)["ship_cell"]==dock["ship_cell"],"帰還MP2・人物と船が戻る")
	await picture("11-returned-to-coast")
	if not castle_check(await _walk(_world_point(_definition["second_port_entrance"]["cell"]),_definition["second_port_spawn"]),"沿岸から石アーチへ通常入場"):return
	await picture("12-stone-arch-entrance")
	castle_check(not new_port_battle,"町と6室は非戦闘")

func finish_port() -> void:
	castle_check(Time.get_ticks_msec()-port_started_at<LIMIT_MS,"180秒以内")
	castle_check(_moves<=LIMIT_MOVES and _input_log.size()<LIMIT_INPUTS and not _input_violation,"既存の移動・入力上限と禁止操作を維持")
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if castle_failures.is_empty() else "FAIL","checks":castle_checks,"failures":castle_failures,"images":castle_images,"shots":port_shots,"visible_pixels":visible_pixels,"moves":_moves,"inputs":_input_log,"turns":_turns,"source_sha256":source_hash,"elapsed_ms":Time.get_ticks_msec()-port_started_at,"limits":{"milliseconds":LIMIT_MS,"moves":LIMIT_MOVES,"inputs":LIMIT_INPUTS,"turns":LIMIT_TURNS},"method":"通常入力による船取得準備" if preparation else "船取得後の無編集保存をタイトルから再開し、通常入力で第2港を航行・徒歩・施設利用・保存再開。","build":BuildIdentity.current()})
	for failure in castle_failures:printerr("REGION2_PORT_RUNTIME_FAIL: "+failure)
	print("REGION2_PORT_RUNTIME_PASS: checks=%d images=%d" % [castle_checks,castle_images.size()] if castle_failures.is_empty() else "REGION2_PORT_RUNTIME_FAIL")
	_finished=true
	quit(0 if castle_failures.is_empty() else 1)
