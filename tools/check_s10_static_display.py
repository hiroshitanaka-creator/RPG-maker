#!/usr/bin/env python3
"""083採用固定bytes、素材制約、出所許可の正負例。原画は一切書き込まない。"""
import copy
import hashlib
import json
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from PIL import Image
import validate_assets as validator
from import_s10_ner_static import reproduce

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png'
SOURCE_SHA = '7fb285a7c31839ff33350c328f39dfd97e94ea57a0fe6567ef862f8fb19a9aa5'
SPRITE = 'assets/characters/ner/event_standing.png'
ADOPTED_SHA = '121010a316a31b88dca753ed48bc9404f176a4fe5f0d6dd5508ebf0615559f5d'
PREVIEW = 'docs/verification/s10-placement-preview/ner-static-proposal.png'
BASE = 'a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf'
checks = []

def sha(data): return hashlib.sha256(data).hexdigest()
def check(ok, label):
    checks.append({'ok': bool(ok), 'label': label})
    if not ok: print('S10_ASSET_FAIL:', label)

def image_errors(im):
    im = im.convert('RGBA')
    palette = validator.load_palette(ROOT/'assets/palette/natural.gpl')
    pixels = np.array(im)
    colors = {tuple(p) for p in pixels[:,:,:3][pixels[:,:,3]>0]}
    return [name for ok,name in [
        (im.size == (32,48),'size'),
        (set(np.unique(pixels[:,:,3])) <= {0,255},'alpha'),
        (len(colors)<=16,'colors'), (colors<=palette,'palette'),
        (im.getbbox() is not None and im.getbbox()[3] == 48,'ground')
    ] if not ok]

def main():
    check(sha((ROOT/SOURCE).read_bytes())==SOURCE_SHA, '採用原画のSHA固定')
    check(Image.open(ROOT/SOURCE).size==(1152,1728), '原画の寸法固定')
    check(sha((ROOT/PREVIEW).read_bytes())==ADOPTED_SHA, '参照PNGのSHA固定')
    check(sha((ROOT/PREVIEW).read_bytes()+b'changed')!=ADOPTED_SHA, '採用PNGの改変SHAを拒否')
    with tempfile.TemporaryDirectory() as temp:
        bad=Path(temp)/'changed.png';bad.write_bytes((ROOT/SOURCE).read_bytes()+b'changed')
        try:
            reproduce(bad)
        except AssertionError:
            check(True,'再現scriptは改変原画を出力前に拒否')
        else:
            check(False,'再現scriptは改変原画を出力前に拒否')
    for path in ['tools/preview_s10_placement.py']+['docs/verification/s10-placement-preview/'+x for x in ['README.md','manifest.json','comparison.png','source-comparison.png','placement-A.png','placement-B.png','ner-static-proposal.png']]:
        check((ROOT/path).read_bytes()==subprocess.check_output(['git','show','d46151a633a2b5701bf0c583bf01344f39095929:'+path],cwd=ROOT), '参照commitのbytes保持: '+path)
    good = Image.open(ROOT/PREVIEW).convert('RGBA')
    check(not image_errors(good), '採用PNGの全画像制約')
    variants = []
    variants.append(('size',good.crop((0,0,31,48))))
    bad=good.copy();bad.putpixel((0,0),(0,0,0,128));variants.append(('alpha',bad))
    bad=good.copy();bad.putpixel((0,0),(1,2,3,255));variants.append(('palette',bad))
    bad=good.copy()
    for i in range(17):bad.putpixel((i,0),(i,0,0,255))
    variants.append(('colors',bad))
    bad=good.copy()
    for x in range(32):bad.putpixel((x,47),(0,0,0,0))
    variants.append(('ground',bad))
    for expected,im in variants:check(expected in image_errors(im), '負例の拒否: '+expected)
    reg=json.loads((ROOT/'assets/registry.json').read_text())
    matches=[e for e in reg['assets'] if e['path']==SPRITE]
    check(len(matches)==1,'台帳の登録は1件')
    if matches:
        e=matches[0]
        check(e.get('kind')=='character_event' and e.get('frame')==[32,48] and e.get('grid')==[1,1] and e.get('max_colors')==16 and e.get('palette')=='assets/palette/natural.gpl','静止1枚として台帳登録')
        check(not validator.check_provenance(e),'固定原画のowner出所を許可')
        bad=copy.deepcopy(e);bad['original_file']='assets/_incoming/owner-2026-10-05-grok-batch3/ner-oasis-shrine-keeper-concept.png'
        check(bool(validator.check_provenance(bad)),'未採用concept原画は拒否')
        for path in ['assets/_incoming/owner-2026-10-05-grok-batch3/../owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png','assets/_incoming/unapproved.png']:
            bad=copy.deepcopy(e);bad['original_file']=path
            check(bool(validator.check_provenance(bad)),'誤path拒否: '+path)
        # コピー先の検証rootだけで改変原画を再現。本番原画を変更しない。
        with tempfile.TemporaryDirectory() as temp:
            original_root=validator.REPO_ROOT
            validator.REPO_ROOT=Path(temp)
            p=Path(temp)/SOURCE;p.parent.mkdir(parents=True);p.write_bytes((ROOT/SOURCE).read_bytes()+b'changed')
            check(bool(validator.check_provenance(e)),'固定pathでも改変原画SHAを拒否')
            validator.REPO_ROOT=original_root
    check((ROOT/SPRITE).exists(),'本番静止PNGが存在')
    if (ROOT/SPRITE).exists():
        check((ROOT/SPRITE).read_bytes()==(ROOT/PREVIEW).read_bytes(),'本番PNGは採用bytesそのもの')
        check(not image_errors(Image.open(ROOT/SPRITE)),'本番PNGの全画像制約')
    old=json.loads(subprocess.check_output(['git','show',BASE+':assets/registry.json'],cwd=ROOT))
    filtered=copy.deepcopy(reg);filtered['assets']=[e for e in reg['assets'] if e['path']!=SPRITE]
    check(filtered==old,'既存台帳の全項目・順序不変')
    before=json.loads(subprocess.check_output(['git','show',BASE+':world/region2_village.json'],cwd=ROOT))
    current=json.loads((ROOT/'world/region2_village.json').read_text())
    added=[e for e in current['site']['rooms'][4]['events'] if e.get('display_only')]
    check(len(added)==1,'表示専用イベントは1件')
    filtered=copy.deepcopy(current);filtered['site']['rooms'][4]['events']=[e for e in filtered['site']['rooms'][4]['events'] if not e.get('display_only')]
    check(filtered==before,'既存人物・台詞・全扉・入口・出口不変')
    # 依頼対象原画2点と082本文を基点とバイト照合。
    originals=[ROOT/SOURCE, ROOT/'assets/_incoming/owner-2026-10-05-grok-batch3/ner-oasis-shrine-keeper-concept.png']
    check(len(originals)==2,'保持対象原画2点')
    for p in originals+[ROOT/'data/region2_shrine_scenes.json']:
        rel=p.relative_to(ROOT).as_posix()
        check(p.read_bytes()==subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT),'原画/082本文bytes不変: '+rel)
    out=ROOT/'docs/verification/task-083/asset-checks.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'checks':checks},ensure_ascii=False,indent=2)+'\n')
    failed=sum(not x['ok'] for x in checks)
    print(f'S10_ASSET_{"PASS" if not failed else "FAIL"}: checks={len(checks)} failures={failed}')
    return bool(failed)

if __name__=='__main__':raise SystemExit(main())
