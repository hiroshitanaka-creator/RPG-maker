"""目標画像と実ゲームを、縦横比を保ったまま並べる。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/verification/battle-layout-target'


def main():
    target=Image.open(ROOT/'docs/reference/visual-targets/battle-layout-target.jpg').convert('RGB')
    target.thumbnail((1024,720),Image.Resampling.LANCZOS)
    game=Image.open(OUTPUT/'01-party-four.png').convert('RGB')
    height=max(target.height,game.height)
    board=Image.new('RGB',(2080,height+56),'#162835');draw=ImageDraw.Draw(board)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20);font.set_variation_by_axes([500])
    draw.text((8,8),'目標画像（依頼者原画・縦横比を維持）',font=font,fill='white')
    draw.text((1056,8),'実ゲーム（512×288を2倍表示・人物72px）',font=font,fill='white')
    board.paste(target,(0,48+(height-target.height)//2))
    board.paste(game,(1056,48+(height-game.height)//2))
    board.save(OUTPUT/'target-comparison.png')
    print('TARGET_COMPARISON_SAVED: 目標原画と実描画を同倍率相当で比較')


if __name__=='__main__':main()
