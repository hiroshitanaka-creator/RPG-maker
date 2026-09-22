"""新しい育成定義を使って旧ACの初期状態を暗黙に変えない。"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
document = json.loads((ROOT / "data/acceptance_battle_initial_states_v1.json").read_text(encoding="utf-8-sig"))
canonical = json.dumps(document["states"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
assert hashlib.sha256(canonical).hexdigest() == "4d607d57f3d81ef07f664128a7c08040620e691b65bc4081cc9918998026c6c6"
assert document["source_commit"] == "d4b5bef38c7ecb05afba604ee1fdd6f5ebfdfc4a"
for size, state in document["states"].items():
    assert state["format_version"] == 1 and len(state["party"]) == int(size)
print("ORIGINAL_ACCEPTANCE_INPUT_PASS: d4b5befの3人・4人の全初期値を保持")
