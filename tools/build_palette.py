#!/usr/bin/env python3
"""既存の PNG 素材から共通パレット (.gpl) を作る。

使い方:
    python tools/build_palette.py assets --max-colors 64 -o assets/palette/base.gpl

既に作られた素材の色を集めて減色し、GIMP パレット形式で書き出す。
Aseprite / Libresprite / GIMP からそのまま読める。
一度作ったら、以後の素材はこのパレットに合わせる。
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    raise SystemExit("Pillow が必要です: pip install pillow")


def collect_opaque_pixels(root: Path) -> list[tuple[int, int, int]]:
    pixels: list[tuple[int, int, int]] = []
    for path in sorted(root.rglob("*.png")):
        if "_incoming" in path.parts:
            continue
        raw = Image.open(path).convert("RGBA").tobytes()
        pixels.extend(
            (raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 4) if raw[i + 3] != 0
        )
    return pixels


def quantize(pixels: list[tuple[int, int, int]], max_colors: int) -> list[tuple[int, int, int]]:
    unique = sorted(set(pixels))
    if len(unique) <= max_colors:
        return unique
    src = Image.new("RGB", (len(pixels), 1))
    src.putdata(pixels)
    reduced = src.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    raw = reduced.getpalette()[: max_colors * 3]
    return sorted({(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)})


def write_gpl(colors: list[tuple[int, int, int]], out: Path, name: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["GIMP Palette", f"Name: {name}", "Columns: 8", "#"]
    for r, g, b in colors:
        lines.append(f"{r:3d} {g:3d} {b:3d}\t#{r:02X}{g:02X}{b:02X}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="PNG 素材から共通パレットを作る")
    parser.add_argument("source", type=Path, help="走査するディレクトリ（例: assets）")
    parser.add_argument("--max-colors", type=int, default=64, help="パレットの色数上限（既定 64）")
    parser.add_argument("-o", "--output", type=Path, default=Path("assets/palette/base.gpl"))
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"ディレクトリが無い: {args.source}")

    pixels = collect_opaque_pixels(args.source)
    if not pixels:
        raise SystemExit(f"{args.source} に不透明ピクセルを持つ PNG が見つからない")

    colors = quantize(pixels, args.max_colors)
    write_gpl(colors, args.output, args.output.stem)
    print(f"{len(colors)} 色を {args.output} に書き出した（元の色数 {len(set(pixels))}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
