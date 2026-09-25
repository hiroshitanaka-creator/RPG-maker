"""採用済み追加条件の登録と、既存凍結条件の保持を照合する。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATTLE = "godot --headless --path . --script res://tools/check_battle_acceptance.gd"
SAVE = "godot --headless --path . --script res://tools/check_save_contract.gd"
ADDITIONS = [
    {"id": "AC-01", "title": "指定戦闘の勝率",
     "done_when": "godot --headless で実行し、指定戦闘ごとに、編成・職業・習得技・装着・初期HP／MP・所持品・自動行動方針を固定して、シード0〜999で各1回、計1,000回試行する。勝利数÷1,000が0.40以上0.60以下であること。試行は毎回初期状態へ戻し、全滅・上限ターン到達を敗北として数え、実行エラーがあれば検査を失敗とする。",
     "verify": BATTLE},
    {"id": "AC-02", "title": "10ターン以内の戦闘終了率",
     "done_when": "godot --headless で実行し、対象戦闘・初期状態・自動行動方針・シード一覧を固定した全試行のうち、10ターン以内に戦闘が終了する割合が80%以上であること。",
     "verify": BATTLE},
    {"id": "AC-03", "title": "保存対象の完全往復",
     "done_when": "godot --headless で実行し、事前に列挙した往復保存対象の全変数について、保存直前と別インスタンスへのロード後を比較し、キー欠落・型・値・配列順序の不一致が0件であること。",
     "verify": SAVE},
]


def problems(contract: dict, before: dict) -> list[str]:
    errors = []
    requirements = contract.get("requirements", [])
    if requirements != before["requirements"] + ADDITIONS:
        errors.append("既存8条件の保持または追加3条件の本文・verify・順序が一致しない")
    for key in before:
        if key not in ("requirements", "amendments") and contract.get(key) != before[key]:
            errors.append("既存設定の変更: " + key)
    amendments = contract.get("amendments", [])
    if amendments[:len(before["amendments"])] != before["amendments"]:
        errors.append("既存の改訂履歴が保持されていない")
    if not any(entry.get("requirement") == "AC-01,AC-02,AC-03" for entry in amendments):
        errors.append("追加3条件の改訂理由がない")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", action="store_true", help="正式契約とは別に改訂案だけを照合する")
    args = parser.parse_args()
    target = "docs/verification/acceptance-registration-proposed.json" if args.proposal else ".scope-lock/spec.lock.json"
    contract = json.loads((ROOT / target).read_text(encoding="utf-8"))
    baseline = ROOT / "docs/verification/acceptance-registration-before/spec.lock.json"
    before = json.loads(baseline.read_text(encoding="utf-8")) if baseline.exists() else contract
    errors = problems(contract, before)
    for error in errors:
        print("AC_REGISTRATION_FAIL: " + error)
    label = "AC_REGISTRATION_PROPOSAL" if args.proposal else "AC_REGISTRATION"
    print("%s: requirements=%d errors=%d" % (label, len(contract["requirements"]), len(errors)))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
