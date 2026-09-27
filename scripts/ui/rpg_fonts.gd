class_name RpgFonts
extends RefCounted
## 2026年9月27日に依頼者がNoto Sans JPを正式採用。OS字体への代替は行わない。
const PATHS := {
	"notosansjp":"res://assets/fonts/notosansjp/NotoSansJP.ttf",
	"dotgothic16":"res://assets/fonts/dotgothic16/DotGothic16-Regular.ttf",
}
const DEFAULT := "notosansjp"
static var _fonts: Dictionary = {}

static func get_font(identifier: String = DEFAULT) -> Font:
	if not _fonts.has(identifier):
		var base := load(PATHS[identifier]) as FontFile
		base.allow_system_fallback=false
		var variation := FontVariation.new()
		variation.base_font=base
		# 字形を潰さず、字体に含まれる上下の余白だけを詰める。
		variation.spacing_top=-2
		variation.spacing_bottom=-2
		if identifier=="dotgothic16":
			base.antialiasing=TextServer.FONT_ANTIALIASING_NONE
			base.hinting=TextServer.HINTING_NONE
			base.oversampling=1.0
		else:
			variation.variation_opentype={TextServerManager.get_primary_interface().name_to_tag("wght"):500.0}
		_fonts[identifier]=variation
	return _fonts[identifier]
