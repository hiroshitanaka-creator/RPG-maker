"""依頼者のIMG_1183を無加工で保管し、灰色背景から敵3体を決定論的に取り込む。"""
from collections import deque
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from import_owner_monsters import PAL

ROOT=Path(__file__).resolve().parents[1]
RECEIVED='assets/_incoming/owner-2026-09-30-interiors/IMG_1183.png'
ARCHIVE='assets/_incoming/owner-2026-09-26/supplement-2026-09-30/IMG_1183.png'
RECORD='assets/source_records/owner-desert-monsters-20260930.json'
OUT=ROOT/'docs/verification/sprint6-desert-monsters'
DEFS=[('desert_scorpion','サソリ（仮）',0,447,'medium',80,'沿岸の通常遭遇'),
      ('sand_worm','砂の虫（仮）',447,777,'large',96,'沿岸の通常遭遇'),
      ('desert_mummy','ミイラ（仮）',777,1168,'medium',80,'遺跡の候補・通常遭遇へ未登録')]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def cut_grey(im):
    a=np.array(im.convert('RGBA'));rgb=a[:,:,:3].astype(np.int16)
    candidate=(rgb.min(axis=2)>=185)&((rgb.max(axis=2)-rgb.min(axis=2))<=16)
    h,w=candidate.shape;seen=np.zeros((h,w),bool);queue=deque()
    for x,y in [(x,0) for x in range(w)]+[(x,h-1) for x in range(w)]+[(0,y) for y in range(h)]+[(w-1,y) for y in range(h)]:
        if candidate[y,x] and not seen[y,x]:seen[y,x]=True;queue.append((x,y))
    while queue:
        x,y=queue.popleft()
        for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if 0<=xx<w and 0<=yy<h and candidate[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;queue.append((xx,yy))
    a[seen]=0;a[~seen,3]=255
    return Image.fromarray(a)

def convert_cutout(clean,box,extent,bank=PAL):
    # 灰背景で確定した透過を維持する。黒背景用の再切り抜きで暗い体を削らない。
    body=clean.crop(box);scale=extent/max(body.size)
    body=body.resize((max(1,round(body.width*scale)),max(1,round(body.height*scale))),Image.Resampling.NEAREST)
    a=np.array(body);opaque=a[:,:,3]>0
    colors,counts=np.unique(a[:,:,:3][opaque],axis=0,return_counts=True)
    near=((colors.astype(np.int32)[:,None,:]-bank[None,:,:])**2).sum(axis=2).argmin(axis=1)
    weights=np.bincount(near,weights=counts,minlength=len(bank));palette=bank[np.argsort(-weights,kind='stable')[:32]]
    values,inverse=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
    near=((values.astype(np.int32)[:,None,:]-palette[None,:,:])**2).sum(axis=2).argmin(axis=1)
    a[:,:,:3]=palette[near[inverse]].reshape(a.shape[:2]+(3,));a[~opaque]=0
    return Image.fromarray(a)

def main():
    raw=(ROOT/RECEIVED).read_bytes();source_sha=sha(raw)
    archive=ROOT/ARCHIVE;archive.parent.mkdir(parents=True,exist_ok=True)
    if archive.exists():assert archive.read_bytes()==raw,'保管原本の上書き禁止'
    else:archive.write_bytes(raw)
    source=Image.open(ROOT/RECEIVED).convert('RGBA');assert source.size==(1168,784)
    registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf8'))
    entries={e['path']:e for e in registry['assets']};rows=[];pieces=[]
    extension_path=ROOT/'assets/source_records/natural-teal-extension.json'
    extension=json.loads(extension_path.read_text(encoding='utf8')) if extension_path.exists() else None
    OUT.mkdir(parents=True,exist_ok=True)
    for slot,(identifier,name,left,right,category,extent,use) in enumerate(DEFS,1):
        original=source.crop((left,0,right,source.height));clean=cut_grey(original)
        box=clean.getbbox();assert box
        bank=PAL
        if extension:
            # ミイラは従来の72色に固定し、将来のパレット拡張でも今回以外の素材を変えない。
            colors=extension['original_colors']+([r['rgb'] for r in extension['selected']] if identifier!='desert_mummy' else [])
            bank=np.array(sorted(map(tuple,colors)),dtype=np.int32)
        body=convert_cutout(clean,box,extent,bank);picture=Image.new('RGBA',(96,96))
        bottom=96-min(2,96-body.height);picture.alpha_composite(body,((96-body.width)//2,bottom-body.height))
        dest=f'assets/monsters/{identifier}/idle.png';(ROOT/dest).parent.mkdir(parents=True,exist_ok=True);picture.save(ROOT/dest)
        clean.save(OUT/(identifier+'-cutout.png'))
        bounds=picture.getbbox();a=np.array(picture);colors={tuple(c) for c in a[:,:,:3][a[:,:,3]>0]}
        assert len(colors)<=32 and set(np.unique(a[:,:,3]))<={0,255}
        row=dict(id=identifier,name=name,slot=slot,received_file=RECEIVED,original_file=ARCHIVE,original_sha256=source_sha,
                 split_rect=[left,0,right,source.height],body_box_in_slot=list(box),background={'minimum_channel':185,'maximum_channel_difference':16,'connected_to_edge':True},
                 resampling='nearest',mirror=False,palette='assets/palette/natural.gpl',max_colors=32,actual_colors=len(colors),
                 size_class=category,target_extent=extent,size=[96,96],visible_size=[bounds[2]-bounds[0],bounds[3]-bounds[1]],path=dest,
                 output_sha256=sha((ROOT/dest).read_bytes()),use=use)
        if extension and identifier!='desert_mummy':row['palette_extension_record']='assets/source_records/natural-teal-extension.json'
        rows.append(row);pieces.append((original,clean,picture,box))
        entries[dest]=dict(path=dest,kind='monster_idle',size=[96,96],max_colors=32,status='optional' if identifier=='desert_mummy' else 'required',
                           palette='assets/palette/natural.gpl',source='owner',license='LicenseRef-Owner-Provided',author='依頼者',provided_at='2026-09-30',
                           original_file=ARCHIVE,received_file=RECEIVED,conversion_record=RECORD+'#'+identifier,
                           modified=f'IMG_1183の左から{slot}体目。外周につながる明るい無彩色の背景だけを除去。最近傍縮小、natural.gplの32色以内、二値透過。反転なし。絵の長辺{extent}px。',
                           facing='right',monster_tier='normal',size_class=category,visible_size=row['visible_size'])
    assert (ROOT/RECEIVED).read_bytes()==raw==archive.read_bytes()
    registry['assets']=list(entries.values());write(registry_path,registry)
    write(ROOT/RECORD,dict(received_file=RECEIVED,archive_copy=ARCHIVE,source_sha256=source_sha,source_bytes=len(raw),author='依頼者',
                          authorization='2026年9月30日の依頼者指示で敵3体をゲーム用に取り込む。今回の原画の生成サービス・共有会話URLは未指定。',
                          storage_note='受領ファイルを元の場所に保持。従来の台帳の取り込みルートにも同一バイトの保管コピーを置き、双方のSHA-256を照合。',imported=rows))
    write(archive.parent/'manifest.json',dict(received_at='2026-09-30',received_file=RECEIVED,sha256=source_sha,files=[{'file':'IMG_1183.png','sha256':source_sha}]))
    (archive.parent/'README.md').write_text('# 砂漠の敵3体の保管コピー\n\n原本の受領場所は `'+RECEIVED+'`。台帳の従来の取り込みルートに同一バイトのコピーを保管した。元ファイルは変更・移動していない。\n\nSHA-256: `'+source_sha+'`\n\n左からサソリ・砂の虫・ミイラ。ミイラは遺跡用候補として保管し、通常遭遇には登録しない。変換記録は `'+RECORD+'`。\n',encoding='utf8')
    fontpath=str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf');font=ImageFont.truetype(fontpath,22);small=ImageFont.truetype(fontpath,17)
    sheet=Image.new('RGB',(1440,900),'#17243c');draw=ImageDraw.Draw(sheet)
    draw.text((18,10),'IMG_1183 原画 → 灰色背景の切り抜き → 32色以内のゲーム用素材',font=font,fill='white')
    for i,(row,(original,clean,picture,box)) in enumerate(zip(rows,pieces)):
        x=i*480+16;draw.text((x,50),row['name']+' / '+('大96px' if i==1 else '中80px'),font=font,fill='white')
        rawpart=original.crop(box);rawpart.thumbnail((430,285),Image.Resampling.NEAREST);sheet.paste(rawpart,(x+(440-rawpart.width)//2,93),rawpart)
        draw.text((x,387),'原画（灰色の背景を含む）',font=small,fill='white')
        mask=clean.crop(box);mask.thumbnail((170,235),Image.Resampling.NEAREST);sheet.paste(mask,(x,420),mask)
        zoom=picture.resize((288,288),Image.Resampling.NEAREST);sheet.paste(zoom,(x+170,403),zoom)
        draw.text((x,704),'切り抜き後',font=small,fill='white');draw.text((x+210,704),'ゲーム用・3倍',font=small,fill='white')
        actual=picture.resize((72,72),Image.Resampling.NEAREST);sheet.paste(actual,(x+20,745),actual)
        draw.text((x+110,764),'戦闘画面の大きさ',font=small,fill='white')
        draw.text((x,847),row['use'],font=small,fill='#ede0be')
    sheet.save(OUT/'source-comparison.png')
    if extension:sheet.crop((0,0,960,900)).save(OUT/'teal-source-comparison.png')
    print('DESERT_MONSTERS_IMPORT: '+', '.join(f"{r['id']}={r['visible_size']}/{r['actual_colors']}色" for r in rows))

if __name__=='__main__':main()
