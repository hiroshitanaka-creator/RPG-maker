"""保管済みの地上敵候補を並べる。元の素材は編集しない。"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/verification/sprint6-coast'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'world/second_region_coast.json').read_text(encoding='utf8'))
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    small=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),16)
    image=Image.new('RGB',(1140,440),'#17243c');draw=ImageDraw.Draw(image)
    draw.text((20,12),'今後の遺跡の近くの候補：通常遭遇へは未登録',font=font,fill='white')
    origins={'desert_mummy':'IMG_1183 右','stone_gargoyle':'IMG_0952 左から2'}
    for i,entry in enumerate(config['ground_proposals']):
        x=20+i*375
        sprite=Image.open(ROOT/f"assets/monsters/{entry['sprite_id']}/idle.png").convert('RGBA')
        sprite=sprite.crop(sprite.getbbox())
        displayed=sprite.resize((round(sprite.width*.75),round(sprite.height*.75)),Image.Resampling.NEAREST)
        image.paste(displayed,(x+100-displayed.width//2,140-displayed.height),displayed)
        zoom=displayed.resize((displayed.width*3,displayed.height*3),Image.Resampling.NEAREST)
        image.paste(zoom,(x+180,65),zoom)
        draw.text((x,270),entry['name'],font=font,fill='white')
        draw.text((x,306),origins[entry['sprite_id']],font=small,fill='#ddd6bf')
        draw.text((x,332),entry['role'],font=small,fill='#ddd6bf')
        draw.text((x,370),'左：画面上の大きさ　右：3倍',font=small,fill='white')
    image.save(OUT/'ruins-reserve.png')
    print('SECOND_COAST_REVIEW: ruins-reserve.png')
if __name__=='__main__':main()
