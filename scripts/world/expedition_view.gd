class_name ExpeditionView
extends Control
signal cell_clicked(cell: Vector2i)
var state: Dictionary = {}
var members: Array[Dictionary] = []
var facing := 0
var walk_frame := 0
var _tiles: Texture2D
var _camera := Vector2i.ZERO
var _sprites: Dictionary = {}

func _ready() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	_tiles = load("res://assets/tiles/field_outdoor.png")
	for actor in members:
		var visual := CharacterVisuals.appearance(actor,"walk")
		if visual["available"]:
			_sprites[actor["id"]] = load(visual["path"])

func _draw() -> void:
	if state.is_empty() or _tiles == null:
		return
	var current := WorldExpedition.point(state["cell"])
	var extent := WorldTerrain.size_tiles() if state["layer"] == "world" else Vector2i(32,18)
	var columns := maxi(1,floori(size.x/32.0))
	var rows := maxi(1,floori(size.y/32.0))
	_camera = Vector2i(clampi(current.x-columns/2,0,maxi(0,extent.x-columns)),clampi(current.y-rows/2,0,maxi(0,extent.y-rows)))
	var indices := {"g":0,"~":2,"r":3,"f":13,"m":10,"b":5,"n":6}
	var definition := WorldExpedition.current_room(state)
	for y in range(rows+1):
		for x in range(columns+1):
			var cell := _camera+Vector2i(x,y)
			var tile_index := 0
			if state["layer"] == "world":
				tile_index = indices.get(WorldTerrain.tile(cell),2)
			else:
				tile_index = 6 if WorldExpedition.walkable_room(definition,cell) else 1
			draw_texture_rect_region(_tiles,Rect2(x*32,y*32,32,32),Rect2(tile_index*32,0,32,32))
	if state["layer"] == "world":
		for entry in WorldTerrain.data()["nodes"]:
			var cell := WorldTerrain.cell_of(entry["id"])
			var node := WorldExpedition.node(entry["id"])
			var index := 8 if node["type"] == "town" else 15 if node["type"] == "dungeon" else 4
			var position_on_map := (cell-_camera)*32
			draw_texture_rect_region(_tiles,Rect2(position_on_map.x,position_on_map.y,32,32),Rect2(index*32,0,32,32))
			var color := Color("e7c77b") if WorldExpedition.unlocked(entry["id"],state["flags"]) else Color("7b8186")
			draw_rect(Rect2(position_on_map.x+1,position_on_map.y+1,30,30),color,false,2)
			if entry["dock"]:
				draw_circle(Vector2(position_on_map.x+26,position_on_map.y+6),3,Color("71b7e8"))
			if abs(cell.x-current.x) <= 4 and abs(cell.y-current.y) <= 2:
				var lift := 36 if cell == current and state["transport"] == "flight" else 20
				draw_string(get_theme_default_font(),Vector2(position_on_map.x-8,position_on_map.y-lift),node["name"],HORIZONTAL_ALIGNMENT_LEFT,-1,10,Color.WHITE)
	else:
		for event in definition["events"]:
			var label: String = {"observe":"記録","battle":"魔物","choice":"相談","rest":"休息"}[event["kind"]]
			var complete: bool = WorldExpedition.done(state,event["id"]) or (event["kind"] == "choice" and state["choices"].has(state["node"]))
			_marker(WorldExpedition.point(event["cell"]),label,Color("718781") if complete else Color("e7c77b"))
		_marker(WorldExpedition.point(definition["exit"]),"出口",Color("71b7e8"))
		if not definition["next"].is_empty():
			_marker(WorldExpedition.point(definition["next"]),"奥へ",Color("71b7e8"))
	var player := (current-_camera)*32
	if state["layer"] == "world" and state["transport"] == "ship":
		var rotation: float = [PI,-PI/2,PI/2,0.0][facing]
		draw_set_transform(Vector2(player.x+16,player.y+16),rotation)
		draw_colored_polygon(PackedVector2Array([Vector2(0,-15),Vector2(-10,9),Vector2(-8,14),Vector2(8,14),Vector2(10,9)]),Color("a67c52"))
		draw_line(Vector2(0,-9),Vector2(0,10),Color("eee7cf"),2)
		draw_colored_polygon(PackedVector2Array([Vector2(1,-8),Vector2(8,7),Vector2(1,7)]),Color("eee7cf"))
		draw_set_transform(Vector2.ZERO)
	elif not members.is_empty() and _sprites.has(members[0]["id"]):
		var visual := CharacterVisuals.appearance(members[0],"walk",walk_frame,facing)
		var lift := 12 if state["layer"] == "world" and state["transport"] == "flight" else 0
		if lift > 0:
			draw_ellipse_shadow(Vector2(player.x+16,player.y+27))
		draw_texture_rect_region(_sprites[members[0]["id"]],Rect2(player.x,player.y-16-lift,32,48),visual["region"])

func draw_ellipse_shadow(center: Vector2) -> void:
	draw_circle(center,8,Color(0,0,0,0.4))
	draw_line(center+Vector2(-16,-12),center+Vector2(-5,-7),Color("dddcc5"),2)
	draw_line(center+Vector2(16,-12),center+Vector2(5,-7),Color("dddcc5"),2)

func _marker(cell: Vector2i, label: String, color: Color) -> void:
	var position_on_map := (cell-_camera)*32
	draw_rect(Rect2(position_on_map.x+5,position_on_map.y+5,22,22),color,false,2)
	draw_string(get_theme_default_font(),Vector2(position_on_map.x,position_on_map.y+17),label,HORIZONTAL_ALIGNMENT_LEFT,-1,10,color)

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		cell_clicked.emit(Vector2i(floori(event.position.x/32),floori(event.position.y/32))+_camera)
