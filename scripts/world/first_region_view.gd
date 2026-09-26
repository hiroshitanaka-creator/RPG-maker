class_name FirstRegionView
extends Control
## 登録済みタイルと人物だけで、最初の地方の実際の配置を描く。
var saved: Dictionary = {}
var walk_frame := 0
var _tiles: Texture2D
var _outdoor: Texture2D
var _boss_texture: Texture2D
var _walkers: Dictionary = {}
var _camera := Vector2i.ZERO

func _ready() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_outdoor = load("res://assets/tiles/field_outdoor.png")
	_boss_texture = load("res://assets/monsters/gate_beast/idle.png")
	_tiles = load("res://assets/tiles/dungeon_cave.png") if saved["overworld"]["node"] == "first_cave" else _outdoor
	for id in ["pc_01","pc_02","pc_03","pc_04"]:
		_walkers[id] = load("res://assets/characters/"+id+"/walk.png")
	for actor in saved["party"]:
		var appearance := CharacterVisuals.appearance(actor,"walk")
		if appearance["available"]:_walkers[actor["id"]] = load(appearance["path"])

func _tile(cell: Vector2i, index: int, texture: Texture2D = null) -> void:
	var position_on_map := (cell-_camera)*32
	draw_texture_rect_region(_tiles if texture == null else texture,Rect2(position_on_map.x,position_on_map.y,32,32),Rect2(index*32,0,32,32))

func _label_at(cell: Vector2i, text: String) -> void:
	var position_on_map := (cell-_camera)*32
	draw_string_outline(get_theme_default_font(),Vector2(position_on_map.x-8,position_on_map.y-7),text,HORIZONTAL_ALIGNMENT_LEFT,-1,10,3,Color("152236"))
	draw_string(get_theme_default_font(),Vector2(position_on_map.x-8,position_on_map.y-7),text,HORIZONTAL_ALIGNMENT_LEFT,-1,10,Color.WHITE)

func _person(id: String, cell: Vector2i, facing: int, frame: int = 0) -> void:
	var position_on_map := (cell-_camera)*32
	var column: int = [0,1,0,2][frame%4]
	draw_texture_rect_region(_walkers[id],Rect2(position_on_map.x,position_on_map.y-16,32,48),Rect2(column*32,facing*48,32,48))

func _draw() -> void:
	if saved.is_empty() or _tiles == null:return
	var state: Dictionary = saved["overworld"]
	var here := WorldExpedition.point(state["cell"])
	var definition := FirstRegion.data()
	var interior := FirstRegion.room(state)
	var columns := maxi(1,floori(size.x/32.0))
	var rows := maxi(1,floori(size.y/32.0))
	var extent := WorldTerrain.size_tiles() if state["layer"] == "world" else Vector2i(str(interior["layout"][0]).length(),interior["layout"].size())
	_camera = Vector2i(clampi(here.x-columns/2,0,maxi(0,extent.x-columns)),clampi(here.y-rows/2,0,maxi(0,extent.y-rows)))
	for y in range(rows+1):
		for x in range(columns+1):
			var cell := _camera+Vector2i(x,y)
			var index := 1
			if state["layer"] == "world":index = {"g":0,"~":2,"r":3,"f":13,"m":1,"b":5,"n":6}.get(WorldTerrain.tile(cell),1)
			elif cell.y < extent.y and cell.x < extent.x:
				index = 0 if str(interior["layout"][cell.y]).substr(cell.x,1) == "." else 1
			_tile(cell,index)
	if state["layer"] == "world":
		_tile(WorldExpedition.point(definition["village_entrance"]["cell"]),8)
		_label_at(WorldExpedition.point(definition["village_entrance"]["cell"]),"村（仮）")
		_tile(WorldExpedition.point(definition["cave_entrance"]["cell"]),15)
		_label_at(WorldExpedition.point(definition["cave_entrance"]["cell"]),"洞窟（仮）")
		var gate := WorldExpedition.point(definition["gate"]["cell"]["cell"])
		_tile(gate,5 if saved["inventory"].get("gate_pass",0) > 0 else 7)
		_label_at(gate,"関所（仮）・開" if saved["inventory"].get("gate_pass",0) > 0 else "関所（仮）・閉")
	else:
		for event in interior["events"]:
			if event["kind"] == "recruit" and FirstRegion.joined(saved,event["actor"]):continue
			var cell := WorldExpedition.point(event["cell"])
			if event["kind"] == "treasure":
				_tile(cell,6 if event["id"] in state["opened"] else 4)
				_label_at(cell,"空" if event["id"] in state["opened"] else "宝箱")
			else:
				_person(event.get("actor","pc_04"),cell,0)
				_label_at(cell,event.get("label","仲間"))
		var points: Array = [[definition["village_exit"],"出口",3],[definition["cave_exit"],"出口",3],[definition["stairs_down"]["from"],"地下2階へ",12],[definition["stairs_up"]["from"],"地下1階へ",12]]
		for link in definition["doors"]:points.append([link["from"],"出入口",3])
		for entry in points:
			if state["node"] == entry[0]["node"] and state["room"] == entry[0]["room"]:
				_tile(WorldExpedition.point(entry[0]["cell"]),entry[2])
				_label_at(WorldExpedition.point(entry[0]["cell"]),entry[1])
		var boss: Dictionary = definition["boss"]["point"]
		if state["node"] == boss["node"] and state["room"] == boss["room"] and "first_boss" not in state["cleared"]:
			var position_on_map := (WorldExpedition.point(boss["cell"])-_camera)*32
			draw_texture_rect(_boss_texture,Rect2(position_on_map.x-16,position_on_map.y-32,64,64),false)
			_label_at(WorldExpedition.point(boss["cell"]),"番人（仮）")
	_person(saved.get("leader_id","pc_01"),here,state["facing"],walk_frame)
