#!/usr/bin/env python3
"""082の採用本文を原文と照合し、本文改変の負例も検出する。"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "0cd7dc2070e651b353554422c361c02b0aedd160"
# 第11節1〜9、第12節で採用。台詞の短縮・言い換えを許容しない。
APPROVED = [
    ("状況", "祠への入室後、ネルは来訪者の腕と目を見てから顔を上げる。"),
    ("ネル", "その力は、身体を変える。便利な力だけれど、危険は隠せない。"),
    ("ネル", "浅いうちなら、ここで清められる。けれど、進みすぎれば人の職には戻れない。"),
    ("ネル", "私が伝えられるのは、スライム、獣、植物、甲殻の四つ。"),
    ("ネル", "仲間を強くする力。続けて攻める力。癒やす力。守る力。使い方は、それぞれ違う。"),
    ("状況", "ネルは古い記録に目を落とす。"),
    ("ネル", "『借りた力は、身体に残る。』……記録には、そうある。"),
    ("ネル", "深く進んだ人を戻す方法が、古い遺跡に残っているかもしれない。ここから先は、私にも分からない。"),
    ("ネル", "力を使うときは、自分の身体も見ておいで。"),
]


def valid(data):
    return (isinstance(data, dict) and set(data) == {"id", "source", "approval", "lines"}
            and data["id"] == "region2_shrine_s10" and SOURCE in data["source"]
            and "第12節" in data["approval"]
            and data["lines"] == [dict(speaker=speaker, text=text) for speaker, text in APPROVED])


def main():
    path = ROOT / "data/region2_shrine_scenes.json"
    data = json.loads(path.read_text())
    assert valid(data), "採用本文・話者・順序・出典の不一致"
    cases = []
    for index in range(9):
        changed = copy.deepcopy(data)
        changed["lines"][index]["text"] += "。"
        cases.append(changed)
    for field, value in [("speaker", "長老"), ("action", "unlock_all")]:
        changed = copy.deepcopy(data)
        changed["lines"][6][field] = value
        cases.append(changed)
    changed = copy.deepcopy(data)
    changed["lines"].reverse()
    cases.append(changed)
    changed = copy.deepcopy(data)
    changed["lines"].pop()
    cases.append(changed)
    assert all(not valid(case) for case in cases), "本文改変の負例を検出できない"
    result = {"status": "PASS", "approved_source_sha": SOURCE, "pages": 9,
              "negative_cases": len(cases), "data_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "placement": "未採用・この検査の対象外"}
    output = ROOT / "docs/verification/task-082/data-checks.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("SHRINE_DATA_PASS: pages=9 negative_cases=" + str(len(cases)))


if __name__ == "__main__":
    main()
