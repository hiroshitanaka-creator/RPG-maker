"""045: 固定043実artifactを別コピーで改変し、044全反例と境界を再現する。"""
import argparse
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
SHA = 'f8ae80b34589f2c0f2c3b5ef3b6d9ddd2e86c94a'
NAMES = ['baseline', '041', 'latest']
CASES = ['control', 'missing_artifact', 'wrong_source', 'stale_artifact',
         'failed_log', 'duplicate_command', 'no_original_command', 'no_pass_line',
         'timeout_record', 'missing_commands', 'empty_fixture_hashes', 'fake_success_json',
         'command_lookalike', 'wrong_checkout', 'wrong_cwd', 'wrong_budget', 'over_budget',
         'nonfinite_seconds', 'bool_exit', 'bool_budget', 'false_engine', 'wrong_wrapper',
         'missing_source_hash', 'duplicate_pass', 'version_no_pass', 'protection_no_pass',
         'import_no_completion', 'fixture_wrong_hash', 'fixture_missing', 'output_missing_valid',
         'output_wrong_case', 'output_duplicate_case', 'output_missing_metrics',
         'output_missing_history', 'output_missing_types', 'output_wrong_value',
         'output_wrong_type', 'output_wrong_valid', 'output_failed', 'missing_manifest_log',
         'wrong_manifest_log', 'wrong_output_hash']


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def mutate(name, inputs):
    latest = inputs / 'equipment-legacy-latest'
    ep = latest / 'execution.json'
    e = json.loads(ep.read_text())
    c = e['commands'][3]
    if name == 'missing_artifact':
        shutil.rmtree(latest)
        return
    if name == 'wrong_source': e['source_sha'] = '0' * 40
    if name == 'stale_artifact': e['latest_sha'] = '0' * 40
    if name == 'duplicate_command': e['commands'] = [copy.deepcopy(e['commands'][0]) for _ in range(5)]
    if name == 'no_original_command': c['command'] = ['true']
    if name == 'missing_commands': e['commands'] = []
    if name == 'timeout_record': c['timed_out'] = True
    if name == 'command_lookalike': c['command'] = ['true', *c['command'][1:]]
    if name == 'wrong_checkout': c['command'][3] = '/tmp/other/checkout'
    if name == 'wrong_cwd': c['cwd'] = '/tmp/other/checkout'
    if name == 'wrong_budget': c['timeout_seconds'] = 121
    if name == 'over_budget': c['seconds'] = 121
    if name == 'nonfinite_seconds': c['seconds'] = float('nan')
    if name == 'bool_exit': c['exit_code'] = False
    if name == 'bool_budget': c['timeout_seconds'] = True
    if name == 'false_engine': e['engine_sha256'] = '0' * 64
    if name == 'wrong_wrapper': e['wrapper_sha256'] = '0' * 64
    if name == 'missing_source_hash': e['source_sha256'] = {}
    logs = {'failed_log': 'ERROR: independent fixture\n', 'no_pass_line': 'original check not executed\n',
            'duplicate_pass': 'LEGACY_EQUIVALENCE_PASS: validation=142 upgrade=10 failures=0\n' * 2,
            'version_no_pass': 'not executed\n', 'protection_no_pass': 'not executed\n',
            'import_no_completion': 'not executed\n'}
    if name in logs:
        idx = {'version_no_pass': 0, 'protection_no_pass': 1, 'import_no_completion': 2}.get(name, 3)
        log_cmd = e['commands'][idx]
        path = latest / log_cmd['log']
        path.write_text(logs[name])
        log_cmd['log_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    save(ep, e)
    # manifestも更新し、整合するhashだけで改変を受理しないことを示す。
    if name in logs:
        man = json.loads((latest / 'sha256.json').read_text())
        man[log_cmd['log']] = log_cmd['log_sha256']
        man['execution.json'] = hashlib.sha256(ep.read_bytes()).hexdigest()
        save(latest / 'sha256.json', man)
    if name in ['empty_fixture_hashes', 'fixture_wrong_hash', 'fixture_missing']:
        for profile in NAMES:
            path = inputs / ('equipment-legacy-' + profile) / 'execution.json'
            v = json.loads(path.read_text())
            if name == 'empty_fixture_hashes': v['fixture_sha256'] = {}
            if name == 'fixture_wrong_hash': v['fixture_sha256'][next(iter(v['fixture_sha256']))] = '0' * 64
            if name == 'fixture_missing': v['fixture_sha256'].pop(next(iter(v['fixture_sha256'])))
            save(path, v)
    if name == 'fake_success_json' or name.startswith('output_'):
        for profile in NAMES:
            folder = inputs / ('equipment-legacy-' + profile)
            v = json.loads((folder / 'legacy.json').read_text())
            if name == 'fake_success_json':
                v = {'validation_count': 142, 'upgrade_count': 10, 'failures': [],
                     'validation': [{'case': str(i), 'unchanged': True} for i in range(142)],
                     'upgrades': [{'case': str(i), 'imported': True, 'saved': True, 'loaded': True,
                                   'roundtrip': True} for i in range(10)]}
            if name == 'output_missing_valid': v['validation'][0].pop('valid')
            if name == 'output_wrong_case': v['validation'][0]['case'] = 'fake-case'
            if name == 'output_duplicate_case': v['validation'][1]['case'] = v['validation'][0]['case']
            if name == 'output_missing_metrics': v['upgrades'][0].pop('metrics_after')
            if name == 'output_missing_history': v['upgrades'][0]['metrics_after'].pop('events')
            if name == 'output_missing_types': v['upgrades'][0].pop('after_types')
            if name == 'output_wrong_value': v['upgrades'][0]['after']['party'][0]['hp'] += 1
            if name == 'output_wrong_type': v['upgrades'][0]['after']['party'][0]['hp'] = float(v['upgrades'][0]['after']['party'][0]['hp'])
            if name == 'output_wrong_valid': v['validation'][0]['valid'] = False
            if name == 'output_failed': v['failures'] = ['fixture']
            save(folder / 'legacy.json', v)
            man = json.loads((folder / 'sha256.json').read_text())
            man['legacy.json'] = hashlib.sha256((folder / 'legacy.json').read_bytes()).hexdigest()
            save(folder / 'sha256.json', man)
    if name in ['missing_manifest_log', 'wrong_manifest_log', 'wrong_output_hash']:
        path = latest / 'sha256.json'
        v = json.loads(path.read_text())
        if name == 'missing_manifest_log': v.pop('legacy.log')
        if name == 'wrong_manifest_log': v['legacy.log'] = '0' * 64
        if name == 'wrong_output_hash': v['legacy.json'] = '0' * 64
        save(path, v)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', type=Path, default=ROOT / 'tools/run_equipment_ci.py')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-rejection', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = args.output / 'original'
    source.mkdir()
    zip_hashes = {}
    for profile in NAMES:
        archive = ROOT / f'docs/verification/equipment-ci/ci-code/equipment-legacy-{profile}.zip.gz'
        raw = gzip.decompress(archive.read_bytes())
        zip_hashes[profile] = hashlib.sha256(raw).hexdigest()
        zipfile.ZipFile(io.BytesIO(raw)).extractall(source / ('equipment-legacy-' + profile))
    outcomes = []
    for name in CASES:
        folder = args.output / name
        inputs = folder / 'inputs'
        shutil.copytree(source, inputs)
        out = folder / 'out'
        out.mkdir()
        mutate(name, inputs)
        code = (f'import importlib.util,pathlib;s=importlib.util.spec_from_file_location("m",{str(args.module.resolve())!r});'
                f'm=importlib.util.module_from_spec(s);s.loader.exec_module(m);'
                f'm.compare_legacy(pathlib.Path({str(inputs.resolve())!r}),pathlib.Path({str(out.resolve())!r}),{SHA!r})')
        with (folder / 'result.log').open('w') as log:
            result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=10)
        outcomes.append({'case': name, 'expected_exit': 0 if name == 'control' else 1, 'observed_exit': result.returncode})
        print(name, result.returncode)
    save(args.output / 'results.json', {'module_sha256': hashlib.sha256(args.module.read_bytes()).hexdigest(),
         'artifact_sha': SHA, 'original_zip_sha256': zip_hashes, 'cases': outcomes})
    if args.require_rejection:
        assert all(v['expected_exit'] == v['observed_exit'] for v in outcomes), '不正artifactを受理'


if __name__ == '__main__':
    main()
