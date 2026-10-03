extends SceneTree
## 人工状態による境界・保存互換検査と通常UI入力の検査。R-07通し検査の代用ではない。
var checks := 0
var failures: Array[String] = []
var main: Node
var scene_order: Array[String] = []

func check(ok: bool, reason: String) -> void:
	checks += 1
	if not ok:failures.append(reason)

func _initialize() -> void:
	OS.set_environment("RPG_QA_SAVE_PREFIX","intro_"+str(OS.get_process_id()))
	call_deferred("run")

func without_intro(saved: Dictionary) -> Dictionary:
	var value := saved.duplicate(true)
	for flag in FirstRegionStory.FLAGS:value["progress_flags"].erase(flag)
	return value

func fixture(point: Dictionary, boss: bool, four: bool = false) -> Dictionary:
	var game := GameSession.new()
	check(game.new_first_region(),"境界検査用の通常開始")
	var state := game.export_state()
	var waiting: Array=state["first_region"]["reserve"].duplicate(true)
	state["first_region"]["reserve"]=[]
	for actor in waiting:
		if actor["id"]=="pc_04" and not four:state["first_region"]["reserve"].append(actor)
		else:state["party"].append(actor)
	if boss:
		state["inventory"]["gate_pass"]=1
		state["overworld"]["cleared"]=["first_boss"]
	if point["node"] in ["first_forest_tower","first_port","brine_port"]:
		state["progress_flags"]["castle_north_permission"]=true
		state["progress_flags"]["job_change_unlocked"]=true
	if four:
		state["overworld"]["cleared"].append("forest_tower_boss")
		state["progress_flags"]["mountain_path_open"]=true
	FirstRegion.place(state["overworld"],point)
	return state

func finish(game: GameSession, result: Dictionary) -> Dictionary:
	var current := result
	var limit := 0
	while current.has("story_scene") and limit < 6:
		limit+=1
		var id: String=current["story_scene"]
		scene_order.append(id)
		var before := game.export_state()
		var entry := FirstRegionStory.scene(id)
		var baseline := without_intro(before)
		var visual := game.first_region_story_presentation()
		check(visual["actors"].size()==entry["party"].size(),"場面の人数")
		check(not visual["actors"].any(func(actor:Dictionary)->bool:return actor.get("npc")=="pc_04"),"当時の場面へ4人目を加えない")
		check(visual["actors"].all(func(actor:Dictionary)->bool:return (actor["cell"][1]-visual["camera"][1]+1)*32<=165),"人物の足元を会話窓より上に配置")
		var npc_cell := Vector2(WorldExpedition.point(visual["npc_cell"]))
		var npc_rect := Rect2(npc_cell*32+Vector2(0,-16),Vector2(32,48))
		var tool_rect := Rect2(Vector2(WorldExpedition.point(visual["tool_cell"]))*32,Vector2(32,32))
		check(not tool_rect.intersects(npc_rect),"道具が追加人物の絵に重ならない")
		for actor in visual["actors"]:
			var actor_rect := Rect2(Vector2(WorldExpedition.point(actor["cell"]))*32+Vector2(0,-16),Vector2(32,48))
			check(not npc_rect.intersects(actor_rect),"追加人物が仲間の絵に隠れない")
			check(not tool_rect.intersects(actor_rect),"道具が仲間の絵に重ならない")
		if id.begins_with("promise"):check(visual["repair_sound"]==null,"修理を描かない会話では修理音を新しく鳴らさない")
		for page in entry["lines"].size():
			if entry["lines"][page]["action"]=="leave_tool":check(game.first_region_story_presentation()["tool_texture"]==FirstRegionStory.data()["art"]["tool_broken"],"確認操作前に道具の差分を先送りしない")
			check(not game.export_state()["progress_flags"].get(entry["flag"],false),"最終操作より前は未完了")
			current=game.confirm_first_region_story(id,page)
			check(not current.is_empty(),"順序どおりの決定操作を受理")
			if entry["lines"][page]["action"]=="leave_tool":check(game.first_region_story_presentation()["tool_texture"]==FirstRegionStory.data()["art"]["tool_repaired"],"確認操作の後で道具の表示段階を更新")
			check(game.confirm_first_region_story(id,page).is_empty(),"二重決定を拒否")
		check(game.export_state()["progress_flags"].get(entry["flag"],false),"最終操作で完了")
		if current.get("kind")!="moved":check(without_intro(game.export_state())==baseline,"会話で能力・編成・所持品・位置を変えない")
	check(limit<6,"場面が無限に繰り返されない")
	return current

