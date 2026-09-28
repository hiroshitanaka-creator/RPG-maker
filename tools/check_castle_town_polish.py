#!/usr/bin/env python3
"""城下町の見た目の仕上げ（2026年9月28日の依頼6項目と、案B採用後の修正4点）を、本番配置データから機械検査する。

比較の相手は、この作業の直前のコミット 07ac451（城下町・城の採用後の最終コミット）に固定する。
修正4点の「道幅を細く」は、依頼者が見た案Bのコミット 20fdaab と比べる。
城下町（first_castle の部屋0）以外の部屋・地図、扉と部屋の対応、人物の役と台詞が変わっていないことも確かめる。
主観の評価（目標の絵に近いか）はここでは判定せず、確認画像で依頼者が判断する。
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = '07ac451'
ADOPTED = '20fdaab'  # 依頼者が採用した案Bの提出時点
NODE = 'first_castle'


def at_base(path, commit=BASE):
    return json.loads(subprocess.run(['git', 'show', f'{commit}:{path}'], cwd=ROOT, capture_output=True, check=True).stdout)


def now(path):
    return json.loads((ROOT / path).read_text(encoding='utf8'))


def cells(layer):
    return {(c[0], c[1]) for c in layer['cells']}


def main():
    failures = []

    def check(ok, label):
        print(('PASS ' if ok else 'FAIL ') + label)
        if not ok:
            failures.append(label)

    visual = now('world/first_region_visuals.json')
    base_visual = at_base('world/first_region_visuals.json')
    town = visual['maps'][f'{NODE}:0']
    tiles = town['tiles']
    layers = town['layers']

    def named(stem):
        return [l for l in layers if l['name'] in (stem, 'natural_' + stem, 'bright_' + stem)]

    # (1) 丸い木20本以上。家の周り（家の庭＝家から5セル以内）と町の縁（外周から4セル以内）に置かれている
    # 修正：大きな丸い木（3×3セル）を6本以上。どの木も隣り合う木（1セル以内）を持ち、2〜3本ずつ固まる
    trees = named('tree_oak') + named('tree_round_large')
    houses = [l for l in layers if 'house' in l['name'] or l['name'] in ('natural_church', 'natural_manor')]
    house_cells = set().union(*[cells(l) for l in houses])
    near = 0
    for tree in trees:
        xs = [c[0] for c in tree['cells']]; ys = [c[1] for c in tree['cells']]
        edge = min(xs) <= 5 or max(xs) >= town['width'] - 6 or min(ys) <= 4 or max(ys) >= town['height'] - 5
        house = any(abs(x - hx) <= 5 and abs(y - hy) <= 5 for x, y in cells(tree) for hx, hy in house_cells)
        near += edge or house
    check(len(trees) >= 20, f'(1) 丸い木が20本以上: {len(trees)}本')
    check(near == len(trees), f'(1) 木はすべて家の周りか町の縁: {near}/{len(trees)}')
    large = named('tree_round_large')
    check(len(large) >= 6, f'修正2 大きな丸い木（3×3セル）が6本以上: {len(large)}本')
    lonely = []
    for tree in trees:
        others = [o for o in trees if o is not tree]
        if not any(abs(x - ox) <= 1 and abs(y - oy) <= 1 for x, y in cells(tree) for o in others for ox, oy in cells(o)):
            lonely.append(min(cells(tree)))
    check(not lonely, f'修正2 どの木も隣り合う木を持つ（2〜3本の固まり）: 孤立 {lonely}')
    rows = {}
    for tree in trees:
        rows.setdefault(min(y for _, y in cells(tree)), []).append(tree)
    lined = max(len(v) for v in rows.values())
    check(lined <= 4, f'修正2 同じ行に並ぶ木は4本まで（生け垣のような一列を作らない）: 最大{lined}本')

    # (2) 門から噴水へまっすぐな十字の石畳：南北の門の間の4列が途切れない石畳、東西の2行が外壁の内側まで続く
    cobble = set().union(*[cells(l) for l in named('cobble')]) if named('cobble') else set()
    vertical = all((x, y) in cobble for x in range(16, 20) for y in range(0, town['height']))
    horizontal = all((x, y) in cobble for x in range(2, town['width'] - 2) for y in range(8, 10))
    check(vertical, '(2) 北門から南門まで4マス幅のまっすぐな石畳（噴水の下も石畳）')
    check(horizontal, '(2) 東西の外壁まで2マス幅のまっすぐな石畳')
    adopted = at_base('world/first_region_visuals.json', ADOPTED)['maps'][f'{NODE}:0']
    adopted_cobble = set().union(*[cells(l) for l in adopted['layers'] if l['name'] == 'cobble'])
    check(len(cobble) < len(adopted_cobble), f'修正3 石畳のセル数を採用時（20fdaab）より減らす: {len(adopted_cobble)} → {len(cobble)}')
    check(not any((x, 11) in cobble for x in list(range(2, 12)) + list(range(24, 34))), '修正3 東西の道は2マス幅（噴水の行では広場の外に石畳がない）')
    fountain = named('fountain')
    check(len(fountain) == 1 and min(c[0] for c in fountain[0]['cells']) == 16 and min(c[1] for c in fountain[0]['cells']) == 11, '(2) 噴水は十字の中心列（x16〜19）に初版と同じ位置')

    # (3) 噴水のまわりに柵で囲んだ花壇4つ（噴水の四方の斜め、噴水から4セル以内）
    beds = [l for l in layers if l['name'].startswith('natural_fenced_flowerbed')]
    fx, fy = 17.5, 12.5
    quadrants = set()
    for bed in beds:
        bx = sum(c[0] for c in bed['cells']) / len(bed['cells']); by = sum(c[1] for c in bed['cells']) / len(bed['cells'])
        if abs(bx - fx) <= 7 and abs(by - fy) <= 5:
            quadrants.add((bx > fx, by > fy))
    check(len(beds) == 4 and len(quadrants) == 4, f'(3) 噴水の四方の斜めに柵つき花壇4つ: 花壇{len(beds)} 方角{len(quadrants)}')
    for bed in beds:
        side = bed['name'].rsplit('_', 1)[1]
        bx = sum(c[0] for c in bed['cells']) / len(bed['cells']); by = sum(c[1] for c in bed['cells']) / len(bed['cells'])
        expect = ('n' if by < fy else 's') + ('w' if bx < fx else 'e')
        check(side == expect, f'修正4 花壇の欠けた角が噴水を向く: {bed["name"]} の位置は {expect}')

    # (4) 屋根の色は赤・茶・青だけ。わら屋根（黄色い屋根）の家を使わない
    roof_of = {'town_house_red': '赤', 'town_house_blue': '青', 'manor': '赤', 'church': '青',
               'gable_house_red': '赤', 'gable_house_brown': '茶', 'gable_house_blue': '青'}
    kinds = [l['name'].removeprefix('natural_') for l in houses]
    check(all(k in roof_of for k in kinds) and len(kinds) == 6, f'(4) 6棟の屋根が赤・茶・青のどれか: {kinds}')
    check(not any('farm_house' in l['name'] for l in layers), '(4) わら屋根の家を置かない')
    wooden = sum(k.startswith('gable_house') for k in kinds)
    check(wooden >= 3, f'(4) 教会以外の5棟のうち過半（3棟以上）が木造の大屋根の家: {wooden}棟')
    check(wooden == 5, f'修正1 教会以外の5棟すべてが三角の切妻屋根の木造の家: {wooden}棟')

    # (5) 家ごとの庭：各家から5セル以内に樽・木箱・井戸・花のどれかがある。井戸が1つ以上
    props = [l for l in layers if l['name'].removeprefix('natural_') in ('barrels', 'crates', 'well', 'flowers_pink', 'flowers_white', 'flowers_yellow', 'flowerbed')]
    prop_cells = set().union(*[cells(l) for l in props])
    for house in houses:
        ok = any(abs(x - px) <= 5 and abs(y - py) <= 5 for x, y in cells(house) for px, py in prop_cells)
        check(ok, f'(5) 庭の小物が近くにある: {house["name"]}')
    check(len(named('well')) >= 1, f'(5) 井戸がある: {len(named("well"))}')
    fences = [l for l in layers if 'fence' in l['name'] and 'flowerbed' not in l['name']]
    check(len(fences) >= 4, f'(5) 庭を道から区切る柵がある: {len(fences)}片')

    # (6) 草地は明るい草地の素材。花が点々と（花の小物30以上）
    ground = next(l for l in layers if l['name'] == '地面')
    grass = {tiles[c[2]]['path'] for c in ground['cells']}
    base_ground = next(l for l in base_visual['maps'][f'{NODE}:0']['layers'] if l['name'] == '地面')
    base_grass = {base_visual['maps'][f'{NODE}:0']['tiles'][c[2]]['path'] for c in base_ground['cells']}
    check(grass != base_grass and grass <= {'assets/tiles/natural_grass_meadow.png'}, f'(6) 初版の暗い草地 {sorted(base_grass)} から明るい草地 {sorted(grass)} へ')
    flowers = sum(len(l['cells']) for l in layers if l['name'].removeprefix('natural_').startswith('flowers_'))
    check(flowers >= 30, f'(6) 草地の花が30以上: {flowers}')

    # 変えていないこと：城下町以外の地図・部屋、扉と部屋の対応、人物の役と台詞
    for key, value in base_visual['maps'].items():
        if key != f'{NODE}:0':
            check(visual['maps'].get(key) == value, f'城下町以外の地図は07ac451と同じ: {key}')
    base_def = at_base('world/first_region.json')['first_region']
    definition = now('world/first_region.json')
    first = definition['first_region']
    # 扉のセルは家の絵の扉の列に合わせて動くことがある。部屋の対応と、城下町以外の出入口は変えない
    def door_rooms(links):
        return sorted((l['from']['room'], l['to']['room']) for l in links)
    def outside_town(links):
        return sorted(json.dumps(l, sort_keys=True) for l in links if l['from']['room'] != 0 and l['to']['room'] != 0)
    def town_side(links):
        return sorted(json.dumps(l, sort_keys=True) for l in links if l['from']['room'] in (0, 1, 2) and l['to']['room'] in (0, 1, 2))
    check(door_rooms(first['castle_doors']) == door_rooms(base_def['castle_doors']), '扉と部屋の対応（どの扉がどの部屋へ）は07ac451と同じ')
    check(outside_town(first['castle_doors']) == outside_town(base_def['castle_doors']), '城内・店の中の出入口セルは07ac451と同じ')
    check(town_side(first['castle_doors']) == town_side(base_def['castle_doors']), '北門から城の中庭への出入口セルは07ac451と同じ')
    moved = sorted({tuple(l['from']['cell']) for l in first['castle_doors'] if l['from']['room'] == 0} - {tuple(l['from']['cell']) for l in base_def['castle_doors'] if l['from']['room'] == 0})
    print(f'INFO 家の絵に合わせて移した城下町側の扉セル: {moved}')
    for key in ('castle_entrance', 'castle_exit', 'castle_spawn'):
        check(first[key] == base_def[key], f'城下町の出入口は07ac451と同じ: {key}')
    base_site = next(s for s in at_base('world/first_region.json')['sites'] if s['id'] == NODE)
    site = next(s for s in definition['sites'] if s['id'] == NODE)
    check(site['rooms'][1:] == base_site['rooms'][1:], '城内・店の部屋は07ac451と同じ')
    strip = lambda events: sorted((e['id'], e['label'], tuple(e['text']), e.get('sprite')) for e in events)
    check(strip(site['rooms'][0]['events']) == strip(base_site['rooms'][0]['events']), '城下町の住人8人の役・絵・台詞は07ac451と同じ（立ち位置だけ変更）')
    check(site['rooms'][0]['title'] == base_site['rooms'][0]['title'], '城下町の名前は07ac451と同じ')
    interiors = now('world/interiors.json')
    check(next(s for s in interiors['sites'] if s['id'] == NODE) == site and interiors['first_region'] == first, 'interiors.json の城下町は first_region.json と一致')

    if failures:
        print(f'CASTLE_TOWN_POLISH_FAIL: failures={len(failures)}')
        return 1
    print(f'CASTLE_TOWN_POLISH_PASS: trees={len(trees)} beds={len(beds)} flowers={flowers}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
