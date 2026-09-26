#!/usr/bin/env python3
"""保管済み人物原画を演出用の静止ポーズへ変換する。ゲーム処理へは接続しない。"""
from pathlib import Path
import hashlib, json, math
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from import_owner_monsters import ROOT, SHEETS, PAL, split_parts, remove_background

BASE='f288ed442731c4b1ae33649219647bca0a1a26e6'
RECORD='assets/source_records/owner-characters.json'
OUT=ROOT/'docs/verification/sprint-1'
ORIGINAL='assets/_incoming/owner-2026-09-26/'
# 矢とその発光を射手のコマへ含める。元絵を見て確認した空白の分割線。
ACTION_CUTS={962:([0,250,510,850,1019],[0,241,481,722]),963:([0,248,496,744,992],[0,244,488,732]),964:([0,241,482,810,964],[0,216,433,649]),965:([0,246,492,738,984],[0,236,471,707]),966:([0,259,518,850,1036],[0,230,459,689]),967:([0,236,471,706,942],[0,260,484,726]),968:([0,253,506,850,1013],[0,220,478,708])}
YOUNG={962:1,963:1,964:2,965:2,966:3,967:3,968:4}
ROLES={
 'h_sun_guard':'太陽の神・明るい姿', 'h_moon_robed':'月の神・明るい姿', 'h_sea_god':'海の神・明るい姿', 'h_red_guard':'戦いの神・明るい姿', 'h_harvest':'実りの神・明るい姿',
 'h_dark_sun':'太陽の神・黒く染まった姿', 'h_dark_moon':'月の神・黒く染まった姿', 'h_war_god':'戦いの神・黒く染まった姿', 'h_wood_god':'実りの神・黒く染まった姿', 'h_depth_god':'海の神・黒く染まった姿',
 'h_reaper':'死者の国の役候補', 'h_smith':'武器屋・特別な武器を作る人の候補', 'h_white_spirit':'各地の守り手の候補', 'h_tree_spirit':'各地の守り手の候補', 'h_masked_spirit':'案内役の候補',
}
PAIRS=[('太陽','h_sun_guard','h_dark_sun'),('月','h_moon_robed','h_dark_moon'),('海','h_sea_god','h_depth_god'),('戦い','h_red_guard','h_war_god'),('実り','h_harvest','h_wood_god')]

def sha(data): return hashlib.sha256(data).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def source_rows():
    """各原画の切り出しと、その原画座標を返す。原本は読み取りのみ。"""
    held=json.loads((ROOT/'assets/source_records/owner-monsters.json').read_text(encoding='utf8'))['held_back']
    cache={};rows=[]
    for item in held:
        if item['slot']=='all':continue
        original=item['original_file'];number=int(Path(original).stem[4:])
        if original not in cache:cache[original]=split_parts(Image.open(ROOT/original),len(SHEETS[number].split(';')))
        part,box=cache[original][item['slot']-1]
        rows.append(dict(id=item['source_id'],name=item['name'],original_file=original,slot=item['slot'],crop=list(box),part=part.crop(box),pose='standing',role=ROLES.get(item['source_id'],'役・配置とも未決')))
    original=ORIGINAL+'IMG_0961.PNG'
    for index,(part,box) in enumerate(split_parts(Image.open(ROOT/original),4),1):
        rows.append(dict(id=f'owner_young_{index:02}',name=f'もう一組の冒険者{index}（仮）',original_file=original,slot=index,crop=list(box),part=part.crop(box),pose='standing',role='別の冒険者の一行。ライバルかゲストか、名前・性格・登場場面は未決'))
    for number,(xs,ys) in ACTION_CUTS.items():
        original=ORIGINAL+f'IMG_{number:04}.PNG';im=remove_background(Image.open(ROOT/original))
        assert im.size==(xs[-1],ys[-1])
        a=np.array(im.getchannel('A'))
        for x in xs[1:-1]: assert not a[:,x].any(),f'{number}: 列境界が絵を横切っている'
        for y in ys[1:-1]: assert not a[y,:].any(),f'{number}: 行境界が絵を横切っている'
        actions=['bow','sword','dagger'] if number%2==0 else ['magic','hurt','victory']
        for row,action in enumerate(actions):
            for col in range(4):
                box=[xs[col],ys[row],xs[col+1],ys[row+1]]
                part=im.crop(box);assert part.getchannel('A').getbbox()
                index=YOUNG[number]
                rows.append(dict(id=f'owner_young_{index:02}',name=f'もう一組の冒険者{index}（仮）',original_file=original,slot=row*4+col+1,crop=box,part=part,pose=f'{action}_{col+1:02}',role='会話・事件の場面の演出用ポーズ。戦闘や歩行の操作には未接続'))
    return rows