func run() -> void:
	var game := GameSession.new()
	check(game.new_first_region(),"新規開始")
	var initial := game.export_state()
	var result := game.interact_first_region()
	check(result.get("story_scene")=="workshop" and game.export_state()==initial,"最初の会話で過去の場面を開始・保存位置は不変")
	check(game.confirm_first_region_story("workshop",1).is_empty(),"ページを飛ばして確定できない")
	check(game.confirm_first_region_story("encounter",0).is_empty(),"別の場面IDを拒否")
	check(game.move_first_region(Vector2i(6,8)).is_empty(),"場面中の移動を拒否")
	var save_path := "user://intro_boundary_%d.json" % OS.get_process_id()
	check(game.save_game(save_path),"会話前相当の状態を実ファイルへ保存")
	check(game.confirm_first_region_story("workshop",0).get("kind")=="story_page","1ページ目の通常決定")
	check(game.save_game(save_path),"会話途中の実保存")
	var loaded := GameSession.new()
	check(loaded.load_game(save_path) and loaded.export_state()==initial,"中断した場面は未完了のまま復元")
	scene_order.clear()
	finish(loaded,loaded.interact_first_region())
	check(scene_order==["workshop"],"中断した過去場面を最初から再試行")
	check(loaded.save_game(save_path) and game.load_game(save_path) and game.export_state()==loaded.export_state(),"完了後の実保存を完全復元")
	var prior := fixture({"layer":"interior","node":"first_cave","room":1,"cell":[30,15]},false)
	prior["overworld"]["facing"]=3
	check(game.import_state(prior),"未見の洞窟前状態")
	scene_order.clear()
	finish(game,game.interact_first_region())
	check(scene_order==["workshop","encounter"],"過去から初会話の順序")
	check(not game.export_state()["progress_flags"].get("gado_promise_seen",false),"撃破前に撃破後の場面を出さない")
	var unchanged := game.export_state()
	check(game.interact_first_region().get("kind")=="dialogue" and game.export_state()==unchanged,"再訪の通常会話は一度きりのフラグを再確定しない")
	var return_point := {"layer":"interior","node":"first_cave","room":1,"cell":[17,21]}
	check(game.import_state(fixture(return_point,false)),"途中で引き返す状態")
	check(game.move_first_region(Vector2i(17,22)).get("kind")=="moved" and game.overworld_state()["room"]==0,"未撃破の階段帰路を妨げない")
	check(game.import_state(fixture(return_point,true)),"主経路を急いだ撃破後の状態")
	result=game.move_first_region(Vector2i(17,22))
	check(result.has("story_scene") and game.overworld_state()["room"]==1 and game.overworld_state()["cell"]==[17,22],"帰路で会話し移動先は保留")
	check(game.save_game(save_path),"保留階段の実保存")
	check(loaded.load_game(save_path),"保留階段の保存を通常ロード")
	scene_order.clear()
	finish(loaded,loaded.interact_first_region())
	check(scene_order==["workshop","encounter_after","promise_after"],"未見撃破は初対面を先に時制を調整")
	check(loaded.overworld_state()["room"]==0 and loaded.overworld_state()["cell"]==[17,6],"最後の操作だけで元の階段移動を完了")
	var finished := loaded.export_state()
	check(loaded.confirm_first_region_story("promise_after",9).is_empty() and loaded.export_state()==finished,"二重決定で移動・報酬を重複しない")
	var seen := fixture(return_point,true)
	seen["progress_flags"]["gado_workshop_seen"]=true
	seen["progress_flags"]["gado_encounter_seen"]=true
	check(game.import_state(seen),"初会話済みの帰路")
	scene_order.clear()
	finish(game,game.move_first_region(Vector2i(17,22)))
	check(scene_order==["promise"],"既読の場面を飛ばして再会へ")
	var places: Array=[FirstRegion.data()["start"],FirstRegion.data()["cave_spawn"],return_point,FirstRegion.data()["gate"]["beyond"],FirstRegion.data()["castle_spawn"],FirstRegion.data()["tower_spawn"],FirstRegion.data()["port_spawn"],FirstRegion.data()["second_port_spawn"]]
	for index in places.size():
		var state := fixture(places[index],index>=2,index>=6)
		check(game.import_state(state),"新フラグのない旧保存の位置・編成を保持")
		check(game.save_game(save_path) and loaded.load_game(save_path) and loaded.export_state()==state,"旧保存の実ファイル往復一致")
		check(not loaded.export_state()["progress_flags"].get("gado_promise_seen",false),"旧保存の欠損を既読補完しない")
		check(loaded.require_first_region_intro().get("kind")=="intro_required" and not loaded.require_first_region_intro().has("text"),"後続APIは本文より先に導入を要求")
		if loaded.first_region_intro_available():
			var baseline := without_intro(loaded.export_state())
			scene_order.clear()
			finish(loaded,loaded.begin_first_region_intro())
			check(scene_order==["workshop","encounter_after","promise_after"],"旧保存補完でも3場面を実再生")
			check(without_intro(loaded.export_state())==baseline,"補完で現在地・現在の仲間・所持品は不変")
			check(loaded.require_first_region_intro().get("kind")=="ready","完了後だけ後続APIが許可")
			check(not loaded.first_region_intro_available(),"完了後に補完の二重開始を拒否")
	# 3個の真偽値すべての組合せで、未完了だけを順序どおり補完する。
	for mask in range(8):
		var partial := fixture(FirstRegion.data()["second_port_spawn"],true,true)
		var expected: Array[String]=[]
		for index in FirstRegionStory.FLAGS.size():
			partial["progress_flags"][FirstRegionStory.FLAGS[index]]=(mask & (1<<index))!=0
		if (mask & 1)==0:expected.append("workshop")
		if (mask & 2)==0:expected.append("encounter_after")
		if (mask & 4)==0:expected.append("promise" if (mask & 2)!=0 else "promise_after")
		check(game.import_state(partial),"部分完了フラグを持つ保存を受理")
		check(game.save_game(save_path) and loaded.load_game(save_path) and loaded.export_state()==partial,"部分完了の真偽値を推測せず実保存往復")
		check(loaded.first_region_intro_available()==(mask!=7),"3場面すべてが既読のときだけ補完不要")
		check((loaded.require_first_region_intro().get("kind")=="ready")== (mask==7),"未見があれば後続APIを許可しない")
		if mask!=7:
			scene_order.clear()
			finish(loaded,loaded.begin_first_region_intro())
			check(scene_order==expected,"未見の場面だけ順序どおりに補完")
			check(loaded.require_first_region_intro().get("kind")=="ready" and without_intro(loaded.export_state())==without_intro(partial),"補完後も既存の位置・編成・所持品を保持")
	# 導入フラグが通行証の代わりにならず、通行証の既存条件も妨げない。
	for intro_seen in [false,true]:
		for has_pass in [false,true]:
			var gate_state := fixture(FirstRegion.data()["gate"]["beyond"],has_pass)
			for flag in FirstRegionStory.FLAGS:gate_state["progress_flags"][flag]=intro_seen
			check(FirstRegion.walkable(gate_state,WorldExpedition.point(FirstRegion.data()["gate"]["cell"]["cell"]))==has_pass,"関所の通行証条件は導入の既読から独立")
	# 新しい人物のセルに立つ旧保存を、実ロードの置き直し入口へ渡す。
	check(game.import_state(prior) and game.save_game(save_path),"重なり検査用の旧保存")
	var raw: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(save_path))
	raw["overworld"]["cell"]=[30,14]
	check(PlaySessionMetrics.write_json(save_path,raw),"人物追加前の保存位置を再現")
	check(loaded.load_game(save_path) and loaded.position_relocated,"重なる旧保存を入口へ置き直し通知")
	check(loaded.overworld_state()["cell"]==FirstRegion.entrance_landing("first_cave",1),"既存の入口へ置き直す")
	for count in [3,4]:
		check(game.new_game(count) and not game.first_region_active(),"旧本編の開始人数・経路を維持")
		check(game.begin_first_region_intro().is_empty() and game.first_region_story_presentation().is_empty(),"旧本編へ導入を挿入しない")
	await ui_checks()
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"pending_art":FirstRegionStory.missing_art(),"native_render":DisplayServer.get_name()!="headless","scope":"状態・保存互換の人工境界入力と通常UIの操作。R-07と実素材の検証は別。"}
	PlaySessionMetrics.write_json("res://docs/verification/first-region-intro/runtime-checks.json",report)
	for failure in failures:printerr("INTRO_RUNTIME_FAIL: "+failure)
	print("INTRO_RUNTIME_PASS: checks=%d pending_art=%d" % [checks,FirstRegionStory.missing_art().size()] if failures.is_empty() else "INTRO_RUNTIME_FAIL")
	quit(0 if failures.is_empty() else 1)

