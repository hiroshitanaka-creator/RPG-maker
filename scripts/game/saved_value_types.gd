class_name SavedValueTypes
extends RefCounted

const ARRAY_TYPES := [TYPE_BOOL,TYPE_INT,TYPE_FLOAT,TYPE_STRING,TYPE_DICTIONARY,TYPE_ARRAY]

# JSONだけでは区別できない型情報を値とは別に保存する。
static func describe(value: Variant) -> Dictionary:
	var result := {"version":1,"arrays":[],"floats":[],"errors":[]}
	_collect(value,[],result)
	result["arrays"].sort_custom(func(a: Dictionary,b: Dictionary) -> bool: return JSON.stringify(a["path"]) < JSON.stringify(b["path"]))
	result["floats"].sort_custom(func(a: Array,b: Array) -> bool: return JSON.stringify(a) < JSON.stringify(b))
	return result

static func _collect(value: Variant, path: Array, result: Dictionary) -> void:
	if value is Dictionary:
		if value.is_typed():result["errors"].append("型付き辞書の保存定義が必要です。")
		for key in value:
			if not key is String:
				result["errors"].append("保存辞書のキーは文字列です。")
				continue
			_collect(value[key],path+[key],result)
	elif value is Array:
		if value.is_typed():
			var kind: int = value.get_typed_builtin()
			if kind not in ARRAY_TYPES:result["errors"].append("未対応の配列要素型です。")
			else:result["arrays"].append({"path":path.duplicate(),"builtin":kind})
		for index in range(value.size()):_collect(value[index],path+[index],result)
	elif value is float:
		if is_finite(value):result["floats"].append(path.duplicate())
		else:result["errors"].append("非有限値は保存できません。")
	elif typeof(value) not in [TYPE_NIL,TYPE_BOOL,TYPE_INT,TYPE_STRING]:
		result["errors"].append("未対応の保存値です。")

static func restore(value: Dictionary, metadata: Variant) -> Dictionary:
	if not metadata is Dictionary or metadata.get("version") != 1 or not metadata.get("arrays") is Array or not metadata.get("floats") is Array or metadata.get("errors") != []:
		return {"ok":false}
	var restored := value.duplicate(true)
	var seen: Dictionary = {}
	for path in metadata["floats"]:
		var reference := _reference(restored,path)
		if not reference.get("ok",false) or seen.has(JSON.stringify(path)):return {"ok":false}
		seen[JSON.stringify(path)] = true
		var scalar: Variant = reference["parent"][reference["key"]]
		if not (scalar is int or scalar is float):return {"ok":false}
		reference["parent"][reference["key"]] = float(scalar)
	var arrays: Array = metadata["arrays"].duplicate(true)
	for entry in arrays:
		if not entry is Dictionary or not entry.get("path") is Array or not (entry.get("builtin") is int or entry.get("builtin") is float):return {"ok":false}
		if entry["builtin"] != int(entry["builtin"]) or int(entry["builtin"]) not in ARRAY_TYPES:return {"ok":false}
	arrays.sort_custom(func(a: Dictionary,b: Dictionary) -> bool: return a["path"].size() > b["path"].size())
	for entry in arrays:
		var reference := _reference(restored,entry["path"])
		if not reference.get("ok",false) or seen.has(JSON.stringify(entry["path"])):return {"ok":false}
		seen[JSON.stringify(entry["path"])] = true
		var items: Variant = reference["parent"][reference["key"]]
		if not items is Array:return {"ok":false}
		for item in items:
			if typeof(item) != int(entry["builtin"]):return {"ok":false}
		reference["parent"][reference["key"]] = Array(items,int(entry["builtin"]),StringName(""),null)
	return {"ok":true,"value":restored}

static func _reference(document: Dictionary, path: Variant) -> Dictionary:
	if not path is Array or path.is_empty() or path.size() > 64:return {"ok":false}
	var current: Variant = document
	for index in range(path.size()):
		var key: Variant = path[index]
		if current is Dictionary:
			if not key is String or not current.has(key):return {"ok":false}
		elif current is Array:
			if not (key is int or key is float) or key != int(key):return {"ok":false}
			key = int(key)
			if key < 0 or key >= current.size():return {"ok":false}
		else:return {"ok":false}
		if index == path.size()-1:return {"ok":true,"parent":current,"key":key}
		current = current[key]
	return {"ok":false}
