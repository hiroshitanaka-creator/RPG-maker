"""承認された人物別魔物化アトラスを規約どおりの歩行・戦闘シートへ分割する。"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image,ImageDraw
from import_character_art import ROOT,quantize
from import_party_art import sheet

FORMS=['slime','beast','undead','bird','plant','shell','spirit','dragon']
SOURCE=ROOT/'assets/_incoming/monster_forms_20260919'
STAGE=ROOT/'.tools/monster-forms'


def frames_from_alpha(path: Path) -> list[Image.Image]:
    raw=Image.open(path).convert('RGBA')
    scale=min(1,720/raw.height)
    image=raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.NEAREST)
    width,height=image.size
    # 生成物の半透明の縁と背景光を二値化し、人物の不透明部分を分離する。
    mask=bytearray(image.getchannel('A').point(lambda a:255 if a>=220 else 0).tobytes())
    groups=[]
    for origin in range(len(mask)):
        if not mask[origin]:continue
        queue=deque([origin]);mask[origin]=0;group=[]
        while queue:
            index=queue.popleft();group.append(index);x,y=index%width,index//width
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=nx<width and 0<=ny<height and mask[ny*width+nx]:
                    mask[ny*width+nx]=0;queue.append(ny*width+nx)
        if len(group)>=4:groups.append(group)
    groups.sort(key=len,reverse=True)
    if len(groups)<15:raise ValueError(f'{path.name}: 独立した15コマを抽出できません ({len(groups)})')
    bodies=groups[:15]
    def bounds(group):
        xs=[n%width for n in group];ys=[n//width for n in group]
        return min(xs),min(ys),max(xs)+1,max(ys)+1
    boxes=[bounds(g) for g in bodies]
    centers=[((b[0]+b[2])/2,(b[1]+b[3])/2) for b in boxes]
    for g in groups[15:]:
        b=bounds(g);point=((b[0]+b[2])/2,(b[1]+b[3])/2)
        nearest=min(range(15),key=lambda i:(centers[i][0]-point[0])**2+(centers[i][1]-point[1])**2)
        # 本体近くの離れた指先・杖先は保持し、コマ間の背景の断片は採用しない。
        if abs(centers[nearest][0]-point[0])<width/6 and abs(centers[nearest][1]-point[1])<height/10 and b[3]<=boxes[nearest][3]:
            bodies[nearest].extend(g)
    order=sorted(range(15),key=lambda i:centers[i][1])
    ordered=[]
    for row in range(5):ordered.extend(sorted(order[row*3:row*3+3],key=lambda i:centers[i][0]))
    result=[]
    for i in ordered:
        alpha=bytearray(width*height)
        for index in bodies[i]:alpha[index]=255
        piece=image.copy();piece.putalpha(Image.frombytes('L',image.size,bytes(alpha)))
        box=piece.getbbox()
        if box is None or box[3]-box[1]<height/12 or box[2]-box[0]>width*.47:
            raise ValueError(f'{path.name}: コマの分離範囲が不正です {box}')
        result.append(piece.crop(box))
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    SOURCE.mkdir(parents=True,exist_ok=True);STAGE.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'docs/monster-form-generation.json').read_text(encoding='utf-8'))
    records=manifest['records']
    for record in records:
        if record['actor'] not in {f'pc_{i:02d}' for i in range(1,5)} or record['form'] not in FORMS:
            raise ValueError('未定義の人物・魔物職が生成台帳にあります。')
        target=SOURCE/(record['actor']+'_'+record['form']+'.png')
        origin=Path(record.get('path',target))
        if origin.exists() and origin.resolve()!=target.resolve():shutil.copy2(origin,target)
        if not target.is_file():raise FileNotFoundError(f'再加工には原画が必要です: {target}')
        if record.get('source_sha256') and hashlib.sha256(target.read_bytes()).hexdigest()!=record['source_sha256']:
            raise ValueError(f'原画のハッシュが一致しません: {target.name}')
    palette=[]
    for line in (ROOT/'assets/palette/base.gpl').read_text(encoding='utf-8').splitlines():
        parts=line.split()
        if len(parts)>=3 and all(x.isdigit() for x in parts[:3]):palette.append(tuple(map(int,parts[:3])))
    visuals=json.loads((ROOT/'data/character_visuals.json').read_text(encoding='utf-8'))
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    entries={r['path']:r for r in registry['assets']}
    outputs=[];missing=[]
    previews={f:Image.new('RGBA',(1280,540),'#26394b') for f in FORMS}
    for index in range(1,5):
        actor=f'pc_{index:02d}'
        for form in FORMS:
            source=SOURCE/(actor+'_'+form+'.png')
            extracted=frames_from_alpha(source) if source.exists() else None
            visual=visuals['actors'][actor]['forms'].setdefault(form,{})
            for kind in ['walk','battle']:
                if actor=='pc_01' and form=='undead' and kind=='battle':
                    visual[kind]='assets/characters/pc_01/battle_monster.png'
                    image=Image.open(ROOT/visual[kind]).convert('RGBA')
                else:
                    path=f'assets/characters/{actor}/forms/{form}/{kind}.png'
                    visual[kind]=path
                    frame=(32,48) if kind=='walk' else (48,48)
                    rows=4 if kind=='walk' else 1
                    entries[path]={'path':path,'kind':'character_walk' if kind=='walk' else 'character_battle_monster','size':[frame[0]*3,frame[1]*rows],'frame':list(frame),'grid':[3,rows],'max_colors':16,'status':'required' if extracted else 'placeholder','character_id':actor,'form_reference':form}
                    if extracted is None:
                        missing.append(path);continue
                    image=sheet(extracted[:12] if kind=='walk' else extracted[12:],frame,rows,True)
                    image=quantize(image,palette,16)
                    destination=ROOT/path if args.apply else STAGE/path
                    destination.parent.mkdir(parents=True,exist_ok=True);image.save(destination)
                    outputs.append({'path':path,'source':source.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()})
                x=(index-1)*320+10;y=30 if kind=='walk' else 425
                previews[form].alpha_composite(image.resize((image.width*2,image.height*2),Image.Resampling.NEAREST),(x,y))
                ImageDraw.Draw(previews[form]).text((x,8),actor+' '+form,fill='white')
    if args.apply:
        registry['assets']=list(entries.values())
        for path,value in [('assets/registry.json',registry),('data/character_visuals.json',visuals)]:
            (ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    for form,preview in previews.items():preview.convert('RGB').save(STAGE/(form+'_preview.png'))
    report={'applied':args.apply,'outputs':outputs,'missing':missing,'preserved_existing_battle':'assets/characters/pc_01/battle_monster.png'}
    (STAGE/'import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'applied':args.apply,'outputs':len(outputs),'missing':len(missing)},ensure_ascii=False))


if __name__=='__main__':main()
