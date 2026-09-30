class_name RpgMenuColors
extends RefCounted
## 採用済みの色だけを既存コントロールへ当てる。余白・文字寸法・接続・使用可否は保持する。
const BLUE := Color("101c50")
const MUTED := Color("9aa6c4")

static func box(source: StyleBox, background: Color, border: bool, radius: int = 2) -> StyleBoxFlat:
	var result := StyleBoxFlat.new()
	result.bg_color=background;result.border_color=Color.WHITE
	result.set_border_width_all(1 if border else 0);result.set_corner_radius_all(radius)
	if source!=null:
		for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:result.set_content_margin(side,source.get_margin(side))
	return result

static func window(source: StyleBox = null) -> StyleBoxFlat:
	return box(source,BLUE,true,3)

static func controls(node: Node) -> Array[Node]:
	var result: Array[Node]=[node]
	for child in node.get_children(true):result.append_array(controls(child))
	return result

static func apply(root: Control) -> void:
	var themed := root.theme.duplicate() as Theme
	themed.default_font=RpgFonts.get_font()
	themed.set_color("font_color","Label",Color.WHITE)
	themed.set_color("default_color","RichTextLabel",Color.WHITE)
	themed.set_stylebox("panel","FirstRegionAtlas",window())
	themed.set_stylebox("panel","TooltipPanel",window(root.get_theme_stylebox("panel","TooltipPanel")))
	themed.set_color("font_color","TooltipLabel",Color.WHITE)
	themed.set_font("font","TooltipLabel",RpgFonts.get_font())
	# 選択リストの内部に後から作られるスクロールバーにも同じ色を渡す。
	for kind in ["VScrollBar","HScrollBar"]:
		for state in ["scroll","scroll_focus","grabber","grabber_highlight","grabber_pressed"]:
			var color := BLUE if state.begins_with("scroll") else Color("bdc7d3") if state=="grabber" else Color.WHITE
			themed.set_stylebox(state,kind,box(root.get_theme_stylebox(state,kind),color,state=="scroll_focus"))
	root.theme=themed
	for control in controls(root):
		if control is Label:control.add_theme_color_override("font_color",Color.WHITE)
		if control is RichTextLabel:control.add_theme_color_override("default_color",Color.WHITE)
		if control is PanelContainer:
			control.add_theme_stylebox_override("panel",window(control.get_theme_stylebox("panel")))
		if control is Button:
			for state in ["normal","hover","pressed","focus","disabled"]:
				var color := Color(1,1,1,0.10) if state in ["hover","pressed"] else Color(0,0,0,0) if state=="focus" else BLUE
				control.add_theme_stylebox_override(state,box(control.get_theme_stylebox(state),color,state=="focus"))
			for key in ["font_color","font_hover_color","font_pressed_color","font_focus_color","icon_normal_color","icon_hover_color","icon_pressed_color","icon_focus_color"]:
				control.add_theme_color_override(key,Color.WHITE)
			for key in ["font_disabled_color","icon_disabled_color"]:control.add_theme_color_override(key,MUTED)
		if control is PopupMenu:
			var popup_theme := themed.duplicate() as Theme
			popup_theme.set_font("font","PopupMenu",RpgFonts.get_font())
			popup_theme.set_font_size("font_size","PopupMenu",control.get_theme_font_size("font_size"))
			popup_theme.set_stylebox("panel","PopupMenu",window(control.get_theme_stylebox("panel")))
			popup_theme.set_stylebox("hover","PopupMenu",box(control.get_theme_stylebox("hover"),Color(1,1,1,0.10),true))
			for key in ["font_color","font_hover_color","font_accelerator_color","font_separator_color"]:popup_theme.set_color(key,"PopupMenu",Color.WHITE)
			popup_theme.set_color("font_disabled_color","PopupMenu",MUTED)
			control.theme=popup_theme
		if control is ScrollBar:
			for state in ["scroll","scroll_focus","grabber","grabber_highlight","grabber_pressed"]:
				var color := BLUE if state.begins_with("scroll") else Color("bdc7d3") if state=="grabber" else Color.WHITE
				control.add_theme_stylebox_override(state,box(control.get_theme_stylebox(state),color,state=="scroll_focus"))
		if control is TextEdit or control is LineEdit:
			for state in ["normal","focus","read_only"]:
				control.add_theme_stylebox_override(state,box(control.get_theme_stylebox(state),Color(0,0,0,0) if state=="focus" else BLUE,true))
			for key in ["font_color","font_selected_color","caret_color"]:control.add_theme_color_override(key,Color.WHITE)
			control.add_theme_color_override("font_readonly_color",MUTED)
			control.add_theme_color_override("font_placeholder_color",MUTED)
			control.add_theme_color_override("selection_color",Color("37528a"))
