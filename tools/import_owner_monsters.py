#!/usr/bin/env python3
"""依頼者の原画を透明な余白で分割し、対応記録付きでゲーム用へ変換する。"""
from pathlib import Path
from collections import deque
import io,json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from validate_assets import load_palette

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'assets/_incoming/owner-2026-09-26'
OUT=ROOT/'docs/verification/owner-monsters'
RECORD='assets/source_records/owner-monsters.json'
BASE='0d025c36c266e9635a1420ccc7cc879cdb1a8ce9'
NOTICE='依頼者が独自の意匠であると判断して採用（2026年9月26日）。公開・販売を検討する段階で再確認する'
PAL=np.array(sorted(load_palette(ROOT/'assets/palette/natural.gpl')),dtype=np.int32)
# 左から順。名称・属性・生息地・強さは配置前の提案。hは役割未定の人型。
SHEETS={
929:'crowned_ogre|棘冠の大鬼|地|cave|boss|F',
933:'green_droplet|緑のしずく|水|plains|early|F;brown_cave_bat|茶翼コウモリ|風|cave|early|F;gray_fang_wolf|灰毛の牙狼|無|forest|early|L;club_goblin|こん棒小鬼|無|plains|early|F;blue_horn_beetle|青角甲虫|地|forest|early|L',
934:'violet_fang_bat|紫の牙コウモリ|闇|cave|middle|F;rock_toad|岩肌ガエル|地|cave|middle|R;violet_spider|紫脚グモ|毒|cave|early|F;spotted_mushroom|斑点キノコ|毒|forest|early|F;lava_rock_golem|熔岩の岩巨人|火|cave|late|F',
935:'hollow_armor|うつろの鎧|闇|castle|middle|F;white_shroud|白い布の魔物|闇|tower|middle|F;toothed_chest|牙付き宝箱|無|cave|middle|F;shield_skeleton|盾持ち骸骨|闇|underworld|middle|F;moss_stone_golem|苔石巨人|地|forest|late|F',
936:'crowned_club_ogre|冠のこん棒鬼|地|castle|boss|F;brood_spider|子連れ大グモ|毒|cave|boss|F;horned_armor|角付きの鎧|闇|tower|boss|F;stone_sword_golem|石剣巨人|地|tower|boss|F',
937:'bristled_boar|剛毛イノシシ|無|plains|middle|L;green_coil_snake|緑巻きヘビ|毒|forest|early|L;brown_forest_bear|森の茶熊|地|forest|middle|L;broadwing_eagle|大翼ワシ|風|sky|middle|L;marsh_frog|沼ガエル|水|plains|early|L',
938:'flame_wisp|火の小精|火|cave|early|F;ice_wisp|氷の小精|氷|cave|middle|F;spark_wisp|雷の小精|雷|tower|middle|F;wind_wisp|風の小精|風|sky|early|F;clay_wisp|土の小精|地|cave|early|F',
939:'green_drake|緑翼の小竜|風|forest|middle|R;crested_raptor|冠羽の猛禽|風|sky|middle|R;striped_hornet|縞の大蜂|毒|forest|early|R;dusk_owl|夕闇フクロウ|闇|forest|middle|F;red_horn_dragon|赤角の火竜|火|cave|boss|L',
940:'rotting_walker|腐敗歩き|闇|underworld|middle|R;h_hooded_spirit|フードの人型霊|闇|underworld|late|F;skeletal_wolf|骸骨狼|闇|underworld|middle|R;sealed_coffin|封じられた棺|闇|underworld|middle|F;violet_skull_flame|紫炎の頭骨|闇|underworld|late|F',
941:'axe_orc|斧の大鬼|地|castle|middle|L;h_masked_scout|覆面の人物|無|castle|middle|F;h_violet_mage|紫衣の術者|闇|tower|middle|F;h_bandit|鉢巻の人物|無|plains|middle|F;h_ochre_mage|黄衣の術者|無|tower|middle|F',
942:'wailing_root|叫び根|地|forest|middle|F;thorn_cactus|花咲く刺サボテン|地|desert|middle|F;blue_water_blob|青い水滴|水|sea|early|F;redfin_biter|赤びれの牙魚|水|sea|middle|L;haunted_sword|ひとりで動く剣|闇|castle|middle|F',
943:'meadow_droplet|草色のしずく|地|plains|early|F;river_droplet|川色のしずく|水|sea|early|F;red_droplet|赤いしずく|火|cave|early|F;amber_droplet|琥珀のしずく|雷|desert|early|F;violet_droplet|紫のしずく|毒|cave|early|F',
944:'charcoal_droplet|炭色のしずく|闇|cave|middle|F;silver_droplet|銀のしずく|無|tower|late|F;gold_droplet|金のしずく|無|castle|late|F;blazing_droplet|炎のしずく|火|cave|middle|F;crystal_droplet|結晶のしずく|氷|cave|middle|F',
945:'charged_droplet|帯電しずく|雷|tower|middle|F;venom_droplet|毒斑のしずく|毒|forest|middle|F;crowned_droplet|冠のしずく|無|castle|boss|F;stacked_droplet|重なりしずく|地|cave|middle|F;boulder_droplet|岩のしずく|地|cave|middle|F',
946:'spiny_puffer|刺ふぐ|水|sea|early|L;red_claw_crab|赤爪ガニ|水|sea|early|F;pale_jellyfish|白クラゲ|水|sea|early|F;gold_seahorse|金色タツノオトシゴ|水|sea|middle|L;green_octopus|緑ダコ|水|sea|early|F',
947:'reef_shark|岩礁ザメ|水|sea|middle|L;coil_sea_serpent|巻き海蛇|水|sea|late|L;lantern_angler|灯りアンコウ|水|sea|middle|L;green_shell_turtle|緑甲羅の海亀|水|sea|middle|L;h_trident_merman|三叉槍の人魚|水|sea|late|F',
948:'fang_clam|大牙の貝|水|sea|late|F;coral_guardian|珊瑚の岩獣|水|sea|late|F;seaweed_eye|海藻の目玉|水|sea|middle|F;h_ghost_sailor|幽霊の船乗り|闇|sea|late|F;azure_water_drake|蒼い水竜|水|sea|late|L',
949:'crowned_crab|冠の大ガニ|水|sea|boss|F;violet_kraken|紫の大ダコ|水|sea|boss|F;h_ghost_captain|幽霊船長|闇|sea|boss|F;blue_horn_dragon|青角の大竜|水|sea|boss|L',
951:'deep_angler_king|深海の灯魚|水|sea|boss|F;h_sea_king|海王の人型|水|sea|boss|F;haunted_ship|魔物の帆船|闇|sea|boss|L',
952:'eagle_griffin|鷲頭の翼獣|風|sky|late|R;stone_gargoyle|石の翼像|地|tower|middle|R;winged_eye|翼の一つ目|闇|tower|middle|F;gold_thunderbird|金の雷鳥|雷|sky|late|L;red_imp|赤翼の小悪魔|火|tower|middle|L',
953:'dark_winged_horse|黒翼の馬|風|sky|late|R;violet_ghost_orb|紫の幽翼玉|氷|cave|middle|F;night_raptor|夜の猛禽|闇|sky|middle|L;h_fairy_knight|妖精の騎士|風|sky|middle|F;cloud_wisp|雲の小精|風|sky|early|F',
954:'flame_phoenix|炎羽の大鳥|火|sky|boss|R;horned_chimera|角獣の合成魔獣|闇|underworld|boss|R;axe_bull_beast|斧持ち牛獣|地|castle|late|F;h_serpent_haired|蛇髪の人型|毒|underworld|late|F;three_headed_hound|三頭の魔犬|火|underworld|late|F',
955:'triple_hydra|三首の大蛇|水|sea|boss|F;one_eye_ogre|一つ目の大鬼|地|cave|late|F;winged_sphinx|翼の人面獣|地|desert|boss|F;white_manytail_fox|白い多尾狐|無|forest|late|L;violet_unicorn|紫たてがみの一角獣|無|forest|late|L',
956:'h_sun_guard|日輪の人型|光|castle|boss|F;h_moon_robed|月衣の人型|氷|tower|boss|F;h_sea_god|海神の人型|水|sea|boss|F;h_red_guard|赤鎧の人型|火|castle|boss|F;h_harvest|実りの人型|地|forest|boss|F',
957:'h_reaper|鎌の人型|闇|underworld|boss|F;h_smith|鍛冶の人物|地|castle|late|F;h_white_spirit|白衣の精霊|風|sky|boss|F;h_tree_spirit|樹木の精霊|地|forest|boss|F;h_masked_spirit|狐面の人型|闇|tower|boss|F',
958:'h_dark_sun|暗い日輪の人型|闇|underworld|boss|F;h_dark_moon|暗い月の人型|闇|tower|boss|F;h_war_god|戦の人型|火|castle|boss|F;h_wood_god|森の人型|地|forest|boss|F;h_depth_god|深海の人型|水|sea|boss|F',
959:'gold_block_golem|金の角柱人形|地|castle|late|F;h_bishop|司祭の人物|光|castle|late|F;h_pale_spirit|白い人型精霊|光|sky|late|F;h_stone_sage|石の賢者像|地|tower|boss|F;h_jester|道化の人物|無|castle|late|F',
960:'gold_plume_bird|金羽の霊鳥|光|sky|late|R;scroll_dove|巻物の白鳥|風|sky|middle|R;storm_raven|雷羽の黒鳥|雷|sky|late|R;gold_guard_lion|金の守護獅子|地|castle|late|F;silver_guard_lion|銀の守護獅子|氷|tower|late|F',
}
REPLACEMENTS={
'slime':('green_droplet','序盤の緑色の粘体という役割を維持'),
'bat':('brown_cave_bat','洞窟の小型コウモリに一致'),
'bone_bat':(None,'骨格のコウモリ原画がないため旧画像を維持'),
'bone_wolf':('skeletal_wolf','骸骨の四足獣で蘇生・呪い系の外見に一致'),
'chimera_boss':('red_horn_dragon','炎の息と強打を使う溶岩の大荒獣。火竜の原画を採用'),
'crystal_slime':('crystal_droplet','氷結晶を持つ粘体で氷魔法型に一致'),
'ember_wisp':('flame_wisp','火の小精で炎魔法の役割に一致'),
'flame_slime':('blazing_droplet','炎に包まれた粘体で熔体の役割に一致'),
'gate_beast':('crowned_ogre','IMG_0929の大鬼。棘付き棍棒と大きな体格が最初の強打型ボスを示す'),
'ghost_bat':('violet_ghost_orb','幽霊のような翼玉を幽翼コウモリへ割当。氷の外見は弱い'),
'glacier_turtle':(None,'氷の甲羅を持つ亀の原画がないため旧画像を維持'),
'lava_turtle':('lava_rock_golem','熔殻の番兵の重装・炎魔法を熔岩の岩巨人で示す。外見は亀から岩巨人へ'),
'magma_wolf':('three_headed_hound','炉心の魔狼へ三頭の魔犬を採用。火の分類は配置提案で、原画自体に炎はない'),
'shadow_wolf':('gray_fang_wolf','暗い灰毛の四足獣が影毛の荒獣と牙の役割に合う'),
'shell_guard':('blue_horn_beetle','硬い甲殻の青い甲虫で防御型を示す'),
'stone_slime':('boulder_droplet','岩に覆われた粘体で防御交替型に一致'),
'storm_wolf':('storm_raven','雷の外見を優先し雷羽の黒鳥を採用。外見は狼から鳥へ'),
'underworld_boss':('horned_chimera','複数の獣の頭と蛇尾を持つ合成魔獣を冥界の大型敵へ'),
'wet_beast':('bristled_boar','牙と剛毛を持つイノシシが川辺の荒獣の強打を示す'),
'wind_wolf':('dark_winged_horse','疾風の荒獣へ黒翼の馬を採用。速さと飛翔を優先'),
'winged_beast':('eagle_griffin','鷲頭と大翼の獣が守門の翼獣の防御・強打型に合う'),
'zombie_wolf':(None,'腐敗した狼の原画がないため旧画像を維持'),
}

