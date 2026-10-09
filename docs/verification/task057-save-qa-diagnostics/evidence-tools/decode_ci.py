from pathlib import Path
import argparse,base64,hashlib,json,re,tarfile,io
p=argparse.ArgumentParser();p.add_argument('log');p.add_argument('output');a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
raw=Path(a.log).read_bytes();text=raw.decode('utf-8');meta=json.loads(re.search(r'NATIVE_RAW_PROOF_META (\{[^\n]+\})',text)[1]);chunks=re.findall(r'NATIVE_RAW_PROOF_DATA ([A-Za-z0-9+/=]+)',text);proof=base64.b64decode(''.join(chunks),validate=True)
assert hashlib.sha256(proof).hexdigest()==meta['archive_sha256'] and len(proof)==meta['archive_bytes']
(out/'raw-proof.tar.gz').write_bytes(proof);members=[]
with tarfile.open(fileobj=io.BytesIO(proof),mode='r:gz') as tar:
 for member in tar:
  assert (member.isfile() or member.islnk()) and not member.name.startswith('/') and '..' not in Path(member.name).parts
  data=tar.extractfile(member).read();members.append(dict(path=member.name,size=len(data),sha256=hashlib.sha256(data).hexdigest()))
  path=out/member.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
assert len(members)==meta['members']
(out/'members.json').write_text(json.dumps(members,ensure_ascii=False,indent=2)+'\n');(out/'archive-meta.json').write_text(json.dumps(dict(meta,decoded_job_log_utf8_sha256=hashlib.sha256(raw).hexdigest(),original_job_log_byte_hash='未取得: connector decoded text',all_members_verified=True),indent=2)+'\n')
summary={}
for name in ['results/summary.json','commands.json','task057/execution.json','task057/measurements/diagnostics.json','extra/summary.json','build/build.json']:
 path=out/'evidence'/name
 if path.exists():
  value=json.loads(path.read_bytes())
  summary[name]={'status':value.get('status'),'case_count':value.get('case_count'),'checks':value.get('checks'),'seconds':value.get('seconds')} if isinstance(value,dict) else [(r.get('name'),r.get('seconds'),r.get('exit_code')) for r in value]
  if isinstance(value,dict) and 'failures' in value:summary[name]['failures']=value['failures'][:3]
manifest=out/'evidence/results/sha256.json'
if manifest.exists():
 for path,expected in json.loads(manifest.read_bytes()).items():assert hashlib.sha256((manifest.parent/path).read_bytes()).hexdigest()==expected
 summary['manifest']='PASS'
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(meta,summary=summary),ensure_ascii=False))
