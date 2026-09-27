extends "res://tools/capture_first_region.gd"
## 通常の9場面に加え、初めて洞窟へ入る直前の入口を実描画で保存する。
var _entrance_captured := false

func _watch() -> void:
	super._watch()
	if _capture_busy or _finished or _entrance_captured or _definition.is_empty():return
	if not _at(_outside(_definition["cave_entrance"])) or _has_pass():return
	if _snapshot().get("mode")!="world":return
	_entrance_captured=true
	_capture_busy=true
	call_deferred("_capture","14-cave-entrance")

func _finish() -> void:
	if not _entrance_captured:
		printerr("FIRST_REGION_ENTRANCE_CAPTURE_FAIL: 入口画像が未撮影")
		quit(1)
		return
	print("FIRST_REGION_ENTRANCE_CAPTURE_PASS: additional_images=1")
	await super._finish()
