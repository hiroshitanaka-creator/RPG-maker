"""確認用画像：(1) 目標の絵・今までの部品を並べた港町・今回の一枚絵の港町の比較、
(2) 通行地図と上の層を原画に重ねた図、(3) 実際に歩いた画面の一覧。画像の内容は書き換えない（並べるだけ）。
使い方: python tools/build_region2_port_backdrop_review.py
前提: 実ゲームの撮影（capture_region2_port_backdrop.gd）と全体図の保存が済んでいること。
"""
import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/region2-port-backdrop'
ORIGINAL=ROOT/'assets/_incoming/owner-2026-10-01-region2-port/FE4B1B12-C9B1-4DB0-B374-81F51D061BA6.PNG'
OLD_COMMIT='f12f542'
FONT=str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf')

def old_full_town():
    raw=subprocess.check_output(['git','show',f'{OLD_COMMIT}:docs/verification/region2-port/runtime/04-full-town.png'],cwd=ROOT)
    tmp=OUT/'before-parts-full-town.png'
    if not tmp.exists() or tmp.read_bytes()!=raw:tmp.write_bytes(raw)
    return Image.open(tmp).convert('RGB')

def comparison():
    target=Image.open(ORIGINAL).convert('RGB')
    old=old_full_town()
    new=Image.open(OUT/'runtime/00-full-town.png').convert('RGB')
    width=900;panels=[('目標の絵：依頼者の原画（全体）',target),('今まで：部品（タイル）を並べた港町（実ゲームの描画）',old),('今回：原画を1枚の背景にした港町（実ゲームの描画）',new)]
    scaled=[im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS) for _,im in panels]   # 比較表示用の縮小（素材ではない）
    font=ImageFont.truetype(FONT,22);small=ImageFont.truetype(FONT,16)
    height=max(i.height for i in scaled)+110
    canvas=Image.new('RGB',(width*3+80,height),(232,222,200));d=ImageDraw.Draw(canvas)
    d.text((20,12),'第2地方の港町：目標の絵／部品を並べた港町／一枚絵の港町',font=font,fill=(30,30,30))
    for i,((title,_),im) in enumerate(zip(panels,scaled)):
        x=20+i*(width+20);d.text((x,52),title,font=small,fill=(30,30,30));canvas.paste(im,(x,80))
    d.text((20,height-26),'左：原画そのまま。中・右：実際のゲームの描画クラスで町全体を表示した画像（比較のため同じ幅に縮小して並べた）。',font=small,fill=(60,60,60))
    canvas.save(OUT/'comparison-target-before-after.png')

