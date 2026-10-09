"""351ec408 / code55 の同じ5診断。既存058 checkoutをSHA確認して再利用する。"""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
root=Path('/tmp/qa059/resume351-code');area=Path('/tmp/qa059/resume351/native-evidence');out=area/'task059'
fixture=root/'tools/fixtures/equipment-save-transaction-platform'
sys.path.insert(0,str(fixture))
from process_capture import run_command,save
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
assert source=='351ec408e62c22c5ab509c0c0624808ffdc60613'
baseline=Path('/tmp/qa059/before');assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=baseline,text=True).strip()=='579ca1f463aaf9e93275039a59cf9d1ffb86adb5'
inventory=json.loads((root/'docs/verification/task059-save-qa-finalization/code-inventory.json').read_bytes())
for name,row in inventory['inventory'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==row['raw_sha256']
engine=area/'bin/Godot_v4.7.2-stable_linux.x86_64';env=os.environ.copy()
for key in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME','APPDATA','LOCALAPPDATA']:
 p=area/'profile'/key;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
run_command([str(engine),'--headless','--editor','--import','--quit'],area.parent/'import-isolated.log',area.parent/'import-isolated-process.json',cwd=root,env=env,budget=600,timeout_kind='outer_600_seconds')
assert not re.search(rb'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|Fontconfig error', (area.parent/'import-isolated.log').read_bytes())
out.mkdir(exist_ok=False)
commands=[('capture-tests',[sys.executable,str(fixture/'test_capture057.py'),'--output',str(out/'capture-tests')],180),
 ('scope059',[sys.executable,str(fixture/'scope059.py'),'--code-sha',inventory['code_sha'],'--source-sha',source,'--self-test','--output',str(out/'scope.json')],30),
 ('capture059',[sys.executable,str(fixture/'test_capture059.py'),'--output',str(out/'capture059')],180),
 ('baseline058',[sys.executable,str(fixture/'reproduce058.py'),'--checkout',str(baseline),'--output',str(out/'baseline058')],30),
 ('measurements',[sys.executable,str(fixture/'diagnostics057.py'),'--godot',str(engine),'--output',str(out/'measurements')],180)]
rows=[];failures=[]
for label,argv,budget in commands:
 path=out/(label+'-process.json')
 try:run_command(argv,out/(label+'.log'),path,cwd=root,budget=budget,timeout_kind='diagnostic_outer_'+str(budget)+'_seconds')
 except Exception as exc:failures.append(label+': '+type(exc).__name__+': '+str(exc))
 row=json.loads(path.read_bytes());rows.append(dict(row,label=label))
 if row['exit_code']!=0 or row['supervision'].get('stopped') is not True:failures.append(label+': exit='+str(row['exit_code'])+' stopped='+str(row['supervision'].get('stopped')))
 save(out/'execution.json',dict(source_sha=source,code_sha=inventory['code_sha'],status='FAIL' if failures else 'PASS',commands=rows,failures=failures,original_job_cause='UNCONFIRMED: original logs unavailable',difference='既存058 clean checkout再利用。元5コマンド/予算/検査本文不変。CI原失敗の再現成功とは別'))
 print(label,row['exit_code'],row['seconds'],flush=True)
print('RESUME_DIAGNOSTIC_'+('FAIL' if failures else 'PASS'),flush=True)
sys.exit(bool(failures))
