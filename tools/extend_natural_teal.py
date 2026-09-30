"""IMG_1183に実在する青緑4色を、既存72色の末尾だけへ追加する。"""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='7e1f02a678f69d06f27044a4a5cae321c297b57d'
PALETTE='assets/palette/natural.gpl'
SOURCE='assets/_incoming/owner-2026-09-30-interiors/IMG_1183.png'
RECORD='assets/source_records/natural-teal-extension.json'
SAMPLES=[((198,149),(19,45,46),'サソリの尾の暗部'),((181,141),(39,71,66),'サソリの尾の主な青緑'),
         ((609,234),(66,96,84),'砂の虫の頭の青緑'),((632,228),(98,125,108),'砂の虫の頭の明部')]

def main():
    original=subprocess.check_output(['git','show',BASE+':'+PALETTE],cwd=ROOT)
    colors=[]
    for line in original.decode().splitlines():
        if line.strip() and line.strip()[0].isdigit():colors.append(list(map(int,line.split()[:3])))
    assert len(colors)==72
    raw=(ROOT/SOURCE).read_bytes();image=Image.open(ROOT/SOURCE).convert('RGB');samples=[]
    for xy,rgb,reason in SAMPLES:
        assert image.getpixel(xy)==rgb and list(rgb) not in colors
        samples.append(dict(rgb=list(rgb),hex='#'+''.join(f'{n:02X}' for n in rgb),source=SOURCE,source_xy=list(xy),source_sha256=hashlib.sha256(raw).hexdigest(),reason=reason))
    extra='\n# Owner-approved source teal extension; 2026-09-30\n'+''.join(f"{r['rgb'][0]:3} {r['rgb'][1]:3} {r['rgb'][2]:3}\t{r['hex']}\n" for r in samples)
    expected=original+extra.encode()
    current=(ROOT/PALETTE).read_bytes();assert current in (original,expected),'既存パレットの上書き禁止'
    (ROOT/PALETTE).write_bytes(expected)
    result=dict(baseline=BASE,original_sha256=hashlib.sha256(original).hexdigest(),original_colors=colors,original_color_count=72,
                new_color_count=76,selected=samples,palette_sha256=hashlib.sha256(expected).hexdigest(),
                reason='原画の暗い青緑が紺・灰に置き換わるため、原画に実在する暗部・中間色・明部を追加。')
    (ROOT/RECORD).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print('NATURAL_TEAL: 既存72色の順番・値・原本バイトを維持、4色追加',[(r['hex'],r['source_xy']) for r in samples])
if __name__=='__main__':main()