def fit(part):
    bounds=part.getchannel('A').getbbox();assert bounds
    part=part.crop(bounds);scale=min(30/part.width,46/part.height)
    part=part.resize((max(1,round(part.width*scale)),max(1,round(part.height*scale))),Image.Resampling.NEAREST)
    # ここでは演出用の静止ポーズとして、武器・発光を含む全形を1コマへ収める。
    return part

def palettes(rows):
    groups=defaultdict(list)
    for row in rows:
        im=np.array(fit(row['part']));groups[row['id']].append(im[:,:,:3][im[:,:,3]>0])
    result={}
    for id_,parts in groups.items():
        colors,counts=np.unique(np.concatenate(parts),axis=0,return_counts=True)
        nearest=((colors.astype(np.int32)[:,None,:]-PAL[None,:,:])**2).sum(axis=2).argmin(axis=1)
        weights=np.bincount(nearest,weights=counts,minlength=len(PAL))
        # 使用頻度だけで選ぶと、少数のコマにある魔法の緑や衣装の識別色が落ちる。
        # 頻度の高い色を起点に、距離と頻度の平方根で異なる色相も残す。
        selected=[int(weights.argmax())]
        for _ in range(min(16,int(np.count_nonzero(weights)))-1):
            distance=((PAL[:,None,:]-PAL[selected][None,:,:])**2).sum(axis=2).min(axis=1)
            selected.append(int((distance*np.sqrt(weights)).argmax()))
        result[id_]=PAL[selected]
    return result

