extends "res://tools/capture_castle_town.gd"
## 通常操作で作成した山道の保存から、港町だけを通常UIで確認する。
var port_battle_seen := false

func _watch() -> void:
	super._watch()
	if is_instance_valid(_main) and _state().get("overworld",{}).get("node")=="first_port" and _battle()!=null:port_battle_seen=true

# 一枚絵の背景へ変更した建物（2026年9月29日）の、店員・住人へ話しかける立ち位置。店員は台の裏。
const INTERIOR_STAND := {2:[8,5],3:[8,5],4:[8,5],5:[8,7],6:[8,7],7:[8,5],8:[9,7]}

func port_point(index: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":"first_port","room":index,"cell":cell}

func _trigger_points() -> Array:
	var points := super._trigger_points()
	if not _definition.is_empty():
		points.append(_definition["port_exit"])
		points.append(_world_point(_definition["port_entrance"]["cell"]))
	return points

func _run() -> void:
	OUTPUT=OS.get_environment("PORT_CAPTURE_OUTPUT") if not OS.get_environment("PORT_CAPTURE_OUTPUT").is_empty() else "res://docs/verification/sprint5-travel/port-runtime/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.min_size=Vector2i(1024,576);root.max_size=Vector2i(1024,576);root.size=Vector2i(1024,576)
	var raw := FileAccess.get_file_as_bytes("res://.tools/port-departure.json")
	var hash := HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(raw)
	var origin: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/sprint5-port-town/departure/save-origin.json"))
	if not castle_check(hash.finish().hex_encode()==origin["sha256"],"通常到達からの保存が未編集"):finish_port();return
	var copy_path := "user://qa_"+OS.get_environment("RPG_QA_SAVE_PREFIX")+"_save.json"
	var file := FileAccess.open(copy_path,FileAccess.WRITE);file.store_buffer(raw);file.close()
	var packed: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	_main=packed.instantiate();root.add_child(_main);process_frame.connect(_watch);await _frames()
	if not castle_check(await _button(["手動セーブから再開"]),"タイトルから通常保存を再開"):finish_port();return
	if not castle_check(_load_definition(),"本番定義の読取"):finish_port();return
	_definition["doors"].append_array(_definition["port_doors"])
	castle_check(_state()["party"].size()==4 and _state()["progress_flags"].get("mountain_path_open",false),"スイナ加入後の山道から開始")
	await port_route()
	finish_port()

func save_check(label: String) -> void:
	var path := "user://port_%s_%d.json" % [label,OS.get_process_id()]
	castle_check(_session().save_game(path),label+"を保存")
	var loaded := GameSession.new()
	castle_check(loaded.load_game(path) and loaded.export_state()==_state(),label+"の場所・向き・4人・所持品を完全復元")

func talk(facing: int) -> void:
	await _key(facing);await create_timer(.17).timeout
	await _key(KEY_ENTER);await _settle()

func port_route() -> void:
	await picture("01-world-port")
	if not castle_check(await _walk(_world_point(_definition["port_entrance"]["cell"]),_definition["port_spawn"]),"山道から港町へ通常入場"):return
	await picture("02-town-entrance")
	# まず宿へ行き、塔で消耗した4人を休ませる。
	# 宿は一枚絵の背景へ変更（2026年9月29日）。受付台の前(11,9)から、台越しに宿の主人へ話す。
	if not castle_check(await _walk(port_point(1,[11,9])),"宿へ通常入場"):return
	await talk(KEY_UP)
	castle_check(_state()["party"].all(func(a:Dictionary)->bool:return a["hp"]==a["max_hp"] and a["mp"]==a["max_mp"]),"宿で戦闘不能を含む4人が回復")
	await picture("03-inn")
	save_check("宿")
	if not castle_check(await _walk(port_point(0,[18,7])),"露店の広場へ"):return
	await picture("04-market")
	for entry in [[2,"05-item-shop"],[3,"06-weapon-shop"],[4,"07-armor-shop"],[5,"08-shrine"],[6,"09-home"],[7,"10-harbor-office"],[8,"11-lighthouse-room"]]:
		var index: int=entry[0]
		if not castle_check(await _walk(port_point(index,INTERIOR_STAND[index])),"建物の通常入場: "+entry[1]):return
		if index==2 or index==3:
			var before := _state()
			await _key(KEY_UP);await _key(KEY_ENTER)
			await picture(entry[1])
			var label := "回復薬を買う　5" if index==2 else "補強剣を買う　15"
			if not castle_check(await _button([label]),"通常購入: "+label):return
			if index==2:castle_check(_state()["inventory"]["potion"]==before["inventory"]["potion"]+1 and _state()["first_region"]["coins"]==before["first_region"]["coins"]-5,"回復薬と代金")
			else:castle_check("iron_blade" in _state()["integrated"]["armory"] and _state()["first_region"]["coins"]==before["first_region"]["coins"]-15,"既存武器と代金")
			if not castle_check(await _button(["やめる"]),"買い物から戻る"):return
		else:
			if index in [4,7]:await talk(KEY_UP)
			elif index==6 or index==8:await talk(KEY_RIGHT)
			if index==5:castle_check(_session().at_purification_shrine(),"港町の祠として認識")
			await picture(entry[1])
	for shot in [[[29,5],"12-lighthouse-coast"],[[25,13],"13-upper-pier"],[[26,25],"14-lower-pier"]]:
		if not castle_check(await _walk(port_point(0,shot[0])),"桟橋と海岸へ通常歩行"):return
		await picture(shot[1])
	save_check("桟橋")
	castle_check(not _session().first_region_walkable(Vector2i(26,21)),"桟橋から海へ歩いて落ちない")
	castle_check(not _session().at_purification_shrine(),"町全体を祠として扱わない")
	if not castle_check(await _walk(_definition["port_exit"],_outside(_definition["port_entrance"])),"港町から山道へ通常退出"):return
	castle_check(_outward(_definition["port_entrance"]),"出口の一歩手前・外向き")
	await picture("15-return-world")
	save_check("退出後")
	castle_check(not port_battle_seen,"町と施設内に戦闘なし")
	castle_check(_state()["overworld"]["transport"]=="walk","町の施設確認後は徒歩のまま")

func finish_port() -> void:
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if castle_failures.is_empty() else "FAIL","checks":castle_checks,"failures":castle_failures,"images":castle_images,"visible_pixels":visible_pixels,"moves":_moves,"inputs":_input_log.size(),"limits":{"milliseconds":LIMIT_MS,"inputs":LIMIT_INPUTS,"moves":LIMIT_MOVES},"source":"prepare_port_departure.gdが通常到達から作った保存を、未編集のままタイトル画面から再開。","build":BuildIdentity.current()})
	for failure in castle_failures:printerr("PORT_RUNTIME_FAIL: "+failure)
	print("PORT_RUNTIME_PASS: checks=%d images=%d" % [castle_checks,castle_images.size()] if castle_failures.is_empty() else "PORT_RUNTIME_FAIL")
	quit(0 if castle_failures.is_empty() else 1)
