#!/usr/bin/env python3
"""取り込んだ敵の実寸一覧、置換比較、戦闘静止図、保留原画を出力する。"""
from pathlib import Path
import io,json,math
from PIL import Image,ImageDraw,ImageFont
from import_owner_monsters import ROOT,OUT,ORIGINAL,REPLACEMENTS,git_bytes,split_parts,SHEETS

FONT=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',13)
SMALL=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',11)

def battle(filename,enemy_ids,boss=False):
    background='plains' if 'plains' in filename else 'cave'
    im=Image.open(ROOT/f'assets/backgrounds/{background}.png').convert('RGBA')
    positions=[(24,244)] if boss else [(8,174),(99,216),(190,178)]
    for id_,(x,foot) in zip(enemy_ids,positions):
        pic=Image.open(ROOT/f'assets/monsters/{id_}/idle.png').convert('RGBA');im.alpha_composite(pic,(x,foot-pic.height))
    for i in range(4):
        pic=Image.open(ROOT/f'assets/characters/pc_{i+1:02}/battle.png').convert('RGBA').crop((0,0,48,48))
        im.alpha_composite(pic,(365+(i%2)*65,110+(i//2)*72))
    ImageDraw.Draw(im).text((8,5),'素材確認用の静止配置 / 512×288・拡大なし',font=FONT,fill='white',stroke_width=1,stroke_fill='black')
    im.save(OUT/filename)

def main():
    record=json.loads((ROOT/'assets/source_records/owner-monsters.json').read_text(encoding='utf8'));rows=record['imported']
    cols=6;cw,ch=212,206;sheet=Image.new('RGB',(cw*cols,math.ceil(len(rows)/cols)*ch),'#d9d5c7');d=ImageDraw.Draw(sheet)
    for i,r in enumerate(rows):
        pic=Image.open(ROOT/r['path']).convert('RGBA');x=i%cols*cw;y=i//cols*ch
        sheet.paste(pic,(x+(cw-pic.width)//2,y+164-pic.height),pic)
        d.text((x+5,y+169),r['id'],font=SMALL,fill='#20251d');d.text((x+5,y+185),r['name'],font=SMALL,fill='#20251d')
    sheet.save(OUT/'catalog-sheet.png')
    cw,ch=480,215;sheet=Image.new('RGB',(cw*2,ch*11),'#d9d5c7');d=ImageDraw.Draw(sheet)
    for i,(id_,(source,reason)) in enumerate(REPLACEMENTS.items()):
        x=i%2*cw;y=i//2*ch;old=Image.open(io.BytesIO(git_bytes(f'assets/monsters/{id_}/idle.png'))).convert('RGBA');new=Image.open(ROOT/f'assets/monsters/{id_}/idle.png').convert('RGBA')
        d.text((x+5,y+4),id_+(' / 置換' if source else ' / 旧画像維持'),font=FONT,fill='black')
        d.text((x+20,y+25),'旧',font=FONT,fill='black');d.text((x+240,y+25),'新',font=FONT,fill='black')
        sheet.paste(old,(x+80-old.width//2,y+204-old.height),old);sheet.paste(new,(x+335-new.width//2,y+204-new.height),new)
    sheet.save(OUT/'replacement-before-after.png')
    battle('battle-mock-plains.png',['slime','shadow_wolf','shell_guard']);battle('battle-mock-cave.png',['bat','crystal_slime','bone_wolf']);battle('boss-mock.png',['gate_beast'],True)
    held=record['held_back'];cw,ch=330,280;sheet=Image.new('RGB',(cw*4,math.ceil(len(held)/4)*ch),'#d9d5c7');d=ImageDraw.Draw(sheet);cache={}
    for i,r in enumerate(held):
        file=Path(r['original_file']).name;im=Image.open(ROOT/r['original_file']).convert('RGBA')
        if r['slot']!='all':
            number=int(file[4:8])
            if file not in cache:cache[file]=split_parts(im,len(SHEETS[number].split(';')),40 if number==929 else 24)
            part,box=cache[file][r['slot']-1];im=part.crop(box)
        im.thumbnail((310,235),Image.Resampling.NEAREST);x=i%4*cw;y=i//4*ch
        sheet.paste(im,(x+(cw-im.width)//2,y+26+(235-im.height)//2),im)
        d.text((x+5,y+5),f"保留 {file} / {r['slot']}",font=FONT,fill='black')
    sheet.save(OUT/'held-back.png')
    print(f'OWNER_REVIEW_PASS: catalog={len(rows)} comparisons=22 battle_mocks=3 held_records={len(held)}')

if __name__=='__main__':main()
