class_name RpgBattleView
extends Control
## 背景も味方も原寸で表示する。背景の上移動で足元の地面を確保する。
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
const BACKGROUND_LAYOUT := {
	"plains": [64,28], "forest": [56,40], "cave": [56,44], "tower": [48,48],
	"desert": [48,34], "sea": [48,48], "sky": [48,54], "castle": [48,64],
	"snowfield": [16,28], "volcano": [8,28], "ruins": [12,28],
	"underworld": [8,28], "temple": [44,84], "final_land": [0,28],
}

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
	# 48pxのまま下の人を右へ寄せる。背景ごとの床面に足を置き、顔を隠さない。
	var offset := (4-members.size())*Vector2(24,14)
	var top: int = BACKGROUND_LAYOUT.get(background,[48,48])[1]
	return Rect2(Vector2(304+index*48,top+index*28)+offset,Vector2(48,48))

func background_offset() -> Vector2:
	return Vector2(0,-int(BACKGROUND_LAYOUT.get(background,[48,48])[0]))

func actor_rect(identifier: String) -> Rect2:
	for i in range(members.size()):
		if members[i]["id"]==identifier:return party_rect(i)
	var positions: Array[Vector2]=[Vector2(24,145),Vector2(124,110),Vector2(200,151)]
	for i in range(enemy_ids.size()):
		if identifier!="enemy_%02d" % (i+1):continue
		var texture := _enemy_texture(enemy_ids[i])
		var feet: Vector2=Vector2(64,142) if enemy_ids.size()==1 else positions[mini(i,2)]
		feet.y=maxf(feet.y,maxf(party_rect(0).end.y+4,texture.get_height()+28))
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
	# 原寸で背景別に上へ移す。下端は文字窓の裏に収まり、空や天井の一部を残す。
	draw_texture(backdrop,background_offset())
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
		var radius := minf(actor_rect(effect_target).size.x,actor_rect(effect_target).size.y)*0.35
		if effect_code in ["heal","revive"]:draw_circle(center,radius,Color(0.6,1,0.65,0.35))
		if effect_code=="damage":draw_line(center+Vector2(-radius,radius),center+Vector2(radius,-radius),Color(1,0.96,0.65),2)
		if effect_code in ["damage","heal","revive"]:
			var number := str(effect_amount)
			var point := center+Vector2(-8,-10)
			if effect_target.begins_with("pc_"):point=Vector2(actor_rect(effect_target).position.x-38,center.y+5)
			draw_string_outline(get_theme_default_font(),point,number,HORIZONTAL_ALIGNMENT_LEFT,-1,12,3,Color.BLACK)
			draw_string(get_theme_default_font(),point,number,HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color.WHITE)

func _highlight() -> StyleBoxFlat:
	var highlight := StyleBoxFlat.new()
	highlight.bg_color=Color(1,0.88,0.3,0.75)
	highlight.set_corner_radius_all(3)
	return highlight
