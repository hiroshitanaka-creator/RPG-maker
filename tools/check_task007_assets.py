"""007の全72コマを実画素で検査。--stageは完成時の再生成一致も検査する。"""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from validate_assets import load_palette

ROOT = Path(__file__).resolve().parents[1]
IDS = ['water_keeper','date_farmer','innkeeper','camel_keeper','elder','child']

BASE='8694aad22ce8ceab74ac96c090360739c30d9983'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

def scope(completed):
    changed=git('diff','--name-only',BASE,completed).decode().splitlines()
    allowed={'.github/workflows/ci.yml','world/region2_village.json','scripts/game/game_session.gd','assets/registry.json','assets/source_records/task007-residents.json','assets/source_records/task007-residents-generation.json','docs/region2-village-backdrops.md','docs/decision-log.md','docs/tasks/007-oasis-village-connect.md','docs/tasks/reports/007-oasis-village-connect.md'}
    old=git('ls-tree','-r','--name-only',BASE).decode().splitlines()
    for path in changed:
        added=path not in old
        assert path in allowed or (added and (path.startswith('docs/verification/task-007/') or path.startswith('tools/') and 'task007' in path or path.startswith('assets/characters/npc_oasis_') and path.endswith('/walk.png'))),'担当外差分: '+path
    before=json.loads(git('show',BASE+':assets/registry.json'))
    after=json.loads(git('show',completed+':assets/registry.json'))
    assert {k:v for k,v in after.items() if k!='assets'}=={k:v for k,v in before.items() if k!='assets'}
    new_paths={f'assets/characters/npc_oasis_{name}/walk.png' for name in IDS}
    assert [e for e in after['assets'] if e['path'] not in new_paths]==before['assets']
    assert {e['path'] for e in after['assets'] if e['path'] in new_paths}==new_paths and len(after['assets'])==len(before['assets'])+6
    old_script=git('show',BASE+':scripts/game/game_session.gd').decode()
    new_script=git('show',completed+':scripts/game/game_session.gd').decode()
    extension=' or (_state["overworld"]["node"]=="region2_village" and _state["overworld"]["room"]==4)'
    assert new_script.count(extension)==1 and new_script.replace(extension,'',1)==old_script,'祠の場所追加以外に既存処理変更'
    before=json.loads(git('show',BASE+':world/region2_village.json'));after=json.loads(git('show',completed+':world/region2_village.json'))
    for room in after['site']['rooms']:room['events']=[]
    assert after==before,'006の接続・既存地形の変更'
    old_ci=git('show',BASE+':.github/workflows/ci.yml').decode()
    new_ci=git('show',completed+':.github/workflows/ci.yml').decode()
    pattern=r'      - name: 007完成版と最新の住人・宿・祠・通常操作を検査\n.*?(?=      - name:)'
    steps=re.findall(pattern,new_ci,re.S)
    assert len(steps)==1 and re.sub(pattern,'',new_ci,flags=re.S)==old_ci, '既存CI不変・追加1ステップ'
    return dict(status='PASS',ci_added_steps=1,base_sha=BASE,completed_sha=completed,files=changed,existing_registry_entries_unchanged=True,existing_service_rules_unchanged=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',action='store_true');args=parser.parse_args()
    completed=git('rev-parse','HEAD').decode().strip() if args.stage else None
    if args.stage:assert completed==os.environ.get('TASK007_EXECUTION_SHA',completed), '完成checkoutと実行SHA一致'
    scope_record=scope(completed) if args.stage else None
    palette=load_palette(ROOT/'assets/palette/natural.gpl')
    results=[]
    for name in IDS:
        path=ROOT/f'assets/characters/npc_oasis_{name}/walk.png'
        image=Image.open(path).convert('RGBA');a=np.array(image)
        assert image.size==(96,192) and set(np.unique(a[:,:,3]))=={0,255},name
        colors=set(map(tuple,a[:,:,:3][a[:,:,3]>0]));assert colors<=palette and 0<len(colors)<=16,name
        frames=[a[y*48:(y+1)*48,x*32:(x+1)*32] for y in range(4) for x in range(3)]
        ground=[];differences=[]
        for frame in frames:
            ys,xs=np.where(frame[:,:,3]>0);assert len(xs)>20,name
            ground.append(int(ys.max()));assert xs.min()>0 and xs.max()<31,name+' 横端切れ'
        assert ground==[47]*12,name+' 接地'
        assert len({frame.tobytes() for frame in frames})==12,name+' コピーされたコマ'
        for row in range(4):
            base=frames[row*3]
            motion=[int(np.any(base[32:]!=frames[row*3+col][32:],axis=2).sum()) for col in [1,2]]
            assert min(motion)>=4,name+' 足運び不足';differences.append(motion)
        assert frames[3].tobytes()!=frames[6][:,::-1].tobytes(),name+' 左右単純反転'
        results.append(dict(id=name,frames=12,colors=len(colors),ground=ground,footfall_changed_pixels=differences,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    if args.stage:
        from import_task007_residents import render
        recorded=json.loads((ROOT/'assets/source_records/task007-residents.json').read_text())
        for index,(expected,record) in enumerate(render()):
            assert Image.open(ROOT/record['path']).tobytes()==expected.tobytes(),'再生成画素不一致'
            assert recorded['entries'][index]==dict(record,sha256=results[index]['sha256']),'出所・全切り抜き範囲・倍率の記録不一致'
    out=ROOT/'docs/verification/task-007/latest';out.mkdir(parents=True,exist_ok=True)
    (out/'assets.json').write_text(json.dumps(dict(status='PASS',stage=args.stage,scope=scope_record,execution_sha=os.environ.get('TASK007_EXECUTION_SHA',''),people=6,frames=72,results=results,direction_review='generated/pair1〜3の実画像を目視し、行順を下・左・右・上と確認。背面に顔なし。方向の意味は数値だけでは採否しない。'),ensure_ascii=False,indent=2)+'\n')
    print('TASK007_ASSETS_PASS: people=6 frames=72 regenerated='+str(args.stage))

if __name__=='__main__':
    main()
