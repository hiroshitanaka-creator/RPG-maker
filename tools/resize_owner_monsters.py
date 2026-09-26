#!/usr/bin/env python3
"""原画から体格区分ごとに再変換する。原画・配役・保留人物は変更しない。"""
from pathlib import Path
import json,hashlib
from collections import Counter
from PIL import Image
from import_owner_monsters import ROOT,SHEETS,split_parts,convert

RECORD='assets/source_records/owner-monsters-size-review.json'
SMALL=set('green_droplet brown_cave_bat violet_fang_bat violet_spider spotted_mushroom white_shroud green_coil_snake marsh_frog flame_wisp ice_wisp spark_wisp wind_wisp clay_wisp striped_hornet dusk_owl violet_skull_flame blue_water_blob redfin_biter meadow_droplet river_droplet red_droplet amber_droplet violet_droplet charcoal_droplet silver_droplet gold_droplet blazing_droplet crystal_droplet charged_droplet venom_droplet stacked_droplet boulder_droplet spiny_puffer red_claw_crab pale_jellyfish gold_seahorse green_octopus winged_eye red_imp violet_ghost_orb cloud_wisp scroll_dove'.split())
LARGE=set('lava_rock_golem moss_stone_golem bristled_boar brown_forest_bear green_drake reef_shark coil_sea_serpent fang_clam coral_guardian azure_water_drake eagle_griffin gold_thunderbird dark_winged_horse axe_bull_beast three_headed_hound one_eye_ogre white_manytail_fox violet_unicorn gold_plume_bird storm_raven gold_guard_lion silver_guard_lion'.split())
BOSS_EXTENT={'crowned_ogre':156,'crowned_club_ogre':144,'brood_spider':156,'horned_armor':144,'stone_sword_golem':156,'red_horn_dragon':176,'crowned_droplet':128,'crowned_crab':176,'violet_kraken':160,'blue_horn_dragon':176,'deep_angler_king':160,'haunted_ship':188,'flame_phoenix':176,'horned_chimera':176,'triple_hydra':176,'winged_sphinx':160}
NAMES={'small':'小','medium':'中','large':'大','boss':'ボス'}

def specification(row):
    id_=row['source_id']
    if row['tier']=='boss':return 'boss',BOSS_EXTENT[id_],[192,160]
    if id_ in SMALL:
        extent=48 if ('droplet' in id_ or 'wisp' in id_ or id_ in ('spotted_mushroom','blue_water_blob','violet_ghost_orb')) else 56
        if id_ in ('stacked_droplet','boulder_droplet','crystal_droplet'):extent=64
        return 'small',extent,[64,64]
    if id_ in LARGE:return 'large',96,[96,96]
    return 'medium',80 if id_ in ('gray_fang_wolf','skeletal_wolf','axe_orc','hollow_armor') else 72,[96,96]

def sized_image(part,box,row):
    category,extent,canvas=specification(row)
    # 既存の32色変換を再利用し、透明余白を除いた絵の長辺を区分値へ合わせる。
    limit=[extent,extent]
    if category=='boss':limit=[min(extent,188),min(extent,156)]
    intermediate=convert(part,box,[limit[0]+4,limit[1]+4],row['mirror'])
    bounds=intermediate.getchannel('A').getbbox();assert bounds
    body=intermediate.crop(bounds);out=Image.new('RGBA',tuple(canvas))
    bottom=canvas[1]-min(2,canvas[1]-body.height)
    out.alpha_composite(body,((canvas[0]-body.width)//2,bottom-body.height))
    return out,category,extent

def main():
    original=json.loads((ROOT/'assets/source_records/owner-monsters.json').read_text(encoding='utf8'))
    registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf8'));entries={e['path']:e for e in registry['assets']}
    cache={};results=[]
    for row in original['imported']:
        source=row['original_file'];number=int(Path(source).stem[4:])
        if source not in cache:cache[source]=split_parts(Image.open(ROOT/source).convert('RGBA'),len(SHEETS[number].split(';')),row['black_threshold'])
        part,box=cache[source][row['slot']-1];assert list(box)==row['crop']
        picture,category,extent=sized_image(part,box,row);dest=ROOT/row['path'];picture.save(dest)
        b=picture.getchannel('A').getbbox();visible=[b[2]-b[0],b[3]-b[1]]
        result={**row,'size':list(picture.size),'size_class':category,'target_extent':extent,'visible_size':visible,'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()};results.append(result)
        entry=entries[row['path']];entry.update(size=list(picture.size),size_class=category,visible_size=visible,conversion_record=RECORD+'#'+row['source_id'])
        note=f"2026-09-27: 体格{NAMES[category]}、絵の長辺{max(visible)}px。原本から最近傍で再変換し、32色以内と二値透過を維持。"
        entry['modified']=entry['modified'].split('2026-09-27:')[0].rstrip()+' '+note
    record={'baseline':'883af5e7aa563bcf59155c00137834c697eac153','measurement':'透明余白を除いた不透明領域の長辺。ボスは192×160キャンバス内へ縦横比を保って収める。','imported':results,'counts':dict(Counter(r['size_class'] for r in results))}
    (ROOT/RECORD).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    registry['assets']=list(entries.values());registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    doc=ROOT/'docs/monster-catalog.md';text=doc.read_text(encoding='utf8')
    start=text.index('| id |');end=text.index('\n## 既存22種との対応',start)
    lines=['| id | 仮名 | 外見・原本 | 属性案 | 生息地案 | 強さ案 | 使用 | 体格 | 絵の実寸 | キャンバス |','| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in results:lines.append(f"| {r['id']} | {r['name']} | {r['source_id']} / {Path(r['original_file']).name} 左から{r['slot']} | {r['element']} | {r['habitat']} | {r['tier']} | {r['registered_status']} | {NAMES[r['size_class']]} | {r['visible_size'][0]}×{r['visible_size'][1]} | {r['size'][0]}×{r['size'][1]} |")
    text=text[:start]+'\n'.join(lines)+'\n'+text[end:]
    text=text.replace('通常敵は96×96、ボスは192×160のキャンバス。','体格は透明余白を除いた絵の長辺で区別する。小48〜64px、中64〜80px、大96px、ボス128〜192px。キャンバスは32pxの倍数を維持する。')
    text=text.replace('ボスと原画で大型に描かれたものは192×160に保ち、通常敵へ無理に縮めない。','絵の体格を小・中・大・ボスで分ける。ボス用キャンバスは192×160以内、通常敵は64×64または96×96とし、透明余白ではなく不透明領域の長辺を測る。')
    doc.write_text(text,encoding='utf8',newline='\n')
    print('MONSTER_SIZE_BUILD: '+json.dumps(record['counts'],ensure_ascii=False))

if __name__=='__main__':main()
