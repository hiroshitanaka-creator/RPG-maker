#!/usr/bin/env python3
"""固定SHAの装備APIへ一時定義を注入し、正負例・終了値・エラーを照合する。"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
ERROR = re.compile(r"SCRIPT ERROR|ERROR:|WARNING:|Parse Error")
PROBE = '''extends SceneTree
const Rules = preload("res://scripts/game/equipment_rules.gd")
var failures: Array = []
var checks := 0
func check(value: bool, label: String) -> void:
    checks += 1
    if not value:
        failures.append(label)
func _initialize() -> void:
    var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://case.json"))
    var r = Rules.new()
    var s = {"equipment_rules_version": 1, "equipment_stock": {"instances": {}, "bag": []},
        "party": [{"id": "a", "job_id": "warrior", "monster_form": "", "learned_abilities": [], "equipped_abilities": [],
            "equipment": {"weapons": [], "armor": "", "accessories": ["", "", ""]}, "hp": 0, "mp": 1}],
        "first_region": {"reserve": []}, "progress_flags": {"midgame_slots": false}}
    for i in range(int(config.count)):
        var identifier := "bracelet%d" % i
        s.equipment_stock.instances[identifier] = "guard_stitched_bracelet"
        s.party[0].equipment.accessories[i] = identifier
    if int(config.count) == 3:
        s.party[0].job_id = "slime"
    var before: Dictionary = s.duplicate(true)
    var request := {"kind": "set_abilities", "equipped_abilities": []}
    var request_before := request.duplicate(true)
    var definitions: Array = r.definition_errors()
    var catalog: Dictionary = r.catalog()
    var valid: Array = r.validate_equipment_state(s)
    var plan: Dictionary = r.plan_equipment_change(s, "a", request)
    var bonus: Dictionary = r.equipment_bonuses(s, "a")
    var allowed: bool = r.can_equip("warrior", [], "practice_blade", "weapon", 0)
    check(s == before and request == request_before, "入力不変")
    if config.mode == "invalid":
        check(not definitions.is_empty(), "定義不正を明示")
        check(not valid.is_empty(), "state拒否")
        check(catalog.is_empty(), "半完成カタログを非公開")
        check(not plan.get("ok", true) and plan.get("reason_code") == "invalid_state" and not plan.has("candidate"), "計画拒否・候補なし")
        check(not bonus.get("ok", true) and bonus.get("reason_code") == "invalid_state", "補正拒否")
        check(not allowed, "装備不可")
        check(config.reason in definitions.map(func(e): return e.get("reason_code")), "期待した定義拒否理由 " + config.reason)
    else:
        check(definitions.is_empty() and catalog.size() == 14 and valid.is_empty() and allowed, "正常定義対照")
        if config.mode == "overflow":
            check(not bonus.get("ok", true) and bonus.get("reason_code") == "numeric_overflow" and not bonus.has("bonuses"), "合算overflow拒否")
            check(not plan.get("ok", true) and plan.get("reason_code") == "numeric_overflow" and not plan.has("candidate"), "overflow計画拒否")
        else:
            check(bonus.get("ok", false) and str(bonus.get("bonuses", {}).get("defense")) == config.expected, "固定補正期待 " + config.expected)
            check(plan.get("ok", false) and plan.get("stats_after") == bonus.get("bonuses"), "正常計画対照")
    print("EQUIPMENT_INVALID_RESULT " + JSON.stringify({"checks": checks, "failures": failures, "definitions": definitions,
        "catalog_size": catalog.size(), "validation": valid, "plan": plan, "bonus": bonus, "can_equip": allowed, "input_unchanged": s == before}))
    quit(0 if failures.is_empty() else 1)
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--godot", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
        parser.error("--source-sha は完全SHAが必要です")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    godot = str(Path(args.godot).resolve())
    env = os.environ.copy()
    def blob(path: str) -> bytes:
        return subprocess.check_output(["git", "show", f"{args.source_sha}:{path}"], cwd=ROOT)
    paths = ["scripts/game/equipment_rules.gd", "data/equipment_rules.json", "data/integrated_rules.json"]
    paths += subprocess.check_output(["git", "ls-tree", "-r", "--name-only", args.source_sha, "data/jobs"], cwd=ROOT, text=True).splitlines()
    originals = {p: blob(p) for p in paths if p.endswith((".gd", ".json"))}
    catalog = json.loads(originals["data/equipment_rules.json"])
    legacy = json.loads(originals["data/integrated_rules.json"])
    cases = []
    def case(name, path=None, mutate=None, mode="invalid", reason="invalid_definition", count=0, expected="0", base=None):
        content = None
        if path:
            content = copy.deepcopy(base if base is not None else catalog)
            replacement = mutate(content)
            if replacement is not None or name == "root_value_0":
                content = replacement
        cases.append((name, path, content, {"mode": mode, "reason": reason, "count": count, "expected": expected}))
    case("legacy_file_missing", "data/equipment_rules.json", lambda d: d.__setitem__("legacy_source", "res://data/missing.json"), reason="invalid_legacy_source")
    case("normal", mode="valid", count=1, expected="1")
    bad_types = [None, True, 1, 1.5, [], {}, "unknown"]
    def field_cases(prefix, path, location, fields, base, reason):
        for field in fields:
            for label, value in [("missing", None)] + [(f"type_{i}", v) for i, v in enumerate(bad_types)]:
                def mutate(data, field=field, value=value, label=label):
                    target = data
                    for key in location:
                        target = target[key]
                    if label == "missing":
                        target.pop(field)
                    else:
                        target[field] = copy.deepcopy(value)
                # 一部の型が合法値のフィールドは個別に検査する。
                if field in ("bonuses", "items", "jobs", "weapons") and value == ([] if field in ("items", "weapons") else {}) and label != "missing":
                    continue
                if field == "provisional" and isinstance(value, bool):
                    continue
                if field in ("armor_rank", "accessory_slots", "equipment_rules_version") and type(value) is int and value == 1:
                    continue
                case(f"{prefix}_{field}_{label}", path, mutate, reason=reason, base=base)
    path = "data/equipment_rules.json"
    field_cases("root", path, [], ["legacy_source", "equipment_rules_version", "jobs", "items"], catalog, "invalid_definition")
    for i, value in enumerate(bad_types):
        case(f"root_value_{i}", path, lambda d, v=value: v, reason="invalid_definition")
    field_cases("item", path, ["items", 13], ["id", "name", "kind", "bonuses", "provisional"], catalog, "invalid_item_definition")
    # IDは専用の理由コード。
    cases = [(n, p, c, {**cfg, "reason": "invalid_item_id"} if n.startswith("item_id_") else cfg) for n,p,c,cfg in cases]
    field_cases("weapon", path, ["items", 6], ["weapon_category"], catalog, "invalid_weapon_definition")
    field_cases("armor", path, ["items", 8], ["armor_rank"], catalog, "invalid_armor_definition")
    field_cases("legacy_catalog", path, ["items", 0], ["legacy"], catalog, "legacy_mismatch")
    for i, value in enumerate(bad_types):
        case(f"legacy_bonus_{i}", path, lambda d,v=value: d["items"][0]["bonuses"].__setitem__("attack", v), reason="invalid_bonus")
    case("item_null", path, lambda d: d["items"].__setitem__(13, None), reason="invalid_item_id")
    field_cases("job", path, ["jobs", "warrior"], ["type", "weapon_category", "armor_rank", "accessory_slots"], catalog, "invalid_job_definition")
    for i, value in enumerate(bad_types):
        case(f"job_value_{i}", path, lambda d,v=value: d["jobs"].__setitem__("warrior", v), reason="invalid_job_definition")
    oldpath = "data/integrated_rules.json"
    field_cases("legacy_root", oldpath, [], ["weapons"], legacy, "invalid_legacy_source")
    field_cases("legacy_item", oldpath, ["weapons", 0], ["id", "name", "attack"], legacy, "invalid_legacy_source")
    case("legacy_item_null", oldpath, lambda d: d["weapons"].__setitem__(0, None), reason="invalid_legacy_source", base=legacy)
    jobpath = "data/jobs/01_warrior.json"
    field_cases("job_source", jobpath, [], ["id", "type"], json.loads(originals[jobpath]), "invalid_job_source")
    # 非文字列name/idは拒否。未知文字列name/idは型正常なので名前変更の不整合で拒否させる。
    cases = [c for c in cases if not (c[0] in ["item_name_type_6", "item_id_type_6", "legacy_item_name_type_6", "legacy_item_id_type_6", "job_source_id_type_6", "legacy_item_attack_type_2", "legacy_bonus_2"])]
    boundary = [
        ("huge_positive", 1e30, "invalid", "0"), ("huge_negative", -1e30, "invalid", "0"),
        ("fraction", 1.5, "invalid", "0"), ("numeric_string", "1", "invalid", "0"), ("numeric_bool", True, "invalid", "0"),
        ("upper_exclusive", 9223372036854775808, "invalid", "0"),
        ("upper_integer_rounds_out", 9223372036854775807, "invalid", "0"),
        ("upper_float_neighbor", 9223372036854774784, "valid", "9223372036854774784"),
        ("lower_inclusive", -9223372036854775808, "valid", "-9223372036854775808"),
        ("lower_float_neighbor", -9223372036854777856, "invalid", "0"),
        ("lower_integer_rounds_in", -9223372036854775809, "valid", "-9223372036854775808"),
        ("integral_float", 2.0, "valid", "2"), ("legal_negative", -2, "valid", "-2"),
        ("zero", 0, "valid", "0")]
    for name, value, mode, expected in boundary:
        case(name, path, lambda d,v=value: d["items"][13]["bonuses"].__setitem__("defense", v), mode=mode, reason="invalid_bonus", count=1, expected=expected)
    for name, value, count, mode, expected in [
        ("sum_upper_overflow", 4611686018427387904, 2, "overflow", "0"),
        ("sum_lower_overflow", -4611686018427387904, 3, "overflow", "0"),
        ("sum_lower_exact", -4611686018427387904, 2, "valid", "-9223372036854775808")]:
        case(name, path, lambda d,v=value: d["items"][13]["bonuses"].__setitem__("defense", v), mode=mode, count=count, expected=expected)
    version = subprocess.check_output([godot, "--version"], env=env, stderr=subprocess.STDOUT, text=True).strip()
    if version != "4.7.2.stable.official.ed1daf0bf":
        raise RuntimeError("指定版と不一致: " + version)
    results = []
    with tempfile.TemporaryDirectory(prefix="equipment038-fixtures-") as folder:
        project = Path(folder)
        (project / "project.godot").write_text('config_version=5\n[application]\nconfig/name="装備不正定義検査"\n')
        (project / "probe.gd").write_text(PROBE)
        for p, data in originals.items():
            dest = project / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        for name, path, content, config in cases:
            if path:
                (project / path).write_text(json.dumps(content, ensure_ascii=False))
            (project / "case.json").write_text(json.dumps(config))
            command = [godot, "--headless", "--path", str(project), "--script", "res://probe.gd"]
            try:
                process = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
                code, log = process.returncode, process.stdout
            except subprocess.TimeoutExpired as exc:
                code, log = 124, (exc.stdout or b"").decode() + "\nTIMEOUT\n"
            (output / (name + ".log")).write_text(log)
            observations = [json.loads(line.removeprefix("EQUIPMENT_INVALID_RESULT ")) for line in log.splitlines() if line.startswith("EQUIPMENT_INVALID_RESULT ")]
            errors = ERROR.findall(log)
            passed = code == 0 and not errors and len(observations) == 1 and observations[0]["checks"] > 0 and not observations[0]["failures"]
            results.append({"case": name, "expectation": config, "fixture_path": path, "fixture_sha256": hashlib.sha256((project/path).read_bytes()).hexdigest() if path else None,
                "exit_code": code, "errors": errors, "status": "PASS" if passed else "FAIL", "observed": observations,
                "log_sha256": hashlib.sha256(log.encode()).hexdigest()})
            if path:
                (project / path).write_bytes(originals[path])
    report = {"source_sha": args.source_sha, "engine": version, "source_sha256": {p: hashlib.sha256(v).hexdigest() for p,v in originals.items()},
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "probe_sha256": hashlib.sha256(PROBE.encode()).hexdigest(),
        "case_count": len(results), "checks": sum(o["checks"] for r in results for o in r["observed"]), "passed": sum(r["status"] == "PASS" for r in results), "results": results}
    (output / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f'EQUIPMENT_INVALID: cases={report["case_count"]} passed={report["passed"]} checks={report["checks"]} failed={report["case_count"]-report["passed"]}')
    for r in results:
        if r["status"] != "PASS":
            print(r["case"], "exit=", r["exit_code"], "errors=", len(r["errors"]), "failures=", [o["failures"] for o in r["observed"]])
    return 0 if report["passed"] == report["case_count"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
