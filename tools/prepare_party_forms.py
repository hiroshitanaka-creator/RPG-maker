"""新原画からリオネ・ハルド・スイナを切り出す。白い体を明度だけで消さない。"""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/_incoming/owner-2026-09-28/monster-job-images'
RAW=ROOT/'assets/_incoming/party-forms-2026-09-29'
REVIEW=ROOT/'docs/verification/sprint4-party'
FORMS=['slime','beast','undead','plant','shell','spirit','dragon','bird']
NAMES={'slime':'スライム','beast':'獣','undead':'不死','plant':'植物','shell':'甲殻','spirit':'精霊','dragon':'竜','bird':'鳥'}
ACTORS={'pc_02':('リオネ',1101,1106,1),'pc_03':('ハルド',1102,1107,2),'pc_04':('スイナ',1104,1108,3)}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def separate(number):
    image=Image.open(SOURCE/f'IMG_{number}.PNG').convert('RGBA');a=np.array(image);rgb=a[:,:,:3].astype(float)
    h,w=rgb.shape[:2];yy,xx=np.indices((h,w))
    # 外周の背景から緩やかな明るさの変化を推定する。白い体そのものはサンプルにしない。
    sample=(yy<30)|(yy>h-30)
    matrix=np.stack([np.ones(sample.sum()),xx[sample]/w,yy[sample]/h],axis=1)
    coefficients=np.linalg.lstsq(matrix,rgb[sample],rcond=None)[0]
    field=np.stack([np.ones((h,w)),xx/w,yy/h],axis=2)@coefficients
    near=np.max(abs(rgb-field),axis=2)<=13
    near&=(rgb.max(2)-rgb.min(2)<=14)
    if number==1104:
        # スイナの淡い外光が隣の姿をつなぐため、無彩色の外光まで背景候補へ含める。
        near=(np.max(abs(rgb-field),axis=2)<=45)&(rgb.max(2)-rgb.min(2)<=35)
    seeds=np.zeros((h,w),bool);seeds[0,:]=near[0,:];seeds[-1,:]=near[-1,:];seeds[:,0]=near[:,0];seeds[:,-1]=near[:,-1]
    background=ndimage.binary_propagation(seeds,mask=near)
    mask=~background
    labels,count=ndimage.label(mask,structure=np.ones((3,3)))
    sizes=np.bincount(labels.ravel());sizes[0]=0
    primary=sorted(np.argsort(-sizes)[:4],key=lambda k:ndimage.center_of_mass(mask,labels,int(k))[1])
    centers=[np.array(ndimage.center_of_mass(mask,labels,int(k))) for k in primary]
    groups=[[int(k)] for k in primary]
    for k in range(1,count+1):
        if k in primary or sizes[k]<3:continue
        if number==1104:
            fragment=rgb[labels==k]
            if float(fragment.mean())>170 and float((fragment.max(1)-fragment.min(1)).mean())<50:continue
        center=np.array(ndimage.center_of_mass(mask,labels,k))
        index=min(range(4),key=lambda i:np.linalg.norm(center-centers[i]))
        groups[index].append(k)
    result=[]
    for group in groups:
        pixels=a.copy();inside=np.isin(labels,group);pixels[:,:,3]=inside*255;pixels[~inside]=0
        part=Image.fromarray(pixels);box=part.getbbox();assert box
        result.append((part.crop(box),list(box)))
    return result,dict(background_tolerance=45 if number==1104 else 13,background_chroma_limit=35 if number==1104 else 14,method='外周から推定した背景色に近い無彩色のうち、外周に接続する部分だけを除去。体内の白や明部は保持。4体の主成分へ近傍の小部分を割り当てる。')

def main():
    RAW.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    cache={};records=[]
    for actor,(name,first,second,bird) in ACTORS.items():
        panel=Image.new('RGB',(900,8*270),'#e6e3d9');draw=ImageDraw.Draw(panel)
        for row,form in enumerate(FORMS):
            number,slot=(first,row) if row<3 else ((second,row-3) if row<7 else (1109,bird))
            if number not in cache:cache[number]=separate(number)
            parts,method=cache[number];cut,box=parts[slot]
            path=RAW/f'{actor}-{form}-reference.png';cut.save(path)
            original=Image.open(SOURCE/f'IMG_{number}.PNG').convert('RGBA').crop(box)
            scale=min(420/cut.width,225/cut.height)
            draw.text((10,row*270+5),name+' '+NAMES[form]+'：原画 ／ 切り抜き（同倍率）',font=font,fill='#162835')
            for col,im in enumerate([original,cut]):
                im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
                x=col*450+10;y=row*270+38
                for by in range(y,y+226,12):
                    for bx in range(x,x+426,12):draw.rectangle((bx,by,bx+11,by+11),fill='#87939b' if (bx//12+by//12)%2 else '#c8ced0')
                panel.paste(im,(x,y),im)
            source=SOURCE/f'IMG_{number}.PNG'
            records.append(dict(actor=actor,form=form,name=name+' '+NAMES[form],source=str(source.relative_to(ROOT)).replace('\\','/'),slot=slot+1,source_sha256=sha(source),crop=box,reference=str(path.relative_to(ROOT)).replace('\\','/'),reference_sha256=sha(path),**method))
        panel.save(REVIEW/f'{actor}-source-cutouts.png')
    (ROOT/'assets/source_records/party-form-cutouts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PARTY_CUTOUTS: actors=3 forms=24 originals=unchanged')

if __name__=='__main__':main()
