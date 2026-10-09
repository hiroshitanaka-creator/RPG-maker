"""実行済み059原物を追加保存。旧archiveを上書きせず全member hashを照合する。"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import tarfile

E=Path(__file__).resolve().parents[1]

def sha(raw):return hashlib.sha256(raw).hexdigest()

def index(path):
    rows=[]
    with tarfile.open(path) as tar:
        for member in tar:
            if member.isdir():continue
            assert member.isfile() or member.islnk(),member.name
            raw=tar.extractfile(member).read()
            rows.append(dict(path=member.name,size=len(raw),sha256=sha(raw)))
    return rows

def main(a):
    path=E/(a.name+'.tar.gz');assert not path.exists(),path
    meta={'kind':a.kind}
    if a.log:
        rawlog=Path(a.log).read_bytes();lines=rawlog.decode().splitlines()
        declaration=next(json.loads(line.split('NATIVE_RAW_PROOF_META ',1)[1]) for line in lines if 'NATIVE_RAW_PROOF_META ' in line)
        raw=base64.b64decode(''.join(line.split('NATIVE_RAW_PROOF_DATA ',1)[1].strip() for line in lines if 'NATIVE_RAW_PROOF_DATA ' in line))
        assert len(raw)==declaration['archive_bytes'] and sha(raw)==declaration['archive_sha256']
        path.write_bytes(raw)
        meta.update(declaration,decoded_text_sha256=sha(rawlog),head_sha=a.head,run_id=a.run,job_id=a.job)
    else:
        folder=Path(a.folder)
        with tarfile.open(path,'w:gz',compresslevel=9) as tar:
            for p in sorted(folder.rglob('*')):
                if not p.is_file() or p.is_symlink() or p.suffix=='.index':continue
                tar.add(p,arcname=p.relative_to(folder).as_posix(),recursive=False)
            for p in map(Path,a.extra):tar.add(p,arcname='wrapper/'+p.name,recursive=False)
        meta.update(code_sha=a.head)
    members=index(path)
    if a.log:assert len(members)==meta['members']
    (E/(a.name+'-members.json')).write_text(json.dumps(members,indent=2)+'\n')
    meta.update(raw_sha256=sha(path.read_bytes()),bytes=path.stat().st_size,members=len(members))
    (E/(a.name+'-meta.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    rows=json.loads((E/'archives.json').read_bytes())
    rows.append(dict(archive=path.name,raw_sha256=meta['raw_sha256'],bytes=meta['bytes'],members=len(members),member_index=a.name+'-members.json',kind=a.kind))
    (E/'archives.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(meta,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--kind',required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--log');g.add_argument('--folder');p.add_argument('--extra',action='append',default=[]);p.add_argument('--head');p.add_argument('--run',type=int);p.add_argument('--job',type=int);main(p.parse_args())
