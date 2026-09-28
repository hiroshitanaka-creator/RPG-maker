"""依頼者の新原画からカイナの8系統を切り出す。原本は書き換えない。"""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/_incoming/owner-2026-09-28/monster-job-images'
OUT=ROOT/'assets/_incoming/kaina-forms-2026-09-29'
REVIEW=ROOT/'docs/verification/sprint4-kaina'
SPECS={
 'slime':(1100,[0,280,260,590],'スライム系'),
 'beast':(1100,[218,175,522,590],'獣系'),
 'undead':(1100,[511,215,811,590],'不死系'),
 'plant':(1105,[0,160,309,590],'植物系'),
 'shell':(1105,[289,275,607,590],'甲殻系'),
 'spirit':(1105,[589,150,830,590],'精霊系'),
 'dragon':(1105,[832,165,1168,590],'竜系'),
 'bird':(1109,[0,155,296,580],'鳥系'),
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True);REVIEW.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    panel=Image.new('RGB',(960,8*260),'#e8e6df');draw=ImageDraw.Draw(panel)
    records=[]
    for row,(form,(number,box,label)) in enumerate(SPECS.items()):
        source=SOURCE/f'IMG_{number}.PNG';original=Image.open(source).convert('RGBA').crop(box)
        a=np.array(original);rgb=a[:,:,:3].astype(np.int16)
        # 灰色の背景候補だけを除く。彩度のある青い体や暗い布を候補にしない。
        gray=(rgb.max(2)-rgb.min(2)<=24)&(rgb.min(2)>=170)
        border=np.zeros(gray.shape,dtype=bool)
        border[0,:]=gray[0,:];border[-1,:]=gray[-1,:]
        border[:,0]=gray[:,0];border[:,-1]=gray[:,-1]
        background=ndimage.binary_propagation(border,mask=gray)
        mask=~background
        labels,count=ndimage.label(mask)
        sizes=np.bincount(labels.ravel());sizes[0]=0
        # 隣の体が手動の切出し枠に少し入る場合、最大の連結した体だけを採る。
        mask=labels==sizes.argmax()
        a[:,:,3]=mask*255;a[~mask]=0
        cutout=Image.fromarray(a);bounds=cutout.getbbox();cutout=cutout.crop(bounds)
        cutout.save(OUT/f'{form}-reference.png')
        draw.text((12,row*260+8),label+'：原画 ／ 切り抜き（原寸比率）',font=font,fill='#17232b')
        for col,im in enumerate([original,cutout]):
            im=im.copy();im.thumbnail((430,214),Image.Resampling.NEAREST)
            x=col*480+(480-im.width)//2;y=row*260+40+(214-im.height)//2
            for yy in range(row*260+38,row*260+258,12):
                for xx in range(col*480+10,col*480+470,12):
                    draw.rectangle((xx,yy,xx+11,yy+11),fill='#b8b9bc' if (xx//12+yy//12)%2 else '#dedfe2')
            panel.paste(im,(x,y),im)
        records.append(dict(form=form,name=label,source=str(source.relative_to(ROOT)).replace('\\','/'),source_sha256=sha(source),crop=box,alpha_bbox=list(bounds),cutout=str((OUT/f'{form}-reference.png').relative_to(ROOT)).replace('\\','/'),cutout_sha256=sha(OUT/f'{form}-reference.png'),method='カイナのみ：RGBの最大最小差24以下・最小値170以上を灰色背景候補とし、枠の外周に接続する候補だけを除く。体内の白い光沢は保持。残った最大連結成分を保持し、手動枠・比較画像で隣の姿と輪郭を確認。ハルドには未適用。'))
    panel.save(REVIEW/'source-cutouts.png')
    (ROOT/'assets/source_records/kaina-form-cutouts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('KAINA_CUTOUTS: 8 原画は無変更')

if __name__=='__main__':main()
