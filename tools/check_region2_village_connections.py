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
# 監督が2026-10-04に保持を指示したmain。006の差分と区別して固定する。
APPROVED_UPSTREAM = "677e5a74937921250ec388c72fb1ceaba0341c8c"
UPSTREAM_ORIGINALS = {"assets/_incoming/owner-2026-10-04-grok-region3-rooms/region3-room-"+role+".png" for role in ("armor-shop","harbor-office","inn","item-shop","shrine","weapon-shop")}
# 初回006統合後にmainへ追加された未採用原画。固定2コミット間の追加11件だけを保持する。
BATCH3_BASE = "37b16815492ca2922fd2850d2e1bae4283bdb3c2"
BATCH3_UPSTREAM = "24bd7d07a87e00872ae106a0ca3c7f06f9ac65a2"
BATCH3_ORIGINALS = {"assets/_incoming/owner-2026-10-05-grok-batch3/"+name+".png" for name in (
    "bookmark-design-candidates-4", "region3-village-exterior", "region3-village-room-inn",
    "region3-village-room-item-shop", "region3-village-room-shrine", "region3-village-room-weapon-shop",
    "region3-volcano-cave-1f", "region3-volcano-cave-2f", "region3-volcano-cave-battle",
    "region3-volcano-cave-boss-floor", "region3-volcano-cave-boss",
)}
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
    contains_upstream = subprocess.run(["git","merge-base","--is-ancestor",APPROVED_UPSTREAM,target],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode == 0
    contains_batch3 = subprocess.run(["git","merge-base","--is-ancestor",BATCH3_UPSTREAM,target],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode == 0
    comparison_base = APPROVED_UPSTREAM if contains_upstream else BASE
    upstream_changes = git("diff","--name-only",BASE,APPROVED_UPSTREAM).decode().splitlines() if contains_upstream else []
    changed = git("diff", "--name-only", comparison_base, target).decode().splitlines()
    batch3_changes = git("diff", "--name-status", BATCH3_BASE, BATCH3_UPSTREAM).decode().splitlines() if contains_batch3 else []
    # 比較基準は677e5a7のまま。新mainに既に入った006コードを比較から隠さない。
    retained_batch3 = BATCH3_ORIGINALS if contains_batch3 else set()
    changed = [s for s in changed if s not in retained_batch3]
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
    a, b = tree(comparison_base), tree(target)
    if contains_batch3:
        if set(batch3_changes) != {"A\t"+s for s in BATCH3_ORIGINALS}:
            failures.append("初回006統合後の上流差分が固定原画11件の追加と一致しません")
        source_batch3 = tree(BATCH3_UPSTREAM)
        failures += [s for s in BATCH3_ORIGINALS if source_batch3.get(s) != b.get(s)]
    if contains_upstream and set(upstream_changes) != UPSTREAM_ORIGINALS:
        failures.append("監督指定mainの原画6件以外に上流差分があります")
    original_paths = [s for s in a if s.startswith(("assets/", "test/", ".scope-lock/")) or (s.startswith("tools/") and s not in ALLOWED) or s in ["project.godot", ".github/workflows/ci.yml", "world/region2_village_backdrops.json", "world/region2_port.json", "world/second_region_coast.json"]]
    altered = [s for s in original_paths if a[s] != b.get(s)]
    failures += altered
    originals = [s for s in a if s.startswith("assets/_incoming/owner-2026-10-04-grok-region3/")]
    return {"status": "PASS" if not failures else "FAIL", "base": BASE, "comparison_base":comparison_base, "preserved_upstream_originals":upstream_changes, "commit": target,
            "changed_files": changed, "failures": failures, "protected_and_existing_unchanged": len(original_paths),
            "grok_originals_unchanged": len(originals), "preserved_batch3_upstream": BATCH3_UPSTREAM if contains_batch3 else None,
            "preserved_batch3_originals": sorted(retained_batch3), "checks_weakened_or_removed": 0 if not altered else None,
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
