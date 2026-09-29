"""職業衣装を保つ独立した模様レイヤー。初回はカイナの戦士だけを試作する。"""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/erosion-pattern-preview'
COLORS=['5D98C4','BDC7D3','EEF6EB']
RGB=[tuple(int(c[i:i+2],16) for i in (0,2,4)) for c in COLORS]
NODES={
'battle':[
 {'cheek':[(44,42),(47,44),(49,42),(52,43)],'arm':[(38,52),(35,56),(37,60),(32,64),(34,69)],'neck':[(45,47),(46,50),(51,50),(53,48)],'other_arm':[(59,50),(63,54),(61,58),(65,62)]},
 {'cheek':[(47,44),(50,46),(52,43),(55,43)],'arm':[(42,53),(37,55),(34,52),(29,54),(25,52)],'neck':[(48,48),(49,51),(54,53),(55,50)],'other_arm':[(61,50),(64,53),(63,57),(66,60)]},
 {'cheek':[(39,49),(41,51),(44,49),(46,50)],'arm':[(33,59),(29,64),(31,68),(27,72),(29,75)],'neck':[(43,53),(45,55),(50,55),(52,52)],'other_arm':[(55,52),(57,56),(55,60),(60,64)]}],
'walk':[
 {'cheek':[(14,16),(16,18),(19,17)],'arm':[(10,24),(8,27),(10,29),(8,33)],'neck':[(14,20),(16,22),(18,20)],'other_arm':[(22,24),(24,27),(22,30),(24,33)]},
 {'cheek':[(10,16),(12,18),(13,19)],'arm':[(15,24),(16,27),(14,30),(16,33)],'neck':[(12,21),(14,22),(16,22)],'other_arm':[(11,26),(10,29),(11,32)]},
 {'cheek':[(22,16),(20,18),(19,19)],'arm':[(17,24),(16,27),(18,30),(16,33)],'neck':[(20,21),(18,22),(16,22)],'other_arm':[(21,26),(22,29),(21,32)]},
 {'cheek':[],'arm':[(8,25),(7,28),(9,30),(7,33)],'neck':[(14,20),(16,21),(18,20)],'other_arm':[(24,25),(25,28),(23,30),(25,33)]}]
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
                    body=np.array(base.crop((col*w,row*h,(col+1)*w,(row+1)*h)))
                    body_mask=body[:,:,3]>0
                    if stage==60:
                        # 内側の輪郭光なら元の大きさ・透過・足元を維持できる。
                        outer=body_mask&~ndimage.binary_erosion(body_mask,iterations=1,border_value=0)
                        rim=body_mask&~ndimage.binary_erosion(body_mask,iterations=2 if kind=='battle' else 1,border_value=0)
                        a=np.array(local);a[rim]=RGB[1]+(255,);a[outer]=(RGB[0] if kind=='battle' else RGB[1])+(255,)
                        local=Image.fromarray(a);draw=ImageDraw.Draw(local)
                    for part in ['cheek','arm']+(['neck','other_arm'] if stage==60 else []):
                        points=nodes[part]
                        if not points:continue
                        # 近白色の芯を太めにし、暗い鎧と髪に埋もれない発光模様にする。
                        draw.line(points,fill=(RGB[0] if kind=='battle' else RGB[1])+(255,),width=5 if kind=='battle' else 3)
                        draw.line(points,fill=RGB[2]+(255,),width=2 if kind=='battle' else 1)
                    a=np.array(local);a[~body_mask]=0;mask.alpha_composite(Image.fromarray(a),(col*w,row*h))
            if stage==60:mask=Image.alpha_composite(previous_masks[kind],mask)
            previous_masks[kind]=mask.copy()
            composite=Image.alpha_composite(base,mask)
            overlay_path=f'assets/characters/pc_01/erosion_overlays/warrior/{stage}/{kind}.png'
            combined_path=f'assets/characters/pc_01/erosion_signs/jobs/warrior/{stage}/{kind}.png'
            for path,image,overlay in [(overlay_path,mask,True),(combined_path,composite,False)]:
                dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True);image.save(dest)
                entry=dict(path=path,kind='erosion_pattern_overlay' if overlay else ('character_battle' if kind=='battle' else 'character_walk'),size=list(image.size),max_colors=3 if overlay else (20 if kind=='battle' else 16),status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-29',prompt_record='assets/source_records/erosion-pattern-preview.json',conversion_record='assets/source_records/erosion-pattern-preview.json',modified='近白色の発光模様。30は片腕・頬、60は両腕・首・頬と内側の輪郭光。衣装の原本は無変更。'+('重ね絵のため接地行を持たない。' if overlay else '同じ大きさの衣装と重ね絵を合成。'))
                if overlay:entry.update(cell_size=[w,h],layout=[3,rows])
                else:entry.update(frame=[w,h],grid=[3,rows])
                entries[path]=entry
            assert np.array_equal(np.array(base)[:,:,3],np.array(composite)[:,:,3])
            stages[str(stage)][kind]=combined_path
            records.append(dict(contour_inside_pixels=(2 if kind=='battle' else 1) if stage==60 else 0,request='依頼者修正：白に近い明るい水色で発光。兆候は片腕と頬。変異は両腕・首・頬に拡大し、輪郭に1〜2画素の光を沿わせる。まずカイナ戦士。',tool='Python/Pillowによる決定論的な重ね絵。画像生成モデルは未使用。',actor='pc_01',job='warrior',stage=stage,kind=kind,base=base_path,base_sha256=digest(ROOT/base_path),overlay=overlay_path,overlay_sha256=digest(ROOT/overlay_path),composite=combined_path,composite_sha256=digest(ROOT/combined_path),colors=COLORS,nodes=NODES[kind],opaque_overlay_pixels=int((np.array(mask)[:,:,3]>0).sum())))
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
