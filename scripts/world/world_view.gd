class_name WorldView
extends Control

signal cell_clicked(cell: Vector2i)

var location: String = "town"
var section_id: String = ""
var player_cell := Vector2i(2,4)
var objective := Vector2i(5,4)
var facing: int = 0
var walk_frame: int = 0
var progress_flags: Dictionary = {}
var sites: Array[Dictionary] = []
var members: Array[Dictionary] = []
var trail: Array[Dictionary] = []
var _tiles: Texture2D
var _walkers: Dictionary = {}
var _camera := Vector2i.ZERO


func _ready() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	var tile_path := "res://assets/tiles/field_outdoor.png" if location in ChapterOne.TOWNS or location == "waterway" else "res://assets/tiles/dungeon_cave.png"
	if ResourceLoader.exists(tile_path):
		_tiles = load(tile_path)
	for actor in members:
		var visual := CharacterVisuals.appearance(actor,"walk")
		if visual["available"]:
			_walkers[actor["id"]] = load(visual["path"])
	queue_redraw()


func _draw() -> void:
	if _tiles == null:
		return
	var columns := maxi(1, floori(size.x / 32.0))
	var rows := maxi(1, floori(size.y / 32.0))
	_camera = Vector2i(clampi(player_cell.x - floori(float(columns)/2.0), 0, ChapterOne.WIDTH-columns), clampi(player_cell.y - floori(float(rows)/2.0), 0, ChapterOne.HEIGHT-rows))
	for y in range(rows+1):
		for x in range(columns+1):
			var cell := _camera + Vector2i(x,y)
			var walkable := ExplorationSites.is_walkable(location,cell,progress_flags) if section_id.is_empty() else CampaignContent.is_walkable(section_id,cell)
			var index := 0 if walkable else (2 if location == "waterway" else 1)
			draw_texture_rect_region(_tiles, Rect2(x*32,y*32,32,32), Rect2(index*32,0,32,32))
	for site in sites:
		var marker_cell := (Vector2i(site["cell"][0],site["cell"][1])-_camera)*32
		var color := Color("71b7e8") if site["kind"] == "device" else Color("7dcc9b")
		if site["complete"]:
			color = Color("697b84")
		draw_rect(Rect2(marker_cell.x+5,marker_cell.y+5,22,22),color,false,2.0)
		if site["kind"] == "cache":
			draw_line(Vector2(marker_cell.x+5,marker_cell.y+13),Vector2(marker_cell.x+27,marker_cell.y+13),color,2.0)
	var marker := (objective-_camera)*32
	if objective != player_cell:
		draw_texture_rect_region(_tiles, Rect2(marker.x,marker.y,32,32), Rect2(4*32,0,32,32))
		draw_rect(Rect2(marker.x+1,marker.y+1,30,30), Color("e7c77b"), false, 1.0)
	var units: Array[Dictionary] = []
	for index in range(members.size()):
		var previous: Dictionary = {"cell":[player_cell.x,player_cell.y],"facing":facing}
		if index > 0 and not trail.is_empty():
			previous = trail[mini(index-1,trail.size()-1)]
		units.append({"actor":members[index],"cell":previous["cell"],"facing":previous["facing"],"order":index})
	units.sort_custom(func(a: Dictionary,b: Dictionary) -> bool: return a["order"] > b["order"] if a["cell"][1] == b["cell"][1] else a["cell"][1] < b["cell"][1])
	for unit in units:
		var actor: Dictionary = unit["actor"]
		var position_on_map := (Vector2i(unit["cell"][0],unit["cell"][1])-_camera)*32
		var visual := CharacterVisuals.appearance(actor,"walk",walk_frame,unit["facing"])
		if _walkers.has(actor["id"]):
			draw_texture_rect_region(_walkers[actor["id"]],Rect2(position_on_map.x,position_on_map.y-16,32,48),visual["region"])
		else:
			draw_string(get_theme_default_font(),Vector2(position_on_map.x,position_on_map.y+10),"外見未取込",HORIZONTAL_ALIGNMENT_LEFT,-1,9,Color.WHITE)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		cell_clicked.emit(Vector2i(floori(event.position.x/32), floori(event.position.y/32)) + _camera)
