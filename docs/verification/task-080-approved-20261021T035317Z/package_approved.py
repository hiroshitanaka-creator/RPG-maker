"""検証済み候補を全treeから再構成し、未commit提出物をまとめる。"""
from pathlib import Path
from datetime import datetime, timezone
import subprocess, json, hashlib, os, shutil, gzip, zipfile

w = Path('/workspace/task080')
a = json.loads((w/'active-approved.json').read_text())
run = Path(a['run']); evidence = Path(a['evidence']); source = Path('/workspace/RPG-maker')
delivery = run/'delivery'; delivery.mkdir()
proof_dir = delivery/'reconstruction'; proof_dir.mkdir()
utc = lambda: datetime.now(timezone.utc).isoformat()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
records = []
def execute(args, cwd, env=None):
    record = {'command':args, 'cwd':str(cwd), 'started_at_utc':utc(), 'timeout_seconds':None}
    result = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    record.update(ended_at_utc=utc(), exit_code=result.returncode)
    records.append(record)
    with (proof_dir/'reconstruction.log').open('ab') as f:
        f.write(result.stdout)
    assert result.returncode == 0, result.stdout.decode(errors='replace')
    return result.stdout

summary = json.loads((evidence/'summary.json').read_text())
assert summary['room_checks']==1191 and summary['room_inputs']==1862 and summary['strict_exit']==0
pretest = json.loads((evidence/'pretest-all-tracked-sha256.json').read_text())
report = 'docs/tasks/reports/080-adopted-room-walking-foundation.md'
assert all(sha((source/p).read_bytes()) == v['sha256'] for p,v in pretest.items() if p != report)
prefix = 'docs/verification/task-080-approved-'+a['stamp']
dest = source/prefix; dest.mkdir()
copied = []
for p in sorted(evidence.rglob('*')):
    if not p.is_file(): continue
    relative = p.relative_to(evidence)
    raw = p.read_bytes()
    target = dest/relative
    if p.suffix in ('.log', '.patch'):
        target=target.with_name(target.name+'.gz')
        packed=gzip.compress(raw, mtime=0)
        assert gzip.decompress(packed)==raw
    else: packed=raw
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(packed)
    copied.append({'source':str(relative),'candidate':str(target.relative_to(source)),'raw_bytes':len(raw),'raw_sha256':sha(raw),'candidate_sha256':sha(packed)})
(dest/'.gdignore').write_text('')
write(proof_dir/'evidence-raw-to-candidate.json', copied)
previous_paths=set(x['path'] for x in json.loads((w/'delivery/changed-files.json').read_text()))
allowed=previous_paths|{'tools/validate_assets.py','tools/check_adopted_room_provenance.py'}|{str(p.relative_to(source)) for p in dest.rglob('*') if p.is_file()}
actual=set(subprocess.check_output(['git','diff','--name-only',a['base']],cwd=source,text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=source,text=True).splitlines())
assert actual==allowed, {'extra':sorted(actual-allowed),'missing':sorted(allowed-actual)}
env=os.environ.copy(); env['GIT_INDEX_FILE']=str(run/'final.index')
execute(['git','read-tree',a['base']], source, env)
execute(['git','add','--',*sorted(actual)],source,env)
tree=execute(['git','write-tree'],source,env).decode().strip()
patch=execute(['git','diff','--cached','--binary',a['base']],source,env)
(delivery/'changes.patch').write_bytes(patch)
execute(['git','diff','--cached','--check',a['base']],source,env)
diff=execute(['git','diff','--cached','--name-status',a['base']],source,env).decode()
(delivery/'changed-files.txt').write_text(diff)
status={line.split('\t',1)[1]:line.split('\t',1)[0] for line in diff.splitlines()}
assert set(status)==actual and all(s in ['A','M'] for s in status.values())
entries=[]
for path in sorted(actual):
    raw=(source/path).read_bytes(); destfile=delivery/'payload'/path
    destfile.parent.mkdir(parents=True,exist_ok=True); destfile.write_bytes(raw)
    entries.append({'path':path,'status':status[path],'bytes':len(raw),'sha256':sha(raw)})
write(delivery/'changed-files.json',entries)
repo=run/'final-reconstructed'
execute(['git','clone','--shared','--no-checkout',str(source),str(repo)],run)
execute(['git','checkout','--detach',a['base']],repo)
def snapshot(ref):
    result={}
    for item in subprocess.check_output(['git','ls-tree','-r','-z',ref],cwd=repo).split(b'\0'):
        if not item: continue
        metadata,path=item.split(b'\t',1); mode,kind,blob=metadata.decode().split(); assert kind=='blob'
        name=path.decode(); raw=(repo/name).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,name
        result[name]={'mode':mode,'git_blob':blob,'bytes':len(raw),'sha256':sha(raw)}
    return result
baseline=snapshot(a['base'])
assert baseline==json.loads((evidence/'base-all-tracked-sha256.json').read_text())
execute(['git','apply','--check','--index',str(delivery/'changes.patch')],repo)
execute(['git','apply','--index',str(delivery/'changes.patch')],repo)
reconstructed=execute(['git','write-tree'],repo).decode().strip(); assert reconstructed==tree
final=snapshot(tree)
for path,entry in final.items(): assert entry['sha256']==sha((source/path).read_bytes()),path
delta=sorted(path for path,entry in final.items() if path not in pretest or pretest[path]!=entry)
assert all(path==report or path.startswith(prefix+'/') for path in delta),delta
protected=[]
for row in json.loads((repo/'.scope-lock/frozen-files.json').read_text())['files']:
    path=row['path']; actual_sha=final[path]['sha256']
    protected.append({'path':path,'base_sha256':baseline[path]['sha256'],'candidate_sha256':actual_sha,'frozen_sha256':row['sha256'],'match':baseline[path]['sha256']==actual_sha==row['sha256']})
