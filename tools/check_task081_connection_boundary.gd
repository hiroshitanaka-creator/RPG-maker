extends SceneTree
## 081の接続前調査。本番データを観測し、架空の航路を追加しない。

func _initialize() -> void:
	var game := GameSession.new()
	var new_game := game.new_first_region()
	var definition := FirstRegion.data()
	var links: Dictionary = {}
	for key in definition:
		if "entrance" in str(key) or "spawn" in str(key) or "exit" in str(key) or "doors" in str(key):
			links[key] = definition[key]
	var sites: Array = []
	for site in FirstRegion._data["sites"]:
		sites.append({"id":site["id"],"rooms":site["rooms"].size()})
	var rejections: Array = []
	for node in ["region3_port","mist_market","dev_adopted_inn","dev_adopted_item_shop","dev_adopted_weapon_shop","dev_adopted_shrine","dev_adopted_armor_shop"]:
		var candidate := game.export_state()
		FirstRegion.place(candidate["overworld"],{"layer":"interior","node":node,"room":0,"cell":[6,9]})
		var loaded := GameSession.new()
		rejections.append({"node":node,"room_defined":not FirstRegion.room(candidate["overworld"]).is_empty(),"save_import_accepted":loaded.import_state(candidate)})
	var observed := {"engine":Engine.get_version_info(),"new_game":new_game,"sites":sites,"links":links,"docks":FirstRegionTravel.docks(),"sea_bounds":FirstRegionTravel.sea_bounds(),"destinations":FirstRegionTravel.destinations(),"unconnected_save_probes":rejections}
	var output := FileAccess.open("res://docs/verification/task-081/runtime-boundary.json",FileAccess.WRITE)
	output.store_string(JSON.stringify(observed,"\t")+"\n")
	output.close()
	# 旧mist_marketは凍結内部データとして存在するが、新本編の保存先にはできない。
	var blocked := new_game and rejections.all(func(item:Dictionary)->bool:return not item["save_import_accepted"] and item["room_defined"] == (item["node"] == "mist_market"))
	print("TASK081_BOUNDARY_OBSERVED: missing_runtime_port=%s probes=%d" % [blocked,rejections.size()])
	quit(0 if blocked else 1)
