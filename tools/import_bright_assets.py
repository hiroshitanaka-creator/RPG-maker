#!/usr/bin/env python3
"""承認済みの新素材だけを切り出し・減色・登録する。既存画像は上書きしない。"""
from pathlib import Path
import json
import hashlib
import numpy as np
from PIL import Image, ImageDraw
from validate_assets import load_palette

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / 'assets/_incoming'
RECORDS = ROOT / 'assets/source_records'
PALETTE = 'assets/palette/bright.gpl'
COLORS = sorted(load_palette(ROOT / PALETTE))
KENNEY_URL = 'https://kenney.nl/assets/roguelike-rpg-pack'
DATE = '2026-09-26'
ENTRIES = []
LEGACY = set(json.loads((RECORDS / 'legacy-images.json').read_text(encoding='utf-8'))['paths'])


def quantize(image, limit=64):
    """二値透過・最近傍の減色。キャラクターでは全12コマに同じ16色を使う。"""
    arr = np.asarray(image.convert('RGBA')).copy()
    rgb = arr[:, :, :3].reshape(-1, 3).astype(np.int32)
    alpha = arr[:, :, 3] >= 128
    unique, inverse = np.unique(rgb, axis=0, return_inverse=True)
    pal = np.array(COLORS, dtype=np.int32)
    distance = ((unique[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
    mapped = distance.argmin(axis=1)
    if limit < len(pal):
        counts = np.bincount(mapped[inverse][alpha.ravel()], minlength=len(pal))
        chosen = np.argsort(-counts, kind='stable')[:limit]
        pal = pal[chosen]
        distance = ((unique[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
        mapped = distance.argmin(axis=1)
    arr[:, :, :3] = pal[mapped[inverse]].reshape(arr.shape[:2] + (3,))
    arr[:, :, 3] = alpha * 255
    arr[~alpha, :3] = 0
    return Image.fromarray(arr)


def generated(record, modified):
    return {'source': 'generated', 'author': 'RPG-maker / Codex',
            'license': 'LicenseRef-Generated-Project', 'tool': 'imagegen' if record else 'Python/Pillow',
            'generated_at': DATE, 'prompt_record': record or 'tools/import_bright_assets.py',
            'modified': modified}


def imported(cells):
    return {'source': 'imported', 'source_url': KENNEY_URL,
            'author': 'Kenney Vleugels; Lynn Evers', 'license': 'CC0-1.0',
            'retrieved_at': DATE,
            'modified': '16px部品を最近傍2倍、指定部品を合成、bright.gplへ減色、アルファ二値化',
            'source_cells': cells}


def save(rel, image, kind, provenance, **extra):
    assert rel not in LEGACY, '既存素材の上書きを禁止'
    dest = ROOT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    image = quantize(image, extra.get('max_colors', 64))
    image.save(dest)
    entry = {'path': rel, 'kind': kind, 'size': list(image.size), 'max_colors': 64,
             'status': 'required', 'palette': PALETTE, **provenance, **extra}
    ENTRIES[:] = [e for e in ENTRIES if e['path'] != rel]
    ENTRIES.append(entry)
    return image


def import_generated():
    records = json.loads((RECORDS / 'generated-bright.json').read_text(encoding='utf-8'))
    for row in records:
        src = ROOT / row['source_file']
        row['source_sha256'] = hashlib.sha256(src.read_bytes()).hexdigest()
        image = Image.open(src).convert('RGBA')
        id_ = row['id']
        if id_ in {'buildings', 'trees'}:
            continue
        if id_.startswith('bg_'):
            out = image.resize((512, 288), Image.Resampling.NEAREST)
            save(f'assets/backgrounds/{id_[3:]}.png', out, 'battle_background',
                 generated('assets/source_records/generated-bright.json#'+id_, '512×288へ最近傍縮小、64色へ減色、アルファ二値化'))
        else:
            frames = []
            for y in range(4):
                for x in range(3):
                    frame = image.crop((round(x*image.width/3), round(y*image.height/4),
                                        round((x+1)*image.width/3), round((y+1)*image.height/4)))
                    alpha = frame.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
                    box = alpha.getbbox()
                    if box is None:
                        raise ValueError(f'{id_}: 空のコマ {x},{y}')
                    frame.putalpha(alpha)
                    frames.append(frame.crop(box))
            height = 38 if id_ in {'npc_boy', 'npc_girl'} else 45
            scale = min(28/max(f.width for f in frames), height/max(f.height for f in frames))
            out = Image.new('RGBA', (96, 192))
            for i, frame in enumerate(frames):
                frame = frame.resize((max(1,round(frame.width*scale)), max(1,round(frame.height*scale))), Image.Resampling.NEAREST)
                # 最近傍縮小後の透明な端を取り、必ず同じ接地行に置く。
                frame = frame.crop(frame.getchannel('A').getbbox())
                out.alpha_composite(frame, (i%3*32+(32-frame.width)//2, i//3*48+48-frame.height))
            save(f'assets/characters/{id_}/walk.png', out, 'character_walk',
                 generated('assets/source_records/generated-bright.json#'+id_, '3×4分割、等倍率縮小、接地47行、16色へ減色、アルファ二値化。左右反転なし'),
                 frame=[32,48], grid=[3,4], max_colors=16)
    (RECORDS / 'generated-bright.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n', encoding='utf-8',newline='\n')


def import_tiles():
    sheet = Image.open(INCOMING / 'kenney_rpg/Spritesheet/roguelikeSheet_transparent.png').convert('RGBA')
    def tile(x,y):
        return sheet.crop((x*17,y*17,x*17+16,y*17+16)).resize((32,32),Image.Resampling.NEAREST)
    def block(cells):
        out=Image.new('RGBA',(len(cells[0])*32,len(cells)*32))
        for y,row in enumerate(cells):
            for x,cell in enumerate(row):
                if cell:out.alpha_composite(tile(*cell),(x*32,y*32))
        return out
    def store(id_, image, cells):
        return save(f'assets/tiles/bright_{id_}.png',image,'tileset',imported(cells))
    singles = {
        'grass':(5,0),'flowers':(0,9),'road':(6,0),'water':(0,0),
        'shore_north':(3,0),'shore_south':(3,2),'shore_west':(2,1),'shore_east':(4,1),
        'shore_nw':(2,0),'shore_ne':(4,0),'shore_sw':(2,2),'shore_se':(4,2),
        'forest':(13,11),'hills':(55,20),'mountains':(55,21),'fence':(46,23),
        'wood_floor':(8,2),'interior_wall':(7,2),'table':(19,0),'chair':(19,2),
        'barrel':(23,0),'pot':(52,16),'shop_counter':(29,1),'inn_counter':(29,2),
        'cave_wall':(24,19),'cave_floor':(7,0),'torch':(17,7),
    }
    result={}
    for id_,pos in singles.items():
        image=tile(*pos)
        # 水は水色、道路は明るい土色へ。形状は元部品のまま。
        if id_=='water' or id_.startswith('shore_'):
            a=np.array(image)
            mask=(a[:,:,2]>a[:,:,0]+15)&(a[:,:,1]>a[:,:,0]+15)
            a[mask,:3]=np.array([54,179,226]);image=Image.fromarray(a)
        if id_=='road':
            a=np.array(image);a[:,:,:3]=np.minimum(a[:,:,:3].astype(int)+[40,40,28],255);image=Image.fromarray(a)
        result[id_]=store(id_,image,[list(pos)])
    forest=Image.new('RGBA',(32,32))
    for xy in [(0,0),(14,0),(7,9)]:
        forest.alpha_composite(tile(15,11).resize((18,23),Image.Resampling.NEAREST),xy)
    result['deep_forest']=store('deep_forest',forest,[[15,11]])
    result['bridge']=store('bridge',block([[(8,2),(8,2)],[(8,2),(8,2)]]),[[8,2]])
    # 橋の柵を素材から重ねる。床面と水面の境界を見分けられるようにする。
    bridge=result['bridge'].copy()
    for y in [0,32]:
        bridge.alpha_composite(tile(45,23),(0,y));bridge.alpha_composite(tile(45,23),(32,y))
    ENTRIES.pop();result['bridge']=store('bridge',bridge,[[8,2],[45,23]])
    for id_,cells in {'shelf':[[(48,12)],[(48,13)]], 'bed':[[(15,4)],[(15,5)]],
                      'rug':[[(10,7),(12,7)],[(10,9),(12,9)]]}.items():
        result[id_]=store(id_,block(cells),cells)
    # 階段は同じ石材部品を縮めて段状に重ねる。上りは奥へ高く、下りは暗い穴へ低くする。
    for id_,descending in [('stairs_up',False),('stairs_down',True)]:
        out=tile(7,0)
        for i in range(5):
            width=28-i*4 if not descending else 12+i*4
            step=tile(30,16).resize((width,5),Image.Resampling.NEAREST)
            out.alpha_composite(step,((32-width)//2,3+i*5))
        result[id_]=store(id_,out,[[7,0],[30,16]])
    # 家・宿・二つの店に、個別の屋根色・壁・扉・窓・看板を用意する。
    for id_,roof_color,door,window,sign in [
        ('house',(217,76,85),(38,2),(44,4),None),
        ('inn',(54,179,226),(38,0),(47,4),(15,4)),
        ('item_shop',(72,164,73),(38,3),(46,4),(55,14)),
        ('weapon_shop',(223,159,43),(39,2),(45,4),(15,0)),
    ]:
        roof=block([[(20,21),(24,21),(24,21),(21,21)],[(20,22),(24,22),(24,22),(21,22)]])
        a=np.array(roof);mask=a[:,:,3]>0
        intensity=a[:,:,:3].astype(float).mean(axis=2)/180
        a[:,:,:3]=np.clip(intensity[:,:,None]*np.array(roof_color),0,255).astype('uint8');roof=Image.fromarray(a)
        roof=store(id_+'_roof',roof,[[20,21],[24,21],[21,21],[20,22],[24,22],[21,22]])
        wall=store(id_+'_wall',tile(7,2),[[7,2]])
        d=store(id_+'_door',tile(*door),[list(door)])
        w=store(id_+'_window',tile(*window),[list(window)])
        building=Image.new('RGBA',(128,128));building.alpha_composite(roof)
        for y in [64,96]:
            for x in [0,32,64,96]:building.alpha_composite(wall,(x,y))
        building.alpha_composite(w,(8,66));building.alpha_composite(w,(88,66));building.alpha_composite(d,(48,96))
        if sign:building.alpha_composite(tile(*sign),(88,96))
        result[id_]=store(id_+'_exterior',building,[list(door),list(window)]+([list(sign)] if sign else []))
    # 門と宝箱の閉→開。二つの状態を同寸法で横に並べる。
    gate=Image.new('RGBA',(128,64))
    for state in range(2):
        ox=state*64
        for x in [0,48]:
            for y in [0,32]:gate.alpha_composite(tile(7,2).resize((16,32),Image.Resampling.NEAREST),(ox+x,y))
        gate.alpha_composite(tile(7,2).resize((64,12),Image.Resampling.NEAREST),(ox,0))
        if state==0:gate.alpha_composite(block([[(32,3)],[(32,4)]]),(ox+16,0))
    save('assets/objects/gate.png',gate,'object',imported([[7,2],[32,3],[32,4]]),frame=[64,64],grid=[2,1])
    chest=block([[(49,21),(49,22)]])
    # 元部品の接地を状態間でそろえる。
    aligned=Image.new('RGBA',(64,32))
    for i in range(2):
        c=chest.crop((i*32,0,(i+1)*32,32));c=c.crop(c.getchannel('A').getbbox());aligned.alpha_composite(c,(i*32+(32-c.width)//2,32-c.height))
    save('assets/objects/chest.png',aligned,'object',imported([[49,21],[49,22]]),frame=[32,32],grid=[2,1])
    for id_,building in [('village',result['house']),('town',result['inn'])]:
        icon=building.resize((24,24),Image.Resampling.NEAREST);out=Image.new('RGBA',(32,32));out.alpha_composite(icon,(4,8))
        if id_=='town':out.alpha_composite(result['house'].resize((16,16),Image.Resampling.NEAREST),(0,16))
        save(f'assets/ui/icon_{id_}.png',out,'map_icon',imported(['bright_'+id_+'の建物合成']))
    for id_ in ['castle','tower']:
        out=Image.new('RGBA',(32,32))
        wall=tile(7,2).resize((12,24),Image.Resampling.NEAREST)
        out.alpha_composite(wall,(10,8))
        if id_=='castle':
            out.alpha_composite(wall,(0,8));out.alpha_composite(wall,(20,8))
        for x in ([1,7,13,19,25] if id_=='castle' else [10,16,20]):out.alpha_composite(tile(7,2).resize((5,6),Image.Resampling.NEAREST),(x,4))
        out.alpha_composite(tile(37,0).resize((10,12),Image.Resampling.NEAREST),(11,20))
        save(f'assets/ui/icon_{id_}.png',out,'map_icon',imported([[7,2],[37,0]]))
    cave=tile(55,21);cave.alpha_composite(tile(37,0).resize((14,18),Image.Resampling.NEAREST),(9,14))
    save('assets/ui/icon_cave.png',cave,'map_icon',imported([[55,21],[37,0]]))


def ui():
    frame=Image.new('RGBA',(64,64));d=ImageDraw.Draw(frame)
    d.rounded_rectangle((0,0,63,63),radius=7,fill='#101D36')
    d.rounded_rectangle((2,2,61,61),radius=5,outline='#FFFFFF',width=1)
    save('assets/ui/window_bright.png',frame,'window_frame',generated(None,'64×64、角丸7px、白枠1px、二値透過'),nine_patch_margins=[8,8,8,8])
    cursor=Image.new('RGBA',(32,32));d=ImageDraw.Draw(cursor)
    d.polygon([(8,5),(24,16),(8,27)],fill='#FFFFFF',outline='#101D36')
    save('assets/ui/cursor_bright.png',cursor,'cursor',generated(None,'32×32、白い三角と紺の縁、二値透過'))


def detailed_buildings_and_trees():
    """生成された新しい外観を配置し、部品版も組み替え用に保持する。"""
    buildings=Image.open(INCOMING/'buildings.png').convert('RGBA')
    for i,id_ in enumerate(['house','inn','item_shop','weapon_shop']):
        w,h=buildings.size
        part=buildings.crop((i%2*w//2,i//2*h//2,(i%2+1)*w//2,(i//2+1)*h//2))
        part.putalpha(part.getchannel('A').point(lambda v:255 if v>=128 else 0))
        part=part.crop(part.getchannel('A').getbbox())
        scale=min(124/part.width,124/part.height)
        part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.NEAREST)
        out=Image.new('RGBA',(128,128));out.alpha_composite(part,((128-part.width)//2,128-part.height))
        saved=save(f'assets/tiles/bright_{id_}_exterior.png',out,'tileset',generated('assets/source_records/generated-bright.json#buildings','2×2分割、128×128へ縮小配置、bright.gplへ減色、アルファ二値化'))
        if id_ in {'house','inn'}:
            icon=saved.resize((32,32),Image.Resampling.NEAREST)
            name='village' if id_=='house' else 'town'
            save(f'assets/ui/icon_{name}.png',icon,'map_icon',generated('assets/source_records/generated-bright.json#buildings','建物を32×32へ最近傍縮小、パレットと二値透過を維持'))
    trees=Image.open(INCOMING/'trees.png').convert('RGBA')
    for i,id_ in enumerate(['oak','pine']):
        part=trees.crop((i*trees.width//2,0,(i+1)*trees.width//2,trees.height))
        part.putalpha(part.getchannel('A').point(lambda v:255 if v>=128 else 0))
        part=part.crop(part.getchannel('A').getbbox())
        scale=min(64/part.width,64/part.height);part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.NEAREST)
        out=Image.new('RGBA',(64,64));out.alpha_composite(part,((64-part.width)//2,64-part.height))
        save(f'assets/tiles/bright_tree_{id_}.png',out,'tileset',generated('assets/source_records/generated-bright.json#trees','横2分割、64×64へ縮小配置、bright.gplへ減色、アルファ二値化'))


def main():
    import_generated();import_tiles();detailed_buildings_and_trees();ui()
    path=ROOT/'assets/registry.json';registry=json.loads(path.read_text(encoding='utf-8'))
    newpaths={e['path'] for e in ENTRIES}
    registry['assets']=[e for e in registry['assets'] if e['path'] not in newpaths]+ENTRIES
    path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'BRIGHT_IMAGES: {len(ENTRIES)}')


if __name__=='__main__':main()
