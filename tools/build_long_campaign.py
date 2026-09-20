"""手書きの連作台本を、再訪する区画と本番の進行データへコンパイルする。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGION_ENEMIES = {
    'waterway': [['slime', 'mire_slime'], ['bat', 'slime'], ['shell_guard'], ['balm_slime', 'slime'], ['frost_slime', 'bat'], ['elder_slime']],
    'cave': [['shell_guard', 'bat'], ['tide_shell'], ['ward_shell', 'bat'], ['spike_shell', 'slime'], ['rending_bat', 'shell_guard'], ['ancient_shell']],
    'school': [['ward_slime', 'bat'], ['rending_bat'], ['echo_bat', 'shell_guard'], ['vigilant_bat', 'slime'], ['frost_bat', 'ember_wisp'], ['night_bat']],
    'records': [['ember_wisp', 'bat'], ['racing_wisp'], ['cinder_wisp', 'slime'], ['lamp_wisp', 'shell_guard'], ['ash_wisp', 'bat'], ['core_wisp']],
    'gate': [['river_beast'], ['swift_beast', 'bat'], ['watch_beast'], ['mending_beast', 'slime'], ['river_beast', 'ember_wisp'], ['flood_beast']],
}
CHAPTERS = {19: 2, 23: 3, 28: 4, 34: 5, 38: 6}


def layout(index: int) -> list[str]:
    cells = [['#' if x in (0, 31) or y in (0, 17) else '.' for x in range(32)] for y in range(18)]
    # 同じ連作では同じ地形を再訪する。通路の開口はIDから決まり、再生成で変わらない。
    gaps = [2 + index % 13, 2 + (index // 13) % 13, 2 + (index * 5 + 3) % 13]
    for wall, gap in zip([7, 15, 23], gaps):
        for y in range(1, 17):
            if y not in (gap, gap + 1):
                cells[y][wall] = '#'
    for x, y in [(2, 4), (5, 4), (12, 6), (25, 10), (26, 14), (29, 14)]:
        cells[y][x] = '.'
    return [''.join(row) for row in cells]


def compile_catalog() -> dict:
    outline = json.loads((ROOT / 'docs/long-campaign-authoring.json').read_text(encoding='utf-8'))
    arcs, rooms, missions = [], [], []
    episodes = {}
    for arc_index, arc in enumerate(outline['arcs']):
        identifier, region = arc['id'], arc['region']
        room_ids = [f'journey_{identifier}_{suffix}' for suffix in 'abcd']
        for number, room_id in enumerate(room_ids):
            rooms.append({'id': room_id, 'location': region, 'title': f'{arc["title"]}・{number + 1}',
                          'spawn': [2, 4], 'layout': layout(arc_index * 4 + number)})
        source = ROOT / 'data/long_campaign/arcs' / (identifier + '.json')
        scripts = json.loads(source.read_text(encoding='utf-8'))['episodes'] if source.exists() else []
        arcs.append({'id': identifier, 'region': region, 'title': arc['title'], 'person': arc['person'],
                     'rooms': room_ids, 'missions': [f'{identifier}_{number + 1}' for number in range(4)],
                     'script_count': len(scripts)})
        for number, episode in enumerate(scripts):
            episodes[episode['id']] = episode
            assert episode['id'] == f'{identifier}_{number + 1}', '連作と話のIDが対応していません'
            assert len(episode['scenes']) == 4, '4つの訪問場面が必要です'
            assert all(len(scene) >= 2 and all(isinstance(line, str) and line for line in scene) for scene in episode['scenes'])
            assert len(episode['choice']['effects']) == len(episode['choice']['options'])
            affected_room = next(room for room in rooms if room['id'] == room_ids[number])
            door_y = next(y for y in [4,5,6,7,8,9,10,11,12,13,14,3,2,1,15,16] if affected_room['layout'][y][7] == '#')
            passage_flag = 'journey_passage_' + episode['id']
            affected_room.setdefault('passages', []).append({'cell': [7,door_y], 'flag': passage_flag})
            trigger = arc['trigger_step']
            chapter = CHAPTERS[trigger]
            steps = []
            battle_index = 0
            choice_id = episode['id'] + '_choice'
            for room_number, room_id in enumerate(room_ids):
                lines = episode['scenes'][room_number]
                split = (len(lines) + 1) // 2
                is_past = room_number in episode.get('past_scene_indices', [])
                prefix = episode['id'] + '_' + str(room_number)

                def step(kind, cell, **extra):
                    return {'id': prefix + '_' + str(len(steps)) + '_' + kind, 'kind': kind,
                            'location': region, 'section': room_id, 'chapter': chapter, 'cell': cell, **extra}

                start = step('dialogue', [5, 4], objective=episode['title'] + 'の話を聞く',
                             text=['奥の足場を確かめ、落ち着いて話を聞ける場所へ進もう。'] if is_past else lines[:split],
                             rest=True, past=False)
                if room_number == 3:
                    start['responses'] = [{'choice': choice_id, 'variants': episode['choice']['outcomes']}]
                steps.append(start)
                for wave_in_room in range(2 if room_number < 2 else 1):
                    roster = REGION_ENEMIES[region][(battle_index + number) % 6]
                    steps.append(step('battle', [12, 6] if wave_in_room == 0 else [26, 14],
                                      objective=episode['title'] + 'の通り道を確保する', enemies=roster,
                                      seed=710000 + arc_index * 10000 + number * 1000 + battle_index,
                                      text=['通り道を確保した。残りの力を確かめて、話の続きを追おう。']))
                    battle_index += 1
                steps.append(step('dialogue', [25, 10], objective=episode['title'] + 'の状況を調べる',
                                  text=lines if is_past else lines[split:], past=is_past))
                if room_number == 2:
                    choice = episode['choice']
                    effects = [{'flags': [passage_flag] if effect.get('passage') else [],
                                'potion_bonus': effect.get('potion_bonus', 0)} for effect in choice['effects']]
                    options = [label + ('（近道を残す）' if effect.get('passage') else '（補給を多く残す）')
                               for label, effect in zip(choice['options'], choice['effects'])]
                    entry = step('challenge', [26, 14], objective=episode['title'] + 'で引き受けることを選ぶ',
                                 choice=True, question=choice['question'], options=options, choice_effects=effects, answer=0,
                                 record='\n'.join(episode['scenes'][room_number]),
                                 resolution='選んだことを伝えた。この結果は次の場面で確かめられる。',
                                 reward_potions=1, reward_hp_percent=50, reward_mp_percent=50)
                    entry['id'] = choice_id
                    steps.append(entry)
                if room_number < 3:
                    steps.append(step('section_travel', [29, 14], objective='次の場所へ進む',
                                      destination=room_ids[room_number + 1], spawn=[2, 4]))
                else:
                    steps.append(step('circuit_complete', [29, 14], objective='今回の結果を持ち帰る'))
            missions.append({'id': episode['id'], 'arc': identifier, 'title': episode['title'],
                             'region': region, 'chapter': chapter, 'trigger_step': trigger,
                             'requires': [] if number == 0 else [f'{identifier}_{number}'],
                             'sections': [room for room in rooms if room['id'] in room_ids],
                             'steps': steps, 'followup': episode['followup']})
    mission_lookup = {entry['id']: entry for entry in missions}
    clue_source = ROOT / 'data/long_campaign/clues.json'
    clues = json.loads(clue_source.read_text(encoding='utf-8'))['clues'] if clue_source.exists() else []
    for clue in clues:
        for field in ('setup', 'payoff'):
            reference = clue[field]
            episode = episodes[reference['mission']]
            text = episode['scenes'][reference['scene']][reference['line']]
            mission = mission_lookup[reference['mission']]
            section = mission['sections'][reference['scene']]['id']
            matches = [step for step in mission['steps'] if step['section'] == section and text in step.get('text', [])]
            assert len(matches) == 1, f'{clue["id"]}: 設置・回収の本文が一つの提示地点に対応していません'
            clue[field] = {**reference, 'step': matches[0]['id'], 'text': text}
    complete = len(missions) == 80 and all(arc['script_count'] == 4 for arc in arcs)
    complete = complete and all(sum(clue['arc'] == arc['id'] for clue in clues) >= 2 for arc in arcs)
    return {'version': 1, 'enabled': complete, 'design_status': '設計者の提案。全台本と進行の接続・検査が終わるまで人間試遊可能と扱わない。',
            'arcs': arcs, 'rooms': rooms, 'missions': missions, 'clues': clues}


def main() -> None:
    document = compile_catalog()
    destination = ROOT / 'data/long_campaign_v1.json'
    destination.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_ledger(document)
    print(f'LONG_BUILD: scripts={len(document["missions"])} / 80, rooms={len(document["rooms"])}, enabled={document["enabled"]}')


def write_ledger(document: dict) -> None:
    """制作用の台帳を本番データと同じ参照から出力する。ゲーム内には未読の解答を出さない。"""
    missions = {entry['id']: entry for entry in document['missions']}
    rows = [
        '# 長編の回収台帳（制作資料・物語の内容あり）', '',
        f'設計者の提案。制作済み{sum(arc["script_count"] > 0 for arc in document["arcs"])}連作の台帳であり、全80話の完成を示さない。既存R01〜R08の台帳は維持する。', '',
        '`tools/build_long_campaign.py` が `data/long_campaign/clues.json` の参照を本番の会話地点へ解決して生成する。'
        '未読の記録は手帳へ出さず、設置後は最初の見立てだけ、回収後は新しい意味と次の問いを表示する。', '',
        '既読は、該当話の `journey_<話ID>_cleared`、または同じ話の `expedition.stage` が提示地点を越えたことから導く。'
        '回収には設置済みと依存IDの回収済みも必要。追加の既読フラグは保存せず、帰還中も保持される既存の進行状態を使う。', '',
        '| ID | 設置箇所（章・場所・形式） | 最初の意味 | 回収箇所 | 回収後の意味 | 必要フラグ | 見逃した場合の挙動 | 実装コスト | 依存ID |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    def place(point: dict) -> str:
        mission = missions[point['mission']]
        return f'第{mission["chapter"]}章／{mission["region"]}／`{point["mission"]}` 場面{point["scene"]+1}段落{point["line"]+1}（必須会話）'
    for clue in document['clues']:
        rows.append('| ' + ' | '.join([
            clue['id'], place(clue['setup']), clue['first'], place(clue['payoff']), clue['resolved'],
            '上記の保存済み進行から導出', '未読は未公開。必須会話を閉じると更新し、手帳で既出情報を再読できる',
            '小（共通の進行・手帳表示を使用）', '、'.join(clue['requires']) or 'なし',
        ]) + ' |')
    rows += ['', '## 機械検査', '',
             '`godot --headless --path . --script res://tools/check_long_clues.gd` で、各IDの設置と回収、本文の存在、提示順、依存の先行回収、循環の不在、既読直前・直後の公開範囲を検査する。', '',
             '`tools/check_long_ui.gd` は3人／4人で回収前後の手帳を開き、512×288内の表示と戻る操作を検査する。'
             '`tools/check_long_integration.gd` は進行地点ごとの保存復帰で手帳内容も一致することを検査する。', '',
             '受け手が意味の変化に気づくか、次の問いを持つかは未検証。PLAYTEST_QUEUE.md の主観観測と分離する。', '']
    (ROOT / 'docs/long-campaign-clue-ledger.md').write_text('\n'.join(rows), encoding='utf-8')


if __name__ == '__main__':
    main()
