"""依頼者のIMG_0974を、原本を変えず4方向の船へ切り出す。"""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def main():
    source=ROOT/'assets/_incoming/owner-2026-09-26/supplement-2026-09-27/3-写真3.jpg'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='566cb733bb8ec639a680468fbd8fb2a01ea4e0297d7b71df372543287fb86a44'
    raw=Image.open(source).convert('RGB');colors=[]
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
        p=line.split()
        if len(p)>=3 and all(v.isdigit() for v in p[:3]):colors.append(tuple(map(int,p[:3])))
    colors=colors[:64];pal=Image.new('P',(1,1));pal.putpalette(sum((list(c) for c in colors),[])+[0]*(768-3*len(colors)))
    sheet=Image.new('RGBA',(384,96));records=[]
    # 左から前・左・右・後ろ。左右反転では作らない。
    for i,box in enumerate([(55,210,235,520),(270,230,570,490),(600,230,900,490),(960,210,1130,520)]):
        image=raw.crop(box).convert('RGBA');a=np.array(image)
        a[:,:,3]=np.where(a[:,:,:3].max(axis=2)>20,255,0).astype('uint8');image=Image.fromarray(a)
        bounds=image.getbbox();image=image.crop(bounds);scale=min(88/image.width,88/image.height)
        size=(max(1,round(image.width*scale)),max(1,round(image.height*scale)))
        image=image.resize(size,Image.Resampling.NEAREST);alpha=image.getchannel('A')
        image=image.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE).convert('RGBA');image.putalpha(alpha)
        offset=((96-image.width)//2,96-image.height);sheet.alpha_composite(image,(i*96+offset[0],offset[1]))
        records.append(dict(direction=['down','left','right','up'][i],crop=list(box),opaque_bounds=list(bounds),size=list(size),offset=list(offset)))
    path='assets/vehicles/owner_ship.png';(ROOT/path).parent.mkdir(parents=True,exist_ok=True);sheet.save(ROOT/path)
    record=dict(source=str(source.relative_to(ROOT)).replace('\\','/'),logical_id='IMG_0974',sha256=hashlib.sha256(source.read_bytes()).hexdigest(),tool='Python/Pillow。黒背景の透過、最近傍縮小、既存自然色64色への減色。原本不変。',frames=records,output=path)
    (ROOT/'assets/source_records/owner-ship.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    reg=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    entry=dict(path=path,kind='object',size=[384,96],frame=[96,96],grid=[4,1],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='external',tool='Grok / Python/Pillow',author='依頼者',license='LicenseRef-Owner-Provided',generated_at='2026-09-29',prompt_record='assets/source_records/owner-ship.json',conversion_record='assets/source_records/owner-ship.json',modified='IMG_0974の4方向を原画どおりに切り出した船。飛行船は未使用。')
    entry.update(source='owner',provided_at='2026-09-27',original_file=str(source.relative_to(ROOT)).replace('\\','/'))
    reg['assets']=[e for e in reg['assets'] if e['path']!=path]+[entry];(ROOT/'assets/registry.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    out=ROOT/'docs/verification/sprint5-travel';out.mkdir(parents=True,exist_ok=True)
    preview=Image.new('RGB',(1152,530),'#244153');draw=ImageDraw.Draw(preview);font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    src=raw.copy();src.thumbnail((1152,270));preview.paste(src,((1152-src.width)//2,30));preview.paste(sheet.resize((768,192),Image.Resampling.NEAREST),(192,320),sheet.resize((768,192),Image.Resampling.NEAREST));draw.text((12,4),'依頼者原本 IMG_0974 / 下：ゲーム用4方向',font=font,fill='white');preview.save(out/'ship-source-comparison.png')
    print('OWNER_SHIP_IMPORTED: directions=4 frame=96x96 original_unchanged=True')
if __name__=='__main__':main()
