extends "res://tools/capture_port_town.gd"
## 未編集の通常到達保存から、習得・借用・航行・乗降・帰還を通常操作で撮影する。
var capture_busy := false
var sea_battles := 0
var sea_picture_started := false

func _run() -> void:
	OS.set_environment("PORT_CAPTURE_OUTPUT","res://docs/verification/sprint5-travel/runtime/")
	await super._run()

func _key(code: int) -> bool:
	while capture_busy:
		if not _active():return false
		await process_frame
	return await super._key(code)

func _combat_command(action: Dictionary) -> bool:
	while capture_busy:
		if not _active():return false
		await process_frame
	return await super._combat_command(action)

func _watch() -> void:
	super._watch()
	if not is_instance_valid(_main):return
	var screen: FirstRegionScreen=_main.get("_region_screen")
	if is_instance_valid(screen) and screen.screen_mode=="battle" and _session().current_encounter_id()=="coastal_encounter":
		if not sea_picture_started:
			sea_picture_started=true;sea_battles+=1;capture_busy=true
			capture_sea_battle.call_deferred()

func capture_sea_battle() -> void:
	await picture("04-sea-battle")
	var screen: FirstRegionScreen=_main.get("_region_screen")
	castle_check(is_instance_valid(screen) and screen.battle_background=="sea","海の戦闘背景を本番描画")
	capture_busy=false

func picture(name: String) -> void:
	if _snapshot().get("mode")!="world" or _state()["overworld"]["transport"]!="ship":
		await super.picture(name)
		if name in ["01-bay-docked-ship","11-ship-returned-to-pier"]:check_docked_ship(name)
		return
	await _frames(3);await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := _main.get_viewport().get_texture().get_image()
	var screen: FirstRegionScreen=_main.get("_region_screen");var view := screen.map_view
	var state: Dictionary = _state()["overworld"]
	var texture := load("res://assets/vehicles/owner_ship.png") as Texture2D
	var sprite := texture.get_image().get_region(Rect2i(int(state["facing"])*96,0,96,96))
	var origin := WorldExpedition.point(view._map["origin"])
	var pos := view._screen(Vector2(WorldExpedition.point(state["cell"])-origin))+Vector2(-32,-64)
	var matched := 0;var opaque := 0
	for y in range(96):
		for x in range(96):
			var color := sprite.get_pixel(x,y)
			if color.a<1.0:continue
			opaque+=1
			var sample := Vector2i((pos+Vector2(x,y))*2)+Vector2i.ONE
			if sample.x>=0 and sample.y>=0 and sample.x<image.get_width() and sample.y<image.get_height() and image.get_pixelv(sample).is_equal_approx(color):matched+=1
	castle_check(opaque>0 and float(matched)/opaque>=.90,"本番の船画素が90%以上見える: "+name)
	visible_pixels.append({"image":name,"subject":"ship","matched":matched,"opaque":opaque})
	castle_check(image.save_png(OUTPUT+name+".png")==OK,"航行の実画面保存: "+name);castle_images.append(name+".png")

func check_docked_ship(name: String) -> void:
	var screen: FirstRegionScreen=_main.get("_region_screen");var view := screen.map_view
	castle_check(view.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST,"船の拡大表示にぼかしなし")
	var sprite := (load("res://assets/vehicles/owner_ship.png") as Texture2D).get_image().get_region(Rect2i(96,0,96,96))
	var image := Image.load_from_file(ProjectSettings.globalize_path(OUTPUT+name+".png"))
	var cell := WorldExpedition.point(FirstRegionTravel.data()["docks"][0]["display_cell"])
	var pos := view._screen(Vector2(cell))+Vector2(-80,-160)
	var matched := 0;var opaque := 0
	for y in range(96):
		for x in range(96):
			var color := sprite.get_pixel(x,y)
			if color.a<1.0:continue
			opaque+=1
			var sample := Vector2i((pos+Vector2(x*2,y*2))*2)+Vector2i.ONE
			if sample.x>=0 and sample.y>=0 and sample.x<image.get_width() and sample.y<image.get_height() and image.get_pixelv(sample).is_equal_approx(color):matched+=1
	castle_check(opaque>0 and float(matched)/opaque>=.90,"停泊船の画素が90%以上見える: "+name)
	visible_pixels.append({"image":name,"subject":"docked_ship","matched":matched,"opaque":opaque})

