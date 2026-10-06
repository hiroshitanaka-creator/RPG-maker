"""011の原画実測と素材見本。確認図だけに線・文字を重ね、原本は保存しない。"""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/task-011'
FONT=ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'
def label(draw,xy,text,size=18):draw.text(xy,text,font=ImageFont.truetype(str(FONT),size),fill='white')
def measurements():
 items=[(1,'横幅',706,260,831,260),(2,'横幅',269,465,336,465),(2,'縦幅',500,778,500,812),(3,'横幅',238,300,273,300),(3,'縦幅',430,211,430,237),(3,'縦幅',770,470,770,533),(4,'横幅',176,300,233,300),(4,'縦幅',440,735,440,764)]
 records=json.loads((ROOT/'assets/source_records/task011-ruins.json').read_text())['maps']
 canvas=Image.new('RGB',(1000,1000),(18,28,42));d=ImageDraw.Draw(canvas);label(d,(12,6),'確認用図 / 原画の実測（画素座標、縮小前）');rows=[]
 for k,(n,kind,x0,y0,x1,y1) in enumerate(items):
  record=records[str(n-1)];source=Image.open(ROOT/record['original']).convert('RGB')
  left=min(x0,x1)-45;top=min(y0,y1)-45;right=max(x0,x1)+46;bottom=max(y0,y1)+46
  crop=source.crop((left,top,right,bottom)).resize(((right-left)*2,(bottom-top)*2),Image.Resampling.NEAREST)
  col,row=k%2,k//2;px,py=col*500+12,row*240+65;canvas.paste(crop,(px,py))
  line=(px+(x0-left)*2,py+(y0-top)*2,px+(x1-left)*2,py+(y1-top)*2);d.line(line,fill=(255,40,40),width=3)
  for x,y in [line[:2],line[2:]]:d.ellipse((x-4,y-4,x+4,y+4),fill=(255,240,0))
  width=abs(x1-x0)+abs(y1-y0);ratio=record['scale'];converted=width*ratio[0]/ratio[1]
  label(d,(col*500+12,row*240+36),f'{n}階 {kind} ({x0},{y0})→({x1},{y1}) = {width}px',16)
  label(d,(col*500+12,row*240+218),f'{ratio[0]}/{ratio[1]} → {converted:g}px',16)
  rows.append(dict(floor=n,axis=kind,from_pixel=[x0,y0],to_pixel=[x1,y1],source_width=width,derived_width=converted))
 canvas.save(OUT/'measurements.png');(OUT/'measurements.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
def enemy_contact():
 records=json.loads((ROOT/'assets/source_records/task011-enemies.json').read_text())['enemies']
 canvas=Image.new('RGB',(1440,780),(18,28,42));d=ImageDraw.Draw(canvas);label(d,(12,8),'確認用図 / 敵6体・ボスの派生素材（通常遭遇・ボス戦は未有効化）')
 for k,e in enumerate(records):
  x,y=k%4*360,k//4*370+42;im=Image.open(ROOT/e['path']).convert('RGBA');factor=2 if e['monster_tier']=='boss' else 3;large=im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST)
  canvas.paste(large,(x+(360-large.width)//2,y),large)
  label(d,(x+8,y+310),e['name'],17);label(d,(x+8,y+337),f"{e['size'][0]}×{e['size'][1]} / {e['size_class']} / 接地位置固定",14)
 canvas.save(OUT/'enemy-assets.png')
def target_comparison():
 target=Image.open(ROOT/'docs/reference/visual-targets/ruins-temple.jpg').convert('RGB');target.thumbnail((720,430),Image.Resampling.NEAREST)
 canvas=Image.new('RGB',(1440,760),(18,28,42));d=ImageDraw.Draw(canvas);label(d,(12,8),'確認用図 / 採用済み見た目資料と実描画の比較');label(d,(12,40),'資料：ruins-temple.jpg（参考）');canvas.paste(target,(12,75))
 # 実画面は左右に1階・最下層。残る2階は画像一覧で同じ大きさで確認できる。
 for i,x in [(0,12),(3,740)]:
  path=OUT/f'latest/images/floor{i+1}-walking.png'
  if path.exists():
   im=Image.open(path).convert('RGB').resize((512,288),Image.Resampling.NEAREST);label(d,(x,430),f'実描画：{i+1}階（確認用状態）');canvas.paste(im,(x,465))
 label(d,(740,75),'原画の暖色・石材を保持。参考資料は緑の苔・冷色が強い。',17)
 label(d,(740,110),'人物の比率、陰影、柱の前後、背景の密度を一括確認。',17)
 canvas.save(OUT/'visual-target-comparison.png')
if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True);measurements();enemy_contact();target_comparison()
