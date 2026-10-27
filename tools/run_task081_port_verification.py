#!/usr/bin/env python3
"""081本番接続の回帰検証。原verify・原判定器と既存の上限を維持する。"""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from run_locked_checks import judge_output

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/verification/task-081-implementation"
ENGINE = ROOT / ".tools/godot/4.7.2/godot"


def main():
    if (OUT / "regression-execution.json").exists():
        archive = OUT / "attempts" / ("regression-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        archive.mkdir(parents=True, exist_ok=True)
        for pattern in ["verify-*.log.gz", "regression-execution.json", "api-runtime.json", "data-checks.json"]:
            for file in OUT.glob(pattern):
                shutil.copyfile(file, archive / file.name)
    inputs = [*ROOT.glob("scripts/world/first_region*.gd"), ROOT / "scripts/world/region3_port.gd",
              ROOT / "world/region3_port.json", ROOT / "assets/registry.json", ROOT / "tools/validate_assets.py",
              *ROOT.glob("tools/check_task081_port*"), ROOT / "assets/town_backdrops/region3_port.png"]
    (OUT / "verified-source-sha256.json").write_text(json.dumps({str(file.relative_to(ROOT)): hashlib.sha256(file.read_bytes()).hexdigest() for file in inputs}, ensure_ascii=False, indent=2) + "\n")
    env = dict(os.environ, RPG_QA_SAVE_PREFIX="task081_regression", PYTHONDONTWRITEBYTECODE="1")
    env["PATH"] = str(ENGINE.parent) + os.pathsep + env["PATH"]
    for category in ["CACHE", "CONFIG", "DATA"]:
        path = ROOT / ".tools/task081/regression" / category.lower()
        path.mkdir(parents=True, exist_ok=True)
        env["XDG_" + category + "_HOME"] = str(path)
    records = []

    def run(name, command, limit, requirement=False):
        start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        timed_out = False
        try:
            result = subprocess.run(shlex.split(command), cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=limit)
            code, raw = result.returncode, result.stdout
        except subprocess.TimeoutExpired as exc:
            code, raw, timed_out = 124, exc.stdout or b"", True
        text = raw.decode("utf-8", errors="replace")
        (OUT / ("verify-" + name + ".log.gz")).write_bytes(gzip.compress(raw, mtime=0))
        judged = judge_output(name, command, code, text, timed_out) if requirement else {
            "status": "PASS" if code == 0 and not any(value in text for value in ["SCRIPT ERROR", "ERROR:", "WARNING:", "Parse Error", "_FAIL:"]) else "FAIL"}
        records.append(dict(name=name, command=command, cwd=str(ROOT), started=start,
                            finished=datetime.datetime.now(datetime.timezone.utc).isoformat(), timeout_seconds=limit,
                            exit_code=code, timed_out=timed_out, result=judged, raw_log_sha256=hashlib.sha256(raw).hexdigest()))
        (OUT / "regression-execution.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
        print(name, code, judged["status"], flush=True)

    run("engine", "godot --version", 30)
    run("editor-import", "godot --headless --editor --import --quit", 600)
    run("frozen-before", f"{sys.executable} tools/check_frozen_files.py", 30)
    run("data", f"{sys.executable} tools/check_task081_port_data.py", 120)
    run("assets", f"{sys.executable} tools/validate_assets.py --strict", 180)
    for requirement in json.loads((ROOT / ".scope-lock/spec.lock.json").read_text())["requirements"]:
        run(requirement["id"], requirement["verify"], 300, True)
    for name, limit in [("saved_value_types", 60), ("saved_position_relocation", 120),
                        ("coastal_travel", 180), ("second_region_coast", 180), ("region2_port", 180),
                        ("region2_port_backdrop", 120), ("region2_village_backdrops", 120),
                        ("first_region_screen", 180), ("battle_recovery", 180), ("enemy_encounters", 180),
                        ("task081_port_runtime", 120)]:
        run(name, "godot --headless --path . --script res://tools/check_" + name + ".gd", limit)
    run("frozen-after", f"{sys.executable} tools/check_frozen_files.py", 30)
    return 0 if all(record["result"]["status"] == "PASS" for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
