"""本番撮影済み画像を並べる。画面の内容や依頼者原画は変更しない。"""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from import_region2_port_assets import ROOMS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/region2-port'
RUNTIME=OUT/'runtime'
RAW=ROOT/'assets/_incoming/owner-2026-10-01-region2-port'
BG='#e9dfc9';INK='#1b2931'
F=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),21)
F.set_variation_by_name('Medium')
SMALL=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),17)
SMALL.set_variation_by_name('Medium')
NAMES=['宿屋','道具屋','武器屋','防具屋','祠','港務所']

def fit(canvas,path,rect):
    x,y,w,h=rect
    im=Image.open(path).convert('RGB');im.thumbnail((w,h),Image.Resampling.NEAREST)
    canvas.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))

def main():
    report=json.loads((RUNTIME/'checks.json').read_text(encoding='utf8'))
    if report['status']!='PASS':raise ValueError('本番撮影が成功していないため比較画像を作らない')
    canvas=Image.new('RGB',(1568,624),BG);d=ImageDraw.Draw(canvas)
    d.text((16,8),'第2地方の港町（仮）／採用された案A',font=F,fill=INK)
    d.text((16,42),'目標の絵：依頼者原画（全体）',font=F,fill=INK)
    d.text((800,42),'実装後：本番FirstRegionViewによる町全体',font=F,fill=INK)
    fit(canvas,RAW/'FE4B1B12-C9B1-4DB0-B374-81F51D061BA6.PNG',(16,80,768,512))
    fit(canvas,RUNTIME/'04-full-town.png',(800,80,752,512))
    d.text((16,596),'右は通常到達後の状態を本番の描画処理で全体表示した画像。通常のゲーム窓の撮影は別の一覧に収録。',font=SMALL,fill=INK)
    canvas.save(OUT/'exterior-comparison.png')
    overview=Image.new('RGB',(1568,696),BG);o=ImageDraw.Draw(overview)
    o.text((16,8),'6室の実ゲーム画面／通常歩行で入室し、場所名の一時表示が消えてから撮影',font=F,fill=INK)
    comparisons=[]
    for i,(kind,original) in enumerate(ROOMS.items(),1):
        shot=RUNTIME/f'06-room-{i:02d}-{kind}.png'
        row=Image.new('RGB',(1392,460),BG);dr=ImageDraw.Draw(row)
        dr.text((16,8),NAMES[i-1]+'：新設前・依頼者原画・実装後の比較',font=F,fill=INK)
        dr.text((16,48),'新設前（136c4dc）',font=SMALL,fill=INK)
        dr.rectangle((16,88,303,408),fill='#d2c7af',outline='#8b8069',width=2)
        for j,line in enumerate(['新ゲームでは未実装','この6室へ入る経路なし','変更前の実画面は存在しない','旧本編の汎用部屋とは区別']):dr.text((30,158+j*38),line,font=SMALL,fill=INK)
        dr.text((328,48),'依頼者の原画（全体を表示）',font=SMALL,fill=INK)
        fit(row,RAW/original,(328,80,512,342))
        dr.text((864,48),'実装後：通常操作の実ゲーム画面',font=SMALL,fill=INK)
        fit(row,shot,(864,80,512,342))
        dr.text((16,434),'原画は不変。部屋は一枚絵の背景と見えない通行地図。防具屋は会話のみ、祠の石板は飾り。',font=SMALL,fill=INK)
        row.save(OUT/f'room-comparison-{kind}.png');comparisons.append(row)
        x=16+(i-1)%3*520;y=48+(i-1)//3*324
        o.text((x,y),NAMES[i-1],font=F,fill=INK);fit(overview,shot,(x,y+30,512,288))
    overview.save(OUT/'rooms-overview.png')
    combined=Image.new('RGB',(1392,460*6),BG)
    for i,row in enumerate(comparisons):combined.paste(row,(0,i*460))
    combined.save(OUT/'rooms-before-after.png')
    shots=[n for n in report['images'] if n!='04-full-town.png']
    grid=Image.new('RGB',(1568,48+((len(shots)+2)//3)*324),BG);gd=ImageDraw.Draw(grid)
    gd.text((16,8),'通常操作の連続記録：航行・下船・町内・6室・保存再開・再乗船・帰還',font=F,fill=INK)
    for i,name in enumerate(shots):
        x=16+i%3*520;y=48+i//3*324
        gd.text((x,y),name[:-4],font=SMALL,fill=INK);fit(grid,RUNTIME/name,(x,y+26,512,288))
    grid.save(OUT/'runtime-overview.png')
    print('外観比較・6室比較6枚と一覧・通常画面一覧を保存')

if __name__=='__main__':main()
