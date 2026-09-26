#!/usr/bin/env python3
"""原本・変換・今回以外の素材の不変性を実ファイルで検査する。"""
from pathlib import Path
import io,json,hashlib,copy,subprocess,argparse,sys,tarfile,tempfile
import numpy as np
from PIL import Image
from validate_assets import load_palette,check_asset,check_provenance

ROOT=Path(__file__).resolve().parents[1]
FINAL_REF='refs/tags/sprint-0-owner-monsters-2026-09-26-final'

def digest(data):return hashlib.sha256(data).hexdigest()

def audit_snapshot():
    from import_owner_monsters import ORIGINAL,OUT,BASE,NOTICE,REPLACEMENTS,SHEETS,split_parts,convert,git_bytes
    record=json.loads((ROOT/'assets/source_records/owner-monsters.json').read_text(encoding='utf8'))
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));entries={e['path']:e for e in registry['assets']}
    manifest=json.loads((ORIGINAL/'manifest.json').read_text(encoding='utf8'));assert len(manifest['files'])==36
    for row in manifest['files']:
        path=ORIGINAL/row['file'];assert digest(path.read_bytes())==row['sha256'],str(path)
    imported=record['imported'];assert len(imported)==102 and len({r['source_id'] for r in imported})==102
    assert len({r['path'] for r in imported})==102
    assert record['baseline']==BASE
    palette=load_palette(ROOT/'assets/palette/natural.gpl');parts={};replayed=0;rejections=0
    for row in imported:
        path=row['path'];e=entries[path];original=ROOT/row['original_file'];number=int(original.stem[4:])
        assert digest(original.read_bytes())==row['original_sha256']
        assert e['source']=='owner' and e['author']=='依頼者' and e['license']=='LicenseRef-Owner-Provided'
        assert e['provided_at']=='2026-09-26' and e['original_file']==row['original_file'] and e['modified']
        assert not check_provenance(e)
        errors,exists=check_asset(e,palette);assert exists and not errors,errors
        assert e['size']==row['size'] and all(n%32==0 for n in e['size'])
        w,h=e['size'];limit=(192,160) if e['monster_tier']=='boss' else (96,96)
        assert 64<=w<=limit[0] and 64<=h<=limit[1]
        a=np.array(Image.open(ROOT/path).convert('RGBA'));assert set(np.unique(a[:,:,3]))=={0,255}
        colors=set(map(tuple,a[:,:,:3][a[:,:,3]>0]));assert len(colors)<=32 and colors<=palette
        assert e['facing'] in ('front','right') and row['mirror']==(row['original_facing']=='L')
        assert np.any(a[:,:,3]) and np.all(a[0,:,3]==0) and np.all(a[-1,:,3]==0)
        assert digest((ROOT/path).read_bytes())==row['output_sha256']
        if str(original) not in parts:parts[str(original)]=split_parts(Image.open(original).convert('RGBA'),len(SHEETS[number].split(';')),row['black_threshold'])
        part,box=parts[str(original)][row['slot']-1];assert list(box)==row['crop']
        expected=convert(part,box,row['size'],row['mirror']);assert expected.tobytes()==a.tobytes(),path;replayed+=1
        if 'droplet' in row['source_id'] or row['source_id'] in ('blue_water_blob','gold_block_golem'):assert e.get('note')==NOTICE
        broken=copy.deepcopy(e);del broken['original_file'];assert check_provenance(broken);rejections+=1
    changed={f'assets/monsters/{id_}/idle.png' for id_,(source,_) in REPLACEMENTS.items() if source}
    assert len(changed)==19
    old=json.loads(git_bytes('assets/registry.json'));unchanged=0
    for e in old['assets']:
        path=e['path']
        if path in changed:assert git_bytes(path)!=(ROOT/path).read_bytes(),path
        else:assert git_bytes(path)==(ROOT/path).read_bytes(),path;unchanged+=1
    assert unchanged==302
    frozen=['assets/palette/base.gpl','assets/palette/bright.gpl','assets/palette/natural.gpl','docs/verification/art-review/party-design-sheet.png']+[f'docs/verification/art-review/source/pc_{i:02}_design.png' for i in range(1,5)]+[e['path'] for e in old['audio']]
    for path in frozen:assert git_bytes(path)==(ROOT/path).read_bytes(),path
    assert registry['audio']==old['audio']
    held={(r['original_file'],r['slot']) for r in record['held_back']}
    for row in imported:
        assert (row['original_file'],row['slot']) not in held and (row['original_file'],'all') not in held
    assert all(not e['path'].startswith('assets/_incoming/') for e in registry['assets'])
    imported_paths={r['path'] for r in imported}
    assert {e['path'] for e in registry['assets'] if e.get('source')=='owner'}==imported_paths
    assert sum(e['status']=='optional' for e in registry['assets'] if e.get('source')=='owner')==83
    # ゲーム処理・敵定義・既存の保護範囲を変更していないことも比較する。
    paths=subprocess.run(['git','ls-tree','--full-tree','-r','--name-only',BASE],cwd=ROOT,capture_output=True,check=True).stdout.decode().splitlines()
    protected=[p for p in paths if p.startswith(('scripts/','scenes/','world/','data/','test/','addons/','.scope-lock/','.github/')) or p in ('project.godot','tools/smoke_first_region.gd','tools/smoke_chapter1.gd','docs/first-region-acceptance.md')]
    # 両方ともGitの保存内容を読むため、Windowsの作業ツリーの改行変換に依存しない。
    for path in protected:assert git_bytes(path)==(ROOT/path).read_bytes(),path
    # 今回の岩壁がすべての床境界から64pxぶん存在し、内柱へも同じ規則がかかる。
    from build_owner_cave import expand
    cave=ROOT/'docs/verification/art-review-2'
    floor=np.array(Image.open(cave/'floor-mask.png'),bool);wall=np.array(Image.open(cave/'wall-mask.png'),bool)
    assert np.array_equal(wall,expand(floor,64)&~floor)
    top=np.array(Image.open(cave/'wall-top-mask.png'),bool);side=np.array(Image.open(cave/'wall-side-mask.png'),bool)
    assert np.array_equal(side,expand(floor,32)&~floor) and np.array_equal(top,wall&~side)
    measured=json.loads((cave/'cave-revision-checks.json').read_text());assert measured['side_luma']>measured['top_luma']
    for i in range(1,4):
        lake=np.array(Image.open(cave/f'lake-{i}-mask.png'),bool);y,x=np.where(lake)
        assert lake.sum()/((x.max()-x.min()+1)*(y.max()-y.min()+1))<.9
    result=dict(originals=36,imported=len(imported),replayed=replayed,replaced=19,retained=3,optional=83,held_records=len(held),unchanged_existing_images=unchanged,unchanged_palettes=3,unchanged_audio=14,unchanged_party_designs=5,protected_files=len(protected),provenance_missing_rejected=rejections,cave_wall_depth_px=64,organic_lakes=3)
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f'OWNER_MONSTERS_PASS: originals=36 imported=102 replayed={replayed} replaced=19 retained=3 optional=83')
    print(f'OWNER_UNCHANGED_PASS: existing_images=302 palettes=3 audio=14 party_designs=5 protected_files={len(protected)}')
    print(f'OWNER_PROVENANCE_PASS: missing_original_rejected={rejections} held_registered=0')
    print('OWNER_CAVE_PASS: wall_depth=64 side=32 top=32 organic_lakes=3')

