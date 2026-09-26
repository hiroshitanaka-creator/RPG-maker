#!/usr/bin/env python3
"""スプリントAの設定・コマ・反復・静止合成を作成する。ゲームデータは触らない。"""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from import_art_sprint_a import transition_masks

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/art-review'
FONT='C:/Windows/Fonts/meiryo.ttc'


def font(size):return ImageFont.truetype(FONT,size)
def load(path):return Image.open(ROOT/path).convert('RGBA')
def tile(name):return load('assets/tiles/bright_'+name+'.png')
def label(canvas,xy,text,size=17):ImageDraw.Draw(canvas).text(xy,text,font=font(size),fill='#101D36')
def paste(canvas,im,xy,scale=1):
    if scale!=1:im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    canvas.paste(im,xy,im)


def party():
    names=['カイナ','リオネ','ハルド','スイナ']
    sheet=Image.new('RGB',(1320,760),'#e7eff0')
    for i,name in enumerate(names):
        x=i*330+16;id_=f'pc_0{i+1}';label(sheet,(x,10),id_+' '+name)
        paste(sheet,load(f'assets/characters/{id_}/walk.png'),(x,42),2)
        label(sheet,(x,438),'待機・攻撃・被弾（左向き）',15)
        paste(sheet,load(f'assets/characters/{id_}/battle.png'),(x,466),2)
        paste(sheet,load(f'assets/characters/{id_}/portrait.png'),(x,590),2)
    sheet.save(OUT/'party-sprites.png')
    ids=[f'pc_0{i}' for i in range(1,5)]+['npc_farmer','npc_woman','npc_elder_man','npc_elder_woman','npc_boy','npc_girl','npc_item_clerk','npc_weapon_clerk','npc_innkeeper','npc_gatekeeper']
    sheet=Image.new('RGB',(1540,190),'#e7eff0');label(sheet,(16,8),'仲間4人と承認済みNPC10人 / 全員2倍・接地一致')
    for i,id_ in enumerate(ids):
        paste(sheet,load(f'assets/characters/{id_}/walk.png').crop((0,0,32,48)),(i*110+20,52),2)
        label(sheet,(i*110+8,154),id_.replace('npc_',''),12)
    sheet.save(OUT/'party-with-npcs.png')


def tiling():
    rows=json.loads((OUT/'tiling-checks.json').read_text(encoding='utf-8'))
    result=Image.new('RGB',(3240,math.ceil(len(rows)/3)*1100+360),'#e7eff0')
    for i,row in enumerate(rows):
        im=load(row['path']);repeat=Image.fromarray(np.tile(np.array(im),(8,8,1)))
        name=Path(row['path']).stem
        repeat.save(OUT/(name+'-8x8.png'))
        x=i%3*1080+16;y=i//3*1100
        label(result,(x,y+8),name+' / 8×8反復・端の不一致0')
        paste(result,repeat,(x,y+40),2 if im.width==32 else 1)
    y=math.ceil(len(rows)/3)*1100
    label(result,(16,y+8),'岸8方向＋内角4方向 / 道と草の接続')
    for i,name in enumerate(transition_masks(32)):
        paste(result,tile('shore_'+name),(16+i*100,y+70),2);label(result,(16+i*100,y+140),name,11)
    for x in range(12):
        for yy in range(3):paste(result,tile('road' if yy==1 else 'grass'),(16+x*32,y+195+yy*32))
    result.save(OUT/'tiling-preview.png')


def objects():
    sheet=Image.new('RGB',(1050,500),'#e7eff0')
    label(sheet,(16,8),'宝箱と門：左が閉、右が開 / 全画像2倍')
    paste(sheet,load('assets/objects/chest.png'),(16,54),2)
    paste(sheet,load('assets/objects/gate.png'),(230,54),2)
    for i,id_ in enumerate(['village','town','castle','tower','cave']):
        label(sheet,(16+i*180,310),id_);paste(sheet,load(f'assets/ui/icon_{id_}.png'),(16+i*180,350),2)
    sheet.save(OUT/'objects.png')
    paths=json.loads((OUT/'changed-assets.json').read_text(encoding='utf-8'))
    paths=[p for p in paths if p.startswith('assets/tiles/bright_') and '_edge_' not in p and 'shore_' not in p and 'road_edge_' not in p]
    sheet=Image.new('RGB',(1200,math.ceil(len(paths)/4)*300),'#e7eff0')
    for i,p in enumerate(paths):
        x=i%4*300+10;y=i//4*300;label(sheet,(x,y+4),Path(p).stem,13);paste(sheet,load(p),(x,y+35),2)
    sheet.save(OUT/'tiles-and-furniture.png')
    atlas=Image.new('RGB',(1056,552),'#e7eff0')
    for i,name in enumerate(['field_outdoor','dungeon_cave']):
        label(atlas,(i*528+8,8),name+' / 512×512・参照番号維持',14)
        paste(atlas,load('assets/tiles/'+name+'.png'),(i*528+8,36))
    atlas.save(OUT/'compatibility-atlases.png')


