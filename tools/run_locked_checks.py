#!/usr/bin/env python3
"""指定されたverifyを変更せず逐次実行し、実際の終了コードを記録する。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', default='.scope-lock/spec.lock.json')
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    contract = json.loads((ROOT / args.spec).read_text(encoding='utf-8'))
    requirements = contract.get('requirements', [])
    if not requirements:
        print('要件が空のため検証成功とは扱いません。', file=sys.stderr)
        return 2
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    log_root = ROOT / '.tools' / 'verification' / (('baseline-' if args.baseline else 'current-') + run_id)
    log_root.mkdir(parents=True, exist_ok=True)
    results = []
    for requirement in requirements:
        command = requirement['verify']
        timed_out = False
        try:
            process = subprocess.run(
                command, shell=True, cwd=ROOT, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=300,
            )
            code = process.returncode
            output = process.stdout.decode('utf-8', errors='replace')
        except subprocess.TimeoutExpired as exc:
            code, timed_out = -1, True
            output = (exc.stdout or b'').decode('utf-8', errors='replace') + '\nTIMEOUT'
        (log_root / (requirement['id'] + '.log')).write_text(output, encoding='utf-8')
        clean = re.sub(r'\x1b\[[0-9;]*m', '', output)
        failures = [line.strip() for line in clean.splitlines() if '[Failed]' in line or 'CHAPTER1_FAIL:' in line]
        parser_failed = 'Parse Error' in clean or 'Failed to load script' in clean
        summaries = re.findall(r'^SCOPE_GUT_RESULT (.+)$', clean, flags=re.MULTILINE)
        gut_summary = json.loads(summaries[-1]) if summaries else None
        tests_ran = bool(gut_summary and gut_summary['tests'] > 0 and gut_summary['assertions'] > 0) if requirement['id'] != 'R-07' else ('CHAPTER1_' in clean)
        result = {
            'id': requirement['id'], 'verify': command, 'exit_code': code,
            'status': ('INVALID' if parser_failed or not tests_ran or timed_out else ('PASS' if code == 0 else 'FAIL')), 'tests_ran': tests_ran,
            'parser_failed': parser_failed, 'timed_out': timed_out,
            'gut_summary': gut_summary,
            'failure_messages': failures[:20],
        }
        results.append(result)
        print('%s %s (exit=%s, tests_ran=%s, parser_failed=%s)' % (
            result['status'], requirement['id'], code, tests_ran, parser_failed), flush=True)
        if failures:
            print('  ' + failures[0], flush=True)
    baseline_valid = all(r['exit_code'] != 0 and r['tests_ran'] and not r['parser_failed'] and not r['timed_out'] for r in results)
    report = {
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'kind': ('pre_implementation_baseline' if baseline_valid else 'invalid_baseline_attempt') if args.baseline else 'requirement_verification',
        'test_sha256': {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((ROOT / 'test').rglob('*.gd'))},
        'smoke_sha256': hashlib.sha256((ROOT / 'tools/smoke_chapter1.gd').read_bytes()).hexdigest(),
        'results': results,
    }
    filename = 'scope-lock-baseline.json' if args.baseline and baseline_valid else ('scope-lock-attempt-' + run_id + '.json' if args.baseline else 'scope-lock-current.json')
    destination = ROOT / 'docs' / 'verification' / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    if args.baseline and destination.exists():
        destination = destination.with_name('scope-lock-baseline-' + run_id + '.json')
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('検証記録: ' + destination.relative_to(ROOT).as_posix())
    if args.baseline:
        print('初期FAILの確認: ' + ('成立' if baseline_valid else '未成立。テスト未実行や構文エラーを確認してください。'))
        return 0 if baseline_valid else 1
    return 0 if all(r['status'] == 'PASS' for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