assert len(protected)==26 and all(p['match'] for p in protected)
write(proof_dir/'base-all-tracked-sha256.json',baseline)
write(proof_dir/'candidate-all-tracked-sha256.json',final)
write(proof_dir/'protected-26-sha256.json',protected)
write(proof_dir/'posttest-docs-only-paths.json',delta)
old=[]
for filename,expected,ident in [
    ('task-080-adopted-room-walking-foundation.zip','b96acae544b2cd3a139f248e89f380aa720e666a27f0e38012195d4e8cf63e0c','libfile_5494cd2d160c8191a6db103edeb95af2'),
    ('task-080-timestamped-evidence-20261021T033604Z.zip','07f6d1d5440e94024ff77c0feff4c19655b821ee11e14df42cffe6d79648a429','libfile_7d337407ecd081919857cf57216a86e2')]:
    raw=(w/filename).read_bytes(); assert sha(raw)==expected
    old.append({'file':filename,'library_id':ident,'bytes':len(raw),'sha256':sha(raw),'unchanged':True})
write(proof_dir/'reconstruction.json',{'base_sha':a['base'],'base_tree':'db2d461e2c31b99f909056cf730c453823ab08ae','pretest_tree':a['pretest_tree'],'candidate_tree':tree,'applied_tree':reconstructed,'base_tracked':len(baseline),'candidate_tracked':len(final),'all_physical_blobs_verified':True,'patch_sha256':sha(patch),'commands':records})
write(delivery/'candidate.json',{'base_sha':a['base'],'base_tree':'db2d461e2c31b99f909056cf730c453823ab08ae','source_sha':a['source'],'previous_candidate_tree':a['previous_candidate_tree'],'pretest_tree':a['pretest_tree'],'candidate_tree':tree,'commit_created':False,'github_mutations':False,'files':len(entries),'core_files':sum(not e['path'].startswith('docs/verification/') for e in entries),'evidence_files':sum(e['path'].startswith('docs/verification/') for e in entries),'patch_applies_to_base':True,'applied_tree_equals_candidate':True,'strict_blocker_resolved':True,'strict_images':1159,'room_checks':1191,'room_inputs':1862,'provenance_checks':summary['provenance_checks'],'formal_ci':'未実行・親担当','legacy_coastal':'今回未実行。初回の基点/候補exit124とDictionary error原ログを保持','old_zips':old})
shutil.copyfile(evidence/'REPRODUCE.md',delivery/'REPRODUCE.md')
historical=delivery/'historical-candidate'; historical.mkdir()
shutil.copyfile(w/'delivery/changes.patch',historical/'changes.patch')
shutil.copyfile(w/'delivery/candidate.json',historical/'candidate.json')
with (delivery/'REPRODUCE.md').open('a') as f:
    f.write('\n## 固定前候補の再構成\n\n新検証器は前候補tree `19f0ef9e08b546ad3b9d9143e5b6b97e59ba6d31` と固定PR49のGit objectを参照する。前候補patchも `historical-candidate/changes.patch` に同梱した。基点の別checkoutで `git apply --check --index <historical-candidate/changes.patch>`、`git apply --index <historical-candidate/changes.patch>`、`git write-tree` を実行し、結果が前候補treeと一致することを確認する。最新候補を組む前に同じobject store内で作るか、objectsを共有するcheckoutを使う。PR49固定commitは原リポジトリから読取り取得し、mergeしない。前候補のimportと旧Python検証はこの別checkoutで行う。正式commit作成は不要。\n')
shutil.copyfile(w/'package_approved.py',proof_dir/'package_approved.py')
# 原ログをgzip前のbytesでも提出する。
for p in evidence.rglob('*.log'):
    q=delivery/'raw-logs'/p.relative_to(evidence); q.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(p,q)
manifest={str(p.relative_to(delivery)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(delivery.rglob('*')) if p.is_file()}
write(delivery/'SHA256SUMS.json',manifest)
zip_path=w/('task-080-approved-room-walking-foundation-'+a['stamp']+'.zip')
with zipfile.ZipFile(zip_path,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(delivery.rglob('*')):
        if p.is_file(): z.write(p,str(p.relative_to(delivery)))
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(manifest)+1
    for name,entry in manifest.items():
        raw=z.read(name); assert len(raw)==entry['bytes'] and sha(raw)==entry['sha256'],name
handoff={'zip':str(zip_path),'bytes':zip_path.stat().st_size,'sha256':sha(zip_path.read_bytes()),'base_sha':a['base'],'candidate_tree':tree,'files':len(entries),'manifest_entries':len(manifest),'zip_entries':len(manifest)+1,'reconstructed_tracked':len(final),'old_zips':old,'library_status':'未保存'}
write(run/'handoff.json',handoff)
print(json.dumps(handoff,ensure_ascii=False),flush=True)
