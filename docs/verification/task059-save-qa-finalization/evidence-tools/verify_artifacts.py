"""059保存原archive・全member索引と、旧固定bytesを再照合する。"""
from pathlib import Path
import hashlib,json,subprocess,tarfile
E=Path(__file__).resolve().parents[1];R=E.parents[2];count=0
for row in json.loads((E/'archives.json').read_bytes()):
 p=E/row['archive'];assert p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['raw_sha256'],p
 expected={v['path']:v for v in json.loads((E/row['member_index']).read_bytes())};seen=set()
 with tarfile.open(p) as tar:
  for m in tar:
   if m.isdir():continue
   assert m.isfile() or m.islnk(),m.name
   data=tar.extractfile(m).read();v=expected[m.name]
   assert len(data)==v['size'] and hashlib.sha256(data).hexdigest()==v['sha256'],(p,m.name)
   seen.add(m.name)
 assert seen==set(expected) and len(seen)==row['members'],p
 count+=len(seen)
old=json.loads((E/'unchanged-inventory.json').read_bytes())['files'];paths=list(old)
actual=subprocess.check_output(['git','hash-object','--stdin-paths'],input='\n'.join(paths)+'\n',text=True,cwd=R).splitlines()
assert len(actual)==len(paths)
for path,blob in zip(paths,actual):assert old[path]['git_blob']==blob,path
print('ARTIFACT059_PASS archives='+str(len(json.loads((E/'archives.json').read_bytes())))+' members='+str(count)+' original_blobs='+str(len(paths)))
