#!/usr/bin/env python3
"""012の独立信頼基点照合。最新manifestを期待値に使わず、当時検査に追加する。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from test_task012_pinned_audit import MANIFEST, WORKFLOW, resolve, run, selected, show

# 016依頼書で承認済みの既存記録。CLI・最新文書・git logから選ばない。
TRUST_RECORD = '9e647b3d6d0f91b061f7de974dbb5411937a2bb9'
ROOT = Path(__file__).resolve().parent.parent
SELF = 'tools/check_task016_fixed_anchor.py'


def trusted_record(repo: Path) -> dict:
    resolve(repo, TRUST_RECORD)
    record = json.loads(show(repo, TRUST_RECORD, MANIFEST))
    sha = resolve(repo, record['completed_sha'])
    if not re.fullmatch('[0-9a-f]{40}', record['completed_tree']):
        raise ValueError('信頼記録treeが完全SHAではありません')
    if run(repo, 'rev-parse', sha + '^{tree}').decode().strip() != record['completed_tree']:
        raise ValueError('信頼記録と実commit treeが不一致')
    return record


def verify_selection(repo: Path, latest: str) -> dict:
    resolve(repo, latest)
    expected = trusted_record(repo)
    actual = json.loads(show(repo, latest, MANIFEST))
    # SHA/treeだけでなく記録全体を独立の固定blobと照合する。
    if actual != expected:
        raise ValueError('012 manifestが独立信頼基点の記録と不一致')
    selection = selected(repo, latest, expected['completed_sha'])
    return {'trust_record_sha': TRUST_RECORD, 'completed_sha': expected['completed_sha'],
            'completed_tree': expected['completed_tree'], 'selection': selection}


def verify_checkout(path: Path, expected: dict) -> None:
    if run(path, 'rev-parse', 'HEAD').decode().strip() != expected['completed_sha']:
        raise ValueError('012別checkoutのHEADが独立信頼基点と不一致')
    if run(path, 'rev-parse', 'HEAD^{tree}').decode().strip() != expected['completed_tree']:
        raise ValueError('012別checkoutのtreeが独立信頼基点と不一致')
    changed = run(path, 'diff', '--name-only', 'HEAD').decode().splitlines()
    if any(not p.startswith('docs/verification/task-012/') for p in changed):
        raise ValueError('012別checkoutの当時コード/検査器/期待値が改変')
    # 新規ソースによるshadowingも拒否。実行結果の新規証拠は許容する。
    untracked = run(path, 'ls-files', '--others', '--exclude-standard').decode().splitlines()
    if any(not p.startswith('docs/verification/task-012/') for p in untracked):
        raise ValueError('012別checkoutに未追跡の実行入力が存在')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--current-path', type=Path, default=ROOT)
    parser.add_argument('--fixed012-path', type=Path, required=True)
    parser.add_argument('--latest-sha', required=True)
    args = parser.parse_args()
    current = args.current_path.resolve()
    report = {'status': 'FAIL', 'execution_sha': args.latest_sha, 'trust_record_sha': TRUST_RECORD}
    output = current / 'docs/verification/task-016/fixed-anchor.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        resolve(current, args.latest_sha)
        if run(current, 'rev-parse', 'HEAD').decode().strip() != args.latest_sha:
            raise ValueError('最新入力SHAとcurrent checkoutのHEAD不一致')
        for path in [MANIFEST, WORKFLOW, SELF, 'tools/test_task012_pinned_audit.py']:
            if (current / path).read_bytes() != show(current, args.latest_sha, path):
                raise ValueError('最新照合入力の未commit改変: ' + path)
        expected = verify_selection(current, args.latest_sha)
        verify_checkout(args.fixed012_path.resolve(), expected)
        report.update(expected, status='PASS', checkout_sha=expected['completed_sha'])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        report['failure'] = str(exc)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
