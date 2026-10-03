"""場面の原稿から、既存の洞窟へ1件だけ局所適用する。"""
from pathlib import Path
import copy
import json

ROOT = Path(__file__).resolve().parent.parent

def definition():
    return json.loads((ROOT / "data/first_region_gado_scenes.json").read_text(encoding="utf8"))

def apply(definition_data):
    event = definition()["event"]
    cave = next(site for site in definition_data["sites"] if site["id"] == "first_cave")
    events = cave["rooms"][1]["events"]
    found = [index for index, item in enumerate(events) if item["id"] == event["id"]]
    if len(found) > 1:
        raise ValueError("導入人物のIDが重複しています")
    if found:
        if events[found[0]].get("kind") != event["kind"]:
            raise ValueError("導入人物のIDが既存の別種イベントと競合しています")
        events[found[0]] = copy.deepcopy(event)
    else:
        events.append(copy.deepcopy(event))
