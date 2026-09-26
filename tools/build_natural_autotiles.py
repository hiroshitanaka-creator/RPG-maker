#!/usr/bin/env python3
"""8近傍の47接続形を生成する。絵は登録済み生成素材のみから合成する。"""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from import_visual_target_assets import PAL,quantize

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/art-review-2'
DIRS=[(0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)]

def canonical(m):
    for diagonal,a,b in [(4,0,1),(5,1,2),(6,2,3),(7,3,0)]:
        if not(m&(1<<a) and m&(1<<b)):m&=~(1<<diagonal)
    return m

MASKS=sorted({canonical(m) for m in range(256)})
assert len(MASKS)==47

def shape(m,radius=4):
    """四半セルで外角・内角・直線を接続。端の形は近傍の同じ情報だけで決める。"""
    y,x=np.mgrid[:32,:32];out=np.zeros((32,32),bool)
    for left,top,side_x,side_y,diag in [(True,True,3,0,7),(False,True,1,0,4),(False,False,1,2,5),(True,False,3,2,6)]:
        xx=x+.5 if left else 31.5-x;yy=y+.5 if top else 31.5-y
        q=(xx<16)&(yy<16);a=bool(m&(1<<side_x));b=bool(m&(1<<side_y))
        wave_x=np.sin(xx*np.pi/16)*np.sin(xx*3*np.pi/16)
        wave_y=np.sin(yy*np.pi/16)*np.sin(yy*3*np.pi/16)
        if a and b:inside=np.ones_like(q) if m&(1<<diag) else xx*xx+yy*yy>=radius*radius
        elif a:inside=yy>=radius+wave_x
        elif b:inside=xx>=radius+wave_y
        else:inside=(xx-16)**2+(yy-16)**2<=(16-radius)**2
        out|=q&inside
    return out

def neighbor_mask(field,x,y):
    h,w=field.shape
    return canonical(sum(1<<i for i,(dx,dy) in enumerate(DIRS) if 0<=x+dx<w and 0<=y+dy<h and field[y+dy,x+dx]))

def read(id_):return np.array(Image.open(ROOT/f'assets/tiles/{id_}.png').convert('RGBA'))

def phase(a,x,y):
    yy,xx=np.mgrid[:32,:32]
    return a[(yy+y*32)%a.shape[0],(xx+x*32)%a.shape[1]]

def main():
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'));entries={e['path']:e for e in registry['assets']}
    grass=read('natural_grass');dirt=read('natural_dirt');water=read('natural_water');rock=read('natural_cave_rock');cave=read('natural_cave_floor')
    void=np.zeros((64,64,4),dtype=np.uint8);void[:,:,:3]=PAL[np.argmin(PAL.sum(axis=1))];void[:,:,3]=255
    families=[('dirt',dirt,grass,None),('cobble',read('natural_cobble'),grass,None),('river',water,grass,rock),('lake',water,cave,rock),('cave',cave,void,rock),('forest',read('bright_forest'),grass,None),('mountains',read('bright_mountains'),grass,None),('hills',read('bright_hills'),grass,None),('shore',grass,water,rock)]
    source_names={'dirt':['natural_dirt','natural_grass'],'cobble':['natural_cobble','natural_grass'],'river':['natural_water','natural_grass','natural_cave_rock'],'lake':['natural_water','natural_cave_floor','natural_cave_rock'],'cave':['natural_cave_floor','natural_cave_rock'],'forest':['bright_forest','natural_grass'],'mountains':['bright_mountains','natural_grass'],'hills':['bright_hills','natural_grass'],'shore':['natural_grass','natural_water','natural_cave_rock']}
    receipts=[]
    for name,fg,bg,rim in families:
        phases=max(fg.shape[0],bg.shape[0])//32;count=48*phases*phases;cols=8;rows=count//cols
        atlas=Image.new('RGBA',(cols*32,rows*32))
        for py in range(phases):
            for px in range(phases):
                a=phase(fg,px,py);b=phase(bg,px,py)
                for j,m in enumerate(MASKS+[None]):
                    mask=shape(m) if m is not None else np.zeros((32,32),bool)
                    if rim is None and m is not None:
                        yy,xx=np.mgrid[:32,:32]
                        fringe=mask&~shape(m,6)
                        mask=mask&~(fringe&(((xx%31)*7+(yy%31)*11)%5<2))
                    out=np.where(mask[:,:,None],a,b)
                    if rim is not None and m is not None:
                        edge=mask&~shape(m,14 if name=='cave' else 8)
                        out=np.where(edge[:,:,None],phase(rim,px,py),out)
                    index=(py*phases+px)*48+j
                    atlas.paste(Image.fromarray(out.astype('uint8')),((index%cols)*32,(index//cols)*32))
        rel=f'assets/tiles/natural_auto_{name}.png';atlas.save(ROOT/rel)
        sources=[f'assets/tiles/{part}.png' for part in source_names[name]]
        assert all(p in entries for p in sources)
        entries[rel]=dict(path=rel,kind='terrain_autotile',size=list(atlas.size),frame=[32,32],grid=[cols,rows],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillowによる登録済みimagegen原画の接続合成',generated_at='2026-09-26',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',prompt_record='assets/source_records/visual-target-generation.json#surfaces',modified='登録済みの地面・水・岩・スプリントA地形から47形×模様位相を合成。各位相48番目は背景。目標JPEGの画素は不使用。',autotile=dict(scheme='blob47',masks=MASKS,phase_cells=[phases,phases],stride=48,background_index=47,bit_order=['N','E','S','W','NE','SE','SW','NW']),component_sources=sources)
        receipts.append({'family':name,'shapes':47,'phase_cells':[phases,phases],'cells':count})
    # 4×3局所配置4096通りから、水平・垂直の共有境界を全数照合する。
    joins=0;bad=0
    for bits in range(4096):
        f=np.array([(bits>>i)&1 for i in range(12)],dtype=bool).reshape(3,4)
        for transposed in (False,True):
            g=f.T if transposed else f
            p=(1,1);q=(1,2) if transposed else (2,1)
            if not(g[p[1],p[0]] and g[q[1],q[0]]):continue
            for radius in (4,6,8,14):
                a=shape(neighbor_mask(g,*p),radius);b=shape(neighbor_mask(g,*q),radius)
                bad+=int(np.any(a[-1]!=b[0]) if transposed else np.any(a[:,-1]!=b[:,0]));joins+=1
    assert bad==0,(joins,bad)
    registry['assets']=list(entries.values());(ROOT/'assets/registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (OUT/'autotile-checks.json').write_text(json.dumps({'families':receipts,'local_arrangements':4096,'shape_joins':joins,'shape_mismatches':bad},indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'AUTOTILE_PASS: families={len(families)} shapes_each=47 arrangements=4096 joins={joins} mismatches={bad}')

if __name__=='__main__':main()
