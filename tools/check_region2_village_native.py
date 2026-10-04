"""実Godotの保存画面を独立した画素合成と照合し、原画・目標との比較を保存する。"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'docs/verification/region2-village-backdrops'

def read(path):return json.loads(path.read_text(encoding='utf-8'))

def sprite_for(capture):
    return Image.open(ROOT/capture['sprite']).convert('RGBA').crop((0,capture['facing']*48,32,(capture['facing']+1)*48))

def assemble(role,capture,record):
    background=Image.open(ROOT/record['background']).convert('RGBA')
    actual=Image.open(ROOT/capture['path']).convert('RGBA')
    cx,cy=[round(v*32) for v in capture['camera']]
    expected=background.crop((cx,cy,cx+512,cy+288))
    hidden=visible=0
    if capture['party_visible']:
        sprite=sprite_for(capture)
        x,y=capture['cell'];px,py=x*32-cx,y*32-cy-16
        expected.alpha_composite(sprite,(px,py))
        mask=np.array(sprite)[:,:,3]>0
        cover=np.zeros((48,32),bool)
        atlas=Image.open(ROOT/record['overlays']['path']).convert('RGBA')
        for ax,ay,w,h,ox,oy,bottom,name in record['overlays']['pieces']:
            if bottom-.5<=y+1:continue
            tile=atlas.crop((ax,ay,ax+w,ay+h))
            expected.alpha_composite(tile,(ox-cx,oy-cy))
            dx,dy=ox-x*32,oy-(y*32-16)
            left,top=max(0,dx),max(0,dy);right,lower=min(32,dx+w),min(48,dy+h)
            if left<right and top<lower:
                cover[top:lower,left:right]|=np.array(tile)[top-dy:lower-dy,left-dx:right-dx,3]>0
        hidden=int((cover&mask).sum());visible=int((~cover&mask).sum())
    difference=np.abs(np.array(actual).astype(int)-np.array(expected).astype(int))
    return dict(path=capture['path'],max_channel_difference=int(difference.max()),pixels_over_one=int(np.any(difference>1,axis=2).sum()),hidden_sprite_pixels=hidden,visible_sprite_pixels=visible,sha256=hashlib.sha256((ROOT/capture['path']).read_bytes()).hexdigest())

def panel(image,size):
    image=image.convert('RGB');scale=min(size[0]/image.width,size[1]/image.height)
    image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.NEAREST)
    result=Image.new('RGB',size,(24,24,30));result.paste(image,((size[0]-image.width)//2,(size[1]-image.height)//2));return result

def comparisons(role,record,captures):
    reference='docs/reference/visual-targets/'+('region2-port-town.png' if role=='exterior' else 'first-castle-hall.png')
    sources=[('原画と派生の比較',Image.open(DIR/role/'source-comparison.png')),('通行判定・扉位置',Image.open(DIR/role/'collision-overlay.png')),('実表示・人物尺度',Image.open(ROOT/next(c['path'] for c in captures if c['path'].endswith('/native-detail.png')))),('目標（構図・色調の比較）',Image.open(ROOT/reference)),('実表示・上層の遮蔽',Image.open(ROOT/next(c['path'] for c in captures if c['path'].endswith('/native-behind.png')))),('上層の元画素',Image.open(DIR/role/'upper-mask.png'))]
    sheet=Image.new('RGB',(1536,624),(24,24,30));draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),14)
    for i,(label,picture) in enumerate(sources):
        x,y=(i%3)*512,(i//3)*312;sheet.paste(panel(picture,(512,288)),(x,y+24));draw.text((x+8,y+2),label,font=font,fill='white')
    path=DIR/role/'review-comparison.png';sheet.save(path)
    return dict(path=str(path.relative_to(ROOT)).replace('\\','/'),reference=reference,reference_sha256=hashlib.sha256((ROOT/reference).read_bytes()).hexdigest(),original_sha256=record['sha256'])

def main():
    native=read(DIR/'native-checks.json');records=read(ROOT/'assets/source_records/region2-village-backdrops.json')['maps']
    failures=[];results=[];sheets=[]
    if native['status']!='PASS' or not native['native_render'] or native['failures']:failures.append('ネイティブGodot検査が成功していない')
    for role,record in records.items():
        captures=[c for c in native['captures'] if ('/'+role+'/') in c['path']]
        if len(captures)!=5:failures.append('実表示5枚不足: '+role)
        for capture in captures:
            result=assemble(role,capture,record);results.append(result)
            if result['pixels_over_one']:failures.append('独立画素合成との不一致: '+capture['path'])
            if capture['path'].endswith('/native-detail.png') and result['hidden_sprite_pixels']!=0:failures.append('手前の人物が上層に隠れる: '+role)
            if capture['path'].endswith('/native-behind.png') and min(result['hidden_sprite_pixels'],result['visible_sprite_pixels'])<8:failures.append('実際の人物遮蔽または可視画素が不足: '+role)
        sheets.append(comparisons(role,record,captures))
    report=dict(status='FAIL' if failures else 'PASS',captures=results,comparisons=sheets,failures=failures,tolerance='GPUの8bit丸め差は1まで。最近傍縮小・減色の検査には許容差を使わない。',scope='ネイティブ実描画の独立合成と原画・既存目標の比較。見た目の採用判断は別。')
    (DIR/'native-pixel-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for failure in failures:print('VILLAGE_NATIVE_FAIL: '+failure)
    print(('VILLAGE_NATIVE_FAIL' if failures else 'VILLAGE_NATIVE_PASS')+': captures='+str(len(results)))
    return int(bool(failures))

if __name__=='__main__':raise SystemExit(main())
