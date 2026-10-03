extends "res://tools/capture_region2_port.gd"
## 一枚絵の港町：主人公が建物の奥・ヤシの木の後ろ・露店の日よけの奥・アーチの下を歩く画面と、
## 手前を歩く画面、桟橋で船に乗る画面を、船取得後の未編集保存から通常入力だけで撮る。
## 人物の画素が画面にどれだけ見えているか（奥では一部が隠れ、手前では全て見える）も数える。
const BACKDROP_OUTPUT := "res://docs/verification/region2-port-backdrop/runtime/"
## [画像名, 目標のマス, 期待：behind＝奥にいて一部が隠れる / front＝手前にいて全て見える / any・ship＝記録だけ]
const SHOTS := [
	["01-front-of-palm-trunk",[19,6],"front"],
	["02-behind-palm-crown",[19,4],"behind"],
	["03-behind-stall-awning",[13,8],"behind"],
	["04-front-of-stall",[14,14],"front"],
	["05-under-stone-arch",[4,2],"any"],
	["06-behind-building-roof-home-b",[12,15],"behind"],
	["07-front-of-building-door-home-b",[13,20],"front"],
	["08-pier-before-boarding",[34,21],"front"],
]
var scenic: Array = []

func shot(name: String, expectation: String) -> void:
	await create_timer(2.5).timeout   # 場所名の表示が消えるのを通常どおり待つ
	await _frames(3);await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := _main.get_viewport().get_texture().get_image()
	var panel: FirstRegionScreen=_main.get("_region_screen")
	var view := panel.map_view
	var saved := _state()
	var member: Dictionary=saved["party"].filter(func(a:Dictionary)->bool:return a["id"]==saved.get("leader_id","pc_01"))[0]
	var appearance := CharacterVisuals.appearance(member,"walk",view.walk_frame,int(saved["overworld"]["facing"]))
	var sprite := (load(appearance["path"]) as Texture2D).get_image().get_region(Rect2i(appearance["region"]))
	var origin := WorldExpedition.point(view._map.get("origin",[0,0]))
	var pos := view._screen(Vector2(WorldExpedition.point(saved["overworld"]["cell"])-origin)+view.movement_offset)+Vector2(0,-16)
	var opaque := 0;var matched := 0;var head_opaque := 0;var head_matched := 0
	for y in range(48):
		for x in range(32):
			var color := sprite.get_pixel(x,y)
			if color.a<1.0:continue
			opaque+=1
			if y<24:head_opaque+=1
			var sample := Vector2i((pos+Vector2(x,y))*2)+Vector2i.ONE
			if sample.x>=0 and sample.y>=0 and sample.x<image.get_width() and sample.y<image.get_height() and image.get_pixelv(sample).is_equal_approx(color):
				matched+=1
				if y<24:head_matched+=1
	var ratio := float(matched)/maxf(opaque,1)
	if expectation=="front":castle_check(opaque>0 and matched==opaque,"手前にいる主人公の画素が全て見える: "+name)
	elif expectation=="behind":castle_check(opaque>0 and matched<opaque,"奥にいる主人公は上の層に一部が隠れる: "+name)
	castle_check(image.save_png(OUTPUT+name+".png")==OK,"実画面保存: "+name)
	castle_images.append(name+".png")
	scenic.append({"image":name+".png","cell":saved["overworld"]["cell"],"expect":expectation,"opaque":opaque,"visible":matched,"head_opaque":head_opaque,"head_visible":head_matched,"visible_ratio":snappedf(ratio,0.001)})

func full_town_exact() -> void:
	# 町の全体（1440×960px）を、本番のFirstRegionViewで1:1に描く。到達後の状態の読み取り専用コピー。通常のゲーム窓とは別の全体図。
	var viewport := SubViewport.new();viewport.size=Vector2i(1440,960);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var view := FirstRegionView.new();view.saved=_state().duplicate(true);view.size=Vector2(1440,960)
	viewport.add_child(view)
	await _frames(6);await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	castle_check(image.get_size()==Vector2i(1440,960) and image.save_png(OUTPUT+"00-full-town.png")==OK,"本番描画クラスによる町全体（1440×960）の保存")
	castle_images.append("00-full-town.png")
	viewport.queue_free();await _frames()

func visit_port() -> void:
	OUTPUT=BACKDROP_OUTPUT
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	castle_check(_state()["overworld"]["transport"]=="ship" and FirstRegionTravel.snapshot(_state()).get("ship_owned",false),"船取得後の未編集保存から開始")
	var dock: Dictionary=Region2Port.data()["docks"][0]
	if not castle_check(await _walk(_world_point(dock["ship_cell"])),"第1港から第2港へ通常航行"):return
	await _key(KEY_ENTER);await _settle()
	if not castle_check(FirstRegion.at(_state()["overworld"],dock["land"]) and _state()["overworld"]["transport"]=="walk","中央桟橋へ通常下船"):return
	await full_town_exact()
	for entry in SHOTS:
		if not castle_check(await _walk(p(0,entry[1])),"歩いて到達: "+entry[0]):return
		await shot(entry[0],entry[2])
	await _key(KEY_ENTER);await _settle()
	castle_check(_state()["overworld"]["transport"]=="ship","桟橋で通常操作により乗船")
	await shot("09-after-boarding","ship")
	castle_check(not new_port_battle,"町は非戦闘")

func finish_port() -> void:
	castle_check(Time.get_ticks_msec()-port_started_at<LIMIT_MS,"180秒以内")
	castle_check(_moves<=LIMIT_MOVES and _input_log.size()<LIMIT_INPUTS and not _input_violation,"既存の移動・入力上限と禁止操作を維持")
	PlaySessionMetrics.write_json(BACKDROP_OUTPUT+"checks.json",{"status":"PASS" if castle_failures.is_empty() else "FAIL","checks":castle_checks,"failures":castle_failures,"images":castle_images,"scenic":scenic,"moves":_moves,"inputs":_input_log.size(),"source_sha256":source_hash,"elapsed_ms":Time.get_ticks_msec()-port_started_at,"method":"船取得後の無編集保存をタイトルから再開し、通常入力で第2港へ航行・下船・徒歩。奥で隠れ手前で見える人物画素を実画面で数える。"})
	for failure in castle_failures:printerr("REGION2_BACKDROP_RUNTIME_FAIL: "+failure)
	print("REGION2_BACKDROP_RUNTIME_PASS: checks=%d images=%d" % [castle_checks,castle_images.size()] if castle_failures.is_empty() else "REGION2_BACKDROP_RUNTIME_FAIL")
	_finished=true
	quit(0 if castle_failures.is_empty() else 1)