def render(part,palette):
    a=np.array(fit(part));opaque=a[:,:,3]>0
    colors,inv=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
    nearest=((colors.astype(np.int32)[:,None,:]-palette[None,:,:])**2).sum(axis=2).argmin(axis=1)
    a[:,:,:3]=palette[nearest[inv]].reshape(a.shape[:2]+(3,));a[:,:,3]=opaque*255;a[~opaque]=0
    body=Image.fromarray(a);out=Image.new('RGBA',(32,48))
    out.alpha_composite(body,((32-body.width)//2,46-body.height))
    return out

def main():
    rows=source_rows();bank=palettes(rows);results=[]
    registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf8'));entries={e['path']:e for e in registry['assets']}
    for r in rows:
        path=f"assets/characters/{r['id']}/event_{r['pose']}.png";dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True)
        im=render(r['part'],bank[r['id']]);im.save(dest)
        row={k:v for k,v in r.items() if k!='part'}
        row.update(path=path,original_sha256=sha((ROOT/r['original_file']).read_bytes()),output_sha256=sha(dest.read_bytes()),size=[32,48],max_colors=16,black_threshold=24,resampling='nearest',mirror=False,palette_colors=bank[r['id']].tolist())
        results.append(row)
        entries[path]=dict(path=path,kind='character_event',size=[32,48],frame=[32,48],grid=[1,1],max_colors=16,status='optional',palette='assets/palette/natural.gpl',source='owner',license='LicenseRef-Owner-Provided',author='依頼者',provided_at='2026-09-26',original_file=r['original_file'],conversion_record=RECORD+'#'+r['id']+'/'+r['pose'],modified='原本は不変。黒背景の除去、記録した範囲で分割、最近傍縮小、人物ごとに共通16色、二値透過。静止ポーズとして全形を32×48へ収める。反転なし。',role=r['role'],usage='event_pose_unplaced')
    registry['assets']=list(entries.values());write_json(registry_path,registry)
    write_json(ROOT/RECORD,dict(baseline=BASE,shared_conversation='https://grok.com/share/c2hhcmQtMg_2d6106a4-1817-4b58-ba1c-28eb1121196f',imported=results,god_pairs=PAIRS,missing_sources=['owner_young_04: magic/hurt/victoryの原画は未提供。生成しない。'],guardian_references=['assets/monsters/gold_guard_lion/idle.png','assets/monsters/silver_guard_lion/idle.png']))
    OUT.mkdir(parents=True,exist_ok=True);font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',13)
    standing=[r for r in rows if r['pose']=='standing']
    for page in range(math.ceil(len(standing)/12)):
        items=standing[page*12:(page+1)*12];sheet=Image.new('RGB',(1080,math.ceil(len(items)/3)*255),'#d9d5c7');d=ImageDraw.Draw(sheet)
        for i,r in enumerate(items):
            x=i%3*360;y=i//3*255;source=r['part'].copy();source.thumbnail((145,185),Image.Resampling.NEAREST)
            sheet.paste(source,(x+12,y+40),source)
            actual=render(r['part'],bank[r['id']]);sheet.paste(actual,(x+185,y+185-48),actual)
            zoom=actual.resize((96,144),Image.Resampling.NEAREST);sheet.paste(zoom,(x+245,y+48),zoom)
            d.text((x+7,y+5),r['id'],font=font,fill='black');d.text((x+7,y+22),r['name'],font=font,fill='black');d.text((x+7,y+231),'原画 / 実寸32×48 / 3倍（最近傍）',font=font,fill='black')
        sheet.save(OUT/f'characters-{page+1:02}.png')
    for young in range(1,5):
        items=[r for r in rows if r['id']==f'owner_young_{young:02}'];sheet=Image.new('RGB',(1000,math.ceil(len(items)/5)*192),'#d9d5c7');d=ImageDraw.Draw(sheet)
        for i,r in enumerate(items):
            x=i%5*200;y=i//5*192;im=render(r['part'],bank[r['id']]).resize((96,144),Image.Resampling.NEAREST)
            sheet.paste(im,(x+52,y+20),im);d.text((x+10,y+169),r['pose'],font=font,fill='black')
        sheet.save(OUT/f'young-{young:02}-poses.png')
    # 承認済みの人物と目標の村の上で色・縮尺を並べる。画面実装ではない。
    target=Image.open(ROOT/'docs/reference/visual-targets/village-farm-a.jpg').convert('RGB');target.thumbnail((1168,784),Image.Resampling.NEAREST)
    d=ImageDraw.Draw(target);d.rectangle((0,570,1168,784),fill='#d9d5c7')
    for i in range(4):
        old=Image.open(ROOT/f'assets/characters/pc_{i+1:02}/walk.png').convert('RGBA').crop((0,0,32,48))
        r=next(r for r in standing if r['id']==f'owner_young_{i+1:02}')
        new=render(r['part'],bank[r['id']])
        target.paste(old.resize((64,96),Image.Resampling.NEAREST),(30+i*145,625),old.resize((64,96),Image.Resampling.NEAREST))
        target.paste(new.resize((64,96),Image.Resampling.NEAREST),(620+i*135,625),new.resize((64,96),Image.Resampling.NEAREST))
    d.text((12,585),'目標の村との比較：左は既存の仲間4人、右は別の冒険者4人（各2倍）',font=font,fill='black')
    target.save(OUT/'target-character-compare.png')
    doc=['# スプリント1：人物原画の取り込み','','2026年9月27日。原本は保管済みの36枚を変更せず使った。会話・事件用の静止ポーズ34体と、若い4人の動作ポーズ84コマを登録した。仲間 pc_01〜pc_04 の置換・職業変更・戦闘処理への接続は行っていない。','','人物は32×48 px、自然色16色以内、二値透過。若い4人は立ち姿と動作を人物ごとの共通16色へそろえた。個々のポーズは武器・光を含む全形を収めるため、見かけの体格が異なる。連続再生する歩行・戦闘アニメーションとしては登録していない。','','名前・性格・配置・ライバルかゲストかは未決。以下の役は採用済みの物語の大筋に対応する範囲だけを記録した。神の明暗対は原画の並び順が異なるため、原本スロットを個別に対応させた。','','| 人物id | 原画・位置 | 役または候補 |','| --- | --- | --- |']
    for r in standing:doc.append(f"| {r['id']} | {Path(r['original_file']).name} 左から{r['slot']} | {r['role']} |")
    doc+=['','## 神の姿の対応','','| 柱 | 明るい姿 | 黒く染まった姿 |','| --- | --- | --- |']+[f'| {name} | {light} | {dark} |' for name,light,dark in PAIRS]
    doc+=['','## 確認画像と記録','','- `characters-01.png`〜`characters-03.png`：原画、実寸、3倍表示。','- `young-01-poses.png`〜`young-04-poses.png`：若い4人のポーズ一覧。','- `target-character-compare.png`：目標の村と人物の色・縮尺の比較。参考画像はゲーム素材へ転用していない。','- `assets/source_records/owner-characters.json`：全118コマの切り出し座標、原本SHA-256、共通16色、出力SHA-256。','','## 未提供・未接続','','若い4人のうち4人目の詠唱・被弾・勝利の原画は未提供。今回の原画には含まれないため生成していない。全員の4方向歩行も今回の原画からは作れないため、歩行シートを偽造していない。物語への配置と画面への接続は後続の依頼で行う。','','狛犬の対の候補は、既に登録済みの `gold_guard_lion` と `silver_guard_lion` の原画・画像を参照する。今回の用途のために敵の配置や画像を変えていない。','','検査は `python tools/check_sprint1_characters.py`。完成時の固定タグを読み、後続スプリントの作業ツリーには依存しない。','']
    (OUT/'README.md').write_text('\n'.join(doc),encoding='utf8',newline='\n')
    print(f'OWNER_CHARACTERS_IMPORT: characters={len(standing)} action_poses={len(rows)-len(standing)} files={len(rows)}')

if __name__=='__main__':main()
