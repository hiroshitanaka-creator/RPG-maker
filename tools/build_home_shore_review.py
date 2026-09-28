"""家と水際の変更前後を、保存済みの本番画像で比較する。"""
from pathlib import Path
from io import BytesIO
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/sprint5-home-shoreline'
BASE='1579ba51f3fa1f568738b07784e27c0e98cb834b'

def main():
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),22)
    font.set_variation_by_name('Medium')
    for name,oldfile,newfile in [('home','01-village-start.png','01-village-start.png'),('gate-shore','04-closed-gate.png','04-closed-gate.png')]:
        old=Image.open(BytesIO(subprocess.check_output(['git','show',BASE+':docs/verification/first-region/'+oldfile],cwd=ROOT))).convert('RGB')
        new=Image.open(OUT/'runtime'/newfile).convert('RGB')
        canvas=Image.new('RGB',(2048,620),'#d6d2bb');draw=ImageDraw.Draw(canvas)
        for i,(im,title) in enumerate([(old,'変更前'),(new,'今回の実ゲーム画面')]):
            draw.text((i*1024+12,7),title,font=font,fill='#14212b');canvas.paste(im,(i*1024,42))
        canvas.save(OUT/(name+'-before-after.png'))
    canvas=Image.new('RGB',(2048,1240),'#d6d2bb');draw=ImageDraw.Draw(canvas)
    for i in range(4):
        x,y=i%2*1024,i//2*620
        draw.text((x+12,y+7),f'世界の水際 {i+1}（描画の確認。進行の解放ではない）',font=font,fill='#14212b')
        canvas.paste(Image.open(OUT/'runtime'/f'global-coast-{i+1}.png'),(x,y+42))
    canvas.save(OUT/'global-coasts.png')
    for title,reference,actual,name in [('家の木材・漆喰の色と質感','village-farm-a.jpg','home-layout.png','home-target-comparison'),('川岸と水面の色・輪郭','town-river.jpg','runtime/04-closed-gate.png','shore-target-comparison')]:
        canvas=Image.new('RGB',(1536,630),'#d6d2bb');draw=ImageDraw.Draw(canvas)
        for i,path in enumerate([ROOT/'docs/reference/visual-targets'/reference,OUT/actual]):
            im=Image.open(path).convert('RGB');im.thumbnail((752,565),Image.Resampling.NEAREST)
            draw.text((i*768+10,8),('目標：'+title) if i==0 else '今回の配置・描画',font=font,fill='#14212b')
            canvas.paste(im,(i*768+(768-im.width)//2,48))
        canvas.save(OUT/(name+'.png'))
    print('HOME_SHORE_REVIEW_PASS: comparisons=4 global_contact_sheet=1')

if __name__=='__main__':main()
