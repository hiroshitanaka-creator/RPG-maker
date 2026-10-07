#!/usr/bin/env python3
"""043: 原検査を別checkoutで実行し、固定版と最新版の証拠を分離する。"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
FIXED = {
    "036": "dbceae8f68e18939a40ace71f3a24a1a1953e653",
    "038": "45a58b7faf09809d916954353a3a1fe0c3d2d035",
    "041": "8d3c1848d09b588fa41bcf6345d3aab6e12a5347",
    "baseline": "821448b384d37edc041152beb5d6b6f560ad771d",
}
BASE = {"036": "79caadbe71e13ba7060aab598dc460035b04cab9",
        "038": "2547e91d36c59ed6d59f46be15c5c40b20a6b184", "041": FIXED["baseline"]}
VERSION = "4.7.2.stable.official.ed1daf0bf"
ENGINE_SHA256 = "8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e"
MIGRATION_EVIDENCE = "ddf2153e0f47513eb7906ddd68ab03b645edacd7"
BAD_LOG = re.compile(r"SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL:|Fontconfig error")
FIXTURE_FILES = ["base.json", "fixtures.gd", "fixtures.gd.uid",
                 "legacy_equivalence.gd", "legacy_equivalence.gd.uid"]
SOURCE_FILES = ["data/equipment_rules.json", "data/integrated_rules.json",
                "scripts/game/equipment_rules.gd", "scripts/game/game_session.gd",
                "scripts/game/integrated_progression.gd", "scripts/game/equipment_save_migration.gd",
                "scripts/game/equipment_save_validation.gd", "scripts/game/equipment_state_view.gd",
                "tools/check_equipment_rules.gd", "tools/check_equipment_invalid_definitions.py",
                "tools/check_equipment_save_migration.gd", "tools/fixtures/equipment-save/expectations.json"]


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str, cwd: Path = ROOT) -> bytes:
    return subprocess.check_output(["git", *args], cwd=cwd)


def blob(sha: str, path: str) -> bytes:
    return git("show", f"{sha}:{path}")


def load_json(raw: str | bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"JSONキー重複: {key}")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("JSON非有限数: " + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def read_json(path: Path) -> dict:
    return load_json(path.read_bytes())


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def exact_lines(log: str, prefix: str, expected: str) -> None:
    require([line for line in log.splitlines() if line.startswith(prefix)] == [expected],
            f"最終行欠落・重複・件数不一致: {prefix}")


def run_checked(command: list[str], cwd: Path, env: dict, output: Path,
                timeout: float | None, records: list) -> str:
    start = time.monotonic()
    timed_out = False
    with output.open("w", encoding="utf-8") as log:
        try:
            process = subprocess.run(command, cwd=cwd, env=env, stdout=log,
                                     stderr=subprocess.STDOUT, timeout=timeout)
            code = process.returncode
        except subprocess.TimeoutExpired:
            code, timed_out = 124, True
    text = output.read_text(encoding="utf-8")
    record = {"command": command, "cwd": str(cwd), "timeout_seconds": timeout,
              "exit_code": code, "timed_out": timed_out, "seconds": round(time.monotonic()-start, 3),
              "log": output.name, "log_sha256": sha256(output.read_bytes()),
              "bad_lines": [line for line in text.splitlines() if BAD_LOG.search(line)]}
    records.append(record)
    print(f"{output.name}: exit={code} seconds={record['seconds']}", flush=True)
    require(code == 0 and not timed_out and not record["bad_lines"], f"コマンド失敗/警告: {output}")
    return text


def check_core(report: dict, original: bool) -> None:
    require(report["status"] == "PASS" and report["failures"] == [], "装備条件失敗")
    require(report["checks"] == (5394 if original else 5487) and report["transitions"] == 400,
            "装備件数不一致")
    require(report["engine"] == "4.7.2-stable (official)", "装備エンジン不一致")
    if not original:
        require(report["legacy_checks"] == 5394 and report["additional_checks"] == 93, "追加93条件欠落")


def frozen_invalid() -> dict:
    return json.loads(blob(FIXED["038"], "docs/verification/equipment-validation/after-final/results.json"))


def check_invalid(report: dict, source_sha: str, directory: Path, reference: dict) -> None:
    require(report["source_sha"] == source_sha and report["engine"] == VERSION, "異常検査の対象版不一致")
    require((report["case_count"], report["passed"], report["checks"]) == (202, 202, 1576), "異常件数不一致")
    results = report["results"]
    require(len(results) == 202, "異常結果の欠落")
    require([r["case"] for r in results] == [r["case"] for r in reference["results"]], "異常ケースID/順不一致")
    require(len({r["case"] for r in results}) == 202, "異常ケース重複")
    total = 0
    for result, fixed in zip(results, reference["results"]):
        require(result["expectation"] == fixed["expectation"] and result["fixture_path"] == fixed["fixture_path"],
                "固定の異常期待不一致: " + result["case"])
        require(result["exit_code"] == 0 and result["status"] == "PASS" and result["errors"] == [], "異常子プロセス失敗")
        observed = result["observed"]
        require(len(observed) == 1 and observed[0]["failures"] == [] and observed[0]["input_unchanged"] is True,
                "異常観測の欠落/失敗/入力変更")
        require(observed[0]["checks"] == fixed["observed"][0]["checks"], "異常ケースのassert件数不一致")
        total += observed[0]["checks"]
        raw = (directory / (result["case"] + ".log")).read_bytes()
        log = raw.decode("utf-8")
        require(not BAD_LOG.search(log) and sha256(raw) == result["log_sha256"], "異常ログ警告/hash不一致")
        lines = [line.removeprefix("EQUIPMENT_INVALID_RESULT ") for line in log.splitlines()
                 if line.startswith("EQUIPMENT_INVALID_RESULT ")]
        require(len(lines) == 1 and json.loads(lines[0]) == observed[0], "異常ログとJSON不一致")
    require(total == 1576, "異常条件合計不一致")


def check_migration(report: dict, source_sha: str, reference: dict) -> None:
    require(report["source_sha"] == source_sha and report["stage"] == "S1", "S1対象版不一致")
    require(report["checks"] == 2828 and report["case_count"] == 61 and report["failures"] == [], "S1件数/失敗")
    require(report["cases"] == reference["cases"] and len(set(report["cases"])) == 61, "S1ケース欠落/重複/順不一致")
    require([(r["case"], r.get("reason_code"), r.get("count")) for r in report["observations"]] ==
            [(r["case"], r.get("reason_code"), r.get("count")) for r in reference["observations"]],
            "S1観測ID/固定成否理由/leaf検査数不一致")
    require(report["engine"]["string"] == "4.7.2-stable (official)" and
            report["not_verified"] == reference["not_verified"], "S1版/保証境界不一致")


@lru_cache
def frozen_legacy() -> dict:
    """041当時の旧基点実出力。最新実装から期待を作らない。"""
    return load_json(gzip.decompress(blob(MIGRATION_EVIDENCE,
        "docs/verification/equipment-save-migration/legacy-before.json.gz")))


def same_values_and_types(actual, expected, path: str = "legacy") -> None:
    require(type(actual) is type(expected), "旧出力の型不一致: " + path)
    if isinstance(expected, dict):
        require(actual.keys() == expected.keys(), "旧出力の必須フィールド不一致: " + path)
        for key in expected:
            same_values_and_types(actual[key], expected[key], path + "/" + key)
    elif isinstance(expected, list):
        require(len(actual) == len(expected), "旧出力の件数不一致: " + path)
        for i, (value, fixed) in enumerate(zip(actual, expected)):
            same_values_and_types(value, fixed, path + "/" + str(i))
    else:
        require(actual == expected, "旧出力の固定値不一致: " + path)


def check_legacy(report: dict) -> None:
    require((report["validation_count"], report["upgrade_count"]) == (142, 10) and report["failures"] == [], "旧入口件数/失敗")
    require(len(report["validation"]) == 142 and len(report["upgrades"]) == 10, "旧入口結果欠落")
    for key in ["validation", "upgrades"]:
        require(len({item["case"] for item in report[key]}) == len(report[key]), "旧入口ケース重複")
    require(all(item["unchanged"] is True for item in report["validation"]), "旧検証副作用")
    require(all(all(item[k] is True for k in ["imported", "saved", "loaded", "roundtrip"])
                for item in report["upgrades"]), "旧I/O往復失敗")
    # 全固定ID・valid・入力/純粋変換/前後state・型記録・metrics/履歴も必須。
    same_values_and_types(report, frozen_legacy())


@lru_cache
def fixed_fixture_hashes() -> dict:
    return {"tools/fixtures/equipment-save/" + name:
            sha256(blob(FIXED["041"], "tools/fixtures/equipment-save/" + name))
            for name in FIXTURE_FILES}


@lru_cache
def source_hashes(source_sha: str) -> dict:
    paths = set(git("ls-tree", "-r", "--name-only", source_sha).decode().splitlines())
    return {path: sha256(blob(source_sha, path)) for path in SOURCE_FILES if path in paths}


def check_legacy_commands(execution: dict, folder: Path, manifest: dict) -> None:
    commands = execution["commands"]
    require(type(commands) is list and len(commands) == 5, "旧入口必須5コマンド欠落")
    engine = commands[0]["command"][0]
    python = commands[1]["command"][0]
    checkout = commands[0]["cwd"]
    require(type(engine) is str and Path(engine).is_absolute() and
            Path(engine).name in ("godot", "Godot_v4.7.2-stable_linux.x86_64") and
            type(python) is str and Path(python).is_absolute() and
            re.fullmatch(r"python(?:3(?:\.\d+)?)?", Path(python).name) is not None and
            type(checkout) is str and Path(checkout).is_absolute() and Path(checkout).name == "checkout",
            "旧入口実行ファイル/checkout不一致")
    expected = [
        ("version.log", 30, [engine, "--version"]),
        ("frozen-before.log", 30, [python, "tools/check_frozen_files.py"]),
        ("import.log", 600, [engine, "--headless", "--path", checkout, "--editor", "--import", "--quit"]),
        ("legacy.log", 120, [engine, "--headless", "--path", checkout, "--script",
                              "res://tools/fixtures/equipment-save/legacy_equivalence.gd"]),
        ("frozen-after.log", 30, [python, "tools/check_frozen_files.py"]),
    ]
    protected_count = len(load_json(blob(execution["source_sha"], ".scope-lock/frozen-files.json"))["files"])
    for command, (name, budget, argv) in zip(commands, expected):
        require(command["log"] == name and command["command"] == argv and command["cwd"] == checkout,
                "旧入口コマンド種類/順/一意性/対象不一致: " + name)
        require(type(command["timeout_seconds"]) is int and command["timeout_seconds"] == budget and
                type(command["seconds"]) in (int, float) and math.isfinite(command["seconds"]) and
                0 <= command["seconds"] <= budget and type(command["exit_code"]) is int and
                command["exit_code"] == 0 and command["timed_out"] is False and command["bad_lines"] == [],
                "旧入口実行結果/予算不一致: " + name)
        raw = (folder / name).read_bytes()
        log = raw.decode("utf-8")
        require(sha256(raw) == command["log_sha256"] == manifest[name] and not BAD_LOG.search(log),
                "旧入口ログhash/警告不一致: " + name)
        if name == "version.log":
            require(log.strip() == VERSION, "旧入口Godot版ログ不一致")
        elif name.startswith("frozen-"):
            require(log.strip() == f"保護対象{protected_count}件、一致{protected_count}件。", "旧入口保護PASS欠落")
        else:
            require(log.splitlines()[0] == f"Godot Engine v{VERSION} - https://godotengine.org",
                    "旧入口Godot実行ログ欠落")
            if name == "legacy.log":
                exact_lines(log, "LEGACY_EQUIVALENCE_", "LEGACY_EQUIVALENCE_PASS: validation=142 upgrade=10 failures=0")
            else:
                clean = re.sub(r"\x1b\[[0-9;]*m", "", log)
                require("[ DONE ] loading_editor_layout" in clean, "旧入口import終了ログ欠落")


def check_scope(profile: str, output: Path) -> None:
    """変更範囲と未接続条件は当時の完成SHA間だけで照合する。"""
    files = {
        "036": ["data/equipment_rules.json", "scripts/game/equipment_rules.gd", "tools/check_equipment_rules.gd",
                "docs/design/equipment-content-options.md", "docs/tasks/036-equipment-core.md",
                "docs/tasks/reports/036-equipment-core.md"],
        "038": ["scripts/game/equipment_rules.gd", "tools/check_equipment_rules.gd",
                "tools/check_equipment_invalid_definitions.py", "docs/tasks/038-fix-equipment-validation.md",
                "docs/tasks/reports/038-fix-equipment-validation.md"],
        "041": ["scripts/game/game_session.gd", "scripts/game/integrated_progression.gd",
                "scripts/game/equipment_save_migration.gd", "scripts/game/equipment_save_migration.gd.uid",
                "scripts/game/equipment_save_validation.gd", "scripts/game/equipment_save_validation.gd.uid",
                "scripts/game/equipment_state_view.gd", "scripts/game/equipment_state_view.gd.uid",
                "tools/check_equipment_save_migration.gd", "tools/check_equipment_save_migration.gd.uid",
                "docs/tasks/041-equipment-save-migration.md", "docs/tasks/reports/041-equipment-save-migration.md"],
    }
    prefixes = {"036": "docs/verification/equipment-core/", "038": "docs/verification/equipment-validation/",
                "041": "tools/fixtures/equipment-save/"}
    changed = git("diff", "--name-only", BASE[profile], FIXED[profile]).decode().splitlines()
    allowed = set(files[profile] + ["docs/decision-log.md"])
    require(changed and all(p in allowed or p.startswith(prefixes[profile]) for p in changed), "固定完成版の担当外差分")
    require(not git("diff", "--name-only", BASE[profile], FIXED[profile], "--",
                    ".github", ".scope-lock", "test", "assets", "addons"), "固定完成版の保護・workflow・原画変更")
    if profile in ["036", "038"]:
        require(not git("diff", "--name-only", BASE[profile], FIXED[profile], "--",
                        "scripts/game/game_session.gd", "scripts/game/integrated_progression.gd"), "固定版のゲーム接続変更")
    if profile == "038":
        old = blob(FIXED["036"], "tools/check_equipment_rules.gd").split(b"func _initialize()")[0]
        require(blob(FIXED["038"], "tools/check_equipment_rules.gd").startswith(old), "036全検査本文の改変")
    write_json(output / "scope.json", {"status": "PASS", "profile": profile, "base_sha": BASE[profile],
               "completed_sha": FIXED[profile], "changed_paths": changed,
               "classification": "当時だけの変更範囲/未接続。最新の接続禁止へ転用しない"})


def compare_legacy(inputs: Path, output: Path, latest_sha: str) -> None:
    versions = {"baseline": FIXED["baseline"], "041": FIXED["041"], "latest": latest_sha}
    hashes = {}
    fixture_hashes = fixed_fixture_hashes()
    baseline = None
    for profile, expected_sha in versions.items():
        folder = inputs / ("equipment-legacy-" + profile)
        execution = read_json(folder / "execution.json")
        require(execution["status"] == "PASS" and execution["suite"] == "legacy" and execution["profile"] == profile and
                execution["source_sha"] == expected_sha and execution["latest_sha"] == latest_sha,
                "旧入口artifactの実行版/成否不一致")
        require(execution["fixture_sha"] == FIXED["041"], "旧入口固定fixture版不一致")
        require(execution["engine"] == VERSION and execution["engine_sha256"] == ENGINE_SHA256 and
                execution["wrapper_sha256"] == sha256(blob(latest_sha, "tools/run_equipment_ci.py")),
                "旧入口engine/wrapper原本hash不一致")
        require(execution["source_sha256"] == source_hashes(expected_sha), "旧入口対象checkout原本hash不一致")
        manifest = read_json(folder / "sha256.json")
        check_legacy_commands(execution, folder, manifest)
        require(manifest["legacy.json"] == sha256((folder / "legacy.json").read_bytes()), "旧入口出力hash不一致")
        require(execution["fixture_sha256"] == fixture_hashes, "固定041 fixture5原本hash不一致")
        raw = (folder / "legacy.json").read_bytes()
        check_legacy(read_json(folder / "legacy.json"))
        if baseline is None:
            baseline = raw
        require(raw == baseline, "旧人物処理の前後出力不一致: " + profile)
        hashes[profile] = sha256(raw)
    write_json(output / "comparison.json", {"status": "PASS", "versions": versions,
               "fixture_sha": FIXED["041"], "fixture_sha256": fixture_hashes,
               "output_sha256": hashes, "validation_count": 142, "upgrade_count": 10})


def comparison_fixtures(output: Path, scripts: dict) -> None:
    """044全12プローブを含む追加42件。各改変は別artifactコピーへ限定する。"""
    latest_sha = git("rev-parse", "HEAD").decode().strip()
    originals = output / "comparison-originals"
    originals.mkdir()
    engine = "/fixture/bin/godot"
    python = "/fixture/bin/python"
    checkout = "/fixture/checkout"
    log_data = [VERSION + "\n", "保護対象26件、一致26件。\n",
                f"Godot Engine v{VERSION} - https://godotengine.org\n[ DONE ] loading_editor_layout\n",
                f"Godot Engine v{VERSION} - https://godotengine.org\nLEGACY_EQUIVALENCE_PASS: validation=142 upgrade=10 failures=0\n",
                "保護対象26件、一致26件。\n"]
    definitions = [
        ("version.log", 30, [engine, "--version"]),
        ("frozen-before.log", 30, [python, "tools/check_frozen_files.py"]),
        ("import.log", 600, [engine, "--headless", "--path", checkout, "--editor", "--import", "--quit"]),
        ("legacy.log", 120, [engine, "--headless", "--path", checkout, "--script",
                             "res://tools/fixtures/equipment-save/legacy_equivalence.gd"]),
        ("frozen-after.log", 30, [python, "tools/check_frozen_files.py"]),
    ]
    for profile, source in {"baseline": FIXED["baseline"], "041": FIXED["041"], "latest": latest_sha}.items():
        folder = originals / ("equipment-legacy-" + profile)
        folder.mkdir()
        commands = []
        for (name, budget, argv), log in zip(definitions, log_data):
            (folder / name).write_text(log, encoding="utf-8")
            commands.append({"command": argv, "cwd": checkout, "timeout_seconds": budget,
                             "exit_code": 0, "timed_out": False, "seconds": 1,
                             "log": name, "log_sha256": sha256(log.encode()), "bad_lines": []})
        write_json(folder / "legacy.json", frozen_legacy())
        write_json(folder / "execution.json", {"status": "PASS", "suite": "legacy", "profile": profile,
                   "source_sha": source, "latest_sha": latest_sha, "fixture_sha": FIXED["041"],
                   "fixture_sha256": fixed_fixture_hashes(), "commands": commands,
                   "engine": VERSION, "engine_sha256": ENGINE_SHA256,
                   "wrapper_sha256": sha256(blob(latest_sha, "tools/run_equipment_ci.py")),
                   "source_sha256": source_hashes(source)})
        write_json(folder / "sha256.json", {p.name: sha256(p.read_bytes()) for p in folder.iterdir()})
    names = ["control", "missing_artifact", "wrong_source", "stale_artifact", "failed_log",
             "duplicate_command", "no_original_command", "no_pass_line", "timeout_record", "missing_commands",
             "empty_fixture_hashes", "fake_success_json", "command_lookalike", "wrong_checkout", "wrong_cwd",
             "wrong_budget", "over_budget", "nonfinite_seconds", "bool_exit", "bool_budget", "false_engine",
             "wrong_wrapper", "missing_source_hash", "duplicate_pass", "version_no_pass", "protection_no_pass",
             "import_no_completion", "fixture_wrong_hash", "fixture_missing", "output_missing_valid",
             "output_wrong_case", "output_duplicate_case", "output_missing_metrics", "output_missing_history",
             "output_missing_types", "output_wrong_value", "output_wrong_type", "output_wrong_valid",
             "output_failed", "missing_manifest_log", "wrong_manifest_log", "wrong_output_hash"]
    for name in names:
        inputs = output / ("comparison-" + name)
        shutil.copytree(originals, inputs)
        folder = inputs / "equipment-legacy-latest"
        execution = read_json(folder / "execution.json")
        command = execution["commands"][3]
        if name == "missing_artifact":
            shutil.rmtree(folder)
        else:
            if name == "wrong_source": execution["source_sha"] = "0"*40
            if name == "stale_artifact": execution["latest_sha"] = "0"*40
            if name == "duplicate_command": execution["commands"] = [copy.deepcopy(execution["commands"][0]) for _ in range(5)]
            if name == "no_original_command": command["command"] = ["true"]
            if name == "missing_commands": execution["commands"] = []
            if name == "timeout_record": command["timed_out"] = True
            if name == "command_lookalike": command["command"][0] = "/fixture/bin/true"
            if name == "wrong_checkout": command["command"][3] = "/other/checkout"
            if name == "wrong_cwd": command["cwd"] = "/other/checkout"
            if name == "wrong_budget": command["timeout_seconds"] = 121
            if name == "over_budget": command["seconds"] = 121
            if name == "nonfinite_seconds": command["seconds"] = float("nan")
            if name == "bool_exit": command["exit_code"] = False
            if name == "bool_budget": command["timeout_seconds"] = True
            if name == "false_engine": execution["engine_sha256"] = "0"*64
            if name == "wrong_wrapper": execution["wrapper_sha256"] = "0"*64
            if name == "missing_source_hash": execution["source_sha256"] = {}
            log_cases = {"failed_log": (3, "ERROR: fixture\n"), "no_pass_line": (3, "not executed\n"),
                         "duplicate_pass": (3, log_data[3] + log_data[3]), "version_no_pass": (0, "not executed\n"),
                         "protection_no_pass": (1, "not executed\n"), "import_no_completion": (2, "not executed\n")}
            if name in log_cases:
                index, text = log_cases[name]
                execution["commands"][index]["log_sha256"] = sha256(text.encode())
                (folder / definitions[index][0]).write_text(text, encoding="utf-8")
            write_json(folder / "execution.json", execution)
            for profile in ["baseline", "041", "latest"]:
                target = inputs / ("equipment-legacy-" + profile)
                if name in ["empty_fixture_hashes", "fixture_wrong_hash", "fixture_missing"]:
                    changed = read_json(target / "execution.json")
                    if name == "empty_fixture_hashes": changed["fixture_sha256"] = {}
                    if name == "fixture_wrong_hash": changed["fixture_sha256"][next(iter(changed["fixture_sha256"]))] = "0"*64
                    if name == "fixture_missing": changed["fixture_sha256"].pop(next(iter(changed["fixture_sha256"])))
                    write_json(target / "execution.json", changed)
                if name == "fake_success_json" or name.startswith("output_"):
                    report = copy.deepcopy(frozen_legacy())
                    if name == "fake_success_json":
                        report = {"validation_count": 142, "upgrade_count": 10, "failures": [],
                                  "validation": [{"case": str(i), "unchanged": True} for i in range(142)],
                                  "upgrades": [{"case": str(i), "imported": True, "saved": True, "loaded": True,
                                                "roundtrip": True} for i in range(10)]}
                    if name == "output_missing_valid": report["validation"][0].pop("valid")
                    if name == "output_wrong_case": report["validation"][0]["case"] = "fake-case"
                    if name == "output_duplicate_case": report["validation"][1]["case"] = report["validation"][0]["case"]
                    if name == "output_missing_metrics": report["upgrades"][0].pop("metrics_after")
                    if name == "output_missing_history": report["upgrades"][0]["metrics_after"].pop("events")
                    if name == "output_missing_types": report["upgrades"][0].pop("after_types")
                    if name == "output_wrong_value": report["upgrades"][0]["after"]["party"][0]["hp"] += 1
                    if name == "output_wrong_type": report["upgrades"][0]["after"]["party"][0]["hp"] = float(report["upgrades"][0]["after"]["party"][0]["hp"])
                    if name == "output_wrong_valid": report["validation"][0]["valid"] = False
                    if name == "output_failed": report["failures"] = ["fixture"]
                    write_json(target / "legacy.json", report)
                # log/output改変後にもmanifestを整合させ、意味の検証まで実行させる。
                write_json(target / "sha256.json", {p.name: sha256(p.read_bytes()) for p in target.iterdir() if p.name != "sha256.json"})
            manifest = read_json(folder / "sha256.json")
            if name == "missing_manifest_log": manifest.pop("legacy.log")
            if name == "wrong_manifest_log": manifest["legacy.log"] = "0"*64
            if name == "wrong_output_hash": manifest["legacy.json"] = "0"*64
            write_json(folder / "sha256.json", manifest)
        result = output / ("comparison-result-" + name)
        result.mkdir()
        scripts["comparison_" + name] = (f"m.compare_legacy(pathlib.Path({str(inputs)!r}), "
                                           f"pathlib.Path({str(result)!r}), {latest_sha!r})\n")


def self_test(output: Path) -> None:
    """専用fixtureを別Pythonで拒否し、実際のexit1まで確認する。"""
    cases = []
    module_path = str(Path(__file__).resolve())
    preamble = ("import importlib.util, pathlib, os\n"
                f"s=importlib.util.spec_from_file_location('equipment_ci', {module_path!r})\n"
                "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)\n")
    scripts = {"control": "m.require(True, '対照')\n"}
    for name, text, code, budget in [
        ("exit1", "PASS", 1, 2), ("warning", "WARNING: fixture", 0, 2),
        ("script_error", "SCRIPT ERROR fixture", 0, 2), ("parse_error", "Parse Error fixture", 0, 2),
        ("error", "ERROR: fixture", 0, 2), ("fail_marker", "EQUIPMENT_CORE_FAIL: fixture", 0, 2),
        ("timeout", "", 0, 0.05),
    ]:
        child = "import time; time.sleep(1)" if name == "timeout" else f"print({text!r}); raise SystemExit({code})"
        scripts[name] = (f"m.run_checked([{sys.executable!r}, '-c', {child!r}], pathlib.Path({str(ROOT)!r}), "
                         f"os.environ.copy(), pathlib.Path({str(output / (name+'-child.log'))!r}), {budget}, [])\n")
    core = {"status": "PASS", "failures": [], "checks": 5487, "transitions": 400,
            "legacy_checks": 5394, "additional_checks": 93, "engine": "4.7.2-stable (official)"}
    scripts["core_control"] = f"m.check_core({core!r}, False)\n"
    for name, field, value in [("core_count", "checks", 5486), ("core_missing_additional", "additional_checks", 92),
                               ("core_failure", "failures", ["fixture"]), ("core_transition", "transitions", 399)]:
        bad = {**core, field: value}
        scripts[name] = f"m.check_core({bad!r}, False)\n"
    for name, log in [("missing_pass", ""), ("duplicate_pass", "PASS\nPASS\n"), ("wrong_count", "PASS: cases=60")]:
        scripts[name] = f"m.exact_lines({log!r}, 'PASS', 'PASS')\n"
    # 元35fixtureの全ID・拒否変異を維持。正常旧対照には省略されていた原本フィールドを補う。
    legacy = copy.deepcopy(frozen_legacy())
    scripts["legacy_control"] = f"m.check_legacy({legacy!r})\n"
    for name in ["legacy_missing", "legacy_failure", "legacy_duplicate", "legacy_roundtrip"]:
        bad = copy.deepcopy(legacy)
        if name == "legacy_missing": bad["validation"].pop()
        if name == "legacy_failure": bad["failures"] = ["fixture"]
        if name == "legacy_duplicate": bad["upgrades"][1]["case"] = bad["upgrades"][0]["case"]
        if name == "legacy_roundtrip": bad["upgrades"][0]["roundtrip"] = False
        scripts[name] = f"m.check_legacy({bad!r})\n"
    migration = {"source_sha": "a"*40, "stage": "S1", "checks": 2828, "case_count": 61,
                 "failures": [], "cases": [str(i) for i in range(61)],
                 "observations": [{"case": str(i), "reason_code": "ok"} for i in range(61)],
                 "engine": {"string": "4.7.2-stable (official)"}, "not_verified": ["fixture-boundary"]}
    scripts["migration_control"] = f"m.check_migration({migration!r}, {'a'*40!r}, {migration!r})\n"
    for name in ["migration_count", "migration_missing", "migration_duplicate", "migration_failure", "migration_sha"]:
        bad = copy.deepcopy(migration)
        if name == "migration_count": bad["checks"] -= 1
        if name == "migration_missing": bad["cases"].pop()
        if name == "migration_duplicate": bad["cases"][1] = bad["cases"][0]
        if name == "migration_failure": bad["failures"] = ["fixture"]
        if name == "migration_sha": bad["source_sha"] = "b"*40
        scripts[name] = f"m.check_migration({bad!r}, {'a'*40!r}, {migration!r})\n"
    # 実装出力を使わない専用異常fixture。名前・件数・期待・子観測・生ログを別々に反証。
    invalid_dir = output / "invalid-fixture"
    invalid_dir.mkdir()
    results = []
    for i in range(202):
        observed = {"checks": 7 if i < 40 else 8, "failures": [], "input_unchanged": True}
        raw = "EQUIPMENT_INVALID_RESULT " + json.dumps(observed) + "\n"
        (invalid_dir / f"fixture-{i}.log").write_text(raw, encoding="utf-8")
        results.append({"case": f"fixture-{i}", "expectation": {"mode": "invalid"}, "fixture_path": None,
                        "exit_code": 0, "status": "PASS", "errors": [], "observed": [observed],
                        "log_sha256": sha256(raw.encode())})
    invalid = {"source_sha": "a"*40, "engine": VERSION, "case_count": 202, "passed": 202, "checks": 1576, "results": results}
    write_json(invalid_dir / "reference.json", invalid)
    invalid_call = (f"m.check_invalid(m.read_json(pathlib.Path(INPUT)), {'a'*40!r}, "
                    f"pathlib.Path({str(invalid_dir)!r}), m.read_json(pathlib.Path({str(invalid_dir / 'reference.json')!r})))\n")
    scripts["invalid_control"] = f"INPUT={str(invalid_dir / 'reference.json')!r}\n" + invalid_call
    for name in ["invalid_count", "invalid_missing", "invalid_duplicate", "invalid_failure", "invalid_exit", "invalid_warning", "invalid_log_hash"]:
        bad = copy.deepcopy(invalid)
        if name == "invalid_count": bad["checks"] -= 1
        if name == "invalid_missing": bad["results"].pop()
        if name == "invalid_duplicate": bad["results"][1]["case"] = bad["results"][0]["case"]
        if name == "invalid_failure": bad["results"][0]["observed"][0]["failures"] = ["fixture"]
        if name == "invalid_exit": bad["results"][0]["exit_code"] = 1
        if name == "invalid_warning": bad["results"][0]["errors"] = ["WARNING: fixture"]
        if name == "invalid_log_hash": bad["results"][0]["log_sha256"] = "0"*64
        write_json(output / (name + ".json"), bad)
        scripts[name] = f"INPUT={str(output / (name + '.json'))!r}\n" + invalid_call
    comparison_fixtures(output, scripts)
    for name, script in scripts.items():
        expected = 0 if name.endswith("control") else 1
        log_file = output / (name + ".log")
        with log_file.open("w", encoding="utf-8") as log:
            process = subprocess.run([sys.executable, "-c", preamble + script], cwd=ROOT,
                                     stdout=log, stderr=subprocess.STDOUT, timeout=10)
        require(process.returncode == expected, f"失敗伝播fixture誤判定: {name}")
        cases.append({"case": name, "expected_exit": expected, "observed_exit": process.returncode,
                      "log": log_file.name, "log_sha256": sha256(log_file.read_bytes())})
    write_json(output / "failure-propagation.json", {"status": "PASS", "cases": cases,
               "note": "専用fixtureの子exit1は期待結果。本番検査のFAILを成功扱いする例外ではない"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True, choices=["core", "invalid", "migration", "legacy", "compare", "self-test"])
    parser.add_argument("--profile", choices=[*FIXED, "latest"], default="latest")
    parser.add_argument("--latest-sha", required=True)
    parser.add_argument("--godot", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inputs", type=Path)
    args = parser.parse_args()
    require(re.fullmatch(r"[0-9a-f]{40}", args.latest_sha) is not None, "最新対象は完全SHAが必要")
    require(git("rev-parse", "HEAD").decode().strip() == args.latest_sha, "wrapper checkoutと最新SHA不一致")
    source = args.latest_sha if args.profile == "latest" else FIXED[args.profile]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    record = {"status": "FAIL", "suite": args.suite, "profile": args.profile,
              "source_sha": source, "latest_sha": args.latest_sha, "commands": [],
              "wrapper_sha256": sha256(Path(__file__).read_bytes())}
    target = None
    temp = None
    try:
        if args.suite == "self-test":
            self_test(output)
        elif args.suite == "compare":
            require(args.inputs is not None, "比較artifactが必要")
            compare_legacy(args.inputs.resolve(), output, args.latest_sha)
        else:
            require(args.godot is not None, "指定Godotが必要")
            allowed = {"core": ["036", "038", "041", "latest"], "invalid": ["038", "041", "latest"],
                       "migration": ["041", "latest"], "legacy": ["baseline", "041", "latest"]}
            require(args.profile in allowed[args.suite], "存在しない段階の検査")
            engine = str(args.godot.resolve())
            temp = tempfile.TemporaryDirectory(prefix=f"equipment-ci-{args.suite}-{args.profile}-")
            folder = Path(temp.name)
            target = folder / "checkout"
            git("worktree", "add", "--detach", str(target), source)
            require(git("rev-parse", "HEAD", cwd=target).decode().strip() == source, "対象checkout SHA不一致")
            record["source_sha256"] = {p: sha256((target / p).read_bytes()) for p in SOURCE_FILES if (target / p).is_file()}
            env = os.environ.copy()
            for name in ["CACHE", "CONFIG", "DATA"]:
                path = folder / "xdg" / name.lower()
                path.mkdir(parents=True)
                env[f"XDG_{name}_HOME"] = str(path)
            env["PATH"] = str(Path(engine).parent) + os.pathsep + env.get("PATH", "")
            version = run_checked([engine, "--version"], target, env, output / "version.log", 30, record["commands"])
            require(version.strip() == VERSION, "Godot公式指定版不一致")
            record["engine"] = VERSION
            record["engine_sha256"] = sha256(Path(engine).read_bytes())
            run_checked([sys.executable, "tools/check_frozen_files.py"], target, env,
                        output / "frozen-before.log", 30, record["commands"])
            if args.profile in ["036", "038", "041"] and args.suite in ["core", "migration"]:
                check_scope(args.profile, output)
            if args.suite == "legacy":
                fixture_hashes = {}
                for name in FIXTURE_FILES:
                    path = "tools/fixtures/equipment-save/" + name
                    raw = blob(FIXED["041"], path)
                    destination = target / path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(raw)
                    fixture_hashes[path] = sha256(raw)
                record.update(fixture_sha=FIXED["041"], fixture_sha256=fixture_hashes)
            if args.suite != "invalid":
                run_checked([engine, "--headless", "--path", str(target), "--editor", "--import", "--quit"],
                            target, env, output / "import.log", 600, record["commands"])
            if args.suite == "core":
                original = args.profile == "036"
                generated = target / ("docs/verification/equipment-core/checks.json" if original else
                                      "docs/verification/equipment-validation/core-checks.json")
                # 原検査が固定名へ書くのは使い捨てcheckout内だけ。古い結果を読まない。
                generated.unlink(missing_ok=True)
                log = run_checked([engine, "--headless", "--path", str(target), "--script", "res://tools/check_equipment_rules.gd"],
                                  target, env, output / "core.log", 240, record["commands"])
                exact_lines(log, "EQUIPMENT_CORE_", "EQUIPMENT_CORE_PASS: checks=5394 transitions=400 failures=0")
                if not original:
                    exact_lines(log, "EQUIPMENT_VALIDATION_", "EQUIPMENT_VALIDATION_PASS: additional_checks=93 failures=0")
                shutil.copyfile(generated, output / "core.json")
                check_core(read_json(output / "core.json"), original)
            elif args.suite == "invalid":
                log = run_checked([sys.executable, "tools/check_equipment_invalid_definitions.py", "--source-sha", source,
                                   "--godot", engine, "--output", str(output / "invalid")], target, env,
                                  output / "invalid.log", None, record["commands"])
                exact_lines(log, "EQUIPMENT_INVALID:", "EQUIPMENT_INVALID: cases=202 passed=202 checks=1576 failed=0")
                check_invalid(read_json(output / "invalid/results.json"), source, output / "invalid", frozen_invalid())
            elif args.suite == "migration":
                env.update(RPG_EQUIPMENT_SAVE_OUTPUT=str(output / "migration.json"), RPG_EQUIPMENT_SAVE_EXECUTION_SHA=source)
                log = run_checked([engine, "--headless", "--path", str(target), "--script", "res://tools/check_equipment_save_migration.gd"],
                                  target, env, output / "migration.log", 120, record["commands"])
                exact_lines(log, "EQUIPMENT_SAVE_MIGRATION_", "EQUIPMENT_SAVE_MIGRATION_PASS: cases=61 checks=2828 failed=0")
                # ケース一覧は当時の原検査を実行した保存証拠。期待JSONは変更しない。
                reference = json.loads(blob(MIGRATION_EVIDENCE, "docs/verification/equipment-save-migration/migration.json"))
                check_migration(read_json(output / "migration.json"), source, reference)
            elif args.suite == "legacy":
                env["RPG_LEGACY_EQ_OUTPUT"] = str(output / "legacy.json")
                log = run_checked([engine, "--headless", "--path", str(target), "--script", "res://tools/fixtures/equipment-save/legacy_equivalence.gd"],
                                  target, env, output / "legacy.log", 120, record["commands"])
                exact_lines(log, "LEGACY_EQUIVALENCE_", "LEGACY_EQUIVALENCE_PASS: validation=142 upgrade=10 failures=0")
                check_legacy(read_json(output / "legacy.json"))
        record["status"] = "PASS"
    except (RuntimeError, OSError, ValueError, KeyError, IndexError, TypeError, subprocess.SubprocessError) as error:
        record["error"] = str(error)
        print("EQUIPMENT_CI_FAIL: " + str(error), file=sys.stderr)
    finally:
        if target is not None:
            try:
                run_checked([sys.executable, "tools/check_frozen_files.py"], target, env,
                            output / "frozen-after.log", 30, record["commands"])
            except (RuntimeError, OSError, subprocess.SubprocessError) as error:
                record.update(status="FAIL", protection_error=str(error))
            try:
                git("worktree", "remove", "--force", str(target))
            except subprocess.SubprocessError as error:
                record.update(status="FAIL", cleanup_error=str(error))
        if temp is not None:
            temp.cleanup()
        write_json(output / "execution.json", record)
        write_json(output / "sha256.json", {str(p.relative_to(output)): sha256(p.read_bytes())
                   for p in sorted(output.rglob("*")) if p.is_file() and p.name != "sha256.json"})
    print(f"EQUIPMENT_CI_{record['status']}: suite={args.suite} profile={args.profile} source={source}")
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
