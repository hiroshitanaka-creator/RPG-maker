"""第2港の外観を、依頼者の原画1枚まるごとの背景＋見えない通行地図＋上の層にする。

建物の中（docs/port-inn-backdrop.md）と同じ規則：原画全体を最近傍で縮小し、natural.gpl へ最近傍で減色する。
拡大・ぼかし・半透明・色調補正はしない。原本は変更しない。

建物の中との違いは次の2点。
1. 町は画面より広い（45×30マス）。絵は1枚のまま敷き、画面は FirstRegionView の既存のカメラで動く。
2. 屋根・ヤシの葉・石柱の上・アーチ・帆柱は人物より手前に見える部分がある。そこだけを原画から切り出して
   「上の層」の部品にし、人物と同じ足元の順（bottom）で重ねる。部品は 1 枚の素材（アトラス）にまとめる。

使い方: python tools/build_region2_port_town_backdrop.py
  前提: python tools/extend_natural_water.py を実行済み（海の青4色が natural.gpl に入っていること）。
  world/region2_port.json は tools/build_region2_port.py が作ったものへ、この外観を上書きする（何度実行しても同じ）。
"""
import hashlib,json
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import region2_port_town_defs as D
from import_region2_port_assets import CUTS
from backdrop_common import palette,ROOT

ORIGINAL='assets/_incoming/owner-2026-10-01-region2-port/FE4B1B12-C9B1-4DB0-B374-81F51D061BA6.PNG'
ORIGINAL_SHA='996ecd98050831b0e45a06ddf0fb26708ad91db37891d523ba27916e14571296'
BACKDROP='assets/town_backdrops/region2_port.png'
OVERLAY='assets/town_backdrops/region2_port_overlay.png'
RECORD='assets/source_records/region2-port-town-backdrop.json'
VERIFY=ROOT/'docs/verification/region2-port-backdrop'
K=D.SCALE_NUM/D.SCALE_DEN
W,H=D.COLUMNS*32,D.ROWS*32
SPAWN=(4,4)   # 石のアーチの南。世界マップから入ったとき着く
EXIT=(4,1)    # アーチの下。ここへ入ると世界マップへ出る
DOCK=(34,21)  # 中央桟橋の板。船のすぐ隣で乗り降りする
NPCS={'fisher':dict(cell=[30,24]),'merchant':dict(cell=[15,11]),
      'child':dict(cell=[17,13],patrol=[[17,13],[18,13],[18,14],[17,14]]),
      'traveller':dict(cell=[6,4],patrol=[[6,4],[7,4],[7,5],[6,5]])}

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

# ---------------------------------------------------------------- 絵 ----
def scaled_and_quantized():
    raw=(ROOT/ORIGINAL).read_bytes();assert hashlib.sha256(raw).hexdigest()==ORIGINAL_SHA,'原本が記録と一致しない'
    source=Image.open(ROOT/ORIGINAL).convert('RGB');assert source.size==(1536,1024)
    # 最近傍：出力の (x,y) は原画の ((2x+1)*16//30, (2y+1)*16//30) の1画素そのもの。整数だけで決める（平均化・補間なし）。
    columns=(2*np.arange(W)+1)*D.SCALE_DEN//(2*D.SCALE_NUM);rows=(2*np.arange(H)+1)*D.SCALE_DEN//(2*D.SCALE_NUM)
    small=np.array(source)[rows][:,columns]
    pal=palette();flat=small.reshape(-1,3).astype(float)
    nearest=((flat[:,None,:]-pal[None])**2).sum(2).argmin(1)
    counts=np.bincount(nearest,minlength=len(pal)).astype(float);keep=[int(i) for i in np.flatnonzero(counts)]
    pp=((pal[:,None]-pal[None])**2).sum(2);dropped=[]
    while len(keep)>64:   # 1枚64色以内。除いても最も目立たない色から外す
        cost,color=min((counts[c]*pp[c,[o for o in keep if o!=c]].min(),c) for c in keep)
        keep.remove(color);dropped.append((tuple(int(v) for v in pal[color]),int(counts[color])))
    chosen=pal[keep]
    index=((flat[:,None,:]-chosen[None])**2).sum(2).argmin(1)
    out=chosen[index].astype('uint8').reshape(H,W,3)
    return small,out,[tuple(int(v) for v in c) for c in chosen],dropped,hashlib.sha256(raw).hexdigest()

