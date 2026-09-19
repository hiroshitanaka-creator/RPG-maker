#!/usr/bin/env python3
"""提供シートの有効コマと承認された補完コマから人物素材を作る。"""
from __future__ import annotations

import argparse
from collections import deque
import json

from PIL import Image, ImageDraw

from import_character_art import ROOT, STAGE, quantize
from import_chapter1_art import SOURCE, cutout


def components(source: Image.Image, count: int) -> list[Image.Image]:
    image = source.convert("RGBA")
    # 大きな生成原画を同率で縮小してから、アルファの連結領域で分割する。
    factor = min(1.0, 384/image.height)
    image = image.resize((round(image.width*factor),round(image.height*factor)),Image.Resampling.NEAREST)
    image.putalpha(image.getchannel("A").point(lambda a: 255 if a>=128 else 0))
    width, height = image.size
    mask = bytearray(image.getchannel("A").tobytes())
    groups = []
    for origin in range(len(mask)):
        if mask[origin] == 0:
            continue
        pending = deque([origin]); mask[origin] = 0; group = []
        while pending:
            current = pending.popleft(); group.append(current)
            x,y = current%width,current//width
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=nx<width and 0<=ny<height:
                    index=ny*width+nx
                    if mask[index]:
                        mask[index]=0; pending.append(index)
        if len(group)>100:
            groups.append(group)
    groups.sort(key=len,reverse=True)
    if len(groups)<count:
        raise ValueError(f"独立した人物が足りません: {len(groups)} / {count}")
    result=[]
    for group in groups[:count]:
        alpha=bytearray(width*height)
        for index in group: alpha[index]=255
        character=image.copy();character.putalpha(Image.frombytes("L",image.size,bytes(alpha)))
        box=character.getbbox()
        result.append((box[0],character.crop(box)))
    return [image for _,image in sorted(result,key=lambda entry:entry[0])]


def original_crop(name: str, box: tuple[int,int,int,int]) -> Image.Image:
    image=Image.open(ROOT / "assets/_incoming/20260919" / name).crop(box).convert("RGBA")
    pixels=image.load()
    for y in range(image.height):
        for x in range(image.width):
            r,g,b,_=pixels[x,y]
            pixels[x,y]=(r,g,b,0 if g>100 and g>r*2 and g>b*1.8 else 255)
    return components(image,1)[0]


