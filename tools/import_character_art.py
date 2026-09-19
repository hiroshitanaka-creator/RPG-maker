#!/usr/bin/env python3
"""提供済み人物画像を決定論的に切り出す。新しいポーズは作らない。"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'assets/_incoming/20260919'
STAGE = ROOT / '.tools/art-stage'


def remove_green(image: Image.Image) -> Image.Image:
    result = image.convert('RGBA')
    pixels = result.load()
    for y in range(result.height):
        for x in range(result.width):
            r, g, b, _ = pixels[x, y]
            pixels[x, y] = (r, g, b, 0 if g > 60 and g > r * 1.28 and g > b * 1.25 else 255)
    seen = set()
    components = []
    for y in range(result.height):
        for x in range(result.width):
            if (x, y) in seen or pixels[x, y][3] == 0:
                continue
            queue = deque([(x, y)])
            seen.add((x, y))
            component = []
            while queue:
                px, py = queue.popleft()
                component.append((px, py))
                for nx, ny in ((px-1, py), (px+1, py), (px, py-1), (px, py+1)):
                    if 0 <= nx < result.width and 0 <= ny < result.height and (nx, ny) not in seen and pixels[nx, ny][3] > 0:
                        seen.add((nx, ny))
                        queue.append((nx, ny))
            components.append(component)
    if not components:
        raise ValueError('人物の不透明領域がありません。')
    largest = max(len(component) for component in components)
    for component in components:
        if len(component) < max(12, largest // 100):
            for x, y in component:
                r, g, b, _ = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)
    return result


def character_frames() -> list[list[Image.Image]]:
    source = Image.open(SOURCE / 'photo_04.jpg')
    xs = [0, 148, 296, 443, 591]
    tops, bottoms = [373, 561, 759], [539, 737, 934]
    crops = []
    for column in [0, 2, 1, 3]:
        direction = []
        for frame in range(3):
            crop = source.crop((xs[column]+2, tops[frame], xs[column+1]-2, bottoms[frame]))
            direction.append(remove_green(crop))
        crops.append(direction)
    boxes = [frame.getbbox() for row in crops for frame in row]
    max_height = max(box[3] - box[1] for box in boxes)
    half_width = max(max(frame.width / 2 - box[0], box[2] - frame.width / 2) for row in crops for frame in row for box in [frame.getbbox()])
    scale = min(46 / max_height, 15 / half_width)
    normalized = []
    for row in crops:
        frames = []
        for frame in row:
            box = frame.getbbox()
            cropped = frame.crop(box)
            resized = cropped.resize((max(1, round(cropped.width*scale)), max(1, round(cropped.height*scale))), Image.Resampling.NEAREST)
            target = Image.new('RGBA', (32, 48))
            x = round(16 + (box[0] - frame.width / 2) * scale)
            target.alpha_composite(resized, (x, 48-resized.height))
            frames.append(target)
        normalized.append(frames)
    return normalized


def prepare(include_walk: bool) -> list[tuple[str, Image.Image, int]]:
    STAGE.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE / 'photo_05.jpg').convert('RGB')
    half = source.width // 2
    prepared = []
    for i in range(4):
        x, y = (i % 2)*half, (i // 2)*half
        portrait = source.crop((x, y, x+half, y+half)).resize((64, 64), Image.Resampling.NEAREST).convert('RGBA')
        prepared.append((f'assets/characters/pc_{i+1:02d}/portrait.png', portrait, 16))
    if include_walk:
        walk = Image.new('RGBA', (96, 192))
        for row, frames in enumerate(character_frames()):
            for column, frame in enumerate(frames):
                walk.alpha_composite(frame, (column*32, row*48))
        prepared.append(('assets/characters/pc_01/walk.png', walk, 16))
    return prepared


def build_palette(images: list[Image.Image]) -> list[tuple[int, int, int]]:
    colors = []
    for image in images:
        raw = image.convert('RGBA').tobytes()
        colors.extend((raw[i], raw[i+1], raw[i+2]) for i in range(0, len(raw), 4) if raw[i+3])
    strip = Image.new('RGB', (len(colors), 1))
    strip.putdata(colors)
    quantized = strip.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    raw = quantized.getpalette()
    return [tuple(raw[index:index+3]) for index in range(0, 64*3, 3)]


def quantize(image: Image.Image, colors: list[tuple[int, int, int]], limit: int) -> Image.Image:
    palette = Image.new('P', (1, 1))
    padded = colors + [colors[0]] * (256-len(colors))
    palette.putpalette([channel for color in padded for channel in color])
    rgb = image.convert('RGB')
    initial = rgb.quantize(palette=palette, dither=Image.Dither.NONE)
    histogram = initial.histogram()
    chosen = sorted(range(len(colors)), key=lambda i: (-histogram[i], i))[:limit]
    subset = [colors[i] for i in chosen]
    reduced_palette = Image.new('P', (1, 1))
    reduced_palette.putpalette([c for rgb_color in subset + [subset[0]] * (256-len(subset)) for c in rgb_color])
    result = rgb.quantize(palette=reduced_palette, dither=Image.Dither.NONE).convert('RGBA')
    result.putalpha(image.getchannel('A').point(lambda alpha: 255 if alpha >= 128 else 0))
    result.info.clear()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--portraits-only', action='store_true')
    args = parser.parse_args()
    if args.apply and not args.portraits_only:
        raise SystemExit('元シートの左歩行Bは右向きです。顔画像は --portraits-only --apply、承認済み補完を含む歩行画像は tools/import_chapter1_art.py --apply を使用してください。')
    prepared = prepare(include_walk=not args.portraits_only)
    palette = build_palette([image for _, image, _ in prepared])
    results = [(path, quantize(image, palette, limit), limit) for path, image, limit in prepared]
    for path, image, _ in results:
        destination = STAGE / Path(path).name if path.endswith('/walk.png') else STAGE / (Path(path).parent.name + '_portrait.png')
        image.save(destination)
    preview = Image.new('RGB', (768, 170 if args.portraits_only else 800), '#27354a')
    draw = ImageDraw.Draw(preview)
    for i, (_, portrait, _) in enumerate(results[:4]):
        preview.paste(portrait.resize((128, 128), Image.Resampling.NEAREST), (i*192+32, 20))
    if not args.portraits_only:
        sheet = results[-1][1]
        for row in range(4):
            for column in range(3):
                frame = sheet.crop((column*32, row*48, (column+1)*32, (row+1)*48)).resize((96, 144), Image.Resampling.NEAREST)
                preview.paste(frame, (column*240+72, 175+row*153), frame)
            draw.text((5, 180+row*153), ['DOWN', 'LEFT', 'RIGHT', 'UP'][row], fill='white')
    preview.save(STAGE / 'character-preview.png')
    if args.apply:
        registry_path = ROOT / 'assets/registry.json'
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        entries = {entry['path']: entry for entry in registry['assets']}
        for path, image, limit in results:
            destination = ROOT / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            image.save(destination)
            entry = entries.get(path, {'path': path, 'kind': 'portrait', 'size': [64,64]})
            entry['max_colors'] = limit
            entry['status'] = 'required'
            entries[path] = entry
        registry['assets'] = list(entries.values())
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        palette_path = ROOT / 'assets/palette/base.gpl'
        palette_path.parent.mkdir(parents=True, exist_ok=True)
        palette_path.write_text('GIMP Palette\nName: RPG-maker\nColumns: 8\n#\n' + ''.join(f'{r:3d} {g:3d} {b:3d}\t#{r:02X}{g:02X}{b:02X}\n' for r,g,b in palette), encoding='utf-8')
    print(json.dumps({'preview': '.tools/art-stage/character-preview.png', 'applied': args.apply,
                      'sources': {name: hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in (('photo_05.jpg',) if args.portraits_only else ('photo_04.jpg','photo_05.jpg'))},
                      'outputs': [path for path,_,_ in results]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
