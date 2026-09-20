"""長編未完成の記録を集計側も拒否する。入力は合成値で、人間の実測ではない。"""
import copy
import json
from pathlib import Path
from build_identity import identity, EXPECTED_ENGINE
from summarize_playtest import summarize

ROOT = Path(__file__).resolve().parent.parent


def main():
    target = json.loads((ROOT / 'data/duration_target_v1.json').read_text(encoding='utf-8'))
    build = identity(EXPECTED_ENGINE)
    record = {
        'source': 'human', 'source_changed': False, 'completed': True,
        'measurement_scope': 'whole_trial', 'history_complete': True,
        'builds': [build['id']], 'duration_target': target,
        'active_ms': 3600 * 60000, 'idle_ms': 0, 'pause_ms': 0, 'elapsed_ms': 3600 * 60000,
        'answers': [{'note': '合成境界検査。人間の試遊ではない。'}],
        'game': {'engine': EXPECTED_ENGINE, 'build_id': build['id'],
                 'build_identity_version': 1, 'content_revision': 1, 'mixed_builds': False,
                 'duration_target_id': target['id'], 'long_campaign_complete': False,
                 'circuits_completed': ['waterway', 'cave', 'school', 'records', 'gate']},
    }
    failures = []
    for required in (True, False, None):
        sample = copy.deepcopy(record)
        if required is not None:
            sample['game']['long_campaign_required'] = required
        result = summarize(sample)
        if result['duration_candidate'] or result['status'] != 'NOT_ACCEPTED':
            failures.append(f'未完走を拒否する: required={required}')
    record['game']['long_campaign_required'] = True
    record['game']['long_campaign_complete'] = True
    result = summarize(record)
    if not result['duration_candidate'] or result['status'] != 'REQUIRES_HUMAN_REVIEW':
        failures.append('完走という合成前提の境界値は、人間レビュー前の候補として扱う')
    record['game']['long_campaign_complete'] = 1
    if summarize(record)['duration_candidate']:
        failures.append('真偽値でない長編完了を拒否する')
    record['game']['long_campaign_complete'] = True
    base_circuits = record['game']['circuits_completed']
    for malformed in (base_circuits + ['waterway'], {key: True for key in base_circuits}, ['waterway'] * 5):
        record['game']['circuits_completed'] = malformed
        if summarize(record)['duration_candidate']:
            failures.append('5つの異なる地点を配列で記録していないものを拒否する')
    record['game']['circuits_completed'] = base_circuits
    record['completed'] = 1
    if summarize(record)['duration_candidate']:
        failures.append('真偽値でない本編完了を拒否する')
    for failure in failures:
        print('LONG_RECORD_SUMMARY_FAIL: ' + failure)
    if not failures:
        print('LONG_RECORD_SUMMARY_PASS: 必須欄の有無にかかわらず未完走を拒否。合成入力のみ。')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
