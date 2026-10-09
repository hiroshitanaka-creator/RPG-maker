"""059の実行済み原物だけを追加archiveにする。旧archiveを上書きしない。"""
from pathlib import Path
import hashlib,json,tarfile,shutil
E=Path(__file__).resolve().parents[1];T=Path('/tmp/qa059');rows=json.loads((E/'archives.json').read_bytes())
def package(name,folder):
 path=E/(name+'.tar.gz');assert not path.exists();members=[]
 with tarfile.open(path,'w:gz',compresslevel=9) as tar:
  for p in sorted(folder.rglob('*')):
   if not p.is_file() or p.is_symlink() or p.suffix=='.index':continue
   rel=p.relative_to(folder)
   if any(x in {'profile','legacy053','bin','.godot','propagation'} for x in rel.parts):continue
   raw=p.read_bytes();members.append(dict(path=rel.as_posix(),size=len(raw),sha256=hashlib.sha256(raw).hexdigest()));tar.add(p,arcname=rel.as_posix(),recursive=False)
 idx=E/(name+'-members.json');idx.write_text(json.dumps(members,indent=2)+'\n')
 rows.append(dict(archive=path.name,raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,members=len(members),member_index=idx.name,kind='059 local 原bytes、現在全取引の成功とは分離'))
for name,folder in [('local-full-9d4-failure',T/'full-run'),('local-regression-7f4',T/'regression-logs'),('local-primitives-9d4',T/'primitives-run'),('local-propagation-059',T/'propagation-baseline')]:package(name,folder)
for name in ['ci-first-fixed057-windows']:
 meta=json.loads((E/(name+'-meta.json')).read_bytes());rows.append(dict(archive=name+'.tar.gz',raw_sha256=meta['archive_sha256'],bytes=meta['archive_bytes'],members=meta['members'],member_index=name+'-members.json',kind='057固定・初回9d4 CI原archive、現059の成功ではない'))
(E/'archives.json').write_text(json.dumps(rows,indent=2)+'\n')
for src in ['regressions.py','propagation.py','check_source.py']:
 shutil.copyfile(T/src,E/'evidence-tools'/src)
shutil.copyfile(T/'engine/engine.json',E/'engine-linux.json')
print('追加原archive',len(rows))
