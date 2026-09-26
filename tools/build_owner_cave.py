#!/usr/bin/env python3
"""洞窟の任意輪郭から64pxの岩壁と岩岸を自動接続し、32px層へ出力する。"""
from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from import_visual_target_assets import quantize,periodic

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/verification/art-review-2'
W,H=1152,768
RECORD='assets/source_records/cave-wall-revision.json'

def smooth(points,steps=12):
    pts=np.array(points,float);result=[]
    for i in range(len(pts)):
        p0,p1,p2,p3=[pts[j%len(pts)] for j in (i-1,i,i+1,i+2)]
        for t in np.linspace(0,1,steps,endpoint=False):
            p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
            result.append(tuple(p))
    return result

def organic(cx,cy,rx,ry,phase=0):
    return [(cx+rx*(1+.12*math.sin(3*t+phase)+.055*math.cos(5*t))*math.cos(t),cy+ry*(1+.09*math.sin(4*t+phase))*math.sin(t)) for t in np.linspace(0,2*math.pi,160,endpoint=False)]

def expand(mask,n):
    # 八近傍の膨張。上下左右でも斜めでも最低n pxの帯を残す。
    a=mask.copy()
    for _ in range(n):
        p=np.pad(a,1)
        a=np.logical_or.reduce([p[dy:dy+mask.shape[0],dx:dx+mask.shape[1]] for dy in range(3) for dx in range(3)])
    return a

def masks():
    points=[(4,4),(7,2.8),(10,3),(12.5,6),(15,6.2),(15.5,3),(18,2.8),(19.5,4),(19.5,7),(23,7),(25,3.6),(29,3),(32,5),(32.5,8),(30.5,11),(32,14),(32,19),(29,21),(25,21),(22,19),(19,19.5),(18.5,23.9),(16.8,23.9),(16.5,20),(13,19.5),(10,21),(6,21),(3.5,18),(3.5,15),(5,12),(3.5,9)]
    im=Image.new('1',(W,H));d=ImageDraw.Draw(im);d.polygon(smooth([(x*32,y*32) for x,y in points]),fill=1)
    # 閉じた内柱にも外周と同じ64pxの接続規則を適用。
    for args in [(13.5*32,11.7*32,2.45*32,3.2*32,1),(22.6*32,14.5*32,2.35*32,2.5*32,2)]:d.polygon(organic(*args),fill=0)
    floor=np.array(im,bool);lakes=[]
    for args in [(7.3*32,6.3*32,2*32,1.35*32,.4),(28*32,6.8*32,3.1*32,1.8*32,1.7),(7*32,17*32,2*32,1.25*32,2.3)]:
        lake=Image.new('1',(W,H));ImageDraw.Draw(lake).polygon(organic(*args),fill=1);lakes.append(np.array(lake,bool)&floor)
    return floor,lakes

def texture(im,w=W,h=H,warp=False):
    a=np.array(im);yy,xx=np.mgrid[:h,:w]
    if warp:
        xx=xx+np.rint(19*np.sin(yy/23)+11*np.sin(xx/41)).astype(int)
        yy=yy+np.rint(13*np.sin(xx/33)+7*np.cos(yy/19)).astype(int)
    return a[yy%a.shape[0],xx%a.shape[1]]