def overlay_on_original():
    """通行地図（緑＝歩ける、赤＝通れない、黄＝扉、青水色＝乗り降り、青＝住人）と上の層（赤紫）を、原画そのものに重ねる。"""
    data=json.loads((ROOT/'world/region2_port.json').read_text(encoding='utf8'))
    ext=data['maps']['brine_port:0'];layout=ext['layout']
    record=json.loads((ROOT/'assets/source_records/region2-port-town-backdrop.json').read_text(encoding='utf8'))
    source=Image.open(ORIGINAL).convert('RGBA');w,h=source.size
    scale=w/(ext['width']*32)   # 原画の画素 / 縮小後の画素
    cell=32*scale
    tint=Image.new('RGBA',source.size,(0,0,0,0));d=ImageDraw.Draw(tint)
    doors={tuple(v) for v in record['doors'].values()};npcs={tuple(e['cell']) for e in ext_events(data)}
    for y,row in enumerate(layout):
        for x,c in enumerate(row):
            box=[x*cell,y*cell,(x+1)*cell-1,(y+1)*cell-1]
            if (x,y)==tuple(record['dock']):d.rectangle(box,fill=(0,230,230,120),outline=(0,230,230,255),width=2)
            elif (x,y) in doors or (x,y)==tuple(record['exit']):d.rectangle(box,fill=(255,220,0,120),outline=(255,220,0,255),width=2)
            elif (x,y) in npcs:d.rectangle(box,fill=(40,120,255,130),outline=(40,120,255,255),width=2)
            elif c=='.':d.rectangle(box,fill=(40,220,80,60),outline=(40,220,80,170),width=1)
            else:d.rectangle(box,fill=(230,40,40,75),outline=(230,40,40,110),width=1)
    atlas=np.array(Image.open(ROOT/ext['overlays']['path']).convert('RGBA'));mask=np.zeros((ext['height']*32,ext['width']*32),bool)
    for ax,ay,pw,ph,x,y,bottom,name in ext['overlays']['pieces']:mask[y:y+ph,x:x+pw]|=atlas[ay:ay+ph,ax:ax+pw,3]>0
    ys,xs=np.mgrid[0:h,0:w];src_x=np.minimum(((xs+0.5)/scale).astype(int),mask.shape[1]-1);src_y=np.minimum(((ys+0.5)/scale).astype(int),mask.shape[0]-1)
    big=mask[src_y,src_x];pink=np.zeros((h,w,4),'uint8');pink[big]=(255,0,255,170)
    out=Image.alpha_composite(Image.alpha_composite(source,tint),Image.fromarray(pink))
    font=ImageFont.truetype(FONT,12);d=ImageDraw.Draw(out)
    for y in range(ext['height']):
        for x in range(ext['width']):d.text((x*cell+2,y*cell+1),f'{x},{y}',font=font,fill=(255,255,255),stroke_width=1,stroke_fill=(0,0,0))
    out.convert('RGB').save(OUT/'collision-and-upper-layer-on-original.png')

def ext_events(data):return data['site']['rooms'][0]['events']

def scenic_sheet():
    shots=json.loads((OUT/'runtime/checks.json').read_text(encoding='utf8'))['scenic']
    names={'01-front-of-palm-trunk':'ヤシの幹の手前（人物は全て見える）','02-behind-palm-crown':'ヤシの葉の下・幹の奥（葉の上の層が人物の上に重なる）','03-behind-stall-awning':'露店の日よけの奥（日よけが人物の足元に重なる）','04-front-of-stall':'露店の手前（人物は全て見える）',
           '05-under-stone-arch':'石のアーチの下（アーチの上の層が頭に重なる）','06-behind-building-roof-home-b':'建物の奥（屋根の縁が足元に重なる）','07-front-of-building-door-home-b':'建物の扉の前（人物は全て見える）','08-pier-before-boarding':'桟橋で船のそばに立つ','09-after-boarding':'決定で乗船した直後'}
    ims=[(Image.open(OUT/'runtime'/s['image']).convert('RGB'),s) for s in shots]
    cols=3;tw,th=512,288;rows=(len(ims)+cols-1)//cols;font=ImageFont.truetype(FONT,15)
    sheet=Image.new('RGB',(cols*(tw+12)+12,rows*(th+52)+12),(232,222,200));d=ImageDraw.Draw(sheet)
    for i,(im,s) in enumerate(ims):
        x=12+i%cols*(tw+12);y=12+i//cols*(th+52)
        sheet.paste(im.resize((tw,th),Image.Resampling.LANCZOS),(x,y+44))
        key=s['image'][:-4];d.text((x,y),names.get(key,key),font=font,fill=(30,30,30))
        d.text((x,y+22),f"マス{tuple(s['cell'])}　人物の見える画素 {s['visible']}/{s['opaque']}（頭 {s['head_visible']}/{s['head_opaque']}）",font=font,fill=(70,70,70))
    sheet.save(OUT/'walking-scenes.png')

ERASE_BOX=(830,430,1140,790)
V0_COMMIT='79a43a5'   # 船を消す前（船が背景に描かれていた版）
V1_COMMIT='eb9fd83'   # 船を消した最初の版（今回の修正前）

def backdrop_at(commit):
    if commit is None:return Image.open(ROOT/'assets/town_backdrops/region2_port.png').convert('RGB')
    raw=subprocess.check_output(['git','show',f'{commit}:assets/town_backdrops/region2_port.png'],cwd=ROOT)
    tmp=OUT/('_tmp_%s.png'%commit);tmp.write_bytes(raw);im=Image.open(tmp).convert('RGB');im.load();tmp.unlink();return im

