#!/usr/bin/env python3
"""009の最新動作を実行する。固定006の範囲監査は別checkoutで実行する。"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/verification/task-009/latest'
LIMIT = 180


def run(exe: str, sha: str, name: str, extra: list[str]) -> dict:
    command = [exe, '--headless', '--path', str(ROOT), '--script',
               'res://tools/check_region2_village_regression.gd', *extra]
    env = os.environ.copy()
    env['RPG009_EXECUTION_SHA'] = sha
    report_path = OUT / (name + '.json')
    # 前回のPASSを読み込まない。失敗・timeoutも結果として残す。
    report_path.unlink(missing_ok=True)
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=LIMIT)
        output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        code = result.returncode
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or b'') + (exc.stderr or b'')).decode('utf-8', errors='replace') + '\nTIMEOUT\n'
        code = 124
    (OUT / (name + '.log')).write_text(output, encoding='utf-8')
    bad = [line for line in output.splitlines() if re.search(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL', line)]
    report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    ok = code == 0 and not bad and report.get('status') == 'PASS' and report.get('checks', 0) > 0 and report.get('execution_sha') == sha
    if name == 'runtime-checks':
        states = report.get('save_states', [])
        ok = ok and len(states) == 20 and {(s['room'], s['facing']) for s in states} == {(i, j) for i in range(5) for j in range(4)}
        ok = ok and set(report.get('sections', {})) == {'1', '2', '3', '4', '5', '6', '7', '9'}
    print(f"{name}: {'PASS' if ok else 'FAIL'} checks={report.get('checks', 0)} exit={code}", flush=True)
    return {'status': 'PASS' if ok else 'FAIL', 'command': command, 'exit_code': code,
            'errors': bad, 'checks': report.get('checks', 0), 'elapsed_seconds': round(time.monotonic() - started, 3), 'timeout_seconds': LIMIT}


def run_capture(exe: str, sha: str, mode: str) -> dict:
    from check_task009_lifecycle import CAPTURE_IMAGES
    extra = [] if mode == 'journey' else ['--', '--details'] if mode == 'details' else ['--', '--restart', mode.split('-')[1]]
    command = ['xvfb-run', '-a', exe, '--path', str(ROOT), '--rendering-method', 'mobile', '--rendering-driver', 'vulkan', '--audio-driver', 'Dummy',
               '--script', 'res://tools/capture_task009_village_regression.gd', *extra]
    env = os.environ.copy()
    env['RPG009_EXECUTION_SHA'] = sha
    target = OUT / mode
    target.mkdir(parents=True, exist_ok=True)
    report_path = target / 'checks.json'
    report_path.unlink(missing_ok=True)
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
        text = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        code = result.returncode
    except subprocess.TimeoutExpired as exc:
        text = ((exc.stdout or b'') + (exc.stderr or b'')).decode('utf-8', errors='replace') + '\nTIMEOUT\n'
        code = 124
    (target / 'execution.log').write_text(text, encoding='utf-8')
    bad = [line for line in text.splitlines() if re.search(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL', line)]
    observed = json.loads(report_path.read_text()) if report_path.exists() else {}
    ok = (code == 0 and not bad and observed.get('status') == 'PASS' and observed.get('checks', 0) > 0
          and len(observed.get('images', [])) == CAPTURE_IMAGES[mode] and observed.get('execution_sha') == sha
          and observed.get('renderer') == 'X11'
          and observed.get('limits') == {'milliseconds': 180000, 'moves': 600, 'inputs': 3000, 'turns': 300})
    return {'status': 'PASS' if ok else 'FAIL', 'execution_sha': sha, 'command': command, 'exit_code': code,
            'checks': observed.get('checks'), 'images': len(observed.get('images', [])), 'errors': bad,
            'elapsed_seconds': round(time.monotonic() - started, 3), 'timeout_seconds': 180}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--godot', default=os.environ.get('GODOT', 'godot'))
    parser.add_argument('--capture', choices=['journey', 'details', *[f'restart-{i}' for i in range(5)]])
    args = parser.parse_args()
    sha = subprocess.check_output(['git', 'rev-parse', args.commit + '^{commit}'], cwd=ROOT).decode().strip()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    if sha != head:
        parser.error('最新回帰の実行checkoutと指定SHAが一致しません')
    OUT.mkdir(parents=True, exist_ok=True)
    exe = shutil.which(args.godot) or str(Path(args.godot).resolve())
    if args.capture:
        report = run_capture(exe, sha, args.capture)
        (OUT / args.capture / 'regression-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False), flush=True)
        return 0 if report['status'] == 'PASS' else 1
    results = {'runtime': run(exe, sha, 'runtime-checks', [])}
    # 主検査が壊れた場合も全5別プロセスを走らせ、失敗を隠さない。
    for index in range(5):
        results[f'restart-{index}'] = run(exe, sha, f'restart-{index}', ['--', '--restart', str(index)])
    report = {'status': 'PASS' if all(r['status'] == 'PASS' for r in results.values()) else 'FAIL',
              'execution_sha': sha, 'results': results, 'service_acceptance': '007未着手・未検証',
              'method': '最新checkoutの本番API。期待値は固定006の独立fixture。'}
    (OUT / 'regression-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('VILLAGE_REGRESSION_' + report['status'])
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
