class_name WorldShoreline
extends RefCounted
## 全世界共通の水際。通行判定へは触れず、原寸の32px接続タイルだけを描く。
static var _data: Dictionary={}
static var _atlas: Texture2D

static func data() -> Dictionary:
	if _data.is_empty():_data=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/shoreline.json")))
	return _data

static func region(cell: Vector2i) -> Rect2:
	var source := data()
	if cell.x<0 or cell.y<0 or cell.x>=int(source["width"]) or cell.y>=int(source["height"]):return Rect2()
	var mask: int=source["mask_rows"][cell.y][cell.x]
	if mask not in source["visible_masks"]:return Rect2()
	var index: int=((cell.y%4)*4+cell.x%4)*512+mask
	return Rect2(index%32*32,(index>>5)*32,32,32)

static func draw_at(canvas: CanvasItem, cell: Vector2i, target: Rect2) -> void:
	var source := region(cell)
	if source.size==Vector2.ZERO:return
	canvas.draw_texture_rect_region(texture(),target,source)

static func texture() -> Texture2D:
	if _atlas!=null:return _atlas
	var colors := (load("res://assets/tiles/world_connected_water.png") as Texture2D).get_image()
	var source := (load("res://assets/tiles/world_water_alpha_mask.png") as Texture2D).get_image()
	colors.convert(Image.FORMAT_RGBA8);source.convert(Image.FORMAT_RGBA8)
	var raw := source.get_data();var alpha := PackedByteArray();alpha.resize(1024*512*2)
	for i in range(1024*512):alpha[i*2]=255;alpha[i*2+1]=255 if raw[i*4]>128 else 0
	var mask := Image.create_from_data(1024,512,false,Image.FORMAT_LA8,alpha)
	var composed := Image.create(1024,8192,false,Image.FORMAT_RGBA8);composed.fill(Color(0,0,0,0))
	for phase in range(16):
		var part := colors.get_region(Rect2i(0,phase*512,1024,512))
		composed.blit_rect_mask(part,mask,Rect2i(0,0,1024,512),Vector2i(0,phase*512))
	_atlas=ImageTexture.create_from_image(composed)
	return _atlas
