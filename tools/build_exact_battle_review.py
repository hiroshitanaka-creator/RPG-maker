"""依頼者の見本と実描画、頭・顔の保護範囲を確認画像にする。"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/verification/battle-layout-exact'
JOBS = [('warrior','戦士'),('martial_artist','武闘家'),('priest','僧侶'),('mage','魔法使い')]


def main():
    font = ImageFont.truetype(str(ROOT / 'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    font.set_variation_by_axes([500])
    reference = ROOT / 'docs/reference/visual-targets/battle-layout-mock.png'
    target = Image.open(reference).convert('RGB')
    sheet = Image.new('RGB',(2064,1210),'#17232b');draw=ImageDraw.Draw(sheet)
    draw.text((8,8),'依頼者の見本',font=font,fill='white')
    draw.text((1048,8),'本番描画：上は通常／下は2人目の行動',font=font,fill='white')
    sheet.paste(target,(0,42))
    sheet.paste(Image.open(OUT/'01-party-four.png').convert('RGB'),(1040,42))
    sheet.paste(Image.open(OUT/'02-attack.png').convert('RGB'),(1040,626))
    sheet.save(OUT/'target-comparison.png')
    heads = Image.new('RGB',(2304,936),'#17232b');draw=ImageDraw.Draw(heads)
    definitions = json.loads((OUT/'head-pixels.json').read_text(encoding='utf-8'))['head_regions']
    draw.text((8,4),'黄色枠の和集合にある不透明画素を保護。動作ごとに頭と顎を囲み、肩・襟と区別。',font=font,fill='white')
    records=[]
    for row,(job,title) in enumerate(JOBS):
        for member in range(4):
            source=ROOT/f'assets/characters/pc_{member+1:02}/jobs/{job}/battle.png'
            image=Image.open(source).convert('RGBA').resize((576,192),Image.Resampling.NEAREST)
            x,y=member*576,42+row*222
            draw.text((x+4,y),f'{title} pc_{member+1:02}：待機／攻撃／被弾',font=font,fill='white')
            heads.paste(image,(x,y+26),image)
            for pose in range(3):
                for rx,ry,rw,rh in definitions[job][pose]:
                    rx,ry,rw,rh=map(int,(rx,ry,rw,rh))
                    draw.rectangle((x+pose*192+rx*2,y+26+ry*2,x+pose*192+(rx+rw)*2-1,y+26+(ry+rh)*2-1),outline='#ffdd55',width=1)
            records.append({'path':source.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_frame':[96,96],'regions_by_pose':definitions[job],'poses':[0,1,2],'protected':'矩形の和集合内にある不透明画素。頭・髪・帽子・顔・顎を含む。'})
    heads.save(OUT/'head-regions.png')
    (OUT/'head-regions.json').write_text(json.dumps({'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),'regions':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('EXACT_REVIEW_SAVED: comparison=1 head_regions=16 poses=48')


if __name__ == '__main__':
    main()
