class_name SecondRegionCoast
extends RefCounted
## 第2地方の航路と岸。原画待ちの町や、未採用の地上敵は接続しない。
static var _data: Dictionary = {}
static func data() -> Dictionary:
	if _data.is_empty():_data=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://world/second_region_coast.json")))
	return _data
static func contains(cell: Vector2i) -> bool:
	var b: Array=data()["bounds"]
	return cell.x>=b[0] and cell.y>=b[1] and cell.x<=b[2] and cell.y<=b[3]
static func on_land(cell: Vector2i) -> bool:
	if not contains(cell):return false
	var p := cell-WorldExpedition.point(data()["origin"])
	return str(data()["terrain"][p.y]).substr(p.x,1)=="s"
static func extend_world(base: Dictionary) -> Dictionary:
	var result := base.duplicate(true);var extra := data()
	var w: int=extra["width"];var h: int=extra["height"]
	var terrain: Array=[];var layout: Array=[]
	for y in range(h):
		var row := str(base["terrain"][y]).rpad(w,"~") if y<base["height"] else "~".repeat(w)
		var walk := str(base["layout"][y]).rpad(w,"#") if y<base["height"] else "#".repeat(w)
		for x in range(w):
			if str(extra["terrain"][y]).substr(x,1)=="s":
				row=row.substr(0,x)+"s"+row.substr(x+1)
				walk=walk.substr(0,x)+str(extra["layout"][y]).substr(x,1)+walk.substr(x+1)
		terrain.append(row);layout.append(walk)
	result["terrain"]=terrain;result["layout"]=layout;result["width"]=w;result["height"]=h
	for key in extra["tiles"]:result["tiles"]["second_"+key]=extra["tiles"][key]
	for source in extra["layers"]:
		var layer: Dictionary=source.duplicate(true)
		for cell in layer["cells"]:cell[2]="second_"+str(cell[2])
		result["layers"].append(layer)
	return result
