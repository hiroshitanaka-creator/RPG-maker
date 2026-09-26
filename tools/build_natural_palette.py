#!/usr/bin/env python3
"""参考画像から色だけを採り、自然色パレットと色比較を作る。絵は切り出さない。"""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from validate_assets import load_palette

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'docs/reference/visual-targets'
OUT=ROOT/'docs/verification/art-review-2'


def clusters(values,count):
    im=Image.fromarray(np.asarray(values,dtype=np.uint8).reshape(1,-1,3))
    q=im.quantize(colors=count,method=Image.Quantize.MEDIANCUT)
    palette=q.getpalette()
    rows=sorted(q.getcolors(),reverse=True)
    return [tuple(palette[i*3:i*3+3]) for _,i in rows]


def hsv(rgb):
    a=rgb.astype(float)/255;hi=a.max(axis=1);lo=a.min(axis=1);delta=hi-lo
    h=np.zeros(len(a));valid=delta>0
    for k in range(3):
        mask=valid&(a.argmax(axis=1)==k)
        h[mask]=((a[mask,(k+1)%3]-a[mask,(k+2)%3])/delta[mask]+2*k)%6
    return h/6,np.divide(delta,hi,out=np.zeros_like(delta),where=hi>0),hi


def tonal_clusters(values,bounds,counts):
    """暗部の面積だけで枠を使い切らず、少量の明部と火の色も残す。"""
    light=values.max(axis=1)/255
    chosen=[]
    for low,high,count in zip(bounds,bounds[1:],counts):
        subset=values[(light>=low)&(light<high)]
        if len(subset)>=count:
            chosen.extend(c for c in clusters(subset,count) if c not in chosen)
    target=sum(counts)
    for c in clusters(values,min(64,len(np.unique(values,axis=0)))):
        if c not in chosen:chosen.append(c)
        if len(chosen)>=target:break
    return chosen[:target]


def lab(rgb):
    a=rgb.astype(float)/255;a=np.where(a>.04045,((a+.055)/1.055)**2.4,a/12.92)
    xyz=a@np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]]).T
    xyz/=np.array([.95047,1,1.08883]);f=np.where(xyz>.008856,xyz**(1/3),7.787*xyz+16/116)
    return np.stack([116*f[:,1]-16,500*(f[:,0]-f[:,1]),200*(f[:,1]-f[:,2])],axis=1)


