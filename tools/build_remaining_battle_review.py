"""指定原画と取り込み結果の比較、12職の一覧を作る。原本は変更しない。"""
from pathlib import Path
import argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from import_remaining_battles import JOBS,NAMES,OUT,ROOT

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--jobs',nargs='+',choices=JOBS,required=True);args=parser.parse_args()
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20);font.set_variation_by_axes([500])
    for job in args.jobs:
        original=Image.open(ROOT/f'assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_{JOBS[job]}.PNG').convert('RGB')
        result=Image.new('RGB',(1200,490),'#d6d1bc');draw=ImageDraw.Draw(result)
        draw.text((12,8),f'{NAMES[job]}：上は依頼者原画、下は96px取り込み結果（待機・攻撃・被弾）',font=font,fill='#17232b')
        for actor in range(4):
            x=actor*300;draw.text((x+12,40),['カイナ','リオネ','ハルド','スイナ'][actor],font=font,fill='#17232b')
            piece=original.crop((actor*original.width//4,0,(actor+1)*original.width//4,original.height))
            array=np.asarray(piece);mask=np.max(array,axis=2)>20
            ys,xs=np.where(mask);piece=piece.crop((int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1))
            scale=min(240/piece.width,224/piece.height)
            piece=piece.resize((round(piece.width*scale),round(piece.height*scale)),Image.Resampling.NEAREST)
            result.paste(piece,(x+(300-piece.width)//2,70))
            sheet=Image.open(ROOT/f'assets/characters/pc_{actor+1:02}/jobs/{job}/battle.png')
            result.paste(sheet,(x+6,326),sheet)
            draw.text((x+8,440),'待機      攻撃      被弾',font=font,fill='#17232b')
        result.save(OUT/f'{job}-reference-comparison.png')
    if all((ROOT/f'assets/characters/pc_01/jobs/{job}/battle.png').exists() for job in NAMES):
        overview=Image.new('RGB',(1240,1752),'#d6d1bc');draw=ImageDraw.Draw(overview)
        for row,(job,title) in enumerate(NAMES.items()):
            y=row*146;draw.text((8,y+4),title,font=font,fill='#17232b')
            for actor in range(4):
                sheet=Image.open(ROOT/f'assets/characters/pc_{actor+1:02}/jobs/{job}/battle.png')
                overview.paste(sheet,(44+actor*296,y+38),sheet)
        overview.save(OUT/'all-twelve-jobs.png')
    print('BATTLE_REVIEW_SAVED: comparisons='+','.join(args.jobs))

if __name__=='__main__':main()
