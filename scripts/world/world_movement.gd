class_name WorldMovement
extends RefCounted
## 本番の広域移動と移動時間検査が共用する移動処理。
var cell := Vector2i.ZERO
var transport := "walk"
var route: Array[Vector2i] = []
var elapsed_seconds := 0.0
var _accumulator := 0.0
var _next := 0

func begin(path: Array[Vector2i], mode: String, can_enter: Callable = Callable()) -> bool:
	if path.is_empty():
		return false
	for i in range(path.size()):
		if not (can_enter.call(path[i]) if can_enter.is_valid() else WorldTerrain.passable(path[i], mode)):
			return false
		if i > 0 and absi(path[i].x-path[i-1].x) + absi(path[i].y-path[i-1].y) != 1:
			return false
	route = path.duplicate()
	cell = route[0]
	transport = mode
	elapsed_seconds = 0.0
	_accumulator = 0.0
	_next = 1
	return true

func active() -> bool:
	return _next < route.size()

func advance(delta: float) -> int:
	if not active() or not is_finite(delta) or delta <= 0:
		return 0
	var duration := WorldTerrain.seconds_per_step(transport)
	var remaining := (route.size() - _next) * duration - _accumulator
	var consumed := minf(delta, remaining)
	elapsed_seconds += consumed
	_accumulator += consumed
	var steps := 0
	while _accumulator + 0.0000001 >= duration and active():
		_accumulator -= duration
		cell = route[_next]
		_next += 1
		steps += 1
	return steps

func stop() -> void:
	route.clear()
	_next = 0
	_accumulator = 0.0
