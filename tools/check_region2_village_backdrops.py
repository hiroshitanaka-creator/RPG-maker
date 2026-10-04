"""原画不変・最近傍変換・背景同一上層・連結性・再生成を独立して照合する。"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='dad3fca1d2d6216c3418999d27a4cf581ca00860'
RECORD='assets/source_records/region2-village-backdrops.json'
WORLD='world/region2_village_backdrops.json'
VERIFY='docs/verification/region2-village-backdrops'
checks=0
errors=[]

def check(condition,message):
    global checks
    checks+=1
    if not condition:errors.append(message)

def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))

def palette():
    rows=[]
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
        fields=line.split()
        if len(fields)>=3 and all(v.isdigit() for v in fields[:3]):rows.append([int(v) for v in fields[:3]])
    return np.array(rows,dtype=np.int32)

def source_pixels(record):
    """Pillowのresize呼出しを使わず、出力の画素中心に対応する原画1画素を引く。"""
    source=np.array(Image.open(ROOT/record['original']).convert('RGB'))
    width,height=record['canvas'];sw,sh=record['scaled_size'];ox,oy=record['offset']
    yy,xx=np.indices((height,width));x=xx-ox;y=yy-oy
    valid=(x>=0)&(x<sw)&(y>=0)&(y<sh)
    sx=np.clip(((2*x+1)*source.shape[1])//(2*sw),0,source.shape[1]-1)
    sy=np.clip(((2*y+1)*source.shape[0])//(2*sh),0,source.shape[0]-1)
    expected=source[sy,sx];expected[~valid]=source[0,0]
    return expected

def nearest_mismatches(raw,actual,colors):
    raw=raw.reshape(-1,3).astype(np.int32);actual=actual.reshape(-1,3)
    bad=0
    for start in range(0,len(raw),16384):
        squared=np.sum((raw[start:start+16384,None,:]-colors[None,:,:])**2,axis=2)
        expected=colors[np.argmin(squared,axis=1)]
        bad+=int(np.any(expected!=actual[start:start+16384],axis=1).sum())
    return bad

def reachable(rows,start):
    seen={tuple(start)};queue=deque(seen)
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if 0<=q[1]<len(rows) and 0<=q[0]<len(rows[0]) and rows[q[1]][q[0]]=='.' and q not in seen:seen.add(q);queue.append(q)
    return seen

def verify():
    records=load(RECORD);maps=load(WORLD)['maps'];colors=palette()
    baseline_registry=json.loads(subprocess.check_output(['git','show',BASE+':assets/registry.json'],cwd=ROOT))
    registry=load('assets/registry.json')
    check(set(maps)==set(records['maps'])=={'exterior','inn','item','weapon','shrine'},'5地形がすべて実在')
    check((ROOT/'assets/palette/natural.gpl').read_bytes()==subprocess.check_output(['git','show',BASE+':assets/palette/natural.gpl'],cwd=ROOT),'既存パレットはバイト不変')
    check(hashlib.sha256((ROOT/'assets/palette/natural.gpl').read_bytes()).hexdigest()==records['palette_sha256'],'パレットSHA一致')
    prior={entry['path']:entry for entry in baseline_registry['assets']}
    current={entry['path']:entry for entry in registry['assets']}
    check(all(current.get(path)==entry for path,entry in prior.items()),'既存素材台帳の全項目を保持')
    generated=[]
    for role,record in records['maps'].items():
        raw=(ROOT/record['original']).read_bytes()
        check(raw==subprocess.check_output(['git','show',BASE+':'+record['original']],cwd=ROOT),'原本の全バイト一致: '+role)
        check(hashlib.sha256(raw).hexdigest()==record['sha256'],'原本SHA一致: '+role)
        image=Image.open(ROOT/record['background']);pixels=np.array(image)
        check(image.mode=='RGBA' and list(image.size)==record['canvas'] and all(n%32==0 for n in image.size),'背景形式・寸法: '+role)
        check(np.all(pixels[:,:,3]==255),'背景不透明: '+role)
        used=np.unique(pixels[:,:,:3].reshape(-1,3),axis=0)
        check(len(used)<=64 and len(used)==record['colors'],'背景の規定色数: '+role)
        selected=colors[record['palette_indices']]
        check(nearest_mismatches(source_pixels(record),pixels[:,:,:3],selected)==0,'原画の1画素から最近傍減色だけ: '+role)
        check(record['palette_used']==selected.tolist(),'選択パレット記録: '+role)
        atlas=np.array(Image.open(ROOT/record['overlays']['path']).convert('RGBA'))
        check(all(n%32==0 for n in atlas.shape[:2]),'上層の寸法は32の倍数: '+role)
        check(set(np.unique(atlas[:,:,3]))<={0,255},'上層の二値透過: '+role)
        union=np.zeros(pixels.shape[:2],bool);visible=0
        for ax,ay,w,h,x,y,bottom,name in record['overlays']['pieces']:
            valid=0<=ax<ax+w<=atlas.shape[1] and 0<=ay<ay+h<=atlas.shape[0] and 0<=x<x+w<=pixels.shape[1] and 0<=y<y+h<=pixels.shape[0] and type(bottom) is int and 1<=bottom<=maps[role]['height']+1
            check(valid,'上層の領域と足元: '+role+'/'+name)
            if not valid:continue
            tile=atlas[ay:ay+h,ax:ax+w];mask=tile[:,:,3]==255;visible+=int(mask.sum())
            check(np.array_equal(tile[:,:,:3][mask],pixels[y:y+h,x:x+w,:3][mask]),'上層は背景と同じ画素: '+role+'/'+name)
            union[y:y+h,x:x+w]|=mask
        check(visible>0,'上層の実画素がある: '+role)
        check(np.array_equal(np.array(Image.open(ROOT/VERIFY/role/'upper-mask.png'))>0,union),'上層マスクが一致: '+role)
        rows=maps[role]['layout'];height,width=len(rows),len(rows[0])
        check(rows==record['layout'] and height==maps[role]['height'] and all(len(row)==width and set(row)<={'.','#'} for row in rows),'通行地図の形式と一致: '+role)
        walk=np.array([[c=='.' for c in row] for row in rows])
        check(np.array_equal(np.array(Image.open(ROOT/VERIFY/role/'walk-mask.png'))==255,walk.repeat(32,0).repeat(32,1)),'通行マスクが全画素一致: '+role)
        found=reachable(rows,record['start'])
        check(len(found)==int(walk.sum())==record['walkable_cells'],'歩行マスの全連結性: '+role)
        for label,cell in {**record['doors'],**record['targets']}.items():check(tuple(cell) in found,'入口から到達: '+role+'/'+label)
        if role!='exterior':check(record['start']==[8,10] and record['doors']['exit']==[8,11] and [width,height]==[16,12],'既存室内の扉・大きさ: '+role)
        for path in (record['background'],record['overlays']['path']):
            generated.append(path);entry=current.get(path,{})
            check(entry.get('original_file')==record['original'] and entry.get('conversion_record')==RECORD+'#maps/'+role,'出所と台帳登録: '+path)
    check(len(current)==len(prior)+10 and len(set(generated))==10,'新規素材10件だけを追加')
    for role,cell in [('exterior',[23,15]),('exterior',[16,6]),('inn',[4,4]),('item',[8,5]),('weapon',[8,5]),('shrine',[8,4])]:
        check(maps[role]['layout'][cell[1]][cell[0]]=='#','水面・建物・家具へ立てない: '+role+str(cell))
    with tempfile.TemporaryDirectory(prefix='rpg-village-rebuild-') as first,tempfile.TemporaryDirectory(prefix='rpg-village-rebuild-') as second:
        for directory in (first,second):
            subprocess.run([sys.executable,'-B','tools/build_region2_village_backdrops.py','--output-root',directory],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        paths=generated+[WORLD,RECORD,'assets/registry.json']
        paths += [str(path.relative_to(ROOT)).replace('\\','/') for path in (ROOT/VERIFY).rglob('*.png') if path.name in ('grid.png','collision-overlay.png','source-comparison.png','upper-mask.png','walk-mask.png')]
        for path in paths:check((ROOT/path).read_bytes()==(Path(first)/path).read_bytes()==(Path(second)/path).read_bytes(),'2回再生成の全バイト一致: '+path)
    return records

def main():
    records=verify()
    report=dict(status='FAIL' if errors else 'PASS',checks=checks,failures=errors,baseline_commit=BASE,maps=5,assets=10,originals_byte_identical=True if not any('原本' in e for e in errors) else False,regenerated_twice=True,source='原画の画素中心を整数座標で独立照合。既存の規格・保護条件は変更しない。')
    (ROOT/VERIFY/'data-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for error in errors:print('VILLAGE_DATA_FAIL: '+error,file=sys.stderr)
    print(('VILLAGE_DATA_FAIL' if errors else 'VILLAGE_DATA_PASS')+': checks='+str(checks))
    return int(bool(errors))

if __name__=='__main__':raise SystemExit(main())
