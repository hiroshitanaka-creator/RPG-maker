#!/usr/bin/env python3
"""083採用chibiから再現。固定SHA不一致なら出力せず停止。原画は読取専用。"""
import argparse, hashlib, io
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png'
ADOPTED_SHA = '121010a316a31b88dca753ed48bc9404f176a4fe5f0d6dd5508ebf0615559f5d'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def reproduce(source=SOURCE):
    expected='7fb285a7c31839ff33350c328f39dfd97e94ea57a0fe6567ef862f8fb19a9aa5'
    assert sha(source)==expected
    raw=Image.open(source).convert('RGB'); rgb=np.array(raw).astype(np.int16); h,w=rgb.shape[:2]
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
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
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
    buf=io.BytesIO();sprite.save(buf,format='PNG');data=buf.getvalue()
    if hashlib.sha256(data).hexdigest()!=ADOPTED_SHA:
        raise ValueError('再現PNGが採用SHAと不一致。保存を中止する')
    if sha(source)!=expected:raise ValueError('原画SHAが変化した')
    return data

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path);a=ap.parse_args()
    data=reproduce()
    adopted=(ROOT/'docs/verification/s10-placement-preview/ner-static-proposal.png').read_bytes()
    if data!=adopted:raise ValueError('採用PNGと再生成bytesが不一致')
    target=ROOT/'assets/characters/ner/event_standing.png'
    if target.exists() and target.read_bytes()!=adopted:raise ValueError('本番PNGが採用bytesと不一致')
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(data)
    print('S10_IMPORT_PASS: adopted_sha256='+ADOPTED_SHA+' bytes='+str(len(data)))
if __name__=='__main__':main()
