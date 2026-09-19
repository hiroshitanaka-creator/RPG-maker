class_name CharacterVisuals
extends RefCounted

static var _source: Dictionary = {}


static func data() -> Dictionary:
	if _source.is_empty():
		var value: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/character_visuals.json"))
		if value is Dictionary:
			_source = value
	return _source


static func appearance(actor: Dictionary, kind: String, frame: int = 0, facing: int = 0) -> Dictionary:
	var definition: Dictionary = data().get("actors",{}).get(actor.get("id",""),{})
	var form: String = actor.get("monster_form","")
	var path: String = definition.get(kind,"")
	if not form.is_empty():
		path = definition.get("forms",{}).get(form,{}).get(kind,"")
		if path.is_empty():
			path = data().get("shared_forms",{}).get(form,{}).get(kind,"")
	var exists := not path.is_empty() and ResourceLoader.exists("res://"+path)
	var region := Rect2(clampi(frame,0,2)*48,0,48,48)
	if kind == "walk":
		region = Rect2([0,1,0,2][posmod(frame,4)]*32,clampi(facing,0,3)*48,32,48)
	return {"path":"res://"+path if exists else "","available":exists,"region":region,"form":form,"kind":kind}
