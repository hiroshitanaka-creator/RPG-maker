extends "res://tools/capture_port_town.gd"
## 一枚絵の背景に置き換えた港町の灯台の見張り部屋を、通常操作だけで歩いて確かめ撮影する。
## 保存の出所・照合・上限は capture_port_town.gd と同じ（未編集の山道の保存をタイトルから再開）。

func _run() -> void:
	if OS.get_environment("PORT_CAPTURE_OUTPUT").is_empty():OS.set_environment("PORT_CAPTURE_OUTPUT","res://docs/verification/castle-hall-backdrops/runtime-lighthouse/")
	await super._run()

func lighthouse_layout_matches() -> bool:
	# 見えない通行地図と、実ゲームの歩ける判定が1マスずつ一致するか（灯台守のいるマスは通れない）。
	var room: Dictionary={}
	FirstRegion.data()
	for site in FirstRegion._data["sites"]:
		if site["id"]=="first_port":room=site["rooms"][8]
	var keeper: Array=room["events"][0]["cell"]
	var probe := _state().duplicate(true)
	probe["overworld"]["layer"]="interior";probe["overworld"]["node"]="first_port";probe["overworld"]["room"]=8
	for y in range(room["layout"].size()):
		var row: String=room["layout"][y]
		for x in range(row.length()):
			probe["overworld"]["cell"]=[x,y]
			var expected: bool=row.substr(x,1)=="." and [x,y]!=keeper
			if FirstRegion.walkable(probe,Vector2i(x,y))!=expected:
				_blocker="通行地図と実判定の不一致: %d,%d" % [x,y]
				return false
	return true

func bump_port(cell: Array, key: int, what: String) -> bool:
	if not castle_check(await _walk(port_point(8,cell)),"立ち位置へ歩行: "+what):return false
	var before: Array=_state()["overworld"]["cell"].duplicate()
	await _key(key);await create_timer(.17).timeout;await _settle()
	return castle_check(_state()["overworld"]["cell"]==before,"通れない絵の上へ進まない: "+what)

func port_route() -> void:
	if not castle_check(await _walk(_world_point(_definition["port_entrance"]["cell"]),_definition["port_spawn"]),"山道から港町へ通常入場"):return
	if not castle_check(await _walk(port_point(0,[31,6])),"灯台の扉の前へ"):return
	await picture("01-lighthouse-door")
	if not castle_check(await _walk(port_point(8,[9,8])),"港町の扉から見張り部屋へ通常入場"):return
	castle_check(_state()["overworld"]["room"]==8 and _state()["overworld"]["cell"]==[9,8],"見張り部屋の入口（扉の内側）に着く")
	await picture("02-lighthouse-entered")
	castle_check(lighthouse_layout_matches(),"見えない通行地図と実ゲームの通行判定が全247マスで一致")
	for probe in [[[7,4],KEY_UP,"望遠鏡"],[[6,4],KEY_LEFT,"机と椅子"],[[13,5],KEY_RIGHT,"樽"],[[5,8],KEY_LEFT,"塔の壁"]]:
		if not await bump_port(probe[0],probe[1],probe[2]):return
	if not castle_check(await _walk(port_point(8,[8,5])),"灯台守の前へ"):return
	await _key(KEY_UP);await _key(KEY_ENTER)
	castle_check(str(_snapshot().get("mode",""))=="dialogue","灯台守に話しかけられる")
	await picture("03-talk-keeper")
	await _settle()
	if not castle_check(await _walk(port_point(8,[10,2])),"窓の下まで歩く"):return
	await picture("04-under-window")
	save_check("灯台")
	if not castle_check(await _walk(port_point(0,[31,6])),"扉から港町へ通常退出"):return
	castle_check(_state()["overworld"]["room"]==0,"港町の通りに出る")
	await picture("05-left-lighthouse")
	if not castle_check(await _walk(port_point(8,[9,8])),"もう一度見張り部屋へ入る"):return
	await picture("06-reentered")
	castle_check(not port_battle_seen,"町と見張り部屋の中で戦闘なし")
