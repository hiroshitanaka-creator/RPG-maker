#!/usr/bin/env python3
"""城下町の見た目の仕上げ用に、登録済み素材から派生素材を決定論的に作る。

画像生成は使わない。元画像の画素を切り貼りし、natural.gpl 内の色で描き足すだけで作る。
- natural_gable_house_{red,brown,blue}: わら屋根の家Aの壁・扉・小物はそのまま使い、屋根を
  三角のはっきりした切妻屋根（棟が縦に通り、左右の面で明暗を分けた板葺き）に描き替える
- natural_tree_round_large: 丸い木の葉の塊5つと幹を組んだ、96×96の大きな丸い木
- natural_fenced_flowerbed_{nw,ne,sw,se}: 噴水に向いた角を丸く欠いたL字の花壇。木の縁と杭で囲み、
  中を葉と花でびっしり埋める。4方向は北西の絵の左右・上下反転
- natural_fence_low_horizontal: 柵の角材から組んだ、庭を区切る細い横の柵
- natural_grass_meadow: 草地2の暗い粒を中間の緑へ寄せ、目標画像の草地の明るさへ合わせた128×128の地面
"""
import colorsys
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OBJ = ROOT / 'assets/objects'
TILE = ROOT / 'assets/tiles'
RECORD = ROOT / 'assets/source_records/castle-town-polish.json'
PALETTE = [tuple(map(int, l.split()[:3])) for l in (ROOT / 'assets/palette/natural.gpl').read_text(encoding='utf8').splitlines() if l.strip()[:1].isdigit()]

# 屋根の色段（暗→明）。すべて natural.gpl の色。
RAMPS = {
    'brown': [(37, 15, 7), (58, 35, 23), (75, 55, 28), (104, 66, 47), (116, 90, 50), (154, 96, 72), (169, 131, 71)],
    'red': [(37, 15, 7), (61, 11, 20), (93, 39, 23), (116, 40, 27), (144, 66, 45), (179, 67, 63), (191, 105, 77)],
    'blue': [(11, 24, 36), (22, 40, 53), (21, 53, 80), (37, 74, 99), (51, 108, 149), (114, 133, 147), (189, 199, 211)],
}
# 屋根の面の基本段（左の面・右の面）
FACE = {'brown': (3, 4), 'red': (3, 4), 'blue': (3, 4)}
# 切妻屋根の形（224×192の画像の画素座標）。頂点・軒の高さ・軒の左右端
APEX = (111.5, 14)
EAVE = 134
EAVE_X = (1, 222)
# 煙突（わら屋根の家Aの石の煙突）を切り出す範囲と、貼る位置
CHIMNEY = ((58, 16, 88, 64), (132, 36))
# 草地の置換表。花の色は変えない。暗い粒を中間色へ寄せてざらつきを消し、
# 明るさを目標画像の草地（中央値 RGB 80,108,26 付近）へ合わせる。
MEADOW = {
    (18, 28, 15): (80, 95, 38), (33, 47, 20): (80, 95, 38), (49, 70, 25): (91, 107, 41),
    (70, 79, 35): (91, 107, 41), (80, 95, 38): (91, 107, 41), (91, 107, 41): (101, 123, 42),
}
WOOD = [(42, 33, 19), (75, 55, 28), (116, 90, 50), (139, 127, 85)]  # 花壇の木の縁（暗→明）
LEAF = [(33, 47, 20), (49, 70, 25), (80, 95, 38)]  # 花壇の葉の下地


def hsv(c):
    h, s, v = colorsys.rgb_to_hsv(*[x / 255 for x in c])
    return h * 360, s, v


def gable_house(color):
    """わら屋根の家Aの壁より上を消し、三角の切妻屋根を描く。"""
    src = np.array(Image.open(OBJ / 'natural_farm_house_a.png').convert('RGBA'))
    h, w = src.shape[:2]
    out = src.copy()
    out[:EAVE] = 0
    ramp = RAMPS[color]
    left_base, right_base = FACE[color]
    ax, ay = APEX
    half = lambda y: (y - ay) / (EAVE - ay) * ((EAVE_X[1] - EAVE_X[0]) / 2)
    inside = np.zeros((h, w), bool)
    for y in range(int(ay), EAVE + 1):
        for x in range(w):
            inside[y, x] = abs(x + 0.5 - ax) <= half(y + 0.5)
    for y, x in zip(*np.nonzero(inside)):
        left = x + 0.5 < ax
        i = left_base if left else right_base
        band = (y - int(ay)) // 5
        row = (y - int(ay)) % 5
        col = (x + (band % 2) * 3) % 6
        if y > EAVE - 26:
            i -= 1          # 軒に近い下の帯は一段暗く（上から光が当たる）
        if row == 4:
            i -= 2          # 段の影
        elif col == 0:
            i -= 1          # 板の継ぎ目
        elif row == 0:
            i += 1          # 段の上端の光
        if abs(x + 0.5 - ax) < 1.5:
            i = 1 if left else right_base + 2   # 棟（縦に通る稜線）
        edge = not (inside[y, x - 1] and inside[y, x + 1] and inside[y - 1, x]) if 0 < x < w - 1 else True
        if edge:
            i = 0           # 屋根の輪郭
        elif y >= EAVE - 2:
            i = 1 if y == EAVE - 2 else 0   # 軒先の板
        out[y, x, :3] = ramp[max(0, min(len(ramp) - 1, i))]
        out[y, x, 3] = 255
    # 煙突（石の部分だけ）を右の面に立てる
    (x0, y0, x1, y1), (px, py) = CHIMNEY
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = (int(t) for t in src[y, x])
            if a and hsv((r, g, b))[1] < 0.25:
                out[py + y - y0, px + x - x0] = (r, g, b, 255)
    return Image.fromarray(out), {'base': 'assets/objects/natural_farm_house_a.png', 'apex': list(APEX), 'eave': EAVE, 'ramp': [list(c) for c in ramp], 'faces': list(FACE[color])}