func key(code: int) -> void:
	var event := InputEventKey.new()
	event.keycode=code;event.physical_keycode=code;event.pressed=true
	main.get_viewport().push_input(event,true)
	event=event.duplicate();event.pressed=false;main.get_viewport().push_input(event,true)
	await process_frame
	await process_frame

func check_dialogue_layout() -> void:
	var screen: FirstRegionScreen=main.get("_region_screen")
	for label in screen.find_children("*","Label",true,false):
		check(main.get_viewport_rect().encloses(label.get_global_rect()),"場面の文字が画面内に収まる")
		var font: Font=label.get_theme_font("font")
		check(label.get_line_count()*font.get_height(label.get_theme_font_size("font_size"))<=label.size.y+1.0,"表示された行が文字領域に収まる")

func capture_layout(name: String) -> void:
	if "--capture-layout" not in OS.get_cmdline_user_args():return
	if DisplayServer.get_name()=="headless":check(false,"確認画像には実レンダラーが必要");return
	await RenderingServer.frame_post_draw
	var image := main.get_viewport().get_texture().get_image()
	check(image.get_size()==Vector2i(512,288),"確認画像は内部解像度512×288")
	check(image.save_png("res://docs/verification/first-region-intro/"+name+"-layout.png")==OK,"登録素材を組み込んだ確認画像を保存")

