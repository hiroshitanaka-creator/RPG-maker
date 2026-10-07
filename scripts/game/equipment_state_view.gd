extends RefCounted
## 保存モードを変えず、装備APIに必要な既定値だけをコピーへ補う。

static func project(state: Dictionary) -> Dictionary:
	if not state.get("party") is Array or not state.get("progress_flags") is Dictionary:
		return _failure("$", "invalid_state_view")
	if state.has("first_region") and (not state.first_region is Dictionary or not state.first_region.get("reserve") is Array):
		return _failure("$.first_region.reserve", "invalid_state_view")
	if state.progress_flags.has("midgame_slots") and not state.progress_flags.midgame_slots is bool:
		return _failure("$.progress_flags.midgame_slots", "invalid_capacity_input")
	var view := state.duplicate(true)
	if not view.has("first_region"):
		view["first_region"] = {"reserve": []}
	if not view.progress_flags.has("midgame_slots"):
		view["progress_flags"]["midgame_slots"] = false
	return {"ok": true, "reason_code": "ok", "view": view, "errors": []}

static func _failure(path: String, code: String) -> Dictionary:
	return {"ok": false, "reason_code": code, "errors": [{"target": path, "reason_code": code}]}
