"""残る3人24姿の形式・出所・対象外不変・72px表示を確認する追加検査。"""
import io,json,hashlib,subprocess
import numpy as np
from PIL import Image
from prepare_party_forms import ROOT,RAW,REVIEW,ACTORS,FORMS,SOURCE,sha
from validate_assets import check_asset,load_palette

BASE='7b368702b5a62ebd0b26b83ff170c153f762fe77'
def git_bytes(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

def main():
    records=json.loads((ROOT/'assets/source_records/party-form-conversion.json').read_text(encoding='utf-8'))
    assert len(records)==48 and len({(r['actor'],r['form'],r['kind']) for r in records})==48
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'));entries={e['path']:e for e in registry['assets']}
    changed={r['path'] for r in records};unchanged=0
    for entry in registry['assets']+registry.get('audio',[])+registry.get('fonts',[]):
        path=entry['path']
        if path not in changed:assert (ROOT/path).read_bytes()==git_bytes(path),path;unchanged+=1
    for path in ['assets/palette/natural.gpl','data/character_visuals.json']:
        assert (ROOT/path).read_bytes()==git_bytes(path),path
    original_count=0
    for path in SOURCE.glob('*.PNG'):
        assert path.read_bytes()==git_bytes(str(path.relative_to(ROOT)).replace('\\','/'));original_count+=1
    results=[];battle_frames=0;walk_frames=0
    for r in records:
        assert r['actor'] in ACTORS and r['form'] in FORMS
        for key in ['source','reference','raw']:assert sha(ROOT/r[key])==r[key+'_sha256']
        errors,exists=check_asset(entries[r['path']],load_palette(ROOT/'assets/palette/natural.gpl'));assert exists and not errors,errors
        assert sha(ROOT/r['path'])==r['output_sha256']
        raw=np.array(Image.open(ROOT/r['raw']).convert('RGBA'))[:,:,3]>=160
        assert not(raw[0].any() or raw[-1].any() or raw[:,0].any() or raw[:,-1].any()),'生成原画の端で体が切れている'
        sheet=Image.open(ROOT/r['path']).convert('RGBA');a=np.array(sheet)
        colors=set(map(tuple,a[:,:,:3][a[:,:,3]>0].tolist()));w,h=r['frame']
        assert (w,h)==((96,96) if r['kind']=='battle' else (32,48))
        assert len(colors)<=(20 if r['kind']=='battle' else 16)
        assert len({p['sha256'] for p in r['poses']})==len(r['poses'])
        cores=0
        for i,p in enumerate(r['poses']):
            frame=sheet.crop((i%3*w,i//3*h,(i%3+1)*w,(i//3+1)*h))
            assert hashlib.sha256(frame.tobytes()).hexdigest()==p['sha256']
            assert frame.getbbox()[3]==h
            if r['kind']=='battle':
                scaled=np.array(frame.resize((72,72),Image.Resampling.NEAREST))
                assert set(np.unique(scaled[:,:,3]))<={0,255}
                assert set(map(tuple,scaled[:,:,:3][scaled[:,:,3]>0].tolist()))<=colors
                axis=np.array(Image.fromarray(np.arange(96,dtype=np.int32)[None,:]).resize((72,1),Image.Resampling.NEAREST))[0]
                for x,y in p['light_cores']:
                    xs=np.flatnonzero(axis==x);ys=np.flatnonzero(axis==y)
                    assert len(xs) and len(ys) and tuple(scaled[ys[0],xs[0],:3])==(238,246,235)
                    cores+=1
                battle_frames+=1
            else:walk_frames+=1
        results.append(dict(actor=r['actor'],form=r['form'],kind=r['kind'],colors=len(colors),light_cores_72=cores,sha256=r['output_sha256']))
    assert battle_frames==72 and walk_frames==288 and original_count==9
    output=dict(status='PASS',baseline=BASE,actors=3,forms=24,sheets=48,battle_frames=battle_frames,walk_frames=walk_frames,unchanged_registered_files=unchanged,unchanged_originals=original_count,results=results,scope='形式・出所・画素・参照の検査。目印の形、白い輪郭、原画との近さは比較画像で確認する。カイナ・12職・侵蝕素材は不変。')
    (REVIEW/'asset-checks.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'PARTY_FORMS_PASS: sheets=48 battle_frames=72 walk_frames=288 unchanged={unchanged} originals=9')

if __name__=='__main__':main()