func ui_checks() -> void:
	main=load(str(ProjectSettings.get_setting("application/run/main_scene"))).instantiate()
	root.add_child(main)
	await process_frame
	await process_frame
	main.start_new_game(4,true)
	await process_frame
	var baseline: Dictionary=main.game.export_state()
	await key(KEY_ENTER)
	check(main.get("_region_story_id")=="workshop" and main.automation_snapshot()["mode"]=="dialogue","通常の決定キーから導入へ")
	var screen: FirstRegionScreen=main.get("_region_screen")
	check(screen.story_view["title"].begins_with("以前、") and screen.story_view["actors"].size()==1,"過去表示と当時の配置")
	check_dialogue_layout()
	var audio: RpgAudio=main.get("_rpg_audio")
	var player: AudioStreamPlayer=audio.get("_scene_effect")
	check(player.stream.resource_path=="res://assets/audio/se/gado_repair.wav" and player.playing,"通常会話開始から修理音の再生器へ接続")
	check(player.volume_db==-8.0 and player.max_polyphony==1,"修理音のゲーム内音量と同時数")
	check(is_equal_approx(player.stream.get_length(),0.48) and (player.stream as AudioStreamWAV).loop_mode==AudioStreamWAV.LOOP_DISABLED,"原音の長さを保持してループしない")
	var stream: AudioStream=player.stream
	for attempt in range(20):check(not audio.effect_path("assets/audio/se/gado_repair.wav"),"連打で再生中の修理音を重ねたり再開しない")
	for attempt in range(12):audio.effect("confirm")
	check(player.stream==stream and player.playing,"決定音の連打で修理音を上書きしない")
	check(audio.snapshot()["scene_effect_players"]==1,"修理音の再生器を増殖させない")
	var echo := InputEventKey.new()
	echo.keycode=KEY_ENTER;echo.physical_keycode=KEY_ENTER;echo.pressed=true;echo.echo=true
	main.get_viewport().push_input(echo,true)
	await process_frame
	check(main.get("_message_index")==0 and main.game.export_state()==baseline,"長押しの反復入力で場面を自動送りしない")
	await capture_layout("past")
	for page in FirstRegionStory.scene("workshop")["lines"].size():
		if page==4:await capture_layout("past-repaired")
		await key(KEY_ENTER)
	check(main.automation_snapshot()["mode"]=="world" and without_intro(main.game.export_state())==without_intro(baseline),"空き場所で始めた会話も最終キーで探索へ戻る")
	var state := fixture(FirstRegion.data()["second_port_spawn"],true,true)
	check(main.game.import_state(state),"進行済みの旧保存UI入力")
	main._refresh()
	await process_frame
	await key(KEY_ESCAPE)
	var clicked := false
	for button in main.find_children("*","Button",true,false):
		if button.text=="追加された導入を見る" and button.is_visible_in_tree() and not button.disabled:
			check(main.get_viewport_rect().encloses(button.get_global_rect()),"補完入口のボタンが画面内に収まる")
			var event := InputEventMouseButton.new()
			event.button_index=MOUSE_BUTTON_LEFT;event.button_mask=MOUSE_BUTTON_MASK_LEFT;event.position=button.get_global_rect().get_center();event.pressed=true
			main.get_viewport().push_input(event,true)
			event=event.duplicate();event.pressed=false;event.button_mask=0;main.get_viewport().push_input(event,true)
			clicked=true;break
	await process_frame
	await process_frame
	check(clicked and main.get("_region_story_id")=="workshop","安全な画面の明示入口をクリックして再生")
	var inputs := 0
	while main.automation_snapshot()["mode"]=="dialogue" and inputs<100:
		check_dialogue_layout()
		if main.get("_region_story_id")=="encounter_after" and main.get("_message_index")==0:await capture_layout("cave")
		if main.get("_region_story_id")=="encounter_after" and main.get("_message_index")==7:await capture_layout("cave-repaired")
		await key(KEY_ENTER)
		inputs+=1
	check(inputs<100 and main.automation_snapshot()["mode"]=="world","連続決定で補完から通常探索へ戻る")
	check(without_intro(main.game.export_state())==without_intro(state),"4人の旧保存も位置・編成・所持品を保持")
	check(main.game.require_first_region_intro().get("kind")=="ready","補完の最終入力でだけ後続条件を満たす")
	main.queue_free()
	await process_frame