def large_tree():
    """丸い木の葉の塊を5つ重ね、幹を足して大きな丸い木にする。"""
    oak = np.array(Image.open(TILE / 'bright_tree_oak.png').convert('RGBA'))
    leaves = oak.copy()
    for y in range(64):
        for x in range(64):
            r, g, b, a = (int(t) for t in oak[y, x])
            if a and not (g > r and y < 46):
                leaves[y, x] = 0
    crown = Image.fromarray(leaves).crop((2, 0, 62, 46))
    trunk = Image.fromarray(oak).crop((18, 34, 46, 64))
    out = Image.new('RGBA', (96, 96))
    out.alpha_composite(trunk, (34, 66))
    for x, y in [(18, 0), (0, 16), (36, 16), (6, 30), (30, 30)]:
        out.alpha_composite(crown, (x, y))
    return out, {'components': ['assets/tiles/bright_tree_oak.png']}


def flowerbed_nw():
    """北西の花壇。右下（噴水側）の角を円弧で欠いたL字。木の縁と杭で囲み、中を花で埋める。"""
    size = 96
    yy, xx = np.mgrid[:size, :size] + 0.5
    shape = (xx >= 3) & (xx <= 93) & (yy >= 3) & (yy <= 93) & (np.hypot(xx - 118, yy - 118) >= 70)
    dist = np.full((size, size), 99)
    for d in range(1, 6):
        grown = np.zeros_like(shape)
        for dy in range(-d, d + 1):
            for dx in range(-d, d + 1):
                if abs(dx) + abs(dy) <= d:
                    grown |= np.roll(np.roll(~shape, dy, 0), dx, 1)
        dist[(dist == 99) & shape & grown] = d
    out = np.zeros((size, size, 4), np.uint8)
    # 葉の下地：3色を斜めの縞で混ぜ、土が見えないようにする
    for y, x in zip(*np.nonzero(shape)):
        out[y, x] = (*LEAF[(x * 3 + y * 5) // 4 % 3], 255)
    image = Image.fromarray(out)
    flowers = {c: Image.open(OBJ / f'natural_flowers_{c}.png').convert('RGBA').crop((0, 4, 32, 32)) for c in ('pink', 'white', 'yellow')}
    bush = Image.open(OBJ / 'natural_flowerbed.png').convert('RGBA').crop((4, 2, 92, 46))
    layer = Image.new('RGBA', (size, size))
    layer.alpha_composite(bush, (4, 2))
    layer.alpha_composite(bush.crop((0, 0, 44, 44)), (2, 44))
    order = ['pink', 'yellow', 'white']
    spots = [(4, 4), (26, 2), (50, 4), (70, 6), (6, 24), (30, 22), (52, 26), (4, 46), (24, 48), (6, 66), (22, 64), (40, 40)]
    for i, (x, y) in enumerate(spots):
        layer.alpha_composite(flowers[order[i % 3]], (x, y))
    mask = Image.fromarray(((shape & (dist > 4)) * 255).astype(np.uint8))
    image.paste(layer, (0, 0), Image.composite(layer.getchannel('A'), Image.new('L', (size, size)), mask))
    out = np.array(image)
    # 木の縁（外から暗→明→中間の3画素）と杭
    for y, x in zip(*np.nonzero(shape & (dist <= 4))):
        out[y, x] = (*WOOD[{1: 0, 2: 2, 3: 3, 4: 1}[int(dist[y, x])]], 255)
    post = Image.open(OBJ / 'natural_fence_corner.png').convert('RGBA').crop((1, 2, 6, 13))
    image = Image.fromarray(out)
    for x, y in [(1, 0), (90, 0), (1, 84), (44, 0), (1, 42), (90, 22), (22, 84)]:
        image.alpha_composite(post, (x, y))
    return image


def flowerbeds():
    nw = flowerbed_nw()
    info = {'components': ['assets/objects/natural_flowerbed.png', 'assets/objects/natural_flowers_pink.png', 'assets/objects/natural_flowers_white.png', 'assets/objects/natural_flowers_yellow.png', 'assets/objects/natural_fence_corner.png']}
    return {
        'nw': (nw, info),
        'ne': (nw.transpose(Image.Transpose.FLIP_LEFT_RIGHT), info),
        'sw': (nw.transpose(Image.Transpose.FLIP_TOP_BOTTOM), info),
        'se': (nw.transpose(Image.Transpose.ROTATE_180), info),
    }


def low_fences():
    """柵の角材から、道と庭を区切る細い横の柵（64×32）を組む。"""
    corner = Image.open(OBJ / 'natural_fence_corner.png').convert('RGBA')
    rail_h = corner.crop((8, 2, 21, 12))
    post = corner.crop((1, 2, 6, 13))
    horizontal = Image.new('RGBA', (64, 32))
    for x in range(3, 61, 13):
        horizontal.alpha_composite(rail_h if x + 13 <= 61 else rail_h.crop((0, 0, 61 - x, 10)), (x, 14))
    for x in (0, 30, 59):
        horizontal.alpha_composite(post, (x, 12))
    return horizontal


def meadow(table):
    a = np.array(Image.open(TILE / 'natural_grass_2.png').convert('RGBA'))
    b = a.copy()
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            c = tuple(int(t) for t in a[y, x, :3])
            if c in table:
                b[y, x, :3] = table[c]
    return Image.fromarray(b), {'table': [[list(k), list(v)] for k, v in table.items()]}


def binarize_check(image, name):
    a = np.array(image)
    alpha = a[:, :, 3]
    a[:, :, 3] = np.where(alpha >= 128, 255, 0)
    a[a[:, :, 3] == 0] = 0
    colors = {tuple(int(t) for t in p[:3]) for p in a.reshape(-1, 4) if p[3]}
    outside = colors - set(PALETTE)
    assert not outside, (name, sorted(outside)[:5])
    assert len(colors) <= 64, (name, len(colors))
    return Image.fromarray(a), len(colors)


def main():
    built = {}
    for color in RAMPS:
        built[f'assets/objects/natural_gable_house_{color}.png'] = gable_house(color)
    built['assets/objects/natural_tree_round_large.png'] = large_tree()
    for side, value in flowerbeds().items():
        built[f'assets/objects/natural_fenced_flowerbed_{side}.png'] = value
    built['assets/objects/natural_fence_low_horizontal.png'] = (low_fences(), {'components': ['assets/objects/natural_fence_corner.png']})
    image, info = meadow(MEADOW)
    built['assets/tiles/natural_grass_meadow.png'] = (image, dict(info, base='assets/tiles/natural_grass_2.png'))
    record = {'tool': 'tools/build_castle_town_polish_assets.py', 'generated_at': '2026-09-28', 'method': '画像生成なし。登録済み素材の画素を切り貼りし、natural.gpl 内の色で描き足した決定論的な派生素材。', 'outputs': {}}
    for path, (image, info) in built.items():
        image, count = binarize_check(image, path)
        image.save(ROOT / path, optimize=False)
        record['outputs'][path] = dict(info, size=list(image.size), colors=count, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
    RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
    registry_path = ROOT / 'assets/registry.json'
    registry = json.loads(registry_path.read_text(encoding='utf8'))
    known = {e['path'] for e in registry['assets']}
    for path, (image, info) in built.items():
        entry = {
            'path': path, 'kind': 'tileset' if path.startswith('assets/tiles/') else 'object', 'size': list(image.size), 'max_colors': 64,
            'status': 'required', 'palette': 'assets/palette/natural.gpl', 'source': 'generated', 'tool': 'Python/Pillow',
            'author': 'RPG-maker / Codex', 'license': 'LicenseRef-Generated-Project', 'generated_at': '2026-09-28',
            'prompt_record': 'assets/source_records/castle-town-polish.json',
            'modified': '城下町の仕上げ用。画像生成なし。登録済み素材の画素を切り貼りし、natural.gpl内の色で描き足した決定論的派生。アルファ二値。',
            'component_sources': [info['base']] if 'base' in info else info['components'],
        }
        if path.startswith('assets/tiles/'):
            entry.update(tile_size=[32, 32], repeat_cells=[4, 4])
        if path in known:
            registry['assets'] = [entry if e['path'] == path else e for e in registry['assets']]
        else:
            registry['assets'].append(entry)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
    print('CASTLE_POLISH_ASSETS_PASS: outputs=%d' % len(built))


if __name__ == '__main__':
    main()
