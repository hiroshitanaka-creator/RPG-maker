"""本番描画による14背景の確認画像を一覧へ並べる。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'docs/verification/battle-compact'
NAMES = [('plains','平原'),('forest','森'),('cave','洞窟'),('tower','塔'),
         ('desert','砂漠'),('sea','海'),('sky','空'),('castle','城'),
         ('snowfield','雪原'),('volcano','火山'),('ruins','遺跡'),
         ('underworld','死者の国'),('temple','神殿の中'),('final_land','最後の地')]


def main():
    sheet = Image.new('RGB', (2048, 1280), '#17232b')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(ROOT / 'assets/fonts/notosansjp/NotoSansJP.ttf'), 18)
    font.set_variation_by_axes([500])
    for i, (identifier, name) in enumerate(NAMES):
        x, y = i % 4 * 512, i // 4 * 320
        draw.text((x+8,y+3), name + ('（新原画）' if i < 8 else '（継続）'), font=font, fill='white')
        frame = Image.open(OUTPUT / f'background-{identifier}.png').convert('RGB')
        sheet.paste(frame.resize((512,288), Image.Resampling.NEAREST), (x,y+30))
    sheet.save(OUTPUT / 'backgrounds-14.png')
    print('GROUND_REVIEW_SAVED: backgrounds=14 replacement=8')


if __name__ == '__main__':
    main()
