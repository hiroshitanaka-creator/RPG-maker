"""依頼者原画を基準に生成した4職の戦闘絵だけを96pxへ取り込む。歩行絵は触らない。"""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from import_job_costumes import parts, PAL, COLORS

ROOT=Path(__file__).resolve().parents[1]
JOBS={'warrior':1018,'martial_artist':1019,'priest':1020,'mage':1021}


def main():
    registry_path=ROOT/'assets/registry.json'
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    entries={e['path']:e for e in registry['assets']}
    records=[]
    for job,reference in JOBS.items():
        raw=f'assets/_incoming/battle-large-2026-09-27/{job}.png'
        separated=parts(ROOT/raw,3,4)
        for actor in range(4):
            frames=separated[actor*3:actor*3+3]
            scale=min(92/max(im.height for im,_ in frames),94/max(im.width for im,_ in frames))
            sheet=Image.new('RGBA',(288,96))
            for index,(image,box) in enumerate(frames):
                image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.NEAREST)
                a=np.array(image); mask=a[:,:,3]>=160
                colors,inverse=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
                nearest=((colors.astype(np.int32)[:,None,:]-PAL[None,:,:])**2).sum(axis=2).argmin(axis=1)
                if job=='martial_artist':
                    rgb=colors.astype(np.int32);span=rgb.max(axis=1)-rgb.min(axis=1)
                    hue=60*(rgb[:,1]-rgb[:,2])/np.maximum(span,1)
                    orange=(rgb[:,0]==rgb.max(axis=1))&(hue>=22)&(hue<=45)&(span/np.maximum(rgb.max(axis=1),1)>=0.7)
                    for condition,color in [(orange&(rgb[:,0]<180),'90422D'),(orange&(rgb[:,0]>=180)&(rgb[:,0]<235),'CE9F54'),(orange&(rgb[:,0]>=235),'D7B778')]:nearest[condition]=COLORS.index(color)
                a[:,:,:3]=PAL[nearest[inverse]].reshape(a.shape[:2]+(3,))
                a[:,:,3]=mask*255;a[~mask]=0
                body=Image.fromarray(a);body=body.crop(body.getchannel('A').getbbox())
                sheet.alpha_composite(body,(index*96+(96-body.width)//2,96-body.height))
            path=f'assets/characters/pc_{actor+1:02}/jobs/{job}/battle.png'
            sheet.save(ROOT/path)
            entries[path].update(size=[288,96],frame=[96,96],grid=[3,1],
                prompt_record='assets/source_records/battle-large-generation.json',
                conversion_record='assets/source_records/battle-large-conversion.json',
                modified='指定の依頼者原画から96px向けの3動作を生成し直し、自然色16色・二値透過・接地行95へ整えた。48px画像の拡大ではない。歩行絵は変更しない。')
            records.append({'actor':f'pc_{actor+1:02}','job':job,'path':path,'raw':raw,
                'raw_sha256':hashlib.sha256((ROOT/raw).read_bytes()).hexdigest(),
                'reference':f'assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_{reference}.PNG',
                'boxes':[box for _,box in frames],'scale':scale,'frame':[96,96],'ground_y':95,'palette':COLORS,
                'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()})
    registry['assets']=list(entries.values())
    registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'assets/source_records/battle-large-conversion.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    output=ROOT/'docs/verification/battle-layout-target';output.mkdir(parents=True,exist_ok=True)
    overview=Image.new('RGB',(1200,1720),'#d6d1bc');draw=ImageDraw.Draw(overview)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),18)
    for row,(job,_) in enumerate(JOBS.items()):
        for actor in range(4):
            x=actor*300;y=row*430
            draw.text((x+8,y+4),f'{job} / pc_{actor+1:02}',font=font,fill='#17232b')
            im=Image.open(ROOT/f'assets/characters/pc_{actor+1:02}/jobs/{job}/battle.png')
            for frame in range(3):
                pose=im.crop((frame*96,0,(frame+1)*96,96)).resize((192,192),Image.Resampling.NEAREST)
                # 待機・攻撃・被弾を原寸で横並び、下に待機を整数倍で示す。
                native=im.crop((frame*96,0,(frame+1)*96,96));overview.paste(native,(x+frame*98,y+36),native)
                if frame==0:overview.paste(pose,(x+48,y+164),pose)
    overview.save(output/'four-jobs-battle-96.png')
    print('LARGE_BATTLES_IMPORTED: jobs=4 actors=4 sheets=16 frames=48 frame_size=96 colors=16')


if __name__=='__main__':main()
