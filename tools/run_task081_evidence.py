#!/usr/bin/env python3
"""081の境界と既存受入を原コマンド・原判定器・原時間上限で記録する。"""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from run_locked_checks import judge_output

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/verification/task-081"
ENGINE = ROOT / ".tools/godot/4.7.2/godot"


def main():
    env = dict(os.environ)
    env["PATH"] = str(ENGINE.parent) + os.pathsep + env["PATH"]
    env["RPG_QA_SAVE_PREFIX"] = "task081"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for suffix in ["CACHE", "DATA", "CONFIG"]:
        path = ROOT / ".tools/task081" / suffix.lower()
        path.mkdir(parents=True, exist_ok=True)
        env["XDG_" + suffix + "_HOME"] = str(path)
    contract = json.loads((ROOT / ".scope-lock/spec.lock.json").read_text())
    results = []

    def run(label, command, timeout, requirement=False):
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        timed_out = False
        try:
            process = subprocess.run(shlex.split(command), cwd=ROOT, env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            code, raw = process.returncode, process.stdout
        except subprocess.TimeoutExpired as exc:
            code, raw, timed_out = 124, exc.stdout or b"", True
        finished = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (OUT / (label + ".log.gz")).write_bytes(gzip.compress(raw, mtime=0))
        text = raw.decode("utf-8", errors="replace")
        judged = judge_output(label, command, code, text, timed_out) if requirement else {
            "status": "PASS" if code == 0 and not any(term in text for term in ["SCRIPT ERROR", "ERROR:", "WARNING:", "Parse Error"]) else "FAIL"}
        result = dict(label=label, command=command, timeout_seconds=timeout, started=started, finished=finished,
                      exit=code, timed_out=timed_out, raw_log_sha256=hashlib.sha256(raw).hexdigest(), result=judged)
        results.append(result)
        (OUT / "execution-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
        print(label, code, judged["status"], flush=True)

    run("engine-version", "godot --version", 30)
    run("editor-import", "godot --headless --editor --import --quit", 600)
    run("frozen-before-verify", f"{sys.executable} tools/check_frozen_files.py", 30)
    run("python-boundary", f"{sys.executable} tools/check_task081_connection_boundary.py", 60)
    run("runtime-boundary", "godot --headless --path . --script res://tools/check_task081_connection_boundary.gd", 120)
    run("assets-strict", f"{sys.executable} tools/validate_assets.py --strict", 180)
    for requirement in contract["requirements"]:
        run(requirement["id"], requirement["verify"], 300, True)
    run("frozen-after-verify", f"{sys.executable} tools/check_frozen_files.py", 30)
    return 0 if all(result["result"]["status"] == "PASS" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
