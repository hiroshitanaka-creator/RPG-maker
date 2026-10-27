#!/usr/bin/env python3
"""081の実装前境界を記録する。成功は本編接続の成功を意味しない。"""
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image
import validate_assets

ROOT = Path(__file__).resolve().parents[1]
BASE = "4388bf78cc2fe1763640c5f18dec43fa48eee32f"
ORIGINAL = "assets/_incoming/owner-2026-10-04-grok-region3/region3-world-map-alt-b.png"
EXPECTED_SHA = "30d812e28f8dad699359f489aec0f61e9924dc65dd3288a085f7d2046fa5b454"
OUT = ROOT / "docs/verification/task-081"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = (ROOT / ORIGINAL).read_bytes()
    assert len(raw) == 3807730 and hashlib.sha256(raw).hexdigest() == EXPECTED_SHA
    entry = {
        "path": "assets/town_backdrops/region3_port.png",
        "source": "owner", "author": "依頼者",
        "license": "LicenseRef-Owner-Provided", "provided_at": "2026-10-04",
        "original_file": ORIGINAL,
        "modified": "全原画の最近傍縮小・固定パレット減色を想定。未生成・未登録。",
    }
    errors = validate_assets.check_provenance(entry)
    assert errors, "出所の阻害点が変わった場合は親へ再照合する"
    original_hashes = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "assets/_incoming").rglob("*")) if path.is_file()
    }
    rooms = json.loads((ROOT / "world/adopted_room_foundation.json").read_text())
    assert rooms["development_only"] is True and len(rooms["rooms"]) == 5
    graph = json.loads((ROOT / "world/map_graph.json").read_text())
    legacy = [node for node in graph["nodes"] if node["id"] == "mist_market"]
    report = {
        "status": "BLOCKED_BEFORE_IMPLEMENTATION",
        "base_sha": BASE,
        "observed_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "original": {"path": ORIGINAL, "bytes": len(raw), "sha256": EXPECTED_SHA,
                     "size": list(Image.open(ROOT / ORIGINAL).size)},
        "prospective_entry_only_not_registered": entry,
        "unchanged_validator_errors": errors,
        "validator_sha256": hashlib.sha256((ROOT / "tools/validate_assets.py").read_bytes()).hexdigest(),
        "legacy_graph_status": {key: graph[key] for key in ["status", "runtime_connected", "authority"]},
        "legacy_candidate_not_reassigned": legacy,
        "adopted_rooms": [{"id": room["id"], "node": room["node"], "path": room["path"],
                            "sha256": hashlib.sha256((ROOT / room["path"]).read_bytes()).hexdigest()}
                           for room in rooms["rooms"]],
        "pending": [
            {"action": "第3地方の港を新本編の航路へ接続", "target": "既存本番航路・港入口・上陸点",
             "reason": "第3地方の本番接続定義がなく、旧mist_marketは霧の湖盆の未承認案。別地方の流用をしない。", "state": "判断待ち・未実行"},
            {"action": "外観のゲーム用素材登録", "target": "tools/validate_assets.py のowner原画固定許可",
             "reason": "指定原画パスは既存のowner許可対象外。既存検査の変更は禁止されている。", "state": "範囲確認待ち・未実行"},
        ],
    }
    (OUT / "connection-boundary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (OUT / "original-hashes-before.json").write_text(json.dumps(original_hashes, ensure_ascii=False, indent=2) + "\n")
    print("TASK081_BOUNDARY_OBSERVED: original_hash_match=true provenance_blocked=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
