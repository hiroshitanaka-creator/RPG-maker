from pathlib import Path
import hashlib,json,tarfile,subprocess,time
root=Path('/workspace/RPG-maker');out=Path('/tmp/qa057/original-archive-audit.json');rows=[];start=time.monotonic()
for folder in ['equipment-save-transaction','equipment-save-transaction-platform']:
 base=root/'docs/verification'/folder
 for row in json.loads((base/'archives.json').read_bytes()):
  path=base/row['archive'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
  index_path=base/row.get('member_index',row['archive'].replace('.tar.gz','-members.json'))
  index=json.loads(index_path.read_bytes())
  if isinstance(index,dict):index=index.get('members',index)
  expected={item.get('path',item.get('name')):item for item in index} if isinstance(index,list) else index
  seen=set()
  with tarfile.open(path,'r:gz') as tar:
   for member in tar:
    if member.isdir():continue
    name=member.name;assert name in expected,(path,name)
    data=member.linkname.encode() if member.issym() else tar.extractfile(member).read()
    item=expected[name];assert hashlib.sha256(data).hexdigest()==item['sha256'],(path,name)
    assert len(data)==item.get('size',item.get('bytes')), (path,name,'size')
    seen.add(name)
  assert seen==set(expected),(path,len(seen),len(expected))
  rows.append({'path':str(path.relative_to(root)),'raw_sha256':row['sha256'],'members':len(seen),'git_blob':subprocess.check_output(['git','rev-parse','HEAD:'+str(path.relative_to(root))],cwd=root,text=True).strip(),'status':'PASS'})
  out.write_text(json.dumps({'status':'RUNNING','archives':rows},indent=2)+'\n')
out.write_text(json.dumps({'status':'PASS','archives':rows,'seconds':time.monotonic()-start},indent=2)+'\n');print('ARCHIVES_PASS',len(rows),sum(r['members'] for r in rows))
