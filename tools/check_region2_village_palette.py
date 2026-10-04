"""村の1回の色取り込みを、旧80色の全バイトと原画の実画素へ照合する。"""
from pathlib import Path
import hashlib
import io
import json
from PIL import Image

BASE_BYTES=1940
BASE_SHA='1b1c00dd929b96b64703972a0ae9368c36636b96c8f717dded78524e57913088'
RECORD='assets/source_records/region2-village-backdrops.json'
KEY='palette_extension'
VERIFIED_SAMPLES=[{'rgb': [126, 76, 44],
  'hex': '#7E4C2C',
  'original': 'assets/_incoming/owner-2026-10-03-region3-port/01-oasis-inn.png',
  'coordinate': [1072, 276],
  'original_sha256': '3bec585c4bfe1fda0401b18b084832d51733bbfbe3cbffb6ec55a6eb7d9c3301'},
 {'rgb': [204, 119, 61],
  'hex': '#CC773D',
  'original': 'assets/_incoming/owner-2026-10-03-region3-port/03-oasis-weapon-shop.png',
  'coordinate': [1128, 647],
  'original_sha256': '81a4fa6e5f68c494bef92bd67a0c400193a2c30711472f6ce1704775968495d9'},
 {'rgb': [167, 89, 45],
  'hex': '#A7592D',
  'original': 'assets/_incoming/owner-2026-10-03-region3-port/01-oasis-inn.png',
  'coordinate': [782, 781],
  'original_sha256': '3bec585c4bfe1fda0401b18b084832d51733bbfbe3cbffb6ec55a6eb7d9c3301'},
 {'rgb': [113, 61, 29],
  'hex': '#713D1D',
  'original': 'assets/_incoming/owner-2026-10-03-region3-port/01-oasis-inn.png',
  'coordinate': [1157, 150],
  'original_sha256': '3bec585c4bfe1fda0401b18b084832d51733bbfbe3cbffb6ec55a6eb7d9c3301'}]

def extension(record):
    return ''.join(f"{r:3d} {g:3d} {b:3d}\t#{r:02X}{g:02X}{b:02X}\n" for r,g,b in [c['rgb'] for c in record['additions']]).encode('ascii')

def verify(current,record,source_bytes):
    assert record==EXTENSION_METADATA,'今回の出典記録の全項目一致（無記録の変更を拒否）'
    assert record['baseline_bytes']==BASE_BYTES and record['baseline_sha256']==BASE_SHA
    old=current[:BASE_BYTES]
    assert hashlib.sha256(old).hexdigest()==BASE_SHA,'旧80色の全バイト不一致'
    additions=record['additions']
    assert additions==VERIFIED_SAMPLES,'今回の採取4色・座標・出所だけを許可'
    assert record['baseline_colors']==80 and record['max_added_colors']==4
    assert record['reason']==EXTENSION_METADATA['reason'] and record['selection']==EXTENSION_METADATA['selection'],'追加理由・選択根拠の欠落または変更'
    assert len(additions)==4 and len({tuple(c['rgb']) for c in additions})==4,'今回の原画由来4色だけ'
    assert current[BASE_BYTES:]==extension(record),'末尾の追加4色と記録不一致'
    for color in additions:
        rgb=color['rgb'];assert len(rgb)==3 and all(type(v) is int and 0<=v<=255 for v in rgb)
        assert color['hex']=='#'+''.join(f'{v:02X}' for v in rgb)
        raw=source_bytes(color['original'])
        assert hashlib.sha256(raw).hexdigest()==color['original_sha256'],'採取原画SHA不一致'
        with Image.open(io.BytesIO(raw)) as image:
            assert list(image.convert('RGB').getpixel(tuple(color['coordinate'])))==rgb,'追加色が原画座標の実画素と異なる'
    return old

def original_palette_bytes(root):
    root=Path(root)
    record=json.loads((root/RECORD).read_text(encoding='utf-8'))[KEY]
    return verify((root/'assets/palette/natural.gpl').read_bytes(),record,lambda path:(root/path).read_bytes())

