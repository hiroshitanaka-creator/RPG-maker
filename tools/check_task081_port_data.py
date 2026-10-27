#!/usr/bin/env python3
"""081の厳密な素材出所追加・原画保全・5室対応を独立検証する。"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import types
from unittest import mock

import numpy as np
from PIL import Image
import validate_assets

ROOT = Path(__file__).resolve().parents[1]
BASE = "3f8a9ba40c0a3a7aa0906c116cb07dd399e2766c"
ORIGINAL = "assets/_incoming/owner-2026-10-04-grok-region3/region3-world-map-alt-b.png"
SHA = "30d812e28f8dad699359f489aec0f61e9924dc65dd3288a085f7d2046fa5b454"
BACKGROUND = "assets/town_backdrops/region3_port.png"
OUT = ROOT / "docs/verification/task-081-implementation"
EXPECTED = {"inn": [1, [18, 10], [18, 11]], "item_shop": [2, [6, 19], [6, 20]],
            "weapon_shop": [3, [13, 18], [13, 19]], "shrine": [4, [32, 13], [32, 14]],
            "armor_shop": [5, [23, 17], [23, 18]]}


def main():
    checks = []

    def check(ok, label, detail=None):
        checks.append(dict(ok=bool(ok), label=label, detail=detail))
        if not ok:
            print("TASK081_DATA_FAIL:", label, detail)

    def original(path):
        return subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)

    old = types.ModuleType("task081_old_validator")
    old.__file__ = str(ROOT / "tools/validate_assets.py")
    exec(compile(original("tools/validate_assets.py"), old.__file__, "exec"), old.__dict__)
    expected_whitelist = dict(old.OWNER_ADOPTED_ROOM_ORIGINALS, **{ORIGINAL: SHA})
    check(validate_assets.OWNER_ADOPTED_ROOM_ORIGINALS == expected_whitelist, "既存5原画を保ち1パス/SHAだけ追加")
    current = json.loads((ROOT / "assets/registry.json").read_text())
    baseline = json.loads(original("assets/registry.json"))
    entries = [item for item in current["assets"] if item["path"] == BACKGROUND]
    check(len(entries) == 1, "新背景は台帳1件だけ")
    entry = entries[0]
    without = copy.deepcopy(current)
    without["assets"] = [item for item in without["assets"] if item["path"] != BACKGROUND]
    check(without == baseline, "既存台帳の内容・順序を保持")
    for category in ["assets", "audio", "fonts"]:
        for item in baseline[category]:
            check(validate_assets.check_provenance(item) == old.check_provenance(item), "既存出所の判定不変", item["path"])
    check(not validate_assets.check_provenance(entry) and old.check_provenance(entry), "今回1件だけ適格化")
    for key in ["author", "provided_at", "original_file", "modified", "license"]:
        bad = dict(entry)
        bad.pop(key)
        check(bool(validate_assets.check_provenance(bad)), "必須metadata欠落を拒否", key)
    for key, value in [("author", "別作者"), ("license", "CC0-1.0"),
                       ("original_file", ORIGINAL.replace("/region3-world-map-alt-b", "//region3-world-map-alt-b")),
                       ("original_file", ORIGINAL.replace("/region3-world-map-alt-b", "/../owner-2026-10-04-grok-region3/region3-world-map-alt-b")),
                       ("original_file", ORIGINAL.replace("alt-b", "alt-c")),
                       ("original_file", ORIGINAL.replace("alt-b", "missing")),
                       ("original_file", "assets/_incoming/owner-2026-10-04-grok-region3-rooms/region3-room-harbor-office.png")]:
        bad = dict(entry, **{key: value})
        check(bool(validate_assets.check_provenance(bad)), "不正・別・未承認原画を拒否", [key, value])
    path = ROOT / ORIGINAL
    raw = path.read_bytes()
    check(len(raw) == 3807730 and hashlib.sha256(raw).hexdigest() == SHA, "指定原画のbytes/SHA一致")
    read_bytes, is_file = Path.read_bytes, Path.is_file
    for label, body in [("1byte改変", bytes([raw[0] ^ 1]) + raw[1:]),
                        ("別原画bytes", (ROOT / ORIGINAL.replace("alt-b", "alt-c")).read_bytes())]:
        def observed_read(candidate):
            return body if candidate == path else read_bytes(candidate)
        with mock.patch.object(Path, "read_bytes", autospec=True, side_effect=observed_read):
            check(bool(validate_assets.check_provenance(entry)), "原画の不正hash拒否", label)
    with mock.patch.object(Path, "is_file", autospec=True, side_effect=lambda candidate: False if candidate == path else is_file(candidate)):
        check(bool(validate_assets.check_provenance(entry)), "原画欠損を拒否")
    check(hashlib.sha256(path.read_bytes()).hexdigest() == SHA, "負例後も実原画不変")
    # 変換器と異なる整数座標計算で、全元画像領域の最近傍と固定色への距離を照合。
    image = np.asarray(Image.open(ROOT / BACKGROUND).convert("RGBA"))
    source = np.asarray(Image.open(path).convert("RGB"))
    ys = ((2 * np.arange(864) + 1) * 4) // 6
    xs = ((2 * np.arange(1284) + 1) * 4) // 6
    sampled = source[ys][:, xs].astype(np.int32)
    used = np.unique(image[:, :, :3].reshape(-1, 3), axis=0).astype(np.int32)
    check(image.shape == (864, 1312, 4) and np.all(image[:, :, 3] == 255) and len(used) <= 64, "寸法・不透明・64色")
    pal = []
    for line in (ROOT / "assets/palette/natural.gpl").read_text().splitlines():
        values = line.split()
        if len(values) >= 3 and all(value.isdigit() for value in values[:3]):
            pal.append(tuple(map(int, values[:3])))
    check(all(tuple(color) in pal for color in used), "既存naturalパレットのみ")
    nearest = np.concatenate([((chunk[:, None] - used[None]) ** 2).sum(2).min(1) for chunk in np.array_split(sampled.reshape(-1, 3), 32)])
    actual = image[:, 14:1298, :3].reshape(-1, 3).astype(np.int32)
    check(np.all(((sampled.reshape(-1, 3) - actual) ** 2).sum(1) == nearest), "全原画領域は3/4最近傍・最近色だけ")
    check(np.all(image[:, :14] == image[0, 14]) and np.all(image[:, 1298:] == image[0, 14]), "余白は元左上色だけ・元領域切断なし")
    foundation = json.loads(original("world/adopted_room_foundation.json"))
    data = json.loads((ROOT / "world/region3_port.json").read_text())
    check(len(data["site"]["rooms"]) == 6 and len(data["definition"]["region3_port_doors"]) == 10, "外観と5室だけ")
    for binding, adopted in zip(data["bindings"], foundation["rooms"]):
        index, door, back = EXPECTED[binding["id"]]
        check([binding["room"], binding["door"], binding["return_cell"]] == [index, door, back], "固定の扉別対応", binding["id"])
        check(data["site"]["rooms"][index]["layout"] == adopted["layout"], "採用床不変", binding["id"])
        check(data["maps"][f"region3_port:{index}"]["backdrop"]["path"] == adopted["path"], "採用画像の取り違えなし", binding["id"])
        check(data["maps"][f"region3_port:{index}"]["overlays"]["pieces"] == adopted["overlays"], "採用遮蔽不変", binding["id"])
        check((ROOT / adopted["path"]).read_bytes() == original(adopted["path"]), "採用PNGは全bytes不変", binding["id"])
    check(all(not room["events"] for room in data["site"]["rooms"]), "新人物・サービス・イベントなし")
    for file in ["world/terrain.json", "world/second_region_coast.json", "world/map_graph.json", "assets/palette/natural.gpl", "world/adopted_room_foundation.json", "docs/decision-log.md", "docs/tasks/README.md"]:
        check((ROOT / file).read_bytes() == original(file), "別地方・海域・原画基盤・親台帳不変", file)
    report = dict(checks=checks, failed=sum(not item["ok"] for item in checks))
    (OUT / "data-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("TASK081_DATA_RESULT: checks=%d failed=%d" % (len(checks), report["failed"]))
    return bool(report["failed"])


if __name__ == "__main__":
    raise SystemExit(main())
