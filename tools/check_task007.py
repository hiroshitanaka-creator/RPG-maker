"""007の固定完成版を別checkoutで実行し、継続する動作を最新HEADでも実行する。"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
BAD=re.compile(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL')

def run(command,path,target,env,limit=180,marker=None):
    started=time.monotonic()
    try:
        proc=subprocess.run(command,cwd=path,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit)
        output=proc.stdout.decode('utf-8',errors='replace');code=proc.returncode
    except subprocess.TimeoutExpired as error:
        output=(error.stdout or b'').decode('utf-8',errors='replace')+'\nTIMEOUT\n';code=124
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(output)
    problems=[line for line in output.splitlines() if BAD.search(line)]
    ok=code==0 and not problems and (marker is None or len(re.findall('^'+re.escape(marker),output,re.M))==1)
    print(target.name+': '+('PASS' if ok else 'FAIL')+' '+str(round(time.monotonic()-started,3))+'s',flush=True)
    if not ok:print(output[-4000:],flush=True)
    return dict(status='PASS' if ok else 'FAIL',command=command,exit_code=code,errors=problems,elapsed_seconds=round(time.monotonic()-started,3),timeout_seconds=limit)

def execute(path,exe,sha,target,stage):
    env=os.environ.copy();env['TASK007_EXECUTION_SHA']=sha
    env['RPG_QA_SAVE_PREFIX']='task007-'+('fixed' if stage else 'latest')
    results={}
    if stage:
        results['import']=run([exe,'--headless','--path',str(path),'--editor','--import','--quit'],path,target/'import.log',env,600)
    extra=['--','--stage'] if stage else []
    results['assets']=run([sys.executable,'tools/check_task007_assets.py',*(['--stage'] if stage else [])],path,target/'assets.log',env,180,'TASK007_ASSETS_PASS:')
    results['services']=run([exe,'--headless','--path',str(path),'--script','res://tools/check_task007_services.gd',*extra],path,target/'services.log',env,180,'TASK007_SERVICES_PASS:')
    observed=path/'docs/verification/task-007/latest/services.json'
    report=json.loads(observed.read_text()) if observed.exists() else {}
    if report.get('status')!='PASS' or report.get('execution_sha')!=sha or len(report.get('residents',[]))!=6:results['services']['status']='FAIL'
    for mode in ['outside','rooms']:
        command=[exe,'--path',str(path),'--rendering-method','mobile','--rendering-driver','vulkan','--audio-driver','Dummy','--script','res://tools/capture_task007_services.gd',*(['--','--rooms'] if mode=='rooms' else [])]
        if not env.get('DISPLAY'):command=['xvfb-run','-a',*command]
        results[mode]=run(command,path,target/(mode+'.log'),env,180,'TASK007_CAPTURE_PASS:')
        record=path/'docs/verification/task-007/latest'/mode/'checks.json'
        captured=json.loads(record.read_text()) if record.exists() else {}
        expected=11 if mode=='outside' else 22
        if captured.get('status')!='PASS' or captured.get('execution_sha')!=sha or captured.get('renderer')!='X11' or len(captured.get('images',[]))!=expected:results[mode]['status']='FAIL'
    return dict(status='PASS' if all(r['status']=='PASS' for r in results.values()) else 'FAIL',execution_sha=sha,stage=stage,results=results)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--completed',required=True);parser.add_argument('--godot',default='godot');args=parser.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',args.completed),'完成版は完全SHAで指定'
    assert git('rev-parse',args.completed+'^{commit}').decode().strip()==args.completed
    head=git('rev-parse','HEAD').decode().strip()
    assert subprocess.run(['git','diff','--quiet','HEAD','--','scripts','world','assets','tools','.scope-lock','test','project.godot','.github'],cwd=ROOT).returncode==0,'実行SHAと追跡本番・検査器の一致'
    untracked=git('ls-files','--others','--exclude-standard').decode().splitlines()
    assert not [p for p in untracked if p.startswith(('scripts/','world/','assets/','tools/')) and Path(p).suffix in ['.gd','.py','.json','.png']], '本番・検査器の未登録ファイルがあります'
    exe=str(Path(shutil.which(args.godot) or args.godot).resolve())
    output=ROOT/'docs/verification/task-007/ci';output.mkdir(parents=True,exist_ok=True)
    report=dict(completed_sha=args.completed,latest_sha=head)
    with tempfile.TemporaryDirectory(prefix='task007-') as directory:
        fixed=Path(directory)/'fixed'
        subprocess.run(['git','worktree','add','--detach',str(fixed),args.completed],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            report['fixed']=execute(fixed,exe,args.completed,output/'fixed',True)
            evidence=fixed/'docs/verification/task-007/latest'
            shutil.copytree(evidence,output/'fixed'/'evidence',dirs_exist_ok=True)
            report['scope']=json.loads((evidence/'assets.json').read_text())['scope']
            assert report['scope']['completed_sha']==args.completed and report['scope']['status']=='PASS'
        finally:
            # checkoutに生成されるimport/検査証拠だけを清掃。コミット履歴・登録ブランチは変更しない。
            subprocess.run(['git','worktree','remove','--force',str(fixed)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    report['latest']=execute(ROOT,exe,head,output/'latest',False)
    report['status']='PASS' if report['fixed']['status']==report['latest']['status']=='PASS' else 'FAIL'
    (output/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('TASK007_'+report['status']+': completed='+args.completed+' latest='+head,flush=True)
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':
    raise SystemExit(main())
