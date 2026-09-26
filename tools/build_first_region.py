"""最初の地方の手作業配置を既存データへ局所適用する。全地形は再生成しない。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def definition():
    return json.loads((ROOT / "world/first_region.json").read_text(encoding="utf-8"))


def patch_terrain(terrain):
    for patch in definition()["terrain_patch"]:
        x, y = patch["cell"]
        row = terrain["rows"][y]
        terrain["rows"][y] = row[:x] + patch["tile"] + row[x + 1:]


def patch_interiors(interiors):
    source = definition()
    ids = {site["id"] for site in source["sites"]}
    interiors["sites"] = [site for site in interiors["sites"] if site["id"] not in ids] + source["sites"]
    interiors["first_region"] = source["first_region"]


if __name__ == "__main__":
    for name, apply in [("terrain", patch_terrain), ("interiors", patch_interiors)]:
        path = ROOT / f"world/{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        apply(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("FIRST_REGION_DATA: 既存地形への局所配置と内部2拠点を反映")
