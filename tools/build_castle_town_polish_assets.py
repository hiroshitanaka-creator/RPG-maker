#!/usr/bin/env python3
"""城下町の見た目の仕上げ用に、登録済み素材から派生素材を決定論的に作る。

画像生成は使わない。元画像の画素を、natural.gpl 内の色へ置き換える・切り貼りするだけで作る。
- natural_wood_house_{brown,red,blue}: わら屋根の家Aの屋根（手指定の多角形 × 色条件）を、木板・赤瓦・青石の色段で板葺きの模様に塗り替え
- natural_fenced_flowerbed: 柵の角材から柵の枠を、花の小物から中の花を組んだ96×96の花壇
- natural_fence_low_horizontal: 柵の角材から組んだ、庭を区切る細い横の柵
- natural_grass_meadow: 草地2の暗い粒を中間の緑へ寄せ、目標画像の草地の明るさへ合わせた128×128の地面
- natural_grass_meadow_light: さらに一段明るい緑にした128×128の地面
"""
import colorsys
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

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
# 屋根の範囲（元画像の画素座標の多角形）。壁・扉・樽を含めないよう、軒の下端と破風の三角を除いて指定する。
ROOF = {
    'natural_farm_house_a': [(0, 0), (224, 0), (224, 131), (210, 131), (143, 78), (102, 127), (0, 127)],
}
# 板葺きの陰影に使う色段の開始位置（青は彩度が強く見えるため一段暗く始める）
SHINGLE_BASE = {'brown': 2, 'red': 2, 'blue': 1}
TARGET = {'natural_farm_house_a': 'natural_wood_house'}
# 草地の置換表。花の色は変えない。
# MEADOW: 暗い粒を中間色へ寄せてざらつきを消し、明るさを目標画像の草地（中央値 RGB 80,108,26 付近）へ合わせる。
MEADOW = {
    (18, 28, 15): (80, 95, 38), (33, 47, 20): (80, 95, 38), (49, 70, 25): (91, 107, 41),
    (70, 79, 35): (91, 107, 41), (80, 95, 38): (91, 107, 41), (91, 107, 41): (101, 123, 42),
}
# MEADOW_LIGHT: さらに主色を一段明るくした、明るい草地。
MEADOW_LIGHT = {
    (18, 28, 15): (91, 107, 41), (33, 47, 20): (91, 107, 41), (49, 70, 25): (101, 123, 42),
    (70, 79, 35): (101, 123, 42), (80, 95, 38): (101, 123, 42), (91, 107, 41): (127, 142, 57),
    (101, 123, 42): (134, 155, 64), (117, 127, 54): (134, 155, 64), (127, 142, 57): (136, 164, 65),
    (134, 155, 64): (136, 164, 65), (136, 164, 65): (163, 182, 84), (153, 162, 78): (163, 182, 84),
    (163, 182, 84): (178, 202, 96), (178, 202, 96): (200, 219, 127),
}


def hsv(c):
    h, s, v = colorsys.rgb_to_hsv(*[x / 255 for x in c])
    return h * 360, s, v


