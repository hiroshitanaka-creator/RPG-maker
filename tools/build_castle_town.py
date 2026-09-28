"""城下町・城の本番配置を作る。最初の洞窟・村・関所の条件は保持する。"""
import copy
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from build_visual_target_mocks import Map, obj, tex, route, ellipse, ENTRIES
from build_first_region_presentation import payload, point, room, rows, reachable

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/sprint5-castle-town'
NODE='first_castle'
# 城下町の見た目。0=初版（07ac451）、B=依頼者が採用し修正した仕上げ（既定）。環境変数 CASTLE_TOWN_VARIANT で選ぶ。案A・Cは 20fdaab に記録。
import os,sys
VARIANT=os.environ.get('CASTLE_TOWN_VARIANT','B')
if VARIANT!='0':OUT=ROOT/'docs/verification/castle-town-polish'/('variant-'+VARIANT)

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

class Place:
    def __init__(self,id_,w,h,floor='assets/tiles/castle_floor.png'):
        self.m=Map(id_,w,h);self.m.base(floor);self.mask=np.ones((h,w),bool)
        self.mask[[0,-1],:]=False;self.mask[:,[0,-1]]=False
    def stamp(self,path,x,y,solid=True):
        self.m.stamp(path,x,y,block=solid)
        if solid:
            w,h=ENTRIES[path]['size'];self.mask[max(0,y):min(self.m.h,y+h//32),max(0,x):min(self.m.w,x+w//32)]=False
    def door(self,x,y):self.mask[y,x]=True
    def finish(self,title,events):
        d=payload(self.m);d['layout']=rows(self.mask);d['surround']='assets/tiles/castle_wall.png'
        return d,room(title,self.mask,events)

def npc(id_,cell,label,text,sprite='npc_castle_guard',**extra):
    return dict(id=id_,kind='npc',sprite=sprite,cell=cell,label=label,text=text,**extra)

def enclosed(id_,w,h):
    p=Place(id_,w,h)
    cells=[]
    for y in range(h):
        for x in range(w):
            if y<3 or x in (0,w-1) or y==h-1:
                cells.append([x,y,p.m.tile('assets/tiles/castle_wall.png',(x%4*32,y%4*32,32,32))]);p.mask[y,x]=False
    p.m.layer('壁',cells)
    return p

def furnished(id_,kind):
    p=enclosed(id_,16,12)
    p.door(8,11);p.door(8,10)
    p.stamp('assets/objects/natural_door_open.png',7,10,False)
    if kind=='inn':
        for x in [2,5,11]:p.stamp('assets/tiles/bright_bed.png',x,4)
    elif kind in ('library','home'):
        for x in [2,6,10]:p.stamp('assets/objects/castle_bookcase.png',x,1)
        p.stamp('assets/tiles/bright_table.png',6,6)
        p.stamp('assets/tiles/bright_chair.png',5,6)
    else:
        for x in [2,11]:p.stamp('assets/objects/castle_bookcase.png',x,1)
    if kind in ('inn','item','weapon','armor'):
        for x in range(5,10):p.stamp('assets/tiles/bright_shop_counter.png',x,5)
    p.stamp('assets/objects/castle_banner.png',1,1,False)
    p.stamp('assets/objects/castle_banner.png',14,1,False)
    return p

def legacy_town():
    """2026年9月28日に採用された初版の城下町。比較用に残す。"""
    town=Place('castle_town',36,26,tex('grass'))
    road=ellipse(town.m,18,13,7,5)|route(town.m,[(18,0),(18,8),(18,15),(18,25)],4)
    for points in [[(6,8),(10,9),(14,12)],[(29,9),(25,10),(22,12)],[(6,16),(12,16),(16,15)],[(30,17),(25,17),(21,15)],[(7,24),(12,22),(17,20)],[(29,24),(24,22),(19,20)]]:road|=route(town.m,points,3)
    town.m.terrain('cobble',road)
    for name,x,y in [('town_house_red',3,2),('church',26,1),('town_house_blue',3,10),('town_house_red',27,10),('manor',4,17),('town_house_blue',26,17)]:town.stamp(obj(name),x,y)
    town.stamp(obj('fountain'),16,11)
    for x,y in [(12,9),(22,10),(12,16),(22,17),(11,3),(23,21)]:town.stamp(obj('flowerbed'),x,y,False)
    for x,y in [(3,8),(9,7),(24,5),(3,16),(32,15),(13,21),(26,24)]:town.stamp(obj('barrels'),x,y)
    for x,y in [(10,6),(11,19),(24,8),(24,19)]:town.stamp(obj('crates'),x,y)
    for x,y in [(11,2),(22,2),(22,6),(2,20),(31,9)]:town.stamp('assets/tiles/bright_tree_oak.png',x,y)
    for name,x,y in [('sign_inn',9,7),('sign_item',9,15),('sign_weapon',32,16)]:town.stamp(obj(name),x,y,False)
    town.stamp(obj('bench'),22,14);town.stamp(obj('well'),10,20)
    for x in range(0,36,3):
        if not 15<=x<=18:town.stamp(obj('wall_horizontal'),x,0);town.stamp(obj('wall_horizontal'),x,24)
    for y in range(2,24,3):town.stamp('assets/objects/castle_low_wall_vertical.png',0,y);town.stamp('assets/objects/castle_low_wall_vertical.png',34,y)
    town.stamp(obj('gate_open'),16,0,False);town.stamp(obj('gate_open'),16,22,False)
    for y in range(0,26):
        if y<4 or y>21:
            for x in range(16,20):town.door(x,y)
    town.m.scatter(~road,85)
    events=[
        npc('castle_gate_guard',[17,4],'城門の兵士',['城へは、噴水の北の門を進んでください。']),
        npc('south_guard',[20,23],'町の兵士',['ベルナの関所から来たのですね。町では安心して休んでいってください。']),
        npc('travelling_merchant',[13,13],'旅の商人',['北へ向かうなら、まず城へ。道のことは兵士が詳しいですよ。'],'npc_castle_merchant'),
        npc('town_woman',[22,12],'町の人',['西の赤い屋根は宿屋。その下の青い屋根が道具屋です。'],'npc_woman',patrol=[[22,12],[23,12],[23,13],[22,13]]),
        npc('town_elder',[13,18],'町の人',['城では、それぞれの役目に合った修練を教えてくれるそうです。'],'npc_elder_man'),
        npc('town_child',[21,19],'子ども',['噴水の水、冷たいよ。走って転ばないでね。'],'npc_boy',patrol=[[21,19],[22,19],[22,20],[21,20]]),
        npc('shrine_visitor',[25,10],'祠へ来た人',['祠は東の青い屋根です。旅の前に気持ちを整えていきます。'],'npc_elder_woman'),
        npc('town_farmer',[11,11],'荷を届けた人',['村から野菜を届けに来たんだ。関所を通れるようになって助かったよ。'],'npc_farmer')]
    doors=[([6,7],4),([6,15],5),([30,15],6),([7,22],7),([29,8],8),([29,22],9)]
    for cell,index in doors:town.door(*cell);town.door(cell[0],cell[1]+1)
    return town,events,doors

from castle_town_variants import build_town_variant

def build_town(variant):
    if variant=='0':return legacy_town()
    return build_town_variant(variant,Place,npc)

def render(document,events):
    canvas=Image.new('RGBA',(document['width']*32,document['height']*32));cache={}
    for layer in document['layers']:
        for x,y,key in layer['cells']:
            t=document['tiles'][key];path=t['path']
            if path not in cache:cache[path]=Image.open(ROOT/path).convert('RGBA')
            sx,sy,w,h=t['region'];im=cache[path].crop((sx,sy,sx+w,sy+h));cell=layer.get('cell_size',32)
            if im.size!=(cell,cell):im=im.resize((cell,cell),Image.Resampling.NEAREST)
            canvas.alpha_composite(im,(x*cell,y*cell))
    for event in events:
        if event['kind']=='treasure':
            im=Image.open(ROOT/'assets/objects/chest.png').convert('RGBA').crop((0,0,32,32));offset=0
        else:
            sprite=event.get('sprite','npc_castle_guard');im=Image.open(ROOT/f'assets/characters/{sprite}/walk.png').convert('RGBA').crop((0,0,32,48));offset=-16
        canvas.alpha_composite(im,(event['cell'][0]*32,event['cell'][1]*32+offset))
    return canvas.convert('RGB')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    names_path=ROOT/'world/castle_town_names.json'
    names=json.loads(names_path.read_text(encoding='utf8')) if names_path.exists() else {'town':'第1地方の城下町（仮）','castle':'第1地方の城（仮）'}
    definition=json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'))
    visual=json.loads((ROOT/'world/first_region_visuals.json').read_text(encoding='utf8'))
    maps={};rooms=[];links=[]
    def add(p,title,events):
        d,r=p.finish(title,events);index=len(rooms);maps[f'{NODE}:{index}']=d;rooms.append(r);return index
    town,events,doors=build_town(VARIANT)
    add(town,names['town'],events)
    court=Place('castle_court',32,18,tex('grass'))
    court.m.terrain('cobble',route(court.m,[(16,17),(16,10),(16,1)],5)|route(court.m,[(3,13),(16,13),(28,13)],3))
    court.stamp(obj('castle'),10,1)
    for x in [2,6,24,28]:court.stamp(obj('flowerbed'),x,13,False)
    for x in range(0,32,3):
        if not 12<=x<=18:court.stamp(obj('wall_horizontal'),x,0);court.stamp(obj('wall_horizontal'),x,16)
    for y in range(2,16,3):court.stamp('assets/objects/castle_low_wall_vertical.png',0,y);court.stamp('assets/objects/castle_low_wall_vertical.png',30,y)
    for y in range(10,18):court.door(16,y)
    add(court,names['castle']+' 中庭',[npc('court_guard_left',[13,11],'城の兵士',['正面の扉が謁見の間です。']),npc('court_guard_right',[19,11],'城の兵士',['王がお待ちです。通行証を見せてください。'])])
    hall=enclosed('castle_hall',32,22)
    hall.m.layer('敷物',[[x,y,hall.m.tile('assets/tiles/castle_runner.png',((x-15)*32,y%3*32,32,32))] for y in range(4,22) for x in range(15,18)])
    for x,y in [(5,3),(25,3),(5,10),(25,10),(5,16),(25,16)]:hall.stamp('assets/objects/castle_column.png',x,y)
    for x in [3,9,22,28]:hall.stamp('assets/objects/castle_banner.png',x,1,False)
    hall.stamp('assets/objects/castle_throne.png',15,2)
    for x in [13,18]:hall.stamp('assets/objects/castle_candelabrum.png',x,3)
    for x in range(14,19):hall.door(x,5);hall.door(x,6)
    hall.door(16,21);hall.door(16,20)
    for x,y in [(0,10),(1,10),(30,10),(31,10)]:hall.door(x,y)
    royal=[npc('king',[16,5],'王',['ベルナの通行証を持っているのだな。洞窟から無事に戻ったと聞いた。','先へ進むなら、仲間の得意なことを確かめておくとよい。'],sprite='npc_castle_king',audience=True),npc('advisor',[19,6],'側近',['役目を変えても、身につけた技は失われません。仲間と相談して組み合わせてください。'],sprite='npc_castle_advisor'),npc('hall_guard_left',[13,18],'城の兵士',['王には、正面から話しかけてください。']),npc('hall_guard_right',[19,18],'城の兵士',['西に宝物庫、東に書庫があります。'])]
    add(hall,names['castle']+' 謁見の間',royal)
    treasury=enclosed('castle_treasury',16,12);treasury.door(8,11);treasury.door(8,10)
    for x in [2,5,11]:treasury.stamp(obj('crates'),x,4)
    add(treasury,'城の宝物庫',[dict(id='castle_supplies',kind='treasure',cell=[8,5],item='potion',amount=3),npc('treasury_keeper',[10,7],'宝物庫の兵士',['中央の箱は旅の補給用です。必要なときに役立ててください。'])])
    for kind,title,event in [
        ('inn','城下町の宿屋',dict(id='castle_inn',kind='rest',sprite='npc_innkeeper',cell=[7,4],reach=2,label='宿の主人',text=['お疲れでしょう。どうぞ休んでいってください。'])),
        ('item','城下町の道具屋',dict(id='castle_item_shop',kind='shop',sprite='npc_castle_merchant',cell=[7,4],reach=2,label='道具屋',text=['旅の備えをどうぞ。'])),
        ('weapon','城下町の武器屋',dict(id='castle_weapon_shop',kind='weapon_shop',sprite='npc_weapon_clerk',cell=[7,4],reach=2,label='武器屋',text=['手に合う武器を選んでいってくれ。'])),
        ('armor','城下町の防具屋',npc('castle_armor_clerk',[7,4],'防具屋',['服と防具は、動きやすさも大切ですよ。'],'npc_item_clerk',reach=2)),
        ('shrine','城下町の祠',npc('castle_shrine',[8,5],'祠の世話役',['旅の途中で身体の変化に気づいたら、一人で抱え込まずに相談してください。','清めたい人がいるときは、この祠の中で編成を開いて選んでください。'],'npc_elder_woman',shrine=True)),
        ('home','城下町の民家',npc('castle_home_resident',[10,7],'町の人',['城の北の門は、王の許しを得た人にだけ開かれます。'],'npc_woman')),
        ('library','城の書庫',npc('castle_librarian',[10,7],'書庫の係',['学んだ技の使いどころは、仲間の役目によって変わります。'],'npc_castle_advisor'))]:
        add(furnished('castle_'+kind,kind),title,[event])
    def link(a,ac,b,bc):links.append({'from':point(NODE,a,ac),'to':point(NODE,b,bc)})
    link(0,[18,2],1,[16,15]);link(1,[16,17],0,[18,3])
    link(1,[16,10],2,[16,20]);link(2,[16,21],1,[16,11])
    link(2,[0,10],3,[8,10]);link(3,[8,11],2,[1,10])
    link(2,[31,10],10,[8,10]);link(10,[8,11],2,[30,10])
    for cell,index in doors:link(0,cell,index,[8,10]);link(index,[8,11],0,[cell[0],cell[1]+1])
    for index,r in enumerate(rooms):
        events=r['events'];mask=np.array([[v=='.' for v in row] for row in r['layout']]);start=[18,24] if index==0 else [16,15] if index==1 else [16,20] if index==2 else [8,10]
        found=reachable(mask,start)
        for door in [l['from']['cell'] for l in links if l['from']['room']==index]:assert tuple(door) in found,('出口へ到達不可',index,door)
        for event in events:assert any((event['cell'][0]+dx,event['cell'][1]+dy) in found for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(0,2)]),('人物へ到達不可',index,event['id'])
    d=definition['first_region'];d['castle_entrance']=dict(cell=[43,43],outward=[0,1]);d['castle_exit']=point(NODE,0,[18,25]);d['castle_spawn']=point(NODE,0,[18,24]);d['castle_doors']=links
    definition['sites']=[s for s in definition['sites'] if s['id']!=NODE]+[dict(id=NODE,type='town',legacy=False,rooms=rooms)]
    visual['maps'].update(maps)
    write(ROOT/'world/first_region.json',definition);write(ROOT/'world/first_region_visuals.json',visual)
    interiors=json.loads((ROOT/'world/interiors.json').read_text(encoding='utf8'));interiors['sites']=[s for s in interiors['sites'] if s['id']!=NODE]+[definition['sites'][-1]];interiors['first_region']=d;write(ROOT/'world/interiors.json',interiors)
    # 見た目の案では城下町だけを描く（城内・店は初版のまま。目標との比較は build_castle_town_polish_review.py が実画面で作る）
    for index in ([0,1,2,3,4,8,10] if VARIANT=='0' else [0]):render(maps[f'{NODE}:{index}'],rooms[index]['events']).save(OUT/f'map-{index:02}.png')
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),22)
    for name,index,reference in [('town',0,'first-castle-town.png'),('hall',2,'first-castle-hall.png')][:2 if VARIANT=='0' else 0]:
        canvas=Image.new('RGB',(1536,620),'#d6d2bb');draw=ImageDraw.Draw(canvas)
        for i,path in enumerate([ROOT/'docs/reference/visual-targets'/reference,OUT/f'map-{index:02}.png']):
            im=Image.open(path);im.thumbnail((752,562),Image.Resampling.NEAREST);canvas.paste(im,(i*768+(768-im.width)//2,45));draw.text((i*768+12,8),'依頼者の目標画像' if i==0 else '本番配置データから描画',font=font,fill='#14212b')
        canvas.save(OUT/(name+'-comparison.png'))
    print('CASTLE_MAPS_PASS: rooms=11 town_residents=8 linked_doors='+str(len(links)))

if __name__=='__main__':main()
