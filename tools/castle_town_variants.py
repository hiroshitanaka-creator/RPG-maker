"""城下町（エルヴァ城下町・仮称）の見た目の仕上げ。依頼者が採用した案Bの配置。

依頼者原画 IMG_0997（docs/reference/visual-targets/first-castle-town.png）を目標にする。
2026年9月28日の1回目の依頼（6項目）で案A/B/Cを作り、依頼者が案Bを採用した（案A・Cの確認画像は 20fdaab に残る）。
同日の2回目の依頼で、木・道幅・花壇を直した（87b7e17 で採用）。
- 木：大きな丸い木（3×3セル）を中心に2〜3本ずつ固め、家の周りと町の縁を囲む
- 道幅：噴水の広場を 14×11 から 12×8 セルへ縮め、空いた分を庭と木に使う
- 花壇：噴水側の角を丸く欠いたL字の花壇を、木の縁と杭で囲み、中を花で埋める
スクリプトで描いた切妻屋根の家はテントのように見えたため、3回目の依頼で使わないことになり、
家は案Aと同じ登録済みの町家・館の素材（初版と同じ種類と位置）に戻した。

壁・門・噴水・6棟の位置、扉と部屋の対応、住人の役と台詞は初版のまま。
"""
import os
import numpy as np
from build_visual_target_mocks import obj, tex, ENTRIES

