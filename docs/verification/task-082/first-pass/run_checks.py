#!/usr/bin/env python3
"""082の固定SHA checkoutで原検査を実行し、コマンド・終了値・原ログを保存する。"""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(__file__).resolve().parent
ENGINE = Path("/workspace/RPG-maker/.tools/godot/4.7.2/godot")
PYTHON = sys.executable
sys.path.insert(0, str(ROOT / "tools"))
from run_locked_checks import judge_output

BASE = "6c996d5c37fd384e679bb23dd59113c99494790c"
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
env = dict(os.environ, RPG_QA_SAVE_PREFIX="task082_suite", PYTHONDONTWRITEBYTECODE="1")
env["PATH"] = str(ENGINE.parent) + os.pathsep + env["PATH"]
for kind in ["CACHE", "CONFIG", "DATA"]:
    folder = ROOT / ".tools/task082" / kind.lower()
    folder.mkdir(parents=True, exist_ok=True)
    env["XDG_" + kind + "_HOME"] = str(folder)
records = []
metadata = {"execution_sha": sha, "baseline_main": BASE, "cwd": str(ROOT),
            "python": PYTHON, "engine": str(ENGINE),
            "environment": {key: value for key, value in env.items() if key.startswith(("XDG_", "RPG_QA_", "PYTHONDONT"))},
            "changed_paths": subprocess.check_output(["git", "diff", "--name-only", BASE, sha], cwd=ROOT, text=True).splitlines(),
            "source_sha256": {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in
                              subprocess.check_output(["git", "diff", "--name-only", BASE, sha], cwd=ROOT, text=True).splitlines()}}


def run(name, command, limit, requirement=False, marker=None):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=limit)
        code, raw, timed_out = result.returncode, result.stdout, False
    except subprocess.TimeoutExpired as error:
        code, raw, timed_out = 124, error.stdout or b"", True
    text = raw.decode("utf-8", errors="replace")
    path = OUT / (name + ".log.gz")
    path.write_bytes(gzip.compress(raw, mtime=0))
    command_text = shlex.join(command)
    judged = judge_output(name, command_text, code, text, timed_out) if requirement else {
        "status": "PASS" if code == 0 and not timed_out and not re.search(r"SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL:|Fontconfig error", text)
        and (marker is None or len(re.findall("^"+re.escape(marker), text, re.M)) == 1) else "FAIL"}
    records.append({"name": name, "command": command_text, "execution_sha": sha, "started": started,
                    "finished": datetime.datetime.now(datetime.timezone.utc).isoformat(), "timeout_seconds": limit,
                    "exit_code": code, "timed_out": timed_out, "result": judged, "log": path.name,
                    "raw_sha256": hashlib.sha256(raw).hexdigest()})
    (OUT/"execution.json").write_text(json.dumps(dict(metadata, checks=records), ensure_ascii=False, indent=2)+"\n")
    print(name, code, judged["status"], flush=True)


def gd(name, limit=180, marker=None):
    run(name, [str(ENGINE), "--headless", "--path", ".", "--script", "res://tools/"+name+".gd"], limit, marker=marker)


def py(name, args=(), limit=180):
    run(name, [PYTHON, "tools/"+name+".py", *args], limit)


run("engine", [str(ENGINE), "--version"], 30)
run("import", [str(ENGINE), "--headless", "--editor", "--import", "--quit"], 600)
py("check_frozen_files")
py("check_region2_shrine_story_data")
gd("check_region2_shrine_story", 180, "SHRINE_RUNTIME_PASS:")
py("validate_assets", ["--strict"])
for requirement in json.loads((ROOT/".scope-lock/spec.lock.json").read_text())["requirements"]:
    run(requirement["id"], shlex.split(requirement["verify"]), 300, True)
py("check_original_acceptance_inputs")
for kind in ["entry", "combat", "progression", "storage", "ui", "builds", "completion", "mastery"]:
    gd("check_integrated_"+kind, 240)
for name in ["check_mastery_charger_probe", "check_mastery_role_transition", "check_map_graph_definition",
             "check_map_graph_structure", "check_map_graph_structure_regressions"]:
    gd(name)
for name in ["build_world_terrain", "build_world_interiors"]:py(name)
for name in ["check_world_terrain", "check_world_terrain_boundaries"]:gd(name)
py("check_world_realtime_record")
gd("check_duration_target")
py("check_duration_summary")
for name in ["check_battle_acceptance", "check_reaction_rules", "check_battle_counterplay"]:gd(name, 300)
for name in ["check_region2_port_backdrop", "check_region2_village_scope", "check_region2_village_backdrops",
             "check_region2_village_native", "check_progress_docs", "test_locked_check_reporting"]:py(name)
py("check_acceptance_registration", ["--proposal"])
py("check_registry_sprint_scope")
py("check_first_region_gado_data")
gd("check_first_region_gado")
gd("check_region2_village_backdrops", 120)
py("check_task007", ["--completed", "776ad944723d21c1e250a1ee5fd56d35da42cfed", "--godot", str(ENGINE)], 900)
py("check_task011", ["--completed", "d258908fbb0397e64d08780694786ef1855c4979", "--godot", str(ENGINE)], 900)
py("check_task011_ci_boundary", ["--godot", str(ENGINE)], 300)
for name, limit in [("check_enemy_encounters",180), ("check_battle_recovery",180), ("check_saved_value_types",60),
                    ("check_saved_position_relocation",120), ("check_second_region_coast",180), ("check_first_region_screen",180),
                    ("check_region2_port_backdrop",120), ("check_region2_port",180), ("capture_job_costumes",180),
                    ("check_task081_port_runtime",120)]:gd(name,limit)
py("check_task081_port_data",limit=120)
run("frozen-after", [PYTHON, "tools/check_frozen_files.py"], 30)
raise SystemExit(0 if all(row["result"]["status"]=="PASS" for row in records) else 1)
