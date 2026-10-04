#!/usr/bin/env python3
"""009開始SHAから担当差分だけを独立監査。006のALLOWEDは変更しない。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
FIXED = '5f1c2ba231191b25b9b32a814b616a9f8d0a54ce'
PARENT = '152cdb18228f377adb2f25e868a59d9649f597e4'
START = 'b9024b8379ea08070fa6b4f61149b257e25277e6'
ALLOWED = {
    'AGENTS.md', '.github/workflows/region2-village-connections.yml',
    'tools/check_region2_village_regression.py', 'tools/check_region2_village_regression.gd',
    'tools/check_region2_village_regression.gd.uid',
    'tools/capture_task009_village_regression.gd', 'tools/capture_task009_village_regression.gd.uid',
    'tools/check_task009_scope.py', 'tools/check_task009_lifecycle.py',
    'tools/test_task009_lifecycle.py', 'tools/check_task009_assertion_map.py',
    'docs/decision-log.md', 'docs/tasks/009-test-lifecycle.md', 'docs/tasks/reports/009-test-lifecycle.md',
}
PARENT_PATHS = {'docs/tasks/006-connect-village-shells.md', 'docs/tasks/reports/006-connect-village-shells.md',
                'docs/tasks/007-oasis-village-connect.md', 'docs/tasks/008-record-bookmark-and-batch3.md'}
RULES = '''\n## 検査の世代と段階移行（2026-10-04 依頼者承認）\n\n- 今後の依頼書では、段階限定の状態と変更範囲の受入を、その段階の完成コミットの完全SHAに固定する。別checkoutで当時のコード・期待値・検査器を使い、push/PRのCIで毎回全項目を再検証し、対象SHAと結果を記録する。\n- 継続する動作の不変条件は、最新HEADの本番コードに対する回帰検査で毎回確かめる。固定版の成功だけで最新の成功を代用しない。\n- 承認済みの次段階へ移るときは、元の全assertionを「当時だけ」「最新でも継続」「承認済み新機能で置き換える現在条件」に分類し、固定側・最新側・後続検査の対応表と新機能の正負例を用意する。当時だけの条件も固定側に全て残す。\n- NPCの占有と地形の通行を区別し、入口・出口への到達を守る。未実装の後続機能を成功扱いせず、引継ぎと未検証を明示する。\n- 検査項目の削除・省略・黙ったskip・continue-on-error・実装から期待値を作る自己一致・時間上限の延長で合格させない。別job化する場合も既存の各job・コマンド上限を超えない。時間が不足する場合は証拠とともに報告する。\n- この追記は既存の権限・保護・承認の規則を変更しない。\n'''


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def tree(ref: str) -> dict[str, str]:
    return {line.split('\t', 1)[1]: line.split()[2] for line in git('ls-tree', '-r', ref).decode().splitlines()}


def allowed(path: str) -> bool:
    return path in ALLOWED or path.startswith('docs/verification/task-009/')


def audit(commit: str, worktree: bool = False) -> dict:
    target = git('rev-parse', commit + '^{commit}').decode().strip()
    base, current = tree(START), tree(target)
    failures = []
    if subprocess.run(['git', 'merge-base', '--is-ancestor', START, target], cwd=ROOT).returncode:
        failures.append('009開始SHAの子孫ではありません')
    changed = sorted(path for path in base.keys() | current.keys() if base.get(path) != current.get(path))
    failures += [path for path in changed if not allowed(path)]
    failures += ['削除: ' + path for path in base if path not in current]
    if worktree:
        dirty = set(git('diff', '--name-only', 'HEAD').decode().splitlines())
        dirty.update(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
        changed = sorted(set(changed) | dirty)
        failures += [path for path in dirty if not allowed(path)]
    def content(path: str) -> bytes:
        return (ROOT / path).read_bytes() if worktree else git('show', target + ':' + path)
    original_agents = git('show', START + ':AGENTS.md')
    if content('AGENTS.md') != original_agents + RULES.encode():
        failures.append('AGENTS既存全文または承認済み追記が一致しません')
    request = 'docs/tasks/009-test-lifecycle.md'
    normalize = lambda b: re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b\xef\xbc\x9a.*$', b'- state: excluded', b, count=1, flags=re.M)
    if normalize(content(request)) != normalize(git('show', START + ':' + request)):
        failures.append('009依頼書の状態行以外の変更')
    parent_changes = set(git('diff', '--name-only', FIXED, PARENT).decode().splitlines())
    if parent_changes != PARENT_PATHS:
        failures.append('親登録の固定差分が4パスと一致しません')
    for path in PARENT_PATHS:
        if content(path) != git('show', PARENT + ':' + path):
            failures.append('親確認/007/008の不変違反: ' + path)
    protected = [p for p in base if p.startswith(('assets/', '.scope-lock/', 'test/', 'scripts/', 'world/', 'data/', 'addons/')) or p == 'project.godot' or (p.startswith('tools/') and not allowed(p)) or p == '.github/workflows/ci.yml']
    def blob(path: str) -> str | None:
        if worktree:
            file = ROOT / path
            if not file.is_file():return None
            data = file.read_bytes()
            return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        return current.get(path)
    for path in protected:
        if blob(path) != base[path]:
            failures.append('保全対象のバイト変更: ' + path)
    history = [p for p in base if p.startswith('docs/verification/region2-village-connections/')]
    fixed_tree = tree(FIXED)
    for path in history:
        if blob(path) != fixed_tree[path]:
            failures.append('006歴史証拠の変更: ' + path)
    # 後続でも変わらない009専用依頼書の状態変更commitをCI監査の完成点として使用する。
    report = {'status': 'PASS' if not failures else 'FAIL', 'start_sha': START, 'fixed_006_sha': FIXED,
              'parent_registration_sha': PARENT, 'execution_sha': target, 'worktree': worktree,
              'changed_files': changed, 'failures': sorted(set(failures)), 'preserved_paths': len(protected),
              'owner_originals': sum(p.startswith('assets/_incoming/') for p in protected),
              'historical_images': sum(p.endswith('.png') for p in history),
              'historical_capture_images': sum(p.endswith('.png') and p.split('/')[-2] in ['journey', 'details', *[f'restart-{i}' for i in range(5)]] for p in history),
              'historical_inputs': sum('/saved-inputs/' in p for p in history)}
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--worktree', action='store_true')
    args = parser.parse_args()
    report = audit(args.commit, args.worktree)
    output = ROOT / 'docs/verification/task-009/scope-checks.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
