#!/usr/bin/env python3
"""追加原画を不変で保管し、若い4人の歩行だけを規定のシートへ変換する。"""
from pathlib import Path
import argparse, hashlib, io, json, math, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from import_owner_monsters import ROOT, split_parts

ORIGINAL='assets/_incoming/owner-2026-09-26/reference-pack-2'
RECORD='assets/source_records/owner-walks.json'
ZIP_SHA='495b88ebff10e00f1e4ef42e0e01de3e68f14762829ff8f9247f8133efc06217'
OUT=ROOT/'docs/verification/owner-originals-2'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def ordered_parts(path, columns, rows):
    parts=split_parts(Image.open(path),columns*rows)
    parts.sort(key=lambda p:(p[1][1]+p[1][3])/2)
    result=[]
    for row in range(rows):result.extend(sorted(parts[row*columns:(row+1)*columns],key=lambda p:p[1][0]))
    return result

def frame(part,box,height,palette):
    body=part.crop(box);w=max(1,round(body.width*height/body.height));assert w<=30
    body=body.resize((w,height),Image.Resampling.NEAREST)
    body=body.crop(body.getchannel('A').getbbox())
    a=np.array(body);opaque=a[:,:,3]>0
    colors,inv=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
    nearest=((colors.astype(np.int32)[:,None,:]-palette[None,:,:])**2).sum(axis=2).argmin(axis=1)
    a[:,:,:3]=palette[nearest[inv]].reshape(a.shape[:2]+(3,));a[:,:,3]=opaque*255;a[~opaque]=0
    body=Image.fromarray(a);out=Image.new('RGBA',(32,48));out.alpha_composite(body,((32-body.width)//2,46-body.height))
    return out

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path);args=parser.parse_args()
    folder=ROOT/ORIGINAL;folder.mkdir(parents=True,exist_ok=True)
    if args.archive:
        assert sha(args.archive.read_bytes())==ZIP_SHA
        rows=[]
        with zipfile.ZipFile(args.archive) as archive:
            for item in archive.infolist():
                if item.is_dir() or item.filename.startswith('__MACOSX/') or not item.filename.lower().endswith('.png'):continue
                name=Path(item.filename).name;assert name.startswith('IMG_') and '..' not in name
                raw=archive.read(item);dest=folder/name
                if dest.exists():assert dest.read_bytes()==raw
                else:dest.write_bytes(raw)
                image=Image.open(io.BytesIO(raw));image.verify()
                rows.append(dict(name=name,sha256=sha(raw),bytes=len(raw),size=list(Image.open(io.BytesIO(raw)).size)))
        assert len(rows)==43 and len({r['sha256'] for r in rows})==42
        write_json(folder/'manifest.json',dict(archive_sha256=ZIP_SHA,provided_at='2026-09-27',author='依頼者',source='Grok',declaration='依頼者がGrokに依頼して作成した完全オリジナル画像という申告。共有会話URLは今回のZIPについて未指定。',originals=sorted(rows,key=lambda r:r['name'])))
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
    for r in manifest['originals']:assert sha((folder/r['name']).read_bytes())==r['sha256']
    names={r['name']:r for r in manifest['originals']}
    font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',13);OUT.mkdir(parents=True,exist_ok=True)
    neutral=ordered_parts(folder/'IMG_1042.PNG',4,4)
    older=json.loads((ROOT/'assets/source_records/owner-characters.json').read_text(encoding='utf8'))
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));entries={r['path']:r for r in registry['assets']}
    results=[];sheets=[]
    for actor in range(1,5):
        identifier=f'owner_young_{actor:02}';source=f'IMG_{1044+actor}.PNG';walking=ordered_parts(folder/source,3,4)
        palette=np.array(next(r['palette_colors'] for r in older['imported'] if r['id']==identifier and r['pose']=='standing'),dtype=np.int32)
        selected=[]
        for facing in range(4):
            selected.append((neutral[(actor-1)*4+facing],'IMG_1042.PNG',(actor-1)*4+facing))
            # 4人目の右向き列1は左向きなので使用せず、右向きの列2・3を使う。
            for col in ([1,2] if actor==4 and facing==2 else [0,2]):selected.append((walking[facing*3+col],source,facing*3+col))
        ratio=max((box[2]-box[0])/(box[3]-box[1]) for (part,box),_,_ in selected)
        height=min(44,int(30/ratio));sheet=Image.new('RGBA',(96,192));frames=[]
        for index,((part,box),file,slot) in enumerate(selected):
            picture=frame(part,box,height,palette);sheet.alpha_composite(picture,((index%3)*32,(index//3)*48))
            frames.append(dict(row=index//3,column=index%3,original_file=ORIGINAL+'/'+file,original_sha256=names[file]['sha256'],original_slot=slot,crop=list(box),mirror=False))
        path=f'assets/characters/{identifier}/walk.png';sheet.save(ROOT/path);sheets.append(sheet)
        results.append(dict(id=identifier,path=path,body_height=height,palette_colors=palette.tolist(),frames=frames,output_sha256=sha((ROOT/path).read_bytes())))
        entries[path]=dict(path=path,kind='character_walk',size=[96,192],frame=[32,48],grid=[3,4],max_colors=16,status='optional',palette='assets/palette/natural.gpl',source='owner',license='LicenseRef-Owner-Provided',author='依頼者',provided_at='2026-09-27',original_file=ORIGINAL+'/'+source,conversion_record=RECORD+'#'+identifier,modified='原本は不変。各方向の直立はIMG_1042、歩行は本人の原画を使用。左右反転なし。人物ごとの高さと接地位置をそろえ、既存の演出素材と共通16色へ最近傍変換。',usage='guest_walk_unplaced')
    registry['assets']=list(entries.values());write_json(ROOT/'assets/registry.json',registry)
    write_json(ROOT/RECORD,dict(baseline='6032b9d051d2830e45bab181e91c6e0d9fee2e43',imported=results,unused_frame='IMG_1048.PNGの3行目1列目は向きが違うため使わない。原本はそのまま保存。'))
    poster=Image.new('RGB',(1280,650),'#d9d5c7');draw=ImageDraw.Draw(poster)
    for i,sheet in enumerate(sheets):
        x=i*320;draw.text((x+10,10),f'別の冒険者 {i+1} / 下・左・右・上',font=font,fill='black')
        large=sheet.resize((288,576),Image.Resampling.NEAREST);poster.paste(large,(x+16,40),large)
        draw.text((x+10,622),'直立 / 歩行A / 歩行B・左右反転なし',font=font,fill='black')
    poster.save(OUT/'walk-sheets.png')
    animation=[]
    for step in range(4):
        image=Image.new('RGB',(512,440),'#d9d5c7');draw=ImageDraw.Draw(image)
        for actor,sheet in enumerate(sheets):
            for facing in range(4):
                col=[0,1,0,2][step];pose=sheet.crop((col*32,facing*48,col*32+32,facing*48+48)).resize((64,96),Image.Resampling.NEAREST)
                image.paste(pose,(actor*128+32,facing*108+8),pose)
        animation.append(image)
    animation[0].save(OUT/'walk-preview.gif',save_all=True,append_images=animation[1:],duration=150,loop=0,disposal=2)
    originals=manifest['originals']
    for page in range(math.ceil(len(originals)/12)):
        picked=originals[page*12:(page+1)*12];image=Image.new('RGB',(1200,math.ceil(len(picked)/3)*280),'#dddddd');draw=ImageDraw.Draw(image)
        for index,row in enumerate(picked):
            im=Image.open(folder/row['name']).convert('RGBA');im.thumbnail((385,235),Image.Resampling.NEAREST);x=index%3*400;y=index//3*280
            image.paste(im,(x+(400-im.width)//2,y+30+(240-im.height)//2),im);draw.text((x+8,y+5),row['name'],font=font,fill='black')
        image.save(OUT/f'original-index-{page+1}.png')
    lines=['# 依頼者作成オリジナル画像2の保管記録','','2026年9月27日受領。依頼者がGrokへ依頼して生成した完全オリジナル画像として提供し、制作を進めるよう指示した。PNG43枚をZIPから1バイトも変えず保管した。macOSの付随情報は画像ではないため対象外。共有会話URLは今回未指定。','','ZIP SHA-256: `'+ZIP_SHA+'`','','`IMG_1042.PNG` と `IMG_1042 2.PNG` は同じ内容だが、両方とも元の名前で保持した。種類は42。歩行用4枚と方向別設定画を今回使用し、衣装・魔物化・地形・住民・背景は今後の参考原画として保管する。配置・役・正式名は確定しない。','','| 原画 | サイズ | SHA-256 |','| --- | --- | --- |']
    for r in originals:lines.append(f"| {r['name']} | {r['size'][0]}×{r['size'][1]} | {r['sha256']} |")
    (folder/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    (OUT/'README.md').write_text('# 追加原画と歩行素材の確認\n\n原画43枚・42種類の一覧は original-index-1.png〜4.png。原画の出所とSHA-256は assets/_incoming/owner-2026-09-26/reference-pack-2/README.md に記録した。\n\nwalk-sheets.png は4人の全48コマを3倍で並べた確認画像。walk-preview.gif は0→1→0→2の順、各150ms、2倍表示。接地線は全コマ45行目。直立はIMG_1042から補い、IMG_1048の誤った左向きコマは採用しない。原本は修正も反転もしていない。\n\n歩行素材は台帳へ登録した。人物の登場場所・役は未決であり、今は配置しない。4人目の詠唱・被弾・勝利の原画はこのZIPにも含まれていない。\n',encoding='utf8',newline='\n')
    print('OWNER_WALKS_IMPORT: originals=43 unique=42 walkers=4 frames=48 mirrored=0')

if __name__=='__main__':main()
