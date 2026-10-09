#!/usr/bin/env python3
"""059基点→専用完成SHAと、後続文書追加時の完成コード不変を独立確認。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
BASE='579ca1f463aaf9e93275039a59cf9d1ffb86adb5'
REGISTER='a6022f1e4a7689440928efe65db444336e9128e4'
FIXTURE='tools/fixtures/equipment-save-transaction-platform/'
EXACT={'tools/check_equipment_save_transaction_platform.py',FIXTURE+'process_capture.py',FIXTURE+'run_ci.py',FIXTURE+'test_capture057.py',FIXTURE+'capture_fixture.py',FIXTURE+'diagnostic_ci057.py','.github/workflows/equipment-transaction-platform.yml','docs/decision-log.md','docs/tasks/059-fix-save-qa-finalization.md','docs/tasks/reports/059-fix-save-qa-finalization.md'}


def git(checkout,*args):return subprocess.check_output(['git',*args],cwd=checkout)


def check(checkout,code,source):
    for sha in (code,source):
        if not re.fullmatch('[0-9a-f]{40}',sha or ''):raise ValueError('完全SHA必須')
    changes=git(checkout,'diff','--name-status',BASE,code).decode().splitlines();inventory={}
    for line in changes:
        status,path=line.split('\t')
        added_helper=status=='A' and path.startswith(FIXTURE) and Path(path).suffix=='.py'
        if status not in ('A','M') or not (path in EXACT or added_helper or path.startswith('docs/verification/task059-save-qa-finalization/')):
            raise ValueError('059担当外:'+line)
        if path.startswith(('tools/','.github/')):
            raw=git(checkout,'show',code+':'+path)
            if raw!=git(checkout,'show',source+':'+path):raise ValueError('完成後code変更:'+path)
            inventory[path]=dict(git_blob=git(checkout,'rev-parse',code+':'+path).decode().strip(),raw_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    old=git(checkout,'show',BASE+':docs/decision-log.md');new=git(checkout,'show',code+':docs/decision-log.md')
    if not new.startswith(old):raise ValueError('decision-logは末尾追記だけ')
    old=git(checkout,'show',REGISTER+':docs/tasks/059-fix-save-qa-finalization.md');new=git(checkout,'show',code+':docs/tasks/059-fix-save-qa-finalization.md')
    strip=lambda raw:re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b.*$',b'',raw,flags=re.M)
    if strip(old)!=strip(new):raise ValueError('依頼書は状態行だけ')
    later=git(checkout,'diff','--name-only',code,source).decode().splitlines()
    if any(not p.startswith('docs/') for p in later):raise ValueError('完成後担当外:'+str(later))
    return dict(base=BASE,registration=REGISTER,code_sha=code,source_sha=source,changes=changes,inventory=inventory,later_documents=later)


def tests(checkout,code,output):
    output.mkdir(parents=True,exist_ok=True);rows=[]
    for name,path,expected in [('later-document','docs/tasks/future-independent-review.md',0),('outside-code','scripts/game/outside059.gd',1),('outside-fixed','outside059.txt',1),('changed-fixed-code',FIXTURE+'process_capture.py',1)]:
        env=dict(os.environ,GIT_INDEX_FILE=str(output/(name+'.index')))
        subprocess.run(['git','read-tree',code],cwd=checkout,env=env,check=True)
        blob=git_input(checkout,['git','hash-object','-w','--stdin'],b'059 scope QA\n').decode().strip()
        subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,path],cwd=checkout,env=env,check=True)
        tree=subprocess.check_output(['git','write-tree'],cwd=checkout,env=env).decode().strip()
        sha=git_input(checkout,['git','-c','user.name=QA','-c','user.email=qa@example.invalid','commit-tree',tree,'-p',code],b'059 scope QA\n').decode().strip()
        argv=[sys.executable,__file__,'--checkout',str(checkout),'--code-sha',sha if name=='outside-fixed' else code,'--source-sha',sha]
        start=__import__('time').monotonic();p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        (output/(name+'.log')).write_bytes(p.stdout)
        if p.returncode!=expected:raise ValueError('scope059実exit:'+name)
        rows.append(dict(case=name,code_sha=code,source_sha=sha,expected_exit=expected,exit_code=p.returncode,argv=argv,seconds=__import__('time').monotonic()-start))
    return rows


def git_input(checkout,argv,raw):return subprocess.check_output(argv,input=raw,cwd=checkout)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkout',default=str(Path(__file__).resolve().parents[3]));p.add_argument('--code-sha',required=True);p.add_argument('--source-sha',required=True);p.add_argument('--output');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    try:
        value=check(Path(a.checkout),a.code_sha,a.source_sha)
        if a.self_test:value['propagation']=tests(Path(a.checkout),a.code_sha,Path(a.output).parent/'scope059')
        if a.output:Path(a.output).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('SCOPE059_PASS: '+a.code_sha)
    except Exception as exc:print('SCOPE059_FAIL: '+str(exc));sys.exit(1)