EXTENSION_METADATA={'version': 1,
 'baseline_commit': '6384ee81f99a1c3262823fa5fda04075f214f459',
 'palette': 'assets/palette/natural.gpl',
 'baseline_sha256': '1b1c00dd929b96b64703972a0ae9368c36636b96c8f717dded78524e57913088',
 'baseline_bytes': 1940,
 'baseline_colors': 80,
 'max_added_colors': 4,
 'reason': '村の床・木部が赤系へ置換されるため、原画に実在する土色の明部と陰影色を最大4色追加。元の80色・順番・値・対象外素材は保持する。',
 'selection': {'roles': ['inn', 'item', 'weapon'],
               'canvas_roi': [330, 240, 420, 285],
               'original_warm_hue_degrees': [20, 40],
               'method': '停止時の候補4色を原画の採取座標・SHA・RGBで再照合し、旧80色での最近傍置換誤差、5背景での使用画素数、原画への色差減少で必要性を検証。出力への色調補正・平均化なし。'}}
EXTENSION_METADATA['additions']=VERIFIED_SAMPLES

def extension_metadata():
    import copy
    return copy.deepcopy(EXTENSION_METADATA)

ROOT=Path(__file__).resolve().parents[1]
VERIFY_DIR='docs/verification/region2-village-backdrops'
MAIN_BASE='d2ad6c044920a44340b725987b86c36f4adf7952'