TREE = 'assets/tiles/bright_tree_oak.png'
TREE_LARGE = obj('tree_round_large')
W, H = 36, 26
LENIENT = os.environ.get('CASTLE_TOWN_LENIENT') == '1'  # 配置調整中だけ、重なりを止めずに一覧で出す


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
        w, h = ENTRIES[path]['size']
        cells = rect(x, y, x + w // 32 - 1, y + h // 32 - 1)
        if solid:
            problems = []
            if not behind and (self.solid & cells).any():
                problems.append('重なり')
            if not on_road and (self.road & cells).any():
                problems.append('道の上')
            if problems:
                if not LENIENT:
                    raise AssertionError((problems, path, x, y))
                print('CONFLICT', problems, path.split('/')[-1], x, y)
            self.solid |= cells
        self.p.stamp(path, x, y, solid)
        if path in (TREE, TREE_LARGE):
            self.trees += 1


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


def fence_row(t, x0, x1, y):
    """庭と道を区切る細い横の柵（64px片）を x0..x1 に並べる。"""
    for x in range(x0, x1, 2):
        t.put(obj('fence_low_horizontal'), x, y)


# 6棟（左上：宿屋、左中：道具屋、左下：防具屋、右上：祠（教会）、右中：武器屋、右下：民家）。
# 扉の位置は各絵の扉の列・最下段。台詞「西の赤い屋根は宿屋。その下の青い屋根が道具屋」「祠は東の青い屋根」と合わせる。
HOUSES = [('town_house_red', 3, 2, (3, 5)), ('town_house_blue', 3, 10, (3, 5)), ('manor', 4, 17, (3, 5)),
          ('church', 26, 1, (3, 7)), ('town_house_red', 27, 10, (3, 5)), ('town_house_blue', 26, 17, (3, 5))]
ROOMS = [4, 5, 7, 8, 6, 9]  # 上の順の建物に対応する室内の部屋番号
# 噴水の斜め四方のL字花壇（噴水側の角が丸く欠けている）
BEDS = [('nw', 12, 10), ('ne', 21, 10), ('sw', 12, 15), ('se', 21, 15)]
# 庭と木。'big'=大きな丸い木（3×3）、'tree'=丸い木（2×2）、'behind_big'=家の屋根の後ろに立つ大きな木
# （切妻屋根の上の透明な角に重ね、屋根より奥に描く）、'fence_row'=庭と道を区切る柵、その他=置物
YARDS = [
    # 北西：宿屋の庭
    ('big', 12, 2), ('tree', 10, 3), ('tree', 13, 5), ('crates', 10, 5), ('fence_row', 9, 14, 7),
    # 北東：教会の前庭
    ('big', 20, 2), ('tree', 23, 3), ('tree', 21, 5), ('barrels', 24, 5), ('fence_row', 20, 25, 7),
    # 西の中段・東の中段：道具屋と武器屋の脇
    ('big', 9, 10), ('tree', 9, 13), ('big', 24, 10), ('flowers_yellow', 25, 13), ('flowers_pink', 26, 14),
    # 南西・南東：井戸のある裏庭
    ('big', 11, 18), ('tree', 14, 19), ('tree', 12, 21), ('flowers_pink', 11, 21), ('flowers_yellow', 14, 21), ('flowers_white', 15, 22),
    ('well', 20, 18), ('big', 23, 18), ('flowers_white', 24, 21), ('flowers_white', 21, 21), ('flowers_pink', 22, 22), ('flowers_yellow', 23, 22),
    # 家の後ろの大きな木（町の縁を囲む）。家ごとに2本を段違いに寄せ、一列に並べない
    ('behind_big', 2, 3), ('behind_big', 5, 2), ('behind_big', 2, 11), ('behind_big', 5, 10), ('behind_big', 3, 18),
    ('behind_big', 6, 17), ('behind_big', 27, 11), ('behind_big', 30, 10), ('behind_big', 26, 18), ('behind_big', 29, 17),
]
SIGNS = [('sign_inn', 9, 6), ('sign_item', 9, 15), ('sign_weapon', 26, 15)]


def build_town_variant(variant, Place, npc):
    assert variant == 'B', '採用済みの案Bだけを作る（案A・Cの記録は 20fdaab）'
    p = Place('castle_town', W, H, tex('grass_meadow'))
    # 十字の石畳：南北の門を結ぶ4マス幅の道、東西へ2マス幅の道、噴水を囲む12×8セルの広場
    road = rect(16, 0, 19, 25) | rect(2, 8, 33, 9) | rect(12, 10, 23, 17)
    doors = [([x + dx, y + dy], index) for (name, x, y, (dx, dy)), index in zip(HOUSES, ROOMS)]
    by_room = sorted(doors, key=lambda d: d[1])  # 扉のつながりは初版と同じ部屋番号の順に記録する
    # 扉から道への小道（土）。中段の家は広場の花壇の間へ、下段の家は最下段の道へつなぐ。
    left_mid, right_mid = doors[1][0], doors[4][0]
    left_low, right_low = doors[2][0], doors[5][0]
    doors = by_room
    paths = (rect(left_mid[0], left_mid[1] + 1, 11, left_mid[1] + 1) | rect(11, 13, 11, left_mid[1] + 1)
             | rect(24, right_mid[1] + 1, right_mid[0], right_mid[1] + 1) | rect(24, 13, 24, right_mid[1] + 1)
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
    for name, x, y, _ in HOUSES:
        if name == 'church':
            # 教会は初版と同じく塔の上端が北の石垣に重なり、石段が東西の道に接する
            t.solid[1, 26:33] = False
            t.put(obj(name), x, y, on_road=True)
        else:
            t.put(obj(name), x, y)
    t.put(obj('fountain'), 16, 11, on_road=True)
    for side, x, y in BEDS:
        t.put(obj('fenced_flowerbed_' + side), x, y, on_road=True)
    for item in YARDS:
        kind = item[0]
        if kind == 'fence_row':
            fence_row(t, item[1], item[2], item[3])
        elif kind == 'big':
            t.put(TREE_LARGE, item[1], item[2])
        elif kind == 'tree':
            t.put(TREE, item[1], item[2])
        elif kind == 'behind_big':
            t.put(TREE_LARGE, item[1], item[2], behind=True)
        else:
            t.put(obj(kind), item[1], item[2])
    assert t.trees >= 20, t.trees
    for name, x, y in SIGNS:
        p.stamp(obj(name), x, y, False)
    # 明るい草地に花を点々と
    meadow_scatter(p, ~(road | paths | t.solid), 110, 0.6)
    # 通行：壁と置物を塞ぎ、門・扉を開ける
    p.mask &= ~t.solid
    for y in range(0, 26):
        if y < 4 or y > 21:
            for x in range(16, 20):
                p.door(x, y)
    for cell, _ in doors:
        p.door(*cell)
        p.door(cell[0], cell[1] + 1)
    return p, residents(npc), doors


def residents(npc):
    return [
        npc('castle_gate_guard', [17, 4], '城門の兵士', ['城へは、噴水の北の門を進んでください。']),
        npc('south_guard', [20, 23], '町の兵士', ['ベルナの関所から来たのですね。町では安心して休んでいってください。']),
        npc('travelling_merchant', [14, 13], '旅の商人', ['北へ向かうなら、まず城へ。道のことは兵士が詳しいですよ。'], 'npc_castle_merchant'),
        npc('town_woman', [21, 9], '町の人', ['西の赤い屋根は宿屋。その下の青い屋根が道具屋です。'], 'npc_woman', patrol=[[21, 9], [22, 9], [22, 8], [21, 8]]),
        npc('town_elder', [15, 17], '町の人', ['城では、それぞれの役目に合った修練を教えてくれるそうです。'], 'npc_elder_man'),
        npc('town_child', [20, 16], '子ども', ['噴水の水、冷たいよ。走って転ばないでね。'], 'npc_boy', patrol=[[20, 16], [20, 17], [19, 17], [19, 16]]),
        npc('shrine_visitor', [24, 9], '祠へ来た人', ['祠は東の青い屋根です。旅の前に気持ちを整えていきます。'], 'npc_elder_woman'),
        npc('town_farmer', [12, 13], '荷を届けた人', ['村から野菜を届けに来たんだ。関所を通れるようになって助かったよ。'], 'npc_farmer')]
