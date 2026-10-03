"""第2港の外観の背景が、原画の最近傍縮小と natural.gpl への最近傍減色だけで作られていること（ぼかし・にじみがない）を検査する。

Pillow だけで動く（CI の素材検査と同じ環境）。
 1. 原本のSHA-256が記録と一致する。
 2. 背景の各画素は、原画の「ただ1つの画素」（縮小前の対応位置）の色だけから決まる：
    その画素に最も近い、背景で使われた色と一致する。平均化・補間・重み付けがあれば一致しない。
 3. 背景は不透明、64色以内、全色が natural.gpl にある。大きさは 1440×960。
 4. 上の層の画素は全て背景の同じ位置の画素と同じ色で、アルファは0か255だけ。
"""
import hashlib,json,sys
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL='assets/_incoming/owner-2026-10-01-region2-port/FE4B1B12-C9B1-4DB0-B374-81F51D061BA6.PNG'
SHA='996ecd98050831b0e45a06ddf0fb26708ad91db37891d523ba27916e14571296'
BACKDROP='assets/town_backdrops/region2_port.png'
RECORD='assets/source_records/region2-port-town-backdrop.json'

def palette():
    colors=set()
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
        p=line.split()
        if len(p)>=3 and all(v.isdigit() for v in p[:3]):colors.add(tuple(map(int,p[:3])))
    return colors

def main():
    errors=[]
    raw=(ROOT/ORIGINAL).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:errors.append('原本のSHA-256が記録と一致しない')
    source=Image.open(ROOT/ORIGINAL).convert('RGB');back=Image.open(ROOT/BACKDROP)
    record=json.loads((ROOT/RECORD).read_text(encoding='utf8'))
    num,den=record['scale']
    W,H=source.width*num//den,source.height*num//den
    if back.size!=(W,H) or back.size!=(1440,960):errors.append(f'背景の大きさが不正: {back.size}')
    back=back.convert('RGBA');bp=back.load();sp=source.load()
    used={}
    for y in range(H):
        for x in range(W):
            r,g,b,a=bp[x,y]
            if a!=255:errors.append('背景に透明画素がある');break
            used[(r,g,b)]=used.get((r,g,b),0)+1
    if len(used)>64:errors.append(f'背景の色数が多い: {len(used)}')
    outside=set(used)-palette()
    if outside:errors.append(f'natural.gpl にない色: {sorted(outside)[:5]}')
    colors=list(used);cache={};bad=0;first=None
    for y in range(H):
        sy=min(source.height-1,(2*y+1)*den//(2*num))
        for x in range(W):
            sx=min(source.width-1,(2*x+1)*den//(2*num))
            c=sp[sx,sy];n=cache.get(c)
            if n is None:
                n=min(colors,key=lambda k:(k[0]-c[0])**2+(k[1]-c[1])**2+(k[2]-c[2])**2);cache[c]=n
            got=bp[x,y][:3]
            # 最も近い色と同じ距離なら一致（同距離の色が複数あるときの選び方の差は許す）
            if got!=n and (got[0]-c[0])**2+(got[1]-c[1])**2+(got[2]-c[2])**2!=(n[0]-c[0])**2+(n[1]-c[1])**2+(n[2]-c[2])**2:
                bad+=1
                if first is None:first=(x,y,c,got,n)
    if bad:errors.append(f'原画1画素の色だけから決まらない画素が {bad} ある（最初: {first}）')
    ov=record['upper_layer'];atlas=Image.open(ROOT/ov['path']).convert('RGBA');ap=atlas.load()
    data=json.loads((ROOT/'world/region2_port.json').read_text(encoding='utf8'))
    pieces=data['maps']['brine_port:0']['overlays']['pieces'];pixels=0;diff=0
    for ax,ay,w,h,x,y,bottom,name in pieces:
        for j in range(h):
            for i in range(w):
                pr,pg,pb,pa=ap[ax+i,ay+j]
                if pa not in (0,255):errors.append('上の層のアルファが0/255以外');return finish(errors)
                if pa:
                    pixels+=1
                    if (pr,pg,pb)!=bp[x+i,y+j][:3]:diff+=1
    if diff or not pixels:errors.append(f'上の層の画素が背景と異なる: {diff} / {pixels}')
    return finish(errors,len(used),pixels,len(cache))

def finish(errors,colors=0,pixels=0,sources=0):
    for e in errors:print('REGION2_BACKDROP_PY_FAIL:',e)
    if errors:return 1
    print(f'REGION2_BACKDROP_PY_PASS: 背景は原画の最近傍縮小+最近傍減色のみ（使用{colors}色、原画の色{sources}種を確認）、上の層{pixels}画素が背景と同一')
    return 0

if __name__=='__main__':sys.exit(main())
