extends "res://tools/capture_castle_town.gd"
## 城の部屋のつながり（中庭→大広間→謁見の間・宝物庫・書庫）と、一枚絵の背景に置き換えた
## 大広間・謁見の間を、通常操作だけで歩いて確かめ撮影する。
## 保存の出所は capture_castle_town.gd と同じ（新規開始から保護済みの通常経路）。
## 環境変数 CASTLE_CAPTURE_OUTPUT で保存先を変えられる。

func layout_matches(index: int) -> bool:
	# 見えない通行地図と、実ゲームの歩ける判定が1マスずつ一致するか（人物のいるマスは通れない）。
	var room: Dictionary={}
	FirstRegion.data()
	for site in FirstRegion._data["sites"]:
		if site["id"]=="first_castle":room=site["rooms"][index]
	var probe := _state().duplicate(true)
	probe["overworld"]["layer"]="interior";probe["overworld"]["node"]="first_castle";probe["overworld"]["room"]=index
	var npc_cells: Array=room["events"].filter(func(e:Dictionary)->bool:return e["kind"]=="npc").map(func(e:Dictionary)->Array:return e["cell"])
	for y in range(room["layout"].size()):
		var row: String=room["layout"][y]
		for x in range(row.length()):
			probe["overworld"]["cell"]=[x,y]
			var expected: bool=row.substr(x,1)=="." and [x,y] not in npc_cells
			if FirstRegion.walkable(probe,Vector2i(x,y))!=expected:
				_blocker="通行地図と実判定の不一致: 部屋%d %d,%d" % [index,x,y]
				return false
	return true

func bump(cell: Array, key: int, what: String) -> bool:
	# 通れない絵へ向かって歩こうとしても、その場から動かない。
	if not castle_check(await _walk(castle_point(_state()["overworld"]["room"],cell)),"立ち位置へ歩行: "+what):return false
	var before: Array=_state()["overworld"]["cell"].duplicate()
	await _key(key);await create_timer(.17).timeout;await _settle()
	return castle_check(_state()["overworld"]["cell"]==before,"通れない絵の上へ進まない: "+what)

