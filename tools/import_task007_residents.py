"""007だけの歩行動作を決定論的に取り込む。原画・旧素材・パレットは書かない。"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
from import_job_costumes import parts
from import_region2_port_assets import quantize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/verification/task-007'
OWNER = 'assets/_incoming/owner-2026-10-04-grok-region3/region3-world-map-alt-a.png'
RECORD = 'assets/source_records/task007-residents.json'
IDS = ['water_keeper', 'date_farmer', 'innkeeper', 'camel_keeper', 'elder', 'child']
LABELS = ['泉の番人', 'ナツメヤシの農夫', '宿のおかみ', 'ラクダ飼い', '村の長老', '子ども']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def render():
    outputs = []
    for pair in range(3):
        source = f'docs/verification/task-007/generated/pair{pair+1}.png'
        frames = parts(ROOT / source, 6, 4)
        assert len(frames) == 24
        for person in range(2):
            index = pair * 2 + person
            selected = [frames[row*6 + person*3 + col] for row in range(4) for col in range(3)]
            height = 34 if index == 5 else 44
            scale = min(height / max(im.height for im, _ in selected), 30 / max(im.width for im, _ in selected))
            sheet = Image.new('RGBA', (96, 192))
            for frame, (image, _) in enumerate(selected):
                image = image.resize((max(1, round(image.width*scale)), max(1, round(image.height*scale))), Image.Resampling.NEAREST)
                sheet.alpha_composite(image, (frame % 3 * 32 + (32-image.width)//2, frame // 3 * 48 + 48-image.height))
            sheet, colors = quantize(sheet, 16)
            outputs.append((sheet, dict(id=IDS[index], label=LABELS[index], path=f'assets/characters/npc_oasis_{IDS[index]}/walk.png', generated_source=source, generated_sha256=sha(ROOT/source), owner_reference=OWNER, owner_sha256=sha(ROOT/OWNER), boxes=[box for _, box in selected], scale=scale, colors=colors, ground_y=47, row_order=['down','left','right','up'], column_order=['standing','left_foot','right_foot'], operations='別々に生成した全12コマ。左右反転・同一コマ複製なし。最近傍縮小・RGB最近傍16色・二値透過・接地47。')))
    return outputs

def main():
    outputs = render()
    registry = json.loads((ROOT/'assets/registry.json').read_text())
    paths = {r['path'] for _, r in outputs}
    # 今回の6項目だけ更新。既存1134項目の内容・順序を保持する。
    registry['assets'] = [e for e in registry['assets'] if e['path'] not in paths]
    for image, record in outputs:
        target = ROOT/record['path']; target.parent.mkdir(parents=True, exist_ok=True); image.save(target)
        record['sha256'] = sha(target)
        registry['assets'].append(dict(path=record['path'], kind='character_walk', size=[96,192], frame=[32,48], grid=[3,4], max_colors=16, status='required', palette='assets/palette/natural.gpl', source='generated', tool='imagegen + Python/Pillow', generated_at='2026-10-04', author='RPG-maker / Codex（設定原画：依頼者）', license='LicenseRef-Generated-Project', prompt_record='assets/source_records/task007-residents-generation.json', conversion_record=RECORD, original_file=OWNER, modified=record['operations']))
    for path, value in [(ROOT/'assets/registry.json', registry), (ROOT/RECORD, dict(owner_unchanged=True, palette_added=[], entries=[r for _,r in outputs]))]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    font = ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'), 18)
    board = Image.new('RGB',(960,1272),'#c8c2ad'); d=ImageDraw.Draw(board)
    for index, (image, record) in enumerate(outputs):
        x=index%3*320; y=index//3*630
        d.text((x+8,y+8),record['label'],font=font,fill='#1c2830')
        d.text((x+8,y+35),'下 / 左 / 右 / 上・直立 / 左足 / 右足',font=font,fill='#1c2830')
        large=image.resize((288,576),Image.Resampling.NEAREST);board.paste(large,(x+16,y+60),large)
    board.save(OUT/'residents-walk.png')
    print('TASK007_IMPORT_PASS: people=6 frames=72 palette_added=0')

if __name__ == '__main__':
    main()
