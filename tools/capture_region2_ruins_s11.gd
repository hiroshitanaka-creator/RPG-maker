extends "res://tools/check_region2_ruins_s11.gd"
## 実到達した戦力を保持する段階配置の本番UI試験。全行程の人間初見とは区別。
var main: Node
var trace: Array=[]
var images: Array=[]

func _initialize() -> void:
	OS.set_environment("RPG_QA_SAVE_PREFIX","task085-capture")
	call_deferred("capture_run")

func frames(count: int=3) -> void:
	for i in range(count):await process_frame

func key(code: int, echo: bool=false) -> void:
	trace.append({"key":code,"echo":echo,"mode":main.mode,"cell":main.game.overworld_state()["cell"],"page":main._message_index})
	var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=true;event.echo=echo
	root.push_input(event,true)
	event=event.duplicate();event.pressed=false;root.push_input(event,true)
	await frames()

func picture(name: String) -> void:
	await frames();await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var frame:=root.get_texture().get_image()
	check(frame.get_size()==Vector2i(1024,576) and frame.save_png(OUT+name+".png")==OK,"実Godotの画面保存",name)
	images.append(name+".png")

func staged(saved: Dictionary) -> void:
	main._to_menu();await frames()
	check(main.game.import_state(saved),"実到達戦力を保持した段階保存の受理")
	main.mode=main.Mode.WORLD;main._refresh();await frames()

func walk(cell: Array) -> bool:
	var path:=path_to(main.game.export_state(),WorldExpedition.point(cell))
	if not check(not path.is_empty() or main.game.overworld_state()["cell"]==cell,"本番キーの歩行経路",cell):return false
	for next in path:
		var current:=WorldExpedition.point(main.game.overworld_state()["cell"])
		var delta:=next-current
		await key([KEY_DOWN,KEY_LEFT,KEY_RIGHT,KEY_UP][DIRS.find(delta)])
		var deadline:=Time.get_ticks_msec()+2000
		while main._world_mover.active() and Time.get_ticks_msec()<deadline:await process_frame
		check(not main._world_mover.active(),"本番1歩が制限内に終了")
		await create_timer(0.16).timeout
		if main.mode==main.Mode.DIALOGUE or main.mode==main.Mode.BATTLE:return true
	return true

func ui_fight(policy: String="standard") -> void:
	for turn in range(100):
		if main.mode!=main.Mode.BATTLE:break
		var battle: BattleState=main.game.current_battle()
		for action in combat_actions(battle,policy):
			var command: Dictionary={"kind":{BattleAction.Kind.ATTACK:"attack",BattleAction.Kind.GUARD:"guard",BattleAction.Kind.ABILITY:"ability",BattleAction.Kind.ITEM:"potion"}[action.kind],"actor":action.actor_id,"target":action.target_id,"ability":action.ability_id}
			trace.append({"battle_action":command,"round":battle.round_number})
			check(main.submit_player_action(command),"本番UIの通常戦闘入力",command)
		check(main.submit_player_action({"kind":"resolve_round"}),"本番UIでターン実行")
		await frames();await key(KEY_ENTER)
		await frames()
	for i in range(40):
		if main.mode!=main.Mode.DIALOGUE:break
		await key(KEY_ENTER)
	check(main.mode in [main.Mode.WORLD,main.Mode.DEFEAT],"戦闘表示を通常決定で終了")

