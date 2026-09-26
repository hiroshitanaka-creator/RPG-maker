#!/usr/bin/env python3
"""採用済み配置案を、本番の描画層・通行地形・通常イベントへ接続する。"""
from pathlib import Path
from collections import deque
import copy, hashlib, json, math
import numpy as np
from PIL import Image
from build_visual_target_mocks import Map, obj

ROOT=Path(__file__).resolve().parents[1]
MOCK=ROOT/'docs/verification/art-review-2/mock-maps'

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def point(node,room,cell):return dict(layer='interior',node=node,room=room,cell=cell)
def world_point(cell):return dict(layer='world',node='',room=0,cell=cell)
def payload(m):
    return dict(version=1,id=m.id,tile_size=32,width=m.w,height=m.h,tiles=m.catalog,layers=m.layers+[a[2] for a in sorted(m.objects)],origin=[0,0])
def source(name):
    path=MOCK/(name+'.json');d=json.loads(path.read_text(encoding='utf8'));d.pop('actors',None)
    d['source_file']=path.relative_to(ROOT).as_posix();d['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();d['origin']=[0,0]
    return d
def rows(mask):return [''.join('.' if v else '#' for v in row) for row in mask]
def room(title,mask,events,**extra):return dict(title=title,layout=rows(mask),events=events,**extra)
def is_ground(name):return name in ('地面','dirt','shore','hills','forest','mountains','river','64px岩壁・丸い湖・床の自動接続')
def collision(d):
    mask=np.ones((d['height'],d['width']),bool);mask[[0,-1],:]=False;mask[:,[0,-1]]=False
    solid=('house','well','haystack','barrels','crates','shrine','fence','tree','flowerbed','cabbage','carrots')
    for layer in d['layers']:
        if is_ground(layer['name']) or not layer['cells'] or not any(t in layer['name'] for t in solid):continue
        bottom=max(c[1] for c in layer['cells'])
        for x,y,_ in layer['cells']:
            if 'tree' not in layer['name'] or y==bottom:mask[y,x]=False
    return mask
def interior(id_,width,height,kind):
    m=Map(id_,width,height);m.base('assets/tiles/bright_wood_floor.png')
    door_x=5 if kind=='home' else width//2
    m.layer('壁',[[x,y,m.tile('assets/tiles/bright_interior_wall.png',(0,0,32,32))] for y in range(height) for x in range(width) if y==0 or x in (0,width-1) or (y==height-1 and x!=door_x)])
    m.stamp('assets/tiles/bright_house_door.png',door_x,height-1,block=False)
    mask=np.ones((height,width),bool);mask[0,:]=False;mask[-1,:]=False;mask[:,[0,-1]]=False;mask[-1,width//2]=True
    def stamp(path,x,y):
        m.stamp(path,x,y);w,h=next(e['size'] for e in REG['assets'] if e['path']==path)
        mask[y:y+h//32,x:x+w//32]=False
    if kind=='home':
        stamp('assets/tiles/bright_bed.png',1,1);stamp('assets/tiles/bright_table.png',3,2);stamp('assets/tiles/bright_chair.png',4,2)
        stamp('assets/tiles/bright_shelf.png',6,1);stamp('assets/tiles/bright_pot.png',1,4)
        mask[-1,:]=False;mask[-1,5]=True
    else:
        stamp('assets/tiles/bright_shop_counter.png',3,3);stamp('assets/tiles/bright_shop_counter.png',5,3)
        if kind=='inn':
            for x in (2,5,8):stamp('assets/tiles/bright_bed.png',x,5)
        else:
            stamp('assets/tiles/bright_shelf.png',1,1);stamp('assets/tiles/bright_shelf.png',8,1);stamp('assets/tiles/bright_pot.png',8,5)
    return payload(m),mask

def reachable(mask,start):
    seen={tuple(start)};q=deque(seen)
    while q:
        x,y=q.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=yy<len(mask) and 0<=xx<len(mask[0]) and mask[yy,xx] and (xx,yy) not in seen:seen.add((xx,yy));q.append((xx,yy))
    return seen

REG=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))

def main():
    definition=json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'))
    d=definition['first_region'];d['title']='エルヴァ地方';d['bounds']=[24,40,55,57]
    d['village_entrance']=dict(cell=[32,53],outward=[0,1]);d['cave_entrance']=dict(cell=[48,50],outward=[0,1])
    d['village_exit']=point('start_village',1,[17,23]);d['village_spawn']=point('start_village',1,[17,22])
    d['cave_spawn']=point('first_cave',0,[17,22]);d['cave_exit']=point('first_cave',0,[17,23])
    d['stairs_down']=dict(**{'from':point('first_cave',0,[17,5]),'to':point('first_cave',1,[17,21])})
    d['stairs_up']=dict(**{'from':point('first_cave',1,[17,22]),'to':point('first_cave',0,[17,6])})
    d['save_probe']=point('first_cave',0,[18,21]);d['boss']['point']=point('first_cave',1,[28,17]);d['boss_revisit']=point('first_cave',1,[27,17])
    d['gate']=dict(before=world_point([43,48]),cell=world_point([43,47]),beyond=world_point([43,46]),id='first_gate')
    d['recruits']=[dict(stand=point('start_village',1,[14,12]),facing=[0,-1]),dict(stand=point('start_village',1,[22,15]),facing=[0,-1])]
    maps={};home,home_mask=interior('kaina_home',8,6,'home');maps['start_village:0']=home
    village=source('village-farm-a');maps['start_village:1']=village
    outside=[[8,7],[28,7],[12,19],[28,19]]
    doorway_cells={tuple(p) for p in outside}|{(x,y+1) for x,y in outside}
    # 比較用の木箱が玄関へ重なっていた分だけ、本番では玄関横へ置く。
    for layer in village['layers']:
        if layer['name']=='natural_crates' and layer['cells'] and min(c[0] for c in layer['cells'])==14 and min(c[1] for c in layer['cells'])==19:
            layer['cells']=[[x+2,y-1,identifier] for x,y,identifier in layer['cells']]
        if layer['name']=='natural_barrels' and layer['cells'] and min(c[0] for c in layer['cells'])==25 and min(c[1] for c in layer['cells'])==19:
            layer['cells']=[[x-2,y-2,identifier] for x,y,identifier in layer['cells']]
        if any(tuple(c[:2]) in doorway_cells for c in layer['cells']) and any(t in layer['name'] for t in ('crates','barrels','flowerbed','pebbles','tufts')):
            layer['cells']=[[x+3,y,identifier] for x,y,identifier in layer['cells'] if x+3<village['width']]
    village_mask=collision(village)
    for x,y in doorway_cells:village_mask[y,x]=True
    village_mask[22:24,17]=True
    events=[
        dict(id='join_pc_02',kind='recruit',actor='pc_02',cell=[14,11],text=['こんにちは。一緒に洞窟まで行こう。']),
        dict(id='join_pc_03',kind='recruit',actor='pc_03',cell=[22,14],text=['こんにちは。私も同行します。']),
        dict(id='farmer',kind='npc',sprite='npc_farmer',cell=[12,12],patrol=[[12,12],[12,13],[13,13],[13,12]],label='畑仕事の人',text=['洞窟へは、村を出て東へ進みます。']),
        dict(id='resident',kind='npc',sprite='npc_woman',cell=[21,12],patrol=[[21,12],[22,12],[22,13],[21,13]],label='村人',text=['宿で休むと、体力と魔力が戻ります。']),
        dict(id='child',kind='npc',sprite='npc_boy',cell=[20,16],label='子ども',text=['世界地図は、どうぐから開けます。']),
        dict(id='elder',kind='npc',sprite='npc_elder_man',cell=[19,20],label='村人',text=['北の関所では通行証が必要です。'])]
    village_rooms=[room('カイナの家',home_mask,[]),room('ミルフェ村',village_mask,events)]
    d['doors']=[{'from':point('start_village',0,[5,5]),'to':point('start_village',1,[8,8])},{'from':point('start_village',1,[8,7]),'to':point('start_village',0,[5,4])}]
    for index,(kind,title,cell,sprite,event_kind) in enumerate([('inn','ミルフェ村・宿屋',[28,7],'npc_innkeeper','rest'),('item','ミルフェ村・道具屋',[12,19],'npc_item_clerk','shop'),('weapon','ミルフェ村・武器屋',[28,19],'npc_weapon_clerk','weapon_shop')],2):
        visual,mask=interior('village_'+kind,12 if kind=='inn' else 10,9 if kind=='inn' else 8,kind);maps[f'start_village:{index}']=visual
        width,height=visual['width'],visual['height'];entry=[width//2,height-2];exit_cell=[width//2,height-1]
        event=dict(id='village_'+kind,kind=event_kind,sprite=sprite,cell=[4,2],reach=2,label={'inn':'宿の主人','item':'道具屋','weapon':'武器屋'}[kind],text=['いらっしゃいませ。'])
        village_rooms.append(room(title,mask,[event]))
        d['doors'] += [{'from':point('start_village',1,cell),'to':point('start_village',index,entry)},{'from':point('start_village',index,exit_cell),'to':point('start_village',1,[cell[0],cell[1]+1])}]
    village_reachable=reachable(village_mask,[8,8])
    for p in [[17,23],[14,12],[22,15]]+outside:assert tuple(p) in village_reachable,('村の経路',p)
    cave=source('cave-natural');cave['layers']=[l for l in cave['layers'] if not l['name'].startswith('chest')]
    floor=np.array(Image.open(ROOT/'docs/verification/art-review-2/floor-mask.png'),dtype=bool)
    for i in range(1,4):floor &= ~np.array(Image.open(ROOT/f'docs/verification/art-review-2/lake-{i}-mask.png'),dtype=bool)
    cave_mask=floor[16::32,16::32].copy()
    cave_rooms=[]
    for index in range(2):
        maps[f'first_cave:{index}']=copy.deepcopy(cave)
        cells=[[10,17],[16,10]] if index==0 else [[25,8]]
        treasure=[dict(id=f'first_chest_{i+1 if index==0 else 3}',kind='treasure',cell=p,item='potion',amount=2 if i==0 else 1) for i,p in enumerate(cells)]
        cave_rooms.append(room(f'ソルダ洞窟 地下{index+1}階',cave_mask,treasure,floor=index+1))
    found=reachable(cave_mask,[17,22])
    for p in [[17,5],[17,6],[18,21],[17,23],[28,17],[27,17],[10,17],[16,10],[25,8]]:assert tuple(p) in found,('洞窟の経路',p)
    world=source('world-organic');world['origin']=[24,40]
    # 比較案の城・塔は後続の作業対象。入れない拠点の印をプレイ可能範囲へ置かない。
    world['layers']=[l for l in world['layers'] if l['name'] not in ('gate','icon_castle','icon_tower')]
    maps['world']=world
    semantics=np.full((world['height'],world['width']),'~')
    for l in world['layers']:
        name=l['name'];value={'shore':'g','hills':'g','forest':'f','mountains':'m','river':'~','dirt':'r','bright_bridge':'b'}.get(name)
        if value:
            for x,y,_ in l['cells']:semantics[y,x]=value
    water=np.zeros_like(semantics,dtype=bool)
    for x in range(world['width']):water[7,x]=True;water[6 if math.sin(x/4)>0 else 8,x]=True
    water[6:9,19]=False
    world['layers']=[layer for layer in world['layers'] if is_ground(layer['name']) or layer['name']=='bright_bridge' or not any(water[y,x] for x,y,_ in layer['cells'])]
    m=Map('river_overlay',world['width'],world['height']);m.catalog=world['tiles'];m.reverse={(e['path'],*e['region']):key for key,e in m.catalog.items()}
    m.terrain('river',water);world['layers'].extend(m.layers);world['tiles']=m.catalog;semantics[water]='~'
    edge=np.zeros_like(water)
    for y in range(world['height']):
        for x in range(world['width']):
            distance=min(x,world['width']-1-x,y,world['height']-1-y)
            edge[y,x]=distance==0 or (distance==1 and math.sin(x*0.9+y*1.3)>0.3)
    edge &= semantics!='~'
    m.layers=[];m.terrain('mountains',edge);world['layers'].extend(m.layers);semantics[edge]='m'
    for x,y in [(19,6),(19,7),(19,8),(8,13),(8,14),(24,10),(24,11)]:semantics[y,x]='r'
    world['terrain']=[''.join(row) for row in semantics];world['layout']=rows(~np.isin(semantics,['~','m']))
    world['residents']=[dict(id='first_gatekeeper',kind='npc',sprite='npc_gatekeeper',cell=[42,48],label='門番',text=['通行証を確認します。'])]
    mask=~np.isin(semantics,['~','m']);mask[7,19]=False
    assert (19,6) not in reachable(mask,[8,14]),'通行証なしで関所の北へ迂回できる'
    mask[7,19]=True
    for p in [(19,6),(19,8),(24,10)]:assert p in reachable(mask,[8,14]),('世界の経路',p)
    for key,mask in [('start_village:0',home_mask),('start_village:1',village_mask),('first_cave:0',cave_mask),('first_cave:1',cave_mask)]:maps[key]['layout']=rows(mask)
    for index in range(2,5):maps[f'start_village:{index}']['layout']=village_rooms[index]['layout']
    previous_sites={s['id']:s for s in definition['sites']}
    previous_sites['start_village']['rooms']=village_rooms
    previous_sites['first_cave']['rooms']=cave_rooms
    definition['sites']=[previous_sites['start_village'],previous_sites['first_cave']]
    write(ROOT/'world/first_region.json',definition)
    interiors=json.loads((ROOT/'world/interiors.json').read_text(encoding='utf8'))
    interiors['sites']=[s for s in interiors['sites'] if s['id'] not in ('start_village','first_cave')]+definition['sites'];interiors['first_region']=d
    write(ROOT/'world/interiors.json',interiors)
    write(ROOT/'world/first_region_visuals.json',dict(version=1,maps=maps,notes='登録済み素材だけの本番描画層。広域256×256地形は変更せず、最初の地方の32×18セルのみ専用の地形層で表示・通行を一致させる。'))
    print('FIRST_REGION_PRESENTATION_DATA: maps=8 village_rooms=5 cave_floors=2 chests=3 gate_bypass=0 global_terrain_changes=0')

if __name__=='__main__':main()
