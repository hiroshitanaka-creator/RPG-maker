from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,os
utc=lambda:datetime.now(timezone.utc).isoformat()
w=Path('/workspace/task080');a=json.loads((w/'active-approved.json').read_text());run=Path(a['run']);out=Path(a['evidence']);source=Path('/workspace/RPG-maker');repo=run/'reconstructed';base=a['base'];records=[]
def cmd(args,cwd,env=None):
 d={'command':args,'cwd':str(cwd),'timeout_seconds':None,'started_at_utc':utc()};p=subprocess.run(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);d.update(ended_at_utc=utc(),exit_code=p.returncode);records.append(d)
 with (out/'preparation.log').open('ab') as f:f.write(p.stdout)
 assert p.returncode==0,p.stdout.decode(errors='replace');return p.stdout
base_tree=cmd(['git','rev-parse',base+'^{tree}'],source).decode().strip();assert base_tree=='db2d461e2c31b99f909056cf730c453823ab08ae'
env=os.environ.copy();env['GIT_INDEX_FILE']=str(run/'pretest.index')
cmd(['git','read-tree',base],source,env)
paths=sorted(set(subprocess.check_output(['git','diff','--name-only',base],cwd=source,text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=source,text=True).splitlines()))
allowed=set(x['path'] for x in json.loads((w/'delivery/changed-files.json').read_text()))|{'tools/validate_assets.py','tools/check_adopted_room_provenance.py'}
assert set(paths)==allowed,(set(paths)-allowed,allowed-set(paths))
cmd(['git','add','--',*paths],source,env);tree=cmd(['git','write-tree'],source,env).decode().strip()
patch=cmd(['git','diff','--cached','--binary',base],source,env);(run/'pretest.patch').write_bytes(patch)
cmd(['git','diff','--cached','--check',base],source,env)
cmd(['git','clone','--shared','--no-checkout',str(source),str(repo)],run)
cmd(['git','checkout','--detach',base],repo)
def snapshot(ref):
 data=subprocess.check_output(['git','ls-tree','-r','-z',ref],cwd=repo);result={}
 for item in data.split(b'\0'):
  if not item:continue
  meta,path=item.split(b'\t',1);mode,kind,blob=meta.decode().split();assert kind=='blob';name=path.decode();raw=(repo/name).read_bytes()
  actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert actual==blob,name
  result[name]={'mode':mode,'git_blob':blob,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 return result
before=snapshot(base)
cmd(['git','apply','--check','--index',str(run/'pretest.patch')],repo)
cmd(['git','apply','--index',str(run/'pretest.patch')],repo)
assert cmd(['git','write-tree'],repo).decode().strip()==tree
after=snapshot(tree)
for label,data in [('base',before),('pretest',after)]:
 (out/(label+'-all-tracked-sha256.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
protected=[]
for x in json.loads((repo/'.scope-lock/frozen-files.json').read_text())['files']:
 name=x['path'];protected.append({'path':name,'base_sha256':before[name]['sha256'],'candidate_sha256':after[name]['sha256'],'frozen_sha256':x['sha256'],'match':before[name]['sha256']==after[name]['sha256']==x['sha256']})
assert len(protected)==26 and all(x['match'] for x in protected)
(out/'protected-26-sha256.json').write_text(json.dumps(protected,indent=2)+'\n')
old_zips=[]
for name,sha in [('task-080-adopted-room-walking-foundation.zip','b96acae544b2cd3a139f248e89f380aa720e666a27f0e38012195d4e8cf63e0c'),('task-080-timestamped-evidence-20261021T033604Z.zip','07f6d1d5440e94024ff77c0feff4c19655b821ee11e14df42cffe6d79648a429')]:
 p=w/name;actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==sha;old_zips.append({'file':name,'bytes':p.stat().st_size,'sha256':actual})
proof={'base_sha':base,'base_tree':base_tree,'pretest_tree':tree,'base_tracked':len(before),'pretest_tracked':len(after),'patch_sha256':hashlib.sha256(patch).hexdigest(),'old_zips':old_zips,'commands':records,'source_original_index_unchanged':True}
(out/'pretest-reconstruction.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
a.update(repo=str(repo),pretest_tree=tree);(w/'active-approved.json').write_text(json.dumps(a,indent=2)+'\n')
print(json.dumps({k:v for k,v in proof.items() if k!='commands'}),flush=True)
