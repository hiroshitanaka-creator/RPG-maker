extends "res://tools/capture_port_town.gd"
## 一枚絵の背景に置き換えた港町の宿屋を、通常操作だけで歩いて確かめ撮影する。
## 保存の出所・照合・上限は capture_port_town.gd と同じ（未編集の山道の保存をタイトルから再開）。
const INN_LAYOUT_SOURCE := "res://assets/source_records/port-inn-backdrop.json"

func _run() -> void:
	if OS.get_environment("PORT_CAPTURE_OUTPUT").is_empty():OS.set_environment("PORT_CAPTURE_OUTPUT","res://docs/verification/port-inn-backdrop/runtime/")
	await super._run()

func inn_layout_matches() -> bool:
	# 見えない通行地図と、実ゲームの歩ける判定が1マスずつ一致するか（宿の主人のマスだけは人がいるので通れない）。
	var record: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(INN_LAYOUT_SOURCE))
	var keeper := Vector2i(int(record["innkeeper"][0]),int(record["innkeeper"][1]))
	var saved := _state();var probe: Dictionary=saved.duplicate(true)
	for y in range(record["layout"].size()):
		var row: String=record["layout"][y]
		for x in range(row.length()):
			probe["overworld"]["cell"]=[x,y]
			var expected: bool=row.substr(x,1)=="." and Vector2i(x,y)!=keeper
			if FirstRegion.walkable(probe,Vector2i(x,y))!=expected:
				_blocker="通行地図と実判定の不一致: %d,%d" % [x,y]
				return false
	return true

func port_route() -> void:
	if not castle_check(await _walk(_world_point(_definition["port_entrance"]["cell"]),_definition["port_spawn"]),"山道から港町へ通常入場"):return
	if not castle_check(await _walk(port_point(1,[8,10])),"港町の扉から宿へ通常入場"):return
	castle_check(_state()["overworld"]["room"]==1 and _state()["overworld"]["cell"]==[8,10],"宿の入口（扉の内側）に着く")
	await picture("01-inn-entered")
	castle_check(inn_layout_matches(),"見えない通行地図と実ゲームの通行判定が全216マスで一致")
	for probe in [[[8,9],KEY_UP],[[3,9],KEY_LEFT],[[9,8],KEY_RIGHT],[[11,9],KEY_UP]]:
		# 壁・たる・受付台へ向かって歩こうとしても、その場から動かない。
		if not castle_check(await _walk(port_point(1,probe[0])),"宿の中を通常歩行: %s" % str(probe[0])):return
		var before: Array=_state()["overworld"]["cell"].duplicate()
		if probe[0]!=[8,9]:
			await _key(probe[1]);await create_timer(.17).timeout;await _settle()
			castle_check(_state()["overworld"]["cell"]==before,"通れない絵の上へ進まない: %s" % str(probe[0]))
	if not castle_check(await _walk(port_point(1,[9,3])),"右の寝室へ扉口から入る"):return
	await picture("02-right-bedroom")
	if not castle_check(await _walk(port_point(1,[4,3])),"左の寝室へ扉口から入る"):return
	await picture("03-left-bedroom")
	castle_check(_state()["party"].any(func(a:Dictionary)->bool:return a["hp"]<a["max_hp"] or a["mp"]<a["max_mp"]),"泊まる前は消耗している")
	if not castle_check(await _walk(port_point(1,[11,9])),"受付台の前へ"):return
	await _key(KEY_UP);await create_timer(.17).timeout
	await _key(KEY_ENTER)
	castle_check(str(_snapshot().get("mode",""))=="dialogue","受付台越しに宿の主人と会話が始まる")
	await picture("04-talk-innkeeper")
	await _settle()
	castle_check(_state()["party"].all(func(a:Dictionary)->bool:return a["hp"]==a["max_hp"] and a["mp"]==a["max_mp"]),"宿で戦闘不能を含む4人が回復")
	await picture("05-after-rest")
	save_check("宿")
	if not castle_check(await _walk(port_point(0,[4,7])),"宿の扉から港町へ通常退出"):return
	castle_check(_state()["overworld"]["room"]==0,"港町の通りに出る")
	await picture("06-left-inn")
	if not castle_check(await _walk(port_point(1,[8,9])),"もう一度宿へ入る"):return
	await picture("07-reentered")
	save_check("再入場後")
	castle_check(not port_battle_seen,"町と宿の中で戦闘なし")
