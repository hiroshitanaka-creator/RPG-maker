extends SceneTree
## 共通転職APIと本番描画を確認する。物語の転職解放フラグは変更しない。
const JOBS := ["warrior","martial_artist","priest","mage"]
var failures: Array[String] = []
var lookups := 0
var roundtrips := 0
var capture_enabled := false

class WalkBoard extends Control:
	var party: Array = []
	var textures: Dictionary = {}
	func texture(path: String) -> Texture2D:
		if not textures.has(path):textures[path]=load(path)
		return textures[path]
	func _draw() -> void:
		draw_texture_rect(texture("res://assets/tiles/natural_grass.png"),Rect2(0,0,512,288),true)
		for i in range(party.size()):
			for facing in range(4):
				var visual := CharacterVisuals.appearance(party[i],"walk",1,facing)
				var origin := Vector2(i*128+24+(facing%2)*52,62+floori(facing/2.0)*86)
				draw_texture_rect_region(texture(visual["path"]),Rect2(origin,Vector2(32,48)),visual["region"])

func check(ok: bool,reason: String) -> void:
	if not ok:failures.append(reason)

func _initialize() -> void:
	capture_enabled="--capture" in OS.get_cmdline_user_args()
	if capture_enabled and DisplayServer.get_name()=="headless":printerr("COSTUME_CAPTURE_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.size=Vector2i(1024,576)
	call_deferred("run")

func label(parent: Control,text_value: String,position: Vector2) -> void:
	var text_label := Label.new()
	text_label.text=text_value;text_label.position=position
	var font := SystemFont.new();font.font_names=PackedStringArray(["Yu Gothic UI","Meiryo","Noto Sans CJK JP","sans-serif"])
	text_label.add_theme_font_override("font",font);text_label.add_theme_font_size_override("font_size",12)
	text_label.add_theme_color_override("font_color",Color.WHITE)
	text_label.add_theme_color_override("font_shadow_color",Color.BLACK)
	text_label.add_theme_constant_override("shadow_offset_x",1);text_label.add_theme_constant_override("shadow_offset_y",1)
	parent.add_child(text_label)

func capture(game: GameSession,job: String) -> void:
	if not capture_enabled:return
	var board := WalkBoard.new();board.party=game.export_state()["party"];board.size=Vector2(512,288);board.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;root.add_child(board)
	label(board,"衣装表示見本："+str(game.jobs[job]["name"])+"（共通の転職処理で変更）",Vector2(8,6))
	for i in range(board.party.size()):label(board,str(board.party[i]["name"]),Vector2(i*128+32,32))
	label(board,"上下段：下・左 / 右・上　　物語の転職解放は後続段階",Vector2(8,264))
	await save_frame("res://docs/verification/sprint3/"+job+"-walk-render.png")
	board.queue_free();await process_frame
	for frame in range(3):
		var battle := RpgBattleView.new();battle.size=Vector2(512,288);battle.members=game.export_state()["party"];battle.enemy_ids=["slime"];battle.definitions=game.enemy_definitions
		for actor in battle.members:battle.frames[actor["id"]]=frame
		root.add_child(battle)
		label(battle,"衣装表示見本："+str(game.jobs[job]["name"])+" / "+["待機","攻撃","被弾"][frame],Vector2(8,6))
		label(battle,"本番の戦闘描画を使用した見本（物語の進行記録ではない）",Vector2(8,264))
		await save_frame("res://docs/verification/sprint3/%s-battle-%d.png" % [job,frame])
		battle.queue_free();await process_frame

func save_frame(path: String) -> void:
	await create_timer(0.2).timeout
	await process_frame;await process_frame
	await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var image := root.get_texture().get_image()
	check(not image.is_empty() and image.get_pixel(0,0)!=Color.WHITE,"描画待ちの白い画像ではない")
	check(image.save_png(path)==OK,"実描画保存: "+path)

func run() -> void:
	var game := GameSession.new()
	check(game.new_game(4),"既存の4人開始API")
	for job in JOBS:
		for actor in game.export_state()["party"]:
			check(game.choose_job(actor["id"],job),"共通転職API: "+actor["id"]+"/"+job)
		for actor in game.export_state()["party"]:
			for kind in ["walk","battle"]:
				var visual := CharacterVisuals.appearance(actor,kind)
				check(visual["available"] and visual["path"]=="res://assets/characters/%s/jobs/%s/%s.png" % [actor["id"],job,kind],"職業と衣装参照: "+actor["id"]+"/"+job+"/"+kind)
				lookups+=1
		var path := "user://costume_save_%s_%d.json" % [job,OS.get_process_id()]
		check(game.save_game(path),"転職後の保存")
		var loaded := GameSession.new();check(loaded.load_game(path),"別インスタンスへのロード")
		check(game.export_state()==loaded.export_state(),"保存後の全状態一致")
		for i in range(4):
			for kind in ["walk","battle"]:check(CharacterVisuals.appearance(game.export_state()["party"][i],kind)==CharacterVisuals.appearance(loaded.export_state()["party"][i],kind),"ロード後の衣装一致")
		roundtrips+=1
		await capture(game,job)
	var first := GameSession.new();check(first.new_first_region(),"新しい村内開始")
	var lock_preserved := not first.choose_job("pc_01","mage")
	check(lock_preserved,"最初の村の転職未解放を維持")
	var result := {"status":"PASS" if failures.is_empty() else "FAIL","scope":"共通転職API・保存と本番描画。物語の転職解放の証明ではない","jobs":JOBS,"actors":4,"lookups":lookups,"save_roundtrips":roundtrips,"first_region_job_lock_preserved":lock_preserved,"failures":failures,"native_render":capture_enabled,"build":BuildIdentity.current()}
	PlaySessionMetrics.write_json("res://docs/verification/sprint3/costume-runtime.json",result)
	for error in failures:printerr("JOB_COSTUMES_FAIL: "+error)
	print("JOB_COSTUMES_PASS: jobs=4 actors=4 lookups=32 saves=4" if failures.is_empty() else "JOB_COSTUMES_FAIL: failures="+str(failures.size()))
	quit(0 if failures.is_empty() else 1)
