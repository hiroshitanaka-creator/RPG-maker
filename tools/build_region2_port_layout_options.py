"""第2地方の港町の配置案を描く。本番地図・原画・素材を変更しない。"""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/verification/region2-port-layout'
INCOMING = ROOT / 'assets/_incoming/owner-2026-10-01-region2-port'
TARGET = ROOT / 'docs/reference/visual-targets/region2-port-town.png'
S = 24
W, H = 48*S, 32*S
INK = '#273831'
FONT_PATH = str(ROOT / 'assets/fonts/notosansjp/NotoSansJP.ttf')
FONT = ImageFont.truetype(FONT_PATH, 23)
SMALL = ImageFont.truetype(FONT_PATH, 19)
TITLE = ImageFont.truetype(FONT_PATH, 30)
for font in (FONT,SMALL,TITLE):font.set_variation_by_name('Medium')
SOURCES = {
    'FE4B1B12-C9B1-4DB0-B374-81F51D061BA6.PNG': '港町の外観・町の目標',
    '75462BFD-D5F5-4BEC-94EF-2241C7A1D0C7.PNG': '宿屋の中',
    '7BDBE31E-F3AF-49E2-AD04-6505CCEA796C.PNG': '道具屋の中',
    'C9A48E60-3050-4DE6-AB1F-5399C014323B.PNG': '武器屋の中',
    'A57472FD-36AF-4085-BA41-25B571A3F2AF.PNG': '防具屋の中',
    'FBE86B94-685C-4745-85C0-B45FF36DCCFF.PNG': '祠の中',
    '4D2815AA-E544-49BB-9714-0B9E8FB43D94.PNG': '港務所の中',
}
# 座標は提案上の32pxタイル単位。実ゲームへは接続しない。
PLANS = [
    dict(id='A', title='入り江を囲む町（推奨）',
         note='広場から岩の岸を回って中央桟橋へ。目標の絵の配置を最も近く保つ。',
         tradeoff='港の北側と西側を歩いて回れる。桟橋の先へは少し遠回り。',
         coast=[(48,9),(46,12),(43,16),(40,18),(33,18),(29,19),(25,23),(23,27),(20,32)],
         buildings=[('宿屋',18,3,7,5),('道具屋',29,4,6,4),('武器屋',4,12,6,5),('防具屋',35,11,6,5),('祠',40,3,4,5),('港務所',40,19,6,4),('民家1',4,23,6,4),('民家2',14,24,6,4)],
         well=(22,14), markets=[(17,11),(25,11),(17,17),(25,17)],
         roads=[[(5,5),(9,9),(15,10),(22,10),(22,14),(29,17),(30,19)],[(7,18),(13,20),(22,20),(28,18),(38,17),(42,17),(42,19)],[(7,22),(10,20)],[(17,23),(17,20)],[(22,9),(31,9),(39,9),(42,9)],[(22,20),(23,25),(25,26)]],
         piers=[[(30,18),(30,28),(43,28)],[(42,17),(42,28)],[(25,23),(25,26),(30,26)],[(30,22),(34,22)]],
         platform=(39,18,8,6), ship=(36,25), boats=[(27,24),(44,30),(28,30)]),
    dict(id='B', title='広場から港へまっすぐ',
         note='店と井戸広場を近づけ、広場から中央桟橋へ一本の道で向かう。',
         tradeoff='買い物と乗船の往復が短い。原画より道が整然として見える。',
         coast=[(48,10),(45,12),(43,16),(40,18),(34,18),(29,20),(27,25),(25,28),(23,32)],
         buildings=[('宿屋',16,3,7,5),('道具屋',26,4,6,4),('武器屋',7,11,6,5),('防具屋',32,11,6,5),('祠',40,3,4,5),('港務所',40,19,6,4),('民家1',5,23,6,4),('民家2',16,24,6,4)],
         well=(22,14), markets=[(17,11),(25,11),(17,17),(25,17)],
         roads=[[(5,5),(10,9),(22,9),(22,14),(22,20),(30,20)],[(10,17),(14,19),(22,20)],[(22,9),(35,9),(42,9)],[(35,17),(35,18),(42,18),(42,19)],[(8,22),(8,20),(22,20)],[(19,23),(19,20)]],
         piers=[[(29,20),(30,20),(30,28),(43,28)],[(42,18),(42,28)],[(28,25),(30,25)],[(30,22),(33,22)]],
         platform=(39,18,8,6), ship=(36,25), boats=[(32,26),(45,30),(28,29)]),
    dict(id='C', title='遺跡の小路を巡る町',
         note='西の民家と崩れた遺跡を結ぶ小路を設け、広場へ回り込める配置。',
         tradeoff='砂と遺跡の土地を歩く時間が増える。施設間の移動は3案で最も長い。',
         coast=[(48,9),(46,11),(44,16),(38,18),(30,18),(25,20),(23,24),(22,29),(18,32)],
         buildings=[('宿屋',19,3,7,5),('道具屋',29,5,6,4),('武器屋',6,12,6,5),('防具屋',35,12,6,5),('祠',41,3,4,5),('港務所',40,19,6,4),('民家1',3,23,6,4),('民家2',13,24,6,4)],
         well=(23,14), markets=[(18,11),(26,11),(18,17),(26,17)],
         roads=[[(5,5),(12,9),(23,10),(23,14),(30,17),(37,18),(42,18),(42,19)],[(12,9),(14,18),(11,21),(11,28),(19,29),(21,25),(22,20),(23,14)],[(9,18),(14,18)],[(6,22),(11,21)],[(16,23),(16,21),(22,20)],[(23,10),(32,10),(43,10),(43,9)]],
         piers=[[(29,18),(29,28),(43,28)],[(42,18),(42,28)],[(24,22),(24,25),(29,25)],[(29,22),(33,22)]],
         platform=(39,18,8,6), ship=(35,25), boats=[(26,23),(44,30),(27,30)]),
]


