"""素材の保存記録を照合し、原画・切り抜き・3背景の確認画像を組み立てる。"""
from pathlib import Path
import hashlib, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from prepare_kaina_forms import ROOT, SOURCE, OUT, REVIEW, SPECS, sha
from validate_assets import check_asset, load_palette

BASE='53c1d8979296a7a54e3264aa870d825dd1cc4c8d'

def git_bytes(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,check=True,capture_output=True).stdout

def main():
    records=json.loads((ROOT/'assets/source_records/kaina-form-conversion.json').read_text(encoding='utf-8'))
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    entries={e['path']:e for e in registry['assets']}
    changed={r['path'] for r in records}
    assert len(changed)==16
    baseline=json.loads(git_bytes('assets/registry.json'))
    unchanged=0
    for entry in baseline['assets']+baseline.get('audio',[])+baseline.get('fonts',[]):
        path=entry['path']
        if path in changed:continue
        assert (ROOT/path).read_bytes()==git_bytes(path),path
        unchanged+=1
    for path in ['assets/palette/base.gpl','assets/palette/bright.gpl','assets/palette/natural.gpl','data/character_visuals.json']:
        assert (ROOT/path).read_bytes()==git_bytes(path),path
    checks=[]
    for record in records:
        path=record['path'];entry=entries[path]
        errors,exists=check_asset(entry,load_palette(ROOT/'assets/palette/natural.gpl'))
        assert exists and not errors,(path,errors)
        assert sha(ROOT/path)==record['output_sha256']
        assert sha(ROOT/record['source'])==record['source_sha256']
        assert sha(ROOT/record['raw'])==record['raw_sha256']
        assert record['source'].split('/')[-1] in ['IMG_1100.PNG','IMG_1105.PNG','IMG_1109.PNG']
        sheet=Image.open(ROOT/path).convert('RGBA');w,h=record['frame']
        all_colors=set()
        for i,pose in enumerate(record['poses']):
            frame=sheet.crop((i%3*w,i//3*h,(i%3+1)*w,(i//3+1)*h))
            assert hashlib.sha256(frame.tobytes()).hexdigest()==pose['sha256']
            pixels=np.array(frame);opaque=pixels[:,:,3]>0
            colors=set(map(tuple,pixels[:,:,:3][opaque].tolist()));all_colors|=colors
            assert {(11,24,36),(21,53,80),(37,74,99)}&colors,'紺色が残っていない'
            assert frame.getbbox()[3]==h
            if record['kind']=='battle':
                scaled=frame.resize((72,72),Image.Resampling.NEAREST);a=np.array(scaled)
                assert set(np.unique(a[:,:,3]))<={0,255}
                assert set(map(tuple,a[:,:,:3][a[:,:,3]>0].tolist()))<=colors,'縮小で新しい中間色が生じた'
        checks.append(dict(path=path,colors=len(all_colors),frames=len(record['poses']),binary_alpha=True,source_match=True,nearest_72_no_new_colors=record['kind']=='battle'))
    originals=[]
    for source in sorted(SOURCE.glob('*.PNG')):
        path=str(source.relative_to(ROOT)).replace('\\','/')
        assert source.read_bytes()==git_bytes(path)
        originals.append(dict(path=path,sha256=sha(source),size=list(Image.open(source).size)))
    assert len(originals)==9
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    # 入力参考の切り抜きは生成時のまま保存する。比較用には枝の内側の灰色背景も除去する。
    cutout_review=Image.new('RGB',(1000,8*280),'#e1dfd6');d=ImageDraw.Draw(cutout_review)
    for row,(form,(number,box,label)) in enumerate(SPECS.items()):
        raw=Image.open(SOURCE/f'IMG_{number}.PNG').convert('RGBA').crop(box)
        original_cut=Image.open(OUT/f'{form}-reference.png').convert('RGBA')
        a=np.array(original_cut);rgb=a[:,:,:3].astype(np.int16)
        # 枝に囲まれた穴の灰色を背景サンプルと照合。体の青白い光沢とは色相が異なる。
        neutral=(rgb.max(2)-rgb.min(2)<=4)&(rgb.min(2)>=205)
        if form in ('plant','shell','spirit','dragon'):
            # この4姿の明るい無彩色は枝・翼・脚の間の背景。青い体と発光線は色差で保持。
            neutral=(rgb.max(2)-rgb.min(2)<=24)&(rgb.min(2)>=170)
        a[neutral]=0
        cut=Image.fromarray(a);cut.save(OUT/f'{form}-cutout-review.png')
        d.text((12,row*280+4),label+'：原画の該当範囲 ／ 切り抜き（同じ倍率）',font=font,fill='#162835')
        bbox=json.loads((ROOT/'assets/source_records/kaina-form-cutouts.json').read_text(encoding='utf-8'))[row]['alpha_bbox']
        canvas=Image.new('RGBA',raw.size);canvas.alpha_composite(cut,(bbox[0],bbox[1]))
        factor=min(450/raw.width,238/raw.height)
        for col,im in enumerate([raw,canvas]):
            im=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.NEAREST)
            x=col*500+20;y=row*280+36
            for yy in range(y,y+238,12):
                for xx in range(x,x+450,12):d.rectangle((xx,yy,xx+11,yy+11),fill='#b5b7b9' if (xx//12+yy//12)%2 else '#dddfe2')
            cutout_review.paste(im,(x,y),im)
    cutout_review.save(REVIEW/'source-cutouts.png')
    for background,label in [('plains','平原'),('cave','洞窟'),('underworld','死者の国')]:
        panel=Image.new('RGB',(1024,4*316),'#e1dfd6');d=ImageDraw.Draw(panel)
        for i,(form,(_,_,name)) in enumerate(SPECS.items()):
            x=i%2*512;y=i//2*316;d.text((x+8,y+2),name+' ／ '+label,font=font,fill='#162835')
            image=Image.open(REVIEW/'runtime'/f'{form}-{background}.png')
            assert image.size==(1024,576)
            panel.paste(image.resize((512,288),Image.Resampling.NEAREST),(x,y+28))
        panel.save(REVIEW/f'battle-{background}-eight.png')
    result=dict(status='PASS',baseline=BASE,forms=8,sheets=16,battle_frames=24,walk_frames=96,unchanged_registered_files=unchanged,unchanged_owner_originals=originals,checks=checks,meaning='素材・記録の一致。紺色の画素の存在は確認するが、布の読み取りや姿の採用は画像で依頼者が判断する。ハルドを含む残り3人には未適用。')
    (REVIEW/'asset-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 新しい魔物化原画9枚','', 'PR #2で依頼者から提供された原本。1バイトも変更せず保管する。使用対応は docs/roadmap-v2.md の付録B更新表を優先する。','', '今回の制作はカイナのIMG_1100（左3体）、IMG_1105（4体）、IMG_1109（左1体）のみ。旧IMG_1032〜1035・IMG_1093〜1097は使用しない。','', '| 原本 | 寸法 | SHA-256 |','| --- | --- | --- |']
    for r in originals:lines.append('| '+Path(r['path']).name+' | 1168×784 | '+r['sha256']+' |')
    (SOURCE/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'KAINA_REVIEW_PASS: sheets=16 originals=9 unchanged_registered_files={unchanged}')

if __name__=='__main__':main()
