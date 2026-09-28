extends SceneTree
## 城下町の全体を、本番の描画クラス FirstRegionView で1枚に撮る。
## 位置の書き換えは撮影用の一時状態だけで行い、保存データには書かない。
## 使い方: godot --path . --rendering-method gl_compatibility --script res://tools/capture_castle_town_full.gd -- <出力PNG>

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var output: String = args[0] if args.size()>0 else "res://docs/verification/castle-town-polish/full-town.png"
	var session := GameSession.new()
	if not session.new_first_region():
		printerr("CASTLE_FULL_FAIL: 新規開始に失敗");quit(1);return
	var saved := session.export_state()
	var map: Dictionary=FirstRegionPresentation.data()["maps"]["first_castle:0"]
	var spawn: Dictionary=FirstRegion.data()["castle_spawn"]
	saved["overworld"]["layer"]="interior"
	saved["overworld"]["node"]="first_castle"
	saved["overworld"]["room"]=0
	saved["overworld"]["cell"]=spawn["cell"]
	saved["overworld"]["facing"]=3
	var size := Vector2i(int(map["width"])*32,int(map["height"])*32)
	var port := SubViewport.new()
	port.size=size
	port.transparent_bg=false
	port.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(port)
	var view := FirstRegionView.new()
	view.saved=saved
	view.position=Vector2.ZERO;view.size=Vector2(size)
	port.add_child(view)
	for i in range(6):await process_frame
	await RenderingServer.frame_post_draw
	var image := port.get_texture().get_image()
	if image.get_size()!=size:
		printerr("CASTLE_FULL_FAIL: 画面寸法 %s != %s" % [image.get_size(),size]);quit(1);return
	if image.save_png(output)!=OK:
		printerr("CASTLE_FULL_FAIL: 保存失敗 "+output);quit(1);return
	print("CASTLE_FULL_PASS: %s %dx%d" % [output,size.x,size.y])
	quit(0)
