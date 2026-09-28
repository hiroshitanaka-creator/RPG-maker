"""人物別の原画比較、4人×8系統、歩行、暗所の本番画面を一覧にする。"""
import argparse,json
from PIL import Image,ImageDraw,ImageFont
from prepare_party_forms import ROOT,RAW,REVIEW,FORMS,NAMES,ACTORS

def main():
    p=argparse.ArgumentParser();p.add_argument('--actors',nargs='+',default=list(ACTORS));p.add_argument('--runtime',action='store_true');args=p.parse_args()
    visuals=json.loads((ROOT/'data/character_visuals.json').read_text(encoding='utf-8'))
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    REVIEW.mkdir(parents=True,exist_ok=True)
    for actor in args.actors:
        canvas=Image.new('RGB',(1160,8*244),'#d8d4c7');d=ImageDraw.Draw(canvas)
        walks=Image.new('RGB',(8*210,540),'#d8d4c7');wd=ImageDraw.Draw(walks)
        for row,form in enumerate(FORMS):
            d.text((12,row*244+4),ACTORS[actor][0]+' '+NAMES[form]+'：原画 ／ 待機・攻撃・被弾 ／ 72px表示',font=font,fill='#162835')
            ref=Image.open(RAW/f'{actor}-{form}-reference.png');ref.thumbnail((230,200),Image.Resampling.NEAREST)
            canvas.paste(ref,(12+(230-ref.width)//2,row*244+36),ref)
            original=Image.open(ROOT/visuals['actors'][actor]['forms'][form]['battle'])
            battle=original.resize((576,192),Image.Resampling.NEAREST);canvas.paste(battle,(260,row*244+38),battle)
            small=original.crop((0,0,96,96)).resize((72,72),Image.Resampling.NEAREST).resize((144,144),Image.Resampling.NEAREST)
            canvas.paste(small,(875,row*244+75),small)
            wd.text((row*210+8,8),NAMES[form],font=font,fill='#162835')
            im=Image.open(ROOT/visuals['actors'][actor]['forms'][form]['walk']).resize((192,384),Image.Resampling.NEAREST)
            walks.paste(im,(row*210+8,44),im)
        wd.text((8,455),ACTORS[actor][0]+'：上から下・左・右・上、各3コマ。32×48pxの2倍表示。',font=font,fill='#162835')
        canvas.save(REVIEW/f'{actor}-source-battle.png');walks.save(REVIEW/f'{actor}-walk.png')
    if len(args.actors)==3:
        overview=Image.new('RGB',(4*220,8*224+40),'#d8d4c7');d=ImageDraw.Draw(overview)
        all_actors=['pc_01']+list(ACTORS)
        for col,actor in enumerate(all_actors):d.text((col*220+12,6),'カイナ' if actor=='pc_01' else ACTORS[actor][0],font=font,fill='#162835')
        for row,form in enumerate(FORMS):
            for col,actor in enumerate(all_actors):
                d.text((col*220+10,40+row*224),NAMES[form],font=font,fill='#162835')
                im=Image.open(ROOT/visuals['actors'][actor]['forms'][form]['battle']).crop((0,0,96,96)).resize((192,192),Image.Resampling.NEAREST)
                overview.paste(im,(col*220+14,70+row*224),im)
        overview.save(REVIEW/'all-32-forms.png')
    if args.runtime:
        for bg,title in [('cave','洞窟'),('underworld','死者の国')]:
            canvas=Image.new('RGB',(1024,4*316),'#d8d4c7');d=ImageDraw.Draw(canvas)
            for i,form in enumerate(FORMS):
                x=i%2*512;y=i//2*316;d.text((x+8,y+2),NAMES[form]+'系の4人 ／ '+title,font=font,fill='#162835')
                im=Image.open(REVIEW/'runtime'/f'{form}-{bg}.png').resize((512,288),Image.Resampling.NEAREST);canvas.paste(im,(x,y+28))
            canvas.save(REVIEW/f'battle-{bg}.png')
    print('PARTY_REVIEW_IMAGES:',','.join(args.actors))

if __name__=='__main__':main()
