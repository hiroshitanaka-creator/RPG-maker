#!/usr/bin/env python3
"""013の同時付替えを含む正負例を独立Gitコピーで実証する。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from check_task016_fixed_anchor import ROOT, TRUST_RECORD, trusted_record, verify_checkout, verify_selection
from test_task012_pinned_audit import MANIFEST, WORKFLOW, REQUEST012, normalized_request, run, show, synthetic


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--latest-sha', required=True)
    parser.add_argument('--fixed012-path', type=Path, required=True)
    args = parser.parse_args()
    output = ROOT / 'docs/verification/task-016/anchor-cases'
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    results = {}
    report = {'status': 'FAIL', 'execution_sha': args.latest_sha, 'trust_record_sha': TRUST_RECORD, 'results': results}
    try:
        if run(ROOT, 'rev-parse', 'HEAD').decode().strip() != args.latest_sha:
            raise ValueError('反証実行SHA不一致')
        expected = verify_selection(ROOT, args.latest_sha)
        verify_checkout(args.fixed012_path, expected)
        results['approved-head'] = {'status': 'PASS', **expected}
        with tempfile.TemporaryDirectory(prefix='task016-anchor-') as directory:
            repo = Path(directory) / 'copy'
            run(ROOT, 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(repo))
            original = expected['completed_sha']
            state = normalized_request(show(repo, original, REQUEST012)).replace(
                b'- state: excluded', '- 状態：016コピー限定の後続状態'.encode())
            moved = synthetic(repo, original, {REQUEST012: state})
            manifest = trusted_record(repo)
            manifest['completed_sha'] = moved
            manifest['completed_tree'] = run(repo, 'rev-parse', moved + '^{tree}').decode().strip()
            workflow = show(repo, args.latest_sha, WORKFLOW)
            # 元013と同じ、env + checkout + manifest SHA/treeを同時更新する。
            cases = {
                'state-child-manifest-and-workflow-and-checkout': {
                    MANIFEST: json.dumps(manifest).encode(),
                    WORKFLOW: workflow.replace(original.encode(), moved.encode())},
                'state-child-manifest-only': {MANIFEST: json.dumps(manifest).encode()},
                'state-child-workflow-and-checkout-only': {WORKFLOW: workflow.replace(original.encode(), moved.encode())},
                'wrong-tree': {MANIFEST: json.dumps({**trusted_record(repo), 'completed_tree': 'f' * 40}).encode()},
                'malformed-sha': {MANIFEST: json.dumps({**trusted_record(repo), 'completed_sha': 'HEAD'}).encode()},
                'nonexistent-sha': {MANIFEST: json.dumps({**trusted_record(repo), 'completed_sha': '0' * 40}).encode()},
                'missing-record-fields': {MANIFEST: b'{}'},
                'invalid-record-json': {MANIFEST: b'not json'},
                'missing-checkout': {WORKFLOW: workflow.replace(('          path: completed012\n').encode(), b'          path: missing012\n')},
            }
            for name, changes in cases.items():
                commit = synthetic(repo, args.latest_sha, changes)
                try:
                    verify_selection(repo, commit)
                except (ValueError, KeyError, TypeError) as exc:
                    results[name] = {'status': 'PASS', 'input_sha': commit, 'rejection': str(exc)}
                else:
                    raise ValueError('異常固定参照を受理: ' + name)
            # ファイルそのものが欠損したcommitも受理しない。
            run(repo, 'checkout', '--quiet', '--detach', args.latest_sha)
            run(repo, 'rm', '--quiet', MANIFEST)
            run(repo, '-c', 'user.name=016コピー', '-c', 'user.email=qa@example.invalid', 'commit', '--quiet', '-m', '固定記録欠損の負例')
            missing = run(repo, 'rev-parse', 'HEAD').decode().strip()
            try:
                verify_selection(repo, missing)
            except ValueError as exc:
                results['missing-record-file'] = {'status': 'PASS', 'input_sha': missing, 'rejection': str(exc)}
            else:
                raise ValueError('記録ファイル欠損を受理')
            # manifest/workflowが正しいままでも実checkoutの付替えは拒否。
            run(repo, 'checkout', '--quiet', '--detach', moved)
            try:
                verify_checkout(repo, expected)
            except ValueError as exc:
                results['state-child-actual-checkout'] = {'status': 'PASS', 'rejected_sha': moved, 'rejection': str(exc)}
            else:
                raise ValueError('状態子commitの実checkoutを受理')
            run(repo, 'checkout', '--quiet', '--detach', original)
            source = repo / 'tools/test_task012_pinned_audit.py'
            source.write_bytes(source.read_bytes() + b'\n# copy mutation\n')
            try:
                verify_checkout(repo, expected)
            except ValueError as exc:
                results['modified-fixed-checker'] = {'status': 'PASS', 'rejection': str(exc)}
            else:
                raise ValueError('固定検査器の変更を受理')
            # 信頼基点自身が取得できないコピー。latestへのfallbackは禁止。
            empty = Path(directory) / 'empty'; empty.mkdir(); run(empty, 'init', '--quiet')
            try:
                trusted_record(empty)
            except ValueError as exc:
                results['unavailable-trust-record'] = {'status': 'PASS', 'rejection': str(exc)}
            else:
                raise ValueError('信頼基点欠損を受理')
        report['status'] = 'PASS'
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        report['failure'] = str(exc)
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    (output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
