#!/usr/bin/env python3
"""081の外観を原画全体の最近傍縮小と固定パレット最近傍減色だけで取り込む。"""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from backdrop_common import ROOT,palette,grid
ORIGINAL="assets/_incoming/owner-2026-10-04-grok-region3/region3-world-map-alt-b.png"
SHA="30d812e28f8dad699359f489aec0f61e9924dc65dd3288a085f7d2046fa5b454"
BACKGROUND="assets/town_backdrops/region3_port.png"
RECORD="assets/source_records/region3-port-081.json"

def converted():
 raw=(ROOT/ORIGINAL).read_bytes();assert len(raw)==3807730 and hashlib.sha256(raw).hexdigest()==SHA
 im=Image.open(ROOT/ORIGINAL).convert("RGB");assert im.size==(1712,1152)
 source=np.asarray(im);rows=(2*np.arange(864)+1)*2//3;columns=(2*np.arange(1284)+1)*2//3
 small=source[rows][:,columns];flat=small.reshape(-1,3).astype(np.int32);pal=palette().astype(np.int32)
 nearest=np.concatenate([((chunk[:,None]-pal[None])**2).sum(2).argmin(1) for chunk in np.array_split(flat,32)])
 counts=np.bincount(nearest,minlength=len(pal));keep=list(np.flatnonzero(counts));dist=((pal[:,None]-pal[None])**2).sum(2)
 while len(keep)>64:
  _,color=min((int(counts[c])*int(dist[c,[v for v in keep if v!=c]].min()),int(c)) for c in keep);keep.remove(color)
 chosen=pal[keep];index=np.concatenate([((chunk[:,None]-chosen[None])**2).sum(2).argmin(1) for chunk in np.array_split(flat,32)])
 data=chosen[index].astype("uint8").reshape(864,1284,3)
 canvas=np.empty((864,1312,3),dtype="uint8");canvas[:]=data[0,0];canvas[:,14:1298]=data
 return Image.fromarray(canvas).convert("RGBA")

def main():
 image=converted();(ROOT/BACKGROUND).parent.mkdir(parents=True,exist_ok=True);image.save(ROOT/BACKGROUND)
 record=dict(original=ORIGINAL,original_sha256=SHA,original_bytes=3807730,original_size=[1712,1152],scale=[3,4],scaled_size=[1284,864],canvas_size=[1312,864],offset=[14,0],padding="左右14pxは縮小・減色後の左上画素と同色。元の画像領域を全保持。",conversion="最近傍3/4縮小、natural.gplから使用頻度と距離で64色を決定し最近傍減色。描き足し・消去・ぼかし・色調補正なし。",palette_sha256=hashlib.sha256((ROOT/"assets/palette/natural.gpl").read_bytes()).hexdigest(),output_sha256=hashlib.sha256((ROOT/BACKGROUND).read_bytes()).hexdigest())
 (ROOT/RECORD).write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
 registry=json.loads((ROOT/"assets/registry.json").read_text())
 entry=dict(path=BACKGROUND,kind="town_backdrop",size=[1312,864],max_colors=64,status="required",palette="assets/palette/natural.gpl",source="owner",author="依頼者",license="LicenseRef-Owner-Provided",provided_at="2026-10-04",original_file=ORIGINAL,modified=record["conversion"],conversion_record=RECORD,sha256=record["output_sha256"])
 matches=[i for i,item in enumerate(registry["assets"]) if item["path"]==BACKGROUND]
 if matches:registry["assets"][matches[0]]=entry
 else:registry["assets"].append(entry)
 (ROOT/"assets/registry.json").write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n")
 out=ROOT/"docs/verification/task-081-implementation";out.mkdir(exist_ok=True)
 grid(image,41,27,zoom=1).save(out/"exterior-grid-diagnostic.png")
 print("TASK081_IMPORT: original unchanged; full source; 1312x864")
if __name__=="__main__":main()
