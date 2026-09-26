class_name RpgBattleView
extends Control
## 登録された実寸の敵と48pxの味方を、場所に合う背景へ描く。
var members: Array = []
var enemy_ids: Array = []
var definitions: Dictionary = {}
var enemy_hp: Dictionary = {}
var frames: Dictionary = {}
var background := "plains"
var selected_actor := ""
var effect_target := ""
var effect_code := ""
var _textures: Dictionary = {}
var _time := 0.0

func _ready() -> void:
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST

func _process(delta: float) -> void:
	_time+=delta
	if not effect_code.is_empty():queue_redraw()

func _texture(path: String) -> Texture2D:
	if not _textures.has(path):_textures[path]=load(path)
	return _textures[path]

func _impact(identifier: String) -> Vector2:
	return Vector2(round(sin(_time*70.0)*3.0),0) if identifier==effect_target and effect_code in ["damage","fallen"] else Vector2.ZERO

func _draw() -> void:
	draw_texture_rect(_texture("res://assets/backgrounds/"+background+".png"),Rect2(Vector2.ZERO,size),false)
	var positions: Array[Vector2]=[Vector2(24,169),Vector2(124,132),Vector2(224,173)]
	for i in range(enemy_ids.size()):
		var identifier: String=enemy_ids[i]
		var definition: Dictionary=definitions[identifier]
		var texture := _texture("res://assets/monsters/%s/idle.png" % definition.get("sprite_id",identifier))
		var dimensions := Vector2(texture.get_width(),texture.get_height())
		var position_on_map: Vector2=positions[mini(i,2)]
		if enemy_ids.size()==1:position_on_map=Vector2(64,183)
		var actor_id := "enemy_%02d" % (i+1)
		var tint := Color.WHITE if int(enemy_hp.get(actor_id,1))>0 else Color(1,1,1,0.25)
		draw_texture_rect(texture,Rect2(Vector2(position_on_map.x,position_on_map.y-dimensions.y)+_impact(actor_id),dimensions),false,tint)
	for i in range(members.size()):
		var member: Dictionary=members[i]
		var visual := CharacterVisuals.appearance(member,"battle",int(frames.get(member["id"],0)))
		if not visual["available"]:continue
		var position_on_map := Vector2(368 if i%2==0 else 424,64+i*24)+_impact(member["id"])
		draw_texture_rect_region(_texture(visual["path"]),Rect2(position_on_map,Vector2(48,48)),visual["region"])
		if selected_actor==member["id"]:
			draw_texture_rect(_texture("res://assets/ui/cursor_bright.png"),Rect2(position_on_map+Vector2(40,13),Vector2(16,16)),false)
		if member["id"]==effect_target and effect_code in ["heal","revive"]:
			draw_circle(position_on_map+Vector2(24,26),17,Color(0.6,1,0.65,0.16))
