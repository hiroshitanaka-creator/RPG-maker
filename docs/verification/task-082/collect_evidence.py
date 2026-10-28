#!/usr/bin/env python3
"""最終固定SHAのログ・保存例・継続回帰JSONと変更範囲を不変証拠へ集める。"""
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FINAL_ROOT = Path("/workspace/task082-final-verification")
FINAL = OUT / "final"
BASE = "6c996d5c37fd384e679bb23dd59113c99494790c"
SOURCE = "eb423ad0bc269ac737da80174ff812d63861d26e"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    final = json.loads((FINAL / "execution.json").read_text())
    assert final["execution_sha"] == SOURCE and len(final["checks"]) == 64
    failed = [row for row in final["checks"] if row["exit_code"] != 0 or row["result"]["status"] != "PASS"]
    assert {row["name"] for row in failed}=={"check_task011","check_task081_port_data"}
    assert all(row["exit_code"]==1 for row in failed)
    # 011本体の固定/最新は成功、毎歩通知の別fixture撮影が原180秒上限でtimeout。
    timeout_log=FINAL_ROOT/"docs/verification/task-027/fixtures/battle-capture.log"
    assert "TIMEOUT" in timeout_log.read_text()
    historical = json.loads((OUT / "historical-stage-081.json").read_text())
    assert historical["records"][0]["failed_details"]==["docs/decision-log.md","docs/tasks/README.md"]
    assert historical["records"][1]["exit_code"]==0 and historical["records"][1]["failed"]==0
    stage = json.loads((FINAL_ROOT / "docs/verification/task-081-implementation/data-checks.json").read_text())
    assert len(stage["checks"])==1235 and [row["detail"] for row in stage["checks"] if not row["ok"]]==historical["records"][0]["failed_details"]
    for row in final["checks"]:
        assert digest(gzip.decompress((FINAL / row["log"]).read_bytes())) == row["raw_sha256"]
    for path, value in final["source_sha256"].items():
        assert digest((FINAL_ROOT / path).read_bytes()) == value
    for name in ["runtime-checks.json", "data-checks.json"]:
        shutil.copyfile(FINAL_ROOT / "docs/verification/task-082" / name, FINAL / name)
    runtime = json.loads((FINAL / "runtime-checks.json").read_text())
    assert runtime["status"] == "PASS" and len(runtime["checks"]) == 283
    saves = FINAL_ROOT / ".tools/task082/data/godot/app_userdata/RPG-maker"
    (FINAL / "saves").mkdir(exist_ok=True)
    for path in saves.glob("task082-*.json"):
        shutil.copyfile(path, FINAL / "saves" / path.name)
    with (FINAL / "command-results.tsv").open("w") as file:
        writer = csv.writer(file, delimiter="\t", lineterminator="\n")
        writer.writerow(["name", "exit_code", "status", "timeout_seconds", "execution_sha", "command", "log"])
        for row in final["checks"]:
            writer.writerow([row["name"], row["exit_code"], row["result"]["status"], row["timeout_seconds"], SOURCE, row["command"], row["log"]])
    paths = subprocess.check_output(["git", "diff", "--name-only", "HEAD", "--", "docs/verification/"], cwd=FINAL_ROOT, text=True).splitlines()
    paths += subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "--", "docs/verification/"], cwd=FINAL_ROOT, text=True).splitlines()
    selected = sorted({name for name in paths if name.endswith((".json", ".log", ".log.gz")) and "/task-082/" not in name})
    with tarfile.open(FINAL / "regression-records.tar.gz", "w:gz") as archive:
        for name in selected:
            archive.add(FINAL_ROOT / name, arcname=name, recursive=False)
    save(FINAL / "regression-records.json", {name: digest((FINAL_ROOT / name).read_bytes()) for name in selected})
    # 初回ランナーではPython/Godotの同名検査がログ名を共有していた。
    # 元のraw hashを保ったまま参照名だけ分離する。欠けたPython出力は同SHAで再実行しhash一致を必須にする。
    first = json.loads((OUT / "execution.json").read_text())
    assert len(first["checks"]) == 64
    for row in first["checks"]:
        path = OUT / row["log"]
        if digest(gzip.decompress(path.read_bytes())) == row["raw_sha256"]:
            continue
        backup = OUT / (row["name"] + "-python.log.gz")
        if not backup.exists():
            env = dict(os.environ, **first["environment"])
            env["PATH"] = str(Path(first["engine"]).parent) + os.pathsep + env["PATH"]
            proc = subprocess.run(shlex.split(row["command"]), cwd=first["cwd"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=row["timeout_seconds"])
            assert proc.returncode == row["exit_code"] == 0 and digest(proc.stdout) == row["raw_sha256"]
            backup.write_bytes(gzip.compress(proc.stdout, mtime=0))
            row["identical_output_reproduced"] = True
        assert digest(gzip.decompress(backup.read_bytes())) == row["raw_sha256"]
        row["log"] = backup.name
    first["log_name_note"] = "同名のPython/Godotの参照を分離。終了値・判定・raw hashは変更せず、再取得出力も元hashとの一致を必須とした。最終ランナーは連番名を使用。"
    save(OUT / "execution.json", first)
    for path in OUT.glob("*.log.gz"):
        shutil.copyfile(path, OUT / "first-pass" / path.name)
    save(OUT / "first-pass/execution.json", first)
    changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], cwd=ROOT, text=True).splitlines()
    protected = [".scope-lock/", "test/", "project.godot", ".github/", "assets/", "world/", "docs/tasks/README.md", "docs/decision-log.md", "tools/smoke_chapter1.gd", "tools/smoke_first_region.gd", "docs/first-region-acceptance.md"]
    command = ["git", "diff", "--exit-code", BASE, "HEAD", "--", *protected]
    assert subprocess.run(command, cwd=ROOT).returncode == 0
    current_sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    save(OUT / "scope-audit-final.json", {"status": "PASS", "baseline": BASE, "source_sha": current_sha, "supplemental_regression_source_sha":SOURCE,"changed_source_paths":sorted(final["source_sha256"]),"observed_tracked_diff":changed,"command": command, "exit_code": 0, "source_files_sha256": {path:digest((ROOT/path).read_bytes()) for path in final["source_sha256"]}})
    save(FINAL / "summary.json", {"source_sha":SOURCE,"executed_commands":64,"passed":62,"failed":2,"local_render_timeout":"011本体の固定/最新は成功。通知fixture撮影が原180秒上限でtimeout。FAILを維持。","historical_stage_check":"FAILを維持。基点mainでも同一の2件不一致。固定完成版では1235件全成功。historical-stage-081.json参照。","focused_checks_passed":283,"failures_relabelled_as_pass":False,"scope":"eb423adの補助ローカル回帰。最終3216b3aの検証とは区別。"})
    print("EVIDENCE_COLLECTION_PASS: source=" + SOURCE + " executed_commands=64 passed=62 failed=2 focused_checks=283")


if __name__ == "__main__":
    main()
