#!/usr/bin/env python3
"""元006の全check呼出し・Python判定を固定ソースから列挙し、対応表の欠落を拒否する。"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

from check_task009_scope import FIXED, ROOT, git

OUT = ROOT / 'docs/verification/task-009'
SOURCES = ['tools/check_region2_village_connections.gd', 'tools/capture_region2_village_connections.gd',
           'tools/check_region2_village_connections.py']
REPLACED = ['村NPC・施設・物語イベント0', '調べても回復・取引・装備・祠・解放・付与なし',
            '村の祠を解除施設にしない', '調べる操作で機能を発火しない']


def gd_calls(source: str) -> list[dict]:
    rows = []
    for match in re.finditer(r'(?<![\w.])(check|castle_check)\(', source):
        prefix = source[source.rfind('\n', 0, match.start()) + 1:match.start()]
        if prefix.lstrip().startswith('func '):
            continue
        depth, quote, escape, end = 1, '', False, match.end()
        while depth and end < len(source):
            char = source[end]
            if quote:
                if escape:escape = False
                elif char == '\\':escape = True
                elif char == quote:quote = ''
            elif char in ('"', "'"):quote = char
            elif char == '(':depth += 1
            elif char == ')':depth -= 1
            end += 1
        if depth:raise ValueError('閉じていないassertion')
        funcs = list(re.finditer(r'^func (\w+)\(', source[:match.start()], re.M))
        rows.append({'line': source.count('\n', 0, match.start()) + 1,
                     'function': funcs[-1].group(1), 'condition': source[match.start():end]})
    return rows


def inventory() -> list[dict]:
    rows = []
    for path in SOURCES:
        source = git('show', FIXED + ':' + path).decode()
        if path.endswith('.gd'):
            calls = gd_calls(source)
            for call in calls:
                replaced = any(message in call['condition'] for message in REPLACED)
                latest_path = ('tools/check_region2_village_regression.gd' if path.endswith('check_region2_village_connections.gd')
                               else 'tools/capture_task009_village_regression.gd')
                function = 'nonconnecting_doors' if call['function'] == 'interactions' else call['function']
                category = '007の承認済み新機能で置き換える現在条件' if replaced else '最新でも継続'
                latest = '007引継ぎ表 S01〜S06（未着手・未検証）' if replaced else latest_path + '::' + function
                if '調べても回復' in call['condition']:
                    latest += '。非接続4扉はnonconnecting_doorsで現在も全方向無反応を検査'
                rows.append({'source': path, **call, 'category': category, 'fixed': FIXED + ':' + path + ':' + str(call['line']), 'latest': latest})
        else:
            module = ast.parse(source)
            for function in [n for n in module.body if isinstance(n, ast.FunctionDef)]:
                # 判定に関わるifと判定値・返却値を全列挙。単なるCLI引数分岐も明示する。
                for node in ast.walk(function):
                    if not isinstance(node, (ast.If, ast.Return, ast.Assert, ast.Assign)):
                        continue
                    if isinstance(node, ast.Assign) and not any(isinstance(t, ast.Name) and t.id in ('ok', 'failures', 'report', 'checks', 'denied', 'deleted', 'altered') for t in node.targets):
                        continue
                    condition = ast.get_source_segment(source, node)
                    if isinstance(node, ast.If):condition = 'if ' + ast.get_source_segment(source, node.test)
                    historical = function.name == 'scope'
                    category = '当時だけ' if historical else '最新でも継続'
                    latest = '固定側のscope（最新の範囲は009専用監査、後続はその段階の監査）' if historical else 'tools/check_region2_village_regression.py::' + ('run' if function.name == 'run_godot' else function.name)
                    if function.name in ('git', 'write'):latest = '最新側のGit SHA取得・JSON保存・終了判定'
                    if function.name == 'main' and ('scope' in condition or 'args.runtime_only' in condition or 'args.scope_only' in condition):
                        latest = '固定scopeと最新動作を別jobで必須実行。009差分はcheck_task009_scope.py'
                    rows.append({'source': path, 'line': node.lineno, 'function': function.name, 'condition': condition,
                                 'category': category, 'fixed': FIXED + ':' + path + ':' + str(node.lineno), 'latest': latest})
    rows.sort(key=lambda row: (row['source'], row['line'], row['condition']))
    for index, row in enumerate(rows, 1):row['id'] = f'A{index:03d}'
    return rows


def validate_fixture() -> None:
    def read(path: str) -> dict:return json.loads(git('show', FIXED + ':' + path))
    village = read('world/region2_village.json')
    ports = read('world/region2_port.json')
    travel = read('world/first_region_travel.json')
    definition = read('world/interiors.json')['first_region'] | ports['definition'] | village['definition']
    destinations = travel['destinations'] + ports['destinations'] + village['destinations']
    destinations[-1]['ship_cell'] = [155, 110]
    expected = {'source_sha': FIXED, 'definition': village['definition'],
                'maps': read('world/region2_village_backdrops.json')['maps'],
                'targets': {k: v['targets'] for k, v in read('assets/source_records/region2-village-backdrops.json')['maps'].items()},
                'destinations': destinations,
                'return_landings': {d['id']: [definition[d['entrance']]['cell'][i] + definition[d['entrance']]['outward'][i] for i in range(2)] for d in destinations}}
    if json.loads((OUT / 'continuing-contract.json').read_text()) != expected:
        raise ValueError('期待値fixtureが固定006の採用値と一致しません')
    originals = json.loads((OUT / 'original-checks.json').read_text())
    for path, value in originals.items():
        if hashlib.sha256(git('show', FIXED + ':' + path)).hexdigest() != value:
            raise ValueError('元検査ハッシュの異常: ' + path)
    for path in SOURCES:
        if (ROOT / path).read_bytes() != git('show', FIXED + ':' + path):
            raise ValueError('元006検査のバイト変更: ' + path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-map', action='store_true')
    args = parser.parse_args()
    rows = inventory()
    manifest = {'fixed_006_sha': FIXED, 'unclassified': 0, 'assertion_sites': len(rows), 'assertions': rows}
    path = OUT / 'assertion-map.json'
    if args.write_map:
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        table = ['| ID | 元検査・箇所 | 条件（ループの全反復を含む） | 分類 | 固定側 | 最新側 / 引継ぎ |', '| --- | --- | --- | --- | --- | --- |']
        for row in rows:
            condition = row['condition'].replace('|', '&#124;').replace('\n', '<br>')
            table.append(f"| {row['id']} | `{row['source']}:{row['line']}` `{row['function']}` | `{condition}` | {row['category']} | 同じソース・行を固定006で全実行 | {row['latest']} |")
        (OUT / 'assertion-map.md').write_text('\n'.join(table) + '\n', encoding='utf-8')
    actual = json.loads(path.read_text())
    if actual != manifest:
        raise ValueError('全assertion対応表の欠落/改変/未分類があります')
    validate_fixture()
    for row in rows:
        if row['category'] == '最新でも継続' and '::' in row['latest']:
            file, function = row['latest'].split('::', 1)
            if not re.search(r'(?:func|def) ' + re.escape(function) + r'\(', (ROOT / file).read_text()):
                raise ValueError('最新対応先が存在しません: ' + row['id'])
    print(f'TASK009_ASSERTION_MAP_PASS: sites={len(rows)} unclassified=0 fixture=fixed006')
    return 0


if __name__ == '__main__':
    sys.exit(main())