def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

def remove_background(im,threshold=24):
    a=np.array(im.convert('RGBA'));candidate=a[:,:,:3].max(axis=2)<=threshold
    if threshold>24:
        # 大鬼の原画だけは黒でなく暗い灰色背景。茶色の毛皮・緑の肌まで抜かない。
        candidate&=(a[:,:,:3].max(axis=2)-a[:,:,:3].min(axis=2))<=8
    h,w=candidate.shape;seen=np.zeros((h,w),bool);q=deque()
    for x,y in [(x,0) for x in range(w)]+[(x,h-1) for x in range(w)]+[(0,y) for y in range(h)]+[(w-1,y) for y in range(h)]:
        if candidate[y,x] and not seen[y,x]:seen[y,x]=True;q.append((x,y))
    while q:
        x,y=q.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=xx<w and 0<=yy<h and candidate[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((xx,yy))
    seen|=a[:,:,3]==0
    a[:,:,3]=np.where(seen,0,255);a[seen,:3]=0
    return Image.fromarray(a)

def split_parts(im,count,threshold=24):
    clean=remove_background(im,threshold);a=np.array(clean);h,w=a.shape[:2]
    labels=np.zeros((h,w),np.int32);parts=[]
    for y,x in np.argwhere(a[:,:,3]>0):
        if labels[y,x]:continue
        label=len(parts)+1;q=deque([(int(x),int(y))]);labels[y,x]=label;points=[]
        while q:
            xx,yy=q.popleft();points.append((xx,yy))
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                nx,ny=xx+dx,yy+dy
                if 0<=nx<w and 0<=ny<h and a[ny,nx,3] and not labels[ny,nx]:labels[ny,nx]=label;q.append((nx,ny))
        coords=np.array(points);parts.append(dict(label=label,area=len(points),center=coords.mean(axis=0)))
    main=sorted(sorted(parts,key=lambda p:-p['area'])[:count],key=lambda p:p['center'][0]);assert len(main)==count
    groups=[[p['label']] for p in main]
    for p in parts:
        if p in main:continue
        nearest=min(range(count),key=lambda i:np.sum((p['center']-main[i]['center'])**2))
        groups[nearest].append(p['label'])
    result=[]
    for group in groups:
        pixels=a.copy();pixels[~np.isin(labels,group)]=0;part=Image.fromarray(pixels);box=part.getchannel('A').getbbox();assert box
        result.append((part,box))
    return result

def convert(source,box,size,mirror):
    part=remove_background(source.crop(tuple(box)));bbox=part.getchannel('A').getbbox();assert bbox
    part=part.crop(bbox)
    if mirror:part=part.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    scale=min((size[0]-4)/part.width,(size[1]-4)/part.height)
    # 元のドットの境界を保つ最近傍。透過も先に確定し黒背景を縮小へ混ぜない。
    part=part.resize((max(1,round(part.width*scale)),max(1,round(part.height*scale))),Image.Resampling.NEAREST)
    a=np.array(part);opaque=a[:,:,3]>0;colors,counts=np.unique(a[:,:,:3][opaque],axis=0,return_counts=True)
    nearest=((colors.astype(np.int32)[:,None,:]-PAL[None,:,:])**2).sum(axis=2).argmin(axis=1)
    weights=np.bincount(nearest,weights=counts,minlength=len(PAL));selected=list(np.argsort(-weights,kind='stable')[:32]);palette=PAL[selected]
    values,inv=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
    nearest=((values.astype(np.int32)[:,None,:]-palette[None,:,:])**2).sum(axis=2).argmin(axis=1)
    a[:,:,:3]=palette[nearest[inv]].reshape(a.shape[:2]+(3,));a[~opaque]=0
    out=Image.new('RGBA',tuple(size));out.alpha_composite(Image.fromarray(a),((size[0]-a.shape[1])//2,size[1]-2-a.shape[0]))
    return out

def main():
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));entries={e['path']:e for e in registry['assets']}
    replacements={source:dest for dest,(source,_) in REPLACEMENTS.items() if source}
    imported=[];held=[]
    for number,text in SHEETS.items():
        file=f'IMG_{number:04}.PNG';source=Image.open(ORIGINAL/file).convert('RGBA');defs=[r.split('|') for r in text.split(';')];threshold=40 if number==929 else 24;parts=split_parts(source,len(defs),threshold)
        for index,(values,(part,box)) in enumerate(zip(defs,parts),1):
            id_,name,element,habitat,tier,facing=values
            row=dict(source_id=id_,original_file='assets/_incoming/owner-2026-09-26/'+file,original_sha256=sha((ORIGINAL/file).read_bytes()),slot=index,crop=list(box),name=name+'（仮）',element=element,habitat=habitat,tier=tier,original_facing=facing)
            if id_.startswith('h_'):
                row['reason']='人間または神・精霊の人型。役割未定のため登録しない';held.append(row);continue
            dest_id=replacements.get(id_,id_);rel=f'assets/monsters/{dest_id}/idle.png'
            large=tier=='boss';size=[192,160] if large else [96,96]
            if id_ in ('haunted_ship','crowned_ogre'):size=[192,160]
            picture=convert(part,box,size,facing=='L');path=ROOT/rel;path.parent.mkdir(parents=True,exist_ok=True);picture.save(path)
            row.update(id=dest_id,path=rel,size=size,mirror=facing=='L',output_sha256=sha(path.read_bytes()),black_threshold=threshold,resampling='nearest',max_colors=32,registered_status='required' if id_ in replacements else 'optional')
            entry=dict(path=rel,kind='monster_idle',size=size,max_colors=32,status=row['registered_status'],palette='assets/palette/natural.gpl',source='owner',license='LicenseRef-Owner-Provided',author='依頼者',provided_at='2026-09-26',original_file=row['original_file'],modified=f"原本の左から{index}体目。外周につながるRGB最大{threshold}以下の黒背景を除去、最近傍縮小、32色以内へ減色、二値透過。"+('左向きから右向きへ反転。' if facing=='L' else '正面または右向きを維持。'),conversion_record=RECORD+'#'+id_,facing='right' if facing in ('L','R') else 'front',monster_tier='boss' if large else 'normal')
            if 'droplet' in id_ or id_ in ('green_droplet','blue_water_blob','gold_block_golem'):entry['note']=NOTICE
            entries[rel]=entry;imported.append(row)
    for n in range(961,969):held.append(dict(original_file=f'assets/_incoming/owner-2026-09-26/IMG_{n:04}.PNG',slot='all',reason='若い4人またはその戦闘動作シート。役割未定のため登録しない'))
    registry['assets']=list(entries.values());(ROOT/'assets/registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    record={'baseline':BASE,'shared_conversation':'https://grok.com/share/c2hhcmQtMg_2d6106a4-1817-4b58-ba1c-28eb1121196f','imported':imported,'held_back':held,'replacements':{k:{'source_id':v[0],'reason':v[1]} for k,v in REPLACEMENTS.items()}}
    (ROOT/RECORD).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    docs=['# 依頼者原画の敵候補一覧','', '2026年9月26日。名前・属性・生息地・強さは配置提案であり、敵データは変更していない。人間と人型の神・精霊は保留。通常敵は96×96、ボスは192×160のキャンバス。','', '| id | 仮名 | 外見・原本 | 属性案 | 生息地案 | 強さ案 | 使用 |','| --- | --- | --- | --- | --- | --- | --- |']
    for r in imported:docs.append(f"| {r['id']} | {r['name']} | {r['source_id']} / {Path(r['original_file']).name} 左から{r['slot']} | {r['element']} | {r['habitat']} | {r['tier']} | {r['registered_status']} |")
    docs+=['','## 既存22種との対応','','| 既存id | 原画候補id | 選択理由 |','| --- | --- | --- |']+[f'| {id_} | {source or "旧画像維持"} | {reason} |' for id_,(source,reason) in REPLACEMENTS.items()]
    docs+=['','## 保留','','| 原画 | 範囲 | 理由 |','| --- | --- | --- |']+[f"| {Path(r['original_file']).name} | {r['slot']} | {r['reason']} |" for r in held]
    docs+=['','## 縮小後の確認','', '全体図と戦闘の静止配置で顔・輪郭を確認する。原画の細密な線や色差は32色化で減る。ボスと原画で大型に描かれたものは192×160に保ち、通常敵へ無理に縮めない。','',NOTICE]
    (ROOT/'docs/monster-catalog.md').write_text('\n'.join(docs)+'\n',encoding='utf8',newline='\n')
    print(f'OWNER_IMPORT_PASS: imported={len(imported)} replaced={len(replacements)} retained={22-len(replacements)} held_records={len(held)}')

if __name__=='__main__':main()
