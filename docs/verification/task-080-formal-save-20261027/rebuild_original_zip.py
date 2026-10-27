"""Git保存された原bytesとZIP属性から原ZIPを再構成する。既存出力は上書きしない。"""
from pathlib import Path
import argparse,json,zipfile,gzip,hashlib
p=argparse.ArgumentParser();p.add_argument('repository');p.add_argument('output');a=p.parse_args();repo=Path(a.repository)
meta=json.loads((repo/'docs/verification/task-080-formal-save-20261027/original-archive-map.json').read_text())
with zipfile.ZipFile(a.output,'x',zipfile.ZIP_DEFLATED,compresslevel=meta['compression_level']) as z:
 for row in meta['members']:
  raw=(repo/row['repository_path']).read_bytes()
  if row['codec']=='gzip':raw=gzip.decompress(raw)
  assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['member']
  zi=zipfile.ZipInfo(row['member'],tuple(row['zip_info']['date_time']))
  for k,v in row['zip_info'].items():
   if k=='date_time':continue
   setattr(zi,k,bytes.fromhex(v) if k in ['extra','comment'] else v)
  z.writestr(zi,raw,compresslevel=meta['compression_level'])
out=Path(a.output);actual=hashlib.sha256(out.read_bytes()).hexdigest();assert out.stat().st_size==meta['bytes'] and actual==meta['sha256'],actual
print(json.dumps({'bytes':out.stat().st_size,'sha256':actual,'original_zip_byte_identical':True}))
