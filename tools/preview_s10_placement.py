#!/usr/bin/env python3
"""承認原画不変の決定論的配置比較。実ゲーム接続・素材台帳更新なし。"""
import argparse, hashlib, json
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,required=True); ap.add_argument('--inputs',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    expected='7fb285a7c31839ff33350c328f39dfd97e94ea57a0fe6567ef862f8fb19a9aa5'
    assert sha(a.source)==expected
    raw=Image.open(a.source).convert('RGB'); rgb=np.array(raw).astype(np.int16); h,w=rgb.shape[:2]
    # 実見した薄灰色背景だけを周縁から除去。内部の衣服・髪を全色置換しない。
    candidate=(rgb.min(2)>=140)&((rgb.max(2)-rgb.min(2))<=25)
    seen=np.zeros((h,w),bool); q=deque()
    for x,y in [(x,0) for x in range(w)]+[(x,h-1) for x in range(w)]+[(0,y) for y in range(h)]+[(w-1,y) for y in range(h)]:
        if candidate[y,x] and not seen[y,x]:seen[y,x]=True;q.append((x,y))
    while q:
        x,y=q.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<w and 0<=ny<h and candidate[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;q.append((nx,ny))
    rgba=np.dstack((rgb.astype('uint8'),np.where(seen,0,255).astype('uint8'))); rgba[seen]=0
    cut=Image.fromarray(rgba); box=cut.getbbox(); assert box
    cut=cut.crop(box); scale=min(30/cut.width,46/cut.height)
    small=cut.resize((max(1,round(cut.width*scale)),max(1,round(cut.height*scale))),Image.Resampling.NEAREST)
    pal=[]
    for line in (a.inputs/'natural.gpl').read_text().splitlines():
        parts=line.split()
        if len(parts)>=3 and all(t.isdigit() for t in parts[:3]):pal.append([int(t) for t in parts[:3]])
    pal=np.array(pal,np.int32); arr=np.array(small); mask=arr[:,:,3]>0
    colors,counts=np.unique(arr[:,:,:3][mask],axis=0,return_counts=True)
    nearest=((colors.astype(np.int32)[:,None,:]-pal[None,:,:])**2).sum(2).argmin(1)
    weights=np.bincount(nearest,weights=counts,minlength=len(pal)); selected=[int(weights.argmax())]
    for _ in range(min(16,int(np.count_nonzero(weights)))-1):
        dist=((pal[:,None,:]-pal[selected][None,:,:])**2).sum(2).min(1); selected.append(int((dist*np.sqrt(weights)).argmax()))
    bank=pal[selected]; nearest=((arr[:,:,:3].astype(np.int32)[:,:,None,:]-bank[None,None,:,:])**2).sum(3).argmin(2)
    arr[:,:,:3]=bank[nearest];arr[~mask]=0
    sprite=Image.new('RGBA',(32,48));sprite.alpha_composite(Image.fromarray(arr),((32-small.width)//2,48-small.height))
    assert set(np.unique(np.array(sprite)[:,:,3])) <= {0,255}
    assert len(np.unique(np.array(sprite)[:,:,:3][np.array(sprite)[:,:,3]>0],axis=0))<=16
    a.out.mkdir(parents=True,exist_ok=True);sprite.save(a.out/'ner-static-proposal.png')
    bg=Image.open(a.inputs/'region2_village_shrine.png').convert('RGBA'); elder=Image.open(a.inputs/'walk.png').convert('RGBA').crop((0,0,32,48))
    atlas=Image.open(a.inputs/'region2_village_shrine_overlay.png').convert('RGBA'); cfg=json.loads((a.inputs/'region2_village_backdrops.json').read_text())['maps']['shrine']
    for label,cell in [('A',(7,6)),('B',(8,6))]:
        assert cfg['layout'][cell[1]][cell[0]]=='.'
        im=bg.copy();items=[]
        for ax,ay,ww,hh,x,y,row,name in cfg['overlays']['pieces']:items.append((row-0.5,0,atlas.crop((ax,ay,ax+ww,ay+hh)),(x,y)))
        items += [(7,1,elder,(12*32,6*32-16)),(cell[1]+1,1,sprite,(cell[0]*32,cell[1]*32-16))]
        for row,kind,pic,pos in sorted(items,key=lambda v:(v[0],v[1])):im.alpha_composite(pic,pos)
        im.convert('RGB').save(a.out/f'placement-{label}.png')
    # 比較は全室図。512x288の実ゲーム画面/カメラの再現とは扱わない。
    sheet=Image.new('RGB',(1040,432),'#e9e4d8');d=ImageDraw.Draw(sheet)
    d.text((8,8),'A  [7,6]    static proposal / NOT IN GAME',fill='black');d.text((528,8),'B  [8,6]    static proposal / NOT IN GAME',fill='black')
    for x,label in [(8,'A'),(528,'B')]:sheet.paste(Image.open(a.out/f'placement-{label}.png'),(x,32))
    sheet.save(a.out/'comparison.png')
    detail=Image.new('RGB',(600,480),'#e9e4d8'); dd=ImageDraw.Draw(detail)
    orig=raw.copy();orig.thumbnail((290,430),Image.Resampling.NEAREST);detail.paste(orig,((300-orig.width)//2,35))
    zoom=sprite.resize((256,384),Image.Resampling.NEAREST);detail.paste(zoom,(322,60),zoom)
    dd.text((12,10),'Owner original (unchanged)',fill='black');dd.text((320,10),'32x48 proposal / 8x nearest',fill='black')
    detail.save(a.out/'source-comparison.png')
    assert sha(a.source)==expected
    record={'source_sha256':expected,'source_size':list(raw.size),'crop':list(box),'mask_rule':'border-connected RGB min>=140 and max-min<=25; 4-neighbor','resampling':'nearest','sprite_size':[32,48],'ground_last_opaque_row':47,'palette_colors':bank.tolist(),'original_unchanged':True,'base_main':'a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf','positions':{'A':[7,6],'B':[8,6]},'elder':[12,6],'entry':[8,10],'exit':[8,11],'not_implemented':True,'not_adopted':True,'limitations':['全室の静的合成。実ゲーム512x288カメラ・主人公・入力・会話窓は未再現','初見採否前の素材案。歩行ポーズを生成・反転・複製していない','閾値の境界品質と32x48識別性は画像確認が必要']}
    record['files']={p.name:sha(p) for p in sorted(a.out.glob('*.png'))};(a.out/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(record,ensure_ascii=False))

if __name__=='__main__':main()
