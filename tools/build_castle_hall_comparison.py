"""城の大広間・謁見の間・灯台の見張り部屋の、変更前後の実画面の比較画像と、歩いて出入りした画面の一覧を作る。"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'docs/verification/castle-hall-backdrops'
F=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),22)

def sheet(out,rows):
    W,H,pad=512,288,8
    cols=max(len(r[1]) for r in rows)
    img=Image.new('RGB',(cols*(W+pad)+pad,len(rows)*(H+40+pad)+pad),'#d6d2bb');d=ImageDraw.Draw(img)
    for ri,(title,items) in enumerate(rows):
        for ci,(cap,path) in enumerate(items):
            x=pad+ci*(W+pad);y=pad+ri*(H+40+pad)
            d.text((x,y),f'{title}｜{cap}',font=F,fill='#14212b')
            img.paste(Image.open(V/path).convert('RGB').resize((W,H),Image.Resampling.NEAREST),(x,y+34))
    img.save(V/out)

sheet('before-after.png',[
 ('謁見の間',[('変更前','before/castle/04-throne-hall.png'),('変更後 入口','runtime/04-throne-room-entered.png'),('変更後 玉座の前','runtime/05-throne-room-king.png')]),
 ('大広間（新設）',[('入口（中庭から）','runtime/02-great-hall-entered.png'),('奥の3扉','runtime/03-great-hall-throne-door.png'),('書庫から戻った所','runtime/12-great-hall-from-library.png')]),
 ('灯台の見張り部屋',[('変更前','before/port/11-lighthouse-room.png'),('変更後 入口','runtime-lighthouse/02-lighthouse-entered.png'),('変更後 窓の下','runtime-lighthouse/04-under-window.png')]),
])
sheet('walk-through.png',[
 ('中庭→大広間',[('中庭','runtime/01-court.png'),('大広間に入る','runtime/02-great-hall-entered.png'),('謁見の間の扉の前','runtime/03-great-hall-throne-door.png')]),
 ('謁見の間',[('謁見の間に入る','runtime/04-throne-room-entered.png'),('王の前','runtime/05-throne-room-king.png'),('王と会話','runtime/06-royal-audience.png')]),
 ('解放と宝物庫・書庫',[('転職','runtime/07-job-change.png'),('宝物庫','runtime/10-treasury.png'),('書庫','runtime/11-library.png')]),
])
