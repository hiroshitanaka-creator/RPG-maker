"""地面を広くした依頼者の8原画を、原本不変で戦闘背景へ取り込む。"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from validate_assets import load_palette

ROOT = Path(__file__).resolve().parent.parent
MAPPING = [('castle', '城'), ('sky', '空'), ('sea', '海'), ('desert', '砂漠'),
           ('tower', '塔'), ('cave', '洞窟'), ('forest', '森'), ('plains', '平原')]
ORIGINALS = Path('assets/_incoming/owner-2026-09-26/ground-backgrounds-2026-09-27')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, help='初回だけ、添付の原画フォルダを指定')
    args = parser.parse_args()
    folder = ROOT / ORIGINALS
    folder.mkdir(parents=True, exist_ok=True)
    registry_file = ROOT / 'assets/registry.json'
    registry = json.loads(registry_file.read_text(encoding='utf-8'))
    palette_path = 'assets/palette/natural.gpl'
    colors = sorted(load_palette(ROOT / palette_path))
    palette = Image.new('P', (1, 1))
    palette.putpalette([v for color in (colors * 4)[:256] for v in color])
    records = []
    for i, (identifier, name) in enumerate(MAPPING, 1):
        filename = f'{i}-写真{i}.jpg'
        original = folder / filename
        if args.source_dir:
            data = (args.source_dir / filename).read_bytes()
            if original.exists() and original.read_bytes() != data:
                raise ValueError(f'保存済み原本を上書きしません: {filename}')
            original.write_bytes(data)
        before = sha(original.read_bytes())
        image = Image.open(original).convert('RGB')
        original_size = image.size
        output = f'assets/backgrounds/{identifier}.png'
        image = image.resize((512, 288), Image.Resampling.NEAREST)
        image.quantize(palette=palette, dither=Image.Dither.NONE).convert('RGBA').save(ROOT / output)
        assert sha(original.read_bytes()) == before
        record = {'id': identifier, 'name': name, 'original_file': (ORIGINALS / filename).as_posix(),
                  'original_sha256': before, 'original_size': original_size,
                  'output': output, 'output_sha256': sha((ROOT / output).read_bytes()),
                  'conversion': '原画全体を512×288へ最近傍変換しnatural.gplへ減色。切り抜き・色調補正なし。'}
        records.append(record)
        entry = next(e for e in registry['assets'] if e['path'] == output)
        entry.update({'source': 'owner', 'author': '依頼者', 'license': 'LicenseRef-Owner-Provided',
                      'provided_at': '2026-09-27', 'original_file': record['original_file'],
                      'palette': palette_path, 'modified': record['conversion']})
        # 旧生成原画の出所を新原画の出所として残さない。
        for key in ['source_url', 'retrieved_at', 'tool', 'generated_at', 'prompt_file', 'prompt_record']:
            entry.pop(key, None)
    registry_file.write_text(json.dumps(registry, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (ROOT / 'assets/source_records/ground-backgrounds.json').write_text(
        json.dumps({'provided_at': '2026-09-27', 'source': '依頼者が前回予告した差替原画8枚。今回のメッセージでは生成サービスの明記なし。',
                    'backgrounds': records}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (folder / 'README.md').write_text(
        '# 地面を広くした戦闘背景の原本\n\n2026年9月27日に依頼者が差替用として添付した8枚。'
        '元のバイトを保存している。生成サービスは今回の添付メッセージでは明記されていない。\n\n'
        '対応とSHA-256は `assets/source_records/ground-backgrounds.json` に記録。'
        '変換は `python tools/import_ground_backgrounds.py` で再現する。\n', encoding='utf-8')
    print('GROUND_BACKGROUNDS_PASS: originals=8 unchanged=8 converted=8 size=512x288')


if __name__ == '__main__':
    main()
