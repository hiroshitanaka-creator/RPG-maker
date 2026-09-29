"""拡大した模様・輪郭光と、変更対象外の素材保持を確認する。"""
import io,json,subprocess,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from validate_assets import check_asset,load_palette

ROOT=Path(__file__).resolve().parents[1]
BASE='405fd257fb60cc550cd40c2d693b124317b57ffa'
OUT=ROOT/'docs/verification/erosion-visible'
def old(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

def main():
    records=json.loads((ROOT/'assets/source_records/erosion-pattern-preview.json').read_text(encoding='utf-8'))
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'));entries={e['path']:e for e in registry['assets']}
    changed={r[k] for r in records for k in ['overlay','composite']};assert len(changed)==8
    baseline=json.loads(old('assets/registry.json'));unchanged=0
    for entry in baseline['assets']+baseline.get('audio',[])+baseline.get('fonts',[]):
        path=entry['path']
        if path in changed:continue
        assert (ROOT/path).read_bytes()==old(path),path;unchanged+=1
    for path in ['assets/palette/natural.gpl','project.godot']:
        assert (ROOT/path).read_bytes()==old(path),path
    results=[];masks={}
    for r in records:
        base=Image.open(ROOT/r['base']).convert('RGBA');overlay=Image.open(ROOT/r['overlay']).convert('RGBA');composite=Image.open(ROOT/r['composite']).convert('RGBA')
        assert (ROOT/r['base']).read_bytes()==old(r['base'])
        assert Image.alpha_composite(base,overlay).tobytes()==composite.tobytes()
        b=np.array(base);o=np.array(overlay);c=np.array(composite);mask=o[:,:,3]>0
        assert np.array_equal(b[:,:,3],c[:,:,3]) and np.array_equal(b[~mask],c[~mask])
        before=np.array(Image.open(io.BytesIO(old(r['overlay']))).convert('RGBA'))[:,:,3]>0
        assert mask.sum()>before.sum(),'前の見本より模様の範囲が広がっていない'
        masks[r['kind'],r['stage']]=mask
        for path in [r['overlay'],r['composite']]:
            errors,exists=check_asset(entries[path],load_palette(ROOT/'assets/palette/natural.gpl'));assert exists and not errors,errors
        w,h=(96,96) if r['kind']=='battle' else (32,48)
        rim_pixels=0;bright_pixels=0
        for y in range(0,base.height,h):
            for x in range(0,base.width,w):
                bm=b[y:y+h,x:x+w,3]>0;om=o[y:y+h,x:x+w]
                assert ((om[:,:,:3]==[238,246,235]).all(2)&(om[:,:,3]>0)).any(),'近白色の光がない'
                bright_pixels+=int(((om[:,:,:3]==[238,246,235]).all(2)&(om[:,:,3]>0)).sum())
                if r['stage']==60:
                    width=2 if r['kind']=='battle' else 1
                    rim=bm&~ndimage.binary_erosion(bm,iterations=width,border_value=0)
                    assert (om[:,:,3][rim]==255).all(),'輪郭光に欠けがある'
                    rim_pixels+=int(rim.sum())
        results.append(dict(kind=r['kind'],stage=r['stage'],old_overlay_pixels=int(before.sum()),new_overlay_pixels=int(mask.sum()),near_white_pixels=bright_pixels,contour_pixels=rim_pixels,base_unchanged=True,alpha_unchanged=True))
    for kind in ['battle','walk']:
        assert np.all(~masks[kind,30]|masks[kind,60]) and masks[kind,60].sum()>masks[kind,30].sum()
    output=dict(status='PASS',baseline=BASE,unchanged_registered_files=unchanged,palette_and_project_unchanged=True,composites=results,scope='模様と輪郭光の構成・元衣装の保持を確認。原寸での見分けやすさの採否は依頼者が比較画像で判断する。')
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'asset-checks.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'EROSION_VISIBLE_ASSET_PASS: unchanged={unchanged} near_white=PASS contour=PASS stages=30,60')

if __name__=='__main__':main()
