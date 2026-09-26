"""ゲームと同じ規則で実行版IDを計算する。"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_ENGINE = '4.7.2-stable (official) [ed1daf0bf]'

def identity(engine: str, root: Path = ROOT) -> dict:
    paths = ['project.godot','assets/registry.json','assets/palette/base.gpl']
    for folder in ['scripts','scenes','data','world']:
        paths.extend(p.relative_to(root).as_posix() for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ['.gd','.tscn','.json'])
    paths.extend(e['path'] for e in json.loads((root/'assets/registry.json').read_text(encoding='utf-8'))['assets'])
    paths.append('assets/palette/bright.gpl')
    paths.append('assets/palette/natural.gpl')
    paths.extend(e['path'] for e in json.loads((root/'assets/registry.json').read_text(encoding='utf-8')).get('audio', []))
    paths.sort()
    payload = 'rpg-v1-build-1\n'+engine+'\n'
    payload += ''.join(p+'\t'+hashlib.sha256((root/p).read_bytes()).hexdigest()+'\n' for p in paths)
    return {'version':1,'id':hashlib.sha256(payload.encode('utf-8')).hexdigest(),'engine':engine,'files':len(paths)}
