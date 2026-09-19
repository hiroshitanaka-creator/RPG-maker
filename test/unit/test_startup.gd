extends "res://test/support/game_test.gd"


func test_project_starts_without_errors_or_warnings() -> void:
	var output: Array = []
	var arguments := PackedStringArray(["--headless", "--path", ProjectSettings.globalize_path("res://"), "--quit-after", "20"])
	var code := OS.execute(OS.get_executable_path(), arguments, output, true)
	var text := "\n".join(output)
	assert_eq(code, 0, text)
	assert_false("ERROR:" in text, text)
	assert_false("WARNING:" in text, text)
	assert_false("SCRIPT ERROR" in text, text)
	assert_eq(int(Engine.get_version_info()["major"]), 4)
	assert_eq(int(Engine.get_version_info()["minor"]), 7)
	assert_eq(int(Engine.get_version_info()["patch"]), 2)
	assert_eq(int(ProjectSettings.get_setting("display/window/size/viewport_width")), 512)
	assert_eq(int(ProjectSettings.get_setting("display/window/size/viewport_height")), 288)
