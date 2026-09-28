"""12職の歩行一覧、原画比較、既存素材不変の記録を作る。"""
import hashlib
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont
from import_remaining_walks import ROOT, OUT, RECORD, digest, review
from import_remaining_battles import JOBS, NAMES

BASE = 'e76c7748d25dae5398601dffa89d249d84e80ca1'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'), 22)
    font.set_variation_by_name('Medium')
    canvas = Image.new('RGB', (2400, 1720), '#d6d2bb')
    draw = ImageDraw.Draw(canvas)
    for i, (job, name) in enumerate(NAMES.items()):
        x, y = i%3*800, i//3*430
        draw.text((x+12,y+6), name+'　カイナ / リオネ / ハルド / スイナ', font=font, fill='#14212b')
        for actor in range(1,5):
            im = Image.open(ROOT/f'assets/characters/pc_{actor:02}/jobs/{job}/walk.png')
            im = im.resize((192,384), Image.Resampling.NEAREST)
            canvas.paste(im,(x+12+(actor-1)*196,y+40),im)
    canvas.save(OUT/'all-twelve-walks.png')
    for job, number in JOBS.items():
        source = Image.open(ROOT/f'assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_{number}.PNG').convert('RGB')
        source.thumbnail((820,550),Image.Resampling.LANCZOS)
        comparison = Image.new('RGB',(1240,1250),'#d6d2bb')
        d = ImageDraw.Draw(comparison)
        d.text((12,8),NAMES[job]+'：上は依頼者原画、下は32×48pxの歩行素材（3倍表示）',font=font,fill='#14212b')
        comparison.paste(source,((1240-source.width)//2,40))
        comparison.paste(Image.open(OUT/(job+'-walk-sheet.png')),(0,610))
        comparison.save(OUT/(job+'-reference-comparison.png'))
    generation_path = ROOT/'assets/source_records/walk-eight-generation.json'
    generations = json.loads(generation_path.read_text(encoding='utf8'))
    for record in generations:
        for key in ['raw','reference','identity_reference','style_reference']:
            record[key+'_sha256'] = digest(ROOT/record[key])
    generation_path.write_text(json.dumps(generations,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    # Gitの記録と比較し、採用済み画像・パレットに変更がないことを確かめる。
    listing = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','assets'],cwd=ROOT).decode().splitlines()
    preserved = 0
    for rel in listing:
        if '/_incoming/' in rel or not rel.endswith(('.png','.gpl')):
            continue
        old = subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT)
        assert (ROOT/rel).read_bytes()==old, '既存素材が変化: '+rel
        preserved += 1
    records = json.loads(RECORD.read_text(encoding='utf8'))
    assert len(records)==32
    for record in records:
        assert digest(ROOT/record['path'])==record['sha256']
        assert record['actual_colors']<=16
    audit = {'status':'PASS','baseline_commit':BASE,'existing_images_and_palettes_unchanged':preserved,'new_walk_sheets':32,'new_frames':384,'identity_rule':'完成済み4職の固定16色へのRGB対応を頭髪・顔の保護領域で維持。衣装のみ残り枠を使用。','protected_head_pixels':sum(r['fixed_head_pixels'] for r in records),'color_counts':{job:[r['actual_colors'] for r in records if r['job']==job] for job in JOBS}}
    (OUT/'asset-checks.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print(f'WALK_REVIEW_PASS: sheets=32 frames=384 existing_unchanged={preserved}')


if __name__ == '__main__':
    main()
