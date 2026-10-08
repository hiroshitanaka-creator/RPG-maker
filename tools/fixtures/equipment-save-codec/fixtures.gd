extends RefCounted
## 旧実物の固定入力と手書き派生。期待はexpectations.jsonに独立記述する。
static func base() -> Dictionary:
	return GameSession._normalize_numbers(JSON.parse_string(FileAccess.get_file_as_string("res://tools/fixtures/equipment-save-codec/legacy.json")))

static func region() -> Dictionary:
	var document := base()
	document["first_region"]={"version":1,"coins":20,"reserve":document.party.slice(1).duplicate(true)}
	document.party=[document.party[0]]
	document.inventory["world_map"]=1
	document["overworld"]={"active":true,"layer":"interior","node":"start_village","room":0,"cell":[6,7],"facing":0,"transport":"walk","cleared":[],"opened":[],"entry_lock":""}
	return document

static func metrics() -> Dictionary:
	var entries: Array[Dictionary]=[{"kind":"fixture","chapter":"1","elapsed_ms":0,"details":{"integer_float":1.0,"fraction":1.5,"third":1.0/3.0,"bools":Array([true,false],TYPE_BOOL,"",null),"ints":Array([3,1,2],TYPE_INT,"",null),"strings":Array(["b","a"],TYPE_STRING,"",null),"floats":Array([1.0,1.5,1.0/3.0],TYPE_FLOAT,"",null),"dicts":Array([{"n":1}],TYPE_DICTIONARY,"",null),"empty":Array([],TYPE_STRING,"",null),"nested":Array([Array([],TYPE_INT,"",null)],TYPE_ARRAY,"",null)}}]
	var answers: Array[Dictionary]=[]
	return {"version":1,"source":"automated","source_changed":false,"active_ms":0,"elapsed_ms":0,"idle_ms":0,"pause_ms":0,"chapters":{},"counters":{},"answers":answers,"events":entries,"completed":false}

static func typed(document: Dictionary) -> Dictionary:
	var copy := document.duplicate(true)
	copy.erase("_saved_value_types")
	copy["_saved_value_types"]=SavedValueTypes.describe(copy)
	return copy
