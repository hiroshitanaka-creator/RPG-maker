"""登録済み素材だけで、第2地方の砂地の沿岸と航路の骨組みを再現する。"""
import copy
import json
from pathlib import Path
from build_visual_target_mocks import Map, empty, ellipse

ROOT = Path(__file__).resolve().parents[1]

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8', newline='\n')

def main():
    # 既存256×256の第2地方（x136〜247）内。町の予定ID brine_port はまだ入口にしない。
    m = Map('second_region_coast', 160, 80)
    origin = (24, 40)
    ocean = []
    for y in range(m.h):
        for x in range(m.w):
            if x >= 72 or y >= 40:
                ocean.append([x, y, m.tile('assets/tiles/natural_water.png', (x%4*32,y%4*32,32,32))])
    m.layer('地面', ocean)
    island = ellipse(m, 144, 60, 14, 17)
    # 砂地の芯と、既存の土の接続タイルによる岸。部屋や町の代用絵は作らない。
    m.terrain('dirt', island)
    sand = []
    for y in range(1,m.h-1):
        for x in range(1,m.w-1):
            if island[y-1:y+2,x-1:x+2].all():
                sand.append([x,y,m.tile('assets/tiles/field_outdoor.png',(96,0,32,32))])
    m.layer('地面', sand)
    for x,y in [(143,57),(144,57),(145,57),(145,58),(146,58)]:
        m.layer('cobble',[[x,y,m.tile('assets/tiles/natural_cobble.png',(x%4*32,y%4*32,32,32))]])
    for x,y in [(141,48),(150,54),(149,66)]:
        m.stamp('assets/objects/natural_pebbles.png',x,y,block=False)
    # 西側の浅瀬。3マス以上の連続した砂浜とする。
    terrain = [''.join('s' if island[y,x] else '~' for x in range(m.w)) for y in range(m.h)]
    layout = [''.join('.' if island[y,x] else '#' for x in range(m.w)) for y in range(m.h)]
    layers = m.layers+[v[2] for v in sorted(m.objects)]
    config = dict(version=1,base='63241bc',name='第2地方の沿岸（仮）',origin=list(origin),width=m.w,height=m.h,
                  bounds=[24,40,183,119],terrain=terrain,layout=layout,tiles=m.catalog,layers=layers,
                  island_bounds=[154,83,181,116],walk_goal=[168,99],
                  docks=[dict(id='second_coast',name='第2地方の浅瀬（仮）',ship_cell=[155,109],land=dict(layer='world',node='',room=0,cell=[156,109]))],
                  sea_background='sea',ground_background='desert',ground_encounter_status='registered',
                  sea_encounter=dict(chance=.025,groups=[['coast_water_blob'],['coast_redfin'],['coast_red_crab']]),
                  ground_encounter=dict(chance=.025,groups=[['coast_thorn_cactus'],['coast_scorpion'],['coast_worm']]),
                  ground_proposals=[dict(sprite_id='desert_mummy',name='ミイラ（仮）',base_enemy='shell_guard',role='今後の遺跡の候補・通常遭遇には未登録'),
                                    dict(sprite_id='stone_gargoyle',name='石の翼像（仮）',base_enemy='ward_slime',role='今後の遺跡の候補・通常遭遇には未登録')],
                  excluded_from_encounters=['amber_droplet','desert_mummy','stone_gargoyle'],
                  notes='沿岸の骨組み。港町・室内・魔物職解放は未接続。沿岸には刺サボテン・サソリ・砂の虫を通常登録。')
    write(ROOT/'world/second_region_coast.json',config)
    catalog_path = ROOT/'data/catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf8'))
    by_id = {x['id']:x for x in catalog['enemies']}
    for identifier,name,sprite,base in [('coast_water_blob','青い水滴（仮）','blue_water_blob','slime'),
                                      ('coast_redfin','赤びれの牙魚（仮）','redfin_biter','bat'),
                                      ('coast_red_crab','赤爪ガニ（仮）','red_claw_crab','shell_guard'),
                                      ('coast_thorn_cactus','花咲く刺サボテン（仮）','thorn_cactus','shell_guard'),
                                      ('coast_scorpion','サソリ（仮）','desert_scorpion','bat'),
                                      ('coast_worm','砂の虫（仮）','sand_worm','ward_slime')]:
        enemy = copy.deepcopy(by_id[base])
        enemy.update(id=identifier,name=name,sprite_id=sprite,design_status=f'第2地方の依頼者指定の配置。能力・技・弱点・報酬は既存{base}と同値。遭遇率0.025は既存海域・世界地図と同じ。')
        if identifier in by_id:catalog['enemies'][catalog['enemies'].index(by_id[identifier])]=enemy
        else:catalog['enemies'].append(enemy)
    write(catalog_path,catalog)
    print('SECOND_COAST_BUILD: sea=3 land=3 ruins_reserve=2')

if __name__=='__main__':main()
