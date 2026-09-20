class_name BuildIdentity
extends RefCounted

static var _cached: Dictionary = {}

static func current() -> Dictionary:
	if not _cached.is_empty():
		return _cached.duplicate(true)
	var paths: Array[String] = ["project.godot","assets/registry.json","assets/palette/base.gpl"]
	for directory in ["scripts","scenes","data"]:
		_collect(directory,paths)
	var registry: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/registry.json"))
	for entry in registry["assets"]:
		paths.append(entry["path"])
	paths.sort()
	var version := Engine.get_version_info()
	var engine: String = version["string"]+" ["+str(version["hash"]).left(9)+"]"
	var input := "rpg-v1-build-1\n"+engine+"\n"
	for path in paths:
		input += path+"\t"+FileAccess.get_sha256("res://"+path)+"\n"
	_cached = {"version":1,"id":input.sha256_text(),"engine":engine,"files":paths.size()}
	return _cached.duplicate(true)

static func _collect(directory: String, paths: Array[String]) -> void:
	for file in DirAccess.get_files_at("res://"+directory):
		if file.get_extension() in ["gd","tscn","json"]:
			paths.append(directory.path_join(file))
	for child in DirAccess.get_directories_at("res://"+directory):
		_collect(directory.path_join(child),paths)
