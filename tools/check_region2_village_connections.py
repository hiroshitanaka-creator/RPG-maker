#!/usr/bin/env python3
"""006専用の固定コミット比較と、Godotの実保存・別プロセス復帰を検査する。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = "552261345f68a4916ddeefad959896b44da2fcbf"
REQUEST = "3ddbbc14289599f529421a3587a5b7973a000545"
OUT = ROOT / "docs/verification/region2-village-connections"
ALLOWED = {
    "scripts/world/first_region.gd", "scripts/world/first_region_travel.gd",
    "scripts/world/first_region_presentation.gd", "scripts/world/first_region_view.gd",
    "scripts/world/region2_village.gd", "scripts/world/region2_village.gd.uid",
    "world/region2_village.json", "tools/check_region2_village_connections.gd",
    "tools/check_region2_village_connections.gd.uid", "tools/check_region2_village_connections.py",
    "tools/capture_region2_village_connections.gd", "tools/capture_region2_village_connections.gd.uid",
    "docs/region2-village-connections.md", "docs/tasks/reports/006-connect-village-shells.md",
    "docs/tasks/006-connect-village-shells.md", "docs/decision-log.md", "PLAYTEST_QUEUE.md",
    ".github/workflows/region2-village-connections.yml",
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def write(name: str, document: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scope(commit: str) -> dict:
    """作業ツリーを比較対象にせず、開始mainと指定コミットの全パスを比較する。"""
    target = git("rev-parse", commit + "^{commit}").decode().strip()
    changed = git("diff", "--name-only", BASE, target).decode().splitlines()
    denied = [s for s in changed if s not in ALLOWED and not s.startswith("docs/verification/region2-village-connections/")]
    deleted = git("diff", "--diff-filter=D", "--name-only", BASE, target).decode().splitlines()
    original = git("show", REQUEST + ":docs/tasks/006-connect-village-shells.md").decode()
    current = git("show", target + ":docs/tasks/006-connect-village-shells.md").decode()
    normalize = lambda s: re.sub(r"^- 状態：.*$", "- 状態：比較除外", s, count=1, flags=re.M)
    failures = denied + deleted
    if normalize(original) != normalize(current):
        failures.append("006依頼書の状態行以外が変更されています")
    def tree(ref: str) -> dict:
        return {row.split("\t", 1)[1]: row.split()[2] for row in git("ls-tree", "-r", ref).decode().splitlines()}
    a, b = tree(BASE), tree(target)
    original_paths = [s for s in a if s.startswith(("assets/", "test/", ".scope-lock/")) or (s.startswith("tools/") and s not in ALLOWED) or s in ["project.godot", ".github/workflows/ci.yml", "world/region2_village_backdrops.json", "world/region2_port.json", "world/second_region_coast.json"]]
    altered = [s for s in original_paths if a[s] != b.get(s)]
    failures += altered
    originals = [s for s in a if s.startswith("assets/_incoming/owner-2026-10-04-grok-region3/")]
    return {"status": "PASS" if not failures else "FAIL", "base": BASE, "commit": target,
            "changed_files": changed, "failures": failures, "protected_and_existing_unchanged": len(original_paths),
            "grok_originals_unchanged": len(originals), "checks_weakened_or_removed": 0 if not altered else None,
            "method": "固定開始mainと指定コミットのGitツリー・blobを比較。既存検査・CI全バイト不変。"}


def run_godot(exe: str, sha: str, name: str, extra: list[str]) -> dict:
    command = [exe, "--headless", "--path", str(ROOT), "--script", "res://tools/check_region2_village_connections.gd", *extra]
    env = os.environ.copy()
    env["RPG006_EXECUTION_SHA"] = sha
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
    text = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    (OUT / (name + ".log")).write_text(text, encoding="utf-8")
    bad = [s for s in text.splitlines() if re.search(r"SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL", s)]
    report = json.loads((OUT / (name + ".json")).read_text(encoding="utf-8"))
    ok = result.returncode == 0 and not bad and report["status"] == "PASS" and report["checks"] > 0 and report["execution_sha"] == sha
    print(f"{name}: {'PASS' if ok else 'FAIL'} checks={report['checks']} exit={result.returncode}", flush=True)
    return {"status": "PASS" if ok else "FAIL", "command": command, "exit_code": result.returncode, "errors": bad, "checks": report["checks"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--scope-only", action="store_true")
    parser.add_argument("--runtime-only", action="store_true")
    parser.add_argument("--godot", default=os.environ.get("GODOT", "godot"))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sha = git("rev-parse", args.commit + "^{commit}").decode().strip()
    checks = {}
    if not args.runtime_only:
        checks["scope"] = scope(sha)
        write("scope-checks.json", checks["scope"])
        print("scope:", checks["scope"]["status"], "changed=", len(checks["scope"]["changed_files"]), flush=True)
    if not args.scope_only:
        exe = shutil.which(args.godot) or args.godot
        checks["runtime"] = run_godot(exe, sha, "runtime-checks", [])
        for index in range(5):
            checks[f"restart-{index}"] = run_godot(exe, sha, f"restart-{index}", ["--", "--restart", str(index)])
        data = json.loads((OUT / "runtime-checks.json").read_text(encoding="utf-8"))
        if len(data["save_states"]) != 20 or {s["room"] for s in data["save_states"]} != set(range(5)) or {s["facing"] for s in data["save_states"]} != set(range(4)):
            checks["save_coverage"] = {"status": "FAIL"}
        if set(data["sections"]) != {"1", "2", "3", "4", "5", "6", "7", "9"}:
            checks["section_coverage"] = {"status": "FAIL"}
    report = {"status": "PASS" if all(s["status"] == "PASS" for s in checks.values()) else "FAIL", "execution_sha": sha, "results": checks}
    write("connection-summary.json", report)
    print("VILLAGE_CONNECTIONS_" + report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