def luma(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def roof_recolor(src):
    image = Image.open(OBJ / f'{src}.png').convert('RGBA')
    a = np.array(image)
    poly = Image.new('1', image.size)
    ImageDraw.Draw(poly).polygon(ROOF[src], fill=1)
    inside = np.array(poly, bool)
    roof = np.zeros(inside.shape, bool)
    for y, x in zip(*np.nonzero(inside & (a[:, :, 3] > 0))):
        h, s, v = hsv(tuple(int(t) for t in a[y, x, :3]))
        roof[y, x] = 10 <= h <= 50 and s >= 0.3 and v >= 0.2
    colors = sorted({tuple(int(t) for t in a[y, x, :3]) for y, x in zip(*np.nonzero(roof))}, key=luma)
    # わらの筋を消すため、周囲11×11画素の平均の明るさで陰影を取り、4段の色で塗る。
    # その上に5画素ごとの段の影と、段ごとに3画素ずらした6画素ごとの継ぎ目を入れて板葺きにする。
    lum = (0.3 * a[:, :, 0] + 0.59 * a[:, :, 1] + 0.11 * a[:, :, 2]).astype(float)
    k = 5
    pad = np.pad(lum, k, mode='edge')
    smooth = np.zeros_like(lum)
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            smooth += pad[k + dy:k + dy + lum.shape[0], k + dx:k + dx + lum.shape[1]]
    smooth /= (2 * k + 1) ** 2
    lo, hi = np.percentile(smooth[roof], 5), np.percentile(smooth[roof], 95)
    outputs = {}
    for name, ramp in RAMPS.items():
        base = SHINGLE_BASE[name]
        b = a.copy()
        for y, x in zip(*np.nonzero(roof)):
            i = int(np.clip((smooth[y, x] - lo) / (hi - lo) * 3.99, 0, 3)) + base
            row, col = y % 5, (x + (y // 5) % 2 * 3) % 6
            if row == 4:
                i -= 2
            elif col == 0:
                i -= 1
            elif row == 0:
                i += 1
            b[y, x, :3] = ramp[int(np.clip(i, 0, len(ramp) - 1))]
        outputs[f'{TARGET[src]}_{name}'] = (Image.fromarray(b), {'source_colors': [list(c) for c in colors], 'ramp': [list(c) for c in ramp], 'shingle_base': base, 'roof_pixels': int(roof.sum())})
    return outputs


def fenced_flowerbed():
    corner = Image.open(OBJ / 'natural_fence_corner.png').convert('RGBA')
    dirt = Image.open(TILE / 'natural_dirt.png').convert('RGBA')
    flowers = [Image.open(OBJ / f'natural_flowers_{c}.png').convert('RGBA') for c in ('pink', 'white', 'yellow')]
    bush = Image.open(OBJ / 'natural_flowerbed.png').convert('RGBA')
    rail_h = corner.crop((8, 2, 21, 12))       # 横の2本の横木（13×10）
    rail_v = corner.crop((25, 13, 31, 22))     # 縦の2本の横木（6×9）
    post = corner.crop((1, 2, 6, 13))          # 小さな杭（5×11）
    out = Image.new('RGBA', (96, 96))
    # 中の土と花
    soil = dirt.crop((0, 0, 84, 76))
    out.alpha_composite(soil, (6, 10))
    out.alpha_composite(bush.crop((4, 4, 92, 50)), (4, 12))
    for i, (x, y) in enumerate([(6, 44), (32, 46), (58, 44), (18, 58), (46, 60)]):
        out.alpha_composite(flowers[i % 3].crop((0, 6, 32, 30)), (x, y))
    # 柵の枠：上下は横木、左右は縦木、角と中ほどに杭
    for x in range(4, 88, 13):
        piece = rail_h if x + 13 <= 92 else rail_h.crop((0, 0, 92 - x, 10))
        out.alpha_composite(piece, (x, 4))
        out.alpha_composite(piece, (x, 82))
    for y in range(12, 84, 9):
        piece = rail_v if y + 9 <= 86 else rail_v.crop((0, 0, 6, 86 - y))
        out.alpha_composite(piece, (1, y))
        out.alpha_composite(piece, (89, y))
    for x, y in [(1, 1), (90, 1), (1, 79), (90, 79), (46, 1), (46, 79), (1, 40), (90, 40)]:
        out.alpha_composite(post, (x, y))
    return out, {'components': ['assets/objects/natural_fence_corner.png', 'assets/tiles/natural_dirt.png', 'assets/objects/natural_flowerbed.png', 'assets/objects/natural_flowers_pink.png', 'assets/objects/natural_flowers_white.png', 'assets/objects/natural_flowers_yellow.png']}


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
    for src in ROOF:
        for name, (image, info) in roof_recolor(src).items():
            built[f'assets/objects/{name}.png'] = (image, dict(info, base=f'assets/objects/{src}.png', roof_polygon=ROOF[src]))
    image, info = fenced_flowerbed()
    built['assets/objects/natural_fenced_flowerbed.png'] = (image, info)
    built['assets/objects/natural_fence_low_horizontal.png'] = (low_fences(), {'components': ['assets/objects/natural_fence_corner.png']})
    for name, table in [('natural_grass_meadow', MEADOW), ('natural_grass_meadow_light', MEADOW_LIGHT)]:
        image, info = meadow(table)
        built[f'assets/tiles/{name}.png'] = (image, dict(info, base='assets/tiles/natural_grass_2.png'))
    record = {'tool': 'tools/build_castle_town_polish_assets.py', 'generated_at': '2026-09-28', 'method': '画像生成なし。登録済み素材の画素を natural.gpl 内の色へ置換・切り貼りした決定論的な派生素材。', 'outputs': {}}
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
            'modified': '城下町の仕上げ用。画像生成なし。登録済み素材の画素をnatural.gpl内の色へ置換・切り貼りした決定論的派生。アルファ二値。',
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
