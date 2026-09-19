class_name RuntimeDiagnostics
extends Logger

var _messages: Array[String] = []
var _mutex := Mutex.new()


func _log_error(_function: String, file: String, line: int, code: String, rationale: String, _editor_notify: bool, _error_type: int, _script_backtraces: Array[ScriptBacktrace]) -> void:
	_mutex.lock()
	_messages.append("%s:%d %s %s" % [file, line, code, rationale])
	_mutex.unlock()


func messages() -> Array[String]:
	_mutex.lock()
	var copy: Array[String] = _messages.duplicate()
	_mutex.unlock()
	return copy
