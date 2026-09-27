"""実描画を並べた14背景一覧と字体比較。元の画像は加工しない。"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'docs/verification/battle-fonts'
NAMES = {'plains':'平原','forest':'森','cave':'洞窟','tower':'塔','desert':'砂漠','sea':'海','sky':'空','castle':'城',
         'snowfield':'雪原','volcano':'火山','ruins':'遺跡','underworld':'死者の国','temple':'神殿の中','final_land':'最後の地'}


def main():
    record = json.loads((OUTPUT / 'capture-record.json').read_text(encoding='utf-8'))
    font = ImageFont.truetype(str(ROOT / 'assets/fonts/notosansjp/NotoSansJP.ttf'), 18)
    font.set_variation_by_axes([500])
    sheet = Image.new('RGB', (2048,1280), '#17232b')
    draw = ImageDraw.Draw(sheet)
    for i,(identifier,name) in enumerate(NAMES.items()):
        x,y = (i%4)*512,(i//4)*320
        offset = record['background_layout'][identifier][0]
        draw.text((x+8,y+2), f'{name} / 原寸・上へ{offset}px', font=font, fill='white')
        frame = Image.open(OUTPUT / f'notosansjp-{identifier}.png').convert('RGB')
        sheet.paste(frame.resize((512,288), Image.Resampling.NEAREST), (x,y+30))
    sheet.save(OUTPUT / 'backgrounds-14.png')
    compare = Image.new('RGB', (2064,620), '#17232b')
    draw = ImageDraw.Draw(compare)
    for i,(identifier,title) in enumerate([('notosansjp','Noto Sans JP（正式採用）'),('dotgothic16','DotGothic16（比較記録・不採用）')]):
        draw.text((i*1040+8,8), title, font=font, fill='white')
        compare.paste(Image.open(OUTPUT / f'{identifier}-plains.png').convert('RGB'), (i*1040,40))
    compare.save(OUTPUT / 'font-comparison.png')
    print('FONT_REVIEW_SAVED: 背景14種、字体2種の実描画を合成')


if __name__ == '__main__':
    main()
