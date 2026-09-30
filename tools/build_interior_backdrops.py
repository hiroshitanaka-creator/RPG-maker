"""建物の中の一枚絵の背景（依頼者の原画）と、見えない通行地図を組み立てる。

docs/port-inn-backdrop.md の方式を、港町の宿屋以外の建物へ広げる。原画は
assets/_incoming/owner-2026-09-29-interiors/ にある20枚（原本は変更しない）。

  python tools/build_interior_backdrops.py --town village|castle|port|all

1. 原画の内容の外接矩形を測り、縮小倍率を決める（1712px幅は最大0.34、1168px幅は最大0.50）。
   扉の中心が8列目、踏み段の下端が最下段（12行目）の下端になるよう、縮小後の絵を512×384pxに置く。
2. 最近傍で縮小し、natural.gpl の最も近い色へ最近傍で置き換える（64色を超えるときは、使用の少ない色から
   ほかの使用色へ寄せる）。ぼかし・中間色・半透明・拡大はしない。
3. 通行地図は tools/interior_backdrop_rooms.py の手書き定義。人物の足元が床に乗るマスだけ歩ける。
4. world/first_region.json（部屋の通行地図・住人の位置・扉の着地）、world/first_region_visuals.json
   （描画）、素材台帳、変換記録、確認用の重ね合わせ図を更新する。world/interiors.json は
   tools/build_world_interiors.py で作り直す。
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

sys.path.insert(0,str(Path(__file__).resolve().parent))
import interior_backdrop_rooms as R

ROOT=Path(__file__).resolve().parents[1]
INCOMING='assets/_incoming/owner-2026-09-29-interiors/'
RECORD='assets/source_records/interior-backdrops.json'
VERIFY=ROOT/'docs/verification/interior-backdrops'
TOWNS={'village':'start_village','castle':'first_castle','port':'first_port'}
DOORS={'start_village':'doors','first_castle':'castle_doors','first_port':'port_doors'}
CW,CH=R.COLUMNS*32,R.ROWS*32

def write(path:Path,value)->None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def palette()->np.ndarray:
    colors=[]
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
        p=line.split()
        if len(p)>=3 and all(v.isdigit() for v in p[:3]):colors.append(tuple(map(int,p[:3])))
    return np.array(colors,float)

def content_box(a:np.ndarray)->tuple[int,int,int,int]:
    """外周の暗い余白と違う画素が続く範囲（x0,x1,y0,y1）。"""
    a=a.astype(int)
    edge=np.concatenate([a[:6].reshape(-1,3),a[-6:].reshape(-1,3),a[:,:6].reshape(-1,3),a[:,-6:].reshape(-1,3)])
    bg=np.median(edge,axis=0)
    diff=np.abs(a-bg).sum(2)>45
    ys=np.where(diff.sum(1)>25)[0];xs=np.where(diff.sum(0)>25)[0]
    return int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())

def render(path:Path,cap:float)->tuple[Image.Image,dict]:
    source=Image.open(path).convert('RGB');W,H=source.size
    x0,x1,y0,y1=content_box(np.array(source))
    scale=min(cap,(CW-32)/(x1-x0),(CH-4)/(y1-y0))
    cx=W/2
    ox=(R.COLUMNS//2)*32+16-cx*scale;oy=CH-y1*scale
    w=round(W*scale);h=round(H*scale)
    small=np.array(source.resize((w,h),Image.Resampling.NEAREST)).astype(float)
    canvas=np.zeros((CH,CW,3));canvas[:,:]=small[0:3,0:3].reshape(-1,3).mean(0)
    xi=round(ox);yi=round(oy)
    sx=max(0,-xi);sy=max(0,-yi);dx=max(0,xi);dy=max(0,yi)
    ww=min(w-sx,CW-dx);hh=min(h-sy,CH-dy)
    canvas[dy:dy+hh,dx:dx+ww]=small[sy:sy+hh,sx:sx+ww]
    rgb=palette();index=((canvas[:,:,None,:]-rgb[None,None])**2).sum(3).argmin(2)
    used=np.unique(index);merged=0
    while len(used)>64:
        counts=np.bincount(index.ravel(),minlength=len(rgb));drop=min(used,key=lambda i:counts[i])
        keep=[i for i in used if i!=drop]
        nearest=((canvas[:,:,None,:]-rgb[keep][None,None])**2).sum(3).argmin(2);index=np.array(keep)[nearest]
        used=np.unique(index);merged+=1
    image=Image.fromarray(rgb[index].astype('uint8')).convert('RGBA')
    return image,dict(source_size=[W,H],content_box=[x0,x1,y0,y1],scale=round(scale,5),scaled_size=[w,h],offset=[xi,yi],colors=int(len(used)),merged_colors=merged)

def reachable(layout:list[str],start:tuple[int,int],blocked:set[tuple[int,int]]=frozenset())->set[tuple[int,int]]:
    seen={start};queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n=(x+dx,y+dy)
            if 0<=n[1]<len(layout) and 0<=n[0]<len(layout[0]) and layout[n[1]][n[0]]=='.' and n not in seen and n not in blocked:
                seen.add(n);queue.append(n)
    return seen

def stand_cells(layout:list[str],cell:tuple[int,int],reach:int,start:tuple[int,int])->list[tuple[tuple[int,int],tuple[int,int],int]]:
    """住人 cell に話しかけられる（立つマス, 向き, 距離）。距離2以上は間のマスをカウンターとみなす。"""
    blocked={cell}
    found=reachable(layout,start,blocked)
    out=[]
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        for j in range(1,reach+1):
            g=(cell[0]-dx*j,cell[1]-dy*j)
            if g in found:out.append((g,(dx,dy),j))
    return out

def overlay(image:Image.Image,layout:list[str],events:dict[str,list[int]],doors:list[tuple[int,int]])->Image.Image:
    big=image.convert('RGB').resize((CW*2,CH*2),Image.Resampling.NEAREST)
    tint=Image.new('RGBA',big.size,(0,0,0,0));d=ImageDraw.Draw(tint)
    keepers={tuple(c) for c in events.values()}
    for y,row in enumerate(layout):
        for x,c in enumerate(row):
            box=[x*64,y*64,x*64+63,y*64+63]
            if (x,y) in keepers:d.rectangle(box,fill=(40,120,255,110),outline=(40,120,255,255),width=2)
            elif (x,y) in doors:d.rectangle(box,fill=(255,220,0,90),outline=(255,220,0,255),width=2)
            elif c=='.':d.rectangle(box,fill=(40,220,80,70),outline=(40,220,80,200),width=1)
            else:d.rectangle(box,fill=(230,40,40,55),outline=(230,40,40,120),width=1)
    out=Image.alpha_composite(big.convert('RGBA'),tint).convert('RGB')
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),12);d=ImageDraw.Draw(out)
    for y in range(R.ROWS):
        for x in range(R.COLUMNS):d.text((x*64+3,y*64+1),f'{x},{y}',font=font,fill=(255,255,255))
    return out

def relink(links:list[dict],node:str,room:int,exit_cell:list[int],land_cell:list[int],door_cells:dict[str,list[int]]|None=None)->int:
    """部屋 room の出口（この部屋から出る側）と着地（この部屋へ入る側）の座標だけを変える。"""
    changed=0
    for link in links:
        a,b=link['from'],link['to']
        if a['node']==node and a['room']==room and b['room']!=room:a['cell']=list(exit_cell);changed+=1
        if b['node']==node and b['room']==room and a['room']!=room:b['cell']=list(land_cell);changed+=1
    return changed

def build(town:str)->list[str]:
    node=TOWNS[town]
    document=json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'));d=document['first_region']
    visuals=json.loads((ROOT/'world/first_region_visuals.json').read_text(encoding='utf8'))
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    record_path=ROOT/RECORD
    record=json.loads(record_path.read_text(encoding='utf8')) if record_path.exists() else dict(rooms={})
    site=next(s for s in document['sites'] if s['id']==node)
    log=[]
    for name,spec in R.ROOMS.items():
        if spec['node']!=node:continue
        room=site['rooms'][spec['room']];key=f"{node}:{spec['room']}"
        assert room['title']==spec['title'],(name,room['title'])
        original=INCOMING+spec['file'];raw=(ROOT/original).read_bytes();sha=hashlib.sha256(raw).hexdigest()
        image,info=render(ROOT/original,spec['cap'])
        assert info['colors']<=64,(name,info)
        output=f'assets/interiors/{name}.png';(ROOT/output).parent.mkdir(parents=True,exist_ok=True);image.save(ROOT/output)
        layout=R.spec(R.merged(spec['rows']))
        if spec.get('court'):layout=R.spec(spec['rows'])
        old_size=[len(room['layout'][0]),len(room['layout'])]
        room['layout']=list(layout)
        # 出入口。16×12の部屋は (8,10)/(8,11) のまま。小さかった村の部屋と中庭だけ出入口の座標を変える。
        links=d[DOORS[node]]
        if spec.get('door'):
            n=relink(links,node,spec['room'],[8,11],[8,10]);assert n==2,(name,n)
        if spec.get('court'):
            for link in links:
                a,b=link['from'],link['to']
                if a['node']==node and a['room']==1 and b['room']==0:a['cell']=[8,11]
                if a['node']==node and a['room']==0 and b['room']==1:b['cell']=[8,10]
                if a['node']==node and a['room']==1 and b['room']==2:a['cell']=[8,1]
                if a['node']==node and a['room']==2 and b['room']==1:b['cell']=[8,2]
        if name=='kaina_home':d['start']['cell']=list(spec['start'])
        door_cells=[(8,10),(8,11)] if not spec.get('court') else [(8,1),(8,2),(8,10),(8,11)]
        if spec.get('court'):door_cells=[(8,1),(8,2),(8,10),(8,11)]
        ids={e['id'] for e in room['events']}
        assert set(spec['events'])<=ids,(name,set(spec['events'])-ids)
        # 元の住人をすべて新しい図に置く（書かれていない住人は不明として失敗させる）。
        assert ids==set(spec['events']),(name,ids-set(spec['events']))
        for e in room['events']:
            e['cell']=list(spec['events'][e['id']])
            if e['id'] in spec.get('reach',{}):e['reach']=spec['reach'][e['id']]
        start=(8,10)
        for c in door_cells:assert layout[c[1]][c[0]]=='.',(name,'扉のマスが歩けない',c)
        found=reachable(layout,start)
        for c in door_cells:assert c in found,(name,'扉から届かない',c)
        for e in room['events']:
            cell=tuple(e['cell']);reach=int(e.get('reach',1))
            if e['kind'] in ('recruit',):continue
            stands=stand_cells(layout,cell,reach,start)
            assert stands,(name,e['id'],'話しかけられる場所がない')
            if reach>=2:
                assert layout[cell[1]][cell[0]]=='.' and cell not in found,(name,e['id'],'店員のマスに客が入れる')
                assert any(s[2]==reach for s in stands),(name,e['id'],'カウンター越しに立てない')
            elif e['kind']!='npc' or True:
                assert any(s[2]==1 for s in stands),(name,e['id'],'隣から話しかけられない')
            if e['kind'] in ('npc','treasure'):assert layout[cell[1]][cell[0]]=='.',(name,e['id'],'住人のマスが通行地図の上で歩けない')
        # 描画。
        m=visuals['maps'][key]
        m.update(width=R.COLUMNS,height=R.ROWS,tiles={},layers=[],layout=list(layout),backdrop=dict(path=output,offset=[0,0],size=[CW,CH]))
        outdir=VERIFY/name;outdir.mkdir(parents=True,exist_ok=True)
        overlay(image,layout,{e['id']:e['cell'] for e in room['events']},door_cells).save(outdir/'collision-overlay.png')
        entry=dict(path=output,kind='interior_backdrop',size=[CW,CH],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Claude Code（原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-29',original_file=original,prompt_record=RECORD,conversion_record=RECORD,
                   modified=f"依頼者の原画を倍率{info['scale']}で最近傍縮小し、natural.gplへ最近傍減色。周囲の余白は外周の暗色で埋めた。切り抜き・描き足し・色調補正・ぼかしなし。")
        registry['assets']=[e for e in registry['assets'] if e['path']!=output]+[entry]
        record['rooms'][name]=dict(node=node,room=spec['room'],title=spec['title'],original=original,sha256=sha,output=output,room_size_before=old_size,room_size=[R.COLUMNS,R.ROWS],
                                   layout=layout,events={k:list(v) for k,v in spec['events'].items()},**info)
        log.append(f"{name}: {old_size[0]}x{old_size[1]}→16x12 scale={info['scale']} colors={info['colors']} walkable={sum(r.count('.') for r in layout)}")
    write(ROOT/'world/first_region.json',document);write(ROOT/'world/first_region_visuals.json',visuals)
    registry['assets'].sort(key=lambda e:e['path']) if False else None
    write(ROOT/'assets/registry.json',registry)
    record['unused_originals']={'IMG_1133.png':'城の謁見の間。絵の扉は下辺の1つだけで、ゲームの謁見の間にある西の扉（宝物庫）と東の扉（書庫）がない。扉の接続を切らないため使わず、原画のまま保管する。'}
    record['note']='原画は assets/_incoming/owner-2026-09-29-interiors/ に依頼者の原本のまま保管。倍率・外接矩形・通行地図は部屋ごとに記録。'
    write(record_path,record)
    return log

def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--town',default='all',choices=['village','castle','port','all'])
    args=ap.parse_args()
    for town in (['village','castle','port'] if args.town=='all' else [args.town]):
        for line in build(town):print(f'INTERIOR_BACKDROP: {town} {line}')
    print('INTERIOR_BACKDROPS_BUILD_PASS')

if __name__=='__main__':main()
