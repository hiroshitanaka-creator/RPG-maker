"""本番画面3段階を並べ、人物部分を最近傍で拡大して比較する。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/erosion-pattern-preview'
def main():
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),22)
    for kind,box in [('battle',(708,78,864,234)),('walk',(478,224,558,336))]:
        panel=Image.new('RGB',(1536,670),'#d8d4c7');d=ImageDraw.Draw(panel)
        for col,stage in enumerate([0,30,60]):
            d.text((col*512+12,8),{0:'侵蝕なし 0〜29',30:'兆候 30〜59',60:'変異 60〜89'}[stage],font=font,fill='#162835')
            image=Image.open(OUT/'runtime'/f'{kind}-{stage}.png')
            panel.paste(image.resize((512,288),Image.Resampling.NEAREST),(col*512,42))
            crop=image.crop(box);crop=crop.resize((312,312) if kind=='battle' else (200,280),Image.Resampling.NEAREST)
            panel.paste(crop,(col*512+(512-crop.width)//2,348))
        panel.save(OUT/f'{kind}-stages.png')
    print('EROSION_REVIEW: 戦闘・歩行の実画面と人物部分の拡大を保存')
if __name__=='__main__':main()
