"""GitHubの実行可否と区別して、既存CIの独立した検査をローカルで実行する。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import signal
from pathlib import Path
import subprocess
import sys
import time
from build_identity import identity, EXPECTED_ENGINE

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("--godot", required=True)
parser.add_argument("--from-check")
parser.add_argument("--select-checks")
parser.add_argument("--report-name", default="integrated-local-suite")
parser.add_argument("--resume", action="store_true")
args = parser.parse_args()
if not re.fullmatch(r"[a-z0-9_-]+", args.report_name):
    parser.error("report-nameは英小文字・数字・ハイフン・下線です")
godot = str(Path(args.godot).resolve())
logs = ROOT / ".tools" / "integrated-local-suite"
logs.mkdir(parents=True, exist_ok=True)
commands: list[tuple[str, list[str], int]] = []

def engine(name: str, extra: list[str] | None = None, timeout: int = 600) -> None:
    label = name + ("_" + "_".join(x.lstrip("-").replace("=", "-") for x in extra) if extra else "")
    commands.append((label, [godot, "--headless", "--path", ".", "--log-file", str(logs / (label + "-engine.log")), "--script", "res://tools/" + name + ".gd"] + (["--", *extra] if extra else []), timeout))

def python(name: str, extra: list[str] | None = None) -> None:
    commands.append((name, [sys.executable, "tools/" + name + ".py", *(extra or [])], 600))

for name in ["check_map_graph_definition", "check_map_graph_structure", "check_map_graph_structure_regressions", "check_world_terrain", "check_world_terrain_boundaries"]:
    engine(name)
python("check_world_realtime_record")
engine("check_world_integration")
engine("check_world_integration", ["--party=3"])
for name in ["check_world_state_boundaries", "check_world_ui", "check_duration_target"]:
    engine(name)
python("check_duration_summary")
python("check_long_record_summary")
for name in ["check_preplay_ui", "check_preplay_recovery", "check_preplay_combat", "check_battle_acceptance", "check_reaction_rules", "check_battle_counterplay", "check_field_recovery", "check_route_counterplay"]:
    engine(name, timeout=1800)
python("check_long_authoring")
for kind in ["content", "geometry", "past", "clues", "ui", "record", "device_ui", "device_boundaries", "recovery"]:
    engine("check_long_" + kind)
for name in ["check_progression_paths", "check_erosion_choices", "check_enemy_encounters", "check_exploration_devices", "check_party_playtest", "check_battle_recovery", "check_campaign_boundaries", "check_saved_value_types"]:
    engine(name)
engine("check_progression_paths", ["--three-member-party"])
engine("check_save_complete", ["--automated-playtest"])
engine("check_save_complete", ["--three-member-party", "--teaching-first", "--automated-playtest"])
engine("check_v1_finish")
python("check_build_identity")
python("check_record_restart", ["--godot", godot])
engine("check_worst_case", ["--three-member-party", "--teaching-first", "--automated-playtest"], 1800)
python("check_frozen_files")
python("validate_assets", ["--strict"])

all_count = len(commands)
if args.select_checks:
    if args.from_check:parser.error("from-checkとselect-checksは同時に指定できません")
    selected = args.select_checks.split(",")
    if len(selected)!=len(set(selected)) or set(selected)-{x[0] for x in commands}:parser.error("選択した検査名が不正です")
    commands=[x for x in commands if x[0] in selected]
if args.from_check:
    labels = [x[0] for x in commands]
    if args.from_check not in labels:parser.error("存在しない検査名です")
    commands = commands[labels.index(args.from_check):]
source = identity(EXPECTED_ENGINE)
hashes = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "tools").rglob("*") if p.suffix in [".gd", ".py"]}
results = []
environment = os.environ.copy()
environment["RPG_QA_SAVE_PREFIX"] = "integrated-local-suite"
report_path = ROOT / "docs/verification" / (args.report_name + ".json")
if args.resume and report_path.exists():
    prior = json.loads(report_path.read_text(encoding="utf-8-sig"))
    if prior.get("build") != source or prior.get("checks") != hashes or prior.get("selected_checks") != [x[0] for x in commands]:
        parser.error("同じ版・同じ検査一覧の再開記録ではありません")
    results = prior["results"]
    if [x["name"] for x in results] != [x[0] for x in commands[:len(results)]]:parser.error("記録の順序が不正です")
for label, command, timeout in commands[len(results):]:
    started = time.monotonic()
    path = logs / (label + ".log")
    with path.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0, start_new_session=os.name != "nt")
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
            else:os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            code = "TIMEOUT"
    text = path.read_text(encoding="utf-8", errors="replace")
    diagnostics = [line for line in text.splitlines() if any(marker in line for marker in ["SCRIPT ERROR", "ERROR:", "WARNING:", "Parse Error", "_FAIL:"])]
    passed = code == 0 and not diagnostics
    portable = ["godot" if value == godot else ("python" if value == sys.executable else value.replace(str(ROOT) + os.sep, "")) for value in command]
    summaries = [line for line in text.splitlines() if "_PASS:" in line or "_RESULT:" in line or line.startswith("BATTLE_ACCEPTANCE:")]
    results.append({"name": label, "command": portable, "exit_code": code, "status": "PASS" if passed else "FAIL", "elapsed_seconds": round(time.monotonic() - started, 3), "log": path.relative_to(ROOT).as_posix(), "log_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "summary": summaries[-8:], "diagnostics": diagnostics[:20]})
    document = {"status": "RUNNING" if len(results) < len(commands) else ("PASS" if all(x["status"] == "PASS" for x in results) else "FAIL"), "completed": len(results), "total": len(commands), "all_checks": all_count, "selected_checks": [x[0] for x in commands], "build": source, "checks": hashes, "scope": "GitHub CIの代用の緑表示ではなくローカル実行記録。全80話の4条件・同予算比較・凍結verify・容量・実描画は別の実行記録。", "results": results}
    temporary = report_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(report_path)
    print(f"LOCAL_ACCEPTANCE: {label} {results[-1]['status']} exit={code}", flush=True)
sys.exit(0 if all(x["status"] == "PASS" for x in results) else 1)
