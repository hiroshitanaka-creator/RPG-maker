"""上下の壁の石積みから、尖らず幅が一定の左右用の低い石垣を作る。"""
import json
import hashlib
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def main():
    source='assets/objects/natural_wall_horizontal.png'
    target='assets/objects/castle_low_wall_vertical.png'
    original=Image.open(ROOT/source).convert('RGBA')
    # 胸壁より下のまっすぐな石積みを使う。階段状の縦壁や先細りの輪郭は使わない。
    strip=original.crop((0,24,96,64)).transpose(Image.Transpose.ROTATE_90)
    wall=Image.new('RGBA',(64,96));wall.alpha_composite(strip,(12,0));wall.save(ROOT/target)
    registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf8'))
    entries={e['path']:e for e in registry['assets']}
    entries[target]=dict(path=target,kind='object',size=[64,96],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-28',prompt_record='assets/source_records/visual-target-generation.json#wall_kit',modified='承認済みの水平壁から直線の石積み領域(0,24,96,64)を切り出し、90度回転して左右用の低い石垣へ配置。元画像・通行領域は不変。',component_sources=[source])
    registry['assets']=list(entries.values());registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    record={'source':source,'source_sha256':hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),'crop':[0,24,96,64],'rotation':90,'offset':[12,0],'output':target,'sha256':hashlib.sha256((ROOT/target).read_bytes()).hexdigest()}
    (ROOT/'assets/source_records/castle-low-wall.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    print('LOW_CASTLE_WALL_PASS: size=64x96 source_unchanged=1')

if __name__=='__main__':main()
