extends "res://tools/capture_coastal_travel.gd"
## 通常航行と地上遭遇は保存・位置・乱数を書き換えない。並べた素材見本だけを複製セッションで描く。
var second_sea_seen := false
var ground_seen := false
var preview_state: Dictionary = {}

func _run() -> void:
	OUTPUT="res://docs/verification/sprint6-desert-monsters/runtime/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.min_size=Vector2i(1024,576);root.max_size=Vector2i(1024,576);root.size=Vector2i(1024,576)
	var raw := FileAccess.get_file_as_bytes("res://.tools/port-departure.json")
	var hash := HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(raw)
	var origin: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/sprint5-port-town/departure/save-origin.json"))
	if not castle_check(hash.finish().hex_encode()==origin["sha256"],"通常到達の開始保存が未編集"):finish_port();return
	var file := FileAccess.open("user://qa_"+OS.get_environment("RPG_QA_SAVE_PREFIX")+"_save.json",FileAccess.WRITE)
	file.store_buffer(raw);file.close()
	var packed: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	_main=packed.instantiate();root.add_child(_main);process_frame.connect(_watch);await _frames()
	if not castle_check(await _button(["手動セーブから再開"]),"タイトルから通常読込"):finish_port();return
	if not castle_check(_load_definition(),"本番の配置を読取"):finish_port();return
	_definition["doors"].append_array(_definition["port_doors"])
	await port_route()
	if castle_failures.is_empty():
		await candidate_battle([{"sprite_id":"desert_scorpion","name":"サソリ（仮）"},{"sprite_id":"sand_worm","name":"砂の虫（仮）"},{"sprite_id":"desert_mummy","name":"ミイラ（仮）"}],"07-imported-three-desert","新原画3体の表示見本・ミイラは通常遭遇には未登録")
		await candidate_battle([{"sprite_id":"thorn_cactus","name":"花咲く刺サボテン（仮）"},{"sprite_id":"desert_scorpion","name":"サソリ（仮）"},{"sprite_id":"sand_worm","name":"砂の虫（仮）"}],"08-coastal-three-desert","沿岸に登録した3種の並び見本")
	finish_port()

func _watch() -> void:
	super._watch()
	if not is_instance_valid(_main):return
	var panel: FirstRegionScreen=_main.get("_region_screen")
	if is_instance_valid(panel) and panel.screen_mode=="battle" and not second_sea_seen and _session().current_encounter_id()=="second_coast_encounter":
		second_sea_seen=true;capture_busy=true;capture_second_sea.call_deferred()
	if is_instance_valid(panel) and panel.screen_mode=="battle" and not ground_seen and _session().current_encounter_id()=="second_coast_ground_encounter":
		ground_seen=true;capture_busy=true;capture_ground.call_deferred()

func capture_ground() -> void:
	await picture("06-ground-natural-encounter")
	var panel: FirstRegionScreen=_main.get("_region_screen")
	castle_check(panel.battle_background=="desert","地上の通常遭遇で採用済み砂漠背景")
	castle_check(_session().current_enemy_ids().all(func(id:String)->bool:return id in ["coast_thorn_cactus","coast_scorpion","coast_worm"]),"指定3種だけの地上遭遇")
	capture_busy=false

func capture_sea_battle() -> void:
	await picture("00-first-region-sea-battle")
	capture_busy=false

func capture_second_sea() -> void:
	await picture("03-second-region-sea-battle")
	var panel: FirstRegionScreen=_main.get("_region_screen")
	castle_check(panel.battle_background=="sea","通常遭遇で採用済みの海背景")
	castle_check(_session().current_enemy_ids().all(func(id:String)->bool:return id in ["coast_water_blob","coast_redfin","coast_red_crab"]),"控えから取り込んだ海の敵")
	capture_busy=false

