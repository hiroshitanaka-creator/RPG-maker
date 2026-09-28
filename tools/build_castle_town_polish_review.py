#!/usr/bin/env python3
"""城下町の仕上げ（採用した案Bと、その修正）の比較画像を作る。

入力はすべて実際のゲームで撮った画像：
- variant-X/full-town.png : 本番の描画クラス FirstRegionView で城下町全体を1枚に描いたもの（tools/capture_castle_town_full.gd）
- variant-X/runtime/*.png  : 新規開始から通常入力で城下町まで歩いた実画面（tools/capture_castle_town.gd）
目標の絵（依頼者原画 IMG_0997 の複製）は比較の左に置くだけで、ゲーム素材には使わない。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/verification/castle-town-polish'
TARGET = ROOT / 'docs/reference/visual-targets/first-castle-town.png'
BEFORE = OUT / 'before-full-town.png'
FONT = ImageFont.truetype(str(ROOT / 'assets/fonts/notosansjp/NotoSansJP.ttf'), 22)
SMALL = ImageFont.truetype(str(ROOT / 'assets/fonts/notosansjp/NotoSansJP.ttf'), 18)
TITLES = {
    'B': '案B（採用）を修正：切妻屋根・大きな木の固まり・細い道・花で埋めたL字花壇',
}
ADOPTED = OUT / 'variant-B/adopted-full-town.png'  # 依頼者が採用した時点（20fdaab）の本番描画
BG = '#d6d2bb'
INK = '#14212b'


def fit(path, box):
    im = Image.open(path).convert('RGB')
    im.thumbnail(box, Image.Resampling.LANCZOS if im.width > box[0] * 1.5 else Image.Resampling.NEAREST)
    return im


def pair(left, left_label, right, right_label, title, out):
    canvas = Image.new('RGB', (1536, 640), BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 6), title, font=FONT, fill=INK)
    for i, (path, label) in enumerate([(left, left_label), (right, right_label)]):
        im = fit(path, (752, 552))
        x = i * 768 + (768 - im.width) // 2
        canvas.paste(im, (x, 76))
        draw.text((i * 768 + 12, 42), label, font=SMALL, fill=INK)
    canvas.save(out)


def main():
    variants = [v for v in 'B' if (OUT / f'variant-{v}/full-town.png').exists()]
    pair(TARGET, '依頼者の目標画像 IMG_0997', BEFORE, '変更前（07ac451）の本番描画', '変更前と目標', OUT / 'before-comparison.png')
    for v in variants:
        d = OUT / f'variant-{v}'
        pair(TARGET, '依頼者の目標画像 IMG_0997', d / 'full-town.png', '本番描画（FirstRegionView）で城下町全体', TITLES[v], d / 'comparison.png')
        shots = [d / 'runtime' / f'{n}.png' for n in ('02a-town-gate', '02-town-plaza', '02b-town-southwest', '02c-town-northeast')]
        shots = [s for s in shots if s.exists()]
        if shots:
            canvas = Image.new('RGB', (1040, 60 + 300 * ((len(shots) + 1) // 2)), BG)
            draw = ImageDraw.Draw(canvas)
            draw.text((12, 12), '修正後の案B — 通常操作で歩いた実ゲーム画面（512×288を等倍）', font=SMALL, fill=INK)
            for i, s in enumerate(shots):
                im = Image.open(s).convert('RGB').resize((512, 288), Image.Resampling.BOX)
                canvas.paste(im, (8 + (i % 2) * 520, 48 + (i // 2) * 300))
            canvas.save(d / 'runtime-sheet.png')
    pair(ADOPTED, '採用時の案B（20fdaab）', OUT / 'variant-B/full-town.png', '修正後', '採用時と修正後', OUT / 'variant-B/adopted-vs-revised.png')
    # 目標・変更前・採用時・修正後の一覧
    cells = [(TARGET, '目標 IMG_0997'), (BEFORE, '変更前（07ac451）'), (ADOPTED, '採用時の案B（20fdaab）'), (OUT / 'variant-B/full-town.png', '修正後')]
    cw, ch = 760, 580
    canvas = Image.new('RGB', (cw * 2, 30 + ch * ((len(cells) + 1) // 2)), BG)
    draw = ImageDraw.Draw(canvas)
    for i, (path, label) in enumerate(cells):
        x, y = (i % 2) * cw, 30 + (i // 2) * ch
        im = fit(path, (cw - 16, ch - 44))
        canvas.paste(im, (x + (cw - im.width) // 2, y + 36))
        draw.text((x + 10, y + 4), label, font=SMALL, fill=INK)
    canvas.save(OUT / 'overview.png')
    print('CASTLE_POLISH_REVIEW_PASS: variants=' + ''.join(variants))


if __name__ == '__main__':
    main()