def sand_like(small):
    s=small.astype(float)/255;r,g,b=s[...,0],s[...,1],s[...,2];mx=s.max(2);mn=s.min(2)
    sat=(mx-mn)/np.maximum(mx,1e-6);d=np.maximum(mx-mn,1e-6)
    hue=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))/6
    return (r>=g)&(g>=b)&(sat>0.38)&(mx>0.55)&(hue>0.075)&(hue<0.16)

def flood(passable,starts,diagonal):
    """passable（bool配列）の中で starts から続く画素。"""
    h,w=passable.shape;seen=np.zeros_like(passable);queue=deque()
    for x,y in starts:
        if 0<=x<w and 0<=y<h and passable[y,x] and not seen[y,x]:seen[y,x]=True;queue.append((x,y))
    steps=[(1,0),(-1,0),(0,1),(0,-1)]+([(1,1),(1,-1),(-1,1),(-1,-1)] if diagonal else [])
    while queue:
        x,y=queue.popleft()
        for dx,dy in steps:
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and passable[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;queue.append((nx,ny))
    return seen

# ---------------------------------------------------------------- 通行地図 ----
def rect(grid,r,value):
    x0,y0,x1,y1=r[:4];grid[y0:y1+1,x0:x1+1]=value

def polygon_mask(points):
    m=Image.new('L',(W,H));ImageDraw.Draw(m).polygon([(x*K,y*K) for x,y in points],fill=255);return np.array(m)>0

def cell_coverage(mask,lower_half=True):
    top=16 if lower_half else 0
    return mask.reshape(D.ROWS,32,D.COLUMNS,32)[:,top:,:,:].mean(axis=(1,3))

def layout(small):
    water=(small[:,:,2].astype(int)>small[:,:,0]+60)&(small[:,:,2].astype(int)>small[:,:,1]+20)
    land=cell_coverage(water)<.5
    blocked=np.zeros((D.ROWS,D.COLUMNS),bool);foot={}
    for name,maxrow,door,front in D.BUILDINGS:
        coverage=cell_coverage(polygon_mask(CUTS[name][1]));f=coverage>=.35
        f[maxrow+1:,:]=False;f[door[1],door[0]]=False;f[front[1],front[0]]=False
        foot[name]=f;blocked|=f
    for r in D.BLOCK:rect(blocked,r,True)
    walk=land&~blocked
    for r in D.PIER:rect(walk,r,True)
    for r in D.HARD_BLOCK:rect(walk,r,False)
    for r in D.FORCE_WALK:rect(walk,r,True)
    walk[0,:]=walk[-1,:]=False;walk[:,0]=walk[:,-1]=False
    for name,maxrow,door,front in D.BUILDINGS:walk[door[1],door[0]]=True;walk[front[1],front[0]]=True
    return walk,foot

def reachable(walk,start):
    seen={start};queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n=(x+dx,y+dy)
            if 0<=n[0]<D.COLUMNS and 0<=n[1]<D.ROWS and walk[n[1],n[0]] and n not in seen:seen.add(n);queue.append(n)
    return seen

def prune(walk):
    """入口から歩いて行けない飛び地は、絵の飾りとして通れない扱いにする。"""
    found=reachable(walk,SPAWN);cut=[]
    for y in range(D.ROWS):
        for x in range(D.COLUMNS):
            if walk[y,x] and (x,y) not in found:walk[y,x]=False;cut.append((x,y))
    return cut

# ---------------------------------------------------------------- 上の層 ----
def build_objects(small,foot):
    sandy=sand_like(small);masks={}
    for name,maxrow,door,front in D.BUILDINGS:masks[name]=polygon_mask(CUTS[name][1])
    for obj in D.OBJECTS:
        kind=obj['shape'][0]
        if kind=='poly':
            mask=polygon_mask([(x,y) for x,y in CUTS[obj['shape'][1]][1]])
            if obj.get('hole'):mask&=~polygon_mask(obj['hole'])
        elif kind=='rects':
            mask=np.zeros((H,W),bool)
            for x0,y0,x1,y1 in obj['shape'][1]:mask[y0:y1,x0:x1]=True
        else:
            _,(cx0,cy0,cx1,cy1),seeds=obj['shape']
            x0,y0,x1,y1=[int(round(v*32)) for v in (cx0,cy0,cx1,cy1)];x1=min(x1,W);y1=min(y1,H)
            sub=sandy[y0:y1,x0:x1]
            border=[(x,0) for x in range(x1-x0)]+[(x,y1-y0-1) for x in range(x1-x0)]+[(0,y) for y in range(y1-y0)]+[(x1-x0-1,y) for y in range(y1-y0)]
            holes=[(int(round(hx*32))-x0,int(round(hy*32))-y0) for hx,hy in obj.get('hole_seeds',[])]
            background=flood(sub,border+holes,False);fg=~background
            for name in obj.get('exclude',[]):fg&=~masks[name][y0:y1,x0:x1]
            starts=[]
            for sx,sy in seeds:
                px,py=int(round(sx*32))-x0,int(round(sy*32))-y0
                best=None
                for dy in range(-10,11):
                    for dx in range(-10,11):
                        qx,qy=px+dx,py+dy
                        if 0<=qx<fg.shape[1] and 0<=qy<fg.shape[0] and fg[qy,qx] and (best is None or dx*dx+dy*dy<best[0]):best=(dx*dx+dy*dy,(qx,qy))
                assert best,('種の点が物の上にない',obj['name'])
                starts.append(best[1])
            comp=flood(fg,starts,True);mask=np.zeros((H,W),bool);mask[y0:y1,x0:x1]=comp
        masks[obj['name']]=mask
    feet={}
    for obj in D.OBJECTS:
        f=np.zeros((D.ROWS,D.COLUMNS),bool)
        for r in obj['foot']:rect(f,r,True)
        feet[obj['name']]=f
    for name in foot:feet[name]=foot[name]
    return masks,feet

def column_runs(f):
    runs={}
    for x in range(D.COLUMNS):
        col=f[:,x];y=0;out=[]
        while y<D.ROWS:
            if col[y]:
                t=y
                while y<D.ROWS and col[y]:y+=1
                out.append((t,y))
            else:y+=1
        if out:runs[x]=out
    return runs

def foot_row(runs,x,row):
    """列 x の row 行にある物の足元の行（bottom、下端の次の行）。足元より下の画素なら None。"""
    if x not in runs:
        x=min(runs,key=lambda c:(abs(c-x),c))
    for top,bottom in runs[x]:
        if bottom>row:return bottom
    return None

def upper_layer(masks,feet,walk):
    """人物の足元より奥にいる間だけ人物より手前に見える画素を選ぶ。戻り値 {(物,足元の行): 画素のbool配列}。"""
    pieces={}
    for name,mask in masks.items():
        f=feet[name]
        if not f.any():continue
        runs=column_runs(f);cells=mask.reshape(D.ROWS,32,D.COLUMNS,32).any(axis=(1,3))
        for r in range(D.ROWS):
            for x in range(D.COLUMNS):
                if not cells[r,x]:continue
                bottom=foot_row(runs,x,r)
                if bottom is None:continue
                own=bool(walk[r,x]) and r<=bottom-2
                head=r+1<D.ROWS and bool(walk[r+1,x]) and r+1<=bottom-2
                if not (own or head):continue
                block=mask[r*32:(r+1)*32,x*32:(x+1)*32]
                sel=np.zeros_like(block)
                if own:sel[:]=block
                elif head:sel[16:,:]=block[16:,:]
                if not sel.any():continue
                pieces.setdefault((name,bottom),np.zeros((H,W),bool))[r*32:(r+1)*32,x*32:(x+1)*32]|=sel
    return pieces

def pack(pieces,image):
    """部品を1枚の素材（アトラス）に並べる。戻り値 (RGBA, [[ax,ay,w,h,x,y,bottom,名前]...])。"""
    items=[]
    for (name,bottom),mask in sorted(pieces.items()):
        ys,xs=np.nonzero(mask);x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
        items.append((name,bottom,int(x0),int(y0),mask[y0:y1,x0:x1],image[y0:y1,x0:x1]))
    items.sort(key=lambda it:(-it[4].shape[0],it[0],it[1]))
    width=1024;x=y=shelf=0;placed=[]
    for name,bottom,px,py,m,rgb in items:
        h,w=m.shape
        if x+w>width:x=0;y+=shelf;shelf=0
        placed.append((x,y,name,bottom,px,py,m,rgb));x+=w;shelf=max(shelf,h)
    height=y+shelf
    atlas=np.zeros((height,width,4),'uint8');table=[]
    for ax,ay,name,bottom,px,py,m,rgb in placed:
        h,w=m.shape;tile=atlas[ay:ay+h,ax:ax+w];tile[m,:3]=rgb[m];tile[m,3]=255
        table.append([ax,ay,w,h,px,py,int(bottom),name])
    return Image.fromarray(atlas),table

# ---------------------------------------------------------------- 確認図 ----
def rows_of(walk):return [''.join('.' if walk[y,x] else '#' for x in range(D.COLUMNS)) for y in range(D.ROWS)]

def collision_overlay(image,walk,marks,pieces_mask=None,zoom=2):
    base=Image.fromarray(image).convert('RGBA').resize((W*zoom,H*zoom),Image.Resampling.NEAREST)
    tint=Image.new('RGBA',base.size,(0,0,0,0));d=ImageDraw.Draw(tint);z=32*zoom
    for y in range(D.ROWS):
        for x in range(D.COLUMNS):
            box=[x*z,y*z,x*z+z-1,y*z+z-1];mark=marks.get((x,y))
            if mark=='npc':d.rectangle(box,fill=(40,120,255,120),outline=(40,120,255,255),width=2)
            elif mark=='door':d.rectangle(box,fill=(255,220,0,110),outline=(255,220,0,255),width=2)
            elif mark=='dock':d.rectangle(box,fill=(0,230,230,110),outline=(0,230,230,255),width=2)
            elif walk[y,x]:d.rectangle(box,fill=(40,220,80,70),outline=(40,220,80,200),width=1)
            else:d.rectangle(box,fill=(230,40,40,85),outline=(230,40,40,130),width=1)
    out=Image.alpha_composite(base,tint)
    if pieces_mask is not None:
        m=Image.fromarray((pieces_mask*255).astype('uint8')).resize(out.size,Image.Resampling.NEAREST)
        magenta=Image.new('RGBA',out.size,(255,0,255,150));out=Image.alpha_composite(out,Image.composite(magenta,Image.new('RGBA',out.size,(0,0,0,0)),m))
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),11);d=ImageDraw.Draw(out)
    for y in range(D.ROWS):
        for x in range(D.COLUMNS):d.text((x*z+2,y*z+1),f'{x},{y}',font=font,fill=(255,255,255),stroke_width=1,stroke_fill=(0,0,0))
    return out.convert('RGB')

