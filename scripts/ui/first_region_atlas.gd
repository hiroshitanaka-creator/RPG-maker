class_name FirstRegionAtlas
extends Control
## 道具「世界地図」の表示専用画面。選んだ場所への移動機能は持たない。
signal closed
var saved: Dictionary = {}
var _map: ImageTexture
var _time := 0.0

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var extent := WorldTerrain.size_tiles()
	var image := Image.create(extent.x,extent.y,false,Image.FORMAT_RGB8)
	var colors := {"~":Color("4079a4"),"g":Color("78954a"),"f":Color("3e633d"),"m":Color("787466"),"r":Color("bea272"),"b":Color("ad855a"),"n":Color("e1d2a6")}
	for y in range(extent.y):
		for x in range(extent.x):image.set_pixel(x,y,colors.get(WorldTerrain.tile(Vector2i(x,y)),Color("859265")))
	var local: Dictionary=FirstRegionPresentation.data()["maps"]["world"]
	var origin := WorldExpedition.point(local["origin"])
	for y in range(local["height"]):
		for x in range(local["width"]):image.set_pixel(origin.x+x,origin.y+y,colors.get(str(local["terrain"][y]).substr(x,1),Color("859265")))
	_map=ImageTexture.create_from_image(image)
	var button := Button.new();button.text="地図を閉じる";button.position=Vector2(374,248);button.size=Vector2(128,28);button.pressed.connect(func()->void:closed.emit());add_child(button)
	button.grab_focus.call_deferred()

func _process(delta: float) -> void:
	_time+=delta;queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO,size),Color("0b1925"))
	if _map==null:return
	var origin := Vector2(122,16)
	draw_texture(_map,origin)
	draw_string(get_theme_default_font(),Vector2(12,27),"世界地図",HORIZONTAL_ALIGNMENT_LEFT,-1,16,Color.WHITE)
	var state: Dictionary=saved["overworld"]
	var cell := WorldExpedition.point(state["cell"])
	if state["layer"]=="interior":cell=WorldExpedition.point(FirstRegion.data()["cave_entrance" if state["node"]=="first_cave" else "village_entrance"]["cell"])
	var center := origin+Vector2(cell)
	draw_rect(Rect2(center-Vector2(3,3),Vector2(7,7)),Color("152236"))
	if fmod(_time,0.8)<0.5:draw_rect(Rect2(center-Vector2(2,2),Vector2(5,5)),Color("fff1a9"))
	draw_string(get_theme_default_font(),Vector2(384,30),"点滅：現在地",HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color.WHITE)
