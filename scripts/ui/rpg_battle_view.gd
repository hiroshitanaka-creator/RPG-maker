class_name RpgBattleView
extends Control
## 目標画像の配置。背景は全画面、96px素材の味方は高さの1/4に当たる72px表示。
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
var _enemy_regions: Dictionary = {}
var _time := 0.0
const BACKGROUND_LAYOUT := {
	"plains": [0,68], "forest": [0,68], "cave": [0,80], "tower": [0,80],
	"desert": [0,68], "sea": [0,80], "sky": [0,80], "castle": [0,88],
	"snowfield": [0,68], "volcano": [0,68], "ruins": [0,68],
	"underworld": [0,68], "temple": [0,104], "final_land": [0,68],
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
	# 透明余白を含む72pxの描画枠も重ねない。人数が少ない場合は列を中央へ寄せる。
	var offset := (4-members.size())*Vector2(43,14)
	return Rect2(Vector2(175+index*87,56+index*28)+offset,Vector2(72,72))

func background_offset() -> Vector2:
	return Vector2.ZERO

func actor_rect(identifier: String) -> Rect2:
	for i in range(members.size()):
		if members[i]["id"]==identifier:
			var rect := party_rect(i)
			if identifier==acting_actor:rect.position.x-=12
			return rect
	var positions: Array[Vector2]=[Vector2(112,184),Vector2(24,212),Vector2(112,204),Vector2(16,184)]
	for i in range(enemy_ids.size()):
		if identifier!="enemy_%02d" % (i+1):continue
		var source := enemy_region(enemy_ids[i])
		var dimensions := source.size*minf(72.0/source.size.y,96.0/source.size.x)
		var feet: Vector2=Vector2(116,192) if enemy_ids.size()==1 else positions[mini(i,3)]
		return Rect2(feet-Vector2(0,dimensions.y),dimensions)
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

func enemy_region(identifier: String) -> Rect2:
	if not _enemy_regions.has(identifier):_enemy_regions[identifier]=Rect2(_enemy_texture(identifier).get_image().get_used_rect())
	return _enemy_regions[identifier]

func _draw() -> void:
	var backdrop := _texture("res://assets/backgrounds/"+background+".png")
	# 原寸の全画像を画面全体に描き、右下と半透明の文字窓の後ろまで残す。
	draw_texture(backdrop,background_offset())
	for i in range(enemy_ids.size()):
		var identifier := "enemy_%02d" % (i+1)
		var rect := actor_rect(identifier)
		rect.position+=_impact(identifier)
		var tint := Color.WHITE if int(enemy_hp.get(identifier,1))>0 else Color(1,1,1,0.25)
		draw_texture_rect_region(_enemy_texture(enemy_ids[i]),rect,enemy_region(enemy_ids[i]),tint)
	for i in range(members.size()):
		var member: Dictionary=members[i]
		var identifier: String=member["id"]
		var fallen := int(party_hp.get(identifier,member.get("hp",1)))<=0
		var visual := CharacterVisuals.appearance(member,"battle",2 if fallen else int(frames.get(identifier,0)))
		if not visual["available"]:continue
		var rect := actor_rect(identifier)
		rect.position+=_impact(identifier)
		if identifier==acting_actor or (acting_actor.is_empty() and identifier==selected_actor):
			draw_style_box(_highlight(),Rect2(rect.position+Vector2(6,66),Vector2(60,5)))
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
