"""依頼者のスイナ原画に実在する青紫4色を共通パレット末尾へ追加する。"""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='35222876e1a5aa40dcdd51b19a2f927996c63290'
PALETTE='assets/palette/natural.gpl'
RECORD=ROOT/'assets/source_records/natural-violet-extension.json'

def main():
    original=subprocess.run(['git','show',BASE+':'+PALETTE],cwd=ROOT,check=True,capture_output=True).stdout
    samples=[];locations=[]
    for number,box in [(1104,(0,180,735,610)),(1108,(0,175,1168,590)),(1109,(855,170,1168,565))]:
        path=f'assets/_incoming/owner-2026-09-28/monster-job-images/IMG_{number}.PNG'
        rgb=np.array(Image.open(ROOT/path).convert('RGB'));x1,y1,x2,y2=box;crop=rgb[y1:y2,x1:x2].astype(np.int32)
        mask=(crop[:,:,2]>crop[:,:,0]*1.2)&(crop[:,:,0]>crop[:,:,1]*1.2)&(crop[:,:,2]>crop[:,:,1]*1.4)&(crop[:,:,2]>80)
        yy,xx=np.where(mask);samples.append(crop[mask]);locations.extend((path,int(x+x1),int(y+y1)) for y,x in zip(yy,xx))
    values=np.concatenate(samples);selected=[]
    for target in [[45,19,79],[77,38,127],[115,66,183],[167,119,223]]:
        index=int(((values-np.array(target))**2).sum(1).argmin());color=values[index].tolist();path,x,y=locations[index]
        assert list(Image.open(ROOT/path).convert('RGB').getpixel((x,y)))==color
        selected.append(dict(rgb=color,hex=''.join(f'{v:02X}' for v in color),source=path,source_xy=[x,y],source_sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()))
    assert len({r['hex'] for r in selected})==4
    extension='\n# Owner-approved source violet extension; 2026-09-29\n'+''.join(f"{r['rgb'][0]:3} {r['rgb'][1]:3} {r['rgb'][2]:3}\t#{r['hex']}\n" for r in selected)
    expected=original+extension.encode('utf-8')
    current=(ROOT/PALETTE).read_bytes();assert current in (original,expected),'既存パレットの内容が比較元と異なる'
    (ROOT/PALETTE).write_bytes(expected)
    RECORD.write_text(json.dumps(dict(baseline=BASE,original_sha256=hashlib.sha256(original).hexdigest(),original_color_count=68,new_color_count=72,selected=selected,palette_sha256=hashlib.sha256(expected).hexdigest()),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('NATURAL_VIOLET: 68色の順序・値・原本バイトを保持、4色追加', [r['hex'] for r in selected])

if __name__=='__main__':main()
