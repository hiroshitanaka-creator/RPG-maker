"""070の採用本文を厳密照合し、旧固定値の検査にだけ旧文のコピーを渡す。"""
import ast
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "first_castle"
ROOM = 9
EVENT = "castle_home_resident"
APPROVED = "森の塔へ進むには、王の許しが必要です。"
ORIGINAL = "城の北の門は、王の許しを得た人にだけ開かれます。"
MAPS = ("world/first_region.json", "world/interiors.json")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def target(data):
    sites = [site for site in data["sites"] if site["id"] == SITE]
    require(len(sites) == 1, "対象サイトが一意でない")
    rooms = sites[0]["rooms"]
    require(len(rooms) > ROOM and rooms[ROOM]["title"] == "城下町の民家", "対象部屋が異なる")
    matches = [(site, index, event) for site in data["sites"]
               for index, room in enumerate(site["rooms"]) for event in room["events"]
               if event["id"] == EVENT]
    require(len(matches) == 1, "対象イベントが一意でない")
    site, index, event = matches[0]
    require(site is sites[0] and index == ROOM, "対象イベントの場所が異なる")
    require(event["kind"] == "npc" and event["sprite"] == "npc_woman"
            and event["cell"] == [11, 6] and event["label"] == "町の人", "対象イベントの属性が異なる")
    text = event["text"]
    require(type(text) is list and len(text) == 1 and type(text[0]) is str
            and text[0] == APPROVED, "採用本文の型・件数・文字列が異なる")
    return event


def verify_generator(source):
    tree = ast.parse(source)
    identifiers = [node for node in ast.walk(tree)
                   if isinstance(node, ast.Constant) and node.value == EVENT]
    require(len(identifiers) == 1, "生成元の対象IDが一意でない")
    nodes = [node for node in tree.body if isinstance(node, ast.Assign)
             and any(isinstance(name, ast.Name) and name.id == "NODE" for name in node.targets)]
    require(len(nodes) == 1 and ast.literal_eval(nodes[0].value) == SITE, "生成元のサイトが異なる")
    mains = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"]
    require(len(mains) == 1, "生成元のmainが一意でない")
    calls = [node for node in ast.walk(mains[0]) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "npc"
             and node.args and node.args[0] is identifiers[0]]
    require(len(calls) == 1, "生成元のnpc呼出しが異なる")
    call = calls[0]
    require(not call.keywords and len(call.args) == 5, "生成元の引数が異なる")
    # 070で変更しなかった生成元の旧座標も維持する。
    require([ast.literal_eval(arg) for arg in call.args]
            == [EVENT, [10, 7], "町の人", [APPROVED], "npc_woman"], "生成元の採用本文または属性が異なる")
    require(isinstance(call.args[3], ast.List), "生成元のtextがlistでない")
    groups = [node for node in mains[0].body if isinstance(node, ast.For)
              and isinstance(node.iter, ast.List) and any(call in tuple_node.elts
                  for tuple_node in node.iter.elts if isinstance(tuple_node, ast.Tuple))]
    require(len(groups) == 1, "生成元の部屋定義が異なる")
    entries = groups[0].iter.elts
    require(all(isinstance(entry, ast.Tuple) and len(entry.elts) == 3 for entry in entries), "生成元の部屋配列が異なる")
    require([ast.literal_eval(entry.elts[0]) for entry in entries]
            == ["inn", "item", "weapon", "armor", "shrine", "home", "library"], "生成元の部屋順が異なる")
    require(entries[5].elts[2] is call and ast.literal_eval(entries[5].elts[1]) == "城下町の民家", "生成元の対象部屋が異なる")


def legacy_copies(source, runtime, generator):
    """両JSONと生成元を検証してから、コピーの指定1要素だけを変える。"""
    target(source)
    target(runtime)
    verify_generator(generator)
    copies = [copy.deepcopy(source), copy.deepcopy(runtime)]
    for data in copies:
        target(data)["text"][0] = ORIGINAL
    return copies


