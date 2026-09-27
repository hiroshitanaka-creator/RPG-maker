"""Godotが描画した比較画像を最近傍で整数倍拡大する。72px画像はPythonでは作らない。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/verification/battle-layout-target'
JOBS={'warrior':'戦士（採用：短い剣の案）','martial_artist':'武闘家','priest':'僧侶','mage':'魔法使い'}


def main():
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    font.set_variation_by_axes([500])
    board=Image.new('RGB',(912,4*512),'#162835');draw=ImageDraw.Draw(board)
    for row,(job,title) in enumerate(JOBS.items()):
        y=row*512
        draw.text((16,y+4),title+' / カイナ・待機',font=font,fill='white')
        draw.text((32,y+31),'96px原寸（拡大表示）',font=font,fill='white')
        draw.text((520,y+31),'72px実表示（拡大表示）',font=font,fill='white')
        frame=Image.open(OUTPUT/f'scaling/{job}-pc_01-0.png').convert('RGB')
        assert frame.size==(448,224)
        board.paste(frame.resize((896,448),Image.Resampling.NEAREST),(8,y+64))
    board.save(OUTPUT/'scaling-four-jobs.png')
    all_members=Image.new('RGB',(1792,4*264),'#162835');draw=ImageDraw.Draw(all_members)
    for row,(job,title) in enumerate(JOBS.items()):
        for actor in range(1,5):
            x=(actor-1)*448;y=row*264
            draw.text((x+8,y+3),title.split('（')[0]+f' pc_{actor:02} / 左96・右72',font=font,fill='white')
            all_members.paste(Image.open(OUTPUT/f'scaling/{job}-pc_{actor:02}-0.png').convert('RGB'),(x,y+36))
    all_members.save(OUTPUT/'scaling-all-members.png')
    print('SCALING_REVIEW_SAVED: 4職の拡大比較と16人分の一覧。実描画の画素を整数倍で保持')


if __name__=='__main__':main()