func _castle_route() -> void:
	_definition["doors"].append_array(_definition["castle_doors"])
	if not castle_check(await _walk(_world_point(_definition["castle_entrance"]["cell"]),_definition["castle_spawn"]),"城下町へ通常入場"):return
	castle_check(not _state()["progress_flags"].get("job_change_unlocked",false),"謁見前は転職未解放")
	castle_check(not _session().choose_job("pc_01","thief"),"解放前の転職拒否")
	castle_check(layout_matches(11) and layout_matches(2),"大広間・謁見の間の通行地図が実判定と全マス一致")
	# 中庭 → 大広間
	if not castle_check(await _walk(castle_point(1,[16,13])),"城の中庭へ歩行"):return
	await picture("01-court")
	if not castle_check(await _walk(castle_point(11,[8,8])),"中庭の扉から大広間へ入る"):return
	castle_check(_state()["overworld"]["room"]==11 and _state()["overworld"]["cell"]==[8,8],"大広間の入口（下の両開きの扉の内側）に着く")
	await picture("02-great-hall-entered")
	for probe in [[[5,3],KEY_LEFT,"左の柱"],[[12,3],KEY_RIGHT,"右の柱"],[[7,8],KEY_DOWN,"大広間の下の壁"]]:
		if not await bump(probe[0],probe[1],probe[2]):return
	# 大広間 → 謁見の間（奥の中央の扉、3段の階段の上）
	if not castle_check(await _walk(castle_point(11,[8,3])),"奥の中央の扉の階段の下へ"):return
	await picture("03-great-hall-throne-door")
	if not castle_check(await _walk(castle_point(2,[11,12])),"奥の中央の扉から謁見の間へ入る"):return
	castle_check(_state()["overworld"]["room"]==2 and _state()["overworld"]["cell"]==[11,12],"謁見の間の入口に着く")
	await picture("04-throne-room-entered")
	if not castle_check(await _walk(castle_point(2,[12,6])),"玉座の前へ歩行"):return
	await picture("05-throne-room-king")
	if not castle_check(await _key(KEY_UP),"王の方を向く"):return
	if not castle_check(await _key(KEY_ENTER),"王と会話"):return
	castle_check(_snapshot().get("mode")=="dialogue","謁見会話が表示された")
	castle_check(not _state()["progress_flags"].get("job_change_unlocked",false),"会話開始だけでは解放しない")
	await picture("06-royal-audience")
	if not castle_check(await _settle(),"謁見の会話を最後まで送る"):return
	castle_check(_state()["progress_flags"].get("job_change_unlocked",false),"転職と技の装着が解放された")
	castle_check(_state()["progress_flags"].get("castle_north_permission",false),"北の森への許可を記録")
	if not castle_check(await _key(KEY_ESCAPE),"メニューを開く"):return
	if not castle_check(await _button(["じょうたい・そうび・へんせい"]),"編成を開く"):return
	castle_check(_main.submit_player_action({"kind":"choose_job","actor":"pc_01","job":"thief"}),"通常の職業選択で盗賊へ転職")
	await picture("07-job-change")
	if not castle_check(await _button(["戻る"]),"編成から戻る"):return
	# 側近・兵士にも話しかけられる
	for talker in [[[14,6],KEY_UP,"側近"],[[11,12],KEY_LEFT,"兵士(左)"],[[12,12],KEY_RIGHT,"兵士(右)"]]:
		if not castle_check(await _walk(castle_point(2,talker[0])),"人物の前へ歩行: "+talker[2]):return
		await _key(talker[1]);await _key(KEY_ENTER)
		castle_check(_snapshot().get("mode")=="dialogue","話しかけられる: "+talker[2])
		if talker[2]=="兵士(右)":await picture("08-guard-talk")
		await _settle()
	# 謁見の間には出口が下の扉1つだけ：左右の壁へ進めない
	for probe in [[[3,7],KEY_LEFT,"謁見の間の左の壁"],[[20,7],KEY_RIGHT,"謁見の間の右の壁"],[[10,6],KEY_UP,"玉座の壇"]]:
		if not await bump(probe[0],probe[1],probe[2]):return
	# 謁見の間 → 大広間 → 宝物庫 → 大広間 → 書庫 → 大広間 → 中庭
	if not castle_check(await _walk(castle_point(11,[8,3])),"謁見の間の扉から大広間へ戻る"):return
	await picture("09-back-in-great-hall")
	if not castle_check(await _walk(castle_point(3,[8,6])),"奥の左の扉から宝物庫へ入る"):return
	await picture("10-treasury")
	castle_check(_state()["overworld"]["room"]==3,"宝物庫に入った")
	var before_service := _state()
	await _step_direction(Vector2i.UP);await _key(KEY_ENTER);await _settle()
	castle_check(_state()["inventory"]["potion"]==before_service["inventory"]["potion"]+3,"宝物庫の補給を受取")
	if not castle_check(await _walk(castle_point(11,[5,3])),"宝物庫の下の扉から大広間へ戻る"):return
	castle_check(_state()["overworld"]["cell"]==[5,3],"大広間の奥の左の扉の前に着く")
	if not castle_check(await _walk(castle_point(10,[8,8])),"奥の右の扉から書庫へ入る"):return
	await picture("11-library")
	castle_check(_state()["overworld"]["room"]==10,"書庫に入った")
	if not castle_check(await _walk(castle_point(10,[10,8])),"書庫の係の前へ"):return
	await _key(KEY_UP);await _key(KEY_ENTER)
	castle_check(_snapshot().get("mode")=="dialogue","書庫の係に話しかけられる")
	await _settle()
	if not castle_check(await _walk(castle_point(11,[12,3])),"書庫の下の扉から大広間へ戻る"):return
	castle_check(_state()["overworld"]["cell"]==[12,3],"大広間の奥の右の扉の前に着く")
	await picture("12-great-hall-from-library")
	var save_path: String="user://castle_hall_roundtrip_%d.json" % OS.get_process_id()
	castle_check(_session().save_game(save_path),"大広間で保存")
	var loaded := GameSession.new()
	castle_check(loaded.load_game(save_path) and loaded.export_state()==_state(),"場所・向き・転職・進行の保存復元")
	if not castle_check(await _walk(castle_point(1,[16,11])),"大広間の下の扉から中庭へ戻る"):return
	castle_check(_state()["overworld"]["room"]==1 and _state()["overworld"]["cell"]==[16,11],"中庭の扉の前に着く")
	await picture("13-court-again")
	if not castle_check(await _walk(_definition["castle_exit"],_outside(_definition["castle_entrance"])),"城下町から世界マップへ戻る"):return
	castle_check(_outward(_definition["castle_entrance"]),"出口の一歩手前・外向き")
