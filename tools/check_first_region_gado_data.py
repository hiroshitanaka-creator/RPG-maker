"""導入の原稿・実経路・生成再現性を検査する。保護テストは変更しない。"""
from collections import deque
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = "f6434d5d188449c24dcba935bf1ae92d80080d27"

def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf8"))

BASE_HASHES = {'world/first_region.json': 'fd19f0bcc1b33e06dcd3aeed419402b2e08c869d7e43ac6d37bc49174e003912', 'world/interiors.json': '830eec417c191ca9f4bd8c04b9ce40b4d71ae50813e804d44320f43de796c4df', 'world/terrain.json': '2441bddb27f1a16fe6ef9fe7ea1ec36887b7ee84263564ec69d59d41a9324ff6', 'world/first_region_visuals.json': '881d397f3f962b3ecb2c01449cc54b686a1bcb404d06d9b16a88bc99dc332d8c', 'assets/registry.json': '5d5c888285543b42554a3c819f442aa9a0fed88c73c2ee19eab6011bd5280ea9', 'assets/palette/natural.gpl': '1b1c00dd929b96b64703972a0ae9368c36636b96c8f717dded78524e57913088', 'data/story_v1.json': 'bf6637ea59c236ea59f5cab5b909d64b1e2a7f44546a047c1ab2e2e5af95d5dd', 'docs/story-outline.md': '13e9366c89c5a2cd759406f54f88daca4c188ce06504c532a005e7a9a052650c'}

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf8")).hexdigest()

def reachable(room, start, blocked):
    found={tuple(start)}
    queue=deque(found)
    while queue:
        x,y=queue.popleft()
        for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            point=(x+dx,y+dy)
            if point in found or point in blocked:continue
            if 0<=point[1]<len(room["layout"]) and 0<=point[0]<len(room["layout"][point[1]]) and room["layout"][point[1]][point[0]]==".":
                found.add(point)
                queue.append(point)
    return found

