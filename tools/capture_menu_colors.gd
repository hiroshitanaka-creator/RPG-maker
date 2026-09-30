extends SceneTree
## 変更前後で同じ本番画面を撮影する。条件付き画面は表示用状態であり、通常到達の証拠ではない。
const BASE := "d5833dbbdb5ff725aeb545eacd8966f7b04410e6"
const LIMIT_MS := 180000
var stage := "after"
var main: Control
var document := {"screens":[],"errors":[]}
var started := 0
var out := ""

func _initialize() -> void:
	stage=OS.get_environment("MENU_CAPTURE_STAGE")
	if stage not in ["before","after"]:stage="after"
	started=Time.get_ticks_msec()
	OS.set_environment("RPG_QA_SAVE_PREFIX","menu_colors_%d" % OS.get_process_id())
	root.content_scale_size=Vector2i(512,288);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.size=Vector2i(1024,576)
	call_deferred("run")

func settle() -> void:
	for i in range(5):await process_frame
	if Time.get_ticks_msec()-started>LIMIT_MS:
		printerr("MENU_CAPTURE_FAIL: 180秒の上限");quit(1)

func style(value: StyleBox) -> Dictionary:
	var data := {"type":value.get_class(),"margins":[]}
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:data["margins"].append(value.get_margin(side))
	if value is StyleBoxFlat:
		data["background"]=value.bg_color.to_html();data["border"]=value.border_color.to_html()
		data["widths"]=[value.border_width_left,value.border_width_top,value.border_width_right,value.border_width_bottom]
	return data

func rect_values(rect: Rect2) -> Array:
	return [snappedf(rect.position.x,.0001),snappedf(rect.position.y,.0001),snappedf(rect.size.x,.0001),snappedf(rect.size.y,.0001)]

func record(node: Node, path: String, rows: Array) -> void:
	if node is PopupMenu:
		if not node.visible:return
		var items: Array=[]
		for i in range(node.item_count):items.append({"text":node.get_item_text(i),"disabled":node.is_item_disabled(i),"metadata":str(node.get_item_metadata(i))})
		rows.append({"path":path,"kind":"PopupMenu","rect":[node.position.x,node.position.y,node.size.x,node.size.y],"items":items,
			"font":node.get_theme_font("font").get_font_name(),"font_size":node.get_theme_font_size("font_size"),
			"colors":{"font":node.get_theme_color("font_color").to_html(),"disabled":node.get_theme_color("font_disabled_color").to_html()},
			"styles":{"panel":style(node.get_theme_stylebox("panel")),"hover":style(node.get_theme_stylebox("hover"))}})
	elif node is Control:
		if not node.is_visible_in_tree():return
		var row := {"path":path,"kind":node.get_class(),"rect":rect_values(node.get_global_rect()),"colors":{},"styles":{}}
		if node is Label or node is Button or node is TextEdit or node is LineEdit:
			row["text"]=node.text;row["font"]=node.get_theme_font("font").get_font_name();row["font_size"]=node.get_theme_font_size("font_size")
			row["colors"]["font"]=node.get_theme_color("font_color").to_html()
		if node is RichTextLabel:
			row["text"]=node.text;row["font"]=node.get_theme_font("normal_font").get_font_name();row["font_size"]=node.get_theme_font_size("normal_font_size")
			row["colors"]["font"]=node.get_theme_color("default_color").to_html()
		if node is Button:
			row["disabled"]=node.disabled;row["focus_mode"]=node.focus_mode
			row["colors"]["disabled"]=node.get_theme_color("font_disabled_color").to_html()
			for name in ["normal","focus","disabled"]:row["styles"][name]=style(node.get_theme_stylebox(name))
		if node is OptionButton:
			row["selected"]=node.selected;row["items"]=[]
			for i in range(node.item_count):row["items"].append({"text":node.get_item_text(i),"disabled":node.is_item_disabled(i),"metadata":str(node.get_item_metadata(i))})
		if node is PanelContainer:row["styles"]["panel"]=style(node.get_theme_stylebox("panel"))
		if node is ScrollBar:
			row["range"]=[node.min_value,node.max_value,node.page,node.value]
			for name in ["scroll","grabber","grabber_highlight"]:row["styles"][name]=style(node.get_theme_stylebox(name))
		if node is TextEdit:
			row["placeholder"]=node.placeholder_text;row["editable"]=node.editable
			for name in ["normal","focus"]:row["styles"][name]=style(node.get_theme_stylebox(name))
		rows.append(row)
	var children := node.get_children(true)
	for i in range(children.size()):record(children[i],path+"/"+str(i),rows)