def run_cases(source, runtime, generator, baseline_hashes, canonical_hash, intro_event):
    """期待値は既存の固定hashと明示リテラル。判定対象から期待値を生成しない。"""
    def evaluate(first, second, code):
        snapshot = copy.deepcopy([first, second])
        try:
            copies = legacy_copies(first, second, code)
            for name, data in zip(MAPS, copies):
                floor = next(site for site in data["sites"] if site["id"] == "first_cave")["rooms"][1]
                events = [event for event in floor["events"] if event["id"] == intro_event["id"]]
                require(events == [intro_event], "導入イベントの不一致")
                floor["events"] = [event for event in floor["events"] if event["id"] != intro_event["id"]]
                require(canonical_hash(data) == baseline_hashes[name], "旧固定hashとの不一致")
        finally:
            assert [first, second] == snapshot, "照合が入力を変更した"

    evaluate(source, runtime, generator)
    print("TASK070_SCOPE_CASE_PASS: approved")
    rejected = []

    def reject(name, first, second, code=generator):
        try:
            evaluate(first, second, code)
        except (ValueError, SyntaxError) as error:
            rejected.append(name)
            print(f"TASK070_SCOPE_CASE_PASS: reject={name} reason={error}")
        else:
            raise AssertionError(f"拒否すべき変更を許容した: {name}")

    mutations = {
        "old-text": ("text", [ORIGINAL]),
        "one-character": ("text", [APPROVED[:-1] + "！"]),
        "two-pages": ("text", [APPROVED, APPROVED]),
        "text-not-list": ("text", APPROVED),
        "page-not-string": ("text", [0]),
        "empty-text": ("text", []),
        "id": ("id", EVENT + "_changed"),
        "cell": ("cell", [10, 7]),
        "speaker": ("label", "変更された話者"),
        "kind": ("kind", "story"),
        "sprite": ("sprite", "npc_elder_woman"),
    }
    for side in range(2):
        for name, (key, value) in mutations.items():
            pair = copy.deepcopy([source, runtime])
            target(pair[side])[key] = value
            reject(f"json-{side}-{name}", *pair)
        for name in ["other-event", "deleted", "duplicate", "duplicate-other-room", "site", "room"]:
            pair = copy.deepcopy([source, runtime])
            data = pair[side]
            event = target(data)
            site = next(site for site in data["sites"] if site["id"] == SITE)
            events = site["rooms"][ROOM]["events"]
            if name == "other-event":
                site["rooms"][1]["events"][0]["text"][0] += "！"
            elif name == "deleted":
                events.remove(event)
            elif name == "duplicate":
                events.append(copy.deepcopy(event))
            elif name == "duplicate-other-room":
                site["rooms"][0]["events"].append(copy.deepcopy(event))
            elif name == "site":
                site["id"] = "changed_castle"
            elif name == "room":
                events.remove(event)
                site["rooms"][0]["events"].append(event)
            reject(f"json-{side}-{name}", *pair)
    pair = copy.deepcopy([source, runtime])
    for data in pair:
        target(data)["text"] = [ORIGINAL]
    reject("both-json-old", *pair)
    for name, old, new in [
        ("old-text", APPROVED, ORIGINAL),
        ("one-character", APPROVED, APPROVED[:-1] + "！"),
        ("two-pages", repr(APPROVED), repr(APPROVED) + "," + repr(APPROVED)),
        ("id", EVENT, EVENT + "_changed"),
        ("cell", "[10,7],'町の人'", "[11,6],'町の人'"),
        ("speaker", "'町の人'", "'変更された話者'"),
        ("site", "NODE='first_castle'", "NODE='changed_castle'"),
        ("room", "('home','城下町の民家'", "('other','城下町の民家'"),
    ]:
        require(old in generator, f"負例の置換元がない: {name}")
        reject("generator-" + name, source, runtime, generator.replace(old, new))
    reject("generator-duplicate", source, runtime, generator + "\nDUPLICATE=" + repr(EVENT) + "\n")
    print(f"TASK070_SCOPE_PASS: positive=1 negative={len(rejected)} input_unchanged=1")


def main():
    from check_first_region_gado_data import BASE_HASHES, canonical_hash, read
    run_cases(read(MAPS[0]), read(MAPS[1]), (ROOT / "tools/build_castle_town.py").read_text(encoding="utf8"),
              BASE_HASHES, canonical_hash, read("data/first_region_gado_scenes.json")["event"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
