#!/usr/bin/env python3
"""専用CIの原bytesをarchive化。artifact取得不能時もjob logから同hashで復元可。"""
import argparse,base64,hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main(args):
    area=Path(args.output).resolve();archive=area/'raw-proof.tar.gz';members=[]
    paths=[]
    for base,prefix in [(area,'evidence'),(ROOT/'addons/equipment_save_io','distribution')]:
        for path in sorted(base.rglob('*')):
            relative=path.relative_to(base)
            if any(part in ['profile','legacy053','.godot','bin','propagation'] for part in relative.parts) and prefix=='evidence':continue
            if 'scope' in relative.parts and path.suffix!='.log':continue
            if path.name.startswith('Godot_') or path.name in ['raw-proof.tar.gz','raw-proof-members.json']:continue
            if not path.is_file() or path.is_symlink():continue
            paths.append((path,prefix+'/'+relative.as_posix()))
    with tarfile.open(archive,'w:gz',compresslevel=9) as tar:
        for path,name in paths:
            raw=path.read_bytes();members.append({'path':name,'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()});tar.add(path,arcname=name,recursive=False)
    (area/'raw-proof-members.json').write_text(json.dumps(members,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raw=archive.read_bytes();meta={'archive_sha256':hashlib.sha256(raw).hexdigest(),'archive_bytes':len(raw),'members':len(members)}
    print('NATIVE_RAW_PROOF_META '+json.dumps(meta),flush=True)
    print('NATIVE_RAW_PROOF_BEGIN',flush=True)
    encoded=base64.b64encode(raw).decode()
    for offset in range(0,len(encoded),8192):print('NATIVE_RAW_PROOF_DATA '+encoded[offset:offset+8192],flush=True)
    print('NATIVE_RAW_PROOF_END',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);main(p.parse_args())
