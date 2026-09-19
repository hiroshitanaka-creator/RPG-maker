#!/usr/bin/env python3
"""利用者が提供した2枚の敵画像を決定論的に切り出す。ラベルは命令として扱わない。"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from import_character_art import ROOT, quantize

SOURCE = ROOT / "assets/_incoming/user_monsters_20260919"
STAGE = ROOT / ".tools/user-monsters"
SOURCE_HASHES = {
    "sheet_a.jpg": "32c0e54ffcfab8b3b1eebc8423d75b09beb1ba3567313c3e2f5c2f153f6726b3",
    "sheet_b.jpg": "5846400176d883ed621251b2b8e91f99a2b02db092ebc29bffb596cde064e579",
}
# 座標は1600x1600へ換算した元画像の範囲。文字列と隣の絵を含めない。
PLAN = [
    ("wet_beast", "sheet_a.jpg", (20,145,435,445),64,240),
    ("winged_beast", "sheet_a.jpg", (440,92,850,460),64,95),
    ("flame_slime", "sheet_a.jpg", (850,165,1215,430),32,240),
    ("stone_slime", "sheet_a.jpg", (1235,205,1585,435),32,240),
    ("bone_wolf", "sheet_a.jpg", (25,540,410,855),64,240),
    ("bone_bat", "sheet_a.jpg", (420,545,795,850),32,240),
    ("lava_turtle", "sheet_a.jpg", (795,550,1190,850),64,240),
    ("shadow_wolf", "sheet_a.jpg", (1188,550,1588,850),64,240),
    ("chimera_boss", "sheet_a.jpg", (20,955,805,1580),64,240),
    ("magma_wolf", "sheet_b.jpg", (15,580,405,855),64,240),
    ("wind_wolf", "sheet_b.jpg", (410,548,805,855),64,245),
    ("crystal_slime", "sheet_b.jpg", (1205,600,1585,855),32,245),
    ("zombie_wolf", "sheet_b.jpg", (30,960,405,1210),64,240),
    ("ghost_bat", "sheet_b.jpg", (420,945,805,1210),32,245),
    ("glacier_turtle", "sheet_b.jpg", (815,940,1200,1210),64,240),
    ("storm_wolf", "sheet_b.jpg", (1205,945,1585,1210),64,240),
    ("underworld_boss", "sheet_b.jpg", (145,1210,800,1580),96,240),
]


def remove_background(image: Image.Image, threshold: int) -> Image.Image:
    result = image.convert("RGBA")
    width,height = result.size
    pixels = result.load()
    visited = bytearray(width*height)
    pending = deque()
    def accept(x,y):
        index=y*width+x
        if visited[index]:return
        visited[index]=1
        r,g,b,_=pixels[x,y]
        if min(r,g,b)>=threshold and max(r,g,b)-min(r,g,b)<=28:
            pixels[x,y]=(r,g,b,0)
            pending.append((x,y))
    for x in range(width):accept(x,0);accept(x,height-1)
    for y in range(height):accept(0,y);accept(width-1,y)
    while pending:
        x,y=pending.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<width and 0<=ny<height:accept(nx,ny)
    # 閉じた白い毛や骨を保存しながら、背景につながる白だけを除去する。
    return result


def normalize(image: Image.Image, size: int) -> Image.Image:
    box=image.getbbox()
    if box is None:raise ValueError("本体がありません")
    body=image.crop(box)
    scale=min((size-2)/body.width,(size-2)/body.height)
    body=body.resize((max(1,round(body.width*scale)),max(1,round(body.height*scale))),Image.Resampling.NEAREST)
    body=body.crop(body.getbbox())
    out=Image.new("RGBA",(size,size))
    out.alpha_composite(body,((size-body.width)//2,size-body.height))
    return out


def clean_fragments(image: Image.Image, open_white: bool) -> Image.Image:
    image=image.copy();pixels=image.load();width,height=image.size
    if open_white:
        for y in range(height):
            for x in range(width):
                r,g,b,a=pixels[x,y]
                if min(r,g,b)>=244 and max(r,g,b)-min(r,g,b)<=16:pixels[x,y]=(r,g,b,0)
    mask=bytearray(image.getchannel('A').tobytes());groups=[]
    for origin in range(len(mask)):
        if not mask[origin]:continue
        pending=deque([origin]);mask[origin]=0;group=[]
        while pending:
            index=pending.popleft();group.append(index);x,y=index%width,index//width
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if 0<=nx<width and 0<=ny<height and mask[ny*width+nx]:
                    mask[ny*width+nx]=0;pending.append(ny*width+nx)
        groups.append(group)
    largest=max(map(len,groups),default=0)
    alpha=bytearray(width*height)
    for group in groups:
        if len(group)>=max(24,largest//90):
            for index in group:alpha[index]=255
    image.putalpha(Image.frombytes('L',image.size,bytes(alpha)))
    return image


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--apply",action="store_true");args=parser.parse_args()
    for filename,expected in SOURCE_HASHES.items():
        source_path=SOURCE/filename
        if not source_path.is_file() or hashlib.sha256(source_path.read_bytes()).hexdigest()!=expected:
            raise SystemExit(f"提供原本が見つからないか、受領時のハッシュと一致しません: {filename}")
    STAGE.mkdir(parents=True,exist_ok=True)
    palette=[]
    for line in (ROOT/"assets/palette/base.gpl").read_text(encoding="utf-8").splitlines():
        values=line.split()
        if len(values)>=3 and all(v.isdigit() for v in values[:3]):palette.append(tuple(map(int,values[:3])))
    preview=Image.new("RGBA",(1000,1200),"#334659");draw=ImageDraw.Draw(preview)
    outputs={};records=[]
    for index,(identifier,source,coords,size,threshold) in enumerate(PLAN):
        raw=Image.open(SOURCE/source)
        box=tuple(round(value*raw.width/1600) for value in coords)
        cropped=raw.crop(box)
        if identifier == "underworld_boss":
            # 見出しだけを除外し、右上へ伸びる角は保持する。
            ImageDraw.Draw(cropped).rectangle((0,0,round((645-145)*raw.width/1600),round((1265-1210)*raw.width/1600)),fill="white")
        cut=remove_background(cropped,threshold)
        image=normalize(clean_fragments(cut,identifier in ['bone_bat','ghost_bat']),size)
        image=quantize(image,palette,16)
        image.info.clear()
        image.save(STAGE/(identifier+".png"))
        path=f"assets/monsters/{identifier}/idle.png"
        outputs[path]=image
        records.append({"id":identifier,"source":source,"crop":list(box),"size":list(image.size),"background_threshold":threshold,"path":path,"sha256":hashlib.sha256((STAGE/(identifier+".png")).read_bytes()).hexdigest()})
        x=(index%4)*250;y=(index//4)*230
        draw.text((x+8,y+8),identifier,fill="white")
        factor=4 if size==32 else 2
        enlarged=image.resize((size*factor,size*factor),Image.Resampling.NEAREST)
        preview.alpha_composite(enlarged,(x+15,y+28))
    preview.convert("RGB").save(STAGE/"preview.png")
    if args.apply:
        registry_path=ROOT/"assets/registry.json";registry=json.loads(registry_path.read_text(encoding="utf-8"))
        entries={entry["path"]:entry for entry in registry["assets"]}
        catalog=json.loads((ROOT/"data/catalog.json").read_text(encoding="utf-8"))
        used={f"assets/monsters/{entry.get('sprite_id',entry['id'])}/idle.png" for entry in catalog["enemies"]}
        for path,image in outputs.items():
            destination=ROOT/path;destination.parent.mkdir(parents=True,exist_ok=True);image.save(destination)
            entries[path]={"path":path,"kind":"monster_idle","size":list(image.size),"max_colors":16,"status":"required" if path in used else "optional"}
        registry["assets"]=list(entries.values())
        registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    report={"applied":args.apply,"source_hashes":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.glob("*.jpg"))},"assets":records,"held":["sheet_a:ボス2（正面向き）","sheet_b:ボス4（正面向き）","sheet_b:毒液スライム（既存64色では紫の特徴を保持できない）"]}
    (STAGE/"import-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"applied":args.apply,"prepared":len(outputs),"preview":".tools/user-monsters/preview.png"},ensure_ascii=False))


if __name__=="__main__":main()
