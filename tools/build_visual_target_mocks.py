#!/usr/bin/env python3
"""登録素材の32pxタイル層JSONを組み、JSONだけから確認画像を描く。"""
from pathlib import Path
import json
import random
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_natural_autotiles import MASKS,neighbor_mask

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/art-review-2'
MAPS=OUT/'mock-maps'
REG=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
ENTRIES={e['path']:e for e in REG['assets']}
FONT=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',16)

def obj(name):return f'assets/objects/natural_{name}.png'
def tex(name):return f'assets/tiles/natural_{name}.png'

class Map:
    def __init__(self,id_,w=36,h=24):
        self.id=id_;self.w=w;self.h=h;self.catalog={};self.reverse={};self.layers=[];self.objects=[]
        self.occupied=set();self.anchors={};self.rng=random.Random(926)

    def tile(self,path,region):
        assert path in ENTRIES and path.startswith('assets/')
        key=(path,*region)
        if key not in self.reverse:
            id_=f't{len(self.catalog):04}';self.reverse[key]=id_;self.catalog[id_]=dict(path=path,region=list(region))
        return self.reverse[key]

    def layer(self,name,cells):self.layers.append(dict(name=name,cells=cells))

    def base(self,path):
        cells=[];iw,ih=ENTRIES[path]['size']
        for y in range(self.h):
            for x in range(self.w):cells.append([x,y,self.tile(path,((x*32)%iw,(y*32)%ih,32,32))])
        self.layer('地面',cells)

    def terrain(self,family,field):
        path=tex('auto_'+family);entry=ENTRIES[path];ph=entry['autotile']['phase_cells'][0];cols=entry['grid'][0];cells=[]
        for y,x in np.argwhere(field):
            j=MASKS.index(neighbor_mask(field,int(x),int(y)))
            index=((int(y)%ph)*ph+int(x)%ph)*48+j
            cells.append([int(x),int(y),self.tile(path,(index%cols*32,index//cols*32,32,32))])
        self.layer(family,cells)

    def stamp(self,path,x,y,region=None,block=True):
        w,h=ENTRIES[path]['size'] if region is None else region[2:]
        ox,oy=(0,0) if region is None else region[:2]
        assert w%32==h%32==0
        cells=[]
        for yy in range(h//32):
            for xx in range(w//32):
                if 0<=x+xx<self.w and 0<=y+yy<self.h:
                    cells.append([x+xx,y+yy,self.tile(path,(ox+xx*32,oy+yy*32,32,32))])
                    if block:self.occupied.add((x+xx,y+yy))
        self.objects.append((y+h/32,len(self.objects),dict(name=Path(path).stem,cells=cells)))

    def scatter(self,field,count=130):
        choices=['tufts']*4+['pebbles','flowers_white','flowers_yellow','flowers_pink','leaves','dirt_patch']
        cells=list(map(tuple,np.argwhere(field)));self.rng.shuffle(cells);n=0
        for y,x in cells:
            if (x,y) in self.occupied:continue
            self.stamp(obj(self.rng.choice(choices)),int(x),int(y),block=False);n+=1
            if n>=count:break

    def trees(self,positions):
        for x,y in positions:self.stamp('assets/tiles/bright_tree_oak.png',x,y)

    def finish(self,kaina):
        self.layers.extend(item[2] for item in sorted(self.objects))
        payload=dict(version=1,id=self.id,tile_size=32,width=self.w,height=self.h,tiles=self.catalog,layers=self.layers,actors=[dict(id='pc_01',path='assets/characters/pc_01/walk.png',region=[0,0,32,48],cell=kaina,offset=[0,-16])],anchors=self.anchors,notes='素材確認用配置。衝突・イベント・本番のworldデータは変更しない。建物も32px領域に分割したタイル層。')
        path=MAPS/(self.id+'.json');path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        result=render(path);result.save(OUT/(self.id+'.png'))
        return result

def render(path):
    """目標JPEGへアクセスせず、保存済みJSONの登録素材だけを描く。"""
    data=json.loads(path.read_text(encoding='utf-8'));w,h=data['width'],data['height'];out=Image.new('RGBA',(w*32,h*32));images={}
    for layer in data['layers']:
        for x,y,id_ in layer['cells']:
            assert 0<=x<w and 0<=y<h
            e=data['tiles'][id_];p=e['path'];assert p in ENTRIES and p.startswith('assets/')
            if p not in images:images[p]=Image.open(ROOT/p).convert('RGBA')
            sx,sy,sw,sh=e['region'];assert sw==sh==32 and sx%32==sy%32==0
            assert sx+sw<=images[p].width and sy+sh<=images[p].height
            out.alpha_composite(images[p].crop((sx,sy,sx+sw,sy+sh)),(x*32,y*32))
    for actor in data['actors']:
        assert actor['path'] in ENTRIES and actor['region']==[0,0,32,48]
        im=Image.open(ROOT/actor['path']).convert('RGBA').crop((0,0,32,48));x,y=actor['cell'];dx,dy=actor['offset'];out.alpha_composite(im,(x*32+dx,y*32+dy))
    return out

def empty(m):return np.zeros((m.h,m.w),bool)
def ellipse(m,cx,cy,rx,ry):
    y,x=np.mgrid[:m.h,:m.w];return ((x+.5-cx)/rx)**2+((y+.5-cy)/ry)**2<=1
def route(m,points,width=3):
    im=Image.new('1',(m.w,m.h));d=ImageDraw.Draw(im);d.line(points,fill=1,width=width)
    for x,y in points:d.ellipse((x-width//2,y-width//2,x+width//2,y+width//2),fill=1)
    return np.array(im,dtype=bool)

def fence(m,x,y,w,h,gap=None):
    for xx in range(x,x+w,2):
        if gap is None or not(gap<=xx<gap+2):m.stamp(obj('fence_horizontal'),xx,y+h-1)
        m.stamp(obj('fence_horizontal'),xx,y)
    for yy in range(y+1,y+h-1,2):
        m.stamp(obj('fence_vertical'),x,yy);m.stamp(obj('fence_vertical'),x+w-1,yy)
    for xx,yy in [(x,y),(x+w-1,y),(x,y+h-1),(x+w-1,y+h-1)]:m.stamp(obj('fence_corner'),xx,yy)

def village():
    m=Map('village-farm-a');m.base(tex('grass'))
    road=route(m,[(17,0),(17,5),(16,8),(18,12),(18,17),(17,23)],3)
    for pts in [[(8,8),(10,9),(14,10),(18,12)],[(28,8),(26,9),(23,10),(18,12)],[(13,19),(14,19),(17,17)],[(28,19),(24,19),(20,16)]]:road|=route(m,pts,2)
    for cx,cy in [(8,8),(28,8),(13,19),(28,19)]:road|=ellipse(m,cx,cy,3,1.5)
    m.terrain('dirt',road)
    # 家の正面と庭をずらし、十字の区画ではなく曲がった道へつなぐ。
    for name,x,y in [('farm_house_a',5,2),('farm_house_b',25,2),('town_house_red',10,14),('farm_house_a',25,14)]:m.stamp(obj(name),x,y)
    m.stamp(obj('well'),17,9)
    for x,y in [(12,3),(14,5),(30,20)]:m.stamp(obj('haystack'),x,y)
    for x,y in [(5,7),(29,7),(10,19),(25,19)]:m.stamp(obj('barrels'),x,y)
    for x,y in [(8,7),(31,7),(14,19)]:m.stamp(obj('crates'),x,y)
    m.stamp(obj('shrine'),32,16)
    for x,y in [(12,8),(23,8),(31,13),(21,18),(8,20)]:m.stamp(obj('flowerbed'),x,y)
    for x,y,w,h,crop in [(3,10,7,4,'cabbage'),(3,15,5,6,'carrots'),(27,10,7,4,'cabbage')]:
        patch=empty(m);patch[y:y+h,x:x+w]=True;m.terrain('dirt',patch)
        fence(m,x,y,w,h)
        for yy in range(y+1,y+h-1):
            for xx in range(x+1,x+w-1):m.stamp(obj(crop),xx,yy)
    for x in range(3,34,2):
        if x not in (15,17):m.stamp(obj('fence_horizontal'),x,21)
        if x not in (15,17):m.stamp(obj('fence_horizontal'),x,1)
    for y in range(3,21,2):m.stamp(obj('fence_vertical'),2,y);m.stamp(obj('fence_vertical'),34,y)
    m.trees([(0,y) for y in range(-1,24,3)]+[(34,y) for y in range(-1,24,3)]+[(x,-2) for x in range(2,34,3) if x not in (14,17)]+[(x,22) for x in range(1,35,4) if x not in (13,17)])
    m.scatter(~road,150);m.anchors={'village_exit':[17,23],'well':[18,12]}
    return m.finish([18,15])

def town():
    m=Map('town-walled-a');m.base(tex('grass'))
    plaza=ellipse(m,18,12,6,4)
    road=plaza|route(m,[(17,0),(18,7),(18,12),(17,18),(18,23)],3)
    for pts in [[(1,11),(8,11),(13,10),(18,12)],[(18,12),(23,10),(30,10),(35,11)],[(7,7),(8,9),(13,10)],[(28,7),(27,9)],[(9,20),(12,19),(17,18)],[(28,21),(25,20),(18,19)]]:road|=route(m,pts,2)
    m.terrain('cobble',road);m.stamp(obj('fountain'),16,10)
    for name,x,y in [('town_house_red',3,2),('church',26,1),('town_house_blue',3,9),('town_house_red',27,11),('manor',5,16),('town_house_blue',25,17)]:m.stamp(obj(name),x,y)
    for x,y in [(9,6),(3,14),(28,16),(7,21)]:m.stamp(obj('barrels'),x,y)
    for x,y in [(3,7),(30,8),(31,16),(11,21)]:m.stamp(obj('crates'),x,y)
    for name,x,y in [('sign_inn',9,6),('sign_item',9,13),('sign_weapon',31,15)]:m.stamp(obj(name),x,y)
    for x,y in [(13,9),(21,9),(13,14),(21,15),(10,2),(31,18)]:m.stamp(obj('flowerbed'),x,y)
    m.stamp(obj('well'),11,19);m.stamp(obj('bench'),21,12)
    for x in range(0,36,3):
        if not 15<=x<=18:m.stamp(obj('wall_horizontal'),x,0);m.stamp(obj('wall_horizontal'),x,22)
    for y in range(2,22,3):m.stamp(obj('wall_vertical'),0,y);m.stamp(obj('wall_vertical'),34,y)
    for x,y in [(0,0),(33,0),(0,20),(33,20)]:m.stamp(obj('watchtower'),x,y)
    m.stamp(obj('gate_open'),16,0);m.stamp(obj('gate_open'),16,20)
    m.trees([(12,2),(22,3),(23,17),(2,16),(31,7),(12,16),(23,6),(4,8)])
    m.scatter(~road,95);m.anchors={'north_gate':[18,3],'south_gate':[18,23],'fountain':[18,13]}
    return m.finish([18,17])

def cave():
    m=Map('cave-natural');m.base(tex('auto_cave'))
    # 背景セルは黒い虚空。模様位相の背景インデックスを使う。
    path=tex('auto_cave');m.layers=[];j=47;cols=ENTRIES[path]['grid'][0]
    m.layer('虚空',[[x,y,m.tile(path,(j%cols*32,j//cols*32,32,32))] for y in range(m.h) for x in range(m.w)])
    floor=empty(m)
    for args in [(7,6,6,5),(17,4,3,3),(28,6,6,5),(7,16,6,5),(28,18,6,4),(18,14,5,5)]:floor|=ellipse(m,*args)
    floor|=route(m,[(8,8),(12,10),(17,9),(20,11),(25,9)],3)
    floor|=route(m,[(17,5),(17,10),(18,16),(17,23)],3)
    floor|=route(m,[(8,17),(13,17),(18,16),(25,19)],3)
    m.terrain('cave',floor)
    lakes=ellipse(m,7,6,2,1.5)|ellipse(m,28,6,3,2)|ellipse(m,6,16,2,1.5);m.terrain('lake',lakes)
    for x,y in [(2,5),(5,2),(11,7),(15,2),(29,2),(33,7),(2,14),(10,18),(24,19),(31,19),(19,12)]:m.stamp(obj('stalagmites'),x,y)
    for x,y in [(4,8),(10,5),(15,5),(26,3),(31,8),(3,17),(9,19),(25,20),(32,17),(20,14)]:m.stamp(obj('mushrooms'),x,y)
    m.stamp(obj('mine_timbers'),27,11);m.stamp(obj('rope_bridge'),23,13)
    m.stamp(obj('campfire'),28,18)
    for x,y in [(17,10),(9,16),(31,20)]:m.stamp('assets/objects/chest.png',x,y,[0,0,32,32])
    for x,y in [(13,9),(20,8),(2,10),(32,13),(13,17)]:m.stamp(obj('rubble'),x,y)
    m.anchors={'entrance':[17,23],'mine':[29,13],'chests':[[17,10],[9,16],[31,20]]}
    return m.finish([17,21])

def world():
    m=Map('world-organic',32,18);m.base(tex('water'))
    sea=ellipse(m,32,18,7,6);m.terrain('shore',~sea)
    forest=ellipse(m,3,4,6,6)|ellipse(m,10,1,5,3)|ellipse(m,3,14,6,5)|ellipse(m,18,16,5,4)
    hills=ellipse(m,23,9,6,4)|ellipse(m,17,3,3,3)
    mountain=ellipse(m,28,2,5,4)|ellipse(m,30,7,3,3)|ellipse(m,29,14,4,5)
    river=route(m,[(13,0),(13,3),(11,5),(12,7),(15,9),(15,11),(12,14),(12,17)],2)
    road=route(m,[(8,14),(9,11),(11,10),(14,10),(18,9),(20,6),(22,5)],1)|route(m,[(18,9),(20,12),(23,13)],1)
    mountain&=~sea;hills&=~sea;forest&=~sea
    m.terrain('hills',hills);m.terrain('forest',forest);m.terrain('mountains',mountain);m.terrain('river',river);m.terrain('dirt',road&~river)
    m.stamp('assets/tiles/bright_bridge.png',13,9);m.stamp('assets/tiles/bright_bridge.png',15,9)
    for name,x,y in [('village',8,13),('castle',22,4),('cave',24,10),('tower',22,13)]:m.stamp(f'assets/ui/icon_{name}.png',x,y)
    m.stamp('assets/objects/gate.png',18,5,[0,0,96,96]);m.scatter(~(forest|mountain|hills|river|road|sea),55)
    m.anchors={'village':[8,13],'bridge':[14,10],'gate':[19,7]}
    return m.finish([10,11])

def compare(id_,mock):
    ref=Image.open(ROOT/f'docs/reference/visual-targets/{id_}.jpg').convert('RGB')
    # 左の目標は比較欄だけに表示する。右の描画経路とは分離する。
    canvas=Image.new('RGB',(2304,820),'#eee9dc');d=ImageDraw.Draw(canvas)
    d.text((12,8),'依頼者の目標画像（ゲーム素材として不使用）',font=FONT,fill='#20251d')
    d.text((1164,8),'登録済みゲームタイルのみ / 36×24セル / カイナ32×48px',font=FONT,fill='#20251d')
    ref.thumbnail((1152,768));canvas.paste(ref,((1152-ref.width)//2,42+(768-ref.height)//2));canvas.paste(mock.convert('RGB'),(1152,42));canvas.save(OUT/(id_+'-compare.png'))

def contacts():
    paths=json.loads((OUT/'new-assets.json').read_text());cols=6;cw=240;ch=240
    canvas=Image.new('RGB',(cols*cw,math.ceil(len(paths)/cols)*ch),'#cdcdbb');d=ImageDraw.Draw(canvas)
    for i,p in enumerate(paths):
        im=Image.open(ROOT/p).convert('RGBA');im.thumbnail((220,205),Image.Resampling.NEAREST);x=i%cols*cw;y=i//cols*ch
        canvas.paste(im,(x+(cw-im.width)//2,y+205-im.height),im);d.text((x+4,y+212),Path(p).stem.removeprefix('natural_'),font=FONT,fill='#20251d')
    canvas.save(OUT/'new-assets-contact.png')

def main():
    MAPS.mkdir(parents=True,exist_ok=True)
    for id_,build in [('village-farm-a',village),('town-walled-a',town),('cave-natural',cave)]:compare(id_,build())
    world();contacts()
    report=[]
    for p in sorted(MAPS.glob('*.json')):
        data=json.loads(p.read_text(encoding='utf-8'));report.append(dict(map=data['id'],size=[data['width'],data['height']],tile_regions=len(data['tiles']),placed_cells=sum(len(layer['cells']) for layer in data['layers']),actors=len(data['actors']),registry_only=True))
    (OUT/'mock-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('MOCK_MAP_PASS: maps=4 grid=32 registered_tiles_only=4 actors_32x48=4')

if __name__=='__main__':main()
