#!/usr/bin/env python3
"""016の完成差分だけを監査し、後続HEADの別段階編集を混ぜない。"""
from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import re
import sys
import tempfile

from check_task016_fixed_anchor import ROOT
from test_task012_pinned_audit import WORKFLOW, normalized_request, resolve, run, selected, show, synthetic, tree

START = 'cc86765d7b5bba158dca8b828a626aad98610f12'
RECORD = 'docs/verification/task-016/completed-audit.json'
# 016依頼書の変更範囲をそのまま固定。006/009/012の許可一覧は変更しない。
PERMITTED = {WORKFLOW, 'tools/check_task016_fixed_anchor.py', 'tools/test_task016_fixed_anchor.py',
             'tools/check_task016_scope.py', 'tools/check_region2_village_regression.gd',
             'tools/capture_task009_village_regression.gd', 'tools/test_task009_lifecycle.py',
             'docs/verification/task-009/assertion-map.json', 'docs/verification/task-009/assertion-map.md',
             'docs/decision-log.md', 'docs/tasks/016-fix-audit-review.md',
             'docs/tasks/reports/016-fix-audit-review.md', 'docs/tasks/009-test-lifecycle.md',
             'docs/tasks/012-pin-completed-audit.md'}


def audit(repo: Path, completed: str) -> dict:
    resolve(repo, completed)
    run(repo, 'merge-base', '--is-ancestor', START, completed)
    base, final = tree(repo, START), tree(repo, completed)
    changed = sorted(p for p in base.keys() | final.keys() if base.get(p) != final.get(p))
    failures = [p for p in changed if p not in PERMITTED and not p.startswith('docs/verification/task-016/')]
    failures += ['削除: ' + p for p in base if p not in final]
    for path in ['docs/tasks/009-test-lifecycle.md', 'docs/tasks/012-pin-completed-audit.md', 'docs/tasks/016-fix-audit-review.md']:
        if normalized_request(show(repo, START, path)) != normalized_request(show(repo, completed, path)):
            failures.append('依頼書本文変更: ' + path)
    old = show(repo, START, WORKFLOW).decode().splitlines()
    new = show(repo, completed, WORKFLOW).decode().splitlines()
    # 既存workflowは追加のみ。全旧コマンド・assertion・matrix・上限の削除や変更を拒否する。
    for tag, i, j, _a, _b in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag in ('delete', 'replace'):
            failures.append('既存workflowの削除/変更: ' + '\n'.join(old[i:j]))
    selected(repo, completed, 'c327e7c439c9c8c8f1fd640e6cda6df7550fb26a')
    return {'status': 'FAIL' if failures else 'PASS', 'start_sha': START, 'execution_sha': completed,
            'completed_tree': run(repo, 'rev-parse', completed + '^{tree}').decode().strip(),
            'changed_files': changed, 'preserved_paths': len(base)-len(changed), 'failures': failures}


def verify_record(repo: Path, latest: str, completed: str, fixed: Path) -> dict:
    record = json.loads(show(repo, latest, RECORD))
    if record['completed_sha'] != completed or record['start_sha'] != START:
        raise ValueError('016完成記録と明示固定SHA/開始点が不一致')
    if run(fixed, 'rev-parse', 'HEAD').decode().strip() != completed:
        raise ValueError('016固定checkoutのHEAD不一致')
    if run(fixed, 'rev-parse', 'HEAD^{tree}').decode().strip() != record['completed_tree']:
        raise ValueError('016固定checkoutのtree不一致')
    if run(fixed, 'diff', '--name-only', 'HEAD').strip():
        raise ValueError('016固定checkoutの追跡入力がdirty')
    workflow = show(repo, latest, WORKFLOW).decode()
    if re.findall(r'^  FIXED_016_SHA: (\S+)$', workflow, re.M) != [completed]:
        raise ValueError('016 workflowの固定完全SHA不一致')
    if f'ref: {completed}\n          fetch-depth: 0\n          path: completed016' not in workflow:
        raise ValueError('016の固定別checkout欠損')
    return audit(fixed, completed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--completed-sha', required=True)
    parser.add_argument('--fixed-path', type=Path, required=True)
    parser.add_argument('--latest-sha', required=True)
    parser.add_argument('--bootstrap', action='store_true', help='完成commit初回のみ、まだ記録のない完成差分を直接監査する')
    args = parser.parse_args()
    out = ROOT / 'docs/verification/task-016/scope-checks.json'; out.parent.mkdir(parents=True, exist_ok=True)
    results = {}; report = {'status': 'FAIL', 'execution_sha': args.latest_sha, 'results': results}
    try:
        resolve(ROOT, args.latest_sha)
        if run(ROOT, 'rev-parse', 'HEAD').decode().strip() != args.latest_sha:
            raise ValueError('最新SHAと実行HEAD不一致')
        original = audit(args.fixed_path, args.completed_sha)
        if original['status'] != 'PASS':raise ValueError('016完成差分が許可範囲外: '+str(original['failures']))
        if not args.bootstrap:
            original = verify_record(ROOT, args.latest_sha, args.completed_sha, args.fixed_path)
        results['completed-scope'] = original
        with tempfile.TemporaryDirectory(prefix='task016-scope-') as directory:
            repo = Path(directory) / 'copy'
            run(ROOT, 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(repo))
            request = 'docs/tasks/016-fix-audit-review.md'
            changed_state = normalized_request(show(repo, args.latest_sha, request)).replace(b'- state: excluded', '- 状態：後続編集コピー'.encode())
            for name, changes in [
                ('state-only', {request: changed_state}),
                ('new-request', {'docs/tasks/099-copy-only.md': '# 後続依頼書登録コピー\n'.encode()}),
                ('state-and-request', {request: changed_state, 'docs/tasks/099-copy-only.md': '# コピー\n'.encode()}),
                ('future-other-scope', {'scripts/game/game_session.gd': b'# copy-only future change\n'})]:
                future = synthetic(repo, args.latest_sha, changes)
                # 後続HEADは監査しない。明示固定commitの結果がバイト同一であることを確認する。
                if audit(repo, args.completed_sha) != original:
                    raise ValueError('後続編集で完成差分が変化')
                if not args.bootstrap:
                    verify_record(repo, future, args.completed_sha, args.fixed_path)
                results[name] = {'status': 'PASS', 'input_sha': future, 'audited_sha': args.completed_sha}
            broken = synthetic(repo, args.completed_sha, {'scripts/game/game_session.gd': b'# forbidden inside 016 completion\n'})
            rejected = audit(repo, broken)
            if rejected['status'] != 'FAIL' or 'scripts/game/game_session.gd' not in rejected['failures']:
                raise ValueError('016完成差分内の本番改変を受理')
            results['broken-completed-scope'] = {'status': 'PASS', 'rejected_audit': rejected}
        report['status'] = 'PASS'
    except (ValueError, OSError, KeyError, TypeError) as exc:
        report['failure'] = str(exc)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':
    sys.exit(main())
