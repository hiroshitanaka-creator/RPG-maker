"""承認済みの入り江・船原画・4方向・海域接続を検査する。"""
import hashlib,json
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image
from validate_assets import load_palette
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def main():
    record=read('assets/source_records/owner-ship.json')
    assert record['logical_id']=='IMG_0974'
    assert hashlib.sha256((ROOT/record['source']).read_bytes()).hexdigest()==record['sha256']=='566cb733bb8ec639a680468fbd8fb2a01ea4e0297d7b71df372543287fb86a44'
    im=Image.open(ROOT/record['output']).convert('RGBA');a=np.array(im)
    assert im.size==(384,96) and len(record['frames'])==4
    assert [r['direction'] for r in record['frames']]==['down','left','right','up']
    assert set(np.unique(a[:,:,3]))<={0,255}
    colors=set(map(tuple,a[:,:,:3][a[:,:,3]>0].tolist()))
    assert len(colors)<=64 and colors<=load_palette(ROOT/'assets/palette/natural.gpl')
    for x in range(4):assert (a[-1,x*96:(x+1)*96,3]>0).any()
    maps=read('world/first_region_visuals.json')['maps'];port=maps['first_port:0']
    sea=np.array([[c=='.' for c in row] for row in port['ship_layout']]);ratio=float(sea.sum())/sea.size
    assert .30<=ratio<=.42
    bay=read('docs/verification/sprint5-travel/bay-layout.json');assert bay['sea_cells']==int(sea.sum()) and abs(bay['sea_ratio']-ratio)<1e-9
    # 入り江に延びる上・中・下の桟橋をそれぞれ確認する。
    for x,y in [(25,13),(30,18),(26,25)]:assert port['layout'][y][x]=='.' and not sea[y,x]
    config=read('world/first_region_travel.json');assert config['return_mp']==2 and len(config['docks'])==2
    world=maps['world'];ox,oy=world['origin'];allowed={(x+ox,y+oy) for y,row in enumerate(world['terrain']) for x,c in enumerate(row) if c in '~b'}
    start=tuple(config['docks'][0]['ship_cell']);seen={start};queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for p in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
            if p in allowed and p not in seen:seen.add(p);queue.append(p)
    assert tuple(config['docks'][1]['ship_cell']) in seen and (65,50) in seen
    for dock in config['docks']:
        land=dock['land'];x,y=land['cell']
        surface=world if land['layer']=='world' else port
        if land['layer']=='world':x-=ox;y-=oy
        assert surface['layout'][y][x]=='.'
    result=dict(status='PASS',ship_frames=4,ship_colors=len(colors),binary_alpha=True,original_sha256=record['sha256'],sea_ratio=ratio,piers=3,connected_docks=2,return_mp=2)
    (ROOT/'docs/verification/sprint5-travel/asset-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('COASTAL_ASSETS_PASS: frames=4 piers=3 docks=2 sea_ratio=%.3f'%ratio)
if __name__=='__main__':main()
