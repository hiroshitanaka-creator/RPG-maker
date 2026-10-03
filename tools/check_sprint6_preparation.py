#!/usr/bin/env python3
"""実装前準備の原本・計測値・座標候補を読み取り専用で照合する。"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BASE = "0674954be1b953abd241c3281a269fcb29463d7f"
RECORD = ROOT / "docs/verification/sprint6-preparation/originals.json"


def main() -> int:
    errors = []
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    if record.get("baseline_commit") != BASE or record.get("version") != 1:
        errors.append("基準コミット・記録形式が一致しない")
    files = record.get("files", [])
    if len(files) != 12 or len({item["path"] for item in files}) != 12:
        errors.append("原画12件が一意に記録されていない")
    registry = json.loads((ROOT / "assets/registry.json").read_text(encoding="utf-8"))
    shapes = 0
    for item in files:
        relative = item["path"]
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT / "assets/_incoming") or not path.is_file():
            errors.append(relative + ": 原本の場所が不正")
            continue
        raw = path.read_bytes()
        committed = subprocess.check_output(["git", "show", BASE + ":" + relative], cwd=ROOT)
        if raw != committed or hashlib.sha256(raw).hexdigest() != item["sha256"] or len(raw) != item["bytes"]:
            errors.append(relative + ": 原本バイト・SHA・バイト数が不一致")
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            rgba = image.convert("RGBA")
            alpha = rgba.getchannel("A").histogram()
            actual = dict(dimensions=list(image.size), mode=image.mode, alpha_nonbinary_pixels=sum(alpha[1:255]), colors=len(rgba.getcolors(1 << 24)))
            for key, value in actual.items():
                if item[key] != value:
                    errors.append(relative + ": " + key + "の計測値が不一致")
        references = [entry["path"] for entry in registry["assets"] if path.name in json.dumps(entry, ensure_ascii=False)]
        if references != item["registry_references"]:
            errors.append(relative + ": 台帳参照の記録が不一致")
        if not item.get("approval"):
            errors.append(relative + ": 承認と候補の区別がない")
        geometries = [candidate for key in ("entrances", "walk", "blocks", "overlays") for candidate in item[key]]
        if "crop_candidate" in item:
            geometries.append(dict(label="crop候補", bbox=item["crop_candidate"]))
        for geometry in geometries:
            shapes += 1
            valid = bool(geometry.get("label"))
            if "bbox" in geometry:
                x0, y0, x1, y1 = geometry["bbox"]
                valid = valid and all(type(v) is int for v in (x0, y0, x1, y1)) and 0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height
            else:
                points = geometry.get("points", [geometry.get("point")])
                valid = valid and bool(points) and all(isinstance(p, list) and len(p) == 2 and all(type(v) is int for v in p) and 0 <= p[0] < width and 0 <= p[1] < height for p in points)
            if not valid:
                errors.append(relative + ": 座標候補が原画の範囲外または形式不正")
    for relative in record["existing_paths"]:
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            errors.append(relative + ": 参照した既存ファイルがない")
    for message in errors:
        print("PREPARATION_FAIL: " + message, file=sys.stderr)
    print("PREPARATION_" + ("FAIL" if errors else "PASS") + ": originals=" + str(len(files)) + " candidates=" + str(shapes) + " errors=" + str(len(errors)))
    return int(bool(errors))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print("PREPARATION_FAIL: 記録を照合できない: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
