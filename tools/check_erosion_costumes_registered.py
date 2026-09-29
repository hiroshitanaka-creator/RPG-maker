"""本番登録した侵蝕合成を検査する。元素材は採用済みコミットから不変。"""
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from validate_assets import load_palette

ROOT = Path(__file__).resolve().parents[1]
BASE = '53368733e61c01b9a024b6196c99a7ebc7d961fc'
OUT = ROOT / 'docs/verification/erosion-costumes'

def old(path):
    return subprocess.run(['git', 'show', BASE + ':' + path], cwd=ROOT,
                          capture_output=True, check=True).stdout

def main():
    source = json.loads((ROOT/'assets/source_records/erosion-costumes.json').read_text(encoding='utf-8'))
    records = source['records']
    assert source['approved_extra_color'] and len(records) == 192
    registry = json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    entries = {e['path']: e for e in registry['assets']}
    before = json.loads(old('assets/registry.json'))
    # 既存の素材・台帳の条件をひとつも変更していないこと。
    for e in before['assets']:
        assert entries[e['path']] == e, e['path']
        if (ROOT/e['path']).is_file():
            assert (ROOT/e['path']).read_bytes() == old(e['path']), e['path']
    assert registry['defaults'] == before['defaults']
    assert (ROOT/'assets/palette/natural.gpl').read_bytes() == old('assets/palette/natural.gpl')
    visuals = json.loads((ROOT/'data/character_visuals.json').read_text(encoding='utf-8'))
    palette = load_palette(ROOT/'assets/palette/natural.gpl')
    masks = {}; frames = 0; maxima = {'battle': 0, 'walk': 0}
    expected_new = set()
    for r in records:
        assert (ROOT/r['base']).read_bytes() == old(r['base'])
        for key in ['overlay','composite']:
            p = ROOT/r[key]
            assert hashlib.sha256(p.read_bytes()).hexdigest() == r[key+'_sha256']
            assert p.read_bytes() == (ROOT/r['prepared'][key]).read_bytes()
            if not r['adopted_seed_preserved']: expected_new.add(r[key])
        base, overlay, composite = [Image.open(ROOT/r[k]).convert('RGBA') for k in ['base','overlay','composite']]
        w,h = r['frame']; assert composite.size == (w*3,h*(1 if r['kind']=='battle' else 4))
        assert Image.alpha_composite(base,overlay).tobytes() == composite.tobytes()
        b,o,c = [np.array(i) for i in [base,overlay,composite]]
        mask = o[:,:,3]>0
        assert np.array_equal(b[:,:,3],c[:,:,3]) and np.array_equal(b[~mask],c[~mask])
        assert set(np.unique(c[:,:,3])) <= {0,255} and set(np.unique(o[:,:,3])) <= {0,255}
        colors = set(map(tuple,c[:,:,:3][c[:,:,3]>0].tolist()))
        overlay_colors = set(map(tuple,o[:,:,:3][mask].tolist()))
        assert colors <= palette and overlay_colors <= palette and len(overlay_colors)<=3
        limit = 21 if r['kind']=='battle' else 17
        assert len(colors)<=limit
        maxima[r['kind']] = max(maxima[r['kind']],len(colors))
        if not r['adopted_seed_preserved']:
            assert entries[r['composite']]['max_colors']==limit
            assert entries[r['composite']]['erosion_composite'] is True
            assert entries[r['overlay']]['max_colors']==3
        assert visuals['actors'][r['actor']]['erosion_signs']['jobs'][r['job']][str(r['stage'])][r['kind']]==r['composite']
        masks[r['actor'],r['job'],r['kind'],r['stage']]=mask
        for i in range(r['grid'][0]*r['grid'][1]):
            frames+=1
            ys,xs=slice(i//3*h,(i//3+1)*h),slice(i%3*w,(i%3+1)*w)
            assert (c[ys,xs][-1,:,3]>0).any()
            if r['stage']==60:
                body=b[ys,xs,3]>0
                rim=body&~ndimage.binary_erosion(body,iterations=2 if r['kind']=='battle' else 1)
                assert np.all(~rim|(o[ys,xs,3]>0))
            if not r['adopted_seed_preserved']:
                for part in ['arm','cheek']+(['neck','other_arm'] if r['stage']==60 else []):
                    if part=='cheek' and r['kind']=='walk' and i>=9: continue
                    assert r['parts'][i].get(part,0)>0
    for actor,job,kind,stage in masks:
        if stage==60: assert np.all(~masks[actor,job,kind,30]|masks[actor,job,kind,60])
    assert frames==1440 and len(expected_new)==376
    assert set(entries)-{e['path'] for e in before['assets']}==expected_new
    result=dict(status='PASS',base=BASE,variants=192,frames=frames,new_assets=376,
                maxima=maxima,original_assets_unchanged=True,original_registry_entries_unchanged=True,
                palette_unchanged=True,registered=True)
    (OUT/'registered-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('EROSION_REGISTERED_PASS: variants=192 frames=1440 new_assets=376')

if __name__=='__main__': main()