def negative_cases(root):
    """停止候補の11異常を同じ入力変換で再実行し、旧色削除・出所欠落も拒否する。"""
    import copy
    root=Path(root)
    current=(root/'assets/palette/natural.gpl').read_bytes()
    record=json.loads((root/RECORD).read_text(encoding='utf-8'))[KEY]
    source=lambda path:(root/path).read_bytes()
    verify(current,record,source)
    trials=[]
    changed=bytearray(current);changed[150]^=1
    trials.append(('旧領域1バイト変更',bytes(changed),record,source))
    rows=current[:BASE_BYTES].splitlines(keepends=True);rows[4],rows[5]=rows[5],rows[4]
    trials.append(('旧色の順序変更',b''.join(rows)+current[BASE_BYTES:],record,source))
    extra=copy.deepcopy(record);extra['additions'].append(copy.deepcopy(extra['additions'][0]))
    trials.append(('5色と記録への追加',current[:BASE_BYTES]+extension(extra),extra,source))
    replaced=copy.deepcopy(record);replaced['additions'][0]['rgb']=[127,76,44];replaced['additions'][0]['hex']='#7F4C2C'
    trials.append(('別色と記録への差し替え',current[:BASE_BYTES]+extension(replaced),replaced,source))
    trials.append(('追加4色の削除',current[:BASE_BYTES],record,source))
    reordered=copy.deepcopy(record);reordered['additions'].reverse()
    trials.append(('追加色の順序変更',current[:BASE_BYTES]+extension(reordered),reordered,source))
    wrong_sha=copy.deepcopy(record);wrong_sha['additions'][0]['original_sha256']='0'*64
    trials.append(('原画SHAの差し替え',current,wrong_sha,source))
    wrong_point=copy.deepcopy(record);wrong_point['additions'][0]['coordinate']=[0,0]
    trials.append(('採取座標の差し替え',current,wrong_point,source))
    wrong_source=copy.deepcopy(record);wrong_source['additions'][0]['original']='assets/palette/base.gpl'
    trials.append(('出所の差し替え',current,wrong_source,source))
    def damaged(path):
        data=bytearray(source(path));data[-1]^=1;return bytes(data)
    trials.append(('実原画の1バイト変更',current,record,damaged))
    trials.append(('無記録の末尾文字追加',current+b'# unexpected\n',record,source))
    rows=current[:BASE_BYTES].splitlines(keepends=True)
    trials.append(('旧色の削除',b''.join(rows[:4]+rows[5:])+current[BASE_BYTES:],record,source))
    missing=copy.deepcopy(record);del missing['additions'][0]['original']
    trials.append(('色出典の欠落',current,missing,source))
    no_reason=copy.deepcopy(record);del no_reason['reason']
    trials.append(('追加理由の欠落',current,no_reason,source))
    rejected=[]
    for name,pixels,metadata,loader in trials:
        try:verify(pixels,metadata,loader)
        except (AssertionError,KeyError,ValueError,OSError):rejected.append(name)
        else:raise AssertionError('異常入力を受け入れた: '+name)
    report=dict(status='PASS',baseline_sha256=BASE_SHA,baseline_bytes=BASE_BYTES,added_colors=4,negative_cases=rejected,scope='停止時11負例を同じ実体変換で再実行。旧色削除・出所欠落・追加理由欠落を追加。')
    (root/VERIFY_DIR/'palette-validation-004.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return rejected

def fixed_bytes(path):
    import subprocess
    return subprocess.check_output(['git','show',MAIN_BASE+':'+path],cwd=ROOT)

def verify_geometry_and_assets():
    """固定した開始mainと比較し、色以外の記録・原画・全形状・村外の素材を保持する。"""
    import io
    import subprocess
    import numpy as np
    records=json.loads((ROOT/RECORD).read_text(encoding='utf-8'))
    previous=json.loads(fixed_bytes(RECORD))
    assert (ROOT/'world/region2_village_backdrops.json').read_bytes()==fixed_bytes('world/region2_village_backdrops.json')
    assert (ROOT/'tools/region2_village_backdrop_defs.py').read_bytes()==fixed_bytes('tools/region2_village_backdrop_defs.py')
    assert original_palette_bytes(ROOT)==fixed_bytes('assets/palette/natural.gpl')
    allowed={'assets/palette/natural.gpl',RECORD}
    results={}
    def stripped(record):return {k:v for k,v in record.items() if k not in ('colors','palette_indices','palette_used')}
    def pixels(data):return np.array(Image.open(io.BytesIO(data)).convert('RGBA'))
    from check_region2_village_backdrops import source_pixels
    base_colors=np.array([list(map(int,line.split()[:3])) for line in original_palette_bytes(ROOT).decode().splitlines() if len(line.split())>=3 and all(v.isdigit() for v in line.split()[:3])])
    color_evidence=[]
    for color in VERIFIED_SAMPLES:
        rgb=np.array(color['rgb']);distance=((base_colors-rgb)**2).sum(axis=1);old=base_colors[int(distance.argmin())]
        assert distance.min()>0,'追加色は旧80色に含まれない'
        color_evidence.append(dict(**color,previous_nearest_rgb=old.tolist(),previous_squared_error=int(distance.min()),used_pixels={},reason='床と木部の土色・陰影を旧80色の近似色に置換せず保持する'))
    for role,record in records['maps'].items():
        old_record=previous['maps'][role]
        assert stripped(record)==stripped(old_record),'色以外の座標・寸法・形状の変更: '+role
        assert (ROOT/record['original']).read_bytes()==fixed_bytes(record['original']),'原画変更: '+role
        before=pixels(fixed_bytes(record['background']));after=pixels((ROOT/record['background']).read_bytes())
        for evidence in color_evidence:
            evidence['used_pixels'][role]=int(np.all(after[...,:3]==evidence['rgb'],axis=2).sum())
        assert np.array_equal(before[...,3],after[...,3]),'背景アルファ変更: '+role
        for path,alpha_only in [(record['overlays']['path'],True),(f'{VERIFY_DIR}/{role}/walk-mask.png',False),(f'{VERIFY_DIR}/{role}/upper-mask.png',False)]:
            old=pixels(fixed_bytes(path));new=pixels((ROOT/path).read_bytes())
            assert np.array_equal(old[...,3] if alpha_only else old,new[...,3] if alpha_only else new),'通行・上層形状変更: '+path
        raw=source_pixels(record).astype(float)
        rmse=lambda a:float(np.sqrt(np.mean((a[...,:3].astype(float)-raw)**2)))
        old_error,new_error=rmse(before),rmse(after)
        assert new_error<old_error,'原画への全体色差が改善しない: '+role
        results[role]=dict(previous_rgb_rmse=old_error,revised_rgb_rmse=new_error,geometry_identical=True)
        allowed.update((record['background'],record['overlays']['path']))
    assert all(sum(c['used_pixels'].values())>0 for c in color_evidence),'使われない色の数合わせ追加を拒否'
    tree=subprocess.check_output(['git','ls-tree','-r',MAIN_BASE,'assets'],cwd=ROOT,text=True,encoding='utf-8').splitlines()
    old_assets={line.split('\t',1)[1]:line.split()[2] for line in tree if line.split('\t',1)[1] not in allowed}
    paths=list(old_assets)
    hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],input=('\n'.join(paths)+'\n').encode('utf-8'),cwd=ROOT).decode().splitlines()
    def check_assets(observed):
        assert len(observed)==len(paths) and all(h==old_assets[p] for p,h in zip(paths,observed)),'対象外素材のバイト変更'
    check_assets(hashes)
    # 別素材の実体をTempへ複製し、1バイト変更した実ファイルのハッシュを検査へ渡す。
    import tempfile
    outside=next(p for p in paths if p.endswith('.png') and '/_incoming/' not in p)
    data=bytearray((ROOT/outside).read_bytes());data[-1]^=1
    with tempfile.TemporaryDirectory(prefix='rpg-village-outside-negative-') as directory:
        target=Path(directory)/'damaged.png';target.write_bytes(data)
        damaged=list(hashes)
        damaged[paths.index(outside)]=subprocess.check_output(['git','hash-object',str(target)],cwd=ROOT).decode().strip()
        try:check_assets(damaged)
        except AssertionError:negative='村外素材の実体1バイト変更を拒否: '+outside
        else:raise AssertionError('村外影響の負例が検出されない')
    report=dict(status='PASS',baseline_commit=MAIN_BASE,unchanged_other_assets=len(paths),color_evidence=color_evidence,maps=results,negative_case=negative,visual_adoption='NOT_CONFIRMED')
    (ROOT/VERIFY_DIR/'color-integrity-004.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

def comparisons():
    """原画・開始main・今回・目標・旧/最新の実描画を同じ位置で識別できる5比較を作る。"""
    import io
    from PIL import ImageDraw,ImageFont
    from check_region2_village_backdrops import source_pixels
    from check_region2_village_native import panel
    from village_png import save
    native=json.loads((ROOT/VERIFY_DIR/'native-checks.json').read_text(encoding='utf-8'))
    assert native['status']=='PASS' and native['native_render'] and not native['failures']
    previous=json.loads(fixed_bytes(VERIFY_DIR+'/native-checks.json'))
    assert native['captures']==previous['captures'],'比較のカメラ・人物・位置不一致'
    records=json.loads((ROOT/RECORD).read_text(encoding='utf-8'))['maps']
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),14)
    proofs=[]
    for role,record in records.items():
        c=next(c for c in native['captures'] if '/'+role+'/' in c['path'] and c['path'].endswith('/native-detail.png'))
        cx,cy=[round(v*32) for v in c['camera']];box=(cx,cy,cx+512,cy+288)
        target='docs/reference/visual-targets/'+('region2-port-town.png' if role=='exterior' else 'first-castle-hall.png')
        sources=[('原画の最近傍縮小・減色前',Image.fromarray(source_pixels(record)).crop(box)),('開始main d2ad6c0・派生背景',Image.open(io.BytesIO(fixed_bytes(record['background']))).crop(box)),('今回004・派生背景',Image.open(ROOT/record['background']).crop(box)),('既存目標・構図と色調の参照',Image.open(ROOT/target)),('開始main・Windows実描画',Image.open(io.BytesIO(fixed_bytes(c['path'])))),('今回004・最新Windows実描画',Image.open(ROOT/c['path']))]
        sheet=Image.new('RGB',(1536,624),(24,24,30));draw=ImageDraw.Draw(sheet)
        for i,(label,picture) in enumerate(sources):
            x,y=(i%3)*512,(i//3)*312;sheet.paste(panel(picture,(512,288)),(x,y+24));draw.text((x+8,y+2),label,font=font,fill='white')
        path=f'{VERIFY_DIR}/{role}/color-review-004.png';save(sheet,ROOT/path)
        proofs.append(dict(role=role,path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),original_sha256=record['sha256'],reference=target,reference_sha256=hashlib.sha256((ROOT/target).read_bytes()).hexdigest(),native_path=c['path'],native_sha256=hashlib.sha256((ROOT/c['path']).read_bytes()).hexdigest()))
    (ROOT/VERIFY_DIR/'comparison-index-004.json').write_text(json.dumps(dict(baseline_commit=MAIN_BASE,comparisons=proofs,visual_adoption='NOT_CONFIRMED'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--comparisons',action='store_true');args=parser.parse_args()
    rejected=negative_cases(ROOT)
    report=verify_geometry_and_assets()
    if args.comparisons:comparisons()
    print(f"VILLAGE_PALETTE_004_PASS: old_bytes={BASE_BYTES} added=4 negatives={len(rejected)+1} geometry=5 other_assets={report['unchanged_other_assets']}")
    return 0

if __name__=='__main__':raise SystemExit(main())
