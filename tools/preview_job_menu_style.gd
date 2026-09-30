extends SceneTree
## 採否確認専用。本番の画面生成を呼び、表示中のノードだけに色・枠の案を当てる。
## 操作処理・項目・保存ファイル・本番テーマは変更しない。受入検査ではない。
const OUTPUT := "res://docs/verification/menu-style-preview/job-menu.png"

func _initialize() -> void:
	OS.set_environment("RPG_QA_SAVE_PREFIX","menu_style_preview_%d" % OS.get_process_id())
	root.content_scale_size=Vector2i(512,288)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.size=Vector2i(1024,576)
	call_deferred("render_preview")

func button_box(base: StyleBox, selected: bool, hovered: bool) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color=Color(1,1,1,0.10) if hovered else Color("101c50")
	box.border_color=Color.WHITE
	box.set_border_width_all(1 if selected else 0)
	box.set_corner_radius_all(2)
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:box.set_content_margin(side,base.get_content_margin(side))
	return box

func render_preview() -> void:
	var scene: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	var main := scene.instantiate()
	root.add_child(main)
	await process_frame
	var game: GameSession=main.get("game")
	var preview_save := "user://menu_style_preview_%d.json" % OS.get_process_id()
	var copy := FileAccess.open(preview_save,FileAccess.WRITE)
	copy.store_buffer(FileAccess.get_file_as_bytes("res://.tools/port-departure.json"));copy.close()
	if not game.load_game(preview_save):
		printerr("MENU_PREVIEW: 通常到達保存を読み込めません: "+str(game.errors));quit(1);return
	main.call("_region_ui_action",{"kind":"ui_menu"})
	await process_frame;await process_frame
	main.call("_region_ui_action",{"kind":"party"})
	await process_frame;await process_frame
	var theme := (main.theme as Theme).duplicate()
	theme.default_font=RpgFonts.get_font()
	theme.set_color("font_color","Label",Color.WHITE)
	theme.set_color("default_color","RichTextLabel",Color.WHITE)
	for type in ["Button","OptionButton"]:
		for state in ["normal","hover","pressed","focus","disabled"]:
			theme.set_stylebox(state,type,button_box(main.get_theme_stylebox(state,type),state=="focus",state in ["hover","pressed"]))
		for color in ["font_color","font_hover_color","font_pressed_color","font_focus_color"]:theme.set_color(color,type,Color.WHITE)
		theme.set_color("font_disabled_color",type,Color("9aa6c4"))
		theme.set_color("arrow_color",type,Color.WHITE)
	main.theme=theme
	var panel: FirstRegionScreen=main.get("_region_screen")
	for window in panel.find_children("*","PanelContainer",true,false):
		var old: StyleBox=window.get_theme_stylebox("panel")
		var blue := StyleBoxFlat.new();blue.bg_color=Color("101c50");blue.border_color=Color.WHITE
		blue.set_border_width_all(1);blue.set_corner_radius_all(3)
		for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:blue.set_content_margin(side,old.get_content_margin(side))
		window.add_theme_stylebox_override("panel",blue)
	# 選択欄の内容・接続先・位置を保ったまま、転職の欄へフォーカスを置く。
	for picker in panel.find_children("*","OptionButton",true,false):
		if picker.item_count==game.jobs.size():picker.grab_focus()
	for bar in panel.find_children("*","VScrollBar",true,false):
		for state in ["grabber","grabber_highlight","grabber_pressed"]:
			var style := StyleBoxFlat.new();style.bg_color=Color("bdc7d3") if state=="grabber" else Color.WHITE
			style.set_corner_radius_all(2);bar.add_theme_stylebox_override(state,style)
	await process_frame;await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT.get_base_dir()))
	var result := root.get_texture().get_image().save_png(OUTPUT)
	print("MENU_PREVIEW: "+OUTPUT+"（本番未適用の表示見本）")
	quit(0 if result==OK else 1)
