"""Phase 2の合格済みグラフを保ち、広域の地形と拠点入口を生成する。"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIZE = 256
STEP_SECONDS = 0.15  # 既存の移動間隔を維持。想定秒数に合わせて速度を落とさない。
SEED = 20260920
REGIONS = {
    "riverlands": (8, 8, 119, 119),
    "brine_reaches": (136, 8, 247, 119),
    "mist_basin": (8, 136, 119, 247),
    "sky_ridge": (136, 136, 247, 247),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def positions(graph: dict) -> dict[str, tuple[int, int]]:
    rng = random.Random(SEED)
    bounds = {}
    neighbors = {n["id"]: [] for n in graph["nodes"]}
    for node in graph["nodes"]:
        x0, y0, x1, y1 = REGIONS[node["region"]]
        bounds[node["id"]] = (x0 + 5, y0 + 5, x1 - 5, y1 - 5)
    for edge in graph["edges"]:
        seconds = edge["expected_travel_seconds"]
        # ±50%の受入範囲の内側に余裕を取り、後の地形上の迂回を許す。
        limits = (math.ceil(seconds * 0.57 / STEP_SECONDS), math.floor(seconds * 1.30 / STEP_SECONDS))
        neighbors[edge["from"]].append((edge["to"], limits))
        neighbors[edge["to"]].append((edge["from"], limits))
    ids = list(bounds)
    best_cost = float("inf")
    best = None
    for restart in range(20):
        points = {id_: (rng.randint(b[0], b[2]), rng.randint(b[1], b[3])) for id_, b in bounds.items()}

        def cost(id_: str, point: tuple[int, int]) -> float:
            result = 0.0
            for other, (low, high) in neighbors[id_]:
                d = distance(point, points[other])
                result += max(0, low - d) ** 2 + max(0, d - high) ** 2
            for other in ids:
                if other != id_:
                    result += max(0, 7 - distance(point, points[other])) ** 2 * 4
            return result

        for iteration in range(150000):
            id_ = rng.choice(ids)
            old = points[id_]
            x0, y0, x1, y1 = bounds[id_]
            if rng.random() < 0.15:
                candidate = (rng.randint(x0, x1), rng.randint(y0, y1))
            else:
                candidate = (max(x0, min(x1, old[0] + rng.randint(-15, 15))),
                             max(y0, min(y1, old[1] + rng.randint(-15, 15))))
            delta = cost(id_, candidate) - cost(id_, old)
            temperature = max(0.02, 30 * (1 - iteration / 150000) ** 3)
            if delta <= 0 or rng.random() < math.exp(-delta / temperature):
                points[id_] = candidate
            if iteration % 1000 == 0:
                total = sum(cost(id_, points[id_]) for id_ in ids)
                if total < best_cost:
                    best_cost, best = total, points.copy()
                if total == 0:
                    return points
        print(f"配置探索 {restart + 1}: 制約違反コスト {best_cost}", flush=True)
    raise RuntimeError(f"配置制約が未達。秒数や速度は変更しない: {best_cost}, {best}")


def line(a: tuple[int, int], b: tuple[int, int], horizontal: bool) -> list[tuple[int, int]]:
    result = [a]
    x, y = a
    axes = [0, 1] if horizontal else [1, 0]
    for axis in axes:
        while (x if axis == 0 else y) != b[axis]:
            if axis == 0:
                x += 1 if b[0] > x else -1
            else:
                y += 1 if b[1] > y else -1
            result.append((x, y))
    return result


def inside_land(x: int, y: int) -> bool:
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in REGIONS.values())


def main() -> None:
    graph_path = ROOT / "world/map_graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    proof = json.loads((ROOT / "docs/verification/world-map-phase2.json").read_text(encoding="utf-8"))
    if proof["status"] != "PASS" or proof["errors"] or proof["warnings"] or proof["graph_sha256"] != digest(graph_path):
        raise RuntimeError("同じグラフのPhase 2合格記録が必要。地形生成を開始しない。")
    points = positions(graph)
    cells = [["~"] * SIZE for _ in range(SIZE)]
    for region_index, (x0, y0, x1, y1) in enumerate(REGIONS.values()):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                forest = math.sin(x / 9 + region_index) + math.cos(y / 11) + math.sin((x + y) / 17)
                ridge = abs((x - x0) - (y - y0) * 0.7 - 30) < 3 and 20 < y - y0 < 90
                cells[y][x] = "m" if ridge else "f" if forest > 0.4 else "g"
    # 船の接続を水路として掘る。陸内の橋は歩行と船の双方が通れる。
    docks = set()
    for i, edge in enumerate(graph["edges"]):
        if edge["required_transport"] != "ship":
            continue
        docks.update([edge["from"], edge["to"]])
        for step, (x, y) in enumerate(line(points[edge["from"]], points[edge["to"]], i % 2 == 0)):
            cells[y][x] = "b" if inside_land(x, y) and step % 10 == 0 else "~"
    # 徒歩の全edgeに連続した道を置く。海上に徒歩用の大陸間接続は作らない。
    for i, edge in enumerate(graph["edges"]):
        if edge["required_transport"] != "walk":
            continue
        for x, y in line(points[edge["from"]], points[edge["to"]], i % 2 == 0):
            if not inside_land(x, y):
                raise RuntimeError("徒歩経路が地方間の海へ出た: " + edge["id"])
            cells[y][x] = "b" if cells[y][x] in "~b" else "r"
    for x, y in points.values():
        cells[y][x] = "n"
    # 陸地の小さな分断にも橋を置き、使用拠点のない孤島を生成しない。
    # 敵や拠点を水増しせず、各地方の岸から陸内へ入れる接続を確保する。
    components = []
    seen = set()
    for y in range(SIZE):
        for x in range(SIZE):
            if (x, y) in seen or cells[y][x] == "~":
                continue
            component = set([(x, y)])
            queue = deque([(x, y)])
            seen.add((x, y))
            while queue:
                cx, cy = queue.popleft()
                for nx, ny in [(cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]:
                    if 0 <= nx < SIZE and 0 <= ny < SIZE and cells[ny][nx] != "~" and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        component.add((nx, ny))
                        queue.append((nx, ny))
            components.append(component)
    locations = set(points.values())
    for component in components:
        if component & locations:
            continue
        candidates = [(x, y) for x, y in component if inside_land(x, y)]
        for x, y in candidates:
            bridge = None
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                bx, by, nx, ny = x+dx, y+dy, x+2*dx, y+2*dy
                if 0 <= nx < SIZE and 0 <= ny < SIZE and inside_land(bx, by) and cells[by][bx] == "~" and cells[ny][nx] != "~" and (nx, ny) not in component:
                    bridge = (bx, by)
                    break
            if bridge:
                cells[bridge[1]][bridge[0]] = "b"
                break
    result = {
        "version": 1, "graph_sha256": digest(graph_path), "seed": SEED,
        "width": SIZE, "height": SIZE, "tile_size": 32,
        "step_seconds": {"walk": STEP_SECONDS, "ship": STEP_SECONDS, "flight": STEP_SECONDS},
        "legend": {"~": "海・水路", "g": "草地", "f": "森", "m": "山", "r": "道", "b": "橋・船の通過点", "n": "拠点入口"},
        "regions": [{"id": id_, "bounds": list(bounds)} for id_, bounds in REGIONS.items()],
        "nodes": [{"id": n["id"], "cell": list(points[n["id"]]), "dock": n["id"] in docks} for n in graph["nodes"]],
        "rows": ["".join(row) for row in cells],
        "generation_scope": "Phase 3の地形。到達・秒数・単調区間・未使用陸地の合格はPhase 4の別検査で判定。",
    }
    from build_first_region import patch_terrain
    patch_terrain(result)
    destination = ROOT / "world/terrain.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"WORLD_TERRAIN_GENERATED: width={SIZE} height={SIZE} tiles={SIZE*SIZE} regions=4 nodes={len(points)} edges={len(graph['edges'])}", flush=True)


if __name__ == "__main__":
    main()
