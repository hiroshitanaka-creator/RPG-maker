class_name RpgBattleView
extends Control
## 登録された実寸の敵と48pxの味方を、場所に合う背景へ描く。
var members: Array = []
var enemy_ids: Array = []
var definitions: Dictionary = {}
var enemy_hp: Dictionary = {}
var party_hp: Dictionary = {}
var frames: Dictionary = {}
var background := "plains"
var selected_actor := ""
var target_actor := ""
var acting_actor := ""
var effect_target := ""
var effect_code := ""
var effect_amount := 0
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

func party_rect(index: int) -> Rect2:
	# 48pxの絵を縮小せず、3人・4人とも隊列順で56px間隔にする。
	var top := 36.0 + (4 - members.size()) * 28.0
	return Rect2(448,top+index*56,48,48)

func actor_rect(identifier: String) -> Rect2:
	for i in range(members.size()):
		if members[i]["id"]==identifier:return party_rect(i)
	var positions: Array[Vector2]=[Vector2(24,169),Vector2(124,132),Vector2(224,173)]
	for i in range(enemy_ids.size()):
		if identifier!="enemy_%02d" % (i+1):continue
		var texture := _enemy_texture(enemy_ids[i])
		var feet: Vector2=Vector2(64,183) if enemy_ids.size()==1 else positions[mini(i,2)]
		return Rect2(feet-Vector2(0,texture.get_height()),texture.get_size())
	return Rect2()

func effect_anchor(identifier: String) -> Vector2:
	return actor_rect(identifier).get_center()+_impact(identifier)

func cursor_rect(identifier: String) -> Rect2:
	var rect := actor_rect(identifier)
	return Rect2(Vector2(rect.position.x-18,rect.get_center().y-8)+_impact(identifier),Vector2(16,16))

func focus_target(identifier: String) -> void:
	target_actor=identifier
	queue_redraw()

func _enemy_texture(identifier: String) -> Texture2D:
	return _texture("res://assets/monsters/%s/idle.png" % definitions[identifier].get("sprite_id",identifier))

func _draw() -> void:
	var backdrop := _texture("res://assets/backgrounds/"+background+".png")
	# 縦隊の足元を草地に置くため、空と前景の花を避けた範囲を表示する。
	if background=="plains":draw_texture_rect_region(backdrop,Rect2(Vector2.ZERO,size),Rect2(180,128,512.0/3.0,96))
	else:draw_texture_rect(backdrop,Rect2(Vector2.ZERO,size),false)
	for i in range(enemy_ids.size()):
		var identifier := "enemy_%02d" % (i+1)
		var rect := actor_rect(identifier)
		rect.position+=_impact(identifier)
		var tint := Color.WHITE if int(enemy_hp.get(identifier,1))>0 else Color(1,1,1,0.25)
		draw_texture_rect(_enemy_texture(enemy_ids[i]),rect,false,tint)
	for i in range(members.size()):
		var member: Dictionary=members[i]
		var identifier: String=member["id"]
		var fallen := int(party_hp.get(identifier,member.get("hp",1)))<=0
		var visual := CharacterVisuals.appearance(member,"battle",2 if fallen else int(frames.get(identifier,0)))
		if not visual["available"]:continue
		var rect := party_rect(i)
		rect.position+=_impact(identifier)
		if identifier==acting_actor or (acting_actor.is_empty() and identifier==selected_actor):
			draw_style_box(_highlight(),Rect2(rect.position+Vector2(3,42),Vector2(42,5)))
		draw_texture_rect_region(_texture(visual["path"]),rect,visual["region"],Color(0.6,0.6,0.6,0.7) if fallen else Color.WHITE)
	var cursor := target_actor if not target_actor.is_empty() else selected_actor
	if not actor_rect(cursor).size.is_zero_approx():
		draw_texture_rect(_texture("res://assets/ui/cursor_bright.png"),cursor_rect(cursor),false)
	if not actor_rect(effect_target).size.is_zero_approx():
		var center := effect_anchor(effect_target)
		if effect_code in ["heal","revive"]:draw_circle(center,17,Color(0.6,1,0.65,0.35))
		if effect_code=="damage":draw_line(center+Vector2(-13,13),center+Vector2(13,-13),Color(1,0.96,0.65),3)
		if effect_code in ["damage","heal","revive"]:
			var number := str(effect_amount)
			var point := center+Vector2(-8,-10)
			draw_string_outline(ThemeDB.fallback_font,point,number,HORIZONTAL_ALIGNMENT_LEFT,-1,14,3,Color.BLACK)
			draw_string(ThemeDB.fallback_font,point,number,HORIZONTAL_ALIGNMENT_LEFT,-1,14,Color.WHITE)

func _highlight() -> StyleBoxFlat:
	var highlight := StyleBoxFlat.new()
	highlight.bg_color=Color(1,0.88,0.3,0.75)
	highlight.set_corner_radius_all(3)
	return highlight
