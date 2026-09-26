class_name FirstRegionView
extends Control
## 本番の地形層を描き、人物と建物を足元の順で重ねる。
var saved: Dictionary = {}
var walk_frame := 0
var movement_offset := Vector2.ZERO
var npc_offsets: Dictionary = {}
var speaking_actor := ""
var _camera := Vector2.ZERO
var _textures: Dictionary = {}
var _map: Dictionary = {}
var _ground: Array = []
var _objects: Array = []

func _ready() -> void:
	clip_contents=true
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	_map=FirstRegionPresentation.map_for(saved["overworld"])
	for layer in _map.get("layers",[]):
		if layer["cells"].is_empty():continue
		if layer["name"] in ["地面","dirt","shore","hills","forest","mountains","river","壁","64px岩壁・丸い湖・床の自動接続"]:
			_ground.append(layer)
		else:
			var bottom := 0
			for entry in layer["cells"]:bottom=maxi(bottom,int(entry[1])+1)
			_objects.append({"bottom":float(bottom),"layer":layer})
	for tile in _map.get("tiles",{}).values():_texture("res://"+str(tile["path"]))

func _texture(path: String) -> Texture2D:
	if not _textures.has(path):_textures[path]=load(path)
	return _textures[path]

func _screen(cell: Vector2) -> Vector2:
	return ((cell-_camera)*32.0).round()

func _draw_layer(layer: Dictionary) -> void:
	for entry in layer["cells"]:
		var position_on_map := _screen(Vector2(entry[0],entry[1]))
		if position_on_map.x < -32 or position_on_map.y < -32 or position_on_map.x > size.x or position_on_map.y > size.y:continue
		var tile: Dictionary=_map["tiles"][entry[2]]
		var region: Array=tile["region"]
		draw_texture_rect_region(_texture("res://"+str(tile["path"])),Rect2(position_on_map,Vector2(32,32)),Rect2(region[0],region[1],region[2],region[3]))

func _person(actor: Dictionary, cell: Vector2, facing: int, frame: int, npc: String = "") -> void:
	var path := "res://assets/characters/"+npc+"/walk.png"
	var column: int=[0,1,0,2][frame%4]
	if npc.is_empty():
		var appearance := CharacterVisuals.appearance(actor,"walk")
		path=appearance["path"]
	var position_on_map := _screen(cell)+Vector2(0,-16)
	draw_texture_rect_region(_texture(path),Rect2(position_on_map,Vector2(32,48)),Rect2(column*32,facing*48,32,48))

func _object(path: String, cell: Vector2, dimensions: Vector2, region: Rect2 = Rect2()) -> void:
	var position_on_map := _screen(cell)+Vector2(16-dimensions.x/2.0,32-dimensions.y)
	if region.size==Vector2.ZERO:draw_texture_rect(_texture(path),Rect2(position_on_map,dimensions),false)
	else:draw_texture_rect_region(_texture(path),Rect2(position_on_map,dimensions),region)

func _draw() -> void:
	if saved.is_empty() or _map.is_empty():return
	var state: Dictionary=saved["overworld"]
	var origin := Vector2(WorldExpedition.point(_map.get("origin",[0,0])))
	var here := Vector2(WorldExpedition.point(state["cell"]))-origin+movement_offset
	var extent := Vector2(_map["width"],_map["height"])
	var visible := size/32.0
	_camera=here-visible/2.0+Vector2(0.5,0.5)
	for axis in range(2):
		_camera[axis]=clampf(_camera[axis],0.0,extent[axis]-visible[axis]) if extent[axis]>=visible[axis] else (extent[axis]-visible[axis])/2.0
	draw_rect(Rect2(Vector2.ZERO,size),Color("101719"))
	for layer in _ground:_draw_layer(layer)
	var ordered: Array=_objects.duplicate()
	var definition := FirstRegion.data()
	if state["layer"]=="world":
		var gate := Vector2(WorldExpedition.point(definition["gate"]["cell"]["cell"]))-origin
		ordered.append({"bottom":gate.y+1.0,"object":"res://assets/objects/natural_gate.png","cell":gate,"dimensions":Vector2(96,96),"region":Rect2(128 if saved["inventory"].get("gate_pass",0)>0 else 0,0,128,128)})
	else:
		var stair: Dictionary=definition["stairs_down"]["from"] if state["room"]==0 else definition["stairs_up"]["from"]
		if state["node"]=="first_cave":
			var stairs := Vector2(WorldExpedition.point(stair["cell"]))
			ordered.append({"bottom":stairs.y+1.0,"object":"res://assets/objects/natural_stairs_down.png" if state["room"]==0 else "res://assets/objects/natural_stairs_up.png","cell":stairs,"dimensions":Vector2(64,64)})
		var boss: Dictionary=definition["boss"]["point"]
		if state["node"]==boss["node"] and state["room"]==boss["room"] and "first_boss" not in state["cleared"]:
			var position_on_map := Vector2(WorldExpedition.point(boss["cell"]))
			ordered.append({"bottom":position_on_map.y+1.0,"object":"res://assets/monsters/gate_beast/idle.png","cell":position_on_map,"dimensions":Vector2(96,80)})
	for event in FirstRegion.residents_for(saved):
		if event["kind"]=="recruit" and FirstRegion.joined(saved,event["actor"]) and event["actor"]!=speaking_actor:continue
		var cell := Vector2(FirstRegion.event_cell(saved,event))-origin
		if event["kind"]=="treasure":
			ordered.append({"bottom":cell.y+1.0,"object":"res://assets/objects/chest.png","cell":cell,"dimensions":Vector2(32,32),"region":Rect2(32 if event["id"] in state["opened"] else 0,0,32,32)})
		else:
			var key := FirstRegion.event_key(state,event)
			cell+=npc_offsets.get(key,Vector2.ZERO)
			ordered.append({"bottom":cell.y+1.0,"event":event,"cell":cell,"facing":FirstRegion.event_facing(saved,event)})
	ordered.append({"bottom":here.y+1.0,"player":true,"cell":here})
	ordered.sort_custom(func(a:Dictionary,b:Dictionary)->bool:return float(a["bottom"])<float(b["bottom"]))
	for item in ordered:
		if item.has("layer"):_draw_layer(item["layer"])
		elif item.has("object"):_object(item["object"],item["cell"],item["dimensions"],item.get("region",Rect2()))
		elif item.has("player"):
			for actor in saved["party"]:
				if actor["id"]==saved.get("leader_id","pc_01"):_person(actor,item["cell"],int(state["facing"]),walk_frame)
		else:
			var event: Dictionary=item["event"]
			_person({},item["cell"],item["facing"],1 if npc_offsets.has(FirstRegion.event_key(state,event)) else 0,str(event.get("sprite",event.get("actor","npc_farmer"))))
