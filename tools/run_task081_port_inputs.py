#!/usr/bin/env python3
"""081の本番入力・描画を各180秒以内で逐次実行する。X11と固定Godotを使用。"""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/verification/task-081-implementation"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", default=str(ROOT / ".tools/godot/4.7.2/godot"))
    parser.add_argument("--phases", nargs="+", default=["arrival", "inn", "item_shop", "weapon_shop", "shrine", "armor_shop"])
    args = parser.parse_args()
    assert os.environ.get("DISPLAY"), "描画可能なX11を指定する"
    summary = OUT / "input-execution.json"
    records = json.loads(summary.read_text()) if summary.exists() else []
    for phase in args.phases:
	# 再検証前の原画像・失敗・成功をどれも履歴へ保持する。
        previous = OUT / (phase + "-input.json")
        if previous.exists():
            archive = OUT / "attempts" / (phase + "-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
            archive.mkdir(parents=True, exist_ok=True)
            for pattern in [phase + "-*", "input-" + phase + ".log.gz"]:
                for file in OUT.glob(pattern):
                    if file.is_file():
                        shutil.copyfile(file, archive / file.name)
            if summary.exists():
                shutil.copyfile(summary, archive / summary.name)
        env = dict(os.environ, TASK081_PHASE=phase)
        for category in ["CACHE", "CONFIG", "DATA"]:
            path = ROOT / ".tools/task081" / category.lower()
            path.mkdir(parents=True, exist_ok=True)
            env["XDG_" + category + "_HOME"] = str(path)
        command = [args.godot, "--display-driver", "x11", "--audio-driver", "Dummy", "--path", ".",
                   "--script", "res://tools/check_task081_port_input.gd"]
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            process = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
            raw, code = process.stdout, process.returncode
        except subprocess.TimeoutExpired as exc:
            raw, code = exc.stdout or b"", 124
        filename = OUT / ("input-" + phase + ".log.gz")
        filename.write_bytes(gzip.compress(raw, mtime=0))
        result_path = OUT / (phase + "-input.json")
        result = json.loads(result_path.read_text()) if result_path.exists() else {}
        text = raw.decode("utf8", errors="replace")
        passed = code == 0 and result.get("failed") == 0 and "TASK081_INPUT_RESULT:" in text and not any(value in text for value in ["SCRIPT ERROR", "ERROR:", "TASK081_INPUT_FAIL:"])
        records = [record for record in records if record["phase"] != phase]
        records.append(dict(phase=phase, command=command, cwd=str(ROOT), timeout_seconds=180,
                            started=started, finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            exit_code=code, status="PASS" if passed else "FAIL", raw_log_sha256=hashlib.sha256(raw).hexdigest(),
                            driver_warning="Could not set V-Sync mode" in text))
        (OUT / "input-execution.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
        print(phase, code, records[-1]["status"], flush=True)
    return 0 if all(record["status"] == "PASS" for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
