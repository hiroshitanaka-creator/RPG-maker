"""007の原画・目標・全歩行コマ・通常操作画像を並べる。画像加工は資料の合成だけ。"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/task-007'
FONT=ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'

def fit(path,size):
    image=Image.open(ROOT/path).convert('RGB')
    scale=min(size[0]/image.width,size[1]/image.height)
    image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.NEAREST)
    result=Image.new('RGB',size,'#1a222b');result.paste(image,((size[0]-image.width)//2,(size[1]-image.height)//2));return result

def main():
    reference='assets/_incoming/owner-2026-10-04-grok-region3/region3-world-map-alt-a.png'
    target='docs/verification/art-review/party-design-sheet.png'
    board=Image.new('RGB',(1920,1336),'#c8c2ad');draw=ImageDraw.Draw(board)
    font=ImageFont.truetype(str(FONT),22)
    for label,path,box in [('依頼者の正面設定原画（未変更）',reference,(0,0,960,646)),('既存の採用済み人物目標',target,(0,690,960,620)),('派生歩行素材：4方向×3コマ×6人',str((OUT/'residents-walk.png').relative_to(ROOT)),(960,0,960,1296))]:
        x,y,w,h=box;draw.text((x+12,y+6),label,font=font,fill='#1c2830');board.paste(fit(path,(w,h)),(x,y+36))
    board.save(OUT/'residents-source-comparison.png')
    groups=[('outside',['02-world-village-entrance','west-landing','west-gate-under','roof-behind','leaves-behind','east-gate-under']),('rooms',[f'room-{index}-entry' for index in range(1,5)]),('rooms',['talk-innkeeper','talk-date_farmer','talk-camel_keeper','talk-elder'])]
    for number,(mode,names) in enumerate(groups):
        picture=Image.new('RGB',(1536,312*((len(names)+2)//3)),'#1a222b');d=ImageDraw.Draw(picture)
        for index,name in enumerate(names):
            x=index%3*512;y=index//3*312;path=f'docs/verification/task-007/latest/{mode}/{name}.png'
            d.text((x+6,y+2),name,font=ImageFont.truetype(str(FONT),14),fill='white');picture.paste(fit(path,(512,288)),(x,y+24))
        picture.save(OUT/f'normal-operation-{number+1}.png')
    comparison=Image.new('RGB',(1536,624),'#1a222b');d=ImageDraw.Draw(comparison)
    panels=[('通常操作：村の西門','docs/verification/task-007/latest/outside/west-landing.png'),('通常操作：宿の受付','docs/verification/task-007/latest/rooms/talk-innkeeper.png'),('通常操作：祠','docs/verification/task-007/latest/rooms/talk-elder.png'),('既存外観目標','docs/reference/visual-targets/region2-port-town.png'),('既存室内目標','docs/reference/visual-targets/first-castle-hall.png'),('原画と歩行素材','docs/verification/task-007/residents-source-comparison.png')]
    for index,(label,path) in enumerate(panels):
        x=index%3*512;y=index//3*312;d.text((x+6,y+2),label,font=ImageFont.truetype(str(FONT),14),fill='white');comparison.paste(fit(path,(512,288)),(x,y+24))
    comparison.save(OUT/'target-comparison.png')
    records=[]
    for mode in ['outside','rooms']:
        report=json.loads((OUT/'latest'/mode/'checks.json').read_text());assert report['status']=='PASS'
        for name in report['images']:
            path=OUT/'latest'/mode/name;records.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (OUT/'images.json').write_text(json.dumps(dict(source_original=reference,source_original_sha256=hashlib.sha256((ROOT/reference).read_bytes()).hexdigest(),walk_list='docs/verification/task-007/residents-walk.png',images=records),ensure_ascii=False,indent=2)+'\n')
    lines=['# 007 確認画像','', '新規人物6人の初回見た目は採用待ち。原画は正面設定画で、横・背面・足運びは別の生成素材で補完した。原画の変更は0バイト。通常操作は港の人工境界保存の通常ロードから開始し、以後はキー・画面ボタン・ホイールだけ。村への瞬間移動・状態注入は使っていない。','', '[全72コマ](residents-walk.png) / [原画と既存人物目標](residents-source-comparison.png) / [通常操作：外観](normal-operation-1.png) / [通常操作：入室](normal-operation-2.png) / [通常操作：会話](normal-operation-3.png) / [既存目標との比較](target-comparison.png)','', '| 通常操作画像 | ファイル |','|---|---|']
    for record in records:
        path=record['path'].removeprefix('docs/verification/task-007/');lines.append(f'| {Path(path).stem} | [{path}]({path}) |')
    lines += ['','固定完成版の受入・最新回帰の実行SHAと全結果は [ci/summary.json](ci/summary.json)。後続による検査の変更では、現在条件をこの資料だけで成功扱いしない。','']
    (OUT/'README.md').write_text('\n'.join(lines))
    print('TASK007_REVIEW_PASS: normal_images='+str(len(records)))

if __name__=='__main__':
    main()
