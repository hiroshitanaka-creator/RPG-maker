"""合成境界値で60時間集計を検査する。人間の完走記録は作らない。"""
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
        'active_ms': 0, 'idle_ms': 0, 'pause_ms': 0, 'elapsed_ms': 0,
        'answers': [{'note': '合成境界検査。人間の試遊ではない。'}],
        'game': {'engine': EXPECTED_ENGINE, 'build_id': build['id'],
                 'build_identity_version': 1, 'content_revision': 1, 'mixed_builds': False,
                 'duration_target_id': target['id'],
                 'circuits_completed': ['waterway', 'cave', 'school', 'records', 'gate']},
    }
    for minutes in [330, 3239, 3240, 3600, 3960, 3961]:
        record['active_ms'] = record['elapsed_ms'] = minutes * 60000
        report = summarize(record)
        assert report['duration_candidate'] == (3240 <= minutes <= 3960), minutes
        assert report['status'] == 'REQUIRES_HUMAN_REVIEW'
    record['active_ms'] = record['elapsed_ms'] = 3600 * 60000
    record['source'] = 'automated'
    assert not summarize(record)['duration_candidate']
    record['source'] = 'human'
    record['game'].pop('duration_target_id')
    assert not summarize(record)['duration_candidate']
    assert summarize(record)['status'] == 'NOT_ACCEPTED'
    print('DURATION_SUMMARY_PASS: 旧330分の非受入、60時間の境界、旧目標と自動操作の除外。合成入力のみ。')

if __name__ == '__main__':
    main()
