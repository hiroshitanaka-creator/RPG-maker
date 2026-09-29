"""青紫追加と戦士の重ね絵を検証する。既存色・元衣装・対象外素材を保持する。"""
import json,io,hashlib,subprocess
import numpy as np
from PIL import Image
from pathlib import Path
from validate_assets import load_palette,check_asset

ROOT=Path(__file__).resolve().parents[1]
BASE='35222876e1a5aa40dcdd51b19a2f927996c63290'
def old(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def main():
    extension=json.loads((ROOT/'assets/source_records/natural-violet-extension.json').read_text(encoding='utf-8'))
    palette=(ROOT/'assets/palette/natural.gpl').read_bytes();assert palette.startswith(old('assets/palette/natural.gpl'))
    assert len(load_palette(ROOT/'assets/palette/natural.gpl'))==72
    for color in extension['selected']:
        assert sha(color['source'])==color['source_sha256']
        assert list(Image.open(ROOT/color['source']).convert('RGB').getpixel(tuple(color['source_xy'])))==color['rgb']
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'));entries={e['path']:e for e in registry['assets']}
    changed={f'assets/characters/pc_04/forms/{form}/battle.png' for form in ['slime','beast','undead','bird','plant','shell','spirit','dragon']}
    unchanged=0
    baseline=json.loads(old('assets/registry.json'))
    for e in baseline['assets']+baseline.get('audio',[])+baseline.get('fonts',[]):
        if e['path'] in changed:continue
        assert (ROOT/e['path']).read_bytes()==old(e['path']),e['path'];unchanged+=1
    for path in changed:
        now=np.array(Image.open(ROOT/path).convert('RGBA'));before=np.array(Image.open(io.BytesIO(old(path))).convert('RGBA'))
        assert np.array_equal(now[:,:,3],before[:,:,3]),'スイナの輪郭を変更している'
        errors,exists=check_asset(entries[path],load_palette(ROOT/'assets/palette/natural.gpl'));assert exists and not errors,errors
    records=json.loads((ROOT/'assets/source_records/erosion-pattern-preview.json').read_text(encoding='utf-8'))
    areas={};composite_checks=[]
    for r in records:
        assert (ROOT/r['base']).read_bytes()==old(r['base'])
        base=Image.open(ROOT/r['base']).convert('RGBA');overlay=Image.open(ROOT/r['overlay']).convert('RGBA');composite=Image.open(ROOT/r['composite']).convert('RGBA')
        assert Image.alpha_composite(base,overlay).tobytes()==composite.tobytes()
        b=np.array(base);o=np.array(overlay);c=np.array(composite)
        assert np.array_equal(b[:,:,3],c[:,:,3]) and np.array_equal(b[o[:,:,3]==0],c[o[:,:,3]==0]),'模様の外側を変更している'
        for path in [r['overlay'],r['composite']]:
            errors,exists=check_asset(entries[path],load_palette(ROOT/'assets/palette/natural.gpl'));assert exists and not errors,errors
        areas[r['kind'],r['stage']]=o[:,:,3]>0
        composite_checks.append(dict(stage=r['stage'],kind=r['kind'],overlay_pixels=int((o[:,:,3]>0).sum()),base_unchanged=True,outside_overlay_unchanged=True))
    for kind in ['battle','walk']:
        assert np.all(~areas[kind,30]|areas[kind,60]) and areas[kind,60].sum()>areas[kind,30].sum()
    visuals=json.loads((ROOT/'data/character_visuals.json').read_text(encoding='utf-8'))
    jobs=visuals['actors']['pc_01']['jobs'];assert len(jobs)==12
    for job in jobs.values():
        assert Image.open(ROOT/job['battle']).size==(288,96) and Image.open(ROOT/job['walk']).size==(96,192)
    out=dict(status='PASS',original_colors_unchanged=68,appended_source_colors=4,total_colors=72,suina_alpha_frames_unchanged=24,unchanged_registered_files=unchanged,compatible_job_sheet_formats=12,composites=composite_checks,scope='12職は重ね絵の寸法形式を確認。模様の位置調整・実装見本はカイナ戦士の30・60のみ。90の扱いは確認中。')
    (ROOT/'docs/verification/erosion-pattern-preview/asset-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'VIOLET_EROSION_PREVIEW_PASS: palette=68+4 unchanged_assets={unchanged} overlays=4 composites=4 job_formats=12')

if __name__=='__main__':main()
