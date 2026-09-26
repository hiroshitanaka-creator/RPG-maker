#!/usr/bin/env python3
"""新絵柄139枚の輪郭・色数上限を保つ。仲間は各人の共通色で一対一対応。"""
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from build_natural_palette import lab, hsv, assignment
from validate_assets import load_palette

ROOT=Path(__file__).resolve().parents[1]
BASELINE='3c809e687a4a1a32c139803416084161852e4bc2'

def main():
    registry_path=ROOT/'assets/registry.json'
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    baseline=json.loads(subprocess.run(['git','show',BASELINE+':assets/registry.json'],cwd=ROOT,capture_output=True,check=True).stdout)
    for entry in baseline['assets']:
        if entry.get('palette')!='assets/palette/bright.gpl':continue
        backup=ROOT/'.tools/natural-originals'/entry['path']
        if not backup.exists():
            backup.parent.mkdir(parents=True,exist_ok=True)
            backup.write_bytes(subprocess.run(['git','show',BASELINE+':'+entry['path']],cwd=ROOT,capture_output=True,check=True).stdout)
    palette=np.array(sorted(load_palette(ROOT/'assets/palette/natural.gpl')),dtype=np.int32)
    def match(colors,unique=False,silver=False,terrain=False):
        colors=np.array(colors,dtype=np.int32)
        target=colors.copy()
        if terrain:
            # 旧bright地形の蛍光色を明度ごと引き継がず、葉は自然な中間色へ。
            # 石の青い陰は低彩度に戻し、自然色の灰色に対応させる。
            th,ts,tv=hsv(target)
            green=(th>=.16)&(th<.47)&(ts>.3)
            target[green]=np.rint(target[green]*np.minimum(1,.62/np.maximum(tv[green],.01))[:,None])
            blue=(th>=.47)&(th<.72)&('mountains' in str(terrain))
            gray=target[blue].mean(axis=1)
            target[blue]=np.rint(target[blue]*.18+gray[:,None]*.82)
        cost=((lab(target)[:,None,:]-lab(palette)[None,:,:])**2).sum(axis=2)
        h,s,_=hsv(target);ph,ps,_=hsv(palette)
        delta=np.abs(h[:,None]-ph[None,:]);delta=np.minimum(delta,1-delta)
        cost+=((delta>.15)&(s[:,None]>.3)&(ps[None,:]>.3))*10000
        if silver:
            hair={tuple(bytes.fromhex(h)) for h in ('55718B','87A0AE','BECED1','E7EFF0')}
            for i,color in enumerate(colors):
                if tuple(color) in hair:cost[i,ps>.2]+=1000000
        selected=assignment(cost) if unique else cost.argmin(axis=1)
        return {tuple(c):palette[i] for c,i in zip(colors,selected)}
    party_luts={}
    for actor in range(1,5):
        values=set()
        for name in ('walk','battle','portrait'):
            a=np.array(Image.open(ROOT/f'.tools/natural-originals/assets/characters/pc_{actor:02}/{name}.png').convert('RGBA'))
            values.update(map(tuple,a[:,:,:3][a[:,:,3]>0]))
        party_luts[f'pc_{actor:02}']=match(sorted(values),True,actor==3)
    results=[]
    for entry in registry['assets']:
        if entry.get('palette') not in ('assets/palette/bright.gpl','assets/palette/natural.gpl'):
            continue
        rel=entry['path'];backup=ROOT/'.tools/natural-originals'/rel
        if not backup.is_file():
            continue  # 新規素材はこの再配色の対象外。
        before=np.asarray(Image.open(backup).convert('RGBA'))
        after=before.copy();opaque=before[:,:,3]>0
        colors=np.unique(before[:,:,:3][opaque],axis=0)
        actor=Path(rel).parent.name
        lut=party_luts.get(actor) or match(colors,terrain=rel if rel.startswith('assets/tiles/') else '')
        for color in colors:
            mask=opaque&np.all(before[:,:,:3]==color,axis=2)
            after[:,:,:3][mask]=lut[tuple(color)]
        assert np.array_equal(before[:,:,3],after[:,:,3])
        after_count=len(np.unique(after[:,:,:3][opaque],axis=0))
        assert after_count<=len(colors)
        Image.fromarray(after).save(ROOT/rel)
        entry['palette']='assets/palette/natural.gpl'
        old_note='2026-09-26: natural.gplへの一対一再配色。寸法・輪郭・透過・色数・コマ配置は維持。'
        entry['modified']=entry.get('modified','').replace(old_note,'').strip()
        note='2026-09-26: natural.gplへ色相を保って再配色。寸法・輪郭・透過・コマ配置と色数上限は維持。仲間は各人の共通16色内で一対一対応。'
        if note not in entry.get('modified',''):
            entry['modified']=entry.get('modified','')+' '+note
        results.append({'path':rel,'before_colors':len(colors),'after_colors':after_count,'alpha_unchanged':True,'before_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()})
    assert len(results)==139,len(results)
    for actor in range(1,5):
        common=set()
        for name in ('walk','battle','portrait'):
            a=np.asarray(Image.open(ROOT/f'assets/characters/pc_{actor:02}/{name}.png').convert('RGBA'))
            common.update(map(tuple,a[:,:,:3][a[:,:,3]>0]))
        assert len(common)<=16,(actor,len(common))
    registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'docs/verification/art-review-2/requantization.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('REQUANTIZE_PASS: images=139 alpha_unchanged=139 color_limits_preserved=139 party_common_colors<=16')

if __name__=='__main__':main()