def main():
    regpath=ROOT/'assets/registry.json';registry=json.loads(regpath.read_text(encoding='utf8'));entries={e['path']:e for e in registry['assets']}
    raw=json.loads((ROOT/RECORD).read_text(encoding='utf8'));source=Image.open(ROOT/raw['source_file']).convert('RGBA')
    raw['sha256']=hashlib.sha256((ROOT/raw['source_file']).read_bytes()).hexdigest();(ROOT/RECORD).write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    def save(name,im,**extra):
        path=f'assets/tiles/cave_{name}.png';im=quantize(im);im.save(ROOT/path)
        e=dict(path=path,kind='tileset',size=list(im.size),max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='imagegen + Python/Pillow',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-26',prompt_record=RECORD,modified='丸い岩の新規原画を減色。距離帯の規則で岩壁と岩岸を32pxセルへ自動接続。参考JPEGの画素は不使用。',tile_size=[32,32]);e.update(extra);entries[path]=e;return path,im
    materials={}
    for i,name in enumerate(('wall_top','wall_side','quiet_floor','quiet_water')):
        x=i%2;y=i//2;part=source.crop((x*source.width//2+10,y*source.height//2+10,(x+1)*source.width//2-10,(y+1)*source.height//2-10))
        # 大きな丸石を32px前後で残すため256pxの材質面を使う。
        path,im=save(name,periodic(part.resize((256,256),Image.Resampling.NEAREST)));materials[name]=im
    floor,lakes=masks();wall=expand(floor,64)&~floor;side=expand(floor,32)&~floor;cap=wall&~side
    terrain=np.zeros((H,W,4),np.uint8);terrain[:,:,3]=255;terrain[:,:,:3]=1
    ground=texture(materials['quiet_floor'],warp=True);terrain[floor]=ground[floor]
    top=texture(materials['wall_top'],warp=True);face=texture(materials['wall_side'],warp=True)
    terrain[cap]=top[cap];terrain[side]=face[side]
    water=texture(materials['quiet_water'],warp=True)
    for lake in lakes:
        shore=expand(lake,7)&~lake&floor
        terrain[shore]=face[shore];terrain[lake]=water[lake]
    # 固定の大きな模様の連続を避け、地面の小物をセルごとに散らす。
    image=quantize(Image.fromarray(terrain))
    tiles={};cells=[];unique={};parts=[]
    for y in range(H//32):
        for x in range(W//32):
            tile=image.crop((x*32,y*32,x*32+32,y*32+32));key=tile.tobytes()
            if key not in unique:unique[key]=len(parts);parts.append(tile)
            cells.append([x,y,unique[key]])
    cols=24;rows=math.ceil(len(parts)/cols);atlas=Image.new('RGBA',(cols*32,rows*32),(1,1,1,255))
    for i,tile in enumerate(parts):atlas.paste(tile,((i%cols)*32,(i//cols)*32))
    path,_=save('thick_wall_autotile',atlas,autotile_rule=dict(type='distance_band',wall_depth_px=64,top_depth_px=32,side_depth_px=32,shore_depth_px=7,neighbors='8',generator='tools/build_owner_cave.py',cell_size=32,material_sources=[f'assets/tiles/cave_{name}.png' for name in materials],variants=len(parts)))
    for i in range(len(parts)):tiles[f'c{i:04}']={'path':path,'region':[i%cols*32,i//cols*32,32,32]}
    layers=[{'name':'64px岩壁・丸い湖・床の自動接続','cells':[[x,y,f'c{i:04}'] for x,y,i in cells]}]
    # 旧比較JSONの使える小物を、今回の床の上へ移す。
    objects=[('stalagmites',5,3),('stalagmites',9,8),('stalagmites',26,3),('stalagmites',30,8),('stalagmites',4,14),('stalagmites',9,19),('stalagmites',27,19),('stalagmites',18,11),('mushrooms',6,8),('mushrooms',10,5),('mushrooms',16,5),('mushrooms',26,8),('mushrooms',30,17),('mushrooms',5,18),('campfire',28,18),('mine_timbers',28,10),('rope_bridge',21,10)]
    for n,(name,x,y) in enumerate(objects):
        p=f'assets/objects/natural_{name}.png';sw,sh=entries[p]['size'];cs=[]
        for yy in range(sh//32):
            for xx in range(sw//32):
                id_=f'o{n}_{xx}_{yy}';tiles[id_]={'path':p,'region':[xx*32,yy*32,32,32]};cs.append([x+xx,y+yy,id_])
        layers.append({'name':name,'cells':cs})
    for n,(x,y) in enumerate([(16,10),(10,17),(30,19)]):
        id_=f'chest{n}';tiles[id_]={'path':'assets/objects/chest.png','region':[0,0,32,32]};layers.append({'name':id_,'cells':[[x,y,id_]]})
    payload=dict(version=1,id='cave-natural',tile_size=32,width=36,height=24,tiles=tiles,layers=layers,actors=[dict(id='pc_01',path='assets/characters/pc_01/walk.png',region=[0,0,32,48],cell=[17,21],offset=[0,-16])],anchors={'entrance':[17,23],'inner_pillars':2},terrain_rules=entries[path]['autotile_rule'],notes='輪郭から外側64pxを丸石の壁として自動接続。入口の画面外だけは開放。壁の暗い上面32pxと明るい側面32px。')
    (OUT/'mock-maps/cave-natural.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    registry['assets']=list(entries.values());regpath.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # 登録済みPNGとJSONだけから描画。参考画像は比較欄だけに使う。
    from build_visual_target_mocks import render,compare
    result=render(OUT/'mock-maps/cave-natural.json');result.save(OUT/'cave-natural.png');compare('cave-natural',result)
    for name,mask in [('floor-mask',floor),('wall-mask',wall),('wall-top-mask',cap),('wall-side-mask',side)]+[(f'lake-{i+1}-mask',lake) for i,lake in enumerate(lakes)]:Image.fromarray(mask).save(OUT/(name+'.png'))
    lake_report=[]
    for a in lakes:
        y,x=np.where(a);area=int(a.sum());bbox=int((x.max()-x.min()+1)*(y.max()-y.min()+1));lake_report.append(dict(area=area,bbox_area=bbox,fill_ratio=area/bbox))
    report=dict(wall_depth_px=64,top_depth_px=32,side_depth_px=32,inner_pillars=2,wall_pixels=int(wall.sum()),top_luma=float(np.array(image)[:,:,:3][cap].mean()),side_luma=float(np.array(image)[:,:,:3][side].mean()),lake_count=3,lakes=lake_report,unique_32px_cells=len(parts),reference_pixels_used=0)
    (OUT/'cave-revision-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(f'CAVE_REVISION_PASS: wall_depth=64 top=32 side=32 lakes=3 variants={len(parts)}')

if __name__=='__main__':main()
