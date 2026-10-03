#!/usr/bin/env python3
"""採用済み配置案を、本番の描画層・通行地形・通常イベントへ接続する。"""
from pathlib import Path
from collections import deque
import copy, hashlib, json, math

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
    door_x=width//2
    m.layer('壁',[[x,y,m.tile('assets/tiles/bright_interior_wall.png',(0,0,32,32))] for y in range(height) for x in range(width) if y==0 or x in (0,width-1) or (y==height-1 and x!=door_x)])
    m.stamp('assets/tiles/bright_house_door.png',door_x,height-1,block=False)
    mask=np.ones((height,width),bool);mask[0,:]=False;mask[-1,:]=False;mask[:,[0,-1]]=False;mask[-1,width//2]=True
    def stamp(path,x,y):
        m.stamp(path,x,y);w,h=next(e['size'] for e in REG['assets'] if e['path']==path)
        mask[y:y+h//32,x:x+w//32]=False
    if kind=='home':
        # 寝室・食卓・収納を分け、床の上に敷物、壁に窓を置く。
        m.layer('敷物',[[8+x,4+y,m.tile('assets/tiles/bright_rug.png',(x*32,y*32,32,32))] for y in range(2) for x in range(2)])
        for x in (3,7,11):m.stamp('assets/tiles/bright_house_window.png',x,0,block=False)
        stamp('assets/tiles/bright_bed.png',2,2)
        stamp('assets/tiles/bright_shelf.png',1,1);stamp('assets/tiles/bright_shelf.png',13,1)
        stamp('assets/tiles/bright_table.png',9,4)
        for x,y in [(8,4),(10,4),(9,5)]:stamp('assets/tiles/bright_chair.png',x,y)
        for x,y in [(3,2),(12,5)]:stamp('assets/tiles/bright_pot.png',x,y)
        stamp(obj('barrels'),1,6);stamp(obj('crates'),12,6)
        stamp('assets/tiles/bright_shelf.png',5,1)
        for x in (8,9):stamp('assets/tiles/bright_shop_counter.png',x,1)
    else:
        stamp('assets/tiles/bright_shop_counter.png',3,3);stamp('assets/tiles/bright_shop_counter.png',5,3)
        if kind=='inn':
            for x in (2,5,8):stamp('assets/tiles/bright_bed.png',x,5)
        else:
            stamp('assets/tiles/bright_shelf.png',1,1);stamp('assets/tiles/bright_shelf.png',8,1);stamp('assets/tiles/bright_pot.png',8,5)
    result=payload(m);result['surround']='assets/tiles/bright_house_wall.png'
    return result,mask

def filled_cave(cave):
    """旧地形の黒い未使用画素だけを岩上面で埋め、床・壁の境界は保持する。"""
    old='assets/tiles/cave_thick_wall_autotile.png';new='assets/tiles/cave_filled_wall_autotile.png'
    pixels=np.array(Image.open(ROOT/old).convert('RGBA'))
    rock=np.array(Image.open(ROOT/'assets/tiles/cave_wall_top.png').convert('RGBA'))
    yy,xx=np.indices(pixels.shape[:2]);empty=np.all(pixels[:,:,:3]==1,axis=2)
    pixels[empty]=rock[yy[empty]%rock.shape[0],xx[empty]%rock.shape[1]]
    Image.fromarray(pixels).save(ROOT/new)
    entry=copy.deepcopy(next(e for e in REG['assets'] if e['path']==old))
    entry.update(path=new,tool='Python/Pillow',modified='本番描画用。元のアトラスのRGB(1,1,1)の未使用画素だけを登録済み岩上面で充填。床・水・64px壁の画素と通行範囲は維持。',component_sources=[old,'assets/tiles/cave_wall_top.png'])
    REG['assets']=[e for e in REG['assets'] if e['path']!=new]+[entry]
    write(ROOT/'assets/registry.json',REG)
    for tile in cave['tiles'].values():
        if tile['path']==old:tile['path']=new
    cave['surround']='assets/tiles/cave_wall_top.png'
    assert all(not np.all(pixels[y:y+32,x:x+32,:3]==1) for y in range(0,pixels.shape[0],32) for x in range(0,pixels.shape[1],32))

def connected_water(world,water):
    """川と海を一つの水域として、四分セルの47接続タイルで描く。通行セルは変えない。"""
    # 8px単位で輪郭だけを丸める。素材画像自体をぼかす処理は行わない。
    field=np.repeat(np.repeat(water,4,axis=0),4,axis=1).astype(float)
    for _ in range(7):
        padded=np.pad(field,1,mode='edge')
        field=sum(padded[dy:dy+field.shape[0],dx:dx+field.shape[1]] for dy in range(3) for dx in range(3))/9
    fine=field>=0.5
    assert np.array_equal(fine[2::4,2::4],water),'水際の表示と通行セル中心が不一致'
    m=Map('connected_water',world['width'],world['height']);m.catalog=world['tiles'];m.reverse={(e['path'],*e['region']):key for key,e in m.catalog.items()}
    path='assets/tiles/natural_auto_river.png';cols=ENTRIES[path]['grid'][0];cells=[]
    for y,x in np.argwhere(fine):
        mask=neighbor_mask(fine,int(x),int(y));j=MASKS.index(mask);index=((int(y)%4)*4+int(x)%4)*48+j
        tile=m.tile('assets/tiles/natural_water.png',(int(x)*8%128,int(y)*8%128,8,8)) if mask==255 else m.tile(path,(index%cols*32,index//cols*32,32,32))
        cells.append([int(x),int(y),tile])
    world['layers'].append(dict(name='接続水域',cell_size=8,cells=cells))
    world['tiles']=m.catalog
    return len(cells)

def reachable(mask,start):
    seen={tuple(start)};q=deque(seen)
    while q:
        x,y=q.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=yy<len(mask) and 0<=xx<len(mask[0]) and mask[yy,xx] and (xx,yy) not in seen:seen.add((xx,yy));q.append((xx,yy))
    return seen

REG=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))

def cave_entrance_art():
    """既存の岩上面・側面・床だけで64pxの岩山と開口部を合成する。"""
    path='assets/objects/first_cave_entrance.png'
    rock=Image.open(ROOT/'assets/tiles/cave_wall_top.png').convert('RGBA').crop((0,0,64,64))
    side=Image.open(ROOT/'assets/tiles/cave_wall_side.png').convert('RGBA').crop((0,0,64,64))
    shape=Image.new('L',(64,64));d=ImageDraw.Draw(shape)
    d.polygon([(2,61),(4,39),(10,33),(12,20),(20,16),(24,5),(35,2),(43,8),(47,18),(55,22),(57,36),(62,46),(62,63)],fill=255)
    rock.alpha_composite(side.crop((0,28,64,64)),(0,28));rock.putalpha(shape)
    d=ImageDraw.Draw(rock)
    d.polygon([(22,61),(22,42),(24,33),(29,28),(36,28),(41,35),(43,45),(43,63)],fill=(1,1,1,255))
    floor=Image.open(ROOT/'assets/tiles/cave_quiet_floor.png').convert('RGBA').crop((0,0,20,6))
    rock.alpha_composite(floor,(23,58));rock.save(ROOT/path)
    entry=dict(path=path,kind='object',size=[64,64],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-27',prompt_record='assets/source_records/sprint0-rock-pixel.json',modified='登録済み岩上面・側面・床を64pxへ切り出し、岩山の輪郭と暗い開口部を二値透過で合成。元の素材は変更しない。',component_sources=['assets/tiles/cave_wall_top.png','assets/tiles/cave_wall_side.png','assets/tiles/cave_quiet_floor.png'])
    REG['assets']=[e for e in REG['assets'] if e['path']!=path]+[entry]

def main():
    # 後続のスプリントを含む現在の地図では、古い全面再構築を行わず導入だけを局所反映する。
    from first_region_story_data import apply as apply_story
    current = json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'))
    if current['first_region'].get('castle_entrance'):
        apply_story(current)
        write(ROOT/'world/first_region.json', current)
        from build_first_region import patch_interiors
        interiors = json.loads((ROOT/'world/interiors.json').read_text(encoding='utf8'))
        patch_interiors(interiors)
        write(ROOT/'world/interiors.json', interiors)
        print('FIRST_REGION_STORY_DATA: 局所反映・既存の地形と後続拠点を保持')
        return
    global np, Image, ImageDraw, Map, obj, ENTRIES, MASKS, neighbor_mask
    import numpy as np
    from PIL import Image, ImageDraw
    from build_visual_target_mocks import Map, obj, ENTRIES
    from build_natural_autotiles import MASKS, neighbor_mask
    cave_entrance_art()
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
    maps={};home,home_mask=interior('kaina_home',16,9,'home');maps['start_village:0']=home
    d['start']=point('start_village',0,[4,4])
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
        dict(id='join_pc_02',kind='recruit',actor='pc_02',cell=[14,11],join_on_last_line=True,
             speakers=['リオネ','カイナ','リオネ','カイナ','リオネ','一行'],
             text=['その荷物……カイナ、どこへ行くの？','ソルダ洞窟へ。中の様子を、自分の目で確かめたい。','なら、あたしも行く。村の見回りは済ませたし、道を確かめるのは得意だよ。','助かる。でも、一人で先へ走らないでくれ。','分かってるって。危ない道を見つけたら、ちゃんと戻って知らせる。二人で無事に帰ろう。','リオネが仲間になった。']),
        dict(id='join_pc_03',kind='recruit',actor='pc_03',cell=[22,14],join_on_last_line=True,
             speakers=['ハルド','カイナ','ハルド','村の子','ハルド','村の子','ハルド','カイナ','ハルド','カイナ','ハルド','一行'],
             line_actions=['','','hold_bandage','','release_bandage','','','','','','',''],
             line_prompts=['','','包帯の端を押さえる','','合図に合わせて手を離す','','','','','','',''],
             text=['カイナ、少し手を貸してくれないか。この子の包帯を巻き直したい。端を押さえていてほしいんだ。','このあたりでいい？　きつくならないようにするよ。','そう、そのまま。引っ張らずに、ほどけないよう押さえていてくれ。','あ……今度は痛くない。','よし、巻けた。もう端を離して大丈夫だ。ゆっくり頼む。','しっかりしてる！　二人とも、ありがとう。','助かったよ。片手ではうまく巻けなくてね。ところで、旅支度をしているのかい？','これからソルダ洞窟へ行く。リオネも一緒だ。','それなら、私も同行させてほしい。手当ては任せてくれ。ただし、無理をする前に戻ること。それも大事な備えだ。','分かった。危ないときは、遠慮なく止めてくれ。','約束だ。誰か一人が我慢している旅にはしない。さあ、出発しよう。','ハルドが仲間になった。']),
        dict(id='bandage_patient',kind='npc',sprite='npc_boy',cell=[23,14],label='村の子',text=['包帯がほどけちゃって……。ハルドさんが巻き直してくれてるんだ。'],after_errand='haldo',after_text=['もう大丈夫。二人とも、ありがとう！']),
        dict(id='farmer',kind='npc',sprite='npc_farmer',cell=[12,12],patrol=[[12,12],[12,13],[13,13],[13,12]],label='畑仕事の人',text=['洞窟へは、村を出て東へ進みます。']),
        dict(id='resident',kind='npc',sprite='npc_woman',cell=[21,12],patrol=[[21,12],[22,12],[22,13],[21,13]],label='村人',text=['宿で休むと、体力と魔力が戻ります。']),
        dict(id='child',kind='npc',sprite='npc_boy',cell=[20,16],label='子ども',text=['世界地図は、どうぐから開けます。']),
        dict(id='elder',kind='npc',sprite='npc_elder_man',cell=[19,20],label='村人',text=['北の関所では通行証が必要です。'])]
    village_rooms=[room('カイナの家',home_mask,[]),room('ミルフェ村',village_mask,events)]
    d['doors']=[{'from':point('start_village',0,[8,8]),'to':point('start_village',1,[8,8])},{'from':point('start_village',1,[8,7]),'to':point('start_village',0,[8,7])}]
    assert (8,8) in reachable(home_mask,d['start']['cell'])
    for index,(kind,title,cell,sprite,event_kind) in enumerate([('inn','ミルフェ村・宿屋',[28,7],'npc_innkeeper','rest'),('item','ミルフェ村・道具屋',[12,19],'npc_item_clerk','shop'),('weapon','ミルフェ村・武器屋',[28,19],'npc_weapon_clerk','weapon_shop')],2):
        visual,mask=interior('village_'+kind,12 if kind=='inn' else 10,9 if kind=='inn' else 8,kind);maps[f'start_village:{index}']=visual
        width,height=visual['width'],visual['height'];entry=[width//2,height-2];exit_cell=[width//2,height-1]
        event=dict(id='village_'+kind,kind=event_kind,sprite=sprite,cell=[4,2],reach=2,label={'inn':'宿の主人','item':'道具屋','weapon':'武器屋'}[kind],text=['いらっしゃいませ。'])
        village_rooms.append(room(title,mask,[event]))
        d['doors'] += [{'from':point('start_village',1,cell),'to':point('start_village',index,entry)},{'from':point('start_village',index,exit_cell),'to':point('start_village',1,[cell[0],cell[1]+1])}]
    village_reachable=reachable(village_mask,[8,8])
    for p in [[17,23],[14,12],[22,15]]+outside:assert tuple(p) in village_reachable,('村の経路',p)
    cave=source('cave-natural');cave['layers']=[l for l in cave['layers'] if not l['name'].startswith('chest')]
    filled_cave(cave)
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
    # 既存の水際の層を重ねず、最終的な川・海岸を一つの接続図から描く。
    water_count=connected_water(world,semantics=='~')
    world['layers']=[l for l in world['layers'] if l['name'] not in ('river','shore','icon_cave','icon_village')]
    world['layers'][0]['cells']=[[x,y,m.tile('assets/tiles/natural_grass.png',((x%4)*32,(y%4)*32,32,32))] for x,y,_ in world['layers'][0]['cells']]
    world['tiles']=m.catalog
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
    apply_story(definition)
    write(ROOT/'world/first_region.json',definition)
    interiors=json.loads((ROOT/'world/interiors.json').read_text(encoding='utf8'))
    interiors['sites']=[s for s in interiors['sites'] if s['id'] not in ('start_village','first_cave')]+definition['sites'];interiors['first_region']=d
    write(ROOT/'world/interiors.json',interiors)
    write(ROOT/'world/first_region_visuals.json',dict(version=1,maps=maps,notes='登録済み素材だけの本番描画層。広域256×256地形は変更せず、最初の地方の32×18セルのみ専用の地形層で表示・通行を一致させる。'))
    print(f'FIRST_REGION_PRESENTATION_DATA: maps=8 village_rooms=5 home=16x9 cave_floors=2 chests=3 gate_bypass=0 connected_water_cells={water_count} global_terrain_changes=0')

if __name__=='__main__':main()
