"""城下町（エルヴァ城下町・仮称）の見た目の仕上げ案 A/B/C。

依頼者原画 IMG_0997（docs/reference/visual-targets/first-castle-town.png）を目標に、次の6点を直す。
(1) 丸い緑の木を20本以上、家の周りと町の縁に置く
(2) 門から噴水へまっすぐな十字の石畳
(3) 噴水のまわりに柵で囲んだ花壇を4つ
(4) 大きな屋根の木造の家を中心にし、屋根の色を赤・茶・青に絞る
(5) 家ごとに庭を区切り、樽・木箱・井戸・花を置く
(6) 明るい緑の草地に花が点々と咲く

案A：登録済み素材だけで配置を直す（新しい画像なし）。
案B：派生素材（木造の大屋根の家3色・柵付き花壇・目標画像の明るさの草地）で、家をすべて木造にする。
案C：案Bの派生素材を使い、宿屋と道具屋は従来の町家、ほかの3棟を木造の家にする。草地は案Bより一段明るい緑。

壁・門・広場・噴水・教会・6棟の位置は初版の配置を保ち、扉と部屋の対応・人物の役と台詞は変えない。
"""
import numpy as np
from build_visual_target_mocks import obj, tex

TREE = 'assets/tiles/bright_tree_oak.png'
import os
LENIENT = os.environ.get('CASTLE_TOWN_LENIENT') == '1'  # 配置調整中だけ、重なりを止めずに一覧で出す
W, H = 36, 26


def rect(x0, y0, x1, y1):
    field = np.zeros((H, W), bool)
    field[y0:y1 + 1, x0:x1 + 1] = True
    return field


