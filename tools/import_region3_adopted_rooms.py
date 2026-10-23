#!/usr/bin/env python3
"""073採用ZIPを照合し、採用済みPNGの原バイトだけを配置する。

既定は検査のみ。--applyで5枚をコピーする。台帳・出所の確定は別途必要。
画像の再保存、縮小、減色、生成は一切行わない。
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ZIP_BYTES = 851055
ZIP_SHA256 = "25cab1603a081415699b87722d6211ce0b56da6932c02034c0f3dbb988b4aabf"
PALETTE_SHA256 = "e0221fc6fd01e7adddaafc150f13302b903b24659323b0fe43bd51cfccf969f8"
# 親検収の固定commit d921bfff1339554eb4fe06930a9dc170ecaac98d に記録された値。
EXPECTED = {
    "inn": (184495, "52723c0560ca54cf9aff695d383a17235b8f224058dda7a2367304e79cb5e007"),
    "item-shop": (168249, "76bf5d755bf8b98d7125c800abf02fb27b2b5dda080ac43ff1f966a9c65469cb"),
    "weapon-shop": (167018, "be55b08fc7da5421f84c8c88001586e523369b9dfff8e950d83bd96500e6d93c"),
    "shrine": (166573, "46c00cbdc2ad0d02e1d05662793c15bb2117ea28cb9f0ceeab75f118ce8065c8"),
    "armor-shop": (165817, "eefd5131abf790c2a8e7ff5393054898f8bf126b722cca2982e634a4b21f4b31"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def inspect_archive(path: Path) -> tuple[dict[str, bytes], list[dict]]:
    require(path.stat().st_size == ZIP_BYTES, "採用ZIPのバイト数が不一致")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ZIP_SHA256, "採用ZIPのSHA-256が不一致")
    palette_raw = (ROOT / "assets/palette/natural.gpl").read_bytes()
    require(len(palette_raw) == 2020 and hashlib.sha256(palette_raw).hexdigest() == PALETTE_SHA256,
            "固定パレットのバイト数またはSHA-256が不一致")
    palette = set()
    for line in palette_raw.decode("utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 3 and all(p.isdecimal() for p in parts[:3]):
            palette.add(tuple(map(int, parts[:3])))
    require(len(palette) == 84, "固定パレットが84色ではない")
    by_sha = {sha: (role, size) for role, (size, sha) in EXPECTED.items()}
    payload, report = {}, []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(archive.testzip() is None, "ZIP内のCRC照合が失敗")
        pngs = [item for item in archive.infolist() if item.filename.lower().endswith(".png")]
        require(len(pngs) == 5, "採用ZIP内のPNG数が5ではない")
        for item in pngs:
            data = archive.read(item)
            sha = hashlib.sha256(data).hexdigest()
            require(sha in by_sha, "採用対象外のPNG: " + item.filename)
            role, size = by_sha[sha]
            require(role not in payload and len(data) == size, "PNGの重複またはバイト数不一致")
            require(data[:8] == b"\x89PNG\r\n\x1a\n" and data[24:26] == bytes((8, 6)),
                    "PNGがRGBA8ではない")
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                require(image.mode == "RGBA" and image.size == (448, 384), "PNGの寸法・形式不一致")
                require(image.getchannel("A").getextrema() == (255, 255), "アルファ255以外を検出")
                color_counts = image.convert("RGB").getcolors(maxcolors=64)
                require(color_counts is not None, "64色上限を超過")
                colors = {color for _, color in color_counts}
                require(len(colors) <= 64 and colors <= palette, "色数またはパレット所属が不一致")
            payload[role] = data
            report.append(dict(role=role, member=item.filename, bytes=len(data), sha256=sha,
                               size=[448, 384], colors=len(colors), alpha=[255]))
    require(set(payload) == set(EXPECTED), "採用対象5枚がそろっていない")
    return payload, sorted(report, key=lambda row: row["role"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Libraryから取得した採用ZIP")
    parser.add_argument("--apply", action="store_true", help="全件検査後に5枚の原バイトをコピー")
    args = parser.parse_args()
    try:
        payload, report = inspect_archive(args.archive)
        destinations = {role: ROOT / f"assets/interiors/region3_room_{role.replace('-', '_')}.png"
                        for role in EXPECTED}
        # 全件を先に照合する。異なる既存ファイルを上書きしない。
        for role, dest in destinations.items():
            require(not dest.is_symlink(), "配置先がシンボリックリンク: " + str(dest))
            require(not dest.exists() or dest.read_bytes() == payload[role],
                    "配置先に異なるバイトのファイルが存在: " + str(dest))
        if args.apply:
            for role, dest in destinations.items():
                if not dest.exists():
                    with dest.open("xb") as output:
                        output.write(payload[role])
                require(dest.read_bytes() == payload[role], "コピー後の原バイトが不一致")
        print(json.dumps(dict(status="COPIED" if args.apply else "VERIFIED", files=report,
                              registry_updated=False), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print("073取り込み拒否: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