def main():
    from check_gado_media import main as check_media
    assert check_media()==0
    document=read("data/first_region_gado_scenes.json")
    scenes={entry["id"]:entry for entry in document["scenes"]}
    assert len(scenes)==len(document["scenes"])==5
    speakers={"カイナ","リオネ","ハルド","ガド","状況"}
    for entry in scenes.values():
        assert entry["party"]==(["pc_01"] if entry["id"]=="workshop" else ["pc_01","pc_02","pc_03"])
        assert entry["flag"] in {"gado_workshop_seen","gado_encounter_seen","gado_promise_seen"}
        assert entry["lines"] and all(line["speaker"] in speakers and line["text"] and len(line["text"])<=80 and line["action"] in {"","leave_tool","tend_wound"} for line in entry["lines"])
    assert scenes["workshop"]["title"].startswith("以前、")
    text="\n".join(line["text"] for entry in scenes.values() for line in entry["lines"])
    for rejected in ["人間の仕事へ戻れない","村は川向こう","死んだことにしてくれ","新しい洪水"]:assert rejected not in text
    for adopted in ["もう駄目かと","勝手に終わらせるな。まだ直せる。","道具より先に休め。お前の腕までは直してやれん。","そこ踏むな。まだ直せる","お前には見られたくなかった","この手は戻らんぞ","今は傷のことを聞いています","道があっても、戻れない夜がある","見つからなくても来てくれ","工具は置いてこい。毎回修理じゃかなわん。"]:assert adopted in text
    registry=read("assets/registry.json")
    registered={entry["path"] for group in ["assets","audio"] for entry in registry[group]}
    pending=[]
    for slot,path in document["art"].items():
        if path is None:pending.append(slot)
        else:assert path in registered and (ROOT/path).is_file(), slot
    source=read("world/first_region.json")
    runtime=read("world/interiors.json")
    for data in [source,runtime]:
        ids=[site["id"] for site in data["sites"]]
        assert len(ids)==len(set(ids))
        cave=next(site for site in data["sites"] if site["id"]=="first_cave")
        events=[event for room in cave["rooms"] for event in room["events"]]
        assert len({event["id"] for event in events})==len(events)
        assert sum(event["kind"]=="treasure" for event in events)==3
        assert sum(event["kind"]=="story" for event in events)==1
        assert next(event for event in events if event["kind"]=="story")==document["event"]
        floor=cave["rooms"][1]
        start=source["first_region"]["stairs_down"]["to"]["cell"]
        boss=tuple(source["first_region"]["boss"]["point"]["cell"])
        npc=tuple(document["event"]["cell"])
        found=reachable(floor,start,{boss,npc})
        assert any((npc[0]+dx,npc[1]+dy) in found for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)])
        assert any((boss[0]+dx,boss[1]+dy) in found for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)])
        assert tuple(source["first_region"]["stairs_up"]["from"]["cell"]) in found
        stripped=copy.deepcopy(data)
        next(site for site in stripped["sites"] if site["id"]=="first_cave")["rooms"][1]["events"]=[event for event in floor["events"] if event["id"]!=document["event"]["id"]]
        assert canonical_hash(stripped)==BASE_HASHES["world/first_region.json" if data is source else "world/interiors.json"]
    from first_region_story_data import apply as apply_story
    for duplicate in [False,True]:
        conflict=copy.deepcopy(source)
        conflict_events=next(site for site in conflict["sites"] if site["id"]=="first_cave")["rooms"][1]["events"]
        index=next(index for index,event in enumerate(conflict_events) if event["id"]==document["event"]["id"])
        if duplicate:conflict_events.append(copy.deepcopy(conflict_events[index]))
        else:conflict_events[index]["kind"]="treasure"
        snapshot=copy.deepcopy(conflict)
        try:apply_story(conflict)
        except ValueError:assert conflict==snapshot
        else:raise AssertionError("イベントID競合を拒否しない")
    baseline_registry=copy.deepcopy(registry)
    new_paths={"assets/characters/gado/human_standing_front.png","assets/characters/gado/shell_standing_front.png","assets/objects/gado_tool_broken.png","assets/objects/gado_tool_repaired.png"}
    assert len([entry for entry in registry["assets"] if entry["path"] in new_paths])==4
    baseline_registry["assets"]=[entry for entry in registry["assets"] if entry["path"] not in new_paths]
    assert len([entry for entry in registry["audio"] if entry["path"]=="assets/audio/se/gado_repair.wav"])==1
    baseline_registry["audio"]=[entry for entry in registry["audio"] if entry["path"]!="assets/audio/se/gado_repair.wav"]
    assert canonical_hash(baseline_registry)=="d78aa15fee0289d2ad8d5b068a8e1b48d0330918fb5f3afa285b6ad68c017f23", "既存台帳の変更"
    from import_gado_static_art import EXPECTED, INPUT
    from PIL import Image
    for form,(size,digest) in EXPECTED.items():
        original=(ROOT/INPUT/f"gado-{form}-event-standing-candidate.png").read_bytes()
        assert len(original)==size and hashlib.sha256(original).hexdigest()==digest
        target=ROOT/f"assets/characters/gado/{form}_standing_front.png"
        assert Image.open(ROOT/INPUT/f"gado-{form}-event-standing-candidate.png").convert("RGBA").tobytes()==Image.open(target).convert("RGBA").tobytes()
    retained=["world/terrain.json","world/first_region_visuals.json","assets/palette/natural.gpl","data/story_v1.json","docs/story-outline.md"]
    for name in retained:assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==BASE_HASHES[name], name
    stable=["world/first_region.json","world/interiors.json","assets/registry.json",*retained]
    before={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in stable}
    for iteration in range(2):
        for command in ["tools/build_first_region.py","tools/build_first_region_presentation.py"]:
            subprocess.run([sys.executable,command],cwd=ROOT,check=True)
        after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in stable}
        assert after==before, (iteration,"生成後の差分")
    report={"status":"PASS","scene_variants":len(scenes),"npc_events":1,"chests":3,"generator_runs":2,"retained_files":retained,"pending_art":pending,"scope":"原稿・経路・局所生成の検査。実素材と実画面の完成判定は含まない。"}
    destination=ROOT/"docs/verification/first-region-intro/data-checks.json"
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(f"INTRO_DATA_PASS: variants={len(scenes)} pending_art={len(pending)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
