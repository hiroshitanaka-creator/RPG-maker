#!/usr/bin/env python3
"""承認された生成画像を第1章の規定素材へ変換する。左右反転は行わない。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from import_character_art import ROOT, STAGE, character_frames, quantize

SOURCE = ROOT / "assets/_incoming/generated_20260919"
ENEMIES = {"slime": 32, "bat": 32, "shell_guard": 64,
           "ember_wisp": 32, "gate_beast": 64}


def opaque_colors(image: Image.Image) -> set[tuple[int, int, int]]:
    raw = image.convert("RGBA").tobytes()
    return {tuple(raw[i:i+3]) for i in range(0, len(raw), 4) if raw[i+3]}


def cutout(path: Path, threshold: int = 128) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getextrema()[0] != 0:
        raise ValueError(f"実アルファのない生成画像です: {path}")
    image.putalpha(alpha.point(lambda a: 255 if a >= threshold else 0))
    box = image.getbbox()
    if box is None:
        raise ValueError(f"不透明な本体がありません: {path}")
    if box[0] == 0 or box[1] == 0 or box[2] == image.width or box[3] == image.height:
        raise ValueError(f"本体が画像端に接触しています: {path}")
    return image.crop(box)


def fit_bottom(image: Image.Image, size: tuple[int, int], height: int | None = None) -> Image.Image:
    width, canvas_height = size
    factor = min((width-2)/image.width, (height or canvas_height-2)/image.height)
    scaled = image.resize((max(1, round(image.width*factor)), max(1, round(image.height*factor))), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", size)
    canvas.alpha_composite(scaled, ((width-scaled.width)//2, canvas_height-scaled.height))
    return canvas


def tiles(name: str) -> tuple[Image.Image, Image.Image]:
    source = Image.open(SOURCE / f"{name}.png").convert("RGBA")
    atlas = Image.new("RGBA", (512, 512))
    row = Image.new("RGBA", (512, 32))
    for index in range(16):
        x, y = index % 4, index // 4
        # 生成時の境界線を除外し、各セルを独立した32pxタイルにする。
        box = (round(x*source.width/4)+3, round(y*source.height/4)+3,
               round((x+1)*source.width/4)-3, round((y+1)*source.height/4)-3)
        tile = source.crop(box).resize((32, 32), Image.Resampling.NEAREST)
        tile.putalpha(255)
        row.paste(tile, (index*32, 0))
    # 使用タイルは先頭行の16種類。残る行にも同じ地形タイルを配置する。
    for y in range(16):
        atlas.paste(row, (0, y*32))
    return atlas, row


def palette_for(samples: list[Image.Image]) -> list[tuple[int, int, int]]:
    # 既存の顔画像52色を保持し、未使用の12色だけを新素材から選ぶ。
    keep = sorted(set().union(*(opaque_colors(Image.open(p)) for p in sorted((ROOT / "assets/characters").glob("*/portrait.png")))))
    room = 64-len(keep)
    if room <= 0:
        raise ValueError("既存素材の色を保持したまま新しい色を登録できません。")
    candidates = []
    for image in samples:
        for color in sorted(opaque_colors(image)):
            if max(color)-min(color) > 45 and min(sum((a-b)**2 for a,b in zip(color, old)) for old in keep) > 1800:
                candidates.append(color)
    if not candidates:
        return keep
    strip = Image.new("RGB", (len(candidates), 1))
    strip.putdata(candidates)
    result = strip.quantize(colors=room, method=Image.Quantize.MEDIANCUT)
    raw = result.getpalette()
    additions = [tuple(raw[i:i+3]) for i in range(0, room*3, 3)]
    return keep + additions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="目視後に規定位置と台帳へ反映する")
    args = parser.parse_args()
    STAGE.mkdir(parents=True, exist_ok=True)
    frames = character_frames()
    replacement = cutout(SOURCE / "pc01_left_step_b.png")
    # 既存左向きSTEP Aと同じ45pxの身長。残る11コマの切り出しは変更しない。
    target_height = frames[1][1].getbbox()[3]-frames[1][1].getbbox()[1]
    frames[1][2] = fit_bottom(replacement, (32, 48), target_height)
    walk = Image.new("RGBA", (96, 192))
    for y, row in enumerate(frames):
        for x, frame in enumerate(row):
            walk.alpha_composite(frame, (x*32, y*48))
    prepared = [("assets/characters/pc_01/walk.png", walk, 16, "character_walk")]
    samples = [walk]
    for name in ("field_outdoor", "dungeon_cave"):
        atlas, row = tiles(name)
        prepared.append((f"assets/tiles/{name}.png", atlas, 64, "tileset"))
        samples.append(row)
    for name, size in ENEMIES.items():
        sprite = fit_bottom(cutout(SOURCE / f"{name}.png", 230 if name == "shell_guard" else 128), (size, size))
        prepared.append((f"assets/monsters/{name}/idle.png", sprite, 16, "monster_idle"))
        samples.append(sprite)
    palette = palette_for(samples)
    results = [(path, quantize(image, palette, limit), limit, kind) for path,image,limit,kind in prepared]
    for path, image, _, _ in results:
        destination = STAGE / "chapter1" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination)
    preview = Image.new("RGBA", (960, 900), "#344452")
    draw = ImageDraw.Draw(preview)
    sheet = results[0][1]
    for y in range(4):
        draw.text((8, 8+y*160), ["DOWN", "LEFT", "RIGHT", "UP"][y], fill="white")
        for x in range(3):
            frame = sheet.crop((x*32,y*48,(x+1)*32,(y+1)*48)).resize((96,144),Image.Resampling.NEAREST)
            preview.alpha_composite(frame, (75+x*112, y*160))
    for i, (path, sprite, _, kind) in enumerate(results[3:]):
        name = Path(path).parent.name
        draw.text((470+(i%2)*225, 12+(i//2)*190), name, fill="white")
        factor = 2 if sprite.width == 64 else 4
        preview.alpha_composite(sprite.resize((sprite.width*factor,sprite.height*factor),Image.Resampling.NEAREST), (490+(i%2)*225, 35+(i//2)*190))
    for i, (_, atlas, _, _) in enumerate(results[1:3]):
        preview.alpha_composite(atlas.crop((0,0,512,32)).resize((896,56),Image.Resampling.NEAREST), (25,680+i*85))
    preview.convert("RGB").save(STAGE / "chapter1-preview.png")
    if args.apply:
        registry_path = ROOT / "assets/registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        entries = {entry["path"]: entry for entry in registry["assets"]}
        for path, image, limit, kind in results:
            destination = ROOT / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            image.save(destination)
            entry = entries.get(path, {"path": path, "kind": kind})
            entry.update(size=list(image.size), max_colors=limit, status="required")
            entries[path] = entry
        registry["assets"] = list(entries.values())
        registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
        (ROOT / "assets/palette/base.gpl").write_text("GIMP Palette\nName: RPG-maker\nColumns: 8\n#\n"+"".join(f"{r:3d} {g:3d} {b:3d}\t#{r:02X}{g:02X}{b:02X}\n" for r,g,b in palette),encoding="utf-8",newline="\n")
    report = {"applied": args.apply, "palette_colors": len(palette),
              "sources": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.glob("*.png")) if "candidate" not in p.name},
              "outputs": {path: {"colors": len(opaque_colors(image)), "size": list(image.size)} for path,image,_,_ in results}}
    (STAGE / "chapter1-import.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(report,ensure_ascii=False))


if __name__ == "__main__":
    main()
