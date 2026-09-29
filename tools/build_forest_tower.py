"""依頼者の森の塔の目標と登録済み素材から、3階と通常移動の接続を作る。"""
import copy, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from build_visual_target_mocks import Map, ENTRIES
from build_first_region_presentation import payload, point, room, rows, reachable
from build_castle_town import render
from build_natural_autotiles import MASKS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/sprint5-forest-tower'
NODE='first_forest_tower'

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reference=ROOT/'assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_1009.PNG'
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    # 苔石の床・壁・森を敷き、二値の曲線で円形の壁を作る。
    w,h=640,512;yy,xx=np.indices((h,w));cx,cy=320,258
    outer=((xx-cx)/301)**2+((yy-cy)/239)**2<=1
    inner=((xx-cx)/257)**2+((yy-cy-20)/178)**2<=1
    files=['assets/tiles/natural_moss_floor.png','assets/tiles/natural_moss_wall.png','assets/tiles/natural_auto_forest.png']
    tiled=[]
    for path in files:
        a=np.array(Image.open(ROOT/path).convert('RGBA'));tiled.append(a[yy%a.shape[0],xx%a.shape[1]])
    forest_atlas=np.array(Image.open(ROOT/files[2]).convert('RGBA'))
    forest_entry=ENTRIES[files[2]];phase=forest_entry['autotile']['phase_cells'][0];cols=forest_entry['grid'][0]
    for ty in range(h//32):
        for tx in range(w//32):
            index=((ty%phase)*phase+tx%phase)*48+MASKS.index(255)
            sx,sy=index%cols*32,index//cols*32
            tiled[2][ty*32:(ty+1)*32,tx*32:(tx+1)*32]=forest_atlas[sy:sy+32,sx:sx+32]
    # 画素の色を補間しない。曲線の縁にも半透明を作らない。
    small_moss=np.array(Image.open(ROOT/files[0]).convert('RGBA').resize((64,64),Image.Resampling.NEAREST))
    stone_path='assets/tiles/natural_stone_floor.png'
    small_stone=np.array(Image.open(ROOT/stone_path).convert('RGBA').resize((64,64),Image.Resampling.NEAREST))
    floor=small_stone[yy%64,xx%64].copy()
    moss_patch=(np.sin(xx/51)+np.cos(yy/43)>.9)|(((xx-cx)/257)**2+((yy-cy-20)/178)**2>.78)
    floor[moss_patch]=small_moss[yy[moss_patch]%64,xx[moss_patch]%64]
    # 壁面を暗くし、外縁の石の上面は明るく残す。使用色は既存素材の色だけ。
    palette=np.unique(np.concatenate([t[:,:,:3].reshape(-1,3) for t in tiled]+[small_stone[:,:,:3].reshape(-1,3)]),axis=0)
    assert len(palette)<=64
    wall=tiled[1].copy()
    for color in np.unique(wall[:,:,:3].reshape(-1,3),axis=0):
        match=np.all(wall[:,:,:3]==color,axis=2)
        target=color.astype(float)*.67
        nearest=palette[np.argmin(((palette.astype(float)-target)**2).sum(axis=1))]
        wall[match,:3]=nearest
    cap=outer&~ndimage.binary_erosion(outer,iterations=6)
    wall[cap]=tiled[1][cap]
    edge=inner&~ndimage.binary_erosion(inner,iterations=2)
    dark=palette[np.argmin(((palette.astype(float)-np.array([39,43,31]))**2).sum(axis=1))]
    floor[edge,:3]=dark
    a=tiled[2].copy();a[outer]=wall[outer];a[inner]=floor[inner]
    # 南側に出入口の石床を通す。
    a[440:512,304:336]=floor[440:512,304:336]
    floor_path='assets/tiles/forest_tower_round_room.png'
    Image.fromarray(a).save(ROOT/floor_path)
    colors=len(set(map(tuple,a[:,:,:3].reshape(-1,3).tolist())))
    assert colors<=64,colors
    entry=copy.deepcopy(ENTRIES['assets/tiles/natural_moss_floor.png'])
    entry.update(path=floor_path,size=[w,h],max_colors=64,tool='Python/Pillow',source='generated',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-29',prompt_record='assets/source_records/forest-tower.json',conversion_record='assets/source_records/forest-tower.json',modified='既存の苔床・苔壁・森の画素を、円形の床と壁へ配置。半透明・ぼかしなし。')
    registry['assets']=[e for e in registry['assets'] if e['path']!=floor_path]+[entry]
    write(ROOT/'assets/registry.json',registry);ENTRIES[floor_path]=entry
    definition=json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'))
    visuals=json.loads((ROOT/'world/first_region_visuals.json').read_text(encoding='utf8'))
    d=definition['first_region'];rooms=[];maps={};doors=[]
    speech=(ROOT/'docs/first-region-recruit-scenes.md').read_text(encoding='utf8').split('## スイナ')[1]
    lines=[line[2:].split('：',1) for line in speech.splitlines() if line.startswith('- ') and '：' in line]
    assert len(lines)==10
    for floor in range(3):
        m=Map('forest_tower_'+str(floor+1),20,16);m.base(floor_path)
        mask=np.zeros((16,20),bool)
        for y in range(16):
            for x in range(20):mask[y,x]=inner[min(y*32+16,h-1),x*32+16]
        for y in range(12,16):mask[y,10]=True
        def stamp(path,x,y,solid=True):
            m.stamp(path,x,y,block=solid)
            if solid:
                sw,sh=ENTRIES[path]['size'];mask[y:y+sh//32,x:x+sw//32]=False
        for x,y in [(4,4),(14,10),(4,10)]:stamp('assets/objects/natural_broken_pillar.png',x,y)
        for x,y in [(3,7),(16,5)]:stamp('assets/objects/natural_rubble.png',x,y)
        if floor<2:
            stamp('assets/objects/natural_stairs_up.png',14,3,False)
            mask[4,15]=True
        if floor>0:stamp('assets/objects/natural_stairs_down.png',8,12,False)
        events=[dict(id='forest_tower_chest_'+str(floor+1),kind='treasure',cell=[7,9],item='potion',amount=2)]
        if floor==1:
            # 台詞の「東の階段の先が崩れた」に対応する、調べられる崩れ跡。
            stamp('assets/objects/natural_rubble.png',16,7)
            events.append(dict(id='collapsed_east_stair',kind='npc',sprite='npc_castle_guard',cell=[15,8],label='調査中の兵士',text=['東の階段は途中で崩れている。上へ行くなら、北の階段を使ってくれ。']))
        if floor==2:
            events.append(dict(id='recruit_suina',kind='recruit',actor='pc_04',cell=[11,5],label='スイナ',join_on_last_line=True,requires_clear='forest_tower_boss',speakers=[l[0] for l in lines],text=[l[1] for l in lines]))
        p=payload(m);p['layout']=rows(mask);p['surround']='assets/tiles/natural_forest.png' if (ROOT/'assets/tiles/natural_forest.png').exists() else 'assets/tiles/natural_grass.png'
        maps[NODE+':'+str(floor)]=p
        rooms.append(room('森の塔 '+str(floor+1)+'階',mask,events,floor=floor))
        start=[10,14] if floor==0 else [9,11]
        found=reachable(mask,start)
        for target in [[7,9]]+([[15,4]] if floor<2 else [[10,6],[11,6]]):assert tuple(target) in found,(floor,target)
    for floor in range(2):
        doors += [dict(from_=point(NODE,floor,[15,4]),to=point(NODE,floor+1,[9,11])),dict(from_=point(NODE,floor+1,[9,13]),to=point(NODE,floor,[15,5]))]
    doors=[{'from':l['from_'],'to':l['to']} for l in doors]
    d.update(tower_entrance=dict(cell=[41,41],outward=[0,1]),tower_spawn=point(NODE,0,[10,14]),tower_exit=point(NODE,0,[10,15]),tower_doors=doors,
        tower_boss=dict(id='forest_tower_boss',point=point(NODE,2,[10,6]),enemies=['watch_beast'],sprite='assets/monsters/black_guardian_beast/idle.png'))
    # 敵画像は現在の敵IDの登録済み対応を使う。
    enemy=next(e for e in json.loads((ROOT/'data/catalog.json').read_text(encoding='utf8'))['enemies'] if e['id']=='watch_beast')
    d['tower_boss']['sprite']='assets/monsters/'+enemy['sprite_id']+'/idle.png'
    assert (ROOT/d['tower_boss']['sprite']).exists(),d['tower_boss']['sprite']
    d['encounters'][NODE]=copy.deepcopy(d['encounters']['first_cave'])
    path_cells=[[47,43],[48,43],[49,43],[50,43],[50,42],[50,41]]
    d['tower_mountain_path']=path_cells
    world=visuals['maps']['world'];ox,oy=world['origin'];tile_id='tower_mountain_path'
    forest=Map('tower_forest',world['width'],world['height']);field=np.zeros((world['height'],world['width']),bool)
    for x,y in [(40,41),(41,41),(42,41),(40,42),(41,42),(42,42)]:
        field[y-oy,x-ox]=True
        row=list(world['terrain'][y-oy]);row[x-ox]='f';world['terrain'][y-oy]=''.join(row)
    forest.terrain('forest',field)
    world['tiles'].update({'tower_forest_'+k:v for k,v in forest.catalog.items()})
    world['layers']=[l for l in world['layers'] if not l.get('forest_tower_woods')]
    for layer in forest.layers:
        world['layers'].append(dict(name=layer['name'],cells=[[x,y,'tower_forest_'+tid] for x,y,tid in layer['cells']],forest_tower_woods=True))
    world['tiles'][tile_id]=dict(path='assets/tiles/natural_stone_floor.png',region=[0,0,32,32])
    world['layers']=[l for l in world['layers'] if not l.get('forest_tower_path')]
    world['layers'].append(dict(name='地面',cells=[[x-ox,y-oy,tile_id] for x,y in path_cells],forest_tower_path=True))
    for x,y in path_cells:
        for key,value in [('layout','.'),('terrain','r')]:
            row=list(world[key][y-oy]);row[x-ox]=value;world[key][y-oy]=''.join(row)
    world['residents']=[e for e in world.get('residents',[]) if e.get('id')!='tower_path_guard']
    world['residents'].append(dict(id='tower_path_guard',kind='npc',sprite='npc_castle_guard',cell=[48,44],label='山道の兵士',tower_path=True,text=['森の塔の調査が済むまで、この山道は通せない。城の北西の森にある塔を確かめてくれ。'],after_text=['塔の調査、お疲れさま。山道を通ってよい。足元に気をつけて。']))
    site=dict(id=NODE,type='dungeon',legacy=False,rooms=rooms)
    definition['sites']=[s for s in definition['sites'] if s['id']!=NODE]+[site]
    visuals['maps'].update(maps)
    interiors=json.loads((ROOT/'world/interiors.json').read_text(encoding='utf8'))
    interiors['sites']=[s for s in interiors['sites'] if s['id']!=NODE]+[site];interiors['first_region']=d
    write(ROOT/'world/first_region.json',definition);write(ROOT/'world/interiors.json',interiors);write(ROOT/'world/first_region_visuals.json',visuals)
    for floor in range(3):render(maps[NODE+':'+str(floor)],rooms[floor]['events']).save(OUT/f'floor-{floor+1}-layout.png')
    target=ROOT/'docs/reference/visual-targets/forest-tower.png';target.write_bytes(reference.read_bytes())
    write(ROOT/'assets/source_records/forest-tower.json',dict(reference=str(reference.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),source='依頼者がGrokで生成した原画。公開・ゲーム使用を承認済み。',derived_assets=[floor_path],component_sources=files+[stone_path],method='床は最近傍で半分の模様へ。壁面は同じ64色以内で暗くし、上面と区別。塔は3階、階段・宝箱・最上階の敵を通常歩行へ接続。'))
    canvas=Image.new('RGB',(1280,535),'#162835');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),19)
    for index,path in enumerate([reference,OUT/'floor-1-layout.png']):
        im=Image.open(path).convert('RGB');im.thumbnail((620,475),Image.Resampling.NEAREST)
        canvas.paste(im,(index*640+(640-im.width)//2,48))
        draw.text((index*640+12,10),'依頼者の目標 IMG_1009' if index==0 else '本番配置データから描画・1階',font=font,fill='white')
    canvas.save(OUT/'target-comparison.png')
    print('FOREST_TOWER_BUILD_PASS: floors=3 stairs=4 chests=3 recruit_lines=10')

if __name__=='__main__':main()