def main():
    parser=argparse.ArgumentParser(description='固定したGit版を展開し、スプリント0の素材を検査する')
    parser.add_argument('--revision',default=FINAL_REF,help='既定はスプリント最終コミットの固定タグ。作業中は不変のGit tree IDを指定可能')
    parser.add_argument('--snapshot',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.snapshot:
        assert '.tools' in ROOT.parts and ROOT.name.startswith('owner-snapshot-')
        audit_snapshot();return
    revision=subprocess.run(['git','rev-parse','--verify',args.revision],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()
    archive=subprocess.run(['git','archive','--format=tar',revision],cwd=ROOT,capture_output=True,check=True).stdout
    parent=(ROOT/'.tools').resolve();parent.mkdir(exist_ok=True)
    snapshot=Path(tempfile.mkdtemp(prefix='owner-snapshot-',dir=parent)).resolve()
    assert snapshot.is_relative_to(parent)
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:
        for member in tar.getmembers():assert (snapshot/member.name).resolve().is_relative_to(snapshot)
        tar.extractall(snapshot,filter='data')
    print('OWNER_FIXED_REVISION: '+revision,flush=True)
    completed=subprocess.run([sys.executable,str(snapshot/'tools/check_owner_monsters.py'),'--snapshot'],cwd=snapshot,check=False)
    # 検査に使った不変スナップショットと結果は.tools内へ残す。作業ツリーを書き換えない。
    print('OWNER_SNAPSHOT: '+str(snapshot),flush=True)
    raise SystemExit(completed.returncode)

if __name__=='__main__':main()