def normalize(frames: list[Image.Image], size: tuple[int,int], same_scale: bool) -> list[Image.Image]:
    width,height=size
    factors=[min((width-2)/im.width,(height-2)/im.height) for im in frames]
    factor=min(factors)
    common_height=min(height-2,*(int((width-2)*im.height/im.width) for im in frames))
    outputs=[]
    for index,image in enumerate(frames):
        scale=factor if same_scale else common_height/image.height
        resized=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.NEAREST)
        # 最近傍サンプリングで消えた外縁を除き、不透明な最下行を接地させる。
        resized=resized.crop(resized.getbbox())
        target=Image.new("RGBA",size)
        target.alpha_composite(resized,((width-resized.width)//2,height-resized.height))
        outputs.append(target)
    return outputs


def sheet(frames: list[Image.Image], size: tuple[int,int], rows: int, same_scale: bool) -> Image.Image:
    canvas=Image.new("RGBA",(size[0]*3,size[1]*rows))
    for i,image in enumerate(normalize(frames,size,same_scale)):
        canvas.alpha_composite(image,((i%3)*size[0],(i//3)*size[1]))
    return canvas


def walking() -> dict[str,Image.Image]:
    result={}
    frames=[]
    bounds=[0,432,767,1024]
    for col in (0,2,1,3):
        for row in range(3):
            frames.append(original_crop("photo_02.jpg",(col*256+2,bounds[row]+2,(col+1)*256-2,bounds[row+1]-2)))
    result["pc_02"]=sheet(frames,(32,48),4,False)
    repair=components(Image.open(SOURCE/"pc03_walk_repair.png"),3)
    coords=[(0,0),(2,0),(3,0),(0,2),None,None,(0,1),(2,1),(3,1),(0,3),(2,3),None]
    frames=[]; replacements={4:repair[0],5:repair[1],11:repair[2]}
    for i,coord in enumerate(coords):
        if coord is None: frames.append(replacements[i])
        else:
            x,y=coord
            frames.append(original_crop("photo_03.jpg",(x*256+3,y*256+3,(x+1)*256-3,(y+1)*256-3)))
    result["pc_03"]=sheet(frames,(32,48),4,False)
    repair=components(Image.open(SOURCE/"pc04_walk_repair.png"),2)
    coords=[(0,0),(1,0),(2,0),(0,1),(1,1),None,(2,1),(4,1),(5,1),(0,3),(1,3),None]
    frames=[]; replacements={5:repair[0],11:repair[1]}
    tops=[48,293,542,788];bottoms=[260,513,766,1023]
    for i,coord in enumerate(coords):
        if coord is None: frames.append(replacements[i])
        else:
            x,y=coord
            frames.append(original_crop("photo_01.jpg",(round(x*1024/6)+2,tops[y],round((x+1)*1024/6)-2,bottoms[y])))
    result["pc_04"]=sheet(frames,(32,48),4,False)
    return result


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--apply",action="store_true");args=parser.parse_args()
    palette=[]
    for line in (ROOT/"assets/palette/base.gpl").read_text(encoding="utf-8").splitlines():
        parts=line.split()
        if len(parts)>=3 and all(part.isdigit() for part in parts[:3]):palette.append(tuple(map(int,parts[:3])))
    results={f"assets/characters/{char_id}/walk.png":image for char_id,image in walking().items()}
    for i in range(1,5):
        frames=components(Image.open(SOURCE/f"pc{i:02d}_battle.png"),3)
        if i==3:
            replacement=cutout(SOURCE/"pc03_hurt_repair.png")
            height=frames[2].height
            frames[2]=replacement.resize((round(replacement.width*height/replacement.height),height),Image.Resampling.NEAREST)
        results[f"assets/characters/pc_{i:02d}/battle.png"]=sheet(frames,(48,48),1,True)
    frames=components(Image.open(SOURCE/"pc01_battle_monster.png"),3)
    results["assets/characters/pc_01/battle_monster.png"]=sheet(frames,(48,48),1,True)
    results={path:quantize(image,palette,16) for path,image in results.items()}
    preview=Image.new("RGBA",(1024,1000),"#344452");draw=ImageDraw.Draw(preview)
    for i,(path,image) in enumerate(results.items()):
        destination=STAGE/"party"/path;destination.parent.mkdir(parents=True,exist_ok=True);image.save(destination)
        if path.endswith("walk.png"):
            x=i*320;draw.text((x+10,5),path.split("/")[-2],fill="white")
            preview.alpha_composite(image.resize((288,576),Image.Resampling.NEAREST),(x+10,25))
        else:
            index=i-3;x=(index%2)*500;y=625+(index//2)*120
            draw.text((x+5,y),path.split("/")[-2]+" "+path.split("/")[-1],fill="white")
            preview.alpha_composite(image.resize((288,96),Image.Resampling.NEAREST),(x+10,y+20))
    preview.convert("RGB").save(STAGE/"party-preview.png")
    if args.apply:
        registry_path=ROOT/"assets/registry.json";registry=json.loads(registry_path.read_text(encoding="utf-8"))
        for path,image in results.items():
            destination=ROOT/path;destination.parent.mkdir(parents=True,exist_ok=True);image.save(destination)
            entry=next(entry for entry in registry["assets"] if entry["path"]==path)
            entry["status"]="required"
            if path.endswith("battle_monster.png"):entry["form_reference"]="undead"
        registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"applied":args.apply,"outputs":list(results)},ensure_ascii=False))


if __name__=="__main__":main()
