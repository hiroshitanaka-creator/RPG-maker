"""045専用CI artifactの原ZIP digest・全member・全原結果・比較を再確認する。"""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('equipment_ci', ROOT / 'tools/run_equipment_ci.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sha', required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    expected_names = {f'equipment-core-{p}' for p in ['036', '038', '041', 'latest']}
    expected_names |= {f'equipment-invalid-{p}' for p in ['038', '041', 'latest']}
    expected_names |= {f'equipment-migration-{p}' for p in ['041', 'latest']}
    expected_names |= {f'equipment-legacy-{p}' for p in ['baseline', '041', 'latest']}
    expected_names |= {'equipment-legacy-comparison', 'equipment-failure-propagation'}
    artifacts = m.read_json(args.inputs / 'artifacts.json')
    assert len(artifacts) == 14 and {a['name'] for a in artifacts} == expected_names
    results = []
    for meta in artifacts:
        name = meta['name']
        path = args.inputs / (name + '.zip')
        raw = path.read_bytes() if path.exists() else gzip.decompress(path.with_suffix('.zip.gz').read_bytes())
        assert m.sha256(raw) == meta['digest'].removeprefix('sha256:')
        assert meta['workflow_run']['head_sha'] == args.sha and not meta['expired']
        z = zipfile.ZipFile(io.BytesIO(raw))
        assert z.testzip() is None and len(set(z.namelist())) == len(z.namelist())
        manifest = json.loads(z.read('sha256.json'))
        members = {n for n in z.namelist() if not n.endswith('/') and Path(n).name != 'sha256.json'}
        assert set(manifest) == members
        for member in members:
            assert m.sha256(z.read(member)) == manifest[member], (name, member)
        folder = args.output / name
        z.extractall(folder)
        execution = m.read_json(folder / 'execution.json')
        assert execution['status'] == 'PASS' and execution['latest_sha'] == args.sha
        assert execution['wrapper_sha256'] == m.sha256(m.blob(args.sha, 'tools/run_equipment_ci.py'))
        profile = execution['profile']
        assert execution['source_sha'] == (args.sha if profile == 'latest' else m.FIXED[profile])
        for command in execution['commands']:
            assert command['exit_code'] == 0 and command['timed_out'] is False and command['bad_lines'] == []
            assert command['seconds'] >= 0
            if command['timeout_seconds'] is not None:
                assert command['seconds'] <= command['timeout_seconds']
            log = (folder / command['log']).read_bytes()
            assert m.sha256(log) == command['log_sha256'] and not m.BAD_LOG.search(log.decode())
        suite = execution['suite']
        if suite in ['core', 'invalid', 'migration', 'legacy']:
            assert execution['engine'] == m.VERSION and execution['engine_sha256'] == m.ENGINE_SHA256
            assert (folder / 'frozen-before.log').read_text().strip() == '保護対象26件、一致26件。'
            assert (folder / 'frozen-after.log').read_text().strip() == '保護対象26件、一致26件。'
        if suite == 'core':
            m.check_core(m.read_json(folder / 'core.json'), profile == '036')
        if suite == 'invalid':
            m.check_invalid(m.read_json(folder / 'invalid/results.json'), execution['source_sha'], folder / 'invalid', m.frozen_invalid())
        if suite == 'migration':
            reference = json.loads(m.blob(m.MIGRATION_EVIDENCE, 'docs/verification/equipment-save-migration/migration.json'))
            m.check_migration(m.read_json(folder / 'migration.json'), execution['source_sha'], reference)
        if suite == 'legacy':
            m.check_legacy(m.read_json(folder / 'legacy.json'))
        if suite == 'self-test':
            cases = m.read_json(folder / 'failure-propagation.json')['cases']
            assert len(cases) == len({c['case'] for c in cases}) == 77
            assert sum(c['expected_exit'] == 0 for c in cases) == 6
            assert all(c['expected_exit'] == c['observed_exit'] for c in cases)
        results.append({'name': name, 'artifact_id': meta['id'], 'zip_sha256': m.sha256(raw),
                        'member_count': len(z.namelist()), 'source_sha': execution['source_sha'],
                        'member_sha256': {n: m.sha256(z.read(n)) for n in z.namelist()},
                        'status': 'PASS', 'commands': execution['commands']})
    comparison = args.output / 'comparison-reexecuted'
    comparison.mkdir()
    m.compare_legacy(args.output, comparison, args.sha)
    assert m.read_json(comparison / 'comparison.json') == m.read_json(args.output / 'equipment-legacy-comparison/comparison.json')
    m.write_json(args.output / 'verification.json', {'code_sha': args.sha, 'status': 'PASS', 'artifacts': results})
    print('全14ZIP digest/全member hash/原結果/比較再実行PASS; members=', sum(r['member_count'] for r in results))


if __name__ == '__main__':
    main()
