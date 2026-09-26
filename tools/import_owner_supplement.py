#!/usr/bin/env python3
"""追加の依頼者原画3枚を保管し、敵3体だけを同じパスへ変換する。"""
from pathlib import Path
import argparse, hashlib, io, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
from import_owner_monsters import ROOT, split_parts, convert

BASE = 'e2e1c3bcd7d15b964951a853eb938e97658d5eb5'
ORIGINAL = 'assets/_incoming/owner-2026-09-26/supplement-2026-09-27'
RECORD = 'assets/source_records/owner-supplement.json'
OUT = ROOT / 'docs/verification/owner-supplement'
DEFINITIONS = [('bone_bat', '骨翼コウモリ', 'small', 56, 64), ('glacier_turtle', '氷の甲羅の亀', 'medium', 80, 96), ('zombie_wolf', '腐りかけた狼', 'medium', 80, 96)]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf8', newline='\n')

def render(part, box, extent, canvas):
    temporary = convert(part, box, [extent+4, extent+4], False)
    body = temporary.crop(temporary.getchannel('A').getbbox())
    out = Image.new('RGBA', (canvas, canvas))
    out.alpha_composite(body, ((canvas-body.width)//2, canvas-2-body.height))
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attachments', type=Path, help='初回だけ指定。原本を再符号化せず複写する')
    args = parser.parse_args()
    folder = ROOT / ORIGINAL
    folder.mkdir(parents=True, exist_ok=True)
    sources = []
    for logical, filename, role in [('IMG_0973','1-写真1.jpg','敵3体'), ('IMG_0974','3-写真3.jpg','船4方向・スプリント5で変換'), ('IMG_0975','2-写真2.jpg','鷲の頭と翼を持つ空飛ぶ船4方向・スプリント5で変換')]:
        path = folder / filename
        if args.attachments:
            raw = (args.attachments / filename).read_bytes()
            if path.exists():
                assert path.read_bytes() == raw, '既存原本は上書きしない'
            else:
                shutil.copyfile(args.attachments / filename, path)
            assert path.read_bytes() == raw
        sources.append(dict(logical_id=logical, path=path.relative_to(ROOT).as_posix(), sha256=sha(path.read_bytes()), bytes=path.stat().st_size, role=role))
    write_json(folder/'manifest.json', dict(provided_at='2026-09-27', author='依頼者', generator='Grok', license='LicenseRef-Owner-Provided', authorization='完全オリジナルで公開とゲームでの使用を承認したという依頼者の申告。追加3枚の共有会話URLは未指定。', sources=sources))
    lines=['# 追加原画の保管記録', '', '2026年9月27日受領。依頼者がGrokで生成した完全オリジナルであり、公開とゲームでの使用を承認したと申告した。添付のJPEGを1バイトも変えず、元のファイル名で保管した。', '', '写真2が空飛ぶ船、写真3が通常の船。依頼文のIMG番号と添付の番号は異なるため、画像の内容を照合して下表で対応付ける。船2種は原画の保管のみ。ゲーム用素材への変換・台帳登録・ゲームへの接続はしていない。', '', '| 論理番号 | 添付名 | 用途 | SHA-256 |', '| --- | --- | --- | --- |']
    for r in sources:
        lines.append(f"| {r['logical_id']} | {Path(r['path']).name} | {r['role']} | {r['sha256']} |")
    (folder/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf8')
    parts = split_parts(Image.open(ROOT/sources[0]['path']), 3)
    registry_path=ROOT/'assets/registry.json'
    registry=json.loads(registry_path.read_text(encoding='utf8'))
    entries={e['path']:e for e in registry['assets']}
    rows=[]
    for index, ((id_, name, category, extent, canvas), (part, box)) in enumerate(zip(DEFINITIONS, parts), 1):
        path=f'assets/monsters/{id_}/idle.png'
        picture=render(part, box, extent, canvas)
        picture.save(ROOT/path)
        bounds=picture.getchannel('A').getbbox()
        visible=[bounds[2]-bounds[0], bounds[3]-bounds[1]]
        row=dict(id=id_, name=name, path=path, original_file=sources[0]['path'], original_sha256=sources[0]['sha256'], logical_id='IMG_0973', slot=index, crop=list(box), black_threshold=24, resampling='nearest', mirror=False, max_colors=32, size_class=category, target_extent=extent, size=[canvas,canvas], visible_size=visible, output_sha256=sha((ROOT/path).read_bytes()))
        rows.append(row)
        entries[path].update(size=row['size'], max_colors=32, palette='assets/palette/natural.gpl', source='owner', license='LicenseRef-Owner-Provided', author='依頼者', provided_at='2026-09-27', original_file=row['original_file'], conversion_record=RECORD+'#'+id_, size_class=category, visible_size=visible, facing='front' if index==1 else 'right', modified=f'左から{index}体目。外周につながるRGB最大24以下の黒背景を除去。最近傍縮小、自然色32色以内、二値透過。絵の長辺{extent}px。反転なし。')
    write_json(registry_path, registry)
    write_json(ROOT/RECORD, dict(baseline=BASE, imported=rows, sources=sources))
    doc=ROOT/'docs/monster-catalog.md'
    text=doc.read_text(encoding='utf8')
    for r in rows:
        id_=r['id']
        old=next(line for line in text.splitlines() if line.startswith(f'| {id_} | 旧画像維持 |')) if f'| {id_} | 旧画像維持 |' in text else None
        new=f"| {id_} | IMG_0973 左から{r['slot']} | 2026年9月27日追加原画。指定の骨翼・氷の甲羅・腐敗した狼の外見に一致 |"
        if old: text=text.replace(old,new)
    marker='\n## 2026年9月27日の追加3体\n'
    if marker in text: text=text[:text.index(marker)]
    text+=marker+'\nスプリント0の体格差・岩壁は依頼者が採用済み。旧画像を保留していた3体を同じパスで置換し、既存22種すべての差し替えを済ませた。敵の配置・能力・遭遇条件は変更していない。\n\n| id | 原画 | 体格 | 絵の実寸 | キャンバス |\n| --- | --- | --- | --- | --- |\n'
    for r in rows:
        text+=f"| {r['id']} | IMG_0973 左から{r['slot']} | {'小' if r['size_class']=='small' else '中'} | {r['visible_size'][0]}×{r['visible_size'][1]} | {r['size'][0]}×{r['size'][1]} |\n"
    doc.write_text(text,encoding='utf8',newline='\n')
    OUT.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',16)
    sheet=Image.new('RGB',(1080,620),'#d9d5c7');draw=ImageDraw.Draw(sheet)
    for i,(r,(part,box)) in enumerate(zip(rows,parts)):
        x=i*360
        draw.text((x+12,10),r['name']+' / '+r['id'],font=font,fill='black')
        source=part.crop(box);source.thumbnail((325,250),Image.Resampling.NEAREST)
        sheet.paste(source,(x+(360-source.width)//2,45),source)
        old=Image.open(io.BytesIO(subprocess.run(['git','show',BASE+':'+r['path']],cwd=ROOT,capture_output=True,check=True).stdout)).convert('RGBA')
        new=Image.open(ROOT/r['path']).convert('RGBA')
        draw.text((x+15,308),'旧 → 新（実寸）',font=font,fill='black')
        sheet.paste(old,(x+30,422-old.height),old);sheet.paste(new,(x+180,422-new.height),new)
        zoom=new.resize((new.width*2,new.height*2),Image.Resampling.NEAREST)
        sheet.paste(zoom,(x+20,430),zoom)
        draw.text((x+225,468),('小' if i==0 else '中')+f" / {r['visible_size'][0]}×{r['visible_size'][1]}px\n左下は2倍表示",font=font,fill='black')
    sheet.save(OUT/'three-monsters.png')
    import build_owner_monster_review as review
    review.OUT=OUT
    review.battle('battle-mock-cave.png',[r['id'] for r in rows])
    (OUT/'README.md').write_text('# 追加3体の確認\n\n2026年9月27日。three-monsters.png は原画の切り出し・旧絵・新絵の実寸と2倍表示。battle-mock-cave.png は512×288の静止配置であり、実際の遭遇編成を変更するものではない。\n\n原画3枚の対応とSHA-256は assets/_incoming/owner-2026-09-26/supplement-2026-09-27/manifest.json、変換条件は assets/source_records/owner-supplement.json に保存した。船2種は保管のみ。\n',encoding='utf8')
    print('OWNER_SUPPLEMENT_IMPORT: replaced=3 originals=3 boats_converted=0')

if __name__=='__main__':
    main()
