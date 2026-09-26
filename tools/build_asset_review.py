#!/usr/bin/env python3
"""新素材の等倍・整数倍一覧と、新素材だけの村の静止合成を作る。"""
from pathlib import Path
import json
import math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/asset-review'
FONT_PATH=Path('C:/Windows/Fonts/meiryo.ttc')


def font(size):
    return ImageFont.truetype(str(FONT_PATH),size) if FONT_PATH.exists() else ImageFont.load_default()


def review_sheet(entries,name,columns,width,height):
    canvas=Image.new('RGB',(columns*width,math.ceil(len(entries)/columns)*height+64),'#e7eff0')
    d=ImageDraw.Draw(canvas);d.text((18,12),name+' / 全画像2倍・最近傍',font=font(20),fill='#101d36')
    for i,e in enumerate(entries):
        x=i%columns*width;y=i//columns*height+64
        p=Path(e['path']);label=p.parent.name if p.name=='walk.png' else p.stem
        d.text((x+12,y+6),label,font=font(15),fill='#101d36')
        image=Image.open(ROOT/p).convert('RGBA');image=image.resize((image.width*2,image.height*2),Image.Resampling.NEAREST)
        canvas.paste(image,(x+12,y+36),image)
    canvas.save(OUT/name)


def village_mock():
    def load(path):return Image.open(ROOT/path).convert('RGBA')
    def tile(id_):return load('assets/tiles/bright_'+id_+'.png')
    canvas=Image.new('RGBA',(640,512))
    grass=tile('grass');road=tile('road')
    for y in range(0,512,32):
        for x in range(0,640,32):canvas.alpha_composite(grass,(x,y))
    for y in range(224,320,32):
        for x in range(32,608,32):canvas.alpha_composite(road,(x,y))
    for y in range(32,512,32):
        for x in [288,320]:canvas.alpha_composite(road,(x,y))
    for x in range(32,608,32):
        canvas.alpha_composite(tile('fence'),(x,16));canvas.alpha_composite(tile('fence'),(x,464))
    for y in range(0,480,56):
        for x in [0,576]:canvas.alpha_composite(tile('tree_pine'),(x,y))
    for id_,xy in [('house',(64,80)),('inn',(416,80)),('item_shop',(64,336)),('weapon_shop',(416,336))]:
        canvas.alpha_composite(tile(id_+'_exterior'),xy)
    for x,y in [(208,80),(352,64),(208,384),(336,352),(208,432)]:canvas.alpha_composite(tile('tree_oak'),(x,y))
    for x,y in [(64,224),(192,192),(544,192),(64,304),(480,304)]:canvas.alpha_composite(tile('flowers'),(x,y))
    npc=[('npc_farmer',(224,248)),('npc_woman',(352,224)),('npc_elder_man',(176,304)),('npc_boy',(256,336)),('npc_girl',(368,272)),('npc_gatekeeper',(304,48))]
    for id_,xy in npc:canvas.alpha_composite(load('assets/characters/'+id_+'/walk.png').crop((0,0,32,48)),xy)
    canvas.alpha_composite(load('assets/objects/chest.png').crop((0,0,32,32)),(544,336))
    canvas.resize((1280,1024),Image.Resampling.NEAREST).save(OUT/'village-mock.png')


def compatibility():
    canvas=Image.new('RGB',(720,220),'#e7eff0');d=ImageDraw.Draw(canvas)
    d.text((12,8),'既存の仲間（左4人・無変更） / 新NPC（右3人）',font=font(17),fill='#101d36')
    ids=['pc_01','pc_02','pc_03','pc_04','npc_farmer','npc_woman','npc_gatekeeper']
    for i,id_ in enumerate(ids):
        im=Image.open(ROOT/f'assets/characters/{id_}/walk.png').convert('RGBA').crop((0,0,32,48)).resize((64,96),Image.Resampling.NEAREST)
        canvas.paste(im,(i*100+15,60),im);d.text((i*100+8,168),id_.replace('npc_',''),font=font(12),fill='#101d36')
    canvas.save(OUT/'party-compatibility.png')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    entries=[e for e in registry['assets'] if e.get('palette')=='assets/palette/bright.gpl']
    review_sheet([e for e in entries if e['kind']=='tileset'],'sheet-tiles.png',4,280,300)
    review_sheet([e for e in entries if e['kind']=='character_walk'],'sheet-characters.png',5,225,440)
    review_sheet([e for e in entries if e['kind']=='battle_background'],'sheet-battle-backgrounds.png',2,1050,630)
    review_sheet([e for e in entries if e['kind'] in {'object','map_icon','window_frame','cursor'}],'sheet-ui-objects.png',3,290,200)
    village_mock();compatibility()
    print(f'ASSET_REVIEW_PASS: images={len(entries)} sheets=4 village_mock=1 compatibility=1')


if __name__=='__main__':main()