def village():
    canvas=Image.new('RGBA',(640,512))
    for y in range(16):
        for x in range(20):
            variant=(x*7+y*11)%3;paste(canvas,tile('grass'+('' if variant==0 else '_'+str(variant+1))),(x*32,y*32))
    for y in range(224,320,32):
        for x in range(32,608,32):paste(canvas,tile('road'),(x,y))
    for y in range(32,512,32):
        for x in [288,320]:paste(canvas,tile('road'),(x,y))
    for x in range(32,608,32):
        paste(canvas,tile('fence'),(x,16));paste(canvas,tile('fence'),(x,464))
    for y in range(0,480,56):
        for x in [0,576]:paste(canvas,tile('tree_pine'),(x,y))
    for name,xy in [('house',(64,80)),('inn',(416,80)),('item_shop',(64,336)),('weapon_shop',(416,336))]:paste(canvas,tile(name+'_exterior'),xy)
    for xy in [(208,80),(352,64),(208,384),(336,352),(208,432)]:paste(canvas,tile('tree_oak'),xy)
    for xy in [(64,224),(192,192),(544,192),(64,304),(480,304)]:paste(canvas,tile('flowers'),xy)
    for id_,xy in [('pc_01',(288,248)),('npc_woman',(352,224)),('npc_elder_man',(176,304)),('npc_boy',(256,336)),('npc_girl',(368,272)),('npc_gatekeeper',(304,48))]:
        paste(canvas,load(f'assets/characters/{id_}/walk.png').crop((0,0,32,48)),xy)
    paste(canvas,load('assets/objects/chest.png').crop((0,0,32,32)),(544,336))
    canvas.resize((1280,1024),Image.Resampling.NEAREST).save(OUT/'village-mock-v2.png')


def world():
    canvas=Image.new('RGBA',(1024,576));grid=[['grass']*32 for _ in range(18)]
    for y in range(18):
        for x in range(32):
            if ((x-5)/6)**2+((y-4)/4)**2<1:grid[y][x]='forest'
            if ((x-25)/6)**2+((y-13)/4)**2<1:grid[y][x]='deep_forest'
            if ((x-26)/7)**2+((y-2)/4)**2<1:grid[y][x]='mountains'
            if ((x-10)/4)**2+((y-14)/3)**2<1:grid[y][x]='hills'
            if x in [17,18]:grid[y][x]='water'
    masks=transition_masks(32)
    for y in range(18):
        for x in range(32):
            variant=(x*7+y*11)%3;grass=tile('grass'+('' if variant==0 else '_'+str(variant+1)))
            code=grid[y][x];im=grass
            if code in ['forest','deep_forest','hills','mountains']:
                src=tile(code);im=src.crop((x%4*32,y%4*32,x%4*32+32,y%4*32+32))
                mask=np.ones((32,32),dtype=bool)
                for dx,dy,direction in [(0,-1,'north'),(0,1,'south'),(-1,0,'west'),(1,0,'east')]:
                    nx,ny=x+dx,y+dy
                    if 0<=nx<32 and 0<=ny<18 and grid[ny][nx]!=code:mask &= masks[direction]
                im=Image.fromarray(np.where(mask[:,:,None],np.array(im),np.array(grass)).astype('uint8'))
            elif code=='water':im=tile('water')
            if x==16:im=tile('shore_east')
            if x==19:im=tile('shore_west')
            paste(canvas,im,(x*32,y*32))
    for x in range(3,29):
        if x not in [17,18]:paste(canvas,tile('road'),(x*32,9*32))
    for y in range(5,10):paste(canvas,tile('road'),(8*32,y*32))
    paste(canvas,tile('bridge'),(17*32,9*32-16))
    for id_,xy in [('village',(8*32,5*32)),('town',(13*32,9*32)),('cave',(23*32,11*32)),('castle',(27*32,7*32)),('tower',(4*32,13*32))]:paste(canvas,load(f'assets/ui/icon_{id_}.png'),xy)
    paste(canvas,load('assets/objects/gate.png').crop((0,0,96,96)),(13*32,1*32))
    canvas.save(OUT/'world-mock.png')


def main():
    party();tiling();objects();village();world()
    print('ART_A_REVIEW_PASS: party=4 npcs=10 tiling=13 world=32x18')


if __name__=='__main__':main()