func port_route() -> void:
	if not castle_check(await _walk(_world_point(_definition["port_entrance"]["cell"]),_definition["port_spawn"]),"第1地方の港へ入場"):return
	if not castle_check(await _walk(port_point(1,[11,9])),"宿へ到達"):return
	await talk(KEY_UP);preview_state=_state().duplicate(true)
	if not castle_check(await _walk(port_point(5,[8,7])),"帰還の風の祠へ"):return
	await talk(KEY_UP)
	if not castle_check(await _walk(port_point(7,[8,5])),"船の荷受け所へ"):return
	await talk(KEY_UP)
	var first: Dictionary=FirstRegionTravel.data()["docks"][0]
	if not castle_check(await _walk(first["land"]),"既存の桟橋へ"):return
	await _key(KEY_ENTER);await _settle()
	castle_check(_state()["overworld"]["transport"]=="ship","通常操作で乗船")
	if not castle_check(await _walk(_world_point([150,109])),"第1地方から第2地方へ航行"):return
	await picture("01-crossing-to-second-region");save_check("第2地方への航行")
	var dock: Dictionary=SecondRegionCoast.data()["docks"][0]
	if not castle_check(await _walk(_world_point(dock["ship_cell"])),"第2地方の浅瀬へ"):return
	await _key(KEY_ENTER);await _settle()
	castle_check(FirstRegion.at(_state()["overworld"],dock["land"]) and _state()["overworld"]["transport"]=="walk","岸へ通常下船")
	await picture("02-landed-on-sand-coast");save_check("砂の岸へ上陸")
	castle_check(_main.call("_region_background")=="desert","この岸では砂漠の戦闘背景を選ぶ")
	if not castle_check(await _walk(_world_point(SecondRegionCoast.data()["walk_goal"])),"沿岸の徒歩経路"):return
	await picture("04-coast-walking");save_check("第2地方の徒歩")
	for i in range(80):
		if ground_seen:break
		if not castle_check(await _walk(_world_point([168 if i%2==0 else 169,99])),"地上の通常遭遇まで有限回の往復"):return
	castle_check(ground_seen,"地上の通常遭遇を観測")
	if not castle_check(await _walk(dock["land"]),"岸の船まで戻る"):return
	await _key(KEY_ENTER);await _settle()
	castle_check(_state()["overworld"]["transport"]=="ship","同じ浅瀬から再乗船")
	for i in range(80):
		if second_sea_seen:break
		if not castle_check(await _walk(_world_point([154 if i%2==0 else 155,109])),"海の通常遭遇まで有限回の往復"):return
	castle_check(second_sea_seen,"第2地方の海の通常遭遇を観測")
	var before := _state()
	var users: Array=before["party"].filter(func(a:Dictionary)->bool:return a["hp"]>0 and a["mp"]>=2)
	if not castle_check(not users.is_empty(),"帰還を使える生存者がいる"):return
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["帰還の風"]),"帰還の風を選ぶ"):return
	var actor: Dictionary=users[0]
	if not castle_check(await _button(["%s MP %d" % [actor["name"],actor["mp"]]]) and await _button(["港町"]),"第1地方の港町へ帰還"):return
	castle_check(FirstRegion.at(_state()["overworld"],FirstRegion.outside("port_entrance")),"通常操作で第1地方の入口へ")
	castle_check(FirstRegionTravel.snapshot(_state())["ship_cell"]==first["ship_cell"],"船も帰港")
	await picture("05-returned-to-first-region");save_check("第2地方から帰還")

func candidate_battle(proposals: Array, filename: String, caption: String) -> void:
	# 人工的な敵の表示見本。実際の航行用セッションや保存は変更しない。
	var original := _state()
	var preview := GameSession.new()
	if not castle_check(preview.import_state(preview_state),"見本用に通常宿泊後の状態を複製"):return
	var ids: Array[String]=[]
	var bases := ["shell_guard","slime","ward_slime"]
	for i in range(proposals.size()):
		var entry: Dictionary=preview.enemy_definitions[bases[i]].duplicate(true)
		entry["sprite_id"]=proposals[i]["sprite_id"];entry["name"]=proposals[i]["name"]
		preview.enemy_definitions[bases[i]]=entry;ids.append(bases[i])
	if not castle_check(preview.start_first_region_battle({"kind":"battle","id":"ground_candidate_preview","enemies":ids,"seed":20260930})!=null,"候補の描画見本を開始"):return
	_main.visible=false
	var panel := FirstRegionScreen.new();panel.game=preview;panel.screen_mode="battle";panel.actor="pc_01";panel.battle_background="desert"
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font();panel.theme.default_font_size=11
	root.add_child(panel)
	var label := Label.new();label.text=caption;label.position=Vector2(8,4);label.add_theme_font_size_override("font_size",11);panel.add_child(label)
	await _frames(3);await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	castle_check(image.save_png(OUTPUT+filename+".png")==OK,"3体の本番戦闘描画を保存")
	castle_images.append(filename+".png")
	castle_check(_state()==original,"見本が通常プレイの状態を変えない")
	panel.queue_free();await process_frame;_main.visible=true
