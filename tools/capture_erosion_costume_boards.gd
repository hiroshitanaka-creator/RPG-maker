extends SceneTree
## 本番と同じ72px戦闘・32×48歩行を、標準ウィンドウの整数2倍で一覧にする。
const OUTPUT := "res://docs/verification/erosion-costumes/"
const JOBS := ["warrior","martial_artist","priest","mage","thief","hunter","apothecary","bard","knight","sage","swordsman","shaman"]
const NAMES := ["戦士","武闘家","僧侶","魔法使い","盗賊","狩人","薬師","吟遊詩人","騎士","賢者","剣士","祈祷師"]
var failures: Array[String]=[]
var checks := 0
var draft := false
var prepared: Dictionary={}

class CostumeRow extends Control:
	var actor_id := "pc_01"
	var job := "warrior"
	var title := ""
	var kind := "battle"
	var paths: Array[String]=[]
	var textures: Dictionary={}
	func _ready() -> void:texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	func _draw() -> void:
		draw_rect(Rect2(0,0,512,288),Color("162835"))
		var lines := title.split("\n")
		for index in range(lines.size()):draw_string(RpgFonts.get_font(),Vector2(6,16+index*14),lines[index],HORIZONTAL_ALIGNMENT_LEFT,-1,10,Color("eef6eb"))
		if paths.size()!=3:return
		for index in range(3):
			var x := 108+index*128
			draw_string(RpgFonts.get_font(),Vector2(x,16),["平常","兆候","変異"][index],HORIZONTAL_ALIGNMENT_LEFT,-1,10,Color("eef6eb"))
			var path: String=paths[index]
			if not textures.has(path):textures[path]=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(path)))
			if kind=="battle":draw_texture_rect_region(textures[path],Rect2(x+20,26,72,72),Rect2(0,0,96,96))
			else:
				for facing in range(4):draw_texture_rect_region(textures[path],Rect2(x+facing*32,26,32,48),Rect2(32,facing*48,32,48))

func check(ok: bool, reason: String) -> void:
	checks+=1
	if not ok:failures.append(reason)

func _initialize() -> void:
	draft="--draft" in OS.get_cmdline_user_args()
	if DisplayServer.get_name()=="headless":printerr("COSTUME_BOARDS_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.size=Vector2i(1024,576)
	call_deferred("run")

func run() -> void:
	var list: Array=JSON.parse_string(FileAccess.get_file_as_string(OUTPUT+"prepared-records.json"))
	for r in list:prepared["%s/%s/%s/%d" % [r["actor"],r["job"],r["kind"],int(r["stage"])]]=r
	for actor_index in range(4):
		var actor_id := "pc_%02d" % (actor_index+1)
		for kind in ["battle","walk"]:
			var height := 220 if kind=="battle" else 164
			var atlas := Image.create(1024,height*12,false,Image.FORMAT_RGB8)
			var board := CostumeRow.new();board.kind=kind;board.size=Vector2(512,288);root.add_child(board)
			for ji in range(12):
				var job: String=JOBS[ji];board.title=["カイナ","リオネ","ハルド","スイナ"][actor_index]+"\n"+NAMES[ji];board.paths.clear()
				for stage in [0,30,60]:
					var actor := {"id":actor_id,"job_id":job,"erosion":stage,"monster_form":""}
					var expected := "res://assets/characters/%s/jobs/%s/%s.png" % [actor_id,job,kind] if stage==0 else "res://assets/characters/%s/erosion_signs/jobs/%s/%d/%s.png" % [actor_id,job,stage,kind]
					var path: String=expected
					if draft and stage>0:path="res://"+str(prepared["%s/%s/%s/%d" % [actor_id,job,kind,stage]]["prepared"]["composite"])
					if not draft:
						for facing in range(1 if kind=="battle" else 4):
							for pose in range(3):
								var visual := CharacterVisuals.appearance(actor,kind,pose,facing)
								check(visual["available"] and visual["path"]==expected,"衣装・段階参照: "+expected)
								check(visual["region"].size==(Vector2(96,96) if kind=="battle" else Vector2(32,48)),"フレーム寸法")
					board.paths.append(path)
				board.queue_redraw();await process_frame;await process_frame;await RenderingServer.frame_post_draw
				RenderingServer.force_draw(false);RenderingServer.force_sync()
				var image := root.get_texture().get_image();check(image.get_size()==Vector2i(1024,576),"標準ウィンドウで撮影")
				image.convert(Image.FORMAT_RGB8)
				check(image.get_pixel(0,0)==Color("162835"),"一覧行の背景を実描画")
				atlas.blit_rect(image,Rect2i(0,0,1024,height),Vector2i(0,ji*height))
				check(atlas.get_region(Rect2i(0,ji*height,1024,height)).get_data()==image.get_region(Rect2i(0,0,1024,height)).get_data(),"撮影行を拡縮せず転記")
			check(atlas.save_png(OUTPUT+actor_id+"-"+kind+".png")==OK,"一覧保存")
			board.queue_free();await process_frame
	PlaySessionMetrics.write_json(OUTPUT+"board-checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","draft_mode":draft,"checks":checks,"failures":failures,"actors":4,"jobs":12,"stages":[0,30,60],"battle_display_internal":[72,72],"battle_display_window":[144,144],"walk_display_internal":[32,48],"walk_display_window":[64,96],"rows_resized":false,"scope":"各人物12職×3段階。戦闘一覧は待機、歩行は4方向の歩行コマ。全コマの参照は別途確認。"})
	for failure in failures:printerr("COSTUME_BOARDS_FAIL: "+failure)
	print("COSTUME_BOARDS_PASS: checks=%d draft=%s" % [checks,draft] if failures.is_empty() else "COSTUME_BOARDS_FAIL")
	quit(0 if failures.is_empty() else 1)
