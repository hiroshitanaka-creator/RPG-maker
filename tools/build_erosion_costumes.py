"""48衣装の侵蝕を準備する。規約承認前は確認用の下書きだけを保存する。"""
import argparse,json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
from prepare_erosion_costume_anchors import ROOT,OUT,JOBS,NAMES
from build_erosion_pattern_preview import NODES as ADOPTED_NODES

COLORS={
'pc_01':['5D98C4','BDC7D3','EEF6EB'],
'pc_02':['BF694D','D09279','EEF6EB'],
'pc_03':['CE9F54','D7B778','EEF6EB'],
'pc_04':['A778DE','BDC7D3','EEF6EB']}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def overlay_for(base,frames,kind,stage,actor):
    w,h=(96,96) if kind=='battle' else (32,48)
    rgb=[tuple(int(c[i:i+2],16) for i in (0,2,4)) for c in COLORS[actor]]
    mask=Image.new('RGBA',base.size);parts=[]
    for i,nodes in enumerate(frames):
        body=np.array(base.crop((i%3*w,i//3*h,(i%3+1)*w,(i//3+1)*h)));opaque=body[:,:,3]>0
        local=Image.new('RGBA',(w,h));counts={}
        if stage==60:
            edge=opaque&~ndimage.binary_erosion(opaque,iterations=1)
            rim=opaque&~ndimage.binary_erosion(opaque,iterations=2 if kind=='battle' else 1)
            a=np.array(local);a[rim]=rgb[1]+(255,);a[edge]=rgb[0]+(255,);local=Image.fromarray(a)
        for part in ['cheek','arm']+(['neck','other_arm'] if stage==60 else []):
            points=nodes[part]
            if not points:continue
            layer=Image.new('RGBA',(w,h));d=ImageDraw.Draw(layer)
            d.line([tuple(p) for p in points],fill=rgb[0]+(255,),width=5 if kind=='battle' else 3)
            d.line([tuple(p) for p in points],fill=rgb[2]+(255,),width=2 if kind=='battle' else 1)
            a=np.array(layer);a[~opaque]=0
            # 顔の上側にある目を模様で覆わない。頬は下側の帯に限定する。
            if part=='cheek' and 'head_box' in nodes:
                x1,y1,x2,y2=nodes['head_box'];cut=int(y1+(y2-y1)*.55)
                a[:cut]=0
            counts[part]=int((a[:,:,3]>0).sum());local.alpha_composite(Image.fromarray(a))
        a=np.array(local);a[~opaque]=0;mask.alpha_composite(Image.fromarray(a),(i%3*w,i//3*h));parts.append(counts)
    return mask,parts

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--approved-extra-color',action='store_true');args=parser.parse_args()
    anchors=json.loads((ROOT/'assets/source_records/erosion-costume-anchors.json').read_text(encoding='utf-8'))
    records=[];violations=[]
    for r in anchors:
        actor,job,kind=r['actor'],r['job'],r['kind'];w,h=(96,96) if kind=='battle' else (32,48)
        base=Image.open(ROOT/r['base']).convert('RGBA');previous=None
        seed=actor=='pc_01' and job=='warrior'
        for stage in [30,60]:
            overlay_path=f'assets/characters/{actor}/erosion_overlays/{job}/{stage}/{kind}.png'
            composite_path=f'assets/characters/{actor}/erosion_signs/jobs/{job}/{stage}/{kind}.png'
            if seed:
                overlay=Image.open(ROOT/overlay_path).convert('RGBA');composite=Image.open(ROOT/composite_path).convert('RGBA');parts=[]
            else:
                overlay,parts=overlay_for(base,r['frames'],kind,stage,actor)
                if previous is not None:overlay=Image.alpha_composite(previous,overlay)
                composite=Image.alpha_composite(base,overlay)
            previous=overlay
            a=np.array(composite);cols=set(map(tuple,a[:,:,:3][a[:,:,3]>0].tolist()))
            limit=(21 if kind=='battle' else 17) if args.approved_extra_color else (20 if kind=='battle' else 16)
            if len(cols)>limit:violations.append(dict(actor=actor,job=job,kind=kind,stage=stage,colors=len(cols),limit=limit))
            paths={}
            for key,image in [('overlay',overlay),('composite',composite)]:
                draft=OUT/'prepared'/actor/job/str(stage)/(kind+'-'+key+'.png');draft.parent.mkdir(parents=True,exist_ok=True);image.save(draft);paths[key]=str(draft.relative_to(ROOT)).replace('\\','/')
            records.append(dict(actor=actor,job=job,kind=kind,stage=stage,base=r['base'],base_sha256=sha(ROOT/r['base']),overlay=overlay_path,composite=composite_path,prepared=paths,frame=[w,h],grid=[3,1 if kind=='battle' else 4],colors=len(cols),light_colors=COLORS[actor],parts=parts,adopted_seed_preserved=seed,composite_sha256=sha(ROOT/paths['composite']),overlay_sha256=sha(ROOT/paths['overlay'])))
    (OUT/'prepared-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (OUT/'prepared-color-limits.json').write_text(json.dumps(dict(approved_extra_color=args.approved_extra_color,violations=violations),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    if args.apply:
        assert not violations,'規約の上限を超えるため本番素材へ適用しない'
        registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8'));entries={e['path']:e for e in registry['assets']}
        visual_path=ROOT/'data/character_visuals.json';visuals=json.loads(visual_path.read_text(encoding='utf-8'))
        for r in records:
            if not r['adopted_seed_preserved']:
                for key in ['overlay','composite']:
                    path=ROOT/r[key];path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/r['prepared'][key],path)
                    e=dict(path=r[key],kind='erosion_pattern_overlay' if key=='overlay' else ('character_battle' if r['kind']=='battle' else 'character_walk'),size=[r['frame'][0]*r['grid'][0],r['frame'][1]*r['grid'][1]],max_colors=3 if key=='overlay' else ((21 if r['kind']=='battle' else 17) if args.approved_extra_color else (20 if r['kind']=='battle' else 16)),status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-29',prompt_record='assets/source_records/erosion-costumes.json',conversion_record='assets/source_records/erosion-costumes.json',modified='人物・職業・動作ごとの腕・頬・首へ発光模様を重ねる。元衣装と模様の外側は不変。変異は内側の輪郭光。')
                    if key=='overlay':e.update(cell_size=r['frame'],layout=r['grid'])
                    else:e.update(frame=r['frame'],grid=r['grid'],erosion_composite=True)
                    entries[r[key]]=e
            visuals['actors'][r['actor']]['erosion_signs'].setdefault('jobs',{}).setdefault(r['job'],{}).setdefault(str(r['stage']),{})[r['kind']]=r['composite']
        registry['assets']=list(entries.values());registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');visual_path.write_text(json.dumps(visuals,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        (ROOT/'assets/source_records/erosion-costumes.json').write_text(json.dumps(dict(request='依頼者採用の侵蝕模様を4人×12職へ展開。兆候は片腕と頬、変異は両腕・首・頬と輪郭光。人物別の明るい色。',tool='Python/Pillow。画像生成モデルは未使用。',approved_extra_color=args.approved_extra_color,records=records),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'EROSION_COSTUMES_PREPARED: variants={len(records)} color_conflicts={len(violations)} applied={args.apply}')

if __name__=='__main__':main()
