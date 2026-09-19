extends GutHookScript


func run() -> void:
	var totals: Dictionary = gut.get_summary().get_totals()
	var count: int = gut.get_test_count()
	var asserts: int = gut.get_assert_count()
	var invalid: bool = count == 0 or asserts == 0 or gut.get_pending_count() > 0 or int(totals.get("risky", 0)) > 0
	invalid = invalid or not gut.logger.get_errors().is_empty() or not gut.logger.get_warnings().is_empty()
	if invalid or gut.get_fail_count() > 0:
		set_exit_code(1)
	print("SCOPE_GUT_RESULT " + JSON.stringify({"tests": count, "assertions": asserts, "failed_assertions": gut.get_fail_count(), "pending": gut.get_pending_count(), "invalid": invalid}))
