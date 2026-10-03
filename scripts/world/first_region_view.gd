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

static func ground_layer(layer: Dictionary) -> bool:
	var kind := str(layer["name"]).trim_prefix("natural_").trim_prefix("bright_")
	# 城下町の門（gate_open）は通り抜ける場所なので、人物より奥に描く（2026年9月28日、依頼者決定）
	return kind in ["gate_open","地面","dirt","cobble","shore","hills","forest","mountains","river","壁","敷物","接続水域","64px岩壁・丸い湖・床の自動接続","dirt_patch","pebbles","flowers_white","flowers_yellow","flowers_pink","tufts","leaves","overgrown_grass","flowerbed","cabbage","carrots","wheat","mushrooms","floor_pattern","bridge","rope_bridge"]

func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	clip_contents=true
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	_map=FirstRegionPresentation.map_for(saved["overworld"])
	for layer in _map.get("layers",[]):
		if layer["cells"].is_empty():continue
		if ground_layer(layer):
			_ground.append(layer)
		else:
			var bottom := 0
			for entry in layer["cells"]:bottom=maxi(bottom,int(entry[1])+1)
			_objects.append({"bottom":float(bottom),"layer":layer})
	for tile in _map.get("tiles",{}).values():_texture("res://"+str(tile["path"]))

func _texture(path: String) -> Texture2D:
	if not _textures.has(path):_textures[path]=WorldShoreline.texture() if path=="res://assets/tiles/world_connected_water.png" else load(path)
	return _textures[path]

func _screen(cell: Vector2) -> Vector2:
	return ((cell-_camera)*32.0).round()