def erase_sheet():
    """船を消した部分の拡大：消す前・今回の修正前・今回の修正後。縮小後の同じ範囲を3倍の最近傍で並べる。"""
    panels=[('消す前（船が背景に描かれた版）',backdrop_at(V0_COMMIT)),('今回の修正前（船を消した最初の版）',backdrop_at(V1_COMMIT)),('今回の修正後',backdrop_at(None))]
    x0,y0,x1,y1=ERASE_BOX;font=ImageFont.truetype(FONT,20);w=(x1-x0)*3;h=(y1-y0)*3
    sheet=Image.new('RGB',(w*3+80,h+60),(232,222,200));d=ImageDraw.Draw(sheet)
    for i,(title,im) in enumerate(panels):
        x=20+i*(w+20);d.text((x,14),title,font=font,fill=(30,30,30))
        sheet.paste(im.crop(ERASE_BOX).resize((w,h),Image.Resampling.NEAREST),(x,50))
    sheet.save(OUT/'ship-erase-before-after.png')

def ship_coverage():
    """消して埋めた画素のうち、動く船の絵（不透明画素）で隠れる割合。隠れない部分は周りの海と区別がつかないことを目で確かめる。"""
    record=json.loads((ROOT/'assets/source_records/region2-port-town-backdrop.json').read_text(encoding='utf8'))
    emap=np.array(Image.open(OUT/'ship-erase-source-map.png').convert('RGB')).astype(int)
    value=(emap[:,:,0]<<16)|(emap[:,:,1]<<8)|emap[:,:,2];edited=value>0
    x0,y0=record['ship_erase']['bbox'][:2]   # 写し元の地図の左上
    sprite=Image.open(ROOT/'assets/vehicles/owner_ship.png').convert('RGBA').crop((96,0,192,96)).resize((192,192),Image.Resampling.NEAREST)
    alpha=np.array(sprite)[:,:,3]>0
    cx,cy=record['ship_cell'];sx=cx*32+16-96;sy=(cy+1)*32-192
    covered=0;total=int(edited.sum())
    for yy,xx in zip(*np.nonzero(edited)):
        px,py=xx+x0-sx,yy+y0-sy
        if 0<=px<192 and 0<=py<192 and alpha[py,px]:covered+=1
    return dict(edited_pixels=total,hidden_by_ship_sprite=covered,ratio=round(covered/total,3))

def ship_sheet():
    shots=json.loads((OUT/'ship/checks.json').read_text(encoding='utf8'))['scenic']
    names={'01-ship-at-pier-before-sailing':'出航前：船が中央の桟橋に着いている','02-just-after-sailing-out':'出航した直後（世界マップ）','03-pier-without-ship-readonly-copy':'出航後の桟橋に船がない（読み取り専用コピーの描画）','04-returned-ship-at-pier':'帰還の風で港に戻り、桟橋まで歩いた画面：船が戻っている'}
    ims=[(Image.open(OUT/'ship'/s['image']).convert('RGB'),s['image'][:-4]) for s in shots]
    tw,th=640,360;font=ImageFont.truetype(FONT,16)
    sheet=Image.new('RGB',(2*(tw+12)+12,2*(th+34)+12),(232,222,200));d=ImageDraw.Draw(sheet)
    for i,(im,key) in enumerate(ims):
        x=12+i%2*(tw+12);y=12+i//2*(th+34);d.text((x,y),names.get(key,key),font=font,fill=(30,30,30));sheet.paste(im.resize((tw,th),Image.Resampling.LANCZOS),(x,y+26))
    sheet.save(OUT/'ship-scenes.png')

def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    comparison();overlay_on_original();scenic_sheet();erase_sheet();ship_sheet()
    write_json(OUT/'ship-erase-coverage.json',ship_coverage())
    print('REGION2_BACKDROP_REVIEW_BUILT')
if __name__=='__main__':main()
