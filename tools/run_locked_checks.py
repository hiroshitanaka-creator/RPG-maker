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


def execution_summary(requirement_id: str, clean: str) -> tuple[bool, bool, dict | None]:
    """検査形式ごとの実行証拠を確認し、終了0だけの空実行を拒否する。"""
    clean = clean.replace("\r\n", "\n")
    if requirement_id in ("AC-01", "AC-02"):
        ran = "BATTLE_ACCEPTANCE:" in clean
        samples = re.findall(r"^BATTLE_SAMPLE: (\S+) party=([34]) wins=(\d+)/1000 within10=(\d+) cutoff=(\d+)$", clean, re.MULTILINE)
        complete = len(samples) == 12 and len({(s[0], s[1]) for s in samples}) == 12
        return ran, complete and "BATTLE_ACCEPTANCE: AC-01=PASS AC-02=PASS errors=0" in clean, None
    if requirement_id == "AC-03":
        matches = re.findall(r"^SAVE_COMPLETE_PASS: party=([34]) states=(\d+) differences=0$", clean, re.MULTILINE)
        complete = len(matches) == 2 and {m[0] for m in matches} == {"3", "4"} and all(int(m[1]) > 0 for m in matches)
        return bool(matches), complete, None
    if requirement_id == "R-07":
        return "CHAPTER1_" in clean, "CHAPTER1_PASS:" in clean, None
    summaries = re.findall(r"^SCOPE_GUT_RESULT (.+)$", clean, re.MULTILINE)
    try:
        gut = json.loads(summaries[-1]) if summaries else None
    except json.JSONDecodeError:
        return False, False, None
    ran = bool(gut and gut.get("tests", 0) > 0 and gut.get("assertions", 0) > 0)
    passed = bool(ran and gut.get("failed_assertions") == 0 and gut.get("pending") == 0 and gut.get("invalid") is False)
    return ran, passed, gut


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
        failures = [line.strip() for line in clean.splitlines() if '[Failed]' in line or re.search(r'SCRIPT ERROR|ERROR:|WARNING:|_FAIL:', line)]
        parser_failed = 'Parse Error' in clean or 'Failed to load script' in clean
        tests_ran, reported_pass, gut_summary = execution_summary(requirement['id'], clean)
        result = {
            'id': requirement['id'], 'verify': command, 'exit_code': code,
            'status': ('INVALID' if parser_failed or not tests_ran or timed_out else ('PASS' if code == 0 and reported_pass and not failures else 'FAIL')), 'tests_ran': tests_ran,
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
        'spec_path': args.spec,
        'spec_sha256': hashlib.sha256((ROOT / args.spec).read_bytes()).hexdigest(),
        'test_sha256': {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((ROOT / 'test').rglob('*.gd'))},
        'smoke_sha256': hashlib.sha256((ROOT / 'tools/smoke_chapter1.gd').read_bytes()).hexdigest(),
        'results': results,
    }
    filename = 'scope-lock-baseline.json' if args.baseline and baseline_valid else ('scope-lock-attempt-' + run_id + '.json' if args.baseline else 'scope-lock-current.json')
    if not args.baseline and (ROOT / args.spec).resolve() != (ROOT / '.scope-lock/spec.lock.json').resolve():
        filename = 'scope-lock-proposed-current.json'
        report['kind'] = 'proposed_requirement_verification'
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