func shot(id: String, title: String, fixture: bool = false) -> void:
	await settle();await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var result := image.save_png(out+id+".png")
	if result!=OK:document["errors"].append("画像保存失敗: "+id)
	var rows: Array=[];record(main,"main",rows)
	document["screens"].append({"id":id,"title":title,"display_fixture":fixture,"mode":str(main.Mode.keys()[main.mode]),"controls":rows,"corner":image.get_pixel(4,4).to_html()})
	print("MENU_CAPTURE: "+stage+" "+id)

func show_mode(value: int) -> void:
	main.set("mode",value);main.call("_refresh");await settle()

func job_picker() -> OptionButton:
	for node in main.find_children("*","OptionButton",true,false):
		if node.item_count==main.game.jobs.size():return node
	return null

func run() -> void:
	out="res://docs/verification/menu-colors/"+stage+"/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	var packed: PackedScene=load(str(ProjectSettings.get_setting("application/run/main_scene")))
	main=packed.instantiate()
	var source := "res://scripts/ui/game_root.gd"
	if stage=="before":
		source="res://.tools/menu-baseline-root.gd";main.set_script(load(source))
	root.add_child(main);await settle()
	var raw := FileAccess.get_file_as_bytes("res://.tools/port-departure.json")
	var save_path := "user://menu_colors_%d.json" % OS.get_process_id()
	var file := FileAccess.open(save_path,FileAccess.WRITE);file.store_buffer(raw);file.close()
	if not main.game.load_game(save_path):printerr("MENU_CAPTURE_FAIL: 開始保存の読込");quit(1);return
	document["stage"]=stage;document["baseline"]=BASE;document["root_source_sha256"]=FileAccess.get_sha256(source)
	document["sources"]={}
	for path in ["scripts/ui/first_region_screen.gd","scripts/ui/first_region_atlas.gd","scripts/ui/rpg_menu_colors.gd","scripts/ui/rpg_fonts.gd"]:
		document["sources"][path]=FileAccess.get_sha256("res://"+path)
	var digest := HashingContext.new();digest.start(HashingContext.HASH_SHA256);digest.update(raw);document["save_sha256"]=digest.finish().hex_encode()
	main.call("_region_ui_action",{"kind":"ui_menu"});await settle()
	await shot("01-menu","Escapeメニュー")
	main.call("_region_ui_action",{"kind":"save"});await settle()
	await shot("02-save-notice","保存の通知")
	main.call("_region_ui_action",{"kind":"ui_items"});await settle()
	await shot("03-items","どうぐ・使用相手")
	main.call("_region_ui_action",{"kind":"ui_atlas"});await settle()
	await shot("04-atlas","世界地図")
	# 帰還の風の見た目だけを、習得済み・訪問済みの表示用状態で確認する。
	var ready: Dictionary=main.game.export_state()
	var travel := FirstRegionTravel.ensure(ready)
	travel["return_learned"]=true;travel["visited"]=["start_village","first_castle","first_port"]
	if not main.game.import_state(ready):printerr("MENU_CAPTURE_FAIL: 帰還の表示用状態");quit(1);return
	main.call("_region_ui_action",{"kind":"ui_return_menu"});await settle()
	await shot("05-return","帰還の風・無効な行き先",true)
	main.call("_region_ui_action",{"kind":"ui_return_actor","actor":"pc_01"});await settle()
	await shot("06-return-selected","帰還の風・仲間を選択",true)
	main.call("_region_ui_action",{"kind":"party"});await settle()
	var picker := job_picker();picker.grab_focus()
	await shot("07-party-job","転職・仲間選択")
	picker.show_popup();await settle();picker.get_popup().set_focused_item(picker.selected)
	await shot("08-job-list","開いた職業一覧")
	picker.get_popup().hide();await settle()
	for i in range(picker.item_count):
		if str(picker.get_item_text(i)).contains("未解放"):
			picker.select(i);picker.item_selected.emit(i);break
	await shot("09-job-disabled","未解放の職業・無効な転職ボタン")
	await show_mode(main.Mode.PARTY)
	for scroll in main.find_children("*","ScrollContainer",true,false):scroll.scroll_vertical=10000
	await shot("10-party-bottom","装備・技の装着・状態")
	main.submit_player_action({"kind":"job_lore"});await settle()
	await shot("11-job-lore","町の噂・魔物図鑑")
	await show_mode(main.Mode.PARTY);main.submit_player_action({"kind":"mechanics"});await settle()
	await shot("12-mechanics","機構の覚え書き")
	main.set("_purify_actor","pc_01");await show_mode(main.Mode.PARTY)
	await shot("13-purify","祠で清める確認",true)
	main.set("_purify_actor","")
	await show_mode(main.Mode.RULE_UPGRADE)
	await shot("14-upgrade","旧保存のルール引継ぎ確認",true)
	main.call("_region_ui_action",{"kind":"journal"});await settle()
	await shot("15-journal","旅の手帳")
	main.call("_show_dialogue",[""],false,main.Mode.JOURNAL,true);main.call("_refresh");await settle()
	await shot("16-replay","記録の読み返し・本文は伏せる",true)
	main.call("_to_menu");await settle()
	await shot("17-title","タイトル")
	main.submit_player_action({"kind":"review"});await settle()
	await shot("18-review","試遊の記録と評価")
	var ratings := main.find_children("*","OptionButton",true,false)
	if not ratings.is_empty():ratings[0].show_popup();await settle();ratings[0].get_popup().set_focused_item(1)
	await shot("19-review-list","評価の選択一覧")
	if not ratings.is_empty():ratings[0].get_popup().hide()
	await settle()
	for note in main.find_children("*","TextEdit",true,false):note.grab_focus()
	await shot("20-review-input","メモ入力・選択枠")
	# 習得後・船のそばで増える項目も、同じメニューの表示用状態で撮る。
	travel=FirstRegionTravel.ensure(ready);travel["ship_owned"]=true;travel["ship_cell"]=FirstRegionTravel.data()["docks"][0]["ship_cell"].duplicate()
	FirstRegion.place(ready["overworld"],FirstRegionTravel.data()["docks"][0]["land"])
	if not main.game.import_state(ready):printerr("MENU_CAPTURE_FAIL: 乗船の表示用状態");quit(1);return
	main.call("_region_ui_action",{"kind":"ui_menu"});await settle()
	await shot("21-menu-ship","習得済みの帰還・乗船案内",true)
	# 手帳を生成する本番処理を通す。物語の文章だけをこのプロセス内の表示用データへ置き換える。
	var original_story := StoryCampaign.data().duplicate(true)
	var display_story := original_story.duplicate(true)
	var journal_state: Dictionary=main.game.export_state()
	for i in range(2):
		var clue: Dictionary=display_story["clues"][i]
		journal_state["progress_flags"]["clue_"+str(clue["id"])+"_seeded"]=true
		clue["title"]="表示確認用の記録"+str(i+1)
		for key in ["observation","first","resolved"]:clue[key]="物語の本文は、この表示確認では伏せています。"
	if not main.game.import_state(journal_state):printerr("MENU_CAPTURE_FAIL: 手帳の表示用状態");quit(1);return
	StoryCampaign._data=display_story
	main.call("_region_ui_action",{"kind":"journal"});await settle()
	await shot("22-journal-filled","記録のある手帳・本文は表示用",true)
	var journals := main.find_children("*","OptionButton",true,false)
	if not journals.is_empty():journals[0].show_popup();await settle();journals[0].get_popup().set_focused_item(0)
	await shot("23-journal-list","手帳の記録選択一覧・表示用",true)
	if not journals.is_empty():journals[0].get_popup().hide()
	StoryCampaign._data=original_story
	document["elapsed_ms"]=Time.get_ticks_msec()-started
	document["limit_ms"]=LIMIT_MS
	var output := FileAccess.open(out+"screens.json",FileAccess.WRITE);output.store_string(JSON.stringify(document,"\t")+"\n");output.close()
	print("MENU_CAPTURE_DONE: screens=%d errors=%d" % [document["screens"].size(),document["errors"].size()])
	quit(0 if document["errors"].is_empty() and document["elapsed_ms"]<LIMIT_MS else 1)
