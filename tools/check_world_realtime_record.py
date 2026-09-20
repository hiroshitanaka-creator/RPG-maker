"""加速なしの移動実測が、現在の地形・移動処理・グラフに対応するか照合する。"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    record = json.loads((ROOT / "docs/verification/world-terrain-realtime.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "world/map_graph.json").read_text(encoding="utf-8"))
    terrain = json.loads((ROOT / "world/terrain.json").read_text(encoding="utf-8"))
    expected_paths = {"res://world/map_graph.json", "res://world/terrain.json", "res://scripts/world/world_movement.gd", "res://scripts/world/world_terrain.gd"}
    errors = []
    if record.get("status") != "PASS" or record.get("errors"):
        errors.append("全経路の実時間測定が成功していない")
    if record.get("time_source") != "monotonic_wall_clock_no_acceleration":
        errors.append("加速なしの実時間測定ではない")
    if set(record.get("hashes", {})) != expected_paths:
        errors.append("実測対象のハッシュ一覧が一致しない")
    for path in expected_paths:
        actual = hashlib.sha256((ROOT / path.removeprefix("res://")).read_bytes()).hexdigest()
        if record.get("hashes", {}).get(path) != actual:
            errors.append("実測後に入力が変わった: " + path)
    edges = {edge["id"]: edge for edge in graph["edges"]}
    nodes = {node["id"]: node for node in terrain["nodes"]}
    rows = record.get("routes", [])
    if len(rows) != len(edges) or {row.get("id") for row in rows} != set(edges):
        errors.append("実測した経路の欠落または重複")
    if record.get("edges_required") != len(edges) or record.get("edges_measured") != len(edges):
        errors.append("実測件数が現在のグラフと一致しない")
    for row in rows:
        edge = edges.get(row.get("id"))
        if edge is None:
            continue
        seconds = row.get("wall_seconds")
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or not math.isfinite(seconds):
            errors.append(edge["id"] + ": 実時間が数値でない")
            continue
        if row.get("expected_seconds") != edge["expected_travel_seconds"] or not edge["expected_travel_seconds"] * .5 <= seconds <= edge["expected_travel_seconds"] * 1.5:
            errors.append(edge["id"] + ": 実測移動秒数が想定の±50%を外れる")
        if row.get("arrival") != nodes[edge["to"]]["cell"]:
            errors.append(edge["id"] + ": 実測時の到着位置が一致しない")
    for error in errors:
        print("WORLD_REALTIME_RECORD_FAIL: " + error)
    if not errors:
        print(f"WORLD_REALTIME_RECORD_PASS: edges={len(rows)} hashes=4 errors=0")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
