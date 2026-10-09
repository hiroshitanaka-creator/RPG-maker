from pathlib import Path
import hashlib,json,tarfile,subprocess,shutil
R=Path('/workspace/RPG-maker'); T=Path('/tmp/qa057'); E=R/'docs/verification/task057-save-qa-diagnostics';E.mkdir(exist_ok=True)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def package(name,items):
 paths=[]
 for src,prefix in items:
  src=T/src
  candidates=[src] if src.is_file() else sorted(src.rglob('*'))
  for p in candidates:
   rel=Path(p.name) if src.is_file() else p.relative_to(src)
   if any(x in {'profile','.godot','legacy053','bin','propagation','template'} for x in rel.parts):continue
   if p.is_symlink() or not p.is_file() or p.suffix=='.index':continue
   paths.append((p,str(Path(prefix)/rel)))
 rows=[];dest=E/(name+'.tar.gz')
 with tarfile.open(dest,'w:gz',compresslevel=9) as tar:
  for p,rel in paths:
   raw=p.read_bytes();rows.append(dict(path=rel,size=len(raw),sha256=digest(raw)));tar.add(p,arcname=rel,recursive=False)
 write(E/(name+'-members.json'),rows)
 return dict(archive=dest.name,sha256=digest(dest.read_bytes()),bytes=dest.stat().st_size,members=len(rows),member_index=name+'-members.json',kind='057 local evidence archive')
archives=[]
archives.append(package('local-capture-final',[('capture-shutdown-final','capture-tests'),('scope-final-code.json','scope/code'),('scope057','scope'),('repro.json','before'),('before.py','before'),('reproduce.py','before'),('fake-engine','before')]))
archives.append(package('local-regression',[('regression-logs','regression'),('regressions.py','procedure')]))
archives.append(package('local-propagation',[('propagation-baseline','propagation'),('propagation.py','procedure')]))
archives.append(package('local-primitives',[('local-primitives','primitives'),('local-primitives-wrapper.log','wrapper')]))
archives.append(package('local-full-first',[('local-full','first-import-failure'),('local-full-retry','full-retry'),('local-full-retry-wrapper.log','wrapper'),('local-full-wrapper.log','wrapper')]))
if (T/'local-code-final/commands.json').exists():archives.append(package('local-full-code-final',[('local-code-final','full'),('local-code-final-wrapper.log','wrapper')]))
for stem,log in [('ci-first-linux-fixed-verified','ci-first-linux-fixed.log'),('ci-first-linux-latest-verified','ci-job-113777947342.log'),('ci-first-windows-fixed-verified','ci-job-113777947727.log'),('ci-first-windows-latest-verified','ci-first-windows-latest.log')]:
 folder=T/stem;label=stem.replace('-verified',''); shutil.copyfile(folder/'raw-proof.tar.gz',E/(label+'.tar.gz'));shutil.copyfile(folder/'members.json',E/(label+'-members.json'));shutil.copyfile(folder/'archive-meta.json',E/(label+'-meta.json'));shutil.copyfile(folder/'summary.json',E/(label+'-summary.json'))
 meta=json.loads((folder/'archive-meta.json').read_bytes());archives.append(dict(archive=label+'.tar.gz',sha256=meta['archive_sha256'],bytes=meta['archive_bytes'],members=meta['members'],member_index=label+'-members.json',kind='CI original raw proof recovered from base64 job log'))
 # Decoded connector text is separate from original archive bytes.
 archives.append(package(label+'-decoded-log',[(log,'decoded-log')]))
for stem in ['ci-code-linux-fixed-verified','ci-code-linux-latest-verified','ci-code-windows-fixed-verified','ci-code-windows-latest-verified','ci-code-linux-primitives-verified','ci-code-windows-primitives-verified']:
 folder=T/stem
 if not (folder/'raw-proof.tar.gz').exists():continue
 label=stem.replace('-verified','')
 for old,new in [('raw-proof.tar.gz',label+'.tar.gz'),('members.json',label+'-members.json'),('archive-meta.json',label+'-meta.json'),('summary.json',label+'-summary.json')]:shutil.copyfile(folder/old,E/new)
 meta=json.loads((folder/'archive-meta.json').read_bytes());archives.append(dict(archive=label+'.tar.gz',sha256=meta['archive_sha256'],bytes=meta['archive_bytes'],members=meta['members'],member_index=label+'-members.json',kind='CI original raw proof recovered from base64 job log'))
archives.append(package('ci-code-decoded-logs',[(p.name,'decoded-log') for p in sorted(T.glob('code-job-*.log'))]))
write(E/'archives.json',archives)
for src in ['original-archive-audit.json','artifact-download-result.json','scope-final-code.json']:
 shutil.copyfile(T/src,E/src)
helpers=E/'evidence-tools';helpers.mkdir(exist_ok=True)
for src in ['decode_ci.py','audit_archives.py','package_evidence.py','propagation.py','regressions.py']:
 shutil.copyfile(T/src,helpers/src)
write(E/'code-inventory.json',dict(code_sha='b4ee1ea28864fc2a081647b063ef1b11030d9fec',inventory=json.loads((T/'scope-final-code.json').read_bytes())['inventory']))
print(json.dumps({'archives':len(archives),'bytes':sum(x['bytes'] for x in archives)}))
