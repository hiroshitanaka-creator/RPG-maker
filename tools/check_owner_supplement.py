#!/usr/bin/env python3
"""敵3体と船原画の追加を、その作業の最終Git版に固定して検査する。"""
from pathlib import Path
import argparse, hashlib, io, json, subprocess, sys, tarfile, tempfile
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='e2e1c3bcd7d15b964951a853eb938e97658d5eb5'
FINAL_REF='refs/tags/sprint-0-supplement-2026-09-27'
ORIGINAL='assets/_incoming/owner-2026-09-26/supplement-2026-09-27/'
SOURCE_HASHES={
    '1-写真1.jpg':'8d94d211feca3694d17e978ec84ceec88e89945c8f7b5746456dd4a78480530e',
    '2-写真2.jpg':'d0a39feaa54da13d07249ab248d1325e7586427b5304287fc9fd6eacb5c4156e',
    '3-写真3.jpg':'566cb733bb8ec639a680468fbd8fb2a01ea4e0297d7b71df372543287fb86a44',
}

def previous(path):
    return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

def audit():
    from import_owner_monsters import split_parts
    from import_owner_supplement import render, DEFINITIONS
    from validate_assets import load_palette, check_asset, check_provenance
    record=json.loads((ROOT/'assets/source_records/owner-supplement.json').read_text(encoding='utf8'))
    assert len(record['imported'])==3 and len(record['sources'])==3
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    old=json.loads(previous('assets/registry.json'))
    entries={e['path']:e for e in registry['assets']}
    assert len(entries)==len(registry['assets'])==409
    palette=load_palette(ROOT/'assets/palette/natural.gpl')
    for r in record['sources']:
        raw=(ROOT/r['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==r['sha256']==SOURCE_HASHES[Path(r['path']).name]
    assert [(r['logical_id'],Path(r['path']).name) for r in record['sources']]==[('IMG_0973','1-写真1.jpg'),('IMG_0974','3-写真3.jpg'),('IMG_0975','2-写真2.jpg')]
    parts=split_parts(Image.open(ROOT/(ORIGINAL+'1-写真1.jpg')),3)
    for i,(r,(part,box),definition) in enumerate(zip(record['imported'],parts,DEFINITIONS),1):
        id_,_,category,extent,canvas=definition
        assert r['id']==id_ and r['slot']==i and r['crop']==list(box)
        assert r['size_class']==category and r['target_extent']==extent
        actual=Image.open(ROOT/r['path']).convert('RGBA')
        assert actual.size==(canvas,canvas) and actual.tobytes()==render(part,box,extent,canvas).tobytes()
        assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['output_sha256']
        a=np.array(actual);colors=set(map(tuple,a[:,:,:3][a[:,:,3]>0]))
        assert len(colors)<=32 and colors<=palette and set(np.unique(a[:,:,3]))=={0,255}
        b=actual.getchannel('A').getbbox();visible=[b[2]-b[0],b[3]-b[1]]
        assert max(visible)==extent and visible==r['visible_size']
        assert not check_asset(entries[r['path']],palette)[0] and not check_provenance(entries[r['path']])
    changed={r['path'] for r in record['imported']}
    unchanged=0
    for e in old['assets']:
        if e['path'] not in changed:
            assert entries[e['path']]==e and (ROOT/e['path']).read_bytes()==previous(e['path']),e['path']
            unchanged+=1
    assert unchanged==406
    assert registry['audio']==old['audio'] and registry['defaults']==old['defaults']
    files=subprocess.run(['git','ls-tree','--full-tree','-r','--name-only',BASE],cwd=ROOT,capture_output=True,check=True).stdout.decode().splitlines()
    fixed=[p for p in files if p.startswith(('scripts/','scenes/','world/','data/','test/','addons/','.scope-lock/','.github/','assets/palette/','assets/audio/','assets/_incoming/','docs/reference/','docs/verification/art-review/')) or p in ('AGENTS.md','project.godot','docs/experience-spec-v2.md','docs/asset-spec.md','tools/check_owner_monsters.py','tools/check_size_rock_review.py','tools/check_visual_target_assets.py','tools/validate_assets.py','tools/smoke_first_region.gd','tools/smoke_chapter1.gd')]
    assert fixed
    for p in fixed: assert (ROOT/p).read_bytes()==previous(p),p
    text=(ROOT/'docs/roadmap-v2.md').read_text(encoding='utf8')
    assert 'ゲームの題名（物語の細部が決まった後に決める）' in text
    assert '形は鷲の頭と翼を持つ空飛ぶ船に決定（2026年9月26日）' in text
    print(f'OWNER_SUPPLEMENT_PASS: originals=3 replaced=3 replayed=3 other_images={unchanged} fixed_files={len(fixed)} boats_converted=0')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default=FINAL_REF);parser.add_argument('--snapshot',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.snapshot:
        assert '.tools' in ROOT.parts and ROOT.name.startswith('owner-supplement-snapshot-');audit();return
    revision=subprocess.run(['git','rev-parse','--verify',args.revision],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()
    raw=subprocess.run(['git','archive','--format=tar',revision],cwd=ROOT,capture_output=True,check=True).stdout
    parent=ROOT/'.tools';parent.mkdir(exist_ok=True)
    destination=Path(tempfile.mkdtemp(prefix='owner-supplement-snapshot-',dir=parent)).resolve()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
        for member in tar.getmembers(): assert (destination/member.name).resolve().is_relative_to(destination)
        tar.extractall(destination,filter='data')
    print('OWNER_SUPPLEMENT_FIXED_REVISION: '+revision,flush=True)
    result=subprocess.run([sys.executable,str(destination/'tools/check_owner_supplement.py'),'--snapshot'],cwd=destination)
    raise SystemExit(result.returncode)

if __name__=='__main__': main()
