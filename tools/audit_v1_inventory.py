"""企画監査の数量・参照・証拠ハッシュを採取する。完成判定や仕様変更はしない。"""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from build_identity import identity, EXPECTED_ENGINE

ROOT = Path(__file__).resolve().parent.parent


def read(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect() -> dict:
    registry = read("assets/registry.json")["assets"]
    jobs = [read(path.relative_to(ROOT).as_posix()) for path in sorted((ROOT / "data/jobs").glob("*.json"))]
    catalog = read("data/catalog.json")
    story = read("data/story_v1.json")
    content = read("data/campaign_content_v1.json")
    visuals = read("data/character_visuals.json")["actors"]
    sections = [section for circuit in content["circuits"] for section in circuit["sections"]]
    steps = [step for circuit in content["circuits"] for step in circuit["steps"]]
    kinds = Counter(step["kind"] for step in steps)
    clues = []
    for clue in story["clues"]:
        identifier = clue["id"]
        clues.append({"id": identifier, "dependencies": clue["dependencies"],
                      "seed_events": [key for key, event in story["events"].items() if event["effects"].get(identifier) == 1],
                      "resolve_events": [key for key, event in story["events"].items() if event["effects"].get(identifier) == 2]})
    # 追加区画だけの指紋とは別に、実行に使う全コード・定義・画像を記録する。
    paths = {ROOT / "project.godot", ROOT / "assets/registry.json", ROOT / "assets/palette/base.gpl"}
    for directory, pattern in [("scripts", "*.gd"), ("scenes", "*.tscn"), ("data", "*.json")]:
        paths.update((ROOT / directory).rglob(pattern))
    paths.update(ROOT / entry["path"] for entry in registry)
    hashes = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths) if path.is_file()}
    fingerprint = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "kind": "inventory_only_not_acceptance",
        "observed_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "jobs": {"count": len(jobs), "types": dict(Counter(job["type"] for job in jobs)), "categories": dict(Counter(job["category"] for job in jobs))},
        "abilities": {"count": len(catalog["abilities"]), "kinds": dict(Counter(ability["kind"] for ability in catalog["abilities"]))},
        "enemies": {"count": len(catalog["enemies"]), "used_sprite_ids": sorted({enemy.get("sprite_id", enemy["id"]) for enemy in catalog["enemies"]})},
        "assets": {"count": len(registry), "by_kind": dict(Counter(entry["kind"] for entry in registry)), "by_status": dict(Counter(entry["status"] for entry in registry)), "missing": [entry["path"] for entry in registry if not (ROOT / entry["path"]).is_file()]},
        "actor_visuals": {key: {"walk": value["walk"], "battle": value["battle"], "forms": sorted(value.get("forms", {}))} for key, value in visuals.items()},
        "story": {"chapters": len(story["chapters"]), "clues": clues, "events": len(story["events"]), "reactions": {key: value["reaction"] for key, value in story["events"].items() if "reaction" in value}},
        "expansion": {"circuits": len(content["circuits"]), "sections": len(sections), "distinct_layouts": len({json.dumps(section["layout"]) for section in sections}), "steps": len(steps), "kinds": dict(kinds)},
        "exploration_sites": dict(Counter(site["kind"] for site in read("data/exploration_v1.json")["sites"])),
        "current_build_identity": identity(EXPECTED_ENGINE),
        "audit_runtime_fingerprint": fingerprint,
        "runtime_file_sha256": hashes,
        "human_playtest": "NOT_RUN",
        "note": "不足0や件数の一致を、体験の品質・60時間・元企画全項目の達成とは扱わない。"
    }


def main() -> None:
    result = collect()
    output = ROOT / "docs/verification/v1-audit-inventory-latest.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: value for key, value in result.items() if key not in {"runtime_file_sha256", "actor_visuals", "story"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
