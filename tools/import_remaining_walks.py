"""残り8職の歩行原画を、固定顔色と16色上限を保って32×48へ取り込む。"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from import_job_costumes import parts, PAL, COLORS
from import_remaining_battles import JOBS, NAMES, EXTRA_COLORS, clothing_pixels
from validate_assets import load_palette

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'assets/_incoming/walk-eight-2026-09-28'
OUT = ROOT / 'docs/verification/sprint3-walk-eight'
RECORD = ROOT / 'assets/source_records/walk-eight-conversion.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nearest(rgb, palette):
    return ((rgb[..., None, :].astype(np.int32)-palette)**2).sum(-1).argmin(-1)


def convert(frames, job):
    scale = min(44/max(im.height for im, _ in frames), 30/max(im.width for im, _ in frames))
    prepared = []
    required = set()
    for im, box in frames:
        body = im.resize((max(1, round(im.width*scale)), max(1, round(im.height*scale))), Image.Resampling.NEAREST)
        a = np.array(body)
        opaque = a[:, :, 3] >= 160
        base = nearest(a[:, :, :3], PAL)
        # 上部44%は頭髪と顔を含む。大きな緑・赤の衣装面だけを除き、目・口の小面は固定色へ残す。
        head = opaque & (np.indices(opaque.shape)[0] < body.height*.44) & ~clothing_pixels(body, job)
        required.update(base[head].tolist())
        prepared.append((a, opaque, base, head))
    palette_hex = COLORS + EXTRA_COLORS.get(job, [])
    candidates = np.array([[int(c[i:i+2], 16) for i in (0, 2, 4)] for c in palette_hex], dtype=np.int32)
    chosen = sorted(required)
    assert len(chosen) <= 16, '固定顔色が16色を超える'
    costume = np.concatenate([a[:, :, :3][mask & ~head] for a, mask, base, head in prepared])
    samples, weights = np.unique(costume, axis=0, return_counts=True)
    distances = ((samples[:, None, :].astype(np.int32)-candidates[None, :, :])**2).sum(2)
    best = distances[:, chosen].min(1)
    # 顔に必要な色は一切捨てず、空き枠だけを衣装の誤差が小さくなる色へ割り当てる。
    while len(chosen) < 16:
        available = [i for i in range(len(candidates)) if i not in chosen]
        if not available:
            break
        benefit = [int((np.maximum(best-distances[:, i], 0)*weights).sum()) for i in available]
        pick = available[int(np.argmax(benefit))]
        chosen.append(pick)
        best = np.minimum(best, distances[:, pick])
    palette = candidates[chosen]
    result = []
    fixed_pixels = 0
    for a, opaque, base, head in prepared:
        rgb = palette[nearest(a[:, :, :3], palette)]
        rgb[head] = PAL[base[head]]
        assert np.array_equal(rgb[head], PAL[base[head]])
        fixed_pixels += int(head.sum())
        a[:, :, :3] = rgb
        a[:, :, 3] = opaque*255
        a[~opaque] = 0
        body = Image.fromarray(a)
        body = body.crop(body.getchannel('A').getbbox())
        frame = Image.new('RGBA', (32, 48))
        frame.alpha_composite(body, ((32-body.width)//2, 48-body.height))
        assert frame.getchannel('A').getbbox()[3] == 48
        result.append(frame)
    assert len({im.tobytes() for im in result}) == 12, '重複した歩行コマ'
    for col in range(3):
        assert result[3+col].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes() != result[6+col].tobytes(), '左右が単純反転'
    return result, scale, [palette_hex[i] for i in chosen], fixed_pixels


def review(jobs):
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'), 19)
    for job in jobs:
        canvas = Image.new('RGB', (1240, 640), '#d6d2bb')
        draw = ImageDraw.Draw(canvas)
        for actor, name in enumerate(['カイナ', 'リオネ', 'ハルド', 'スイナ'], 1):
            draw.text(((actor-1)*310+12, 8), NAMES[job]+' / '+name, font=font, fill='#15212b')
            im = Image.open(ROOT/f'assets/characters/pc_{actor:02}/jobs/{job}/walk.png')
            im = im.resize((288, 576), Image.Resampling.NEAREST)
            canvas.paste(im, ((actor-1)*310+10, 42), im)
        canvas.save(OUT/(job+'-walk-sheet.png'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jobs', nargs='+', choices=JOBS, required=True)
    args = parser.parse_args()
    registry = json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    entries = {e['path']: e for e in registry['assets']}
    visuals = json.loads((ROOT/'data/character_visuals.json').read_text(encoding='utf8'))
    records = json.loads(RECORD.read_text(encoding='utf8')) if RECORD.exists() else []
    records = [r for r in records if r['job'] not in args.jobs]
    allowed = load_palette(ROOT/'assets/palette/natural.gpl')
    for job in args.jobs:
        walks = [parts(RAW/(job+'-walk-'+pair+'.png'), 6, 4) for pair in ['12', '34']]
        reference = f'assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_{JOBS[job]}.PNG'
        for index in range(4):
            actor = f'pc_{index+1:02}'
            frames = [walks[index//2][row*6+(index%2)*3+col] for row in range(4) for col in range(3)]
            normalized, scale, palette, fixed_pixels = convert(frames, job)
            sheet = Image.new('RGBA', (96, 192))
            for i, frame in enumerate(normalized):
                sheet.alpha_composite(frame, (i%3*32, i//3*48))
            pixels = np.asarray(sheet)
            colors = set(map(tuple, pixels[:, :, :3][pixels[:, :, 3]>0].tolist()))
            assert len(colors) <= 16 and colors <= allowed
            rel = f'assets/characters/{actor}/jobs/{job}/walk.png'
            path = ROOT/rel
            path.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(path)
            raw = RAW/(job+'-walk-'+('12' if index<2 else '34')+'.png')
            records.append(dict(actor=actor, job=job, path=rel, raw=raw.relative_to(ROOT).as_posix(), raw_sha256=digest(raw), reference=reference, reference_sha256=digest(ROOT/reference), boxes=[box for _, box in frames], scale=scale, alpha_threshold=160, ground_y=47, fixed_identity_palette=COLORS, palette=palette, actual_colors=len(colors), fixed_head_pixels=fixed_pixels, head_rule='不透明領域の上部44%。既存の衣装色面判定で大きな緑・赤の面を除外。小さな目・口は固定。RGB最近傍は完成済み4職の16色と同一。', sha256=digest(path)))
            entries[rel] = dict(path=rel, kind='character_walk', size=[96,192], frame=[32,48], grid=[3,4], max_colors=16, status='required', palette='assets/palette/natural.gpl', source='generated', tool='imagegen + Python/Pillow', author='RPG-maker / Codex（衣装原画：依頼者）', license='LicenseRef-Generated-Project', generated_at='2026-09-28', prompt_record='assets/source_records/walk-eight-generation.json', conversion_record='assets/source_records/walk-eight-conversion.json', modified='指定衣装と設定画から4方向3コマを生成。最近傍縮小、顔色固定、16色以内、二値透過、接地行47。左右は別作画。', actor_id=actor, job_id=job)
            visuals['actors'][actor]['jobs'][job]['walk'] = rel
    registry['assets'] = list(entries.values())
    for path, value in [(ROOT/'assets/registry.json', registry), (ROOT/'data/character_visuals.json', visuals), (RECORD, records)]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8', newline='\n')
    review(args.jobs)
    print(f'WALK_EIGHT_PASS: jobs={len(args.jobs)} sheets={len(args.jobs)*4} frames={len(args.jobs)*48} colors<=16')


if __name__ == '__main__':
    main()
