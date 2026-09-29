"""標準ウィンドウの実画面を上段へ一切拡縮せず並べる。"""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/erosion-visible'
LABELS={0:'平常：侵蝕0／戦士',30:'兆候：侵蝕30／戦士',60:'変異：侵蝕60／戦士',90:'不可逆：侵蝕90／既存スライム姿の例'}

def main():
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),26)
    records=[]
    for kind,box in [('battle',(708,78,864,234)),('walk',(478,224,558,336))]:
        panel=Image.new('RGB',(4096,1020),'#d8d4c7');d=ImageDraw.Draw(panel)
        for col,stage in enumerate([0,30,60,90]):
            d.text((col*1024+16,10),LABELS[stage],font=font,fill='#162835')
            path=OUT/'runtime'/f'{kind}-{stage}.png';image=Image.open(path).convert('RGB')
            assert image.size==(1024,576)
            # 上段はresizeを通さず、撮影した全画素をそのまま配置する。
            panel.paste(image,(col*1024,52))
            assert panel.crop((col*1024,52,(col+1)*1024,628)).tobytes()==image.tobytes()
            d.text((col*1024+16,646),'下段のみ拡大。上段は標準ウィンドウの実画面そのまま。',font=font,fill='#162835')
            crop=image.crop(box);crop=crop.resize((312,312) if kind=='battle' else (224,314),Image.Resampling.NEAREST)
            panel.paste(crop,(col*1024+(1024-crop.width)//2,690))
            records.append(dict(kind=kind,stage=stage,source=str(path.relative_to(ROOT)).replace('\\','/'),source_size=list(image.size),upper_pixels_identical=True))
        panel.save(OUT/f'{kind}-stages.png')
    (OUT/'comparison-checks.json').write_text(json.dumps(dict(status='PASS',upper_scaled=False,source_size=[1024,576],internal_resolution=[512,288],comparisons=records),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('EROSION_VISIBLE_COMPARISON_PASS: 8画面の上段が撮影画像と全画素一致')

if __name__=='__main__':main()
