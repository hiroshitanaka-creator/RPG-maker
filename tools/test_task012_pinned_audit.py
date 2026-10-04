#!/usr/bin/env python3
"""完成点の不変選択・当時の範囲監査・後続commitによる再発を独立コピーで検証する。"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

# 依頼書から独立に転記した期待値。workflowの実装値から生成しない。
EXPECTED006 = '5f1c2ba231191b25b9b32a814b616a9f8d0a54ce'
EXPECTED009 = 'ce07fdada0466138260ab678c10fd78e61c0c63d'
TREE009 = '655312a33364d8e3fe97f09bd9bd3c415ed1ceae'
START012 = '8ed58c00f8d7d16e2df24f3273f18019d2406002'
PARENT = 'a1022b6340d772900563b0d2f60969f9adf50b25'
WORKFLOW = '.github/workflows/region2-village-connections.yml'
CHECKER009 = 'tools/check_task009_scope.py'
SELF = 'tools/test_task012_pinned_audit.py'
REQUEST009 = 'docs/tasks/009-test-lifecycle.md'
REQUEST012 = 'docs/tasks/012-pin-completed-audit.md'
MANIFEST = 'docs/verification/task-012/completed-audit.json'
ALLOWED012 = {WORKFLOW, SELF, REQUEST009, REQUEST012, 'docs/decision-log.md',
              'docs/tasks/reports/012-pin-completed-audit.md'}


def run(repo: Path, *args: str, input_bytes: bytes | None = None, env: dict | None = None) -> bytes:
    result = subprocess.run(['git', *args], cwd=repo, input=input_bytes, env=env,
                            capture_output=True, timeout=180)
    if result.returncode:
        raise ValueError('git失敗: ' + ' '.join(args) + '\n' + result.stderr.decode(errors='replace'))
    return result.stdout


def show(repo: Path, ref: str, path: str) -> bytes:
    return run(repo, 'show', ref + ':' + path)


def resolve(repo: Path, ref: str) -> str:
    if not re.fullmatch('[0-9a-f]{40}', ref):
        raise ValueError('完全SHA以外の可変参照を拒否: ' + ref)
    actual = run(repo, 'rev-parse', '--verify', ref + '^{commit}').decode().strip()
    if actual != ref:
        raise ValueError('完全SHAとcommitが一致しない')
    return actual


def selected(repo: Path, latest: str, expected012: str) -> dict:
    workflow = show(repo, latest, WORKFLOW).decode()
    expected = {'FIXED_006_SHA': EXPECTED006, 'FIXED_009_SHA': EXPECTED009,
                'FIXED_012_SHA': expected012}
    for name, value in expected.items():
        matches = re.findall(r'^  ' + name + r': (\S+)$', workflow, re.M)
        if matches != [value]:
            raise ValueError('独立期待値と固定選択が一致しない: ' + name)
        resolve(repo, matches[0])
    if 'git log' in workflow or 'task_commit=' in workflow:
        raise ValueError('可変の完成点探索を拒否')
    for value, checkout in [(EXPECTED006, 'fixed'), (EXPECTED009, 'completed009'), (expected012, 'completed012')]:
        if f'ref: {value}\n          fetch-depth: 0\n          path: {checkout}' not in workflow:
            raise ValueError('固定SHAの別checkoutが欠落: ' + checkout)
    required = ['(cd ../completed009 && python tools/check_task009_scope.py --commit "$FIXED_009_SHA")',
                'python tools/check_task009_lifecycle.py --fixed-sha "$FIXED_006_SHA"',
                'python tools/check_region2_village_regression.py --commit "$GITHUB_SHA"',
                'python tools/test_task009_lifecycle.py --fixed-path ../fixed --godot ../godot',
                'timeout 180 python ../completed012/tools/test_task012_pinned_audit.py',
                '--current-path . --fixed009-path ../completed009 --completed012-sha "$FIXED_012_SHA" --latest-sha "$GITHUB_SHA"']
    if any(item not in workflow for item in required):
        raise ValueError('固定/最新/反証の実行コマンドが欠落')
    if re.findall(r'timeout-minutes: (\d+)', workflow) != ['15', '15', '15']:
        raise ValueError('既存jobの上限が不一致')
    if 'continue-on-error' in workflow:
        raise ValueError('失敗無視を拒否')
    return expected


def tree(repo: Path, ref: str) -> dict[str, str]:
    return {line.split('\t', 1)[1]: line.split()[2]
            for line in run(repo, 'ls-tree', '-r', ref).decode().splitlines()}


def normalized_request(content: bytes) -> bytes:
    return re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b\xef\xbc\x9a.*$', b'- state: excluded',
                  content, count=1, flags=re.M)


def scope012(repo: Path, commit: str) -> dict:
    resolve(repo, commit)
    run(repo, 'merge-base', '--is-ancestor', START012, commit)
    base, target = tree(repo, START012), tree(repo, commit)
    changed = sorted(p for p in base.keys() | target.keys() if base.get(p) != target.get(p))
    failures = [p for p in changed if p not in ALLOWED012 and not p.startswith('docs/verification/task-012/')]
    failures += ['削除: ' + p for p in base if p not in target]
    for path in [REQUEST009, REQUEST012]:
        if normalized_request(show(repo, START012, path)) != normalized_request(show(repo, commit, path)):
            failures.append('依頼書本文変更: ' + path)
    # 完成版workflowの変更を既存全文へ逆変換し、他の項目/上限の変更を拒否する。
    workflow = show(repo, commit, WORKFLOW).decode()
    restored = workflow.replace('  FIXED_009_SHA: ' + EXPECTED009 + '\n', '')
    restored = restored.replace('      - uses: actions/checkout@v4\n        with:\n          ref: ' + EXPECTED009 + '\n          fetch-depth: 0\n          path: completed009\n', '')
    restored = restored.replace('          # 完成SHAの当時検査器で完成差分のみを監査する。\n          (cd ../completed009 && python tools/check_task009_scope.py --commit "$FIXED_009_SHA")',
                                '          # 009専用の状態変更commitに固定し、後続の機能追加を009の差分に混ぜない。\n          task_commit=$(git log -1 --format=%H -- docs/tasks/009-test-lifecycle.md)\n          if grep -q "^- 状態：作業中$" docs/tasks/009-test-lifecycle.md; then task_commit=$GITHUB_SHA; fi\n          python tools/check_task009_scope.py --commit "$task_commit"')
    restored = restored.replace('            completed009/docs/verification/task-009/scope-checks.json\n            current/docs/verification/task-012/\n', '')
    if restored != show(repo, START012, WORKFLOW).decode():
        failures.append('承認した対象選択以外の既存workflow変更')
    # 全ての範囲外ファイルをblob一致で照合。原画・保護・本番・既存検査器も含む。
    return {'status': 'FAIL' if failures else 'PASS', 'start_sha': START012, 'execution_sha': commit,
            'changed_files': changed, 'preserved_paths': len(base) - len(changed), 'failures': failures}


def validate009(path: Path, selected_sha: str) -> None:
    if selected_sha != EXPECTED009:
        raise ValueError('009完成SHAが独立期待値と一致しない')
    resolve(path, selected_sha)
    if run(path, 'rev-parse', 'HEAD').decode().strip() != EXPECTED009:
        raise ValueError('固定009 checkoutのHEADが不一致')
    if run(path, 'rev-parse', 'HEAD^{tree}').decode().strip() != TREE009:
        raise ValueError('固定009 treeが独立期待値と不一致')
    changed = run(path, 'diff', '--name-only', 'HEAD').decode().splitlines()
    if any(not p.startswith('docs/verification/task-009/') for p in changed):
        raise ValueError('固定009 checkoutの本番/検査器が改変されている')
    if (path / CHECKER009).read_bytes() != show(path, EXPECTED009, CHECKER009):
        raise ValueError('当時009検査器のバイト改変')


def audit009(repo: Path, commit: str, checker: Path, output: Path, name: str) -> dict:
    result = subprocess.run([sys.executable, str(checker), '--commit', commit], cwd=repo,
                            capture_output=True, timeout=180)
    output.mkdir(parents=True, exist_ok=True)
    (output / (name + '.log')).write_bytes(result.stdout + result.stderr)
    report = json.loads((checker.parent.parent / 'docs/verification/task-009/scope-checks.json').read_text())
    (output / (name + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return {'exit_code': result.returncode, 'status': report['status'], 'execution_sha': report['execution_sha'],
            'failures': report['failures'], 'timeout_seconds': 180}


def synthetic(repo: Path, parent: str, changes: dict[str, bytes]) -> str:
    # 別コピーのindexとobjectsのみ。作業リポジトリの履歴/ブランチは動かさない。
    env = {**os.environ, 'GIT_INDEX_FILE': str(repo / '.git/case-index'),
           'GIT_AUTHOR_NAME': '012検証コピー', 'GIT_AUTHOR_EMAIL': 'qa@example.invalid',
           'GIT_COMMITTER_NAME': '012検証コピー', 'GIT_COMMITTER_EMAIL': 'qa@example.invalid'}
    run(repo, 'read-tree', parent, env=env)
    for path, data in changes.items():
        blob = run(repo, 'hash-object', '-w', '--stdin', input_bytes=data).decode().strip()
        run(repo, 'update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + path, env=env)
    new_tree = run(repo, 'write-tree', env=env).decode().strip()
    return run(repo, 'commit-tree', new_tree, '-p', parent, input_bytes='012一時反証\n'.encode(), env=env).decode().strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--current-path', type=Path, required=True)
    parser.add_argument('--fixed009-path', type=Path, required=True)
    parser.add_argument('--completed012-sha', required=True)
    parser.add_argument('--latest-sha', required=True)
    args = parser.parse_args()
    current, fixed009 = args.current_path.resolve(), args.fixed009_path.resolve()
    fixed012 = Path(__file__).resolve().parent.parent
    output = current / 'docs/verification/task-012/pinned-audit'
    output.mkdir(parents=True, exist_ok=True)
    report = {'status': 'FAIL', 'latest_sha': args.latest_sha, 'results': {}}
    results = report['results']
    try:
        latest = resolve(current, args.latest_sha)
        if run(current, 'rev-parse', 'HEAD').decode().strip() != latest:
            raise ValueError('最新回帰対象はcurrent checkoutのHEADでなければならない')
        manifest = json.loads(show(current, latest, MANIFEST))
        expected012 = manifest['completed_sha']
        if args.completed012_sha != expected012:
            raise ValueError('012選択SHAが独立固定記録と不一致')
        resolve(current, expected012)
        if run(current, 'rev-parse', expected012 + '^{tree}').decode().strip() != manifest['completed_tree']:
            raise ValueError('012固定treeが記録と不一致')
        if run(fixed012, 'rev-parse', 'HEAD').decode().strip() != expected012 or fixed012 == current:
            raise ValueError('012検査器は機能完成SHAの別checkoutで実行する')
        if (fixed012 / SELF).read_bytes() != show(current, expected012, SELF):
            raise ValueError('012完成検査器の改変')
        selected(current, latest, expected012)
        validate009(fixed009, EXPECTED009)
        report.update(fixed006_sha=EXPECTED006, fixed009_sha=EXPECTED009, completed012_sha=expected012,
                      completed012_tree=manifest['completed_tree'])
        twelve = scope012(current, expected012)
        (output / 'completed012-scope.json').write_text(json.dumps(twelve, ensure_ascii=False, indent=2) + '\n')
        if twelve['status'] != 'PASS':
            raise ValueError('012完成差分の範囲違反: ' + str(twelve['failures']))
        results['completed012-scope'] = twelve
        observed = audit009(current, EXPECTED009, fixed009 / CHECKER009, output, 'completed009-scope')
        if observed['exit_code'] != 0 or observed['status'] != 'PASS':
            raise ValueError('009固定監査が失敗')
        results['completed009-scope'] = observed
        with tempfile.TemporaryDirectory(prefix='task012-replay-') as directory:
            copy = Path(directory) / 'repo'
            result = subprocess.run(['git', 'clone', '--shared', '--no-checkout', '--quiet', str(current), str(copy)],
                                    capture_output=True, timeout=180)
            if result.returncode:
                raise ValueError('独立コピー取得失敗')
            checker = copy / CHECKER009
            checker.parent.mkdir(parents=True)
            checker.write_bytes(show(current, EXPECTED009, CHECKER009))
            state009 = re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b\xef\xbc\x9a.*$', '- 状態：親の将来確認（コピー限定）'.encode(),
                              show(current, latest, REQUEST009), count=1, flags=re.M)
            docs = {'docs/tasks/099-copy-only.md': '# 未発注のコピー限定登録\n'.encode()}
            registrations = {p: show(current, PARENT, p) for p in ['docs/tasks/010-record-ner.md', 'docs/tasks/011-ruins-dungeon-groundwork.md']}
            cases = [('new-request', latest, docs), ('009-state-only', latest, {REQUEST009: state009}),
                     ('state-and-new-request-same-commit', latest, {REQUEST009: state009, **docs}),
                     ('state-and-010-011-same-commit', latest, {REQUEST009: state009, **registrations}),
                     ('future-other-scope', latest, {'scripts/game/game_session.gd': show(current, latest, 'scripts/game/game_session.gd') + '\n# 012コピー限定の別範囲変更\n'.encode()}),
                     ('012-state-only', latest, {REQUEST012: normalized_request(show(current, latest, REQUEST012)).replace(b'- state: excluded', '- 状態：親の将来確認（コピー限定）'.encode())})]
            # 010/011が既にあるHEADでは追加差分を再現できないため、歴史009点からも同時追加する。
            prior_workflow = show(current, latest, WORKFLOW)
            prior_manifest = show(current, latest, MANIFEST)
            cases.append(('historical-state-and-010-011-added', EXPECTED009,
                          {REQUEST009: state009, **registrations, WORKFLOW: prior_workflow, MANIFEST: prior_manifest}))
            for name, parent, changes in cases:
                commit = synthetic(copy, parent, changes)
                observed_selection = selected(copy, commit, expected012)
                observed = audit009(copy, EXPECTED009, checker, output, name)
                if observed['exit_code'] != 0 or observed['status'] != 'PASS':
                    raise ValueError('後続変更で固定監査失敗: ' + name)
                if scope012(copy, expected012)['status'] != 'PASS':
                    raise ValueError('後続変更で012完成監査が動いた')
                results[name] = {'status': 'PASS', 'input_sha': commit, 'changes': sorted(changes),
                                 'selection': observed_selection, 'fixed009_audit': observed,
                                 'completed012_audit_sha': expected012}
            # 元のアルゴリズムが親登録を選び010/011を誤拒否することも証明する。
            old = run(copy, 'log', '-1', '--format=%H', PARENT, '--', REQUEST009).decode().strip()
            if old != PARENT:
                raise ValueError('旧不具合の再現入力が不一致')
            observed = audit009(copy, old, checker, output, 'old-selector-parent-registration')
            if observed['exit_code'] != 1 or not all(p in observed['failures'] for p in registrations):
                raise ValueError('旧選択の範囲誤拒否を再現できない')
            results['old-selector-parent-registration'] = {'status': 'PASS', 'old_selected_sha': old, **observed}
            results['old-selector-parent-registration']['status'] = 'PASS'
            for name, sha in [('wrong009-sha', START012), ('nonexistent-sha', '0' * 40), ('wrong012-sha', PARENT)]:
                field = 'FIXED_012_SHA' if name == 'wrong012-sha' else 'FIXED_009_SHA'
                original = expected012 if field == 'FIXED_012_SHA' else EXPECTED009
                broken = synthetic(copy, latest, {WORKFLOW: prior_workflow.replace((field + ': ' + original).encode(), (field + ': ' + sha).encode())})
                try:
                    selected(copy, broken, expected012)
                except ValueError as exc:
                    results[name] = {'status': 'PASS', 'rejection': str(exc), 'input_sha': broken}
                else:
                    raise ValueError('異常SHA受理: ' + name)
            try:
                resolve(copy, '0' * 40)
            except ValueError as exc:
                results['nonexistent-object'] = {'status': 'PASS', 'rejection': str(exc)}
            else:
                raise ValueError('不存在commit受理')
            bad009 = synthetic(copy, EXPECTED009, {'docs/tasks/099-copy-only.md': b'# forbidden inside 009 completion\n'})
            observed = audit009(copy, bad009, checker, output, 'broken009-target')
            if observed['exit_code'] != 1 or 'docs/tasks/099-copy-only.md' not in observed['failures']:
                raise ValueError('壊れた009固定対象が成功扱い')
            results['broken009-target'] = {'status': 'PASS', 'rejected_sha': bad009, 'audit': observed}
            bad012 = synthetic(copy, expected012, {'scripts/game/game_session.gd': b'# forbidden inside 012 completion\n'})
            observed12 = scope012(copy, bad012)
            if observed12['status'] != 'FAIL' or 'scripts/game/game_session.gd' not in observed12['failures']:
                raise ValueError('012範囲違反が成功扱い')
            results['broken012-target'] = {'status': 'PASS', 'audit': observed12}
            # 当時検査器を改変した別checkoutを拒否。元checkoutへ書き込まない。
            run(copy, 'sparse-checkout', 'set', '--no-cone', '/' + CHECKER009)
            run(copy, 'checkout', '--detach', EXPECTED009)
            checker.write_bytes(checker.read_bytes() + '# コピーだけの不変違反\n'.encode())
            try:
                validate009(copy, EXPECTED009)
            except ValueError as exc:
                results['modified009-checkout'] = {'status': 'PASS', 'rejection': str(exc)}
            else:
                raise ValueError('固定checkoutの改変受理')
        report['status'] = 'PASS'
    except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as exc:
        report['failure'] = str(exc)
    (output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
