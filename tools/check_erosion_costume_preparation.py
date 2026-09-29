"""下書きの構造検査と、現行色数規約への適合を別々に報告する。"""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image
from scipy import ndimage
from prepare_erosion_costume_anchors import ROOT,OUT
from validate_assets import load_palette

BASE='decffbd443b14e65a43d09b3e806cdf3a92382ad'
def old(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

def main():
    records=json.loads((OUT/'prepared-records.json').read_text(encoding='utf-8'))
    assert len(records)==192
    palette=load_palette(ROOT/'assets/palette/natural.gpl');masks={};conflicts=[];frame_count=0
    for r in records:
        base=Image.open(ROOT/r['base']).convert('RGBA');overlay=Image.open(ROOT/r['prepared']['overlay']).convert('RGBA');composite=Image.open(ROOT/r['prepared']['composite']).convert('RGBA')
        assert (ROOT/r['base']).read_bytes()==old(r['base'])
        assert Image.alpha_composite(base,overlay).tobytes()==composite.tobytes()
        b=np.array(base);o=np.array(overlay);c=np.array(composite);mask=o[:,:,3]>0
        assert np.array_equal(b[:,:,3],c[:,:,3]) and np.array_equal(b[~mask],c[~mask])
        assert set(np.unique(c[:,:,3]))<={0,255}
        colors=set(map(tuple,c[:,:,:3][c[:,:,3]>0].tolist()));assert colors<=palette
        if len(colors)>(20 if r['kind']=='battle' else 16):conflicts.append(dict(actor=r['actor'],job=r['job'],kind=r['kind'],stage=r['stage'],colors=len(colors)))
        masks[r['actor'],r['job'],r['kind'],r['stage']]=mask
        w,h=r['frame']
        for i in range(r['grid'][0]*r['grid'][1]):
            frame_count+=1
            local=c[i//3*h:(i//3+1)*h,i%3*w:(i%3+1)*w]
            assert (local[-1,:,3]>0).any(),'接地行が変わった'
            if r['stage']==60:
                bm=b[i//3*h:(i//3+1)*h,i%3*w:(i%3+1)*w,3]>0
                om=o[i//3*h:(i//3+1)*h,i%3*w:(i%3+1)*w,3]>0
                rim=bm&~ndimage.binary_erosion(bm,iterations=2 if r['kind']=='battle' else 1)
                assert np.all(~rim|om),'輪郭光が欠ける'
            if not r['adopted_seed_preserved']:
                parts=r['parts'][i]
                for part in ['arm','cheek']+(['neck','other_arm'] if r['stage']==60 else []):
                    if part=='cheek' and r['kind']=='walk' and i>=9:continue
                    assert parts.get(part,0)>0,(r['actor'],r['job'],r['kind'],r['stage'],i,part)
    for actor,job,kind,stage in masks:
        if stage==60:assert np.all(~masks[actor,job,kind,30]|masks[actor,job,kind,60])
    assert frame_count==1440
    # 下書き作成では本番の素材・接続・色数規約を変更しない。
    for path in ['assets/registry.json','data/character_visuals.json','assets/palette/natural.gpl','docs/asset-spec.md']:
        assert (ROOT/path).read_bytes()==old(path),path
    result=dict(structure_status='PASS',production_status='NOT_APPLIED',color_policy_status='NEEDS_OWNER_APPROVAL' if conflicts else 'PASS',variants=192,frames=frame_count,original_costumes_unchanged=True,production_files_unchanged=True,color_conflicts=conflicts,meaning='下書きの寸法・透過・部位・輪郭光・元衣装保持が成功。現行の戦闘20色・歩行16色の上限超過は未解決として別に残す。')
    (OUT/'preparation-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'EROSION_PREPARATION: structure=PASS frames=1440 production=NOT_APPLIED color_conflicts={len(conflicts)}')

if __name__=='__main__':main()
