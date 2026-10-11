#!/usr/bin/env python3
"""065専用の正負。合成記録はvalidator fixtureであり、実診断成功を表さない。"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import generation_contract as g

CASES = ('scope-control', 'scope-outside', 'scope-production', 'scope-supervisor',
         'scope-old-assertion', 'scope-workflow', 'scope-task-body', 'scope-old-evidence',
         'scope-submission-document', 'scope-submission-code',
         'map-control', 'map-missing', 'map-duplicate', 'map-replaced',
         'evidence-control', 'wrapper-control', 'wrapper-altered', 'collector-control', 'collector-failure',
         'evidence-generation', 'evidence-fixed-sha',
         'evidence-code-sha', 'evidence-fixed-code', 'evidence-missing-command', 'evidence-duplicate-command',
         'evidence-missing-setup', 'evidence-failed-exit', 'evidence-timeout',
         'evidence-unconfirmed', 'evidence-missing-record', 'evidence-modified-log',
         'evidence-rehashed-log', 'evidence-record-mismatch', 'evidence-missing-case',
         'evidence-replaced-case', 'evidence-missing-sample', 'evidence-fixed-ten',
         'evidence-latest-cwd', 'evidence-budget', 'evidence-hidden-failure',
         'legacy-control', 'legacy-missing-command', 'legacy-missing-setup',
         'legacy-failed-exit')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def commit_variant(root, base, area, path, raw):
    env = dict(os.environ, GIT_INDEX_FILE=str(area / 'variant.index'))
    subprocess.run(['git', 'read-tree', base], cwd=root, env=env, check=True)
    blob = subprocess.check_output(['git', 'hash-object', '-w', '--stdin'], cwd=root, input=raw).decode().strip()
    subprocess.run(['git', 'update-index', '--add', '--cacheinfo', '100644', blob, path], cwd=root, env=env, check=True)
    tree = subprocess.check_output(['git', 'write-tree'], cwd=root, env=env).decode().strip()
    return subprocess.check_output(['git', '-c', 'user.name=QA', '-c', 'user.email=qa@example.invalid',
                                    'commit-tree', tree, '-p', base], cwd=root, input=b'065 scope fixture\n').decode().strip()


def fixture(area, source, code):
    """各欄の拒否を独立検査する合成fixture。実process値とは明記して区別する。"""
    root = str(g.ROOT)
    fixed = g.ROOT.parent / 'qa065-fixed059'
    value = dict(schema=3, fixture_only=True, source_sha=source, code_sha=g.FIXED059,
                 generation_code_sha=code, checkout=root, status='PASS', failures=[], setup=[], commands=[],
                 targets={label: g.FIXED059 if label == 'scope059' else source for label in g.SETUP + g.COMMANDS},
                 fixed_checkout_before=dict(sha=g.FIXED059, clean=True, scope_sha256=g.FIXED_SCOPE_SHA256),
                 fixed_checkout_after=dict(sha=g.FIXED059, clean=True, scope_sha256=g.FIXED_SCOPE_SHA256))
    scripts = ('test_capture057.py', 'scope059.py', 'test_capture059.py', 'reproduce058.py',
               'diagnostics057.py', 'generation_contract.py', 'test_generation_contract.py')
    for label in g.SETUP + g.COMMANDS:
        cwd = str(fixed) if label == 'scope059' else root
        argv = [sys.executable, str(Path(cwd) / g.FIXTURE / scripts[g.COMMANDS.index(label)])] if label in g.COMMANDS else ['git', 'fixture-only']
        if label == 'scope059':
            argv += ['--code-sha', g.FIXED059, '--source-sha', g.FIXED059]
        row = dict(argv=argv, planned_argv=argv, cwd=cwd, exit_code=0, terminal=True,
                   record_saved=True, timed_out=False, exception=None, supervision=dict(stopped=True),
                   wait=dict(ok=True), budget_seconds=g.BUDGETS[label], pid=1,
                   started_utc='fixture', ended_utc='fixture', started_monotonic=1,
                   ended_monotonic=2, seconds=1, log_sha256=g.digest(b'validator fixture\n'))
        (area / (label + '.log')).write_bytes(b'validator fixture\n')
        write(area / (label + '-process.json'), row)
        value['setup' if label in g.SETUP else 'commands'].append(dict(row, label=label))
    for label, cases in (('capture-tests', g.CASES057), ('capture059', g.CASES059)):
        write(area / label / 'tests.json', dict(status='PASS', cases=[dict(case=c, status='PASS') for c in cases]))
    scope = dict(base=g.BASE059, registration=g.REGISTER059, code_sha=g.FIXED059, source_sha=g.FIXED059,
                 propagation=[dict(case=c, exit_code=0 if i == 0 else 1, expected_exit=0 if i == 0 else 1)
                              for i, c in enumerate(g.SCOPE_CASES)])
    write(area / 'scope.json', scope)
    (area / 'scope059').mkdir()
    for name in g.SCOPE_CASES:
        (area / 'scope059' / (name + '.log')).write_bytes(b'validator fixture\n')
    write(area / 'measurements/diagnostics.json', dict(source_sha=source, status='PASS', failures=[],
          samples=[dict(seed=s, mode=m) for s in ('typed', 'plain', 'granted', 'trial-missing', 'trial-corrupt', 'trial-unclean') for m in ('off', 'on')]))
    write(area / 'generation.json', dict(source_sha=source, code_sha=code, fixed059_sha=g.FIXED059))
    write(area / 'generation-tests/tests.json', dict(status='PASS', cases=[dict(case=c, expected_exit=0, exit_code=0) for c in CASES]))
    write(area / 'execution.json', value)
    return value


def main(args):
    root = g.ROOT; code = args.code_sha or g.pin(root)
    source = g.git(root, 'rev-parse', 'HEAD').decode().strip()
    output = Path(args.output).resolve(); output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in CASES:
        area = output / name; area.mkdir()
        expected = 0 if name.endswith('control') or name == 'scope-submission-document' else 1
        if name.startswith('scope-'):
            target = code
            paths = {'outside': 'outside065.txt', 'production': 'scripts/game/equipment_save_transaction.gd',
                     'supervisor': g.FIXTURE + 'process_capture.py', 'old-assertion': g.FIXTURE + 'scope059.py',
                     'workflow': '.github/workflows/equipment-transaction-platform.yml', 'task-body': g.TASK,
                     'old-evidence': 'docs/verification/task059-save-qa-finalization/README.md',
                     'submission-document': g.EVIDENCE + 'README.md', 'submission-code': g.CODE[0]}
            if name != 'scope-control':
                target = commit_variant(root, code, area, paths[name[6:]], b'065 fixture\n')
            argv = [sys.executable, str(root / g.FIXTURE / 'generation_contract.py'), '--scope-only', '--code-sha',
                    code if name.startswith('scope-submission-') else target]
            if name.startswith('scope-submission-'):
                argv += ['--source-sha', target]
        elif name.startswith('map-'):
            value = g.load(root / g.EVIDENCE / 'assertion-map.json')
            if name == 'map-missing': value['old_assertions'].pop()
            if name == 'map-duplicate': value['old_assertions'].append(value['old_assertions'][0])
            if name == 'map-replaced': value['old_assertions'][0]['destination'] = 'latest/skip'
            write(area / 'map.json', value)
            argv = [sys.executable, __file__, '--probe', 'map', '--area', str(area)]
        else:
            value = fixture(area, source, code)
            row = value['commands'][0]
            if name.startswith('wrapper-'):
                row['argv'] = [sys.executable, str(root / g.FIXTURE / 'process_exec059.py'), *row['planned_argv']]
                row['supervision']['mechanism'] = 'Linux dedicated session'
                if name == 'wrapper-altered': row['argv'][1] = str(root / 'unknown-wrapper.py')
                write(area / 'capture-tests-process.json', {k: v for k, v in row.items() if k != 'label'})
            if name == 'collector-failure': row['exit_code'] = 3
            if name == 'evidence-generation': value['source_sha'] = g.FIXED059
            if name == 'evidence-fixed-sha': value['code_sha'] = source
            if name == 'evidence-code-sha': value['generation_code_sha'] = g.FIXED059
            if name == 'evidence-fixed-code':
                value['fixed_checkout_before']['scope_sha256'] = '0' * 64
                value['fixed_checkout_after']['scope_sha256'] = '0' * 64
            if name == 'evidence-missing-command': value['commands'].pop()
            if name == 'evidence-duplicate-command': value['commands'].append(row)
            if name == 'evidence-missing-setup': value['setup'].pop()
            if name == 'evidence-failed-exit': row['exit_code'] = 1
            if name == 'evidence-timeout': row['timed_out'] = True
            if name == 'evidence-unconfirmed': row['supervision']['stopped'] = False
            if name == 'evidence-budget': row['budget_seconds'] = 181
            if name == 'evidence-latest-cwd': row['cwd'] = str(root.parent / 'qa065-fixed059')
            if name == 'evidence-hidden-failure': value['failures'] = ['original failure']
            def edit(relative, mutate):
                path = area / relative; v = g.load(path); mutate(v); write(path, v)
            if name == 'evidence-missing-case': edit('capture059/tests.json', lambda v: v['cases'].pop())
            if name == 'evidence-replaced-case': edit('capture-tests/tests.json', lambda v: v['cases'][0].update(case='invented'))
            if name == 'evidence-missing-sample': edit('measurements/diagnostics.json', lambda v: v['samples'].pop())
            if name == 'evidence-fixed-ten': edit('scope.json', lambda v: v['propagation'].pop())
            if name == 'evidence-record-mismatch': edit('capture-tests-process.json', lambda v: v.update(pid=99))
            if name == 'evidence-missing-record': (area / 'capture-tests-process.json').rename(area / 'missing.saved')
            if name == 'evidence-rehashed-log': (area / 'capture-tests.log').write_bytes(b'altered\n')
            if name.startswith('legacy-'):
                value.update(schema=2); value['commands'] = value['commands'][:5]; value['setup'] = [value['setup'][1]]
                if name == 'legacy-missing-command': value['commands'].pop()
                if name == 'legacy-missing-setup': value['setup'] = []
                if name == 'legacy-failed-exit': value['commands'][0]['exit_code'] = 7
            write(area / 'execution.json', value)
            write(area / 'generation-manifest.json', g.snapshot(area, ('generation-manifest.json',)))
            if name == 'evidence-modified-log': (area / 'capture-tests.log').write_bytes(b'altered\n')
            argv = [sys.executable, __file__, '--probe', 'collect' if name.startswith(('legacy-', 'collector-')) else 'evidence',
                    '--area', str(area), '--code-sha', code, '--source-sha', source]
        start = time.monotonic()
        child = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        (area / 'probe-stdout.log').write_bytes(child.stdout); (area / 'probe-stderr.log').write_bytes(child.stderr)
        rows.append(dict(case=name, expected_exit=expected, exit_code=child.returncode,
                         argv=argv, seconds=time.monotonic() - start))
        write(output / 'tests.json', dict(status='PASS' if all(r['exit_code'] == r['expected_exit'] for r in rows) else 'FAIL',
              source_sha=source, code_sha=code, fixture_scope='合成証拠の拒否と実Git差分。実12/27/12sampleは別診断。', cases=rows))
    failures = [r['case'] for r in rows if r['exit_code'] != r['expected_exit']]
    print('GENERATION065_TESTS_' + ('FAIL' if failures else 'PASS') + ': cases=' + str(len(rows)) + ' failures=' + str(failures))
    return 1 if failures else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output'); parser.add_argument('--code-sha')
    parser.add_argument('--source-sha'); parser.add_argument('--probe'); parser.add_argument('--area')
    args = parser.parse_args()
    try:
        if args.probe == 'map': g.check_map(g.ROOT, g.load(Path(args.area) / 'map.json'))
        elif args.probe == 'evidence': g.validate_execution(Path(args.area), args.source_sha, args.code_sha)
        elif args.probe == 'collect':
            from diagnostic_evidence059 import collect
            result = collect(args.area, str(args.area) + '-collected', args.source_sha, g.FIXED059)
            g.require(result['status'] == 'PASS', '旧schema拒否:' + str(result['errors']))
        else: sys.exit(main(args))
    except Exception as exc:
        print('GENERATION065_TEST_FAIL: ' + type(exc).__name__ + ': ' + str(exc)); sys.exit(1)
