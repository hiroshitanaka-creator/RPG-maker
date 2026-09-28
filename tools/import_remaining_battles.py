"""残り8職の生成原画を、完成済み4職と同じ96px戦闘形式へ取り込む。"""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from import_job_costumes import parts, PAL, COLORS
from validate_assets import load_palette

ROOT=Path(__file__).resolve().parents[1]
JOBS={'thief':1022,'hunter':1023,'apothecary':1024,'bard':1025,'knight':1026,'sage':1027,'swordsman':1028,'shaman':1029}
NAMES={'warrior':'戦士','martial_artist':'武闘家','priest':'僧侶','mage':'魔法使い','thief':'盗賊','hunter':'狩人','apothecary':'薬師','bard':'吟遊詩人','knight':'騎士','sage':'賢者','swordsman':'剣士','shaman':'祈祷師'}
OUT=ROOT/'docs/verification/sprint3-battle-eight'
RECORD=ROOT/'assets/source_records/battle-eight-conversion.json'
EXTRA_COLORS={
 'thief':['212F14','314619','505F26','5B6B29'],
 'hunter':['212F14','314619','505F26','5B6B29'],
 'apothecary':['B5AA95','D9CCB4','E9E7CB','58544C'],
 'sage':['B5AA95','D9CCB4','E9E7CB'],
 'swordsman':['3D0B14', '5A170E', '74281B', 'B3433F'],
 'shaman':['D9CCB4','E9E7CB']}


