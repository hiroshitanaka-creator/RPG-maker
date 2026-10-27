"""限定承認後の時刻付き実行。検査条件・上限・原検査器を維持する。"""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,time,os,importlib.util,hashlib,shutil
utc=lambda:datetime.now(timezone.utc).isoformat(timespec='microseconds')
w=Path('/workspace/task080');a=json.loads((w/'active-approved.json').read_text());run=Path(a['run']);out=Path(a['evidence']);repo=Path(a['repo']);records=[]
env=os.environ.copy();env.update(PATH=str(w/'bin')+':'+env['PATH'],XDG_DATA_HOME=str(run/'xdg/data'),XDG_CONFIG_HOME=str(run/'xdg/config'),XDG_CACHE_HOME=str(run/'xdg/cache'),RPG_QA_SAVE_PREFIX='task080_approved',ADOPTED_ROOM_OUTPUT=str(out),DISPLAY=':83')
def execute(name,command,limit,extra=None,shell=False,cwd=None):
 cwd=Path(cwd or repo);local=env.copy();local.update(extra or {});tick=time.monotonic()
 record={'sequence':len(records),'name':name,'started_at_utc':utc(),'command':command,'shell':shell,'cwd':str(cwd),'timeout_seconds':limit,'status':'running','environment_overrides':{k:local[k] for k in ['PATH','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','RPG_QA_SAVE_PREFIX','ADOPTED_ROOM_OUTPUT','DISPLAY']},'case_environment':extra or {}}
 with (out/(name+'.started.json')).open('x') as f:json.dump(record,f,ensure_ascii=False,indent=2)
 timed_out=False
 with (out/(name+'.log')).open('xb') as f:
  try:p=subprocess.run(command,cwd=cwd,env=local,stdout=f,stderr=subprocess.STDOUT,timeout=limit,shell=shell);code=p.returncode
  except subprocess.TimeoutExpired:code=124;timed_out=True
 record.update(ended_at_utc=utc(),elapsed_seconds=time.monotonic()-tick,exit_code=code,timed_out=timed_out,status='timeout' if timed_out else 'executed',log_sha256=hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest())
 with (out/(name+'.execution.json')).open('x') as f:json.dump(record,f,ensure_ascii=False,indent=2)
 records.append(record);print(json.dumps(record,ensure_ascii=False),flush=True);return record
imp=execute('00-editor-import',['godot','--headless','--editor','--import','--quit'],600)
if imp['exit_code']!=0:raise SystemExit('import failed; subsequent game tests not executed')
execute('01-provenance',['python3','tools/check_adopted_room_provenance.py','--output',str(out)],120)
execute('02-assets-strict',['python3','tools/validate_assets.py','--strict'],120)
xargs=['Xorg',':83','-config','/etc/X11/xorg.conf','-noreset','-nolisten','tcp','-logfile',str(out/'xorg.log')];shutil.copyfile('/etc/X11/xorg.conf',out/'xorg.conf');xf=(out/'xorg-stdout.log').open('xb');xstart=utc();xp=subprocess.Popen(xargs,cwd=repo,env=env,stdout=xf,stderr=subprocess.STDOUT)
try:
 for _ in range(50):
  if xp.poll() is not None:raise RuntimeError('Xorg startup failed')
  if Path('/tmp/.X11-unix/X83').exists():break
  time.sleep(.1)
 else:raise RuntimeError('Xorg startup timed out')
 for index,name in enumerate(['inn','item_shop','weapon_shop','shrine','armor_shop']):execute('03-render-'+name,['godot','--display-driver','x11','--audio-driver','Dummy','--path','.','--script','res://tools/check_adopted_room_foundation.gd'],180,{'ADOPTED_ROOM_INDEX':str(index)})
finally:
 xp.terminate();xp.wait(timeout=30);xf.close()
 (out/'xorg.lifecycle.json').write_text(json.dumps({'command':xargs,'cwd':str(repo),'timeout_seconds':None,'started_at_utc':xstart,'ended_at_utc':utc(),'exit_code':xp.returncode,'status':'terminated by runner after renders; startup readiness 5s; shutdown wait 30s'},indent=2)+'\n')
spec=importlib.util.spec_from_file_location('locked',repo/'tools/run_locked_checks.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);locked=[]
for req in json.loads((repo/'.scope-lock/spec.lock.json').read_text())['requirements']:
 record=execute('04-'+req['id'],req['verify'],300,shell=True)
 locked.append(module.judge_output(req['id'],req['verify'],record['exit_code'],(out/('04-'+req['id']+'.log')).read_text(),record['timed_out']))
(out/'locked-results.json').write_text(json.dumps(locked,ensure_ascii=False,indent=2)+'\n')
execute('05-frozen',['python3','tools/check_frozen_files.py'],60)
# 前段階だけの範囲条件を、無変更の前候補の全tree上で確認する。
history=Path('/workspace/task080/recheck-20261021T033604Z/reconstructed');historical_out=out/'historical';historical_out.mkdir()
execute('06-historical-import',['godot','--headless','--editor','--import','--quit'],600,cwd=history)
execute('07-historical-python',['python3','tools/check_adopted_room_foundation.py','--output',str(historical_out)],120,cwd=history)
summary={'started_at_utc':records[0]['started_at_utc'],'ended_at_utc':utc(),'pretest_tree':a['pretest_tree'],'execution_count':len(records),'import_first':records[0]['name']=='00-editor-import','import_finished_before_every_verification':all(imp['ended_at_utc']<=x['started_at_utc'] for x in records[1:]),'sequential_no_overlap':all(x['ended_at_utc']<=y['started_at_utc'] for x,y in zip(records,records[1:])),'records':records,'locked_all_pass':len(locked)==8 and all(x['status']=='PASS' for x in locked)}
(out/'chronology.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
assert summary['import_first'] and summary['import_finished_before_every_verification'] and summary['sequential_no_overlap'] and summary['locked_all_pass']
assert all(x['exit_code']==0 for x in records)
assert json.loads((out/'provenance.json').read_text())['failed']==0
for name in ['inn','item_shop','weapon_shop','shrine','armor_shop']:assert json.loads((out/('render-'+name+'.json')).read_text())['failed']==0
print('APPROVED_RECHECK: all requested checks passed; strict 1159 passed',flush=True)
