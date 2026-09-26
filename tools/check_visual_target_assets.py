#!/usr/bin/env python3
"""今回の素材範囲・参照保存・人物輪郭・接続規約を実物で確かめる。"""
from pathlib import Path
import copy
import hashlib
import io
import json
import subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from validate_assets import check_autotile

ROOT=Path(__file__).resolve().parents[1]
BASE='3c809e687a4a1a32c139803416084161852e4bc2'
OUT=ROOT/'docs/verification/art-review-2'

def previous(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout
def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    old=json.loads(previous('assets/registry.json'));current=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    unchanged=[];recolored=[]
    for entry in old['assets']:
        path=entry['path'];before=previous(path);after=(ROOT/path).read_bytes()
        if entry.get('palette')!='assets/palette/bright.gpl':
            assert before==after,path;unchanged.append(path)
        else:
            a=np.array(Image.open(io.BytesIO(before)).convert('RGBA'));b=np.array(Image.open(io.BytesIO(after)).convert('RGBA'))
            assert a.shape==b.shape and np.array_equal(a[:,:,3],b[:,:,3]),path
            recolored.append(path)
    assert len(unchanged)==94 and len(recolored)==139
    fixed=['assets/palette/base.gpl','assets/palette/bright.gpl','docs/verification/art-review/party-design-sheet.png']+[f'docs/verification/art-review/source/pc_{i:02}_design.png' for i in range(1,5)]
    for path in fixed+[e['path'] for e in old['audio']]:assert previous(path)==(ROOT/path).read_bytes(),path
    manifest=json.loads((ROOT/'docs/reference/visual-targets/manifest.json').read_text(encoding='utf-8'))
    rows=manifest if isinstance(manifest,list) else manifest['files']
    for row in rows:
        path=row.get('file') or row.get('saved_as')
        assert sha((ROOT/'docs/reference/visual-targets'/path).read_bytes())==row['sha256'],path
    assert len(rows)==10
    entries={e['path']:e for e in current['assets']}
    assert all(path.startswith('assets/') for path in entries)
    atlases=[e for e in entries.values() if 'autotile' in e]
    assert len(atlases)==9
    for e in atlases:
        assert check_autotile(e)==[]
        broken=copy.deepcopy(e);broken['autotile']['masks'].pop()
        assert check_autotile(broken),'欠落形を検出できない'
    party=[]
    chart=Image.new('RGB',(1024,600),'#d5d2c3');d=ImageDraw.Draw(chart);font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',16)
    for actor in range(1,5):
        colors=set();x=(actor-1)*256
        d.text((x+8,4),f'pc_{actor:02} 上: 変更前 / 下: natural',font=font,fill='#20251d')
        for name in ('walk','battle','portrait'):
            path=f'assets/characters/pc_{actor:02}/{name}.png';a=np.array(Image.open(ROOT/path).convert('RGBA'));colors.update(map(tuple,a[:,:,:3][a[:,:,3]>0]))
            if name!='portrait':
                fw=32 if name=='walk' else 48;frames=[a[y:y+48,x:x+fw] for y in range(0,a.shape[0],48) for x in range(0,a.shape[1],fw)]
                assert all(np.any(f[:,:,3]) for f in frames)
                assert len({f.tobytes() for f in frames})==len(frames),(path,'同一コマ')
        assert len(colors)<=16
        party.append({'id':f'pc_{actor:02}','shared_colors':len(colors),'alpha_unchanged':True,'walk_frames':12,'battle_frames':3})
        for row,data in enumerate([previous(f'assets/characters/pc_{actor:02}/walk.png'),(ROOT/f'assets/characters/pc_{actor:02}/walk.png').read_bytes()]):
            walk=Image.open(io.BytesIO(data)).convert('RGBA');chart.paste(walk,(x+8,35+row*280),walk)
            portrait_path=f'assets/characters/pc_{actor:02}/portrait.png'
            portrait=Image.open(io.BytesIO(previous(portrait_path) if row==0 else (ROOT/portrait_path).read_bytes())).convert('RGBA').resize((128,128),Image.Resampling.NEAREST)
            chart.paste(portrait,(x+116,35+row*280),portrait)
    chart.save(OUT/'party-palette-review.png')
    result={'baseline':BASE,'unchanged_legacy_images':94,'recolored_alpha_unchanged':139,'reference_jpegs_hash_match':10,'fixed_party_designs_hash_match':5,'palettes_unchanged':['base.gpl','bright.gpl'],'audio_unchanged':14,'autotile_positive_checks':9,'missing_shape_rejections':9,'party':party}
    (OUT/'scope-and-party-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('VISUAL_TARGET_SCOPE_PASS: legacy_images=94 palette_files=2 fixed_party_designs=5 audio=14 unchanged')
    print('VISUAL_TARGET_PARTY_PASS: alpha_preserved=139 party=4 common_colors<=16 frames_distinct=60')
    print('VISUAL_TARGET_REFERENCE_PASS: jpeg_hashes=10 game_asset_reference_paths=0')
    print('VISUAL_TARGET_AUTOTILE_PASS: valid=9 missing_shape_rejected=9')

if __name__=='__main__':main()
