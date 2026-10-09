#!/usr/bin/env python3
"""057基点→完成SHAの範囲と、後続HEADの完成コード不変を別々に確認する。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

BASE = '849d02bd2ea4dd44298eef225fe9a12927858d1b'
FIXTURE = 'tools/fixtures/equipment-save-transaction-platform/'
EXACT = {'tools/check_equipment_save_transaction_platform.py', FIXTURE+'run_ci.py',
         '.github/workflows/equipment-transaction-platform.yml', 'docs/decision-log.md',
         'docs/tasks/057-save-qa-diagnostics.md', 'docs/tasks/reports/057-save-qa-diagnostics.md'}


def git(checkout, *argv):
    return subprocess.check_output(['git', *argv], cwd=checkout)


def check(checkout, code_sha, source_sha):
    for sha in [code_sha, source_sha]:
        if not re.fullmatch('[0-9a-f]{40}', sha):raise ValueError('完全SHA必須')
    rows = git(checkout, 'diff', '--name-status', BASE, code_sha).decode().splitlines()
    code_paths = []
    for row in rows:
        status, path = row.split('\t')
        added_helper = status=='A' and path.startswith(FIXTURE) and Path(path).suffix in ['.py','.gd','.uid']
        allowed = path in EXACT or path.startswith('docs/verification/task057-save-qa-diagnostics/') or added_helper
        if status not in ['A','M'] or not allowed:raise ValueError('057担当外:'+row)
        if path.startswith(('tools/','.github/')):code_paths.append(path)
    for path in ['docs/decision-log.md','docs/tasks/057-save-qa-diagnostics.md']:
        old = git(checkout, 'show', BASE+':'+path) if path.endswith('decision-log.md') else git(checkout,'show','878c2316a4c9e72b253f7df001b6c6438ef7cb6d:'+path)
        new = git(checkout, 'show', code_sha+':'+path)
        valid = new.startswith(old) if path.endswith('decision-log.md') else re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b.*$',b'',old,flags=re.M)==re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b.*$',b'',new,flags=re.M)
        if not valid:raise ValueError('057文書範囲:'+path)
    inventory = {}
    for path in code_paths:
        raw = git(checkout,'show',code_sha+':'+path)
        if raw!=git(checkout,'show',source_sha+':'+path):raise ValueError('完成後code変更:'+path)
        inventory[path] = dict(git_blob=git(checkout,'rev-parse',code_sha+':'+path).decode().strip(), raw_sha256=hashlib.sha256(raw).hexdigest())
    later = git(checkout,'diff','--name-only',code_sha,source_sha).decode().splitlines()
    if any(not path.startswith('docs/') for path in later):raise ValueError('完成後担当外:'+str(later))
    return dict(base=BASE, code_sha=code_sha, source_sha=source_sha, changes=rows, inventory=inventory, later_documents=later)


def tests(checkout, code_sha, output):
    output.mkdir(parents=True, exist_ok=True)
    rows=[]
    # 実tree/commitを作る。working treeとbranchは変更しない。
    import os
    for name,path,expected in [('later-document','docs/tasks/future-independent-review.md',0),
                               ('outside-code','scripts/game/outside057.gd',1),
                               ('outside-fixed','outside057.txt',1)]:
        env=dict(os.environ,GIT_INDEX_FILE=str(output/(name+'.index')))
        subprocess.run(['git','read-tree',code_sha],cwd=checkout,env=env,check=True)
        blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=b'057 QA fixture\n',cwd=checkout).decode().strip()
        subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,path],cwd=checkout,env=env,check=True)
        tree=subprocess.check_output(['git','write-tree'],cwd=checkout,env=env).decode().strip()
        sha=subprocess.check_output(['git','-c','user.name=QA','-c','user.email=qa@example.invalid','commit-tree',tree,'-p',code_sha],input=b'057 scope QA\n',cwd=checkout).decode().strip()
        argv=[sys.executable,str(Path(__file__).resolve()),'--checkout',str(checkout),'--code-sha',sha if name=='outside-fixed' else code_sha,'--source-sha',sha]
        p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        (output/(name+'.log')).write_bytes(p.stdout)
        if p.returncode!=expected:raise ValueError('057 scope実exit:'+name)
        rows.append(dict(case=name,sha=sha,expected_exit=expected,exit_code=p.returncode,argv=argv))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkout',default=str(Path(__file__).resolve().parents[3]));p.add_argument('--code-sha',required=True);p.add_argument('--source-sha',required=True);p.add_argument('--output');p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    try:
        result=check(Path(a.checkout),a.code_sha,a.source_sha)
        if a.self_test:result['propagation']=tests(Path(a.checkout),a.code_sha,Path(a.output).parent/'scope057')
        if a.output:Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('SCOPE057_PASS: '+a.code_sha)
    except Exception as e:print('SCOPE057_FAIL: '+str(e));sys.exit(1)
