#!/usr/bin/env python3
"""固定006を別checkoutの当時の道具で実行し、SHA・全項目・予算を確認する。"""
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
import time

from check_task009_scope import FIXED, ROOT

OUT = ROOT / 'docs/verification/task-009'
RUNTIME_CHECKS = 7592
CAPTURE_CHECKS = {'journey': 137, 'details': 34, 'restart-0': 17, 'restart-1': 17,
                  'restart-2': 17, 'restart-3': 17, 'restart-4': 17}
CAPTURE_IMAGES = {'journey': 28, 'details': 6, **{f'restart-{i}': 3 for i in range(5)}}


def validate_fixed(path: Path, sha: str) -> None:
    if sha != FIXED:
        raise ValueError('固定006の完全SHAが承認済み完成点と一致しません')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path).decode().strip()
    if head != FIXED or path.resolve() == ROOT:
        raise ValueError('固定006は完成SHAの別checkoutで実行してください')
    originals = json.loads((OUT / 'original-checks.json').read_text())
    for name, digest in originals.items():
        if hashlib.sha256((path / name).read_bytes()).hexdigest() != digest:
            raise ValueError('当時の検査器/期待値/元workflowの不変違反: ' + name)
    changed = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=path).decode().splitlines()
    if any(not p.startswith('docs/verification/') for p in changed):
        raise ValueError('固定checkoutの本番または検査コードが変更されています')


def command_run(command: list[str], cwd: Path, output: Path, timeout: int) -> dict:
    start = time.monotonic()
    env = os.environ.copy()
    env['RPG006_EXECUTION_SHA'] = FIXED
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout)
        text = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        code = result.returncode
    except subprocess.TimeoutExpired as exc:
        text = ((exc.stdout or b'') + (exc.stderr or b'')).decode('utf-8', errors='replace') + '\nTIMEOUT\n'
        code = 124
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding='utf-8')
    bad = [line for line in text.splitlines() if re.search(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL', line)]
    return {'status': 'PASS' if code == 0 and not bad else 'FAIL', 'command': command,
            'exit_code': code, 'errors': bad, 'elapsed_seconds': round(time.monotonic() - start, 3), 'timeout_seconds': timeout}


def fixed_runtime(path: Path, exe: str) -> dict:
    # 元Pythonには各Godotプロセス180秒がある。外側で180秒にまとめて短縮しない。
    start = time.monotonic()
    result = subprocess.run([sys.executable, 'tools/check_region2_village_connections.py',
                             '--commit', FIXED, '--godot', exe], cwd=path, capture_output=True)
    text = (result.stdout + result.stderr).decode('utf-8', errors='replace')
    target = OUT / 'fixed'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'execution.log').write_text(text, encoding='utf-8')
    source = path / 'docs/verification/region2-village-connections'
    report = json.loads((source / 'connection-summary.json').read_text())
    runtime = json.loads((source / 'runtime-checks.json').read_text())
    coverage = (runtime['checks'] == RUNTIME_CHECKS and len(runtime['save_states']) == 20
                and {(s['room'], s['facing']) for s in runtime['save_states']} == {(i, j) for i in range(5) for j in range(4)}
                and all(report['results'][f'restart-{i}']['checks'] > 0 for i in range(5))
                and report['execution_sha'] == FIXED and runtime['execution_sha'] == FIXED
                and report['results']['scope']['commit'] == FIXED)
    for item in source.glob('*.json'):
        shutil.copy2(item, target / item.name)
    for item in source.glob('*.log'):
        shutil.copy2(item, target / item.name)
    shutil.copytree(source / 'saved-inputs', target / 'saved-inputs', dirs_exist_ok=True)
    ok = result.returncode == 0 and report['status'] == 'PASS' and coverage
    return {'status': 'PASS' if ok else 'FAIL', 'execution_sha': FIXED, 'runtime_checks': runtime['checks'],
            'save_states': len(runtime['save_states']), 'restart_checks': [report['results'][f'restart-{i}']['checks'] for i in range(5)],
            'scope_status': report['results']['scope']['status'], 'exit_code': result.returncode,
            'elapsed_seconds': round(time.monotonic() - start, 3), 'process_timeout_seconds': 180}


def fixed_capture(path: Path, exe: str, mode: str) -> dict:
    extra = [] if mode == 'journey' else ['--', '--details'] if mode == 'details' else ['--', '--restart', mode.split('-')[1]]
    target = OUT / 'fixed-render' / mode
    result = command_run(['xvfb-run', '-a', exe, '--path', str(path), '--rendering-method', 'mobile', '--rendering-driver', 'vulkan', '--audio-driver', 'Dummy',
                          '--script', 'res://tools/capture_region2_village_connections.gd', *extra],
                         path, target / 'execution.log', 180)
    source = path / 'docs/verification/region2-village-connections' / mode
    report = json.loads((source / 'checks.json').read_text()) if (source / 'checks.json').exists() else {}
    exact = (report.get('status') == 'PASS' and report.get('checks', 0) > 0
             and len(report.get('images', [])) == CAPTURE_IMAGES[mode] and report.get('execution_sha') == FIXED
             and report.get('renderer') != 'headless'
             and report.get('limits') == {'milliseconds': 180000, 'moves': 600, 'inputs': 3000, 'turns': 300})
    if source.exists():
        shutil.copytree(source, target, dirs_exist_ok=True)
    result.update(execution_sha=FIXED, checks=report.get('checks'), images=len(report.get('images', [])))
    if not exact:
        result['status'] = 'FAIL'
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixed-path', type=Path, required=True)
    parser.add_argument('--fixed-sha', default=FIXED)
    parser.add_argument('--godot', default='godot')
    parser.add_argument('--capture', choices=list(CAPTURE_CHECKS))
    args = parser.parse_args()
    try:
        validate_fixed(args.fixed_path, args.fixed_sha)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print('TASK009_LIFECYCLE_FAIL: ' + str(exc), file=sys.stderr)
        return 1
    exe = shutil.which(args.godot) or str(Path(args.godot).resolve())
    report = fixed_capture(args.fixed_path, exe, args.capture) if args.capture else fixed_runtime(args.fixed_path, exe)
    target = OUT / ('fixed-render/' + args.capture if args.capture else 'fixed') / 'lifecycle-summary.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