# ---------------------------------------------------------------- 本番データ ----
def integrate(walk,table):
    path=ROOT/'world/region2_port.json';data=json.loads(path.read_text(encoding='utf8'))
    rows=rows_of(walk)
    exterior=data['maps']['brine_port:0']
    exterior.clear()
    exterior.update(version=1,id='region2_port',tile_size=32,width=D.COLUMNS,height=D.ROWS,origin=[0,0],tiles={},layers=[],layout=rows,
                    surround='assets/tiles/region2_sand.png',backdrop=dict(path=BACKDROP,offset=[0,0]),
                    overlays=dict(path=OVERLAY,fields=['atlas_x','atlas_y','w','h','x','y','bottom_row','object'],pieces=table))
    room=data['site']['rooms'][0];room['layout']=rows
    for event in room['events']:
        spec=NPCS[event['id'].replace('sand_','')];event['cell']=spec['cell']
        if 'patrol' in spec:event['patrol']=spec['patrol']
        else:event.pop('patrol',None)
    for event in room['events']:assert walk[event['cell'][1]][event['cell'][0]],event['id']
    definition=data['definition'];node='brine_port'
    point=lambda room_index,cell:dict(layer='interior',node=node,room=room_index,cell=list(cell))
    definition['second_port_spawn']=point(0,SPAWN);definition['second_port_exit']=point(0,EXIT)
    index={'inn':1,'item':2,'weapon':3,'armor':4,'shrine':5,'harbor':6}
    doors=[]
    for name,maxrow,door,front in D.BUILDINGS:
        if name in index:
            doors.append({'from':point(0,door),'to':point(index[name],[8,10])})
            doors.append({'from':point(index[name],[8,11]),'to':point(0,front)})
    definition['second_port_doors']=doors
    dock=data['docks'][0];dock['land']=point(0,DOCK);dock['display_cell']=list(DOCK)
    data['note']='外観は依頼者の原画1枚の背景＋見えない通行地図＋上の層（tools/build_region2_port_town_backdrop.py）。部品を並べた旧外観は tools/build_region2_port.py で再生成できる。'
    write(path,data)

