"""依頼者の剣士原画から深紅4色を採り、natural.gplの末尾だけへ追加する。"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SOURCE='assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_1028.PNG'
RECORD=ROOT/'assets/source_records/natural-crimson-extension.json'

def values(data):
    rows=[line.split() for line in data.decode('utf-8').splitlines()]
    return [tuple(map(int,row[:3])) for row in rows if len(row)>=3 and all(v.isdigit() for v in row[:3])]

def main():
    path=ROOT/'assets/palette/natural.gpl';before=path.read_bytes()
    if RECORD.exists():
        record=json.loads(RECORD.read_text(encoding='utf-8'))
        assert values(before)==[tuple(v) for v in record['original_colors']+record['added_colors']]
        print('CRIMSON_PALETTE: 追加済み68色を確認');return
    original=values(before);assert len(original)==64
    image=Image.open(ROOT/SOURCE).convert('RGB');a=np.asarray(image);hsv=np.asarray(image.convert('HSV'))
    selection=(((hsv[:,:,0]<=8)|(hsv[:,:,0]>=247))&(hsv[:,:,1]>=115)&(a[:,:,0]>=50))
    pixels=a[selection];brightness=pixels.astype(float)@np.array([0.2126,0.7152,0.0722])
    added=[];samples=[]
    for percentile in [10,40,70,95]:
        target=np.percentile(brightness,percentile);index=int(np.abs(brightness-target).argmin())
        color=tuple(map(int,pixels[index]));assert color not in original+added;added.append(color)
        y,x=np.argwhere(selection)[index];samples.append({'percentile':percentile,'pixel':[int(x),int(y)],'rgb':color})
    newline=b'\r\n' if b'\r\n' in before else b'\n'
    extension=(b'' if before.endswith(b'\n') else newline)+b'# Owner-approved crimson extension; 2026-09-28'+newline
    for color in added:extension+=('%3d %3d %3d\t#%02X%02X%02X'%(*color,*color)).encode('ascii')+newline
    path.write_bytes(before+extension);assert path.read_bytes().startswith(before)
    RECORD.write_text(json.dumps({'source':SOURCE,'source_sha256':hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest(),'original_colors':original,'added_colors':added,'samples':samples,'rule':'赤の色相・彩度で選んだ原画画素から明るさの10/40/70/95百分位に最も近い実在色を採用。既存64色の順番・値は変更しない。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('CRIMSON_PALETTE: original=64 appended=4 total=68 colors='+str(added))

if __name__=='__main__':main()
