"""007の最新検査を一時コピーで反証する。固定版・本番・採用待ち画像は変更しない。"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from check_task007 import BAD, ROOT, run


def verify(exe, sha, target):
    env = os.environ.copy()
    env['TASK007_EXECUTION_SHA'] = sha
    env['RPG_QA_SAVE_PREFIX'] = 'task021'
    cases = {}
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='task021-mutations-') as directory:
        candidate = Path(directory) / 'candidate'
        shutil.copytree(ROOT, candidate, ignore=shutil.ignore_patterns('.git', '.tools', '__pycache__'))
        village = candidate / 'world/region2_village.json'
        source = candidate / 'scripts/game/game_session.gd'
        village_bytes, source_bytes = village.read_bytes(), source.read_bytes()
        command = [exe, '--headless', '--path', str(candidate), '--script', 'res://tools/check_task007_services.gd']
        evidence = candidate / 'docs/verification/task-007/latest'

        def services(name, failure=None):
            started = time.monotonic()
            proc = subprocess.run(command, cwd=candidate, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
            output = proc.stdout.decode('utf-8', errors='replace')
            (target / (name + '.log')).write_text(output)
            observed = json.loads((evidence / 'services.json').read_text())
            (target / (name + '.json')).write_text(json.dumps(observed, ensure_ascii=False, indent=2) + '\n')
            if failure is None:
                accepted = proc.returncode == 0 and observed['status'] == 'PASS' and not BAD.search(output) and output.count('TASK007_SERVICES_PASS:') == 1
            else:
                accepted = proc.returncode == 1 and observed['status'] == 'FAIL' and any(failure in item for item in observed['failures']) and not re.search(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|TIMEOUT', output)
            cases[name] = dict(status='PASS' if accepted else 'FAIL', exit_code=proc.returncode, elapsed_seconds=round(time.monotonic()-started, 3), timeout_seconds=180, expected_failure=failure, observed=observed)
            return observed

        try:
            services('baseline')
            data = json.loads(village_bytes)
            events = [event for room in data['site']['rooms'] for event in room.get('events', [])]
            inn = [event for event in events if event['id'] == 'oasis_innkeeper']
            assert len(inn) == 1
            # 再現入力はコピー上で作る。最新本番の初期セル・reachは固定しない。
            inn[0]['cell'], inn[0]['reach'] = [12, 3], 2
            village.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            services('inn-fixture')
            inn[0]['cell'] = [11, 3]
            village.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            observed = services('inn-relocated')
            row = [row for row in observed['residents'] if row['id'] == 'oasis_innkeeper']
            assert len(row) == 1 and row[0]['cell'] == [11, 3] and row[0]['approach'] == [11, 5] and row[0]['facing'] == [0, -1] and row[0]['reach'] == 2
            cases['inn-relocated']['movement'] = dict(source=[12, 3], destination=[11, 3], approach=[11, 5], facing=[0, -1], reach=2)
            for mode in ['outside', 'rooms']:
                capture = [exe, '--path', str(candidate), '--rendering-method', 'mobile', '--rendering-driver', 'vulkan', '--audio-driver', 'Dummy', '--script', 'res://tools/capture_task007_services.gd', *(['--', '--rooms'] if mode == 'rooms' else [])]
                if not env.get('DISPLAY'):
                    capture = ['xvfb-run', '-a', *capture]
                result = run(capture, candidate, target / ('relocated-' + mode + '.log'), env, 180, 'TASK007_CAPTURE_PASS:')
                record = json.loads((evidence / mode / 'checks.json').read_text())
                if record['status'] != 'PASS' or record['renderer'] != 'X11' or record['execution_sha'] != sha or len(record['images']) != (11 if mode == 'outside' else 22):
                    result['status'] = 'FAIL'
                (target / ('relocated-' + mode + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
                cases['relocated-' + mode] = result
            # 11,3では10,3から隣接会話できる。届かない負例は020と同じ12,3で作る。
            data = json.loads(village_bytes)
            inn = [event for room in data['site']['rooms'] for event in room.get('events', []) if event['id'] == 'oasis_innkeeper']
            inn[0]['cell'], inn[0]['reach'] = [12, 3], 1
            village.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            services('inn-unreachable', '宿IDの床・占有・reach・入口到達')
            village.write_bytes(village_bytes)
            original = source_bytes.decode()
            needle = '\t_reconcile_slots(actor)\n\treturn true\n'
            start = original.index('func release_monster_form(')
            before, function = original[:start], original[start:]
            assert function.count(needle) >= 1
            mutation = '\tif _state["overworld"]["node"]=="region2_village":_state["overworld"]["cleared"]=[]\n'
            source.write_text(before + function.replace(needle, '\t_reconcile_slots(actor)\n' + mutation + '\treturn true\n', 1))
            services('shrine-cleared-loss', '祠成功前後のoverworld全体不変')
        finally:
            village.write_bytes(village_bytes)
            source.write_bytes(source_bytes)
        services('restored')
    report = dict(status='PASS' if all(case['status'] == 'PASS' for case in cases.values()) else 'FAIL', execution_sha=sha, cases=cases, normalized=['layer', 'node', 'room', 'cell'])
    (target / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('TASK021_' + report['status'] + ': cases=' + str(len(cases)), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--godot', default='godot')
    args = parser.parse_args()
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    exe = str(Path(shutil.which(args.godot) or args.godot).resolve())
    return 0 if verify(exe, sha, ROOT / 'docs/verification/task-021/ci')['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
