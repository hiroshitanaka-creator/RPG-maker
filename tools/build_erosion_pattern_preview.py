"""職業衣装を保つ独立した模様レイヤー。初回はカイナの戦士だけを試作する。"""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/erosion-pattern-preview'
COLORS=['153550','254A63','728593','BDC7D3','5D98C4']
RGB=[tuple(int(c[i:i+2],16) for i in (0,2,4)) for c in COLORS]
NODES={
'battle':[
 {'cheek':[(48,43),(50,45),(53,42)],'arm':[(35,57),(33,61),(36,64),(33,68)],'extra':[(37,53),(39,57),(35,60)]},
 {'cheek':[(48,45),(50,47),(53,44)],'arm':[(29,52),(33,55),(36,52),(40,55)],'extra':[(40,53),(44,56),(45,58)]},
 {'cheek':[(40,50),(42,52),(45,50)],'arm':[(30,64),(27,67),(30,70),(28,73)],'extra':[(33,60),(35,64),(30,67)]}],
'walk':[
 {'cheek':[(17,17),(18,18),(20,17)],'arm':[(9,26),(8,29),(9,31)],'extra':[(10,24),(11,26),(9,28)]},
 {'cheek':[(11,17),(12,19)],'arm':[(15,27),(16,29),(15,32)],'extra':[(15,25),(17,27),(16,30)]},
 {'cheek':[(21,17),(20,19)],'arm':[(17,27),(16,29),(17,32)],'extra':[(17,25),(15,27),(16,30)]},
 {'cheek':[],'arm':[(8,28),(7,30),(8,32)],'extra':[(24,28),(25,30),(24,32)]}]
}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8'));entries={e['path']:e for e in registry['assets']}
    visual_path=ROOT/'data/character_visuals.json';visuals=json.loads(visual_path.read_text(encoding='utf-8'))
    stages={};records=[];previous_masks={}
    for stage in [30,60]:
        stages[str(stage)]={}
        for kind,w,h,rows in [('battle',96,96,1),('walk',32,48,4)]:
            base_path=f'assets/characters/pc_01/jobs/warrior/{kind}.png';base=Image.open(ROOT/base_path).convert('RGBA')
            mask=Image.new('RGBA',base.size)
            for row in range(rows):
                for col in range(3):
                    local=Image.new('RGBA',(w,h));draw=ImageDraw.Draw(local);nodes=NODES[kind][col if kind=='battle' else row]
                    for part in ['cheek','arm']+(['extra'] if stage==60 else []):
                        points=nodes[part]
                        if not points:continue
                        glow=RGB[4] if kind=='battle' else RGB[3]
                        width=(4 if stage==60 and part!='cheek' else 3) if kind=='battle' else (3 if stage==60 and part!='cheek' else 2)
                        draw.line(points,fill=glow+(255,),width=width)
                        draw.line(points,fill=RGB[0]+(255,),width=1)
                        if stage==60:
                            x,y=points[len(points)//2];draw.point((x+1,y),fill=RGB[3]+(255,))
                    a=np.array(local);body=np.array(base.crop((col*w,row*h,(col+1)*w,(row+1)*h)))
                    a[body[:,:,3]==0]=0;mask.alpha_composite(Image.fromarray(a),(col*w,row*h))
            if stage==60:mask=Image.alpha_composite(previous_masks[kind],mask)
            previous_masks[kind]=mask.copy()
            composite=Image.alpha_composite(base,mask)
            overlay_path=f'assets/characters/pc_01/erosion_overlays/warrior/{stage}/{kind}.png'
            combined_path=f'assets/characters/pc_01/erosion_signs/jobs/warrior/{stage}/{kind}.png'
            for path,image,overlay in [(overlay_path,mask,True),(combined_path,composite,False)]:
                dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True);image.save(dest)
                entry=dict(path=path,kind='erosion_pattern_overlay' if overlay else ('character_battle' if kind=='battle' else 'character_walk'),size=list(image.size),max_colors=5 if overlay else (20 if kind=='battle' else 16),status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-29',prompt_record='assets/source_records/erosion-pattern-preview.json',conversion_record='assets/source_records/erosion-pattern-preview.json',modified='独立した腕・頬の模様。衣装の原本は無変更。'+('重ね絵のため接地行を持たない。' if overlay else '同じ大きさの衣装と重ね絵を合成。'))
                if overlay:entry.update(cell_size=[w,h],layout=[3,rows])
                else:entry.update(frame=[w,h],grid=[3,rows])
                entries[path]=entry
            assert np.array_equal(np.array(base)[:,:,3],np.array(composite)[:,:,3])
            stages[str(stage)][kind]=combined_path
            records.append(dict(request='依頼者採用の案2。腕と頬に紺の細い模様を重ね、少し光らせる。侵蝕30から60で模様を増やす。まず戦士の見本。',tool='Python/Pillowによる決定論的な重ね絵。画像生成モデルは未使用。',actor='pc_01',job='warrior',stage=stage,kind=kind,base=base_path,base_sha256=digest(ROOT/base_path),overlay=overlay_path,overlay_sha256=digest(ROOT/overlay_path),composite=combined_path,composite_sha256=digest(ROOT/combined_path),colors=COLORS,nodes=NODES[kind],opaque_overlay_pixels=int((np.array(mask)[:,:,3]>0).sum())))
    visuals['actors']['pc_01']['erosion_signs'].setdefault('jobs',{})['warrior']=stages
    registry['assets']=list(entries.values());registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    visual_path.write_text(json.dumps(visuals,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'assets/source_records/erosion-pattern-preview.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    canvas=Image.new('RGB',(960,760),'#d8d4c7');d=ImageDraw.Draw(canvas)
    for col,stage in enumerate([0,30,60]):
        d.text((col*320+12,8),['侵蝕なし 0〜29','兆候 30〜59','変異 60〜89'][col],font=font,fill='#162835')
        for kind,y in [('battle',48),('walk',450)]:
            path=f'assets/characters/pc_01/jobs/warrior/{kind}.png' if stage==0 else stages[str(stage)][kind]
            im=Image.open(ROOT/path).crop((0,0,96,96) if kind=='battle' else (0,0,32,48))
            im=im.resize((288,288) if kind=='battle' else (128,192),Image.Resampling.NEAREST)
            canvas.paste(im,(col*320+16,y),im)
    d.text((12,690),'96px素材と32×48px歩行の拡大。ゲームの段階条件・職業衣装は変更しない。',font=font,fill='#162835')
    canvas.save(OUT/'warrior-stages-detail.png')
    print('EROSION_PATTERN_PREVIEW: warrior stages=30,60 overlays=4 composites=4')

if __name__=='__main__':main()
