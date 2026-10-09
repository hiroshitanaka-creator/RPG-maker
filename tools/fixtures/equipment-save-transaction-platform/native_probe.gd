extends SceneTree
func _initialize() -> void:
	var config: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	var result: Dictionary={"ok":false,"reason_code":"native_unavailable"}
	var io: RefCounted
	if ClassDB.class_exists("EquipmentSaveIO"):io=ClassDB.instantiate("EquipmentSaveIO")
	if io!=null and io.configure(config.root):
		var tx: String=config.root.path_join("transactions/native-probe")
		match config.operation:
			"path":result={"ok":io.path_ok(config.path),"reason_code":"path_result"}
			"identity":result=io.inspect_identity(config.path)
			"roundtrip":
				if io.make_directories(config.path.get_base_dir()) and io.acquire_lock(tx).ok:
					var opened: Dictionary=io.open_write(config.path,false)
					if opened.ok:
						var bytes: PackedByteArray="保存 native exact bytes".to_utf8_buffer()
						var written: Dictionary=io.write_exact(opened.handle,bytes)
						var flushed: Dictionary=io.flush(opened.handle)
						var closed: Dictionary=io.close_file(opened.handle)
						var renamed: Dictionary=io.rename_file(config.path,config.path+".done",false)
						var reading: Dictionary=io.open_read(config.path+".done")
						if reading.ok:
							var read: Dictionary=io.read_all(reading.handle)
							var read_closed: Dictionary=io.close_file(reading.handle)
							result={"ok":written.ok and flushed.ok and closed.ok and renamed.ok and read.ok and read_closed.ok and read.bytes==bytes,"identity":io.inspect_identity(config.path+".done")}
			"lock":
				if io.make_directories(tx):result=io.acquire_lock(tx)
			"unowned_write":result=io.open_write(config.path,false)
			"exclusive","replace","rename":
				if io.make_directories(tx):
					result=io.acquire_lock(tx)
					if result.ok:
						var path: String=config.path
						var opened: Dictionary=io.open_write(path,config.operation=="replace")
						result=opened
						if opened.ok:
							var bytes: PackedByteArray=config.get("bytes","native exact bytes").to_utf8_buffer()
							var written: Dictionary=io.write_exact(opened.handle,bytes)
							var flushed: Dictionary=io.flush(opened.handle)
							var closed: Dictionary=io.close_file(opened.handle)
							result={"ok":written.ok and flushed.ok and closed.ok,"write":written,"flush":flushed,"close":closed}
							if config.operation=="rename" and result.ok:result=io.rename_file(path,config.to,config.get("receipt_replace",false))
			"swap":
				var opened: Dictionary=io.open_read(config.path)
				if opened.ok:
					result=io.read_all(opened.handle)
					io.close_file(opened.handle)
					pause(config,"native.swap.after")
					result=io.open_read(config.path)
			"process":result={"ok":true,"state":io.process_state(int(config.pid))}
		if config.operation=="lock" and result.ok:pause(config,"native.lock.after")
	result.erase("bytes")
	result["pid"]=OS.get_process_id()
	var out := FileAccess.open(config.root.path_join(config.get("result","native-result.json")),FileAccess.WRITE)
	out.store_string(JSON.stringify(result,"",true,true));out.close()
	print("NATIVE_PROBE: ",JSON.stringify(result));quit(0)
func pause(config: Dictionary, point: String) -> void:
	if config.get("kill_point","")!=point:return
	var path: String=config.root.path_join("paused.json")
	var f := FileAccess.open(path+".tmp",FileAccess.WRITE);f.store_string(JSON.stringify({"point":point,"pid":OS.get_process_id()}));f.flush();f.close()
	DirAccess.rename_absolute(path+".tmp",path)
	while not FileAccess.file_exists(config.root.path_join("release")):OS.delay_msec(5)
