"""生成原画を分割し、職業衣装の歩行・戦闘を同じ16色と接地位置へ整える。"""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from import_owner_monsters import split_parts
from validate_assets import load_palette

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'assets/_incoming/sprint3-2026-09-27'
RECORD=ROOT/'assets/source_records/sprint3-costumes.json'
SPECS={'warrior':('warrior',1018,'warrior-battle-compact.png'),'martial_artist':('martial',1019,'martial-battle.png'),'priest':('priest',1020,'priest-battle.png'),'mage':('mage',1021,'mage-battle.png')}
# 衣装内では4人の服・金属・装飾の色を共有し、歩行と戦闘でも同じ色を使う。
COLORS=['0B1824','153550','254A63','53335F','3A2317','68422F','9A6048','D09279','D7B778','90422D','BF694D','728593','BDC7D3','EEF6EB','CE9F54','657B2A']
PAL=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in COLORS],dtype=np.int32)

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def parts(path,columns,rows):
    image=Image.open(path).convert('RGBA');a=np.array(image);a[:,:,3]=np.where(a[:,:,3]>=160,255,0);a[a[:,:,3]==0]=0
    separated=split_parts(Image.fromarray(a),columns*rows,threshold=-1)
    separated.sort(key=lambda p:(p[1][1]+p[1][3])/2)
    ordered=[]
    for row in range(rows):ordered.extend(sorted(separated[row*columns:(row+1)*columns],key=lambda p:(p[1][0]+p[1][2])/2))
    return [(image.crop(box),list(box)) for image,box in ordered]

def normalize(frames,width,job):
    scale=min(44/max(im.height for im,_ in frames),(width-2)/max(im.width for im,_ in frames))
    result=[]
    for image,box in frames:
        body=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.NEAREST)
        a=np.array(body);mask=a[:,:,3]>0;colors,inv=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
        indices=((colors.astype(np.int32)[:,None,:]-PAL[None,:,:])**2).sum(axis=2).argmin(axis=1)
        if job=='martial_artist':
            # 高彩度の橙を肌色と同じ色へ落とさず、衣装として読める黄土色へ対応する。
            rgb=colors.astype(np.int32);span=rgb.max(axis=1)-rgb.min(axis=1)
            hue=60*(rgb[:,1]-rgb[:,2])/np.maximum(span,1)
            orange=(rgb[:,0]==rgb.max(axis=1))&(hue>=22)&(hue<=45)&(span/np.maximum(rgb.max(axis=1),1)>=0.7)
            for condition,color in [(orange&(rgb[:,0]<180),'90422D'),(orange&(rgb[:,0]>=180)&(rgb[:,0]<235),'CE9F54'),(orange&(rgb[:,0]>=235),'D7B778')]:indices[condition]=COLORS.index(color)
        a[:,:,:3]=PAL[indices[inv]].reshape(a.shape[:2]+(3,));a[:,:,3]=mask*255;a[~mask]=0
        body=Image.fromarray(a);bbox=body.getchannel('A').getbbox();assert bbox
        body=body.crop(bbox);out=Image.new('RGBA',(width,48));out.alpha_composite(body,((width-body.width)//2,48-body.height))
        assert out.getchannel('A').getbbox()[3]==48
        result.append(out)
    assert len({im.tobytes() for im in result})==len(result),'区別できない動作コマがある'
    return result,scale

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--jobs',nargs='+',choices=SPECS,required=True);args=parser.parse_args()
    assert set(map(tuple,PAL.tolist()))<=load_palette(ROOT/'assets/palette/natural.gpl')
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));entries={e['path']:e for e in registry['assets']}
    records=json.loads(RECORD.read_text(encoding='utf8')) if RECORD.exists() else []
    records=[r for r in records if r['job'] not in args.jobs]
    outdir=ROOT/'docs/verification/sprint3';outdir.mkdir(parents=True,exist_ok=True)
    for job in args.jobs:
        prefix,reference,battle_name=SPECS[job]
        walks=[parts(RAW/(prefix+'-walk-'+pair+'.png'),6,4) for pair in ['12','34']]
        battles=parts(RAW/battle_name,3,4)
        for index in range(4):
            actor=f'pc_{index+1:02}'
            walk=[walks[index//2][row*6+(index%2)*3+column] for row in range(4) for column in range(3)]
            for kind,frames,width,grid,raw in [('walk',walk,32,[3,4],prefix+'-walk-'+('12' if index<2 else '34')+'.png'),('battle',battles[index*3:index*3+3],48,[3,1],battle_name)]:
                normalized,scale=normalize(frames,width,job)
                sheet=Image.new('RGBA',(width*grid[0],48*grid[1]))
                for i,frame in enumerate(normalized):sheet.alpha_composite(frame,(i%3*width,i//3*48))
                rel=f'assets/characters/{actor}/jobs/{job}/{kind}.png';path=ROOT/rel;path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path)
                records.append(dict(actor=actor,job=job,kind=kind,path=rel,raw=RAW.relative_to(ROOT).as_posix()+'/'+raw,raw_sha256=digest(RAW/raw),reference=f'assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_{reference}.PNG',boxes=[box for _,box in frames],scale=scale,alpha_threshold=160,ground_y=47,palette=COLORS,sha256=digest(path)))
                records[-1]['color_mapping']='RGB最近傍。武闘家は高彩度の橙（色相22〜45度・彩度0.7以上）をR値180/235の境界で90422D/CE9F54/D7B778へ対応。' if job=='martial_artist' else 'RGB最近傍'
                entries[rel]=dict(path=rel,kind='character_'+kind,size=list(sheet.size),frame=[width,48],grid=grid,max_colors=16,status='required',palette='assets/palette/natural.gpl',source='generated',tool='imagegen + Python/Pillow',author='RPG-maker / Codex（衣装原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-27',prompt_record='assets/source_records/sprint3-generation.json',modified='採用済み人物設定と指定衣装原画を参照して動作を生成。透明領域で分割し、最近傍縮小・共通16色・二値透過・接地行47へ変換。左右反転はしない。',conversion_record='assets/source_records/sprint3-costumes.json',actor_id=actor,job_id=job)
    registry['assets']=list(entries.values());(ROOT/'assets/registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    RECORD.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',18)
    for job in args.jobs:
        canvas=Image.new('RGB',(1280,880),'#c9c7b7');draw=ImageDraw.Draw(canvas)
        for actor in range(1,5):
            x=(actor-1)*320;draw.text((x+8,8),f'pc_{actor:02} / {job}',font=font,fill='#19212b')
            for kind,y in [('walk',42),('battle',670)]:
                im=Image.open(ROOT/f'assets/characters/pc_{actor:02}/jobs/{job}/{kind}.png');scale=3 if kind=='walk' else 2
                im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);canvas.paste(im,(x+8,y),im)
        canvas.save(outdir/(job+'-sheets.png'))
    print('JOB_COSTUMES_CONVERTED: jobs=%d sheets=%d frames=%d colors=16 ground_y=47' % (len(args.jobs),len(args.jobs)*8,len(args.jobs)*60))

if __name__=='__main__':main()
