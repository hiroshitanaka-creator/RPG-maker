"""村の採用原画だけから独立した背景・上層・通行を作る。本番イベントは接続しない。"""
from __future__ import annotations
import argparse
from collections import deque
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from backdrop_common import ROOT, palette
from village_guides import grid, overlay
from build_interior_backdrops import content_box
from build_region2_port_town_backdrop import pack
import region2_village_backdrop_defs as D
from village_png import save as save_png

RECORD = 'assets/source_records/region2-village-backdrops.json'
WORLD = 'world/region2_village_backdrops.json'
VERIFY = 'docs/verification/region2-village-backdrops'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

def nearest(a, colors):
    flat = a.reshape(-1,3).astype(np.int32)
    result = np.zeros(len(flat),np.int32)
    for start in range(0,len(flat),16384):
        diff = flat[start:start+16384,None,:]-colors[None,:,:]
        result[start:start+16384] = np.einsum('ijk,ijk->ij',diff,diff).argmin(1)
    return result.reshape(a.shape[:2])

def nearest_resize(source, size):
    # 出力の画素中心を整数比で原画へ対応させ、境界で浮動小数の丸めを使わない。
    a=np.array(source)
    width,height=size
    xs=((2*np.arange(width)+1)*source.width)//(2*width)
    ys=((2*np.arange(height)+1)*source.height)//(2*height)
    return Image.fromarray(a[ys[:,None],xs[None,:]])

