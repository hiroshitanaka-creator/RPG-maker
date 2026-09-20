"""v1の敵30種。名称・値・同系統の画像共有は調整案。"""


def make_enemies(stats):
    def enemy(identifier, name, family, values, skills, weaknesses, jp,
              profile="legacy", role="接近型", focus="random", heal_below=65):
        return {"id": identifier, "name": name, "sprite_id": family,
                "family": family, "role": role, "stats": stats(values),
                "abilities": skills, "weaknesses": weaknesses, "jp": jp,
                "tactics": {"profile": profile, "focus": focus,
                            "heal_below": heal_below, "guard_every": 2},
                "design_status": "v1調整案。同系統の既存画像を共有し、行動・能力・弱点で区別する。"}

    # 既存5種の数値・技は維持する。
    roster = [
        enemy("slime", "水路スライム", "slime", (60,0,10,6,0,5,5), [], ["fire"],10),
        enemy("bat", "洞窟コウモリ", "bat", (75,0,13,4,0,8,21), [], ["ice"],12),
        enemy("shell_guard", "硬殻の番兵", "shell_guard", (150,0,18,28,0,4,4), [], ["ice"],16),
        enemy("ember_wisp", "残り火の精", "ember_wisp", (110,16,8,7,16,20,12), ["fire"], ["ice"],16, role="魔法型"),
        enemy("gate_beast", "水門の荒獣", "gate_beast", (320,0,30,16,0,12,13), [], [],24),
    ]
    roster += [
        enemy("mire_slime", "再生スライム", "slime", (95,9,11,8,8,7,7), ["slime_mend"], ["fire"],12,"mixed","自己回復型",heal_below=50),
        enemy("frost_slime", "冷気のスライム", "slime", (90,12,8,7,12,12,8), ["ice"], ["fire"],12,"caster","氷魔法型"),
        enemy("ward_slime", "守りのスライム", "slime", (140,9,12,16,6,9,5), ["firm_guard","acid"], ["fire"],14,"guardian","防御交替型"),
        enemy("balm_slime", "癒しのスライム", "slime", (105,16,7,7,10,12,18), ["heal"], ["fire"],14,"healer","仲間回復型",heal_below=75),
        enemy("elder_slime", "古株スライム", "slime", (170,18,16,12,14,14,10), ["acid","slime_mend"], ["fire"],18,"mixed","魔法・再生型",heal_below=50),
        enemy("frost_bat", "霜息コウモリ", "bat", (100,12,12,6,12,10,22), ["ice"], ["fire"],14,"caster","氷魔法型"),
        enemy("rending_bat", "裂羽コウモリ", "bat", (110,10,16,5,5,9,20), ["double_strike"], ["ice"],14,"raider","連撃型","lowest_hp"),
        enemy("echo_bat", "響きコウモリ", "bat", (105,16,10,7,12,13,19), ["soothing_song"], ["ice"],16,"healer","仲間回復型",heal_below=75),
        enemy("vigilant_bat", "見張りコウモリ", "bat", (120,12,15,10,6,10,18), ["firm_guard","quick_slash"], ["ice"],16,"guardian","防御・先制型"),
        enemy("night_bat", "夜渡りコウモリ", "bat", (160,18,19,8,15,14,25), ["spirit_bolt","quick_slash"], ["fire"],20,"caster","魔法・速攻型","highest_magic"),
        enemy("iron_shell", "鉄殻の番兵", "shell_guard", (160,9,18,28,5,5,4), ["firm_guard"], ["ice"],18,"guardian","重装防御型"),
        enemy("tide_shell", "水守りの番兵", "shell_guard", (140,12,13,20,13,9,7), ["ice"], ["fire"],18,"caster","氷魔法型"),
        enemy("ward_shell", "補修の番兵", "shell_guard", (150,12,10,20,11,10,17), ["heal"], ["ice"],20,"healer","仲間回復型",heal_below=75),
        enemy("spike_shell", "突殻の番兵", "shell_guard", (165,12,20,24,5,7,6), ["shield_strike"], ["ice"],20,"raider","物理強打型","lowest_hp"),
        enemy("ancient_shell", "古殻の番兵", "shell_guard", (230,18,23,29,8,8,5), ["shell_bash","firm_guard"], ["ice"],24,"guardian","重装強打型"),
        enemy("racing_wisp", "火走りの精", "ember_wisp", (120,15,15,8,16,16,22), ["quick_slash","fire"], ["ice"],18,"caster","魔法・先制型","lowest_hp"),
        enemy("cinder_wisp", "火守りの精", "ember_wisp", (140,15,9,12,15,20,12), ["firm_guard","fire"], ["ice"],18,"guardian","防御・魔法型"),
        enemy("lamp_wisp", "灯火の精", "ember_wisp", (130,20,8,8,14,18,19), ["heal","fire"], ["ice"],20,"healer","回復・魔法型",heal_below=75),
        enemy("ash_wisp", "灰還りの精", "ember_wisp", (140,16,8,9,15,18,16), ["revive","curse_bolt"], ["ice"],22,"reviver","蘇生型"),
        enemy("core_wisp", "炉心の精", "ember_wisp", (200,24,10,10,21,22,14), ["flame_breath","fire"], ["ice"],26,"caster","高威力魔法型","highest_magic"),
        enemy("river_beast", "川辺の荒獣", "gate_beast", (230,12,24,14,5,10,12), ["fang"], ["ice"],22,"raider","牙の強打型","lowest_hp"),
        enemy("watch_beast", "守門の荒獣", "gate_beast", (260,15,25,18,6,10,9), ["firm_guard","power_strike"], ["fire"],24,"guardian","防御・強打型"),
        enemy("swift_beast", "駆ける荒獣", "gate_beast", (220,15,20,12,8,12,24), ["quick_slash"], ["ice"],24,"raider","先制型","highest_magic"),
        enemy("mending_beast", "息継ぎの荒獣", "gate_beast", (300,12,23,16,10,12,10), ["breath","fang"], ["ice"],26,"mixed","自己回復・強打型",heal_below=50),
        enemy("flood_beast", "激流の荒獣", "gate_beast", (440,20,30,18,18,14,13), ["power_strike","sound_wave"], [],32,"caster","強打・音波型"),
    ]
    # 利用者が追加提供した画像を、行動と見た目が合う敵へ割り当てる。
    supplied = {
        "frost_slime": ("crystal_slime", "冷晶スライム"),
        "ward_slime": ("stone_slime", "岩殻スライム"),
        "elder_slime": ("flame_slime", "熔体スライム"),
        "frost_bat": ("ghost_bat", "幽翼コウモリ"),
        "rending_bat": ("bone_bat", "骨翼コウモリ"),
        "tide_shell": ("glacier_turtle", "氷殻の番兵"),
        "spike_shell": ("lava_turtle", "熔殻の番兵"),
        "ash_wisp": ("bone_wolf", "灰還りの骸獣"),
        "core_wisp": ("magma_wolf", "炉心の魔狼"),
        "river_beast": ("wet_beast", "川辺の荒獣"),
        "watch_beast": ("winged_beast", "守門の翼獣"),
        "swift_beast": ("wind_wolf", "疾風の荒獣"),
        "mending_beast": ("shadow_wolf", "影毛の荒獣"),
        "flood_beast": ("chimera_boss", "溶岩の大荒獣"),
    }
    for entry in roster:
        if entry["id"] in supplied:
            entry["sprite_id"],entry["name"] = supplied[entry["id"]]
            entry["design_status"] = "v1調整案。利用者が提供した追加画像を割り当てる。"
        if entry["id"] == "elder_slime":
            entry["abilities"] = ["fire","slime_mend"]
            entry["weaknesses"] = ["ice"]
        if entry["id"] == "spike_shell":
            entry["abilities"] = ["shield_strike","fire"]
            entry["stats"]["magic"] = 13
            entry["tactics"]["profile"] = "caster"
            entry["role"] = "強打・炎魔法型"
        if entry["id"] == "flood_beast":
            entry["abilities"] = ["power_strike","flame_breath"]
            entry["role"] = "強打・炎の息型"
    # 攻撃技の集中へ反応する節目戦。人数そのものや検査シードで勝敗を決めない。
    reactions = {
        "gate_beast": (320, 100, 0, 40),
        "elder_slime": (200, 500, 2, 20),
        "night_bat": (260, 300, 0, 20),
        "ancient_shell": (175, 400, 0, 40),
        "core_wisp": (220, 250, 0, 1),
        "flood_beast": (160, 200, 0, 20),
    }
    for entry in roster:
        if entry["id"] in reactions:
            hp, power, speed, shield = reactions[entry["id"]]
            entry["stats"]["hp"] = hp
            entry["tactics"].update(reaction_power=power, reaction_speed=speed,
                                     chorus_guard=shield, focus_variation=100)
            entry["design_status"] += " 攻撃技の集中への反応・共鳴防御を予告し、通常攻撃・回復・防御で対処できる調整案。"
        if entry["id"] == "ancient_shell":
            entry["stats"]["resistance"] = 100
            entry["tactics"]["guard_every"] = 3
        if entry["id"] == "elder_slime":
            entry["stats"]["resistance"] = 50
            entry["tactics"]["heal_below"] = 25
        if entry["id"] == "night_bat":
            entry["stats"]["resistance"] = 30
        if entry["id"] == "flood_beast":
            entry["stats"]["resistance"] = 60
    return roster
