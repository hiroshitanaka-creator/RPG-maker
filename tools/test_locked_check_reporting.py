"""検証の空実行・片側だけの保存成功・保留を合格にしない回帰検査。"""
import json
import unittest
from copy import deepcopy

from run_locked_checks import execution_summary, judge_output
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


class FirstRegionReportingTests(unittest.TestCase):
    command = "godot --headless --path . --script res://tools/smoke_first_region.gd"
    chapter_command = "godot --headless --path . --script res://tools/smoke_chapter1.gd"

    def log(self, failed=()):
        lines = [f"FIRST_REGION_CHECK: A{i:02d} {'FAIL' if i in failed else 'PASS'} 検査結果" for i in range(1, 15)]
        final = f"FIRST_REGION_FAIL: failed={len(failed)}/14" if failed else "FIRST_REGION_PASS: checks=14"
        return "\n".join(lines + [final])

    def judge(self, output, code=0, command=None, timed_out=False):
        return judge_output("R-07", self.command if command is None else command, code, output, timed_out)

    def test_all_fourteen_pass(self):
        self.assertEqual(self.judge(self.log())["status"], "PASS")

    def test_one_check_fails(self):
        self.assertEqual(self.judge(self.log((6,)), 1)["status"], "FAIL")

    def test_current_real_fourteen_fail_output(self):
        # 実装前の実行ログを保持し、未到達を検査プログラムの不正と混同しない。
        output = '''FIRST_REGION_CHECK: A01 FAIL New Game後にstart_village内部の位置情報がない
FIRST_REGION_CHECK: A02 FAIL 禁止ラベルを検出: ["世界地図へ"]
FIRST_REGION_CHECK: A03 FAIL 村内経路が未観測、または村内戦闘・観測欠落あり
FIRST_REGION_CHECK: A04 FAIL 村退出時の3人編成を観測できない
FIRST_REGION_CHECK: A05 FAIL 未到達: world/interiors.json のfirst_region定義がない
FIRST_REGION_CHECK: A06 FAIL 未到達: world/interiors.json のfirst_region定義がない
FIRST_REGION_CHECK: A07 FAIL 未到達: world/interiors.json のfirst_region定義がない
FIRST_REGION_CHECK: A08 FAIL 未到達: world/interiors.json のfirst_region定義がない
FIRST_REGION_CHECK: A09 FAIL world/interiors.json のfirst_region定義がない、または不正
FIRST_REGION_CHECK: A10 FAIL 未到達: world/interiors.json のfirst_region定義がない
FIRST_REGION_CHECK: A11 FAIL 未到達: world/interiors.json のfirst_region定義がない
FIRST_REGION_CHECK: A12 FAIL 未到達: world/interiors.json のfirst_region定義がない
FIRST_REGION_CHECK: A13 FAIL 未到達: world/interiors.json のfirst_region定義がない
FIRST_REGION_CHECK: A14 FAIL 通常入力だけでの全経路到達が未成立
FIRST_REGION_FAIL: failed=14/14'''
        result = self.judge(output, 1)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["tests_ran"])

    def test_missing_id(self):
        self.assertEqual(self.judge("\n".join(self.log().splitlines()[1:]))["status"], "INVALID")

    def test_duplicate_id(self):
        self.assertEqual(self.judge(self.log() + "\nFIRST_REGION_CHECK: A01 PASS 重複")["status"], "INVALID")

    def test_unknown_id(self):
        self.assertEqual(self.judge(self.log() + "\nFIRST_REGION_CHECK: A15 PASS 未定義")["status"], "INVALID")

    def test_missing_final(self):
        self.assertEqual(self.judge("\n".join(self.log().splitlines()[:-1]))["status"], "INVALID")

    def test_nonzero_exit_with_all_pass(self):
        self.assertEqual(self.judge(self.log(), 1)["status"], "FAIL")

    def test_pass_final_contradicts_failed_check(self):
        output = self.log((6,)).replace("FIRST_REGION_FAIL: failed=1/14", "FIRST_REGION_PASS: checks=14")
        self.assertEqual(self.judge(output)["status"], "INVALID")

    def test_both_final_lines(self):
        self.assertEqual(self.judge(self.log() + "\nFIRST_REGION_FAIL: failed=0/14")["status"], "INVALID")

    def test_chapter_marker_keeps_previous_rule(self):
        output = "CHAPTER1_PASS: steps=2030 moved=215 battles=15 interactions=83\n"
        self.assertEqual(self.judge(output, command=self.chapter_command)["status"], "PASS")
        self.assertEqual(execution_summary("R-07", output, self.chapter_command), ("CHAPTER1_" in output, "CHAPTER1_PASS:" in output, None))
        for log, code, expected in ((output, 1, "FAIL"), ("CHAPTER1_FAIL: 未到達", 1, "FAIL"), ("", 0, "INVALID"), (self.log(), 0, "INVALID")):
            with self.subTest(log=log, code=code):
                self.assertEqual(self.judge(log, code, self.chapter_command)["status"], expected)

    def test_unknown_command_is_invalid_with_reason(self):
        result = self.judge(self.log(), command="godot --headless --script res://tools/other.gd")
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["failure_messages"][0], "R-07のverifyコマンドに対応する判定規則がありません。")

    def test_final_counts_must_match(self):
        for output in (self.log((1,)).replace("failed=1/14", "failed=2/14"), self.log().replace("checks=14", "checks=13"), self.log().replace("FIRST_REGION_PASS: checks=14", "FIRST_REGION_FAIL: failed=0/14")):
            with self.subTest(output=output):
                self.assertEqual(self.judge(output)["status"], "INVALID")

    def test_duplicate_same_final(self):
        self.assertEqual(self.judge(self.log() + "\nFIRST_REGION_PASS: checks=14")["status"], "INVALID")

    def test_malformed_check_lines(self):
        for line in ("FIRST_REGION_CHECK: A01 PASS", "FIRST_REGION_CHECK: A01 SKIP 理由", "FIRST_REGION_CHECK: A01 PASS  ", "prefix FIRST_REGION_CHECK: A01 PASS 理由", "FIRST_REGION_CHECK: other PASS 理由"):
            with self.subTest(line=line):
                output = "\n".join([line] + self.log().splitlines()[1:])
                self.assertEqual(self.judge(output)["status"], "INVALID")

    def test_ansi_and_crlf_are_cleaned(self):
        output = "\x1b[32m" + self.log().replace("\n", "\r\n") + "\x1b[0m\r\n"
        self.assertEqual(self.judge(output)["status"], "PASS")

    def test_failure_token_anywhere_prevents_pass(self):
        self.assertEqual(self.judge(self.log() + "\n診断 FIRST_REGION_FAIL を検出")["status"], "FAIL")

    def test_global_error_warning_and_timeout_rules_remain(self):
        for command, output in ((self.command, self.log()), (self.chapter_command, "CHAPTER1_PASS: steps=35")):
            for diagnostic, expected in (("Parse Error: 構文", "INVALID"), ("Failed to load script", "INVALID"), ("SCRIPT ERROR: 実行", "FAIL"), ("ERROR: 実行", "FAIL"), ("WARNING: 警告", "FAIL"), ("[Failed] assertion", "FAIL")):
                with self.subTest(command=command, diagnostic=diagnostic):
                    self.assertEqual(self.judge(output + "\n" + diagnostic, command=command)["status"], expected)
            self.assertEqual(self.judge(output, command=command, timed_out=True)["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