func _draw_layer(layer: Dictionary) -> void:
	var cell_size := float(layer.get("cell_size",32))
	for entry in layer["cells"]:
		var position_on_map := _screen(Vector2(entry[0],entry[1])*cell_size/32.0)
		if position_on_map.x < -32 or position_on_map.y < -32 or position_on_map.x > size.x or position_on_map.y > size.y:continue
		var tile: Dictionary=_map["tiles"][entry[2]]
		var region: Array=tile["region"]
		draw_texture_rect_region(_texture("res://"+str(tile["path"])),Rect2(position_on_map,Vector2(cell_size,cell_size)),Rect2(region[0],region[1],region[2],region[3]))

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
	# 画面より小さい室内の周囲にも壁材を敷き、黒い余白を作らない。
	var surround := str(_map.get("surround","assets/tiles/natural_grass.png"))
	draw_texture_rect(_texture("res://"+surround),Rect2(Vector2.ZERO,size),true)
	# 一枚絵の背景を敷く部屋では、通行は見えない地図（layout）だけで決める。
	var backdrop: Dictionary=_map.get("backdrop",{})
	if not backdrop.is_empty():draw_texture(_texture("res://"+str(backdrop["path"])),_screen(Vector2(WorldExpedition.point(backdrop["offset"]))/32.0))
	for layer in _ground:_draw_layer(layer)
	var ordered: Array=_objects.duplicate()
	var definition := FirstRegion.data()
	var travel := FirstRegionTravel.snapshot(saved)
	if travel.get("ship_owned",false) and state.get("transport","walk")=="walk":
		if state["layer"]=="world":
			var ship := Vector2(WorldExpedition.point(travel["ship_cell"]))-origin
			ordered.append({"bottom":ship.y+1.0,"object":"res://assets/vehicles/owner_ship.png","cell":ship,"dimensions":Vector2(96,96),"region":Rect2(96,0,96,96)})
		elif state["node"]=="first_port" and state["room"]==0 and travel["ship_cell"]==FirstRegionTravel.data()["docks"][0]["ship_cell"]:
			var ship := Vector2(WorldExpedition.point(FirstRegionTravel.data()["docks"][0]["display_cell"]))
			ordered.append({"bottom":ship.y+1.0,"object":"res://assets/vehicles/owner_ship.png","cell":ship,"dimensions":Vector2(192,192),"region":Rect2(96,0,96,96)})
	if state["layer"]=="world":
		var second_port := Vector2(WorldExpedition.point(definition["second_port_entrance"]["cell"]))-origin
		ordered.append({"bottom":second_port.y+1.0,"object":"res://assets/ui/icon_town.png","cell":second_port,"dimensions":Vector2(64,64)})
		if definition.has("port_entrance"):
			var port := Vector2(WorldExpedition.point(definition["port_entrance"]["cell"]))-origin
			ordered.append({"bottom":port.y+1.0,"object":"res://assets/ui/icon_town.png","cell":port,"dimensions":Vector2(64,64)})
		if definition.has("tower_entrance"):
			var tower := Vector2(WorldExpedition.point(definition["tower_entrance"]["cell"]))-origin
			ordered.append({"bottom":tower.y+1.0,"object":"res://assets/ui/icon_tower.png","cell":tower,"dimensions":Vector2(64,64)})
		if definition.has("castle_entrance"):
			var castle := Vector2(WorldExpedition.point(definition["castle_entrance"]["cell"]))-origin
			ordered.append({"bottom":castle.y+1.0,"object":"res://assets/ui/icon_castle.png","cell":castle,"dimensions":Vector2(64,64)})
		for entry in [["village_entrance","assets/ui/icon_village.png"],["cave_entrance","assets/objects/first_cave_entrance.png"]]:
			var entrance := Vector2(WorldExpedition.point(definition[entry[0]]["cell"]))-origin
			ordered.append({"bottom":entrance.y+1.0,"object":"res://"+entry[1],"cell":entrance,"dimensions":Vector2(64,64)})
		var gate := Vector2(WorldExpedition.point(definition["gate"]["cell"]["cell"]))-origin
		ordered.append({"bottom":gate.y+1.0,"object":"res://assets/objects/natural_gate.png","cell":gate,"dimensions":Vector2(96,96),"region":Rect2(128 if saved["inventory"].get("gate_pass",0)>0 else 0,0,128,128)})
	else:
		if state["node"]=="first_forest_tower" and "forest_tower_boss" not in state["cleared"] and state["room"]==definition["tower_boss"]["point"]["room"]:
			ordered.append({"bottom":float(definition["tower_boss"]["point"]["cell"][1])+1.0,"object":"res://"+str(definition["tower_boss"]["sprite"]),"cell":Vector2(WorldExpedition.point(definition["tower_boss"]["point"]["cell"])),"dimensions":Vector2(72,72)})
		var stair: Dictionary=definition["stairs_down"]["from"] if state["room"]==0 else definition["stairs_up"]["from"]
		if state["node"]=="first_cave":
			var stairs := Vector2(WorldExpedition.point(stair["cell"]))
			_object("res://assets/objects/natural_stairs_down.png" if state["room"]==0 else "res://assets/objects/natural_stairs_up.png",stairs,Vector2(64,64))
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
	# 一枚絵の町の「上の層」：人物の足元がこの部品の足元より奥（北）にいる間だけ、人物より手前に描く。足元は人物と同じ bottom で比べる。
	var overlays: Dictionary=_map.get("overlays",{})
	if not overlays.is_empty():
		for piece in overlays["pieces"]:ordered.append({"bottom":float(piece[6])-0.5,"overlay":piece})
	ordered.sort_custom(func(a:Dictionary,b:Dictionary)->bool:return float(a["bottom"])<float(b["bottom"]))
	for item in ordered:
		if item.has("layer"):_draw_layer(item["layer"])
		elif item.has("object"):_object(item["object"],item["cell"],item["dimensions"],item.get("region",Rect2()))
		elif item.has("overlay"):
			var piece: Array=item["overlay"]
			var at := _screen(Vector2(piece[4],piece[5])/32.0)
			if at.x<size.x and at.y<size.y and at.x+piece[2]>0 and at.y+piece[3]>0:
				draw_texture_rect_region(_texture("res://"+str(overlays["path"])),Rect2(at,Vector2(piece[2],piece[3])),Rect2(piece[0],piece[1],piece[2],piece[3]))
		elif item.has("player"):
			if state.get("transport","walk")=="ship":_object("res://assets/vehicles/owner_ship.png",item["cell"],Vector2(96,96),Rect2(int(state["facing"])*96,0,96,96))
			else:
				for actor in saved["party"]:
					if actor["id"]==saved.get("leader_id","pc_01"):_person(actor,item["cell"],int(state["facing"]),walk_frame)
		else:
			var event: Dictionary=item["event"]
			_person({},item["cell"],item["facing"],1 if npc_offsets.has(FirstRegion.event_key(state,event)) else 0,str(event.get("sprite",event.get("actor","npc_farmer"))))