def register(small_info):
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    paths={BACKDROP,OVERLAY};registry['assets']=[e for e in registry['assets'] if e['path'] not in paths]
    common=dict(status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Claude Code（原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-10-03',original_file=ORIGINAL,prompt_record=RECORD,conversion_record=RECORD,max_colors=64)
    registry['assets'].append(dict(path=BACKDROP,kind='town_backdrop',size=[W,H],modified='港町の外観：依頼者の原画全体を倍率15/16で最近傍縮小し、natural.gplへ最近傍減色（64色以内）。切り抜き・描き足し・色調補正・ぼかしなし。',**common))
    registry['assets'].append(dict(path=OVERLAY,kind='town_overlay',size=list(small_info),modified='港町の「上の層」：背景と同じ画素のうち、人物より手前に見える部分（屋根・ヤシの葉・石柱の上・アーチ・帆柱）だけを切り出して並べた素材。背景と同じ画素で、アルファは0/255のみ。',**common))
    write(ROOT/'assets/registry.json',registry)

def main():
    VERIFY.mkdir(parents=True,exist_ok=True);(ROOT/BACKDROP).parent.mkdir(parents=True,exist_ok=True)
    small,image,colors,dropped,sha=scaled_and_quantized()
    Image.fromarray(image).convert('RGBA').save(ROOT/BACKDROP)
    walk,foot=layout(small);cut=prune(walk)
    masks,feet=build_objects(small,foot)
    pieces=upper_layer(masks,feet,walk)
    atlas,table=pack(pieces,image);atlas.save(ROOT/OVERLAY)
    found=reachable(walk,SPAWN)
    for name,maxrow,door,front in D.BUILDINGS:assert door in found and front in found,('扉へ行けない',name)
    assert DOCK in found and EXIT in found and SPAWN in found
    for spec in NPCS.values():
        assert tuple(spec['cell']) in found
        for c in spec.get('patrol',[]):assert tuple(c) in found
    integrate(walk,table);register(atlas.size)
    marks={tuple(door):'door' for _,_,door,_ in D.BUILDINGS};marks[EXIT]='door';marks[DOCK]='dock'
    for spec in NPCS.values():marks[tuple(spec['cell'])]='npc'
    union=np.zeros((H,W),bool)
    for m in pieces.values():union|=m
    collision_overlay(image,walk,marks).save(VERIFY/'collision-overlay.png')
    collision_overlay(image,walk,marks,union).save(VERIFY/'collision-and-upper-layer-overlay.png')
    write(ROOT/RECORD,dict(original=ORIGINAL,sha256=sha,source='依頼者の原画（港町の外観）。バイト列を変更せず保管。',
        method='一枚絵の背景＋見えない通行地図＋上の層。最近傍縮小（倍率15/16）、natural.gplへ最近傍減色。',scale=[D.SCALE_NUM,D.SCALE_DEN],canvas=[W,H],cells=[D.COLUMNS,D.ROWS],
        colors=len(colors),palette_used=[list(c) for c in colors],dropped_for_64=[dict(rgb=list(c),pixels=n) for c,n in dropped],
        palette_extension='assets/source_records/natural-water-extension.json',
        spawn=list(SPAWN),exit=list(EXIT),dock=list(DOCK),doors={n:list(d) for n,_,d,_ in D.BUILDINGS},
        pruned_isolated_cells=[list(c) for c in cut],layout=rows_of(walk),
        upper_layer=dict(path=OVERLAY,size=list(atlas.size),pieces=len(table),objects=sorted({t[7] for t in table}))))
    print('REGION2_TOWN_BACKDROP_BUILD_PASS: colors=%d walkable=%d pieces=%d atlas=%s pruned=%d dropped_colors=%d'%(len(colors),walk.sum(),len(table),atlas.size,len(cut),len(dropped)))

if __name__=='__main__':main()
