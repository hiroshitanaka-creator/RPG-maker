extends SceneTree
const T=preload("res://scripts/game/equipment_save_transaction.gd")
func _initialize() -> void:
	var config: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	var result: Dictionary
	if config.operation=="release":
		var unloaded := GDExtensionManager.unload_extension("res://addons/equipment_save_io/equipment_save_io.gdextension")
		var platform := "windows" if OS.get_name()=="Windows" else "linux"
		var suffix := ".dll" if platform=="windows" else ".so"
		var binary := ProjectSettings.globalize_path("res://addons/equipment_save_io/bin/equipment_save_io.%s.template_release.x86_64%s" % [platform,suffix])
		var path: String=config.root.path_join("release.gdextension")
		var f := FileAccess.open(path,FileAccess.WRITE)
		f.store_string('[configuration]\nentry_symbol="equipment_save_io_init"\ncompatibility_minimum="4.5"\n[libraries]\n'+platform+'.debug.x86_64="'+binary.replace("\\","/")+'"\n');f.close()
		var loaded := GDExtensionManager.load_extension(path)
		var io: RefCounted=ClassDB.instantiate("EquipmentSaveIO") if ClassDB.class_exists("EquipmentSaveIO") else null
		result={"ok":unloaded==0 and loaded==0 and io!=null and io.configure(config.root),"unload":unloaded,"load":loaded,"binary_sha256":FileAccess.get_sha256(binary)}
	else:
		var t := T.new(config.root,{},"g1")
		result=t.read_bytes(config.root.path_join("source.json"))
	var output := FileAccess.open(config.root.path_join("result.json"),FileAccess.WRITE);output.store_string(JSON.stringify(result));output.close()
	print("BINARY_PROBE: ",JSON.stringify(result));quit(0)
