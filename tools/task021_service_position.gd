extends RefCounted
## 最新回帰用。初期座標を期待値にせず、ID・床・占有・受付reach・入口到達で選ぶ。
const DIRECTIONS := [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]

static func find(saved: Dictionary, room_index: int, id: String) -> Dictionary:
	var entry := saved.duplicate(true)
	var landing := FirstRegion.entrance_landing("region2_village",room_index)
	if landing.is_empty():return {}
	FirstRegion.place(entry["overworld"],{"layer":"interior","node":"region2_village","room":room_index,"cell":landing})
	var room := FirstRegion.room(entry["overworld"])
	var events: Array=room["events"].filter(func(event:Dictionary)->bool:return event["id"]=="oasis_"+id)
	if events.size()!=1:return {}
	var event: Dictionary=events[0];var cell := FirstRegion.event_cell(entry,event)
	var layout: Array=room["layout"]
	if cell.y<0 or cell.y>=layout.size() or cell.x<0 or cell.x>=str(layout[cell.y]).length():return {}
	if layout[cell.y][cell.x]!="." or FirstRegion.walkable(entry,cell):return {}
	var start := WorldExpedition.point(landing)
	if not FirstRegion.walkable(entry,start):return {}
	var found := {start:true};var queue: Array[Vector2i]=[start];var cursor := 0
	while cursor<queue.size():
		var current := queue[cursor];cursor+=1
		for direction in DIRECTIONS:
			var next: Vector2i=current+direction
			if found.has(next) or not FirstRegion.walkable(entry,next):continue
			found[next]=true;queue.append(next)
	for direction in DIRECTIONS:
		for distance in range(1,int(event.get("reach",1))+1):
			var approach: Vector2i=cell+direction*distance
			if found.has(approach):
				# 宿は受付台越しに話す。受付内へ回り込む隣接会話でreach欠落を隠さない。
				if event["kind"]=="rest" and (distance<2 or layout[cell.y+direction.y][cell.x+direction.x]=="."):continue
				return {"cell":[cell.x,cell.y],"approach":[approach.x,approach.y],"facing":-direction,"reach":int(event.get("reach",1)),"distance":distance,"entrance":landing}
	return {}
