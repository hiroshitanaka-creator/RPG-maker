#!/usr/bin/env python3
"""原ログ・ソース・CIの対応を検証して、全変更パスと証拠目録を作る。"""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE="6c996d5c37fd384e679bb23dd59113c99494790c"
SOURCE="e675aca03d7a726379f88ad1529a2597f38de405"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    local=json.loads((OUT/"final-validation/execution.json").read_text())
    assert local["source_sha"]==SOURCE and len(local["checks"])==19
    for row in local["checks"]:
        assert row["exit_code"]==0 and row["result"]["status"]=="PASS"
        assert hashlib.sha256(gzip.decompress((OUT/"final-validation"/row["log"]).read_bytes())).hexdigest()==row["raw_sha256"]
    for path,value in local["source_sha256"].items():assert sha(ROOT/path)==value
    runtime=json.loads((OUT/"final-validation/runtime-checks.json").read_text())
    assert runtime["status"]=="PASS" and len(runtime["checks"])==293
    ci=json.loads((OUT/"final-validation/github-checks.json").read_text())
    assert ci["head_sha"]==SOURCE and ci["total_count"]==38
    assert all(row["status"]=="completed" and row["conclusion"]=="success" for row in ci["check_runs"])
    runs=json.loads((OUT/"final-validation/github-workflows.json").read_text())
    assert runs["head_sha"]==SOURCE and len(runs["workflow_runs"])==5
    assert all(row["status"]=="completed" and row["conclusion"]=="success" for row in runs["workflow_runs"])
    tracked=subprocess.check_output(["git","diff","--name-only",BASE,"HEAD"],cwd=ROOT,text=True).splitlines()
    staged=subprocess.check_output(["git","diff","--cached","--name-only","HEAD"],cwd=ROOT,text=True).splitlines()
    untracked=subprocess.check_output(["git","ls-files","--others","--exclude-standard"],cwd=ROOT,text=True).splitlines()
    files=sorted(set(tracked+staged+[p for p in untracked if p.startswith("docs/verification/task-082/") or p=="docs/tasks/reports/082-report.md"]+["docs/verification/task-082/evidence-manifest.json","docs/verification/task-082/changed-paths.txt"]))
    allowed=set(local["source_sha256"])
    assert all(p in allowed or p.startswith("docs/verification/task-082/") or p=="docs/tasks/reports/082-report.md" for p in files)
    (OUT/"changed-paths.txt").write_text("\n".join(files)+"\n")
    items={}
    for p in files:
        if p.endswith("/evidence-manifest.json"):continue
        path=ROOT/p
        assert path.is_file(),p
        items[p]={"bytes":path.stat().st_size,"sha256":sha(path)}
    document={"baseline_main":BASE,"verified_implementation_sha":SOURCE,"local_commands":19,"focused_checks":293,"ci_workflows":5,"ci_jobs":38,"ci_result":"success","draft_pr":{"url":"https://github.com/hiroshitanaka-creator/RPG-maker/pull/63","draft":True,"merged":False,"initial_denial_preserved":True,"same_action_retry_count":1},"changed_paths":files,"source_sha256":local["source_sha256"],"artifacts":items,"self_hash_note":"この目録自身のhashだけは循環を避けて除外。changed-paths.txtには目録自身も含む。","remaining":{"visual_integration":"初配置の採否待ち・今回変更なし","optional_jobs":"旧共通ゲートを維持。受取/移行規則は未決","local_extra_regression":"eb423adの64検査中62成功。011通知fixture180秒timeoutと081旧段階比較はFAILを保持。最終版の正式CIは全件成功。"}}
    (OUT/"evidence-manifest.json").write_text(json.dumps(document,ensure_ascii=False,indent=2)+"\n")
    print("MANIFEST_PASS: changed_paths=%d artifacts=%d source=%s"%(len(files),len(items),SOURCE))

if __name__=="__main__":main()
