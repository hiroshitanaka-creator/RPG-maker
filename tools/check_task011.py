"""011完成版の全検査を別checkoutで再実行し、最新HEADの継続条件も独立に実行する。"""
import argparse,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BAD=re.compile(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL:')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def run(command,path,target,env,limit,marker=None):
 started=time.monotonic()
 try:
  result=subprocess.run(command,cwd=path,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit);output=result.stdout.decode('utf8',errors='replace');code=result.returncode
 except subprocess.TimeoutExpired as error:output=(error.stdout or b'').decode('utf8',errors='replace')+'\nTIMEOUT\n';code=124
 target.parent.mkdir(parents=True,exist_ok=True);target.write_text(output)
 problems=[s for s in output.splitlines() if BAD.search(s)];ok=code==0 and not problems and (marker is None or len(re.findall('^'+re.escape(marker),output,re.M))==1)
 record=dict(status='PASS' if ok else 'FAIL',command=command,exit_code=code,errors=problems,elapsed_seconds=round(time.monotonic()-started,3),timeout_seconds=limit)
 print(target.name+': '+record['status']+' '+str(record['elapsed_seconds'])+'s',flush=True)
 if not ok:print(output[-5000:],flush=True)
 return record
def execute(path,exe,sha,target,stage):
 env=os.environ.copy();env['TASK011_EXECUTION_SHA']=sha;env['RPG_QA_SAVE_PREFIX']='task011-'+('fixed' if stage else 'latest');results={}
 with tempfile.TemporaryDirectory(prefix='task011-user-') as user:
  # XDG全域を隔離。通常の保存・自動保存・試遊記録へ一切触れない。
  for key,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:env[key]=str(Path(user)/folder);Path(env[key]).mkdir()
  if stage:results['import']=run([exe,'--headless','--path',str(path),'--editor','--import','--quit'],path,target/'import.log',env,600)
  results['assets']=run([sys.executable,'tools/check_task011_assets.py',*(['--stage'] if stage else [])],path,target/'assets.log',env,180,'TASK011_ASSETS_PASS:')
  results['runtime']=run([exe,'--headless','--path',str(path),'--script','res://tools/check_task011_runtime.gd',*(['--','--stage'] if stage else [])],path,target/'runtime.log',env,120,'TASK011_RUNTIME_PASS:')
  command=[exe,'--path',str(path),'--rendering-method','mobile','--rendering-driver','vulkan','--audio-driver','Dummy','--script','res://tools/capture_task011_ruins.gd']
  if not env.get('DISPLAY'):command=['xvfb-run','-a',*command]
  results['capture']=run(command,path,target/'capture.log',env,180,'TASK011_CAPTURE_PASS:')
  for name in ['assets','runtime']:
   file=path/'docs/verification/task-011/latest'/(name+'.json');record=json.loads(file.read_text()) if file.exists() else {}
   if record.get('status')!='PASS' or record.get('execution_sha')!=sha or record.get('stage')!=stage:results[name]['status']='FAIL'
  file=path/'docs/verification/task-011/latest/images/checks.json';record=json.loads(file.read_text()) if file.exists() else {}
  if record.get('status')!='PASS' or record.get('execution_sha')!=sha or record.get('renderer')!='X11' or len(record.get('images',[]))!=25 or not record.get('confirmation_state'):results['capture']['status']='FAIL'
 return dict(status='PASS' if all(r['status']=='PASS' for r in results.values()) else 'FAIL',execution_sha=sha,stage=stage,results=results)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--completed',required=True);parser.add_argument('--godot',default='godot');args=parser.parse_args()
 assert re.fullmatch('[0-9a-f]{40}',args.completed) and git('rev-parse',args.completed+'^{commit}').decode().strip()==args.completed
 head=git('rev-parse','HEAD').decode().strip();exe=str(Path(shutil.which(args.godot) or args.godot).resolve())
 engine=subprocess.check_output([exe,'--version'],text=True).strip();assert engine=='4.7.2.stable.official.ed1daf0bf','CI固定Godot 4.7.2を使用する'
 assert git('diff','--name-only','HEAD','--','scripts','world','assets','tools','.scope-lock','test','project.godot','.github').decode().strip()=='','実行SHAと本番・検査器の追跡ファイル一致'
 assert not [p for p in git('ls-files','--others','--exclude-standard').decode().splitlines() if p.startswith(('scripts/','world/','assets/','tools/')) and Path(p).suffix in ['.gd','.py','.json','.png']], '未登録の本番・検査器'
 from check_task011_assets import BASE
 old=git('show',BASE+':.github/workflows/ci.yml').decode();new=git('show','HEAD:.github/workflows/ci.yml').decode()
 pattern=r'      - name: 011遺跡の完成版と最新の通行・階段・保存・実描画を検査\n.*?(?=      - name:)'
 steps=re.findall(pattern,new,re.S);assert len(steps)==1 and re.sub(pattern,'',new,flags=re.S)==old,'既存CI不変・追加1ステップ'
 assert args.completed in steps[0] and '--completed '+args.completed in steps[0],'完成版完全SHAの固定'
 output=ROOT/'docs/verification/task-011/ci';output.mkdir(parents=True,exist_ok=True);report=dict(completed_sha=args.completed,latest_sha=head,engine_version=engine)
 with tempfile.TemporaryDirectory(prefix='task011-checkout-') as directory:
  fixed=Path(directory)/'fixed';subprocess.run(['git','worktree','add','--detach',str(fixed),args.completed],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
  try:
   report['fixed']=execute(fixed,exe,args.completed,output/'fixed',True)
   evidence=fixed/'docs/verification/task-011/latest';shutil.copytree(evidence,output/'fixed/evidence',dirs_exist_ok=True)
   assets=evidence/'assets.json';scope=json.loads(assets.read_text()).get('scope',{}) if assets.exists() else {};report['scope']=scope
   if scope.get('completed_sha')!=args.completed or scope.get('status')!='PASS':report['fixed']['status']='FAIL'
  finally:subprocess.run(['git','worktree','remove','--force',str(fixed)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
 report['latest']=execute(ROOT,exe,head,output/'latest',False)
 report['status']='PASS' if report['fixed']['status']==report['latest']['status']=='PASS' else 'FAIL';(output/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('TASK011_'+report['status']+': completed='+args.completed+' latest='+head,flush=True)
 return 0 if report['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
