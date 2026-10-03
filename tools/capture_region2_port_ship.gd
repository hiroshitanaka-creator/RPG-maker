extends "res://tools/capture_region2_port_backdrop.gd"
## 第2港の船：背景には船を描かず、第1地方と同じ動く船の絵を桟橋のそばに重ねる。
## 船取得後の未編集保存から通常入力で、(1)船が桟橋に着いている画面 (2)出航した直後 (4)帰還の風で港に戻り桟橋まで歩いた画面を撮る。
## (3)出航後の桟橋（船がない）は、町の外から徒歩で入る通常経路が船を港へ置いてしまうため、到達後の状態の読み取り専用コピーを
## 本番のFirstRegionViewで描いた画像であり、通常操作の撮影とは区別して記録する。
const SHIP_OUTPUT := "res://docs/verification/region2-port-backdrop/ship/"

func pier_without_ship(name: String) -> void:
	var saved := _state().duplicate(true)
	var dock: Dictionary=Region2Port.data()["docks"][0]
	FirstRegion.place(saved["overworld"],dock["land"])
	saved["overworld"]["transport"]="walk"
	saved["overworld"]["facing"]=2
	saved["first_region"]["travel"]["ship_cell"]=[155,111]
	var viewport := SubViewport.new();viewport.size=Vector2i(512,288);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var view := FirstRegionView.new();view.saved=saved;view.size=Vector2(512,288)
	viewport.add_child(view)
	await _frames(6);await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	image.resize(1024,576,Image.INTERPOLATE_NEAREST)
	castle_check(image.save_png(OUTPUT+name+".png")==OK,"読み取り専用コピーの保存: "+name)
	castle_images.append(name+".png")
	scenic.append({"image":name+".png","cell":saved["overworld"]["cell"],"expect":"readonly-copy-ship-away","note":"船が出航して不在のときの桟橋。到達後の状態の読み取り専用コピーを本番のFirstRegionViewで描いた画像"})
	viewport.queue_free();await _frames()

func visit_port() -> void:
	OUTPUT=SHIP_OUTPUT
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	castle_check(_state()["overworld"]["transport"]=="ship" and FirstRegionTravel.snapshot(_state()).get("ship_owned",false),"船取得後の未編集保存から開始")
	var dock: Dictionary=Region2Port.data()["docks"][0]
	if not castle_check(await _walk(_world_point(dock["ship_cell"])),"第1港から第2港へ通常航行"):return
	await _key(KEY_ENTER);await _settle()
	if not castle_check(FirstRegion.at(_state()["overworld"],dock["land"]) and _state()["overworld"]["transport"]=="walk","中央桟橋へ通常下船"):return
	await shot("01-ship-at-pier-before-sailing","front")
	await _key(KEY_ENTER);await _settle()
	if not castle_check(_state()["overworld"]["transport"]=="ship","桟橋で通常操作により乗船して出航"):return
	await shot("02-just-after-sailing-out","ship")
	await pier_without_ship("03-pier-without-ship-readonly-copy")
	if not castle_check(await _walk(_world_point([155,111])),"第2港の沖へ"):return
	var before_return := _state();var actor: Dictionary=before_return["party"].filter(func(a:Dictionary)->bool:return a["hp"]>0 and a["mp"]>=2)[0]
	if not castle_check(await _key(KEY_ESCAPE) and await _button(["帰還の風"]) and await _button(["%s MP %d" % [actor["name"],actor["mp"]]]),"帰還の風と使う仲間を選ぶ"):return
	if not castle_check(await _button(["第2地方の港町（仮）"]),"訪問済みの第2港を選ぶ"):return
	castle_check(FirstRegionTravel.snapshot(_state())["ship_cell"]==dock["ship_cell"],"帰還で船が港へ戻る")
	if not castle_check(await _walk(_world_point(_definition["second_port_entrance"]["cell"]),_definition["second_port_spawn"]),"沿岸から石アーチへ通常入場"):return
	if not castle_check(await _walk(dock["land"]),"中央桟橋へ歩く"):return
	await shot("04-returned-ship-at-pier","front")
	castle_check(not new_port_battle,"町は非戦闘")

func finish_port() -> void:
	castle_check(Time.get_ticks_msec()-port_started_at<LIMIT_MS,"180秒以内")
	castle_check(_moves<=LIMIT_MOVES and _input_log.size()<LIMIT_INPUTS and not _input_violation,"既存の移動・入力上限と禁止操作を維持")
	PlaySessionMetrics.write_json(SHIP_OUTPUT+"checks.json",{"status":"PASS" if castle_failures.is_empty() else "FAIL","checks":castle_checks,"failures":castle_failures,"images":castle_images,"scenic":scenic,"moves":_moves,"inputs":_input_log.size(),"source_sha256":source_hash,"elapsed_ms":Time.get_ticks_msec()-port_started_at,"method":"船取得後の無編集保存をタイトルから再開し、通常入力で航行・下船・乗船・帰還の風・徒歩。03は読み取り専用コピーの描画。"})
	for failure in castle_failures:printerr("REGION2_SHIP_RUNTIME_FAIL: "+failure)
	print("REGION2_SHIP_RUNTIME_PASS: checks=%d images=%d" % [castle_checks,castle_images.size()] if castle_failures.is_empty() else "REGION2_SHIP_RUNTIME_FAIL")
	_finished=true
	quit(0 if castle_failures.is_empty() else 1)