def clothing_pixels(image,job):
    """衣装色を使える部分だけを選ぶ。顔・髪・目は既存16色への対応を維持。"""
    rgb=np.asarray(image.convert('RGB')).astype(np.int32)
    hsv=np.asarray(image.convert('RGB').convert('HSV'))
    h,s,v=[hsv[:,:,i] for i in range(3)]
    y=np.indices(h.shape)[0]
    if job in ('thief','hunter','swordsman'):
        if job=='swordsman':selected=((h<=8)|(h>=247))&(s>=115)
        else:selected=(h>=48)&(h<=119)&(s>=64)&(rgb[:,:,1]>rgb[:,:,0])&(rgb[:,:,1]>rgb[:,:,2])
        # 顔付近の小さな緑・赤の塊は目・口として固定する。衣装の大きな色面と分ける。
        seen=np.zeros(selected.shape,dtype=bool)
        for yy,xx in zip(*np.where(selected)):
            if seen[yy,xx]:continue
            stack=[(int(yy),int(xx))];seen[yy,xx]=True;group=[]
            while stack:
                cy,cx=stack.pop();group.append((cy,cx))
                for ny,nx in ((cy-1,cx),(cy+1,cx),(cy,cx-1),(cy,cx+1)):
                    if 0<=ny<selected.shape[0] and 0<=nx<selected.shape[1] and selected[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=True;stack.append((ny,nx))
            if len(group)<=12 and min(gy for gy,gx in group)<image.height*0.55:
                for gy,gx in group:selected[gy,gx]=False
        return selected
    if job in ('apothecary','sage','shaman'):
        # 白・生成りの胴衣と灰色の道具。髪のある上半分と暖色の肌を対象外にする。
        return (y>=image.height*0.56)&(s<=70)&(((h>=25)&(h<=48))|(s<=20))
    return np.zeros(h.shape,dtype=bool)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--jobs',nargs='+',choices=JOBS,required=True);args=parser.parse_args()
    registry_file=ROOT/'assets/registry.json';registry=json.loads(registry_file.read_text(encoding='utf-8'));entries={e['path']:e for e in registry['assets']}
    visual_file=ROOT/'data/character_visuals.json';visuals=json.loads(visual_file.read_text(encoding='utf-8'))
    records=json.loads(RECORD.read_text(encoding='utf-8')) if RECORD.exists() else []
    records=[r for r in records if r['job'] not in args.jobs]
    for entry in entries.values():
        if entry['path'].startswith('assets/characters/pc_') and entry['kind'] in ('character_battle','character_battle_monster'):
            entry['max_colors']=20
    OUT.mkdir(parents=True,exist_ok=True)
    for job in args.jobs:
        raw=f'assets/_incoming/battle-eight-2026-09-28/{job}.png'
        reference=f'assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_{JOBS[job]}.PNG'
        separated=parts(ROOT/raw,3,4)
        palette_colors=COLORS+EXTRA_COLORS.get(job,[])
        assert len(palette_colors)<=20 and palette_colors[:16]==COLORS
        full_pal=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in palette_colors],dtype=np.int32)
        assert set(map(tuple,full_pal.tolist()))<=load_palette(ROOT/'assets/palette/natural.gpl')
        if len(separated)!=12:raise ValueError(f'{job}: 4人×3動作に分割できない')
        for actor in range(4):
            frames=separated[actor*3:actor*3+3]
            scale=min(92/max(im.height for im,_ in frames),94/max(im.width for im,_ in frames))
            sheet=Image.new('RGBA',(288,96));hashes=[]
            for index,(image,box) in enumerate(frames):
                image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.NEAREST)
                a=np.array(image);mask=a[:,:,3]>=160
                colors,inverse=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
                nearest=((colors.astype(np.int32)[:,None,:]-PAL[None,:,:])**2).sum(axis=2).argmin(axis=1)
                base=PAL[nearest[inverse]].reshape(a.shape[:2]+(3,))
                costume=clothing_pixels(image,job)&mask
                extra_nearest=((colors.astype(np.int32)[:,None,:]-full_pal[None,:,:])**2).sum(axis=2).argmin(axis=1)
                extended=full_pal[extra_nearest[inverse]].reshape(a.shape[:2]+(3,))
                a[:,:,:3]=np.where(costume[:,:,None],extended,base)
                assert np.array_equal(a[:,:,:3][~costume],base[~costume]),'顔まわりの色対応を変更している'
                a[:,:,3]=mask*255;a[~mask]=0
                body=Image.fromarray(a);body=body.crop(body.getchannel('A').getbbox())
                frame=Image.new('RGBA',(96,96));frame.alpha_composite(body,((96-body.width)//2,96-body.height))
                if frame.getchannel('A').getbbox()[3]!=96:raise ValueError('接地行が一致しない')
                hashes.append(hashlib.sha256(frame.tobytes()).hexdigest());sheet.alpha_composite(frame,(index*96,0))
            if len(set(hashes))!=3:raise ValueError(f'{job}: 動作が区別できない')
            actor_id=f'pc_{actor+1:02}';path=f'assets/characters/{actor_id}/jobs/{job}/battle.png'
            (ROOT/path).parent.mkdir(parents=True,exist_ok=True);sheet.save(ROOT/path)
            entries[path]=dict(path=path,kind='character_battle',size=[288,96],frame=[96,96],grid=[3,1],max_colors=20,status='required',palette='assets/palette/natural.gpl',source='generated',tool='imagegen + Python/Pillow',author='RPG-maker / Codex（衣装原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-28',prompt_record='assets/source_records/battle-eight-generation.json',conversion_record='assets/source_records/battle-eight-conversion.json',modified='付録Bの衣装原画・採用済み人物設定・完成済み戦闘絵を参照して3動作を生成。既存手順で分割、最近傍縮小、固定16色＋衣装最大4色、二値透過、接地行95へ変換。歩行と完成済み4職は不変。',actor_id=actor_id,job_id=job)
            visuals['actors'][actor_id]['jobs'].setdefault(job,{})['battle']=path
            records.append(dict(actor=actor_id,job=job,path=path,raw=raw,raw_sha256=digest(ROOT/raw),reference=reference,reference_sha256=digest(ROOT/reference),boxes=[box for _,box in frames],scale=scale,frame=[96,96],ground_y=95,palette=palette_colors,fixed_identity_palette=COLORS,extra_costume_palette=EXTRA_COLORS.get(job,[]),sha256=digest(ROOT/path)))
    registry['assets']=list(entries.values());registry_file.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    visual_file.write_text(json.dumps(visuals,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    RECORD.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20);font.set_variation_by_axes([500])
    for job in args.jobs:
        review=Image.new('RGB',(640,920),'#d6d1bc');draw=ImageDraw.Draw(review)
        draw.text((12,8),f'{NAMES[job]}：待機 ／ 攻撃 ／ 被弾',font=font,fill='#17232b')
        for actor in range(4):
            draw.text((12,46+actor*216),['カイナ','リオネ','ハルド','スイナ'][actor],font=font,fill='#17232b')
            image=Image.open(ROOT/f'assets/characters/pc_{actor+1:02}/jobs/{job}/battle.png').resize((576,192),Image.Resampling.NEAREST)
            review.paste(image,(32,72+actor*216),image)
        review.save(OUT/f'{job}-battle-sheet.png')
    print(f'REMAINING_BATTLES_IMPORTED: jobs={len(args.jobs)} sheets={len(args.jobs)*4} frames={len(args.jobs)*12} frame=96 colors<=20 identity_colors=16')

if __name__=='__main__':main()
