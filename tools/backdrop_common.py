"""一枚絵の背景（城の大広間・謁見の間・灯台の見張り部屋）に共通する縮小・減色・確認画像の処理。

build_port_inn_backdrop.py と同じ規則：最近傍で縮小し、natural.gpl の最も近い色へ置き換える。
拡大・ぼかし・半透明・色調補正はしない。原本は変更しない。
"""
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]

def palette():
    colors=[]
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
        p=line.split()
        if len(p)>=3 and all(v.isdigit() for v in p[:3]):colors.append(tuple(map(int,p[:3])))
    return np.array(colors,float)

def scaled_backdrop(original,sha256,scale,columns,rows,offset):
    """原画全体を scale 倍（最近傍）し、columns×rows マスのキャンバスの offset へ置く。はみ出す外周の暗色だけが切れる。"""
    raw=(ROOT/original).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==sha256,'原本が記録と一致しない: '+original
    source=Image.open(ROOT/original).convert('RGB')
    width=round(source.width*scale);height=round(source.height*scale)
    small=np.array(source.resize((width,height),Image.Resampling.NEAREST),float)
    rgb=palette();index=((small[:,:,None,:]-rgb[None,None])**2).sum(3).argmin(2)
    quantized=rgb[index].astype('uint8')
    border=quantized[0,0]
    canvas=np.zeros((rows*32,columns*32,3),'uint8');canvas[:,:]=border
    ox,oy=offset
    x0,y0=max(ox,0),max(oy,0);x1,y1=min(ox+width,columns*32),min(oy+height,rows*32)
    canvas[y0:y1,x0:x1]=quantized[y0-oy:y1-oy,x0-ox:x1-ox]
    colors=len({tuple(c) for c in canvas.reshape(-1,3)})
    assert colors<=64,colors
    return Image.fromarray(canvas).convert('RGBA'),(width,height),colors

def grid(image,columns,rows,zoom=3):
    """マス目の番号を重ねた確認画像（通行地図を書くための下絵）。"""
    big=image.convert('RGB').resize((columns*32*zoom,rows*32*zoom),Image.Resampling.NEAREST)
    d=ImageDraw.Draw(big,'RGBA');font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),11)
    for y in range(rows):
        for x in range(columns):
            d.rectangle([x*32*zoom,y*32*zoom,(x+1)*32*zoom-1,(y+1)*32*zoom-1],outline=(255,255,0,90))
            d.text((x*32*zoom+2,y*32*zoom+1),f'{x},{y}',font=font,fill=(255,255,0,255))
    return big

def overlay(image,layout,marks,zoom=3):
    """通行地図を重ねた確認画像（緑=歩ける、赤=通れない、黄=扉、青=人物）。marks は {(x,y):'door'|'npc'}。"""
    rows=len(layout);columns=len(layout[0])
    big=image.convert('RGB').resize((columns*32*zoom,rows*32*zoom),Image.Resampling.NEAREST)
    tint=Image.new('RGBA',big.size,(0,0,0,0));d=ImageDraw.Draw(tint);z=32*zoom
    for y,row in enumerate(layout):
        for x,c in enumerate(row):
            box=[x*z,y*z,x*z+z-1,y*z+z-1];mark=marks.get((x,y))
            if mark=='npc':d.rectangle(box,fill=(40,120,255,110),outline=(40,120,255,255),width=2)
            elif mark=='door':d.rectangle(box,fill=(255,220,0,90),outline=(255,220,0,255),width=2)
            elif c=='.':d.rectangle(box,fill=(40,220,80,70),outline=(40,220,80,200),width=1)
            else:d.rectangle(box,fill=(230,40,40,55),outline=(230,40,40,120),width=1)
    out=Image.alpha_composite(big.convert('RGBA'),tint).convert('RGB')
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),11);d=ImageDraw.Draw(out)
    for y in range(rows):
        for x in range(columns):d.text((x*z+2,y*z+1),f'{x},{y}',font=font,fill=(255,255,255))
    return out
