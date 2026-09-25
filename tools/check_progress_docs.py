"""進捗文書の入口と履歴表示が欠けていないかを照合する。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY = (
    "development-status.md", "remaining-v1-work.md", "spec-status.md",
    "human-playtest-readiness.md", "v1-whole-project-audit.md", "nonhuman-work-v1.md",
    "nonhuman-remaining-20260925.md", "mastery-actions-delivery.md",
    "integrated-task-closure.md", "integrated-mechanics-delivery.md",
    "long-campaign-finish.md", "long-campaign-implementation-plan.md",
    "long-campaign-progress-16.md", "long-campaign-progress-20.md",
    "long-campaign-connection.md", "long-record-acceptance-fix.md",
    "preplay-checks-20260920.md", "battle-and-supply-20260920.md",
    "campaign-expansion-v1.md", "story-campaign-v1.md", "battle-foundation.md",
    "art-import.md", "world-map-phase1.md", "world-map-change-list.md",
    "scope-lock-review.md", "provisional-thresholds-v1.md",
)
NOTICE = "> 履歴資料: 以下の進捗・未達・暫定値は記録時点の状態です。現在の実装・受入・残作業は [現在地](current-status.md) を参照してください。"


def main() -> int:
    errors = []
    for name in HISTORY:
        path = ROOT / "docs" / name
        if not path.is_file() or NOTICE not in path.read_text(encoding="utf-8").splitlines()[:5]:
            errors.append(name + ": 冒頭の履歴表示がない")
    for name, link in (("README.md", "docs/current-status.md"), ("docs/current-status.md", "../.scope-lock/spec.lock.json"), ("docs/current-status.md", "../PLAYTEST_QUEUE.md")):
        if link not in (ROOT / name).read_text(encoding="utf-8"):
            errors.append(name + ": 必須参照がない: " + link)
    for error in errors:
        print("PROGRESS_DOCS_FAIL: " + error)
    print("PROGRESS_DOCS: history=%d errors=%d" % (len(HISTORY), len(errors)))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
