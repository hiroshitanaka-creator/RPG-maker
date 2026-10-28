#!/usr/bin/env python3
"""既存CIと同じ009通常入力・実描画を同じ180秒上限で実行する。"""
import datetime,gzip,hashlib,json,os,subprocess,tarfile
from pathlib import Path
PARENT=Path('/workspace/RPG-maker');ROOT=Path('/workspace/task083-final-verification');OUT=PARENT/'docs/verification/task-083/journey-corrected';OUT.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.update({'PATH':str(PARENT/'.tools/task083/root/usr/bin')+':'+str(PARENT/'.tools/godot/4.7.2')+':'+str(PARENT/'.tools/cloud-onboarding/venv/bin')+':'+env['PATH'],'RPG_QA_SAVE_PREFIX':'task083_journey','XDG_CACHE_HOME':str(ROOT/'.tools/task083/cache'),'XDG_CONFIG_HOME':str(ROOT/'.tools/task083/config'),'XDG_DATA_HOME':str(ROOT/'.tools/task083/data'),'VK_DRIVER_FILES':str(PARENT/'.tools/task083/lvp_icd.json'),'PYTHONDONTWRITEBYTECODE':'1'})
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
records=[]
for name,args in [('prepare',[]),('journey',['--capture','journey'])]:
 cmd=[str(PARENT/'.tools/cloud-onboarding/venv/bin/python'),'tools/check_region2_village_regression.py','--commit',sha,'--godot',str(PARENT/'.tools/godot/4.7.2/godot'),*args]
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (OUT/(name+'.log.gz')).write_bytes(gzip.compress(p.stdout,mtime=0));record={'name':name,'source_sha':sha,'command':cmd,'cwd':str(ROOT),'started':started,'finished':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'raw_sha256':hashlib.sha256(p.stdout).hexdigest(),'limits':'原checkerの各180秒上限を維持','log':name+'.log.gz'};records.append(record);print(name,p.returncode,p.stdout.decode()[-300:],flush=True)
 (OUT/'commands.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
with tarfile.open(OUT/'runtime-records.tar.gz','w:gz') as t:
 t.add(ROOT/'docs/verification/task-009/latest',arcname='docs/verification/task-009/latest')
raise SystemExit(any(r['exit_code']!=0 for r in records))