class Town:
    """配置の重なりを検査しながら、城下町の Place へ物を置く。"""

    def __init__(self, place, road):
        self.p = place
        self.road = road
        self.solid = np.zeros((H, W), bool)
        self.trees = 0

    def put(self, path, x, y, solid=True, on_road=False, behind=False):
        from build_visual_target_mocks import ENTRIES
        w, h = ENTRIES[path]['size']
        cells = rect(x, y, x + w // 32 - 1, y + h // 32 - 1)
        if solid:
            problems = []
            if not behind and (self.solid & cells).any():problems.append('重なり')
            if not on_road and (self.road & cells).any():problems.append('道の上')
            if problems:
                if not LENIENT:raise AssertionError((problems, path, x, y))
                print('CONFLICT', problems, path.split('/')[-1], x, y)
            self.solid |= cells
        self.p.stamp(path, x, y, solid)
        if path == TREE:
            self.trees += 1

    def tree(self, x, y):
        self.put(TREE, x, y)


def walls_and_gates(p):
    for x in range(0, 36, 3):
        if not 15 <= x <= 18:
            p.stamp(obj('wall_horizontal'), x, 0)
            p.stamp(obj('wall_horizontal'), x, 24)
    for y in range(2, 24, 3):
        p.stamp('assets/objects/castle_low_wall_vertical.png', 0, y)
        p.stamp('assets/objects/castle_low_wall_vertical.png', 34, y)
    p.stamp(obj('gate_open'), 16, 0, False)
    p.stamp(obj('gate_open'), 16, 22, False)


def meadow_scatter(p, field, count, flowers):
    """草地に花・草むら・小石を点々と置く。flowers は花の割合（0〜1）。"""
    rng = p.m.rng
    cells = list(map(tuple, np.argwhere(field)))
    rng.shuffle(cells)
    n = 0
    for y, x in cells:
        if (x, y) in p.m.occupied:
            continue
        if rng.random() < flowers:
            name = rng.choice(['flowers_white', 'flowers_yellow', 'flowers_pink'])
        else:
            name = rng.choice(['tufts', 'tufts', 'pebbles', 'leaves'])
        p.m.stamp(obj(name), int(x), int(y), block=False)
        n += 1
        if n >= count:
            break


def fence_row(t, x0, x1, y, on_road=True, piece='fence_horizontal'):
    """横の柵（64px片）を x0..x1 に並べる。端が余る場合は最後を柵の角で閉じる。"""
    x = x0
    while x + 1 <= x1:
        t.put(obj(piece), x, y, on_road=on_road)
        x += 2
    if x == x1:
        t.put(obj('fence_corner'), x, y, on_road=on_road)


def fenced_bed_from_parts(t, x, y):
    """案A：既存の柵と花壇で、4×4セルの柵付き花壇を組む（上下を柵、中に花壇と花）。"""
    fence_row(t, x, x + 3, y)
    fence_row(t, x, x + 3, y + 3)
    t.put(obj('flowerbed'), x, y + 1, on_road=True)
    t.put(obj('flowers_pink'), x + 3, y + 1, on_road=True)
    t.put(obj('flowers_yellow'), x + 3, y + 2, on_road=True)


# 6棟の置き場所（左上：宿屋、左中：道具屋、左下：防具屋、右上：祠（教会）、右中：武器屋、右下：民家）。
# 扉の位置は各絵の扉の列・最下段。台詞「西の赤い屋根は宿屋。その下の青い屋根が道具屋」「祠は東の青い屋根」と合わせる。
HOUSES = {
    'A': [('town_house_red', 3, 2, (3, 5)), ('town_house_blue', 3, 10, (3, 5)), ('manor', 3, 17, (3, 5)),
          ('church', 26, 1, (3, 7)), ('town_house_red', 27, 10, (3, 5)), ('town_house_blue', 26, 17, (3, 5))],
    'B': [('wood_house_red', 2, 2, (4, 5)), ('wood_house_blue', 2, 10, (4, 5)), ('wood_house_brown', 3, 17, (4, 5)),
          ('church', 26, 1, (3, 7)), ('wood_house_red', 27, 10, (4, 5)), ('wood_house_brown', 26, 17, (4, 5))],
    'C': [('town_house_red', 3, 2, (3, 5)), ('town_house_blue', 3, 10, (3, 5)), ('wood_house_brown', 3, 17, (4, 5)),
          ('church', 26, 1, (3, 7)), ('wood_house_red', 27, 10, (4, 5)), ('wood_house_brown', 26, 17, (4, 5))],
}
ROOMS = [4, 5, 7, 8, 6, 9]  # 上の順の建物に対応する室内の部屋番号


def build_town_variant(variant, Place, npc):
    assert variant in HOUSES, variant
    grass = {'A': tex('grass_2'), 'B': tex('grass_meadow'), 'C': tex('grass_meadow_light')}[variant]
    p = Place('castle_town', W, H, grass)
    # (2) 十字の石畳：南北の門を結ぶ4マス幅の道、東西へ2マス幅の道、噴水を囲む四角い広場
    vertical = rect(16, 0, 19, 25)
    horizontal = rect(2, 8, 33, 9)
    plaza = rect(10, 8, 25, 18) if variant == 'A' else rect(11, 8, 24, 18)
    road = vertical | horizontal | plaza
    houses = HOUSES[variant]
    doors = []
    for (name, x, y, (dx, dy)), index in zip(houses, ROOMS):
        doors.append(([x + dx, y + dy], index))
    # 扉から道への小道（土）。中段の家は広場の花壇の間へ、下段の家は最下段の道へつなぐ。
    left_mid, right_mid = doors[1][0], doors[4][0]
    left_low, right_low = doors[2][0], doors[5][0]
    paths = (rect(left_mid[0], left_mid[1] + 1, 10, left_mid[1] + 1) | rect(10, 13, 10, left_mid[1] + 1)
             | rect(25, right_mid[1] + 1, right_mid[0], right_mid[1] + 1) | rect(25, 13, 25, right_mid[1] + 1)
             | rect(left_low[0], 23, 16, 23) | rect(19, 23, right_low[0], 23))
    for (cx, cy), _ in doors:
        paths[cy + 1, cx] = True
    paths &= ~road
    p.m.terrain('dirt', paths)
    p.m.terrain('cobble', road)
    t = Town(p, road | paths)
    walls_and_gates(p)
    t.solid |= rect(0, 0, 35, 1) | rect(0, 24, 35, 25) | rect(0, 0, 1, 25) | rect(34, 0, 35, 25)
    t.solid[0:4, 16:20] = False
    t.solid[22:26, 16:20] = False
    for name, x, y, _ in houses:
        if name == 'church':
            # 教会は初版と同じく塔の上端が北の石垣に重なり、石段が東西の道に接する
            t.solid[1, 26:33] = False
            t.put(obj(name), x, y, on_road=True)
        else:
            t.put(obj(name), x, y)
    t.put(obj('fountain'), 16, 11, on_road=True)
    # (3) 噴水のまわりの柵付き花壇4つ
    if variant == 'A':
        for x, y in [(10, 10), (22, 10), (10, 15), (22, 15)]:
            fenced_bed_from_parts(t, x, y)
    else:
        for x, y in [(11, 10), (22, 10), (11, 15), (22, 15)]:
            t.put(obj('fenced_flowerbed'), x, y, on_road=True)
    # (1)(5) 家ごとの庭と丸い木
    garden(t, variant)
    assert t.trees >= 20, t.trees
    # 看板とベンチ
    signs = {'A': [('sign_inn', 9, 6), ('sign_item', 9, 14), ('sign_weapon', 33, 14)],
             'B': [('sign_inn', 9, 6), ('sign_item', 9, 14), ('sign_weapon', 26, 14)],
             'C': [('sign_inn', 9, 6), ('sign_item', 9, 14), ('sign_weapon', 26, 14)]}[variant]
    for name, x, y in signs:
        p.stamp(obj(name), x, y, False)
    # (6) 明るい草地に花を点々と
    free = ~(road | paths | t.solid)
    meadow_scatter(p, free, 70 if variant == 'A' else 110, 0.35 if variant == 'A' else 0.6)
    # 通行：壁と置物を塞ぎ、門・扉を開ける
    p.mask &= ~t.solid
    for y in range(0, 26):
        if y < 4 or y > 21:
            for x in range(16, 20):
                p.door(x, y)
    for cell, _ in doors:
        p.door(*cell)
        p.door(cell[0], cell[1] + 1)
    events = residents(variant, npc)
    return p, events, doors


# (1)(5) 庭と木。'tree'=丸い木（2×2セル）、'behind'=家の屋根の後ろに立つ木（家の上角の透明部分に重ね、屋根より奥に描く）、
# 'fence_row'=庭を道から区切る横の柵、その他=置物（樽・木箱・井戸・花）。
_FRONT_B = [('fence_row', 9, 14, 7), ('tree', 9, 2), ('tree', 12, 2), ('tree', 14, 2), ('tree', 13, 5), ('crates', 11, 5),
            ('fence_row', 20, 25, 7), ('tree', 21, 2), ('tree', 24, 2), ('tree', 22, 5), ('tree', 20, 5), ('barrels', 24, 5),
            ('tree', 9, 10), ('tree', 25, 10),
            ('fence_row', 10, 15, 19), ('tree', 10, 20), ('well', 12, 20), ('flowers_pink', 15, 20), ('flowers_yellow', 15, 21),
            ('fence_row', 20, 25, 19), ('tree', 24, 20), ('well', 21, 20), ('flowers_white', 20, 21), ('flowers_pink', 20, 22)]
YARDS = {
    'A': [('fence_row', 9, 14, 7), ('tree', 9, 2), ('tree', 12, 2), ('tree', 14, 2), ('tree', 13, 5), ('crates', 10, 5),
          ('fence_row', 20, 25, 7), ('tree', 21, 2), ('tree', 24, 2), ('tree', 22, 5), ('tree', 20, 5), ('barrels', 24, 5),
          ('flowers_yellow', 33, 3),
          ('fence_row', 10, 15, 19), ('tree', 10, 20), ('well', 12, 20), ('flowers_pink', 15, 20), ('flowers_yellow', 15, 21),
          ('fence_row', 20, 25, 19), ('tree', 24, 20), ('well', 21, 20), ('flowers_white', 20, 21), ('flowers_pink', 20, 22),
          ('behind', 3, 2), ('behind', 7, 2), ('behind', 3, 10), ('behind', 7, 10), ('behind', 27, 10), ('behind', 31, 10),
          ('behind', 26, 17), ('behind', 30, 17), ('behind', 3, 17), ('behind', 8, 17)],
    'B': _FRONT_B + [('behind', 2, 2), ('behind', 7, 2), ('behind', 2, 10), ('behind', 7, 10), ('behind', 3, 17), ('behind', 8, 17),
                     ('behind', 27, 10), ('behind', 32, 10), ('behind', 26, 17), ('behind', 31, 17)],
    'C': _FRONT_B + [('behind', 3, 2), ('behind', 7, 2), ('behind', 3, 10), ('behind', 7, 10), ('behind', 3, 17), ('behind', 8, 17),
                     ('behind', 27, 10), ('behind', 31, 10), ('behind', 26, 17), ('behind', 31, 17),
                     ('flowers_white', 2, 16)],
}


def garden(t, variant):
    """家ごとの庭と木。柵で道から区切り、樽・木箱・井戸・花を置く。"""
    for item in YARDS[variant]:
        kind = item[0]
        if kind == 'fence_row':
            fence_row(t, item[1], item[2], item[3], on_road=False, piece='fence_horizontal' if variant == 'A' else 'fence_low_horizontal')
        elif kind == 'tree':
            t.tree(item[1], item[2])
        elif kind == 'behind':
            t.put(TREE, item[1], item[2], behind=True)
        else:
            t.put(obj(kind), item[1], item[2])


def residents(variant, npc):
    return [
        npc('castle_gate_guard', [17, 4], '城門の兵士', ['城へは、噴水の北の門を進んでください。']),
        npc('south_guard', [20, 23], '町の兵士', ['ベルナの関所から来たのですね。町では安心して休んでいってください。']),
        npc('travelling_merchant', [14, 13], '旅の商人', ['北へ向かうなら、まず城へ。道のことは兵士が詳しいですよ。'], 'npc_castle_merchant'),
        npc('town_woman', [21, 9], '町の人', ['西の赤い屋根は宿屋。その下の青い屋根が道具屋です。'], 'npc_woman', patrol=[[21, 9], [22, 9], [22, 8], [21, 8]]),
        npc('town_elder', [14, 17], '町の人', ['城では、それぞれの役目に合った修練を教えてくれるそうです。'], 'npc_elder_man'),
        npc('town_child', [21, 17], '子ども', ['噴水の水、冷たいよ。走って転ばないでね。'], 'npc_boy', patrol=[[21, 17], [21, 18], [20, 18], [20, 17]]),
        npc('shrine_visitor', [24, 9], '祠へ来た人', ['祠は東の青い屋根です。旅の前に気持ちを整えていきます。'], 'npc_elder_woman'),
        npc('town_farmer', [12, 13] if variant != 'A' else [11, 14], '荷を届けた人', ['村から野菜を届けに来たんだ。関所を通れるようになって助かったよ。'], 'npc_farmer')]
