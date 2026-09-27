"""Google Fontsの固定コミットから候補字体とOFL原文を未加工で取り込む。"""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
FONTS = [('notosansjp', 'NotoSansJP%5Bwght%5D.ttf', 'NotoSansJP.ttf', 'Noto Sans JP'),
         ('dotgothic16', 'DotGothic16-Regular.ttf', 'DotGothic16-Regular.ttf', 'DotGothic16')]


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'RPG-maker-font-import'}), timeout=60).read()


def main():
    record_path = ROOT / 'assets/source_records/battle-fonts.json'
    if record_path.exists():
        revision = json.loads(record_path.read_text(encoding='utf-8'))['revision']
    else:
        revision = json.loads(fetch('https://api.github.com/repos/google/fonts/commits/main'))['sha']
    entries = []
    for folder, remote, local, title in FONTS:
        base = f'https://raw.githubusercontent.com/google/fonts/{revision}/ofl/{folder}/'
        font_data, license_data = fetch(base + remote), fetch(base + 'OFL.txt')
        assert font_data[:4] in [b'\x00\x01\x00\x00', b'OTTO']
        assert b'SIL OPEN FONT LICENSE Version 1.1' in license_data
        destination = ROOT / 'assets/fonts' / folder
        destination.mkdir(parents=True, exist_ok=True)
        (destination / local).write_bytes(font_data)
        (destination / 'OFL.txt').write_bytes(license_data)
        entries.append({'id': folder, 'name': title, 'usage': 'game_default' if folder == 'notosansjp' else 'comparison_archive', 'path': (destination / local).relative_to(ROOT).as_posix(),
                        'kind': 'font', 'source': 'external',
                        'source_url': f'https://github.com/google/fonts/tree/{revision}/ofl/{folder}',
                        'download_url': base + remote, 'author': license_data.decode('utf-8').splitlines()[0],
                        'license': 'OFL-1.1', 'license_path': (destination / 'OFL.txt').relative_to(ROOT).as_posix(),
                        'retrieved_at': '2026-09-27', 'modified': 'なし。字体・ライセンス原文のバイト列を保持。',
                        'sha256': hashlib.sha256(font_data).hexdigest(), 'license_sha256': hashlib.sha256(license_data).hexdigest()})
    record_path.write_text(json.dumps({'revision': revision, 'adopted_font': 'notosansjp', 'adopted_at': '2026-09-27', 'fonts': entries}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    registry_path = ROOT / 'assets/registry.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    registry['fonts'] = entries
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'BATTLE_FONTS_IMPORTED: count=2 revision={revision} originals_unmodified=true')


if __name__ == '__main__':
    main()
