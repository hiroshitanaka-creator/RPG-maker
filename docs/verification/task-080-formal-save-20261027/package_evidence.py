from pathlib import Path
import json,zipfile,hashlib,gzip
r=Path(__file__).resolve().parent;repo=r/'repo';dest=repo/'docs/verification/task-080-formal-save-20261027';dest.mkdir();(dest/'.gdignore').write_text('')
zpath=Path('/workspace/task080/task-080-approved-room-walking-foundation-20261021T035317Z.zip');rows=[]
with zipfile.ZipFile(zpath) as z:
 for info in z.infolist():
  raw=z.read(info.filename)
  if info.filename.startswith('payload/'):
   mapped=info.filename[len('payload/'):];assert (repo/mapped).read_bytes()==raw;codec='raw'
  else:
   target=dest/'original-package'/info.filename
   codec='gzip' if target.suffix in ['.log','.patch'] else 'raw'
   if codec=='gzip':target=target.with_name(target.name+'.gz')
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(gzip.compress(raw,mtime=0) if codec=='gzip' else raw);mapped=str(target.relative_to(repo))
  zi={k:getattr(info,k) for k in ['create_system','create_version','extract_version','reserved','flag_bits','volume','internal_attr','external_attr','compress_type']};zi.update(date_time=list(info.date_time),extra=info.extra.hex(),comment=info.comment.hex())
  rows.append({'member':info.filename,'repository_path':mapped,'codec':codec,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'zip_info':zi})
meta={'archive':zpath.name,'bytes':zpath.stat().st_size,'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'members':rows,'compression_level':6}
(dest/'original-archive-map.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('all original ZIP members represented:',len(rows))
