class_name ErosionStageMark
extends Control
## 色だけに頼らず、三角・ひし形・交差印で侵蝕の段階を示す。
var member: Dictionary = {}

func _init() -> void:
	custom_minimum_size=Vector2(7,7)
	size_flags_vertical=Control.SIZE_SHRINK_CENTER
	mouse_filter=Control.MOUSE_FILTER_PASS

func stage_name() -> String:
	return "不可逆" if bool(member.get("irreversible",false)) else GameSession.erosion_stage(int(member.get("erosion",0)))

func _ready() -> void:
	tooltip_text="侵蝕：%s（%d）" % [stage_name(),int(member.get("erosion",0))]

func _draw() -> void:
	var colors := {"pc_01":"d4f3ff","pc_02":"ffd7bd","pc_03":"fff3c7","pc_04":"f0dcff"}
	var color := Color(str(colors.get(member.get("id",""),"ffffff")))
	match stage_name():
		"兆候":
			for y in range(6):
				var extent := int(y/2)
				draw_rect(Rect2(3-extent,y,1,1),color)
				draw_rect(Rect2(3+extent,y,1,1),color)
			draw_rect(Rect2(0,6,7,1),color)
		"変異":
			for y in range(7):
				var extent := 3-absi(y-3)
				draw_rect(Rect2(3-extent,y,extent*2+1,1),color)
		"不可逆":
			for i in range(7):
				draw_rect(Rect2(i,i,1,1),color)
				draw_rect(Rect2(6-i,i,1,1),color)
			draw_rect(Rect2(2,2,3,3),color)
