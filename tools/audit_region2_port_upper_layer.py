"""第2港の「上の層」の監査表。歩けるマスごとに、そのマスに立つ人物（32×48px、足元が下端）が
上の層の部品に何画素隠されるかを数える（部品が人物より後に描かれる＝人物が部品の足元より奥にいるとき）。

人物の矩形は (マスx*32, マスy*32-16) から 32×48。頭・顔は上24px。実際の人物画素ではなく矩形で数える上限値。
使い方: python tools/audit_region2_port_upper_layer.py  → docs/verification/region2-port-backdrop/upper-layer-audit.json
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/region2-port-backdrop/upper-layer-audit.json'

def main():
    data=json.loads((ROOT/'world/region2_port.json').read_text(encoding='utf8'))
    ext=data['maps']['brine_port:0'];layout=ext['layout']
    atlas=np.array(Image.open(ROOT/ext['overlays']['path']).convert('RGBA'))
    W,H=ext['width']*32,ext['height']*32
    canvas=[]   # 部品ごとに全体座標の画素マスク
    for ax,ay,w,h,x,y,bottom,name in ext['overlays']['pieces']:
        m=np.zeros((H,W),bool);m[y:y+h,x:x+w]=atlas[ay:ay+h,ax:ax+w,3]>0
        canvas.append((name,bottom,m))
    rows=[]
    for cy in range(ext['height']):
        for cx in range(ext['width']):
            if layout[cy][cx]!='.':continue
            x0,y0=cx*32,cy*32-16
            hit={}
            for name,bottom,m in canvas:
                if not (cy+1<bottom-0.5):continue   # この部品は人物より先に描かれる（人物が手前）
                sub=m[max(y0,0):y0+48,x0:x0+32]
                if not sub.any():continue
                oy=max(y0,0)-y0
                head=int(sub[:max(0,24-oy)].sum()) if oy<24 else 0
                hit.setdefault(name,[0,0]);hit[name][0]+=int(sub.sum());hit[name][1]+=head
            if hit:rows.append(dict(cell=[cx,cy],hidden={k:dict(pixels=v[0],head_pixels=v[1]) for k,v in hit.items()}))
    summary={}
    for r in rows:
        for k,v in r['hidden'].items():
            s=summary.setdefault(k,dict(cells=0,max_pixels=0,head_cells=0));s['cells']+=1;s['max_pixels']=max(s['max_pixels'],v['pixels']);s['head_cells']+=1 if v['head_pixels']>0 else 0
    OUT.write_text(json.dumps(dict(note='矩形（32×48）で数えた上限値。人物の実画素ではない。人物が部品の足元より奥にいるときだけ隠れる。',walkable_cells=sum(r.count('.') for r in layout),cells_with_hidden_pixels=len(rows),by_object=summary,cells=rows),ensure_ascii=False,indent=1)+'\n',encoding='utf8',newline='\n')
    print('UPPER_LAYER_AUDIT: cells_with_overlap=%d objects=%d'%(len(rows),len(summary)))
    for k,v in sorted(summary.items()):print(' ',k,v)
if __name__=='__main__':main()
