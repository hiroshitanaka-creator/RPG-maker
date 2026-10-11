#!/usr/bin/env python3
"""065: 完成時の範囲、最新の継続条件、原証拠の世代を分けて照合する。"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = 'tools/fixtures/equipment-save-transaction-platform/'
FIXED059 = '41a34ea33fe184274e6722c88cdbca2a7ffd3708'
BASE059 = '579ca1f463aaf9e93275039a59cf9d1ffb86adb5'
REGISTER059 = 'a6022f1e4a7689440928efe65db444336e9128e4'
BASE = '520169e72fd5a86d485bbf29577a9a22f34e96c8'
EVIDENCE = 'docs/verification/task065-save-qa-generations/'
TASK = 'docs/tasks/065-separate-save-qa-generations.md'
CODE = tuple(FIXTURE + name for name in (
    'diagnostic_ci057.py', 'diagnostic_evidence059.py',
    'generation_contract.py', 'test_generation_contract.py'))
DOCUMENTS = (TASK, 'docs/tasks/reports/065-separate-save-qa-generations.md')
EVIDENCE_NAMES = ('README.md', 'assertion-map.json', 'code-fixed-sha.txt', 'hashes.json',
                  'local-results.json', 'local-stdout.log', 'local-stderr.log',
                  'local-artifacts.tar.gz.b64', 'linux-results.json',
                  'linux-artifacts.tar.gz.b64', 'windows-results.json',
                  'windows-artifacts.tar.gz.b64', 'ci-results.json', 'scope-diff.json')
ALLOWED = set(CODE + DOCUMENTS + tuple(EVIDENCE + name for name in EVIDENCE_NAMES))
COMMANDS = ('capture-tests', 'scope059', 'capture059', 'baseline058', 'measurements',
            'generation-contract', 'generation-tests')
SETUP = ('generation-pins', 'baseline-checkout', 'fixed059-checkout')
BUDGETS = dict(zip(COMMANDS, (180, 30, 180, 30, 180, 30, 30)),
               **{name: 30 for name in SETUP})
CASES057 = ('normal', 'abnormal-child', 'parent-exception', 'forced-child-kill',
            'child-real-30-seconds', 'suite-inner-deadline', 'launch-failure',
            'suite-run-parent-exception', 'parallel-batch-normal',
            'parallel-worker-exception', 'shutdown-active-and-futures', 'outer-timeout-scaled')
CASES059 = tuple('prelaunch-' + x for x in (
    'config', 'env', 'capture', 'log', 'capture-record', 'request-record', 'unstarted-batch-record')) + (
    'suite-run-queue-before-config', 'four-root-shared-batch') + tuple('record-' + x for x in (
    'missing', 'broken', 'id', 'batch', 'batch-content', 'unstarted-batch')) + (
    'close-race-and-repeated', 'acceptance-close-race', 'outer-kill-owned-grandchild',
    'parent-exits-first-log-holder', 'nested-capture-stays-in-outer-supervision',
    'ownership-unknown-preserved', 'zero-deadline-unconfirmed', 'supervision-setup-failure',
    'assignment-exit-races', 'ownership-read-child-exit-race',
    'stop-retry-before-wait-consumes-deadline', 'created-before-supervision-failure')
SCOPE_CASES = ('later-document', 'outside-code', 'outside-fixed', 'changed-fixed-code',
               'old-evidence-document', 'past-report', 'outside-document',
               'changed-task-body', 'rewritten-decision-log', 'appended-decision-log')
NEW_CONDITIONS = ('scope065', 'generation-identity', 'source-bytes', 'assertion-coverage',
                  'command-set', 'process-terminal', 'raw-evidence', 'failure-propagation',
                  'fixed059-ten', 'latest-twelve-twentyseven-twelve', 'archive-members')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'JSON重複キー:' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def sha(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{40}', value), '完全SHA必須')
    return value


def pin(root):
    return sha((root / EVIDENCE / 'code-fixed-sha.txt').read_text().strip())


def changes(root, first, last):
    return [line.split('\t') for line in git(root, 'diff', '--no-renames', '--name-status', first, last).decode().splitlines()]


def strip_status(raw):
    return re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b.*$', b'', raw, flags=re.M)


def scope(root, code, source=None):
    """065の完成範囲だけを固定。任意の後続HEADへこの許可集合を適用しない。"""
    sha(code)
    rows = changes(root, BASE, code)
    require(all(status in ('A', 'M') and path in ALLOWED for status, path in rows), '065未列挙差分')
    require({path for _, path in rows} >= set(CODE), '065専用4コード欠落')
    require(strip_status(git(root, 'show', BASE + ':' + TASK)) ==
            strip_status(git(root, 'show', code + ':' + TASK)), '065依頼本文変更')
    if source is not None:
        sha(source)
        later = changes(root, code, source)
        require(all(status in ('A', 'M') and path in ALLOWED - set(CODE)
                    and path != EVIDENCE + 'assertion-map.json' for status, path in later), '065提出差分')
        require(strip_status(git(root, 'show', source + ':' + TASK)) ==
                strip_status(git(root, 'show', BASE + ':' + TASK)), '065提出依頼本文変更')
    return rows


def assertion_inventory(root):
    """固定059の全assert/raiseを位置とAST hashで列挙。新実装から旧期待を作らない。"""
    result = []
    for name in ('scope059.py', 'test_capture057.py', 'test_capture059.py',
                 'diagnostics057.py', 'diagnostic_ci057.py', 'diagnostic_evidence059.py'):
        raw = git(root, 'show', FIXED059 + ':' + FIXTURE + name)
        for node in ast.walk(ast.parse(raw)):
            # runner/collectorの失敗条件はraiseに加えてfailures/errors.appendで保持する。
            append = (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                      and node.func.attr in ('append', 'extend') and isinstance(node.func.value, ast.Name)
                      and node.func.value.id in ('failures', 'errors'))
            if isinstance(node, (ast.Assert, ast.Raise)) or append:
                result.append(dict(id=name + ':' + str(node.lineno) + ':' + str(node.col_offset),
                                   ast_sha256=digest(ast.dump(node, include_attributes=False).encode()),
                                   category='当時だけ' if name == 'scope059.py' else '最新でも継続',
                                   destination='fixed059/scope059' if name == 'scope059.py' else {
                                       'test_capture057.py': 'latest/capture-tests',
                                       'test_capture059.py': 'latest/capture059',
                                       'diagnostics057.py': 'latest/measurements',
                                       'diagnostic_ci057.py': 'latest/execution',
                                       'diagnostic_evidence059.py': 'latest/evidence'}[name]))
    return sorted(result, key=lambda row: row['id'])


def check_map(root, value):
    require(value.get('fixed059_sha') == FIXED059 and value.get('registration065_sha') == BASE, '対応表の世代')
    require(value.get('old_assertions') == assertion_inventory(root), '旧assertionの欠落/重複/改変')
    require(value.get('new_conditions') == [dict(id=x, category='今回承認された配線・証拠契約の新条件',
                                               destination='latest/generation-contract') for x in NEW_CONDITIONS], '新条件の欠落/重複')


def check_sources(root, code, source):
    sha(code); sha(source)
    require(git(root, 'rev-parse', 'HEAD').decode().strip() == source, '最新checkout SHAすり替え')
    scope(root, code)
    # 065の配線は完成版と同一。後続の別文書・独立codeを一律に拒否しない。
    paths = list(CODE) + [EVIDENCE + 'assertion-map.json']
    for path in paths:
        require((root / path).read_bytes() == git(root, 'show', code + ':' + path) ==
                git(root, 'show', source + ':' + path), '065完成code改変:' + path)
    # 本番・監督・旧検査・期待・CI等の今回の継続境界を明示する。別承認変更は別契約で扱う。
    fixed_paths = git(root, 'ls-tree', '-r', '--name-only', BASE, 'scripts', 'native', 'addons',
                      'test', '.scope-lock', '.github', 'tools', 'project.godot').decode().splitlines()
    changed = {path for _, path in changes(root, BASE, source)}
    require(not (changed & (set(fixed_paths) - set(CODE))), '本番/監督/原検査のGit差分')
    dirty = git(root, 'diff', '--name-only', source, '--', 'scripts', 'native', 'addons',
                'test', '.scope-lock', '.github', 'tools', 'project.godot').decode().splitlines()
    require(not (set(dirty) - set(CODE)), '本番/監督/原検査の作業tree差分')
    check_map(root, load(root / EVIDENCE / 'assertion-map.json'))
    return dict(code_sha=code, source_sha=source, fixed059_sha=FIXED059,
                checked_files=len(paths) + len(fixed_paths) - 2, scope=scope(root, code))


def fixed_checkout(root):
    require(git(root, 'rev-parse', 'HEAD').decode().strip() == FIXED059, '固定checkout SHA')
    require(not git(root, 'status', '--porcelain', '--untracked-files=all'), '固定checkout改変')
    raw = (root / FIXTURE / 'scope059.py').read_bytes()
    require(raw == git(root, 'show', FIXED059 + ':' + FIXTURE + 'scope059.py'), '固定検査器改変')
    return dict(sha=FIXED059, scope_sha256=digest(raw), clean=True)


def snapshot(area, exclude=()):
    import os
    files = {}; links = {}; directories = []
    for path in sorted(area.rglob('*')):
        name = path.relative_to(area).as_posix()
        if name in exclude:
            continue
        if path.is_symlink():
            raw = os.fsencode(os.readlink(path))
            links[name] = dict(target_hex=raw.hex(), bytes=len(raw), sha256=digest(raw))
        elif path.is_file():
            raw = path.read_bytes(); files[name] = dict(bytes=len(raw), sha256=digest(raw))
        elif path.is_dir():
            directories.append(name)
        else:
            raise ValueError('原証拠の特殊file:' + name)
    return dict(files=files, symbolic_links=links, directories=directories)


def record_ok(row, budget):
    require(row.get('exit_code') == 0 and type(row.get('exit_code')) is int, '実exit非0/欠落')
    require(row.get('terminal') is True and row.get('record_saved') is True, '終端/保存未確認')
    require(row.get('timed_out') is False and row.get('exception') is None, 'timeout/例外')
    require(row.get('supervision', {}).get('stopped') is True and row.get('wait', {}).get('ok') is True, '終了未確認')
    require(row.get('budget_seconds') == budget, '原予算変更')
    require(row.get('argv') == row.get('planned_argv') and bool(row.get('argv')), '実argv欠落/相違')
    require(row.get('pid') and row.get('ended_utc') and row.get('started_utc'), '起動/終了記録欠落')
    require(0 <= row['ended_monotonic'] - row['started_monotonic'] <= budget and
            0 <= row['seconds'] <= budget, '終了時刻/予算')


def validate_execution(area, source, code):
    """新schemaは原process/log/manifestと内容を照合。失敗結果も収集対象から外さない。"""
    value = load(area / 'execution.json')
    sha(source); sha(code)
    require(value.get('schema') == 3, '新schema必須')
    require(value.get('source_sha') == source and value.get('code_sha') == FIXED059 and
            value.get('generation_code_sha') == code, '世代/SHAすり替え')
    require(value.get('status') == 'PASS' and value.get('failures') == [], '失敗隠蔽/未終端')
    require(value.get('fixed_checkout_before') == value.get('fixed_checkout_after') and
            value.get('fixed_checkout_before', {}).get('sha') == FIXED059 and
            value.get('fixed_checkout_before', {}).get('clean') is True, '固定checkout原物未確認')
    require([r['label'] for r in value['commands']] == list(COMMANDS) and
            [r['label'] for r in value['setup']] == list(SETUP), '診断/準備の欠落/重複')
    manifest = load(area / 'generation-manifest.json')
    require(manifest == snapshot(area, ('generation-manifest.json',)), '証拠bytes/hash/集合改変')
    for row in value['setup'] + value['commands']:
        label = row['label']; record_ok(row, BUDGETS[label])
        persisted = load(area / (label + '-process.json'))
        require(persisted == {k: v for k, v in row.items() if k != 'label'}, '原process改変:' + label)
        raw = (area / (label + '.log')).read_bytes()
        require(digest(raw) == row['log_sha256'], '原log改変:' + label)
        expected = FIXED059 if label == 'scope059' else source
        require(value['targets'].get(label) == expected, '実行世代:' + label)
        if label == 'scope059':
            require(Path(row['cwd']).name == 'qa065-fixed059' and
                    '--code-sha' in row['argv'] and row['argv'][row['argv'].index('--code-sha') + 1] == FIXED059 and
                    row['argv'][row['argv'].index('--source-sha') + 1] == FIXED059 and
                    Path(row['argv'][1]).is_relative_to(Path(row['cwd'])), '固定059実argv/cwd')
        elif label not in SETUP:
            scripts = dict(zip(COMMANDS, ('test_capture057.py', 'scope059.py', 'test_capture059.py',
                           'reproduce058.py', 'diagnostics057.py', 'generation_contract.py', 'test_generation_contract.py')))
            require(row['cwd'] == value['checkout'] and
                    Path(row['argv'][1]) == Path(value['checkout']) / FIXTURE / scripts[label], '最新実argv/cwd')
    for label, expected in (('capture-tests', CASES057), ('capture059', CASES059)):
        tests = load(area / label / 'tests.json')
        require(tests.get('status') == 'PASS' and [r['case'] for r in tests['cases']] == list(expected) and
                all(r.get('status') == 'PASS' for r in tests['cases']), '最新全正負欠落:' + label)
    fixed = load(area / 'scope.json')
    require((fixed.get('base'), fixed.get('registration'), fixed.get('code_sha'), fixed.get('source_sha')) ==
            (BASE059, REGISTER059, FIXED059, FIXED059), '059基点/登録/完成の混同')
    require([r['case'] for r in fixed['propagation']] == list(SCOPE_CASES), '059全10正負欠落')
    for index, row in enumerate(fixed['propagation']):
        require(row['exit_code'] == row['expected_exit'] == (0 if index == 0 else 1), '059正負exit')
        require((area / 'scope059' / (row['case'] + '.log')).is_file(), '059正負原log欠落')
    measurement = load(area / 'measurements/diagnostics.json')
    require(measurement.get('source_sha') == source and measurement.get('status') == 'PASS' and
            measurement.get('failures') == [], '最新計測失敗/世代')
    require([(s['seed'], s['mode']) for s in measurement['samples']] ==
            [(seed, mode) for seed in ('typed', 'plain', 'granted', 'trial-missing', 'trial-corrupt', 'trial-unclean')
             for mode in ('off', 'on')], '最新12sample欠落')
    contract = load(area / 'generation.json')
    require(contract.get('source_sha') == source and contract.get('code_sha') == code and
            contract.get('fixed059_sha') == FIXED059, '世代契約検査失敗')
    from test_generation_contract import CASES
    tests = load(area / 'generation-tests/tests.json')
    require(tests.get('status') == 'PASS' and [r['case'] for r in tests['cases']] == list(CASES) and
            all(r['exit_code'] == r['expected_exit'] for r in tests['cases']), '専用正負欠落/失敗')
    return value


def main(args):
    root = Path(args.checkout).resolve()
    code = sha(args.code_sha) if args.code_sha else pin(root)
    if args.fetch_pins:
        for value in (BASE, code, FIXED059, BASE059, REGISTER059):
            if subprocess.run(['git', 'cat-file', '-e', value + '^{commit}'], cwd=root,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
                subprocess.run(['git', 'fetch', '--no-tags', '--depth=1', 'origin', value], cwd=root, check=True)
        result = dict(required_shas=[BASE, code, FIXED059, BASE059, REGISTER059])
    elif args.validate_evidence:
        result = validate_execution(Path(args.validate_evidence), args.source_sha, code)
    elif args.scope_only:
        result = scope(root, code, args.source_sha)
    else:
        result = check_sources(root, code, args.source_sha)
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('GENERATION065_PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkout', default=str(ROOT)); parser.add_argument('--code-sha')
    parser.add_argument('--source-sha'); parser.add_argument('--output')
    parser.add_argument('--fetch-pins', action='store_true'); parser.add_argument('--scope-only', action='store_true')
    parser.add_argument('--validate-evidence')
    try:
        main(parser.parse_args())
    except Exception as exc:
        print('GENERATION065_FAIL: ' + type(exc).__name__ + ': ' + str(exc)); sys.exit(1)
