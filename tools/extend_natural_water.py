"""依頼者の港町原画に実在する海の青4色を、既存76色の末尾だけへ追加する（AGENTS.md：原画由来の色の追加規則）。

海は画面の約2割を占め、natural.gpl の最も近い青（鈍い青）では原画の鮮やかな青が失われる。
既存の色の順番・値と、既存素材は変更しない。4色を超える追加はしない。
"""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='f12f542'   # 追加前のmain
PALETTE='assets/palette/natural.gpl'
SOURCE='assets/_incoming/owner-2026-10-01-region2-port/FE4B1B12-C9B1-4DB0-B374-81F51D061BA6.PNG'
RECORD='assets/source_records/natural-water-extension.json'
SAMPLES=[((1497,430),(1,74,146),'海の暗い波'),((1525,413),(0,101,184),'海の主な青（海の青画素で最も多い色）'),
         ((1489,412),(1,122,203),'海の明るい波'),((1455,916),(93,185,228),'波頭の明るい青')]

def main():
    original=subprocess.check_output(['git','show',BASE+':'+PALETTE],cwd=ROOT)
    colors=[]
    for line in original.decode().splitlines():
        if line.strip() and line.strip()[0].isdigit():colors.append(list(map(int,line.split()[:3])))
    assert len(colors)==76
    raw=(ROOT/SOURCE).read_bytes();image=Image.open(ROOT/SOURCE).convert('RGB');samples=[]
    for xy,rgb,reason in SAMPLES:
        assert image.getpixel(xy)==rgb and list(rgb) not in colors,(xy,rgb)
        samples.append(dict(rgb=list(rgb),hex='#'+''.join(f'{n:02X}' for n in rgb),source=SOURCE,source_xy=list(xy),source_sha256=hashlib.sha256(raw).hexdigest(),reason=reason))
    extra='\n# Source water extension (AGENTS.md rule, max 4 colors); 2026-10-03\n'+''.join(f"{r['rgb'][0]:3} {r['rgb'][1]:3} {r['rgb'][2]:3}\t{r['hex']}\n" for r in samples)
    expected=original+extra.encode()
    current=(ROOT/PALETTE).read_bytes();assert current in (original,expected),'既存パレットの上書き禁止'
    (ROOT/PALETTE).write_bytes(expected)
    result=dict(baseline=BASE,original_sha256=hashlib.sha256(original).hexdigest(),original_colors=colors,original_color_count=76,
                new_color_count=80,selected=samples,palette_sha256=hashlib.sha256(expected).hexdigest(),
                reason='港町原画の海の鮮やかな青が、natural.gplの鈍い青（例 #3174AC）に置き換わるため、原画に実在する暗部・主色・明部・波頭を追加。')
    (ROOT/RECORD).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print('NATURAL_WATER: 既存76色の順番・値・原本バイトを維持、4色追加',[(r['hex'],r['source_xy']) for r in samples])
if __name__=='__main__':main()
