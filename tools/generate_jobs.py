#!/usr/bin/env python3
"""v1の20職と戦闘定義を出力する。数値と未指定の職業名は調整案。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAT_NAMES = ('hp', 'mp', 'attack', 'defense', 'magic', 'resistance', 'speed')


def stats(values: tuple[int, ...]) -> dict[str, int]:
    return dict(zip(STAT_NAMES, values))


def ability(identifier, name, kind, power, cost, *, target='enemy', hits=1, priority=0, element='none'):
    return {'id': identifier, 'name': name, 'kind': kind, 'power': power, 'cost': cost,
            'target': target, 'hits': hits, 'priority': priority, 'element': element,
            'description': f'{name} / MP {cost} / {kind}'}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    humans = [
        ('warrior', '戦士', (140, 24, 20, 14, 5, 8, 8), ['power_strike', 'firm_guard']),
        ('martial_artist', '武闘家', (125, 24, 23, 8, 6, 7, 15), ['double_strike', 'breath']),
        ('priest', '僧侶', (105, 40, 10, 9, 18, 16, 10), ['heal', 'revive']),
        ('mage', '魔法使い', (90, 44, 8, 6, 24, 15, 11), ['fire', 'ice']),
        ('thief', '盗賊', (110, 26, 16, 9, 8, 8, 21), ['steal', 'quick_slash']),
        ('hunter', '狩人', (115, 28, 19, 9, 9, 9, 17), ['quick_shot', 'ice_arrow']),
        ('apothecary', '薬師', (115, 38, 11, 11, 15, 13, 12), ['salve', 'breath']),
        ('bard', '吟遊詩人', (100, 42, 9, 8, 19, 16, 16), ['sound_wave', 'soothing_song']),
        ('knight', '騎士', (160, 22, 18, 20, 8, 12, 5), ['shield_strike', 'firm_guard']),
        ('sage', '賢者', (95, 50, 8, 8, 23, 20, 7), ['holy_light', 'heal']),
        ('swordsman', '剣士', (125, 30, 21, 12, 8, 10, 16), ['double_strike', 'quick_slash']),
        ('shaman', '祈祷師', (110, 44, 10, 10, 21, 18, 9), ['curse_bolt', 'revive']),
    ]
    monsters = [
        ('slime', 'スライム系', (130, 30, 14, 18, 14, 11, 5), ['acid', 'slime_mend'], {'hp': 24, 'defense': 8}, 'magic', 'ice'),
        ('beast', '獣系', (145, 22, 25, 10, 5, 8, 19), ['fang', 'breath'], {'attack': 10, 'speed': 5}, 'physical', 'none'),
        ('undead', '不死系', (135, 40, 17, 13, 20, 17, 7), ['grave_bolt', 'undead_mend'], {'hp': 20, 'magic': 8}, 'magic', 'none'),
        ('bird', '鳥系', (105, 30, 17, 8, 15, 9, 25), ['wind_blade', 'quick_slash'], {'speed': 10, 'attack': 5}, 'physical', 'none'),
        ('plant', '植物系', (150, 38, 15, 16, 17, 15, 4), ['thorn', 'root_mend'], {'hp': 30, 'resistance': 8}, 'magic', 'none'),
        ('shell', '甲殻系', (165, 20, 18, 24, 7, 10, 3), ['shell_bash', 'firm_guard'], {'defense': 14, 'hp': 20}, 'physical', 'none'),
        ('spirit', '精霊系', (95, 52, 8, 8, 26, 24, 15), ['spirit_bolt', 'heal'], {'magic': 10, 'resistance': 10}, 'magic', 'ice'),
        ('dragon', '竜系', (170, 36, 25, 19, 18, 18, 10), ['flame_breath', 'power_strike'], {'attack': 8, 'magic': 8}, 'magic', 'fire'),
    ]
    abilities = [
        ability('power_strike', '強打', 'physical', 150, 3),
        ability('firm_guard', '堅守', 'guard', 25, 3, target='self'),
        ability('double_strike', '連撃', 'physical', 80, 5, hits=2),
        ability('breath', '息を整える', 'heal', 12, 2, target='self'),
        ability('heal', '治癒', 'heal', 24, 4, target='ally'),
        ability('revive', '蘇生', 'revive', 25, 8, target='fallen_ally'),
        ability('fire', '火球', 'magic', 24, 4, element='fire'),
        ability('ice', '氷弾', 'magic', 18, 3, element='ice'),
        ability('steal', '盗む', 'steal', 0, 0),
        ability('quick_slash', '先制斬り', 'physical', 80, 3, priority=1),
        ability('quick_shot', '速射', 'physical', 95, 3, priority=1),
        ability('ice_arrow', '氷矢', 'magic', 22, 4, element='ice'),
        ability('salve', '癒しの調合', 'heal', 38, 5, target='ally'),
        ability('sound_wave', '響きの波', 'magic', 26, 4),
        ability('soothing_song', '安らぎの歌', 'heal', 28, 4, target='ally'),
        ability('shield_strike', '盾打ち', 'physical', 140, 3),
        ability('holy_light', '光輪', 'magic', 34, 6),
        ability('curse_bolt', '呪弾', 'magic', 30, 5),
        ability('acid', '酸液', 'magic', 20, 3),
        ability('slime_mend', '再生', 'heal', 24, 3, target='self'),
        ability('fang', '牙', 'physical', 145, 3),
        ability('grave_bolt', '冥火', 'magic', 30, 5),
        ability('undead_mend', '死気回復', 'heal', 20, 3, target='self'),
        ability('wind_blade', '風刃', 'magic', 23, 3),
        ability('thorn', '棘打ち', 'physical', 135, 3),
        ability('root_mend', '根の再生', 'heal', 35, 4, target='self'),
        ability('shell_bash', '殻打ち', 'physical', 145, 4),
        ability('spirit_bolt', '霊光', 'magic', 30, 4),
        ability('flame_breath', '炎の息', 'magic', 34, 6, element='fire'),
    ]
    for index, (identifier, name, values, skills) in enumerate(humans, 1):
        definition = {'id': identifier, 'name': name, 'type': 'human', 'category': 'human', 'playable': True,
                      'stat_growth': {'hp': 2, 'attack': 1, 'magic': 1}, 'abilities': skills,
                      'mastery_cost': 24 + (index - 1) * 4, 'stats': stats(values),
                      'design_status': '未指定の名称・数値は調整案'}
        write_json(ROOT / 'data/jobs' / f'{index:02d}_{identifier}.json', definition)
    for index, (identifier, name, values, skills, modifiers, kind, element) in enumerate(monsters, 13):
        form_skill = 'form_' + identifier
        abilities.append(ability(form_skill, name.replace('系', '') + 'の奥義', kind, 175 if kind == 'physical' else 42, 7, element=element))
        definition = {'id': identifier, 'name': name, 'type': 'monster', 'category': 'monster', 'playable': True,
                      'stat_growth': {'hp': 3, 'defense': 1, 'resistance': 1}, 'abilities': skills,
                      'mastery_cost': 32 + (index - 13) * 4, 'stats': stats(values),
                      'monster_form': {'stat_modifiers': modifiers, 'abilities': [form_skill],
                                       'release': {'event': 'purification_shrine', 'max_erosion': 89, 'erosion_reduction': 30, 'forget_monster_abilities': True}},
                      'design_status': '未指定の名称・数値は調整案。魔物化はマスター時。解除は祠、侵蝕90未満、魔物技全消去。'}
        write_json(ROOT / 'data/jobs' / f'{index:02d}_{identifier}.json', definition)
    enemies = [
        {'id':'slime', 'name':'水路スライム', 'stats':stats((60,0,10,6,0,5,5)), 'abilities':[], 'weaknesses':['fire'], 'jp':10},
        {'id':'bat', 'name':'洞窟コウモリ', 'stats':stats((75,0,13,4,0,8,21)), 'abilities':[], 'weaknesses':['ice'], 'jp':12},
        {'id':'shell_guard', 'name':'硬殻の番兵', 'stats':stats((150,0,18,28,0,4,4)), 'abilities':[], 'weaknesses':['ice'], 'jp':16},
        {'id':'ember_wisp', 'name':'残り火の精', 'stats':stats((110,16,8,7,16,20,12)), 'abilities':['fire'], 'weaknesses':['ice'], 'jp':16},
        {'id':'gate_beast', 'name':'水門の荒獣', 'stats':stats((320,0,30,16,0,12,13)), 'abilities':[], 'weaknesses':[], 'jp':24},
    ]
    write_json(ROOT / 'data/catalog.json', {
        'schema_version': 1, 'jobs_directory': 'res://data/jobs', 'abilities': abilities, 'enemies': enemies,
        'encounters': [{'id':'waterway', 'name':'水路', 'enemies':['slime','bat']},
                       {'id':'cave', 'name':'地下通路', 'enemies':['shell_guard','ember_wisp']},
                       {'id':'gate', 'name':'水門', 'enemies':['gate_beast']}],
        'design_status':'v1用の調整値。ゲーム全体の所要時間や最終バランスを検証済みとはしない。',
    })
    print('人間職12、モンスター職8、技%d、敵5のデータを生成しました。' % len(abilities))


if __name__ == '__main__':
    main()
