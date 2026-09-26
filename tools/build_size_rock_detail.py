#!/usr/bin/env python3
"""体格と岩の変更前後を、実寸および最近傍拡大で並べる。"""
from pathlib import Path
import io,json,subprocess
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1];BASE='883af5e7aa563bcf59155c00137834c697eac153'
FONT=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',15)
def before(path):return Image.open(io.BytesIO(subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout)).convert('RGBA')

def main():
    rows=json.loads((ROOT/'assets/source_records/owner-monsters-size-review.json').read_text(encoding='utf8'))['imported'];by_id={r['id']:r for r in rows}
    ids=['slime','bat','ember_wisp','shadow_wolf','shell_guard','wet_beast','gate_beast','crowned_droplet']
    canvas=Image.new('RGB',(1680,600),'#ddd9cb');d=ImageDraw.Draw(canvas)
    for i,id_ in enumerate(ids):
        r=by_id[id_];x=i%4*420;y=i//4*300;path=r['path'];old=before(path);new=Image.open(ROOT/path).convert('RGBA')
        d.text((x+8,y+8),id_,font=FONT,fill='black')
        for j,im in enumerate([old,new]):
            b=im.getchannel('A').getbbox();im=im.crop(b);left=x+4+j*210
            canvas.paste(im,(left+(202-im.width)//2,y+225-im.height),im)
            d.text((left+5,y+237),('前 ' if j==0 else '後 ')+f'{im.width}×{im.height}',font=FONT,fill='black')
        d.text((x+8,y+270),r['size_class']+' / 余白を除いた実寸',font=FONT,fill='black')
    canvas.save(ROOT/'docs/verification/owner-monsters/size-before-after.png')
    # 倍率をそろえ、ぼかさずに岩の画素を比較する。
    canvas=Image.new('RGB',(1080,350),'#ddd9cb');d=ImageDraw.Draw(canvas)
    for i,name in enumerate(['wall_top','wall_side']):
        path=f'assets/tiles/cave_{name}.png'
        for j,im in enumerate([before(path),Image.open(ROOT/path).convert('RGBA')]):
            # 同じ32pxセル範囲を4倍へ拡大。
            x=i*540+j*265;d.text((x+10,8),name+(' / 前' if j==0 else ' / 後'),font=FONT,fill='black')
            detail=im.crop((0,0,64,64)).resize((256,256),Image.Resampling.NEAREST);canvas.paste(detail,(x+4,40),detail)
    d.text((8,310),'64×64pxの岩面を4倍表示 / 最近傍・補間なし',font=FONT,fill='black')
    canvas.save(ROOT/'docs/verification/art-review-2/rock-pixel-before-after.png')
    print('SIZE_ROCK_DETAIL: enemy_samples=8 wall_panels=4')

if __name__=='__main__':main()
