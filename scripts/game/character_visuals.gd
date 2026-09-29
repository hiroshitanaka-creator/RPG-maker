class_name CharacterVisuals
extends RefCounted

static var _source: Dictionary = {}
static var _battle_sizes: Dictionary = {}


static func data() -> Dictionary:
	if _source.is_empty():
		var value: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/character_visuals.json"))
		if value is Dictionary:
			_source = value
	return _source


static func appearance(actor: Dictionary, kind: String, frame: int = 0, facing: int = 0) -> Dictionary:
	var definition: Dictionary = data().get("actors",{}).get(actor.get("id",""),{})
	var form: String = actor.get("monster_form","")
	var costume: Dictionary = definition.get("jobs",{}).get(actor.get("job_id",""),{})
	var path: String = costume.get(kind,definition.get(kind,""))
	var signs: bool = int(actor.get("erosion",0)) >= 30
	if signs and form.is_empty():
		var sign_definition: Dictionary = definition.get("erosion_signs",{})
		var job_stages: Dictionary = sign_definition.get("jobs",{}).get(actor.get("job_id",""),{})
		var stage_key := "60" if int(actor.get("erosion",0))>=60 else "30"
		path = job_stages.get(stage_key,{}).get(kind,sign_definition.get(kind,""))
	if not form.is_empty():
		path = definition.get("forms",{}).get(form,{}).get(kind,"")
		if path.is_empty():
			path = data().get("shared_forms",{}).get(form,{}).get(kind,"")
	var exists := not path.is_empty() and ResourceLoader.exists("res://"+path)
	var region := Rect2(clampi(frame,0,2)*48,0,48,48)
	if exists and kind=="battle":
		if not _battle_sizes.has(path):
			var texture := load("res://"+path) as Texture2D
			_battle_sizes[path]=Vector2(texture.get_width()/3.0,texture.get_height())
		var frame_size: Vector2=_battle_sizes[path]
		region=Rect2(Vector2(clampi(frame,0,2)*frame_size.x,0),frame_size)
	if kind == "walk":
		region = Rect2([0,1,0,2][posmod(frame,4)]*32,clampi(facing,0,3)*48,32,48)
	return {"path":"res://"+path if exists else "","available":exists,"region":region,"form":form,"kind":kind,"erosion_signs":signs}


static func battle_line(actor: Dictionary) -> String:
	if int(actor.get("erosion",0)) < 30:
		return ""
	var lines := {"pc_01":"指先の感覚が変わってきた。今の力を確かめて動く。","pc_02":"足取りがいつもと違う。無理に踏み込まないよ。","pc_03":"息の響きが変わった。仲間の声を聞いて合わせよう。","pc_04":"力の流れが揺れている。使う技は自分で選ぶ。"}
	return str(actor.get("name","仲間"))+"「"+str(lines.get(actor.get("id",""),"身体の変化を確かめてから動こう。"))+"」"
