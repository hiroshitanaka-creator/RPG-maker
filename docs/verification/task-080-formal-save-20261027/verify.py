from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,time,os,importlib.util,hashlib,shutil,sys,copy
r=Path(__file__).resolve().parent;repo=r/'repo';out=r/'verification-2';out.mkdir();records=[]
env=os.environ.copy();env.update(PATH='/workspace/task080/bin:'+env['PATH'],XDG_DATA_HOME=str(r/'xdg/data'),XDG_CONFIG_HOME=str(r/'xdg/config'),XDG_CACHE_HOME=str(r/'xdg/cache'),RPG_QA_SAVE_PREFIX='task080_formal',ADOPTED_ROOM_OUTPUT=str(out),DISPLAY=':84')
def execute(name,command,limit,extra=None,shell=False,cwd=repo):
 local=env.copy();local.update(extra or {});start=time.monotonic();d={'name':name,'started_at_utc':datetime.now(timezone.utc).isoformat(),'command':command,'cwd':str(cwd),'timeout_seconds':limit,'case_environment':extra or {},'status':'running'}
 (out/(name+'.started.json')).write_text(json.dumps(d,indent=2)+'\n')
 with (out/(name+'.log')).open('xb') as f:
  try:p=subprocess.run(command,cwd=cwd,env=local,stdout=f,stderr=subprocess.STDOUT,timeout=limit,shell=shell);code=p.returncode
  except subprocess.TimeoutExpired:code=124
 d.update(ended_at_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,exit_code=code,status='executed',log_sha256=hashlib.sha256((out/(name+'.log')).read_bytes()).hexdigest());records.append(d)
 (out/(name+'.execution.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(out/'execution.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(name,code,flush=True);return d
assert execute('00-editor-import',['godot','--headless','--editor','--import','--quit'],600)['exit_code']==0
execute('01-strict',['python3','tools/validate_assets.py','--strict'],120)
# 実装とvalidatorが不変候補と同じbytesで、最新mainの変更も欠落しないことを確認する。
state=json.loads((r/'state.json').read_text());snapshot=state['snapshot_commit'];latest=state['latest_main'];entries=json.loads((r/'planned-files.json').read_text());checks=[]
def git(*args):return subprocess.check_output(['git',*args],cwd=repo)
for e in entries:checks.append({'path':e['path'],'same_as_original_payload':hashlib.sha256((repo/e['path']).read_bytes()).hexdigest()==e['sha256']})
assert all(x['same_as_original_payload'] for x in checks)
assert not git('diff',latest,'--','docs/decision-log.md','docs/tasks/README.md')
for name in filter(None,git('diff','--name-only','-z',snapshot,'HEAD').decode().split('\0')):assert (repo/name).read_bytes()==git('show',latest+':'+name),name
sys.path.insert(0,str(repo/'tools'));import check_adopted_room_foundation as foundation
definition=json.loads((repo/'world/adopted_room_foundation.json').read_text());assert not foundation.inspect(definition)
negatives=[]
for label,mutate in [('missing-room',lambda d:d['rooms'].pop()),('wrong-image',lambda d:d['rooms'][1].update(path=d['rooms'][0]['path'])),('furniture-pass',lambda d:d['rooms'][1]['layout'].__setitem__(8,'##..........##')),('closed-entry',lambda d:d['rooms'][0]['layout'].__setitem__(10,'##############')),('unapproved-world-link',lambda d:d['rooms'][0].update(world_connection='world'))]:
 bad=copy.deepcopy(definition);mutate(bad);errors=foundation.inspect(bad);assert errors;negatives.append({'case':label,'errors':errors})
(out/'probes.json').write_text(json.dumps(foundation.PROBES,ensure_ascii=False,indent=2)+'\n');(out/'current-integrity.json').write_text(json.dumps({'snapshot':snapshot,'latest_main':latest,'candidate_payload':checks,'foundation_negatives':negatives,'all_latest_main_changes_retained':True,'parent_ledgers_exact_latest_main':True},ensure_ascii=False,indent=2)+'\n')
xf=(out/'xorg-stdout.log').open('xb');xp=subprocess.Popen(['Xorg',':84','-config','/etc/X11/xorg.conf','-noreset','-nolisten','tcp','-logfile',str(out/'xorg.log')],stdout=xf,stderr=subprocess.STDOUT,env=env)
try:
 for _ in range(50):
  if xp.poll() is not None:raise RuntimeError('Xorg failed')
  if Path('/tmp/.X11-unix/X84').exists():break
  time.sleep(.1)
 else:raise RuntimeError('Xorg readiness failed')
 for i,n in enumerate(['inn','item_shop','weapon_shop','shrine','armor_shop']):execute('02-render-'+n,['godot','--display-driver','x11','--audio-driver','Dummy','--path','.','--script','res://tools/check_adopted_room_foundation.gd'],180,{'ADOPTED_ROOM_INDEX':str(i)})
finally:xp.terminate();xp.wait(timeout=30);xf.close()
import run_locked_checks as locked
judgments=[]
for req in json.loads((repo/'.scope-lock/spec.lock.json').read_text())['requirements']:
 d=execute('03-'+req['id'],req['verify'],300,shell=True);judgments.append(locked.judge_output(req['id'],req['verify'],d['exit_code'],(out/('03-'+req['id']+'.log')).read_text(),d['exit_code']==124))
(out/'locked-results.json').write_text(json.dumps(judgments,ensure_ascii=False,indent=2)+'\n')
execute('04-frozen',['python3','tools/check_frozen_files.py'],60)
for name,script,limit in [('coastal-boundary','check_coastal_travel.gd',180),('saved-position','check_saved_position_relocation.gd',120),('second-coast','check_second_region_coast.gd',180),('region2-port','check_region2_port.gd',180)]:execute('05-'+name,['godot','--headless','--path','.','--script','res://tools/'+script],limit)
assert len(judgments)==8 and all(x['status']=='PASS' for x in judgments)
assert all(x['exit_code']==0 for x in records)
assert all(json.loads((out/('render-'+n+'.json')).read_text())['failed']==0 for n in ['inn','item_shop','weapon_shop','shrine','armor_shop'])
print('FORMAL_INTEGRATION_CHECKS_PASS',flush=True)