func port_route() -> void:
	if not castle_check(await _walk(_world_point(_definition["port_entrance"]["cell"]),_definition["port_spawn"]),"港町へ通常入場"):return
	if not castle_check(await _walk(port_point(1,[7,6])),"出航前の宿"):return
	await talk(KEY_UP)
	castle_check(_state()["party"].all(func(a:Dictionary)->bool:return a["hp"]==a["max_hp"] and a["mp"]==a["max_mp"]),"4人を通常の宿で回復")
	castle_check(not FirstRegionTravel.snapshot(_state()).get("return_learned",false) and not FirstRegionTravel.snapshot(_state()).get("ship_owned",false),"習得・借用前")
	if not castle_check(await _walk(port_point(5,[8,6])),"祠へ通常入場"):return
	await _key(KEY_UP);await _key(KEY_ENTER)
	castle_check(not FirstRegionTravel.snapshot(_state()).get("return_learned",false),"会話の途中では未習得")
	await _settle();castle_check(FirstRegionTravel.snapshot(_state())["return_learned"],"会話を終えて習得")
	if not castle_check(await _walk(port_point(7,[9,7])),"荷受け所へ通常入場"):return
	await _key(KEY_RIGHT);await _key(KEY_ENTER)
	castle_check(not FirstRegionTravel.snapshot(_state())["ship_owned"],"会話の途中では未借用")
	await _settle();castle_check(FirstRegionTravel.snapshot(_state())["ship_owned"],"会話を終えて借用")
	var ship_before: Array=FirstRegionTravel.snapshot(_state())["ship_cell"].duplicate()
	await _key(KEY_ENTER);await _settle()
	castle_check(FirstRegionTravel.snapshot(_state())["ship_cell"]==ship_before,"繰り返し話しても船を増やさない")
	if not castle_check(await _walk(port_point(0,[28,13])),"停泊船を見渡す桟橋へ"):return
	await picture("01-bay-docked-ship")
	var dock: Dictionary=FirstRegionTravel.data()["docks"][0]
	if not castle_check(await _walk(dock["land"]),"乗船位置へ通常歩行"):return
	await picture("02-before-boarding")
	castle_check(_session().first_region_boarding_label()=="船に乗る","乗船の案内")
	await _key(KEY_ENTER);await _settle()
	castle_check(_state()["overworld"]["transport"]=="ship" and _state()["overworld"]["cell"]==dock["ship_cell"],"決定キーで乗船・沿岸へ")
	save_check("出航")
	if not castle_check(await _walk(_world_point([65,50])),"海を通常航行"):return
	await picture("03-sailing")
	castle_check(_session().first_region_boarding_label().is_empty(),"沖では下船の案内なし")
	var before := _state();await _key(KEY_ENTER);await _settle()
	castle_check(_state()==before,"沖で決定しても下船しない")
	var shallow: Dictionary=FirstRegionTravel.data()["docks"][1]
	if not castle_check(await _walk(_world_point(shallow["ship_cell"])),"浅瀬へ通常航行"):return
	await picture("05-shallows-before-landing")
	await _key(KEY_ENTER);await _settle()
	castle_check(_state()["overworld"]["transport"]=="walk" and FirstRegion.at(_state()["overworld"],shallow["land"]),"浅瀬で下船")
	await picture("06-shallows-on-foot");save_check("浅瀬")
	await _key(KEY_ENTER);await _settle()
	castle_check(_state()["overworld"]["transport"]=="ship","浅瀬で再乗船")
	await picture("07-shallows-reboarding")
	if not castle_check(await _walk(_world_point([65,50])),"沖へ再出航"):return
	# 通常の遭遇が起こるまで、同じ海域を有限回だけ往復する。乱数・勝敗を注入しない。
	for i in range(80):
		if sea_battles>0:break
		if not castle_check(await _walk(_world_point([66 if i%2==0 else 65,50])),"通常の海の遭遇を確認"):return
	castle_check(sea_battles>0,"海の通常遭遇と戦闘を観測")
	castle_check(_state()["overworld"]["transport"]=="ship" and FirstRegionTravel.snapshot(_state())["ship_cell"]==_state()["overworld"]["cell"],"戦闘後も船・位置を保持")
	save_check("海の戦闘後")
	before=_state()
	if not castle_check(await _key(KEY_ESCAPE),"航行中のメニュー"):return
	if not castle_check(await _button(["帰還の風"]),"帰還の風を選択"):return
	await picture("08-return-caster-selection")
	var actor: Dictionary=before["party"][0]
	if not castle_check(await _button(["%s MP %d" % [actor["name"],actor["mp"]]]),"使う仲間を選択"):return
	await picture("09-return-destination-selection")
	if not castle_check(await _button(["港町"]),"行き先に港町を選択"):return
	var after:=_state()
	castle_check(after["party"][0]["mp"]==before["party"][0]["mp"]-2,"通常操作でMP2消費")
	for i in [1,2,3]:castle_check(after["party"][i]["mp"]==before["party"][i]["mp"],"他の仲間のMP不変")
	castle_check(FirstRegion.at(after["overworld"],_outside(_definition["port_entrance"])) and after["overworld"]["transport"]=="walk","港町の入口前へ徒歩で帰還")
	castle_check(FirstRegionTravel.snapshot(after)["ship_cell"]==dock["ship_cell"],"船も港へ戻る")
	await picture("10-returned-to-port");save_check("帰還後")
	if not castle_check(await _walk(_world_point(_definition["port_entrance"]["cell"]),_definition["port_spawn"]),"帰還後に港町へ入場"):return
	if not castle_check(await _walk(port_point(0,[28,13])),"戻った船を確認する桟橋へ"):return
	await picture("11-ship-returned-to-pier")
	if not castle_check(await _walk(dock["land"]),"港での再乗降位置へ"):return
	await _key(KEY_ENTER);await _settle();castle_check(_state()["overworld"]["transport"]=="ship","港から再乗船")
	await _key(KEY_ENTER);await _settle();castle_check(_state()["overworld"]["transport"]=="walk" and FirstRegion.at(_state()["overworld"],dock["land"]),"港で下船")
	await picture("12-port-disembarked");save_check("港で下船後")
	castle_check(not port_battle_seen,"港町内は非戦闘")
