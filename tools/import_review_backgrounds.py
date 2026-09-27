"""依頼された14背景の確認用に、保管済みの残り6原画を素材規約へ変換する。"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageEnhance
from validate_assets import load_palette

ROOT = Path(__file__).resolve().parent.parent
BACKGROUNDS = {
    'Z0Wjp.jpg': ('snowfield', '雪原', 75,250,1.05,1.30,1.05),
    'gFbVF.jpg': ('volcano', '火山', 20,240,1.00,1.10,1.05),
    'zBjGj.jpg': ('ruins', '遺跡', 65,245,1.15,1.25,1.08),
    'lYiti.jpg': ('underworld', '死者の国', 100,255,1.30,0.90,1.07),
    'mUou6.jpg': ('temple', '神殿の中', 12,245,1.12,1.20,1.10),
    'edM34.jpg': ('final_land', '最後の地', 145,255,1.05,1.22,1.03),
}


def main():
    registry_path = ROOT / 'assets/registry.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    palette_path = 'assets/palette/natural.gpl'
    colors = sorted(load_palette(ROOT / palette_path))
    palette = Image.new('P', (1, 1))
    palette.putpalette([v for color in (colors * 4)[:256] for v in color])
    records = []
    for filename, (identifier, title, black, white, gamma, saturation, contrast) in BACKGROUNDS.items():
        original = f'assets/_incoming/owner-2026-09-26/background-replacement-2026-09-27/{filename}'
        source = ROOT / original
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        destination = f'assets/backgrounds/{identifier}.png'
        image = Image.open(source).convert('RGB')
        dimensions = image.size
        levels = [round(255 * (min(1.0,max(0.0,(v-black)/(white-black))) ** gamma)) for v in range(256)]
        image = image.point(levels * 3)
        image = ImageEnhance.Color(image).enhance(saturation)
        image = ImageEnhance.Contrast(image).enhance(contrast)
        image = image.resize((512, 288), Image.Resampling.NEAREST)
        image.quantize(palette=palette, dither=Image.Dither.NONE).convert('RGBA').save(ROOT / destination)
        assert hashlib.sha256(source.read_bytes()).hexdigest() == before
        entry = {'path': destination, 'kind': 'battle_background', 'size': [512, 288],
                 'max_colors': 64, 'status': 'required', 'palette': palette_path,
                 'source': 'owner', 'author': '依頼者', 'license': 'LicenseRef-Owner-Provided',
                 'provided_at': '2026-09-27', 'original_file': original,
                 'modified': f'新原画全体を512×288へ最近傍変換。レベル黒{black}/白{white}、ガンマ{gamma}、彩度{saturation}、コントラスト{contrast}で白い霞を調整し、natural.gplへ減色。原本・既存8背景は不変。後続地方への接続は未実施。'}
        index = next((i for i, e in enumerate(registry['assets']) if e['path'] == destination), None)
        if index is None: registry['assets'].append(entry)
        else: registry['assets'][index] = entry
        records.append({'id': identifier, 'name': title, 'original_file': original,
                        'original_size': dimensions, 'original_sha256': before,
                        'adjustment': {'black':black,'white':white,'gamma':gamma,'saturation':saturation,'contrast':contrast},
                        'output': destination, 'output_sha256': hashlib.sha256((ROOT / destination).read_bytes()).hexdigest()})
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'assets/source_records/review-backgrounds.json').write_text(
        json.dumps({'purpose': '14背景の配置確認。後続地方の実装・接続ではない', 'backgrounds': records}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('REVIEW_BACKGROUNDS_PASS: 原本不変6件、512×288変換6件')


if __name__ == '__main__':
    main()
