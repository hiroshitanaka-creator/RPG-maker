#!/usr/bin/env python3
"""追加原画と歩行48コマを、今回の記録用Git版で検査する。"""
from pathlib import Path
import argparse, hashlib, io, json, subprocess, sys, tarfile, tempfile
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='6032b9d051d2830e45bab181e91c6e0d9fee2e43'
FINAL_REF='refs/tags/sprint-2-screen-review-2026-09-27'
FINGERPRINT='5ef756796db2a6d3451757a638d62cf12d67734929a43257d0bdca6b3bea4383'

def previous(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

def audit():
    from import_owner_walks import ORIGINAL, ZIP_SHA, ordered_parts, frame
    from validate_assets import check_asset, check_provenance, load_palette
    folder=ROOT/ORIGINAL
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
    assert manifest['archive_sha256']==ZIP_SHA
    originals=manifest['originals'];assert len(originals)==43 and len({r['sha256'] for r in originals})==42
    assert hashlib.sha256(''.join(r['name']+'\t'+r['sha256']+'\n' for r in sorted(originals,key=lambda r:r['name'])).encode()).hexdigest()==FINGERPRINT
    for row in originals:assert hashlib.sha256((folder/row['name']).read_bytes()).hexdigest()==row['sha256']
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));old=json.loads(previous('assets/registry.json'))
    entries={e['path']:e for e in registry['assets']};assert len(entries)==531
    record=json.loads((ROOT/'assets/source_records/owner-walks.json').read_text(encoding='utf8'))
    assert len(record['imported'])==4
    palette=load_palette(ROOT/'assets/palette/natural.gpl');parts={}
    old_records=json.loads(previous('assets/source_records/owner-characters.json'))
    for row in record['imported']:
        image=Image.open(ROOT/row['path']).convert('RGBA')
        assert image.size==(96,192)
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['output_sha256']
        entry=entries[row['path']]
        assert entry['frame']==[32,48] and entry['grid']==[3,4] and entry['max_colors']==16
        assert not check_asset(entry,palette)[0] and not check_provenance(entry)
        bank=np.array(row['palette_colors'],dtype=np.int32)
        expected_bank=next(r['palette_colors'] for r in old_records['imported'] if r['id']==row['id'] and r['pose']=='standing')
        assert bank.tolist()==expected_bank
        assert len(row['frames'])==12 and {(r['row'],r['column']) for r in row['frames']}=={(y,x) for y in range(4) for x in range(3)}
        for item in row['frames']:
            source=item['original_file'];name=Path(source).name
            assert item['mirror'] is False
            assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==item['original_sha256']
            if source not in parts:parts[source]=ordered_parts(ROOT/source,4 if name=='IMG_1042.PNG' else 3,4)
            part,box=parts[source][item['original_slot']];assert list(box)==item['crop']
            actual=image.crop((item['column']*32,item['row']*48,item['column']*32+32,item['row']*48+48))
            assert actual.tobytes()==frame(part,box,row['body_height'],bank).tobytes()
            assert actual.getchannel('A').getbbox()[3]==46
            if row['id']=='owner_young_04' and item['row']==2:assert name=='IMG_1042.PNG' or item['original_slot'] in (7,8)
        for y in range(4):assert len({image.crop((x*32,y*48,x*32+32,y*48+48)).tobytes() for x in range(3)})==3
    for entry in old['assets']:
        assert entries[entry['path']]==entry
        assert (ROOT/entry['path']).read_bytes()==previous(entry['path']),entry['path']
    assert registry['audio']==old['audio'] and registry['defaults']==old['defaults']
    for entry in old['audio']:assert (ROOT/entry['path']).read_bytes()==previous(entry['path'])
    for name in ('base','bright','natural'):
        path=f'assets/palette/{name}.gpl';assert (ROOT/path).read_bytes()==previous(path)
    print('OWNER_WALKS_PASS: originals=43 unique=42 frames=48 replayed=48 ground_y=45 distinct_frames=48 unchanged_images=527 audio=14 palettes=3')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default=FINAL_REF);parser.add_argument('--snapshot',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.snapshot:
        assert '.tools' in ROOT.parts and ROOT.name.startswith('owner-walks-snapshot-');audit();return
    revision=subprocess.run(['git','rev-parse','--verify',args.revision],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()
    raw=subprocess.run(['git','archive','--format=tar',revision],cwd=ROOT,capture_output=True,check=True).stdout
    parent=ROOT/'.tools';parent.mkdir(exist_ok=True);destination=Path(tempfile.mkdtemp(prefix='owner-walks-snapshot-',dir=parent)).resolve()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        for member in archive.getmembers():assert (destination/member.name).resolve().is_relative_to(destination)
        archive.extractall(destination,filter='data')
    print('OWNER_WALKS_FIXED_REVISION: '+revision,flush=True)
    result=subprocess.run([sys.executable,str(destination/'tools/check_owner_walks.py'),'--snapshot'],cwd=destination)
    raise SystemExit(result.returncode)

if __name__=='__main__':main()