def assignment(cost):
    """色の統合を防ぐ一対一の最小費用割当。色数とコマの差分を保持する。"""
    n,m=cost.shape;u=np.zeros(n+1);v=np.zeros(m+1);p=np.zeros(m+1,dtype=int);way=np.zeros(m+1,dtype=int)
    for i in range(1,n+1):
        p[0]=i;j0=0;minimum=np.full(m+1,np.inf);used=np.zeros(m+1,dtype=bool)
        while True:
            used[j0]=True;i0=p[j0];delta=np.inf;j1=0
            for j in range(1,m+1):
                if not used[j]:
                    cur=cost[i0-1,j-1]-u[i0]-v[j]
                    if cur<minimum[j]:minimum[j]=cur;way[j]=j0
                    if minimum[j]<delta:delta=minimum[j];j1=j
            for j in range(m+1):
                if used[j]:u[p[j]]+=delta;v[j]-=delta
                else:minimum[j]-=delta
            j0=j1
            if p[j0]==0:break
        while j0:
            j1=way[j0];p[j0]=p[j1];j0=j1
    result=np.empty(n,dtype=int)
    for j in range(1,m+1):
        if p[j]:result[p[j]-1]=j-1
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    samples={p.name:np.asarray(Image.open(p).convert('RGB').resize((160,108),Image.Resampling.NEAREST)).reshape(-1,3) for p in sorted(REF.glob('*.jpg'))}
    pool=np.concatenate(list(samples.values()));h,s,v=hsv(pool)
    masks=[('green',15,(h>=.16)&(h<.47)&(s>=.25)&(v>.06)),
           ('blue',8,(h>=.47)&(h<.72)&(s>=.25)&(v>.06)),
           ('red',8,((h<.075)|(h>=.92))&(s>=.25)&(v>.06)),
           ('purple',4,(h>=.72)&(h<.92)&(s>=.25)&(v>.06)),
           ('neutral',15,(s<.25)|(v<=.06)),
           ('earth',14,(h>=.075)&(h<.16)&(s>=.25)&(v>.06))]
    colors=[];groups=[]
    bands={
        'green':([0,.22,.4,.6,.78,1.01],[2,3,4,4,2]),
        'blue':([0,.25,.45,.65,1.01],[2,2,2,2]),
        'red':([0,.3,.5,.7,1.01],[2,2,2,2]),
        'purple':([0,.3,.5,.75,1.01],[1,1,1,1]),
        'neutral':([0,.1,.3,.6,.83,1.01],[2,2,3,3,2]),
        'earth':([0,.25,.4,.6,.78,.9,1.01],[1,2,3,3,3,2]),
    }
    for name,count,mask in masks:
        values=pool[mask];assert len(values)>count,(name,len(values))
        chosen=tonal_clusters(values,*bands[name])
        if name=='neutral':
            # 銀髪・白布の識別色を石の暖色だけに寄せない。実際の参考画素から採る。
            for target in [(120,136,145),(185,198,205),(244,245,239)]:
                available=values
                order=np.argsort(((available.astype(float)-np.array(target))**2).sum(axis=1))
                color=next(tuple(map(int,available[i])) for i in order if tuple(available[i]) not in chosen)
                chosen.append(color)
        assert len(chosen)==count and len(set(chosen))==count,(name,chosen)
        colors+=chosen;groups.append({'group':name,'count':count})
    assert len(colors)==len(set(colors))==64
    natural=np.array(colors,dtype=np.int32)
    palette_text='GIMP Palette\nName: RPG-maker natural\nColumns: 8\n# Owner reference color sampling; 2026-09-26; no image content copied\n'+''.join('%3d %3d %3d\t#%02X%02X%02X\n'%(*c,*c) for c in colors)
    (ROOT/'assets/palette/natural.gpl').write_text(palette_text,encoding='utf-8',newline='\n')
    bright=np.array(sorted(load_palette(ROOT/'assets/palette/bright.gpl')),dtype=np.int32)
    cost=((lab(bright)[:,None,:]-lab(natural)[None,:,:])**2).sum(axis=2)
    bh,bs,bv=hsv(bright);nh,ns,nv=hsv(natural);diff=np.abs(bh[:,None]-nh[None,:]);diff=np.minimum(diff,1-diff)
    cost+=((diff>.15)&(bs[:,None]>.3)&(ns[None,:]>.3))*10000
    indices=cost.argmin(axis=1);lut=[{'from':list(map(int,a)),'to':list(map(int,natural[j]))} for a,j in zip(bright,indices)]
    (OUT/'palette-mapping.json').write_text(json.dumps(lut,indent=2)+'\n',encoding='utf-8',newline='\n')
    font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',13)
    chart=Image.new('RGB',(1400,700),'#eee9dc');d=ImageDraw.Draw(chart)
    for side,(title,pal) in enumerate([('bright.gpl',bright),('natural.gpl',natural)]):
        d.text((side*700+16,12),title,font=font,fill='#20251d')
        for i,c in enumerate(pal):
            x=side*700+16+i%8*84;y=48+i//8*80;d.rectangle((x,y,x+74,y+45),fill=tuple(map(int,c)));d.text((x,y+48),'#%02X%02X%02X'%tuple(c),font=font,fill='#20251d')
    chart.save(OUT/'palette-natural-compare.png')
    report=[];swatches=Image.new('RGB',(820,10*88),'#eee9dc');d=ImageDraw.Draw(swatches)
    for i,(name,values) in enumerate(samples.items()):
        dominant=clusters(values,8)
        def error(pal):return float(np.sqrt(((values.astype(float)[:,None,:]-pal[None,:,:])**2).sum(axis=2).min(axis=1)).mean())
        row={'target':name,'dominant_colors':['#%02X%02X%02X'%c for c in dominant],'bright_error':round(error(bright),3),'natural_error':round(error(natural),3)};report.append(row)
        d.text((8,i*88+4),name,font=font,fill='#20251d')
        for j,c in enumerate(dominant):
            x=8+j*100;d.rectangle((x,i*88+27,x+92,i*88+56),fill=c);d.text((x,i*88+59),'#%02X%02X%02X'%c,font=font,fill='#20251d')
    swatches.save(OUT/'target-color-samples.png')
    (OUT/'palette-analysis.json').write_text(json.dumps({'method':'各画像160×108最近傍サンプル。材質の色相群と明度帯へ枠を割り当てて中央値分割。誤差は最近色までのRGB距離の平均。palette-mapping.jsonは一般素材の色相を保った最近色対応。仲間の共通16色は別途一対一で選ぶ。','groups':groups,'targets':report},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    for r in report:print(r['target'],r['bright_error'],'->',r['natural_error'])
    print('NATURAL_PALETTE_PASS: colors=64 sampled_targets=10')


if __name__=='__main__':main()
