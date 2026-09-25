"""検証の空実行・片側だけの保存成功・保留を合格にしない回帰検査。"""
import json
import unittest
from copy import deepcopy

from run_locked_checks import execution_summary
from check_acceptance_registration import ADDITIONS, problems


class ReportingTests(unittest.TestCase):
    def test_empty_output_is_not_success(self):
        for key in ("R-01", "R-07", "AC-01", "AC-02", "AC-03"):
            self.assertFalse(execution_summary(key, "")[1])

    def test_save_requires_both_parties_and_nonempty_states(self):
        valid = "SAVE_COMPLETE_PASS: party=3 states=359 differences=0\nSAVE_COMPLETE_PASS: party=4 states=359 differences=0"
        self.assertTrue(execution_summary("AC-03", valid)[1])
        self.assertTrue(execution_summary("AC-03", valid.replace("\n", "\r\n") + "\r\n")[1])
        for invalid in (valid.splitlines()[0], valid.replace("party=4", "party=3"), valid.replace("states=359", "states=0"), valid.replace("differences=0", "differences=1")):
            self.assertFalse(execution_summary("AC-03", invalid)[1])

    def test_battle_requires_twelve_distinct_trials_and_both_pass(self):
        lines = [f"BATTLE_SAMPLE: case{i} party={size} wins=500/1000 within10=900 cutoff=0" for i in range(6) for size in (3, 4)]
        final = "BATTLE_ACCEPTANCE: AC-01=PASS AC-02=PASS errors=0"
        valid = "\n".join(lines + [final])
        for key in ("AC-01", "AC-02"):
            self.assertTrue(execution_summary(key, valid)[1])
            self.assertTrue(execution_summary(key, valid.replace("\n", "\r\n") + "\r\n")[1])
            for invalid in (final, "\n".join(lines[1:] + [final]), valid.replace("case5", "case4"), valid.replace("AC-02=PASS", "AC-02=FAIL")):
                self.assertFalse(execution_summary(key, invalid)[1])

    def test_gut_requires_assertions_and_rejects_pending(self):
        valid = {"tests": 1, "assertions": 2, "failed_assertions": 0, "pending": 0, "invalid": False}
        self.assertTrue(execution_summary("R-01", "SCOPE_GUT_RESULT " + json.dumps(valid))[1])
        for key, value in (("assertions", 0), ("pending", 1), ("failed_assertions", 1), ("invalid", True)):
            self.assertFalse(execution_summary("R-01", "SCOPE_GUT_RESULT " + json.dumps({**valid, key: value}))[1])
        self.assertFalse(execution_summary("R-01", "SCOPE_GUT_RESULT broken")[1])

    def test_registration_rejects_changed_old_conditions_and_new_limits(self):
        before = {"requirements": [{"id": "R-01", "done_when": "original", "verify": "original"}], "amendments": [], "budget": {"verify_timeout_sec": 300}}
        valid = deepcopy(before)
        valid["requirements"] += deepcopy(ADDITIONS)
        valid["amendments"].append({"requirement": "AC-01,AC-02,AC-03"})
        self.assertEqual(problems(valid, before), [])
        changed = deepcopy(valid)
        changed["requirements"][0]["verify"] = "echo PASS"
        self.assertTrue(problems(changed, before))
        changed = deepcopy(valid)
        changed["requirements"][1]["done_when"] = "勝率0%以上"
        self.assertTrue(problems(changed, before))
        changed = deepcopy(valid)
        changed["budget"]["verify_timeout_sec"] = 999
        self.assertTrue(problems(changed, before))


if __name__ == "__main__":
    unittest.main()