def transform(source, spec):
    width,height = source.size
    columns,rows = spec['columns'],spec['rows']
    if 'scale' in spec:
        fraction = Fraction(*spec['scale']);offset=[0,0];box=[0,0,width-1,height-1]
    else:
        x0,x1,y0,y1 = box = list(content_box(np.array(source.convert('RGB'))))
        fraction = min(Fraction(1,2),Fraction(columns*32-32,x1-x0),Fraction(rows*32-4,y1-y0))
        offset=[columns//2*32+16-round(width/2*fraction),rows*32-round(y1*fraction)]
    sw,sh=round(width*fraction),round(height*fraction)
    small=nearest_resize(source.convert('RGB'),(sw,sh))
    raw=Image.new('RGB',(columns*32,rows*32),source.getpixel((0,0))[:3]);raw.paste(small,tuple(offset))
    return np.array(raw),dict(source_size=[width,height],scale=[fraction.numerator,fraction.denominator],scaled_size=[sw,sh],offset=offset,content_box=box)

def mask(points, info, spec):
    source=Image.new('L',info['source_size']);ImageDraw.Draw(source).polygon(points,fill=255)
    small=nearest_resize(source,info['scaled_size'])
    canvas=Image.new('L',(spec['columns']*32,spec['rows']*32));canvas.paste(small,tuple(info['offset']))
    return np.array(canvas)>0

def coverage(m, spec):
    return m.reshape(spec['rows'],32,spec['columns'],32)[:,16:,:,:].mean(axis=(1,3))

def connected(a, start):
    height,width=a.shape
    if not a[start[1],start[0]]:return set()
    found={tuple(start)};queue=deque(found)
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<width and 0<=ny<height and a[ny,nx] and (nx,ny) not in found:
                found.add((nx,ny));queue.append((nx,ny))
    return found

def carve(raw, shape, obj, info):
    """物の外周へつながる明るい砂・床だけを除く。港町と同じ境界洪水方式。"""
    ys,xs=np.nonzero(shape)
    if not len(xs):raise ValueError('物の画素がない: '+obj['name'])
    x0,x1,y0,y1=int(xs.min()),int(xs.max())+1,int(ys.min()),int(ys.max())+1
    rgb=raw[y0:y1,x0:x1].astype(int)
    r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    bright=(r>140)&(g>95)&(r>=g)&(g>=b)&((r-b)>35)
    outside=~shape[y0:y1,x0:x1]
    passable=bright|outside
    h,w=passable.shape
    bg=np.zeros_like(passable);queue=deque()
    for x,y in [(x,0) for x in range(w)]+[(x,h-1) for x in range(w)]+[(0,y) for y in range(h)]+[(w-1,y) for y in range(h)]:
        if passable[y,x] and not bg[y,x]:bg[y,x]=True;queue.append((x,y))
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<w and 0<=ny<h and passable[ny,nx] and not bg[ny,nx]:bg[ny,nx]=True;queue.append((nx,ny))
    candidate=shape[y0:y1,x0:x1]&~bg
    # 種がある植物はその塊だけを選び、切出し範囲内の別の壁や岩を混ぜない。
    if obj.get('seed'):
        sx,sy=obj['seed'];sw,sh=info['scaled_size'];ow,oh=info['source_size']
        sx=round(sx*sw/ow)+info['offset'][0]-x0;sy=round(sy*sh/oh)+info['offset'][1]-y0
        options=[(dx*dx+dy*dy,sx+dx,sy+dy) for dy in range(-12,13) for dx in range(-12,13) if 0<=sx+dx<w and 0<=sy+dy<h and candidate[sy+dy,sx+dx]]
        if not options:raise ValueError('種が物に乗らない: '+obj['name'])
        _,sx,sy=min(options);component=np.zeros_like(candidate);component[sy,sx]=True;queue=deque([(sx,sy)])
        while queue:
            x,y=queue.popleft()
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                nx,ny=x+dx,y+dy
                if 0<=nx<w and 0<=ny<h and candidate[ny,nx] and not component[ny,nx]:component[ny,nx]=True;queue.append((nx,ny))
        candidate=component
    result=np.zeros_like(shape);result[y0:y1,x0:x1]=candidate
    return result

def upper_layers(masks,feet,walk,spec):
    """港町の足元順の切出し方式を、任意の列・行数へ適用する。"""
    rows,columns=spec['rows'],spec['columns'];pieces={}
    for name,m in masks.items():
        f=feet[name]
        occupied=np.where(f.any(axis=0))[0]
        if not len(occupied):continue
        for y,x in np.argwhere(m.reshape(rows,32,columns,32).any(axis=(1,3))):
            fx=min(occupied,key=lambda c:(abs(int(c)-int(x)),int(c)))
            ends=[r+1 for r in range(rows) if f[r,fx] and (r==rows-1 or not f[r+1,fx]) and r+1>y]
            if not ends:continue
            bottom=min(ends)
            own=walk[y,x] and y<=bottom-2
            head=y+1<rows and walk[y+1,x] and y+1<=bottom-2
            if not (own or head):continue
            tile=m[y*32:(y+1)*32,x*32:(x+1)*32].copy()
            if not own:tile[:16]=False
            if tile.any():pieces.setdefault((name,bottom),np.zeros_like(m))[y*32:(y+1)*32,x*32:(x+1)*32]|=tile
    return pieces

def derive(role,spec):
    source_path=ROOT/spec['original'];raw_bytes=source_path.read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest()!=spec['sha256']:raise ValueError('原本不一致: '+role)
    with Image.open(source_path) as source:raw,info=transform(source,spec)
    colors=palette()[:80].astype(np.int32);indices=nearest(raw,colors)
    counts=np.bincount(indices.ravel(),minlength=len(colors));used=np.where(counts>0)[0]
    selected=sorted(sorted(used,key=lambda c:(-int(counts[c]),int(c)))[:64])
    indices=nearest(raw,colors[selected]);rgb=colors[selected][indices].astype('uint8')
    if spec['floor'] is None:walk=np.ones((spec['rows'],spec['columns']),bool)
    else:walk=coverage(mask(spec['floor'],info,spec),spec)>=.70
    masks={};feet={};blocked=np.zeros_like(walk)
    for item in spec['objects']:
        silhouette=mask(item['shape'],info,spec)
        if item.get('carve'):silhouette=carve(raw,silhouette,item,info)
        masks[item['name']]=silhouette
        footprint=coverage(mask(item['foot'],info,spec),spec)>=.35
        feet[item['name']]=footprint;blocked|=footprint
    for shape in spec['blocks']:blocked|=coverage(mask(shape,info,spec),spec)>=.35
    walk&=~blocked
    if role=='exterior':
        walk[0]=walk[-1]=False;walk[:,0]=walk[:,-1]=False
        for cell in spec['doors'].values():
            x,y=cell;walk[y,x]=True;walk[y+1,x]=True
    found=connected(walk,spec['start'])
    if not found:raise ValueError('開始点が床に乗らない: '+role)
    for label,cell in {**spec['doors'],**spec['targets']}.items():
        if tuple(cell) not in found:raise ValueError('到達できない: '+role+'/'+label+' '+str(cell))
    isolated=[]
    for y,x in np.argwhere(walk):
        if (int(x),int(y)) not in found:walk[y,x]=False;isolated.append([int(x),int(y)])
    pieces=upper_layers(masks,feet,walk,spec)
    if not pieces:raise ValueError('上の層がない: '+role)
    atlas,table=pack(pieces,rgb)
    padded=Image.new('RGBA',(atlas.width,((atlas.height+31)//32)*32));padded.paste(atlas,(0,0))
    folder='town_backdrops' if role=='exterior' else 'interiors'
    background=f'assets/{folder}/region2_village_{role}.png'
    upper=f'assets/{folder}/region2_village_{role}_overlay.png'
    image=Image.fromarray(rgb).convert('RGBA')
    layout=[''.join('.' if v else '#' for v in row) for row in walk]
    map_data=dict(version=1,id='region2_village_'+role,tile_size=32,width=spec['columns'],height=spec['rows'],origin=[0,0],tiles={},layers=[],layout=layout,surround='assets/tiles/region2_sand.png',backdrop=dict(path=background,offset=[0,0]),overlays=dict(path=upper,fields=['atlas_x','atlas_y','w','h','x','y','bottom_row','object'],pieces=table))
    record=dict(original=spec['original'],sha256=spec['sha256'],source='依頼者提供の採用原画。原本は無加工で保管。生成手段を独立に確認した記録ではない。',**info,canvas=list(image.size),colors=len(np.unique(rgb.reshape(-1,3),axis=0)),palette_indices=[int(v) for v in selected],palette_used=[list(map(int,c)) for c in colors[selected]],objects=spec['objects'],additional_blocks=spec['blocks'],floor_polygon=spec['floor'],foot_coverage_min=.35,floor_coverage_min=.70,start=spec['start'],doors=spec['doors'],targets=spec['targets'],layout=layout,isolated_cells=isolated,walkable_cells=int(walk.sum()),overlays=dict(path=upper,size=list(padded.size),pieces=table),background=background)
    return image,padded,map_data,record,walk

def build(destination):
    document=dict(version=1,status='独立した地形・施設土台。本番イベント・保存先・施設機能は未接続',maps={})
    records=dict(version=1,baseline_commit='dad3fca1d2d6216c3418999d27a4cf581ca00860',method='原画の最近傍縮小、natural.gplの選択64色への最近傍減色、同じ背景画素から二値透過の上層を切出し。平均化・描足し・色調補正なし。',palette='assets/palette/natural.gpl',palette_sha256='1b1c00dd929b96b64703972a0ae9368c36636b96c8f717dded78524e57913088',maps={})
    outputs=[]
    for role,spec in D.MAPS.items():
        image,atlas,map_data,record,walk=derive(role,spec)
        document['maps'][role]=map_data;records['maps'][role]=record
        for path,picture in [(record['background'],image),(record['overlays']['path'],atlas)]:
            full=destination/path;full.parent.mkdir(parents=True,exist_ok=True);save_png(picture,full);outputs.append(path)
        directory=destination/VERIFY/role;directory.mkdir(parents=True,exist_ok=True)
        save_png(grid(image,spec['columns'],spec['rows'],1),directory/'grid.png')
        save_png(overlay(image,record['layout'],{tuple(c):'door' for c in spec['doors'].values()},1),directory/'collision-overlay.png')
        save_png(Image.fromarray((walk.repeat(32,0).repeat(32,1)*255).astype('uint8')),directory/'walk-mask.png')
        union=np.zeros((image.height,image.width),bool)
        a=np.array(atlas)
        for ax,ay,w,h,x,y,_,_ in record['overlays']['pieces']:union[y:y+h,x:x+w]|=a[ay:ay+h,ax:ax+w,3]>0
        save_png(Image.fromarray((union*255).astype('uint8')),directory/'upper-mask.png')
        source=Image.open(ROOT/spec['original']).convert('RGB')
        original_canvas,_=transform(source,spec)
        panel=Image.new('RGB',(image.width*2,image.height+24),(24,24,30));panel.paste(Image.fromarray(original_canvas),(0,24));panel.paste(image.convert('RGB'),(image.width,24))
        font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),14);draw=ImageDraw.Draw(panel)
        draw.text((8,2),'原画の最近傍縮小（減色前）',font=font,fill='white');draw.text((image.width+8,2),'派生背景（規定パレット）',font=font,fill='white');save_png(panel,directory/'source-comparison.png')
        print('VILLAGE_BUILD: '+role+' colors='+str(record['colors'])+' walk='+str(record['walkable_cells'])+' pieces='+str(len(record['overlays']['pieces'])),flush=True)
    write(destination/WORLD,document);write(destination/RECORD,records)
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    registry['assets']=[entry for entry in registry['assets'] if entry['path'] not in outputs]
    for role,record in records['maps'].items():
        common=dict(status='required',palette='assets/palette/natural.gpl',source='generated',tool='依頼者提供原画 + Python/Pillow（派生変換）',author='RPG-maker / Codex（原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-10-04',original_file=record['original'],prompt_record=RECORD+'#maps/'+role,conversion_record=RECORD+'#maps/'+role,max_colors=64)
        registry['assets'].append(dict(path=record['background'],kind='town_backdrop' if role=='exterior' else 'interior_backdrop',size=record['canvas'],modified='採用原画を記録した最近傍縮小・配置・64色以内の最近傍減色だけで派生。原画は変更しない。本番イベントは未接続。',**common))
        registry['assets'].append(dict(path=record['overlays']['path'],kind='town_overlay',size=record['overlays']['size'],modified='背景と同一画素を足元の順で重ねる上層へ切出し。アルファは0/255、原画への描足しなし。',**common))
    write(destination/'assets/registry.json',registry)
    print('VILLAGE_BACKDROPS_BUILD_PASS: maps=5 assets=10')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-root',type=Path,default=ROOT);args=parser.parse_args();build(args.output_root.resolve())
