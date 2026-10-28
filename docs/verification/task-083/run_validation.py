#!/usr/bin/env python3
"""固定checkoutで083と既存082回帰・原R01〜R08を上限/判定不変で実行し原ログを保存。"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
from datetime import datetime, timezone

PARENT=Path('/workspace/RPG-maker')
PYTHON=PARENT/'.tools/cloud-onboarding/venv/bin/python'
GODOT=PARENT/'.tools/godot/4.7.2/godot'
def now():return datetime.now(timezone.utc).isoformat()
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env.update({'PATH':str(GODOT.parent)+':'+str(PYTHON.parent)+':'+env['PATH'],'PYTHONDONTWRITEBYTECODE':'1','RPG_QA_SAVE_PREFIX':'task083_final','XDG_CACHE_HOME':str(root/'.tools/task083/cache'),'XDG_CONFIG_HOME':str(root/'.tools/task083/config'),'XDG_DATA_HOME':str(root/'.tools/task083/data'),'DISPLAY':':83','VK_DRIVER_FILES':str(PARENT/'.tools/task083/lvp_icd.json')})
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    old=json.loads((PARENT/'docs/verification/task-082/final-validation/execution.json').read_text())
    commands=[]
    for c in old['checks']:
        cmd=c['command'].replace('/workspace/RPG-maker/.tools/godot/4.7.2/godot',str(GODOT)).replace('/workspace/RPG-maker/.tools/cloud-onboarding/venv/bin/python',str(PYTHON))
        commands.append((c['name'],shlex.split(cmd),c['timeout_seconds']))
    commands[2:2]=[('assets-strict',[str(PYTHON),'tools/validate_assets.py','--strict'],120),('s10-assets',[str(PYTHON),'tools/check_s10_static_display.py'],120),('s10-reproduce',[str(PYTHON),'tools/import_s10_ner_static.py','--out',str(out/'regenerated.png')],120),('s10-runtime',[str(GODOT),'--headless','--path','.','--script','res://tools/check_s10_static_display.gd'],120),('s10-capture',[str(GODOT),'--path','.','--rendering-method','mobile','--rendering-driver','vulkan','--audio-driver','Dummy','--script','res://tools/capture_s10_static_display.gd'],180)]
    records=[]
    spec=importlib.util.spec_from_file_location('judge',root/'tools/run_locked_checks.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for n,(name,cmd,limit) in enumerate(commands,1):
        started=now();timed=False
        try:
            p=subprocess.run(cmd,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit);data=p.stdout;code=p.returncode
        except subprocess.TimeoutExpired as e:
            data=e.stdout or b'';code=124;timed=True
        log=f'{n:02}-{name}.log.gz';(out/log).write_bytes(gzip.compress(data,mtime=0));output=data.decode('utf-8',errors='replace')
        issues=re.findall(r'^.*(?:SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL:).*$' ,output,re.M)
        result=module.judge_output(name,shlex.join(cmd),code,output,timed) if name.startswith('R-') else {'status':'PASS' if code==0 and not timed and not issues else 'FAIL','warnings_errors':issues}
        record={'name':name,'source_sha':source,'command':shlex.join(cmd),'cwd':str(root),'started':started,'finished':now(),'timeout_seconds':limit,'exit_code':code,'timed_out':timed,'result':result,'log':log,'raw_sha256':digest(data)}
        records.append(record);print(name,result['status'],code,flush=True)
        (out/'commands.json').write_text(json.dumps({'source_sha':source,'environment':{k:env[k] for k in ['RPG_QA_SAVE_PREFIX','PATH','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','VK_DRIVER_FILES','DISPLAY']},'checks':records},ensure_ascii=False,indent=2)+'\n')
    # 既存検査の証拠出力は新規083目録下で保存。082の原記録は作業ブランチで変更しない。
    generated=[]
    for folder in ['docs/verification/task-082','docs/verification/task-083']:
        for p in (root/folder).rglob('*'):
            if p.is_file():generated.append(p)
    with tarfile.open(out/'runtime-records.tar.gz','w:gz') as t:
        for p in generated:t.add(p,arcname=p.relative_to(root))
    for p in (root/'docs/verification/task-083').glob('*.png'):(out/p.name).write_bytes(p.read_bytes())
    for p in (root/'docs/verification/task-083').glob('*checks.json'):(out/p.name).write_bytes(p.read_bytes())
    changes=subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True)
    (out/'checkout-output-paths.txt').write_text(changes)
    tracked=subprocess.check_output(['git','diff','--name-only'],cwd=root,text=True).splitlines()
    code_paths=[p for p in tracked if not p.startswith('docs/verification/')]
    summary={'source_sha':source,'status':'PASS' if all(x['result']['status']=='PASS' for x in records) and not code_paths else 'FAIL','checks':[{k:x[k] for k in ['name','exit_code','result','log']} for x in records],'changed_code_paths':code_paths,'source_hashes':{p:digest((root/p).read_bytes()) for p in ['world/region2_village.json','assets/registry.json','scripts/world/first_region_view.gd','scripts/game/game_session.gd','tools/validate_assets.py','tools/check_s10_static_display.gd','tools/capture_s10_static_display.gd','tools/check_s10_static_display.py','tools/import_s10_ner_static.py']}}
    (out/'checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print('FINAL',summary['status'],flush=True)
    return summary['status']!='PASS'
if __name__=='__main__':raise SystemExit(main())
