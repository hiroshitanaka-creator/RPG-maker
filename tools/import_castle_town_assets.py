"""城下町・城の生成原画を既存規約へ変換し、原画と変換を台帳へ記録する。"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from import_job_costumes import parts, digest
from validate_assets import load_palette

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'assets/_incoming/castle-town-2026-09-28'
OUT=ROOT/'docs/verification/sprint5-castle-town'
PALETTE=np.array(sorted(load_palette(ROOT/'assets/palette/natural.gpl')),dtype=np.int32)

def quantize(image, limit):
    a=np.array(image.convert('RGBA'));mask=a[:,:,3]>=160
    rgb=a[:,:,:3][mask]
    colors,counts=np.unique(rgb,axis=0,return_counts=True)
    distances=((colors.astype(np.int32)[:,None,:]-PALETTE[None,:,:])**2).sum(2)
    chosen=[int(np.argmin((distances*counts[:,None]).sum(0)))]
    best=distances[:,chosen[0]]
    while len(chosen)<limit:
        benefits=(np.maximum(best[:,None]-distances,0)*counts[:,None]).sum(0)
        benefits[chosen]=-1
        pick=int(benefits.argmax())
        if benefits[pick]<=0:break
        chosen.append(pick);best=np.minimum(best,distances[:,pick])
    pal=PALETTE[chosen]
    index=((a[:,:,:3][:,:,None,:].astype(np.int32)-pal)**2).sum(3).argmin(2)
    a[:,:,:3]=pal[index];a[:,:,3]=mask*255;a[~mask]=0
    return Image.fromarray(a),pal.tolist()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    entries={e['path']:e for e in registry['assets']};records=[]
    def register(image,path,raw,boxes,kind,limit,palette,**extra):
        target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);image.save(target)
        entries[path]=dict(path=path,kind=kind,size=list(image.size),max_colors=limit,status='required',palette='assets/palette/natural.gpl',source='generated',tool='imagegen + Python/Pillow',author='RPG-maker / Codex（参照原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-28',prompt_record='assets/source_records/castle-town-generation.json',conversion_record='assets/source_records/castle-town-conversion.json',modified='原画を透明領域で分割、最近傍縮小、自然色パレットへ減色、二値透過。原本は保持。',**extra)
        records.append(dict(path=path,raw=raw,raw_sha256=digest(ROOT/raw),boxes=boxes,palette=palette,sha256=digest(target),alpha_threshold=160))
    for name,actors in [('royal',['npc_castle_king','npc_castle_advisor']),('town',['npc_castle_guard','npc_castle_merchant'])]:
        raw=f'assets/_incoming/castle-town-2026-09-28/{name}-walk.png'
        split=parts(ROOT/raw,6,4)
        for actor_index,actor in enumerate(actors):
            frames=[split[row*6+actor_index*3+col] for row in range(4) for col in range(3)]
            scale=min(44/max(im.height for im,box in frames),30/max(im.width for im,box in frames))
            sheet=Image.new('RGBA',(96,192))
            for i,(im,box) in enumerate(frames):
                im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
                alpha=np.array(im.getchannel('A'));im.putalpha(Image.fromarray(np.uint8(alpha>=160)*255))
                im=im.crop(im.getchannel('A').getbbox())
                sheet.alpha_composite(im,(i%3*32+(32-im.width)//2,i//3*48+48-im.height))
            sheet,palette=quantize(sheet,16)
            assert len({sheet.crop((c*32,r*48,c*32+32,r*48+48)).tobytes() for r in range(4) for c in range(3)})==12
            register(sheet,f'assets/characters/{actor}/walk.png',raw,[box for im,box in frames],'character_walk',16,palette,frame=[32,48],grid=[3,4])
            records[-1].update(scale=scale,ground_y=47)
    raw='assets/_incoming/castle-town-2026-09-28/furniture.png'
    for (im,box),(name,size) in zip(parts(ROOT/raw,2,2),[('throne',(64,96)),('banner',(32,64)),('candelabrum',(32,64)),('bookcase',(96,96))]):
        im.thumbnail((size[0]-2,size[1]-2),Image.Resampling.NEAREST)
        out=Image.new('RGBA',size);out.alpha_composite(im,((size[0]-im.width)//2,size[1]-im.height))
        out,palette=quantize(out,64)
        register(out,f'assets/objects/castle_{name}.png',raw,[box],'object',64,palette)
    raw='assets/_incoming/castle-town-2026-09-28/surfaces.png'
    for (im,box),(name,size,kind) in zip(parts(ROOT/raw,2,2),[('floor',(128,128),'tile'),('wall',(128,128),'tile'),('column',(64,128),'object'),('runner',(96,96),'tile')]):
        if kind=='tile':
            im=im.crop((3,3,im.width-3,im.height-3)).resize(size,Image.Resampling.NEAREST);im.putalpha(255)
        else:
            im.thumbnail((size[0]-2,size[1]-2),Image.Resampling.NEAREST)
            body=im;im=Image.new('RGBA',size);im.alpha_composite(body,((size[0]-body.width)//2,size[1]-body.height))
        im,palette=quantize(im,64)
        register(im,f'assets/{"objects" if kind=="object" else "tiles"}/castle_{name}.png',raw,[box],kind,64,palette)
    registry['assets']=list(entries.values())
    (ROOT/'assets/registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    (ROOT/'assets/source_records/castle-town-conversion.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    gp=ROOT/'assets/source_records/castle-town-generation.json';generation=json.loads(gp.read_text(encoding='utf8'))
    for item in generation:
        item['raw_sha256']=digest(ROOT/item['raw']);item['reference_sha256']={p:digest(ROOT/p) for p in item['references']}
    gp.write_text(json.dumps(generation,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    canvas=Image.new('RGB',(1240,720),'#d6d2bb');font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    for index,actor in enumerate(['npc_castle_king','npc_castle_advisor','npc_castle_guard','npc_castle_merchant']):
        im=Image.open(ROOT/f'assets/characters/{actor}/walk.png').resize((288,576),Image.Resampling.NEAREST)
        canvas.paste(im,(index*310,45),im);ImageDraw.Draw(canvas).text((index*310+8,8),['王','側近','兵士','商人'][index],font=font,fill='#14212b')
    canvas.save(OUT/'castle-npcs.png')
    print('CASTLE_ASSETS_PASS: npcs=4 frames=48 objects=5 tiles=3')

if __name__=='__main__':main()
