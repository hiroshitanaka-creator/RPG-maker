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
var _layout_ids: Array = []
var _enemy_feet: Array[Vector2] = []
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
	# 足元だけを後続の人物の後ろへ重ねる。描画順は隊列順で、下の人が手前。
	return Rect2(Vector2(356+index*20,40+index*34),Vector2(72,72))

func background_offset() -> Vector2:
	return Vector2.ZERO

func actor_rect(identifier: String) -> Rect2:
	for i in range(members.size()):
		if members[i]["id"]==identifier:
			var rect := party_rect(i)
			if identifier==acting_actor:rect.position.x-=30
			return rect
	for i in range(enemy_ids.size()):
		if identifier!="enemy_%02d" % (i+1):continue
		var source := enemy_region(enemy_ids[i])
		var dimensions := source.size*0.75
		var feet := enemy_feet(i)
		return Rect2(feet-Vector2(dimensions.x/2.0,dimensions.y),dimensions)
	return Rect2()

func enemy_feet(index: int) -> Vector2:
	if _layout_ids!=enemy_ids:_arrange_enemies()
	return _enemy_feet[index]

func _arrange_enemies() -> void:
	const POINTS := {
		1:[Vector2(170,196)],
		2:[Vector2(120,160),Vector2(220,196)],
		3:[Vector2(215,134),Vector2(90,178),Vector2(180,200)],
		4:[Vector2(110,120),Vector2(215,134),Vector2(90,178),Vector2(180,200)],
		5:[Vector2(110,120),Vector2(215,134),Vector2(90,178),Vector2(180,200),Vector2(270,186)]
	}
	_layout_ids=enemy_ids.duplicate();_enemy_feet.assign(POINTS[enemy_ids.size()])
	if enemy_ids.size()==5:return
	var rectangles: Array[Rect2]=[]
	var order: Array[int]=[]
	var collision := false
	for i in range(enemy_ids.size()):
		var dimensions := enemy_region(enemy_ids[i]).size*0.75
		var rectangle := Rect2(_enemy_feet[i]-Vector2(dimensions.x/2,dimensions.y),dimensions)
		for previous in rectangles:
			if rectangle.grow(3).intersects(previous.grow(3)):collision=true
		rectangles.append(rectangle);order.append(i)
	if not collision:return
	# 足元の高さと元の左右順を保ち、縦に重なる組だけに必要な横幅を取る。
	order.sort_custom(func(a: int,b: int)->bool:return _enemy_feet[a].x<_enemy_feet[b].x)
	var minimum: Array[float]=[]
	var maximum: Array[float]=[]
	for rectangle in rectangles:
		minimum.append(maxf(60,24+rectangle.size.x/2))
		maximum.append(minf(300,320-rectangle.size.x/2))
	for rank in range(order.size()):
		var i: int=order[rank]
		for earlier in range(rank):
			var j: int=order[earlier]
			minimum[i]=maxf(minimum[i],minimum[j]+_enemy_gap(rectangles[j],rectangles[i]))
	for rank in range(order.size()-1,-1,-1):
		var i: int=order[rank]
		for earlier in range(rank):
			var j: int=order[earlier]
			maximum[j]=minf(maximum[j],maximum[i]-_enemy_gap(rectangles[j],rectangles[i]))
	for i in range(order.size()):
		if minimum[i]>maximum[i]:
			push_error("敵の表示幅が左側の配置領域に収まりません。編成と原画寸法の確認が必要です。")
			return
	var shift_sum := 0.0
	for rank in range(order.size()):
		var i: int=order[rank]
		var lower := minimum[i]
		for earlier in range(rank):
			var j: int=order[earlier]
			lower=maxf(lower,_enemy_feet[j].x+_enemy_gap(rectangles[j],rectangles[i]))
		var original_x := _enemy_feet[i].x
		_enemy_feet[i].x=clampf(original_x,lower,maximum[i])
		shift_sum+=original_x-_enemy_feet[i].x
	var minimum_shift := -INF;var maximum_shift := INF
	for i in range(_enemy_feet.size()):
		minimum_shift=maxf(minimum_shift,maxf(60,24+rectangles[i].size.x/2)-_enemy_feet[i].x)
		maximum_shift=minf(maximum_shift,minf(300,320-rectangles[i].size.x/2)-_enemy_feet[i].x)
	var shift := clampf(shift_sum/_enemy_feet.size(),minimum_shift,maximum_shift)
	for i in range(_enemy_feet.size()):_enemy_feet[i].x+=shift

func _enemy_gap(a: Rect2, b: Rect2) -> float:
	var outer_a := a.grow(3);var outer_b := b.grow(3)
	return (a.size.x+b.size.x)/2+6 if outer_a.position.y<outer_b.end.y and outer_b.position.y<outer_a.end.y else 1.0

func enemy_draw_order() -> Array[int]:
	var order: Array[int]=[]
	for i in range(enemy_ids.size()):order.append(i)
	order.sort_custom(func(a: int,b: int)->bool:return enemy_feet(a).y<enemy_feet(b).y)
	return order

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
	for i in enemy_draw_order():
		var identifier := "enemy_%02d" % (i+1)
		var rect := actor_rect(identifier)
		rect.position+=_impact(identifier)
		var tint := Color.WHITE if int(enemy_hp.get(identifier,1))>0 else Color(1,1,1,0.25)
		draw_texture_rect_region(_enemy_texture(enemy_ids[i]),rect,enemy_region(enemy_ids[i]),tint)
	# 演出は味方より奥へ描く。頭や顔へ色を重ねず、対象座標は共通のまま使う。
	_draw_feedback()
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
		draw_texture_rect_region(_texture(visual["path"]),rect,visual["region"],Color(0.6,0.6,0.6,1.0) if fallen else Color.WHITE)
	# 対象カーソルは身体の裏へ隠さず、頭・顔の外側に描く。
	var cursor := target_actor if not target_actor.is_empty() else selected_actor
	if not actor_rect(cursor).size.is_zero_approx():
		draw_texture_rect(_texture("res://assets/ui/cursor_bright.png"),cursor_rect(cursor),false)

func _draw_feedback() -> void:
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