def points(seq):
    return [(int(x*S), int(y*S)) for x,y in seq]


def label(draw, xy, text, font=FONT, fill=INK):
    draw.text(xy, text, font=font, fill=fill, anchor='mm', stroke_width=0)


def diagram(plan):
    im=Image.new('RGB',(W,H),'#dbbd7c');d=ImageDraw.Draw(im)
    coast=points(plan['coast'])
    d.polygon(coast+[(W,H)],fill='#397d91')
    for y in range(0,H,S):
        d.line([(0,y),(W,y)],fill='#d2b578',width=1)
    # 海を引き直し、岸はなだらかにつながる岩の帯として示す。
    d.polygon(coast+[(W,H)],fill='#397d91')
    d.line(coast,fill='#826f53',width=12,joint='curve')
    for a,b in zip(coast,coast[1:]):
        count=max(1,int(math.dist(a,b)/22))
        for i in range(count):
            x=a[0]+(b[0]-a[0])*i/count;y=a[1]+(b[1]-a[1])*i/count
            d.ellipse((x-7,y-5,x+7,y+5),fill='#b49b71',outline='#6d654e')
    for road in plan['roads']:
        p=points(road);d.line(p,fill='#aa966f',width=52,joint='curve');d.line(p,fill='#ece0b7',width=45,joint='curve')
        for x,y in p:d.ellipse((x-22,y-22,x+22,y+22),fill='#ece0b7')
    wx,wy=points([plan['well']])[0]
    d.ellipse((wx-145,wy-128,wx+145,wy+128),fill='#d6c9a6',outline='#aa966f',width=3)
    for pier in plan['piers']:
        p=points(pier);d.line(p,fill='#5a402a',width=50,joint='curve');d.line(p,fill='#b88950',width=42,joint='curve')
        for a,b in zip(p,p[1:]):
            n=max(1,int(math.dist(a,b)/12))
            for i in range(n+1):
                x=a[0]+(b[0]-a[0])*i/n;y=a[1]+(b[1]-a[1])*i/n
                if a[0]==b[0]:d.line((x-19,y,x+19,y),fill='#80603b',width=2)
                else:d.line((x,y-19,x,y+19),fill='#80603b',width=2)
    x,y,w,h=plan['platform'];d.rectangle((x*S,y*S,(x+w)*S,(y+h)*S),fill='#b88950',outline='#5a402a',width=4)
    for yy in range(y*S,(y+h)*S,12):d.line((x*S,yy,(x+w)*S,yy),fill='#80603b',width=2)
    for name,x,y,w,h in plan['buildings']:
        rect=(x*S,y*S,(x+w)*S,(y+h)*S)
        d.rectangle((rect[0]+5,rect[1]+8,rect[2]+5,rect[3]+8),fill='#a68d59')
        d.rectangle(rect,fill='#eed5a0',outline='#6e583a',width=3)
        d.rectangle((rect[0]+8,rect[1]+8,rect[2]-8,rect[3]-18),fill='#d5b77c',outline='#9b7b48',width=2)
        cx=(x+w/2)*S;bottom=(y+h)*S
        d.rectangle((cx-12,bottom-15,cx+12,bottom),fill='#463626')
        colors={'宿屋':'#a74838','道具屋':'#3579a6','武器屋':'#a74838','防具屋':'#d5a645','港務所':'#3579a6'}
        if name in colors:d.rectangle((rect[0]+12,bottom-27,rect[2]-12,bottom-17),fill=colors[name])
        if name=='宿屋':d.line((rect[0]+8,rect[1]+20,rect[2]-8,rect[1]+20),fill='#786344',width=3)
        if name in ['祠','防具屋']:
            radius=27 if name=='祠' else 17
            d.ellipse((cx-radius,rect[1]+8,cx+radius,rect[1]+8+radius*2),fill='#d5ab50',outline='#856735',width=2)
        text_y=rect[1]+27 if name in ['道具屋','武器屋','防具屋','港務所'] else (y+h*.57)*S
        label(d,(cx,text_y),name)
        if name=='港務所':label(d,(cx,bottom-39),'錨・縄',SMALL)
        if name=='武器屋':label(d,(cx,bottom-39),'槍・剣',SMALL)
        if name=='防具屋':label(d,(cx,bottom-39),'盾・鎧',SMALL)
        if name=='道具屋':label(d,(cx,bottom-39),'壺・瓶',SMALL)
    for i,(x,y) in enumerate(plan['markets']):
        x*=S;y*=S
        d.rectangle((x-35,y-22,x+35,y+24),fill='#d9b87f',outline='#6f573a',width=2)
        d.rectangle((x-35,y-22,x+35,y-8),fill=['#b4513b','#3d79a2','#c69335','#b89a57'][i])
        label(d,(x,y+7),f'露店{i+1}',SMALL)
    d.ellipse((wx-28,wy-28,wx+28,wy+28),fill='#8b7758',outline='#5b523e',width=3)
    d.ellipse((wx-18,wy-18,wx+18,wy+18),fill='#397d91')
    label(d,(wx,wy+49),'井戸広場')
    # 北西の出口。砂色のアーチと南西・北東の遺跡。
    d.rounded_rectangle((3*S,1*S,7*S,5*S),radius=35,fill='#ab915e',outline='#65543a',width=4)
    d.rounded_rectangle((4*S,2*S,6*S,5*S),radius=20,fill='#e9d9af')
    label(d,(5*S,6*S),'石アーチ出口',SMALL)
    for x,y in [(3,29),(7,30),(12,30),(33,1),(37,2),(46,5)]:
        d.rectangle((x*S-8,y*S-17,x*S+9,y*S+10),fill='#b59c6b',outline='#756343',width=2)
        d.line((x*S-12,y*S+12,x*S+15,y*S+12),fill='#756343',width=4)
    for x,y in [(1,28),(7,29),(30,1),(44,2)]:
        for i in range(4):
            d.rectangle(((x+i*.55)*S,y*S,(x+i*.55+.5)*S,(y+.4)*S),fill='#aa9061',outline='#756343',width=2)
    label(d,(9*S,31*S),'崩れた石柱・石壁',SMALL)
    for x,y in [(1,8),(2,20),(12,4),(15,29),(37,6),(46,14)]:
        x*=S;y*=S;d.line((x,y,x-3,y+25),fill='#785733',width=6)
        for a in range(0,360,60):
            dx=math.cos(math.radians(a))*24;dy=math.sin(math.radians(a))*16
            d.line((x,y,x+dx,y+dy),fill='#527245',width=7)
    sx,sy=points([plan['ship']])[0]
    d.ellipse((sx-38,sy-70,sx+38,sy+65),fill='#704b2c',outline='#e6c681',width=4)
    d.line((sx,sy-60,sx,sy+40),fill='#eedab0',width=4)
    d.polygon([(sx-3,sy-55),(sx-3,sy+17),(sx-35,sy+8)],fill='#fff1d2')
    d.polygon([(sx+4,sy-45),(sx+4,sy+28),(sx+34,sy+17)],fill='#eee0ba')
    label(d,(sx,sy+5),'帆船',SMALL)
    d.ellipse((sx-7,28*S-7,sx+7,28*S+7),fill='#fff4b9',outline=INK,width=2)
    label(d,(sx,29.6*S),'中央桟橋・乗船',SMALL,fill='#ffffff')
    for x,y in plan['boats']:
        x*=S;y*=S
        d.ellipse((x-13,y-23,x+13,y+23),fill='#ab814a',outline='#ead0a0',width=2)
        d.line((x-8,y,x+8,y),fill='#604429',width=3)
    label(d,(44*S,31.2*S),'海へ',FONT,fill='white')
    d.rectangle((0,0,W-1,H-1),outline=INK,width=3)
    return im


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for name,role in SOURCES.items():
        path=INCOMING/name
        with Image.open(path) as im: size=list(im.size)
        records.append(dict(path=path.relative_to(ROOT).as_posix(),role=role,size=size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    source_record=dict(date='2026-10-01',author='依頼者',tool='ChatGPTの画像生成（依頼者申告）',permission='これまでの依頼者原画と同じ扱いで使用する指示',files=records,originals_modified=False,
                       scope='指定7枚のみ。ほかの同居ファイルと.keepは不使用。室内6枚は保管・対応記録のみ。')
    (ROOT/'assets/source_records/region2-port-originals.json').write_text(json.dumps(source_record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    TARGET.write_bytes((INCOMING/next(iter(SOURCES))).read_bytes())
    (OUT/'layout-options.json').write_text(json.dumps(dict(status='未採用の配置提案。本番未接続',tiles=[48,32],tile_size=32,plans=PLANS),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    target=Image.open(TARGET).convert('RGB').resize((W,H),Image.Resampling.NEAREST)
    panels=[target]
    for p in PLANS:
        draft=diagram(p);panels.append(draft);draft.save(OUT/f'plan-{p["id"]}.png')
        sheet=Image.new('RGB',(2*W+72,H+212),'#f5f0e2');d=ImageDraw.Draw(sheet)
        d.text((24,12),f'第2地方の港町（仮） / 案{p["id"]}：{p["title"]}',font=TITLE,fill=INK)
        d.text((24,58),'依頼者の目標の絵（全体を表示）',font=FONT,fill=INK)
        d.text((W+48,58),'配置の提案図：48×32マス想定 / 実ゲーム画面ではありません',font=FONT,fill=INK)
        sheet.paste(target,(24,98));sheet.paste(draft,(W+48,98))
        d.text((24,H+118),p['note'],font=FONT,fill=INK)
        d.text((24,H+150),p['tradeoff'],font=FONT,fill=INK)
        d.text((24,H+180),'砂色＝陸地　青＝入り江　薄い石色＝道　木色＝桟橋　明るい丸＝乗船位置。小舟は停泊風景の飾り。',font=SMALL,fill=INK)
        sheet.save(OUT/f'comparison-{p["id"]}.png')
    overview=Image.new('RGB',(2*W+72,2*(H+72)+66),'#f5f0e2');d=ImageDraw.Draw(overview)
    d.text((24,12),'第2地方の港町（仮）：目標の絵と配置3案 / 全案とも未実装',font=TITLE,fill=INK)
    for i,panel in enumerate(panels):
        x=24+(i%2)*(W+24);y=64+(i//2)*(H+72)
        title='依頼者の目標の絵' if i==0 else f'案{PLANS[i-1]["id"]}：{PLANS[i-1]["title"]}'
        d.text((x,y),title,font=FONT,fill=INK);overview.paste(panel,(x,y+42))
    overview.save(OUT/'overview.png')
    print('配置案3枚・原画との比較3枚・全案一覧1枚を保存。原画7枚は読み取りのみ。')


if __name__=='__main__':main()
