#!/usr/bin/env python3
"""体格差と岩壁の修正を、固定したGit版で検査する。過去の検査は変更しない。"""
from pathlib import Path
import argparse,copy,hashlib,io,json,subprocess,sys,tarfile,tempfile
import numpy as np
from collections import Counter
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='883af5e7aa563bcf59155c00137834c697eac153'
FINAL_REF='refs/tags/sprint-0-size-rock-review-2026-09-27'

def previous(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout
def rgba(data):return np.array(Image.open(io.BytesIO(data)).convert('RGBA'))

def terrain_layer(document,read):
    result=np.zeros((document['height']*32,document['width']*32,4),np.uint8);cache={}
    for x,y,id_ in document['layers'][0]['cells']:
        tile=document['tiles'][id_];p=tile['path']
        if p not in cache:cache[p]=rgba(read(p))
        sx,sy,w,h=tile['region'];assert w==h==32
        result[y*32:y*32+32,x*32:x*32+32]=cache[p][sy:sy+32,sx:sx+32]
    return result

def audit():
    from import_owner_monsters import SHEETS,split_parts
    from resize_owner_monsters import sized_image
    from validate_assets import check_asset,check_provenance,load_palette
    from build_owner_cave import expand
    record=json.loads((ROOT/'assets/source_records/owner-monsters-size-review.json').read_text(encoding='utf8'))
    old=json.loads(previous('assets/registry.json'));new=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));entries={e['path']:e for e in new['assets']}
    assert len(record['imported'])==102 and len({r['id'] for r in record['imported']})==102
    palette=load_palette(ROOT/'assets/palette/natural.gpl');parts={};sizes={};replayed=0
    limits={'small':(48,64),'medium':(64,80),'large':(96,96),'boss':(128,192)}
    for row in record['imported']:
        e=entries[row['path']];a=rgba((ROOT/row['path']).read_bytes());im=Image.fromarray(a);b=im.getchannel('A').getbbox();assert b
        visible=[b[2]-b[0],b[3]-b[1]];low,high=limits[row['size_class']]
        assert low<=max(visible)<=high,(row['id'],visible)
        assert visible==row['visible_size']==e['visible_size'] and e['size_class']==row['size_class']
        assert list(im.size)==row['size']==e['size'] and all(n%32==0 for n in im.size)
        cap=(192,160) if row['size_class']=='boss' else (96,96)
        assert im.width<=cap[0] and im.height<=cap[1]
        colors=set(map(tuple,a[:,:,:3][a[:,:,3]>0]));assert len(colors)<=32 and colors<=palette
        assert set(np.unique(a[:,:,3]))=={0,255}
        assert not check_asset(e,palette)[0] and not check_provenance(e)
        source=row['original_file'];raw=(ROOT/source).read_bytes();assert raw==previous(source)
        assert hashlib.sha256(raw).hexdigest()==row['original_sha256']
        if source not in parts:
            number=int(Path(source).stem[4:]);parts[source]=split_parts(Image.open(io.BytesIO(raw)),len(SHEETS[number].split(';')),row['black_threshold'])
        part,box=parts[source][row['slot']-1];assert list(box)==row['crop']
        expected,category,extent=sized_image(part,box,row)
        assert expected.tobytes()==a.tobytes() and category==row['size_class'] and extent==row['target_extent']
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['output_sha256']
        sizes[row['id']]=visible;replayed+=1
    assert max(sizes['slime'])==48 and max(sizes['shadow_wolf'])==80
    assert sizes['slime'][0]*sizes['slime'][1]<sizes['shadow_wolf'][0]*sizes['shadow_wolf'][1]
    allowed={r['path'] for r in record['imported']}|{f'assets/tiles/cave_{n}.png' for n in ('wall_top','wall_side','thick_wall_autotile')}
    unchanged=0
    for e in old['assets']:
        if e['path'] not in allowed:assert previous(e['path'])==(ROOT/e['path']).read_bytes(),e['path'];unchanged+=1
    assert unchanged==304
    for id_ in ('bone_bat','glacier_turtle','zombie_wolf'):
        p=f'assets/monsters/{id_}/idle.png';assert previous(p)==(ROOT/p).read_bytes()
    files=subprocess.run(['git','ls-tree','--full-tree','-r','--name-only',BASE],cwd=ROOT,capture_output=True,check=True).stdout.decode().splitlines()
    fixed=[p for p in files if p.startswith(('scripts/','scenes/','world/','data/','test/','addons/','.scope-lock/','.github/','assets/_incoming/owner-2026-09-26/','assets/palette/','assets/audio/','docs/verification/art-review/source/')) or p in ('AGENTS.md','project.godot','docs/experience-spec-v2.md','docs/roadmap-v2.md','docs/asset-spec.md','docs/verification/art-review/party-design-sheet.png','tools/check_owner_monsters.py','tools/check_visual_target_assets.py','tools/validate_assets.py','tools/check_build_identity.py','tools/smoke_first_region.gd','tools/smoke_chapter1.gd')]
    for p in fixed:assert previous(p)==(ROOT/p).read_bytes(),p
    cave='docs/verification/art-review-2/'
    for name in ('floor-mask','wall-mask','wall-top-mask','wall-side-mask','lake-1-mask','lake-2-mask','lake-3-mask'):
        p=cave+name+'.png';assert previous(p)==(ROOT/p).read_bytes(),p
    masks={n:np.array(Image.open(ROOT/(cave+n+'-mask.png')),dtype=bool) for n in ('floor','wall','wall-top','wall-side')}
    assert np.array_equal(masks['wall'],expand(masks['floor'],64)&~masks['floor'])
    assert np.array_equal(masks['wall-side'],expand(masks['floor'],32)&~masks['floor'])
    current_doc=json.loads((ROOT/(cave+'mock-maps/cave-natural.json')).read_text(encoding='utf8'));old_doc=json.loads(previous(cave+'mock-maps/cave-natural.json'))
    actual=terrain_layer(current_doc,lambda p:(ROOT/p).read_bytes());before=terrain_layer(old_doc,previous)
    yy,xx=np.mgrid[:actual.shape[0],:actual.shape[1]]
    for name,mask_name in [('top','wall-top'),('side','wall-side')]:
        material=rgba((ROOT/f'assets/tiles/cave_wall_{name}.png').read_bytes());assert np.all(material[:,:,3]==255)
        expected=material[yy%material.shape[0],xx%material.shape[1]]
        assert np.array_equal(actual[masks[mask_name]],expected[masks[mask_name]]),'岩面に座標歪みまたは補間がある'
    from import_visual_target_assets import quantize
    source_record=json.loads((ROOT/'assets/source_records/sprint0-rock-pixel.json').read_text(encoding='utf8'))
    raw=(ROOT/source_record['source_file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==source_record['sha256']
    source=Image.open(io.BytesIO(raw)).convert('RGBA')
    for i,name in enumerate(('top','side')):
        part=source.crop((i*source.width//2+12,12,(i+1)*source.width//2-12,source.height-12));part.putalpha(255)
        expected=np.array(quantize(part.resize((128,128),Image.Resampling.NEAREST)))
        expected[:,-1]=expected[:,0];expected[-1]=expected[0]
        assert np.array_equal(expected,rgba((ROOT/f'assets/tiles/cave_wall_{name}.png').read_bytes()))
    assert actual[:,:,:3][masks['wall-side']].mean()>actual[:,:,:3][masks['wall-top']].mean()
    editable=masks['wall'].copy()
    for i in range(1,4):
        lake=np.array(Image.open(ROOT/(cave+f'lake-{i}-mask.png')),bool);editable|=expand(lake,7)&~lake&masks['floor']
    assert np.array_equal(actual[~editable],before[~editable]),'壁・岩岸以外の地面・水面を変更している'
    counts=dict(Counter(r['size_class'] for r in record['imported']));assert counts==record['counts']
    print('SIZE_ROCK_PASS: monsters=102 replayed='+str(replayed)+' '+json.dumps(counts))
    print('SIZE_COMPARISON_PASS: slime='+str(sizes['slime'])+' wolf='+str(sizes['shadow_wolf']))
    print('CRISP_WALL_PASS: depth=64 top=32 side=32 opaque=2 warp_pixels=0 geometry_unchanged=7')
    print('UNCHANGED_PASS: other_images=304 retained_enemies=3 fixed_files='+str(len(fixed)))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default=FINAL_REF);parser.add_argument('--snapshot',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.snapshot:
        assert '.tools' in ROOT.parts and ROOT.name.startswith('size-rock-snapshot-');audit();return
    revision=subprocess.run(['git','rev-parse','--verify',args.revision],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()
    raw=subprocess.run(['git','archive','--format=tar',revision],cwd=ROOT,capture_output=True,check=True).stdout
    parent=(ROOT/'.tools').resolve();parent.mkdir(exist_ok=True);destination=Path(tempfile.mkdtemp(prefix='size-rock-snapshot-',dir=parent)).resolve();assert destination.is_relative_to(parent)
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
        for member in tar.getmembers():assert (destination/member.name).resolve().is_relative_to(destination)
        tar.extractall(destination,filter='data')
    print('SIZE_ROCK_FIXED_REVISION: '+revision,flush=True)
    result=subprocess.run([sys.executable,str(destination/'tools/check_size_rock_review.py'),'--snapshot'],cwd=destination,check=False)
    print('SIZE_ROCK_SNAPSHOT: '+str(destination),flush=True);raise SystemExit(result.returncode)

if __name__=='__main__':main()
