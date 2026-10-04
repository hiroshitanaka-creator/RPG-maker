"""007の全72コマを実画素で検査。--stageは完成時の再生成一致も検査する。"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from validate_assets import load_palette

ROOT = Path(__file__).resolve().parents[1]
IDS = ['water_keeper','date_farmer','innkeeper','camel_keeper','elder','child']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',action='store_true');args=parser.parse_args()
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
    (out/'assets.json').write_text(json.dumps(dict(status='PASS',stage=args.stage,people=6,frames=72,results=results,direction_review='generated/pair1〜3の実画像を目視し、行順を下・左・右・上と確認。背面に顔なし。方向の意味は数値だけでは採否しない。'),ensure_ascii=False,indent=2)+'\n')
    print('TASK007_ASSETS_PASS: people=6 frames=72 regenerated='+str(args.stage))

if __name__=='__main__':
    main()
