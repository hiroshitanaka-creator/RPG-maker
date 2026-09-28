"""採用済みの形・動作と今回の色補正を照合する追加検査。既存検査は変更しない。"""
from pathlib import Path
import io,json,subprocess
import numpy as np
from PIL import Image
from monster_battle_colors import BATTLE_COLORS,recolor
from prepare_kaina_forms import ROOT,REVIEW
from validate_assets import check_asset,load_palette

BASE='05dcae43ddff1bbf7fef22b41f52233cfe9b9a24'
def git_bytes(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout
def light(rgb):return (rgb*[.2126,.7152,.0722]).sum(-1)

def main():
    records=json.loads((ROOT/'assets/source_records/kaina-form-conversion.json').read_text(encoding='utf-8'))
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    entries={e['path']:e for e in registry['assets']}
    changed={r['path'] for r in records if r['kind']=='battle'};assert len(changed)==8
    unchanged=0
    for entry in registry['assets']+registry.get('audio',[])+registry.get('fonts',[]):
        if entry['path'] in changed:continue
        assert (ROOT/entry['path']).read_bytes()==git_bytes(entry['path']),entry['path']
        unchanged+=1
    result=[]
    for r in records:
        if r['kind']!='battle':continue
        image=Image.open(ROOT/r['path']).convert('RGBA');a=np.array(image)
        old=np.array(Image.open(io.BytesIO(git_bytes(r['path']))).convert('RGBA'))
        assert a.shape==old.shape and np.array_equal(a[:,:,3],old[:,:,3]),'輪郭・位置を変更している'
        errors,exists=check_asset(entries[r['path']],load_palette(ROOT/'assets/palette/natural.gpl'))
        assert exists and not errors,errors
        pixels=a[:,:,3]>0
        before=float(light(old[:,:,:3][pixels]).mean());after=float(light(a[:,:,:3][pixels]).mean())
        assert after>before,'全体の明るさが上がっていない'
        poses=[]
        for i,box in enumerate(r['boxes']):
            body=Image.open(ROOT/r['raw']).convert('RGBA').crop(box)
            body=body.resize((round(body.width*r['scale']),round(body.height*r['scale'])),Image.Resampling.NEAREST)
            raw=np.array(body);raw[:,:,3]=(raw[:,:,3]>=160)*255;raw[raw[:,:,3]==0]=0
            body=Image.fromarray(raw);body=body.crop(body.getbbox())
            frame=Image.new('RGBA',(96,96));frame.alpha_composite(body,((96-body.width)//2,96-body.height-(1 if r['outline'] else 0)))
            mapped,details=recolor(frame,r['form'],i)
            actual=a[:,i*96:(i+1)*96,:];mask=mapped[:,:,3]>0
            assert np.array_equal(mapped[:,:,:3][mask],actual[:,:,:3][mask]),'再現結果の不一致'
            scaled=np.array(Image.fromarray(actual).resize((72,72),Image.Resampling.NEAREST))
            if not details['closed_eye']:
                assert details['eye_pixels']>0 and details['light_cores'],(r['form'],i,'目の光がない')
                for x,y in details['light_cores']:
                    assert tuple(actual[y,x,:3])==(238,246,235)
                    axis=np.array(Image.fromarray(np.arange(96,dtype=np.int32)[None,:]).resize((72,1),Image.Resampling.NEAREST))[0]
                    sx=np.flatnonzero(axis==x)
                    sy=np.flatnonzero(axis==y)
                    assert len(sx)>0 and len(sy)>0,(r['form'],i,'72pxで光点が消える')
                    assert tuple(scaled[sy[0],sx[0],:3])==(238,246,235)
            assert set(np.unique(scaled[:,:,3]))<={0,255}
            details['alpha_unchanged']=True;details['glow_survives_72']=not details['closed_eye'];poses.append(details)
        used=set(map(tuple,a[:,:,:3][pixels].tolist()))
        assert len(used)<=20
        result.append(dict(form=r['form'],colors=len(used),before_mean_luma=round(before,2),after_mean_luma=round(after,2),poses=poses))
    out=dict(status='PASS',baseline=BASE,battle_sheets=8,alpha_identical_frames=24,unchanged_registered_files=unchanged,palette=BATTLE_COLORS,forms=result,scope='形・動作・配置は同一。歩行を含む対象外素材を保持。閉眼の甲殻系被弾は光点を描き足さない。平均明度は補助指標で、採否は原画・実画面で判断する。')
    (REVIEW/'color-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'KAINA_COLORS_PASS: alpha_frames=24 unchanged={unchanged} colors<=20 eye_glow_72=PASS')
    for r in result:print(r['form'],r['colors'],r['before_mean_luma'],'->',r['after_mean_luma'])

if __name__=='__main__':main()
