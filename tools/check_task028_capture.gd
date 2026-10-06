extends SceneTree
## 028：本番描画器の同じ確認用状態。遭遇・実戦・報酬は有効化しない。
const BOSS := "ruins_sandstone_colossus"
var failures: Array[String] = []
var checks := 0
var output := ""
var phase := ""

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:failures.append(message)

func frames() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw

func values(rect: Rect2) -> Array:
	return [rect.position.x,rect.position.y,rect.size.x,rect.size.y]

func run() -> void:
	output=OS.get_environment("TASK028_OUTPUT")+"/"
	phase=OS.get_environment("TASK028_PHASE")
	check(phase in ["before","after"],"前後の指定")
	check(DisplayServer.get_name()=="X11","実レンダラーX11")
	check(OS.get_environment("RPG_QA_SAVE_PREFIX").begins_with("task028-"),"専用保存領域")
	DirAccess.make_dir_recursive_absolute(output)
	root.size=Vector2i(1024,576)
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	var session := GameSession.new()
	check(session.new_first_region(),"011と同じ本番新ゲーム")
	var base := session.export_state()
	base["party"].append_array(base["first_region"]["reserve"])
	base["first_region"]["reserve"]=[]
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/source_records/task011-enemies.json"))
	var definitions := session.enemy_definitions.duplicate(true)
	for enemy in data["enemies"]:definitions[enemy["id"]]=enemy
	check(session.enemy_definitions.size()==36,"本番36種を変更しない")
	check(not session.enemy_definitions.has(BOSS),"巨像の本番戦闘を有効化しない")
	var pages := [["ruins_sandstone_doll","ruins_cursed_beetle","ruins_sand_spirit"],["ruins_tomb_hound","desert_mummy","stone_gargoyle"],[BOSS]]
	var images := []
	for page in range(3):
		var arena := RpgBattleView.new()
		arena.size=Vector2(512,288);arena.members=base["party"];arena.enemy_ids=pages[page];arena.definitions=definitions;arena.background="region2_ruins"
		root.add_child(arena)
		var label := Label.new()
		label.text="確認用状態 / 遺跡の素材見本（戦闘は未有効化）";label.position=Vector2(8,250)
		label.add_theme_font_override("font",RpgFonts.get_font());label.add_theme_font_size_override("font_size",12);arena.add_child(label)
		await frames()
		check(arena.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST,"最近傍描画")
		var image := root.get_texture().get_image()
		check(image.get_size()==Vector2i(1024,576),"実画面寸法")
		var rendered := []
		var backdrop := (load("res://assets/backgrounds/region2_ruins.png") as Texture2D).get_image()
		for i in range(pages[page].size()):
			var id: String=pages[page][i]
			var region := arena.enemy_region(id)
			var rect := arena.actor_rect("enemy_%02d" % (i+1))
			var expected_scale := 1.125 if id==BOSS and phase=="after" else 0.75
			check(rect.size.is_equal_approx(region.size*expected_scale),"固定期待倍率 "+id)
			check(Rect2(0,0,512,223).encloses(rect),"全身は画面内かつ下部UIの上 "+id)
			for j in range(4):
				check(not rect.intersects(arena.party_rect(j)),"味方から分離 "+id)
				check(not rect.intersects(Rect2(arena.party_rect(j).position-Vector2(30,0),Vector2(72,72))),"味方の前進後も分離 "+id)
			if id==BOSS:check(rect.end.y==196 and rect.get_center().x==170,"巨像の足元・左右中心を保持")
			var source := arena._enemy_texture(id).get_image()
			var samples := 0;var matched := 0;var opaque := 0
			for y in range(ceili(rect.position.y*2),floori(rect.end.y*2)):
				for x in range(ceili(rect.position.x*2),floori(rect.end.x*2)):
					var uv := region.position+(Vector2(x+0.5,y+0.5)/2-rect.position)/expected_scale
					var xs := [floori(uv.x)];var ys := [floori(uv.y)]
					if absf(uv.x-roundf(uv.x))<0.0001:xs=[roundi(uv.x)-1,roundi(uv.x)]
					if absf(uv.y-roundf(uv.y))<0.0001:ys=[roundi(uv.y)-1,roundi(uv.y)]
					var actual := image.get_pixel(x,y);var same := false;var solid := false
					for sy in ys:
						for sx in xs:
							if not Rect2i(region).has_point(Vector2i(sx,sy)):continue
							var expected := source.get_pixel(sx,sy);solid=solid or expected.a==1
							if expected.a<1:expected=backdrop.get_pixel(x/2,y/2)
							same=same or maxi(maxi(absi(actual.r8-expected.r8),absi(actual.g8-expected.g8)),absi(actual.b8-expected.b8))<=1
					samples+=1;matched+=int(same);opaque+=int(solid)
			check(samples==matched and opaque>20,"固定倍率の敵・透明部の全画素一致 "+id)
			rendered.append({"id":id,"region":values(region),"rect":values(rect),"expected_scale":expected_scale,"samples":samples,"matched":matched,"opaque":opaque})
		check(image.save_png(output+"battle-%d.png" % (page+1))==OK,"実画面保存")
		images.append({"image":"battle-%d.png" % (page+1),"rendered":rendered})
		arena.queue_free();await frames()
	var layouts := {}
	for id in definitions:
		var arena := RpgBattleView.new()
		arena.definitions=definitions;arena.enemy_ids=[id]
		layouts[id]={"region":values(arena.enemy_region(id)),"rect":values(arena.actor_rect("enemy_01")),"feet":[arena.enemy_feet(0).x,arena.enemy_feet(0).y]}
		arena.free()
	var result := {"status":"PASS" if failures.is_empty() else "FAIL","execution_sha":OS.get_environment("TASK028_EXECUTION_SHA"),"phase":phase,"checks":checks,"failures":failures,"renderer":DisplayServer.get_name(),"confirmation_state":true,"enabled_battle":false,"images":images,"layouts":layouts}
	var file := FileAccess.open(output+"checks.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(result,"\t"));file.close()
	for failure in failures:print("TASK028_FAIL: "+failure)
	print("TASK028_CAPTURE_%s: checks=%d" % [result["status"],checks])
	quit(0 if failures.is_empty() else 1)
