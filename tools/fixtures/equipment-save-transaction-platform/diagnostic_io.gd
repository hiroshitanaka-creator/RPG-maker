extends RefCounted
## 元nativeへ同じ引数を転送。kernel内部CPU時間ではなくbinding込みの実経過時間。
var target: RefCounted
var spans: Array=[]
func _init(value: RefCounted) -> void:
	target=value

func path_ok(path: String) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.path_ok(path)
	spans.append({"label":"native.path_ok","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func relative_path(path: String) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.relative_path(path)
	spans.append({"label":"native.relative_path","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func make_directories(path: String) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.make_directories(path)
	spans.append({"label":"native.make_directories","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func open_read(path: String) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.open_read(path)
	spans.append({"label":"native.open_read","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func close_file(handle: int) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.close_file(handle)
	spans.append({"label":"native.close_file","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func read_all(handle: int) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.read_all(handle)
	spans.append({"label":"native.read_all","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func inspect_identity(path: String) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.inspect_identity(path)
	spans.append({"label":"native.inspect_identity","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func acquire_lock(path: String) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.acquire_lock(path)
	spans.append({"label":"native.acquire_lock","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func legacy_link(path: String) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.legacy_link(path)
	spans.append({"label":"native.legacy_link","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func process_state(pid: int) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.process_state(pid)
	spans.append({"label":"native.process_state","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func open_write(path: String, replace: bool) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.open_write(path,replace)
	spans.append({"label":"native.open_write","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func write_exact(handle: int, bytes: PackedByteArray) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.write_exact(handle,bytes)
	spans.append({"label":"native.write_exact","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func flush(handle: int) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.flush(handle)
	spans.append({"label":"native.flush","start_us":start,"end_us":Time.get_ticks_usec()})
	return result

func rename_file(source: String, target_path: String, replace: bool) -> Variant:
	var start := Time.get_ticks_usec()
	var result: Variant=target.rename_file(source,target_path,replace)
	spans.append({"label":"native.rename_file","start_us":start,"end_us":Time.get_ticks_usec()})
	return result
