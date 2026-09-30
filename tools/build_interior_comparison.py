"""建物の中の変更前・変更後の実画面を並べた比較画像を作る（部屋ごと）。

  python tools/build_interior_comparison.py [--town village|castle|port|all]

docs/verification/interior-backdrops/{before,after}/<町>/ の実画面（capture_interior_rooms.gd の出力）、
依頼者の原画、通行地図の重ね合わせ図を、docs/verification/interior-backdrops/<部屋>/before-after.png に並べる。
"""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'docs/verification/interior-backdrops'
TOWN={'start_village':'village','first_castle':'castle','first_port':'port'}
CELL=(640,360)

def fit(image:Image.Image,size:tuple[int,int])->Image.Image:
    image=image.convert('RGB');image.thumbnail(size,Image.Resampling.LANCZOS)
    out=Image.new('RGB',size,(20,14,10));out.paste(image,((size[0]-image.width)//2,(size[1]-image.height)//2));return out

def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--town',default='all',choices=['village','castle','port','all']);args=ap.parse_args()
    record=json.loads((ROOT/'assets/source_records/interior-backdrops.json').read_text(encoding='utf8'))
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),18)
    for name,room in record['rooms'].items():
        town=TOWN[room['node']]
        if args.town!='all' and args.town!=town:continue
        prefix=f"{town}-{room['room']:02d}"
        talks=sorted((V/'after'/town).glob(prefix+'-2-talk-*.png'))
        cells=[('変更前：扉から入った直後',V/'before'/town/(prefix+'-1-entered.png')),('変更後：扉から入った直後',V/'after'/town/(prefix+'-1-entered.png'))]
        for talk in talks:
            event=talk.stem.split('-2-talk-')[1]
            cells.append((f'変更前：話しかけたところ（{event}）',V/'before'/town/talk.name));cells.append((f'変更後：話しかけたところ（{event}）',talk))
        cells.append(('依頼者の原画（無加工）',ROOT/room['original']));cells.append(('通行地図（緑＝歩ける／赤＝通れない／青＝住人／黄＝扉）',V/name/'collision-overlay.png'))
        rows=(len(cells)+1)//2;pad=28
        sheet=Image.new('RGB',(CELL[0]*2,(CELL[1]+pad)*rows),(20,14,10));d=ImageDraw.Draw(sheet)
        for i,(label,path) in enumerate(cells):
            x=(i%2)*CELL[0];y=(i//2)*(CELL[1]+pad)
            image=Image.open(path) if path.exists() else Image.new('RGB',CELL,(60,0,0))
            sheet.paste(fit(image,CELL),(x,y+pad));d.text((x+8,y+3),label,font=font,fill=(255,255,255))
        d.text((CELL[0]*2-330,3),f"{room['title']}（{room['room_size_before'][0]}×{room['room_size_before'][1]}→16×12マス）",font=font,fill=(255,220,120))
        (V/name).mkdir(parents=True,exist_ok=True)
        sheet.convert('P',palette=Image.Palette.ADAPTIVE,colors=256).save(V/name/'before-after.png',optimize=True)
        print('INTERIOR_COMPARISON:',name,sheet.size)

if __name__=='__main__':main()