func capture_run() -> void:
	check(DisplayServer.get_name()!="headless","実レンダラー必須")
	root.size=Vector2i(1024,576);DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var scene: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	main=scene.instantiate();root.add_child(main);await frames()
	var arrival: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string(OUT+"real-arrival-state.json")))
	check(not arrival.is_empty(),"通常新規からの実到達保存を使用")
	FirstRegion.place(arrival["overworld"],point("region2_ruins",3,[18,16]))
	await staged(arrival)
	check(main.game.save_game(main.save_path),"未読直前を本番手動保存")
	await walk([18,15])
	check(main.mode==main.Mode.DIALOGUE and main._message_index==0,"通常一歩で採用場面が冒頭から自動開始")
	await picture("01-record-start")
	var before: Dictionary=main.game.export_state()
	main._refresh();main._refresh();await frames()
	check(main.game.export_state()==before and main._message_index==0,"描画では状態を変えない")
	await key(KEY_ENTER,true)
	check(main._message_index==0,"キーechoでページ送りなし")
	main._region_ui_action({"kind":"ui_items"});main._region_ui_action({"kind":"ui_resume"})
	check(main.mode==main.Mode.DIALOGUE and main._message_index==0,"古いメニュー/復帰通知で会話を破棄しない")
	check(not main.submit_player_action({"kind":"confirm","ruins_scene":Region2RuinsStory.SCENE,"ruins_run":-1,"ruins_page":0}),"古いボタンの実行番号を拒否")
	for i in range(4):await key(KEY_ENTER)
	main._region_ui_action({"kind":"ui_title"});await frames()
	main._region_ui_action({"kind":"ui_load"});await frames()
	check(main.mode==main.Mode.WORLD and not main.game.export_state()["progress_flags"].get(Region2RuinsStory.COMPLETE_FLAG,false),"中断後は最後の有効保存位置、未読を維持")
	await walk([18,15])
	check(main.mode==main.Mode.DIALOGUE and main._message_index==0,"再到達で冒頭から")
	for page in range(22):
		check(main.mode==main.Mode.DIALOGUE and main._message_index==page,"実キーのページ順序",page)
		if page==6:await picture("02-record-page")
		await key(KEY_ENTER)
	check(main.mode==main.Mode.WORLD and main.game.current_battle()==null,"最終決定後に自由行動、強制戦闘なし")
	await picture("03-free-pause")
	await key(KEY_ESCAPE)
	check(main.mode==main.Mode.REGION_COMMANDS,"記録後のメニュー利用")
	main._region_ui_action({"kind":"save"});await frames()
	var read_state: Dictionary=main.game.export_state()
	main._region_ui_action({"kind":"ui_title"});await frames()
	main._region_ui_action({"kind":"ui_load"});await frames()
	check(main.mode==main.Mode.WORLD and main.game.export_state()==read_state,"読了後の実保存/タイトル/ロード、再演なし")
	await walk([31,13])
	# 向きを変える通常キーは1歩移動する。ボスの直下から上のセルへ進んでも自動戦闘しない。
	await key(KEY_UP);await create_timer(0.2).timeout;await frames()
	check(main.mode==main.Mode.WORLD,"ボス位置への歩行だけでは戦闘しない")
	await key(KEY_ENTER)
	check(main.mode==main.Mode.BATTLE and main.game.current_encounter_id()==Region2RuinsStory.BOSS,"通常決定による明示挑戦")
	await picture("04-boss-intents")
	var checkpoint:=GameSession.new()
	check(checkpoint.load_game(main.checkpoint_path) and checkpoint.export_state()["progress_flags"].get("region2_ruins_record_seen",false),"本番checkpointは読了済みを保持")
	await ui_fight()
	check(Region2RuinsStory.BOSS in main.game.overworld_state()["cleared"] and main.game.export_state()["inventory"].get(Region2RuinsStory.KEY,0)==0,"本番UI実勝利、鍵は未受取")
	await picture("05-after-victory")
	await walk([31,9]);await key(KEY_UP);await create_timer(0.2).timeout;await key(KEY_ENTER)
	check(main.game.export_state()["inventory"].get(Region2RuinsStory.KEY,0)==1,"勝利後の別調査で鍵取得")
	await picture("06-box-received")
	for i in range(8):
		if main.mode!=main.Mode.DIALOGUE:break
		await key(KEY_ENTER)
	await key(KEY_ESCAPE)
	check(main.mode==main.Mode.REGION_COMMANDS,"受取後に通常メニューへ戻る")
	main._region_ui_action({"kind":"save"});await frames()
	var received: Dictionary=main.game.export_state()
	main._region_ui_action({"kind":"ui_title"});await frames();main._region_ui_action({"kind":"ui_load"});await frames()
	check(main.game.export_state()==received,"受取済み保存を実UIから再開")
	await picture("07-reloaded-box")
	# 敗北・再挑戦と再起動時checkpointを同じ実到達戦力で独立測定。
	var old: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string(OUT+"real-before-boss-state.json")))
	await staged(old);await key(KEY_ENTER)
	check(main.mode==main.Mode.BATTLE,"再挑戦測定の通常調査")
	await ui_fight("lose")
	check(main.mode==main.Mode.DEFEAT and Region2RuinsStory.BOSS not in main.game.overworld_state()["cleared"],"本番UIで実敗北、報酬なし")
	await picture("08-defeat")
	check(main.submit_player_action({"kind":"retry_battle"}),"本番checkpointから再挑戦前へ")
	check(main.mode==main.Mode.WORLD and main.game.export_state()==old,"全保存値が戦闘前と一致")
	await key(KEY_ENTER)
	check(main.mode==main.Mode.BATTLE and main._notice.is_empty(),"復帰後の通常再操作で再挑戦、古い復帰通知を消す")
	await ui_fight()
	check(main.mode==main.Mode.WORLD and Region2RuinsStory.BOSS in main.game.overworld_state()["cleared"] and main.game.export_state()["inventory"].get(Region2RuinsStory.KEY,0)==0,"実敗北後の再挑戦・実勝利、箱は別操作のまま")
	await picture("09-retry-victory")
	var failed:=checks.filter(func(c:Dictionary)->bool:return not c["ok"])
	PlaySessionMetrics.write_json(OUT+"capture-checks.json",{"status":"PASS" if failed.is_empty() else "FAIL","checks":checks,"images":images,"input_trace":trace,"renderer":DisplayServer.get_name(),"staged":true,"strategy":"公開予告を用いた通常UIコマンド。戦力は実到達保存。人間初見ではない。"})
	print("S11_CAPTURE_%s: checks=%d images=%d"%["PASS" if failed.is_empty() else "FAIL",checks.size(),images.size()])
	main.queue_free();await frames();quit(0 if failed.is_empty() else 1)
