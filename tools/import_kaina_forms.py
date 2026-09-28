"""カイナ8系統の新しい動作原画を、既存形式・既存パレットへ変換する。"""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from import_job_costumes import parts
from prepare_kaina_forms import ROOT, OUT, REVIEW, SPECS, sha
from validate_assets import load_palette

COLORS=['0B1824','153550','254A63','215380','336C95','3174AC','5D98C4','728593','BDC7D3','EEF6EB','3A2317','68422F','9A6048','CE9F54','D7B778','53335F']
PAL=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in COLORS],dtype=np.int32)
RECORD='assets/source_records/kaina-form-conversion.json'

def normalize(frames,width,height,outline):
    scale=min((height-4)/max(im.height for im,_ in frames),(width-4)/max(im.width for im,_ in frames))
    result=[]
    for im,box in frames:
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
        a=np.array(im);mask=a[:,:,3]>=160
        colors,inverse=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
        nearest=((colors.astype(np.int32)[:,None,:]-PAL[None,:,:])**2).sum(2).argmin(1)
        a[:,:,:3]=PAL[nearest[inverse]].reshape(a.shape[:2]+(3,));a[:,:,3]=mask*255;a[~mask]=0
        body=Image.fromarray(a);body=body.crop(body.getbbox())
        frame=Image.new('RGBA',(width,height));frame.alpha_composite(body,((width-body.width)//2,height-1-body.height))
        if outline:
            a=np.array(frame);mask=a[:,:,3]>0
            edge=ndimage.binary_dilation(mask)&~mask
            a[edge]=[114,133,147,255] # natural.gpl の青灰色。暗い背景から輪郭を分離する1画素。
            frame=Image.fromarray(a)
        else:
            aligned=Image.new('RGBA',(width,height));aligned.alpha_composite(body,((width-body.width)//2,height-body.height));frame=aligned
        assert frame.getbbox()[3]==height
        result.append(frame)
    assert len({im.tobytes() for im in result})==len(result),'動作が同一になった'
    return result,scale

def main():
    assert set(map(tuple,PAL.tolist()))<=load_palette(ROOT/'assets/palette/natural.gpl')
    registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
    entries={e['path']:e for e in registry['assets']}
    visuals=json.loads((ROOT/'data/character_visuals.json').read_text(encoding='utf-8'))
    cutouts={r['form']:r for r in json.loads((ROOT/'assets/source_records/kaina-form-cutouts.json').read_text(encoding='utf-8'))}
    records=[];font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    comparison=Image.new('RGB',(1160,8*244),'#d8d4c7');draw=ImageDraw.Draw(comparison)
    walking=Image.new('RGB',(8*210,630),'#d8d4c7');wd=ImageDraw.Draw(walking)
    for row,(form,(_,_,label)) in enumerate(SPECS.items()):
        raw=OUT/f'{form}-motions.png';all_frames=parts(raw,3,5)
        assert len(all_frames)==15
        outputs={}
        for kind,frames,width,height,grid in [('battle',all_frames[:3],96,96,[3,1]),('walk',all_frames[3:],32,48,[3,4])]:
            # 精霊は元の明るい輪郭を使い、ほかは外側1画素の青灰色で暗所の見分けを補う。
            outline=(kind=='battle' and form!='spirit')
            normalized,scale=normalize(frames,width,height,outline)
            sheet=Image.new('RGBA',(width*3,height*grid[1]))
            for index,im in enumerate(normalized):sheet.alpha_composite(im,(index%3*width,index//3*height))
            path=visuals['actors']['pc_01']['forms'][form][kind]
            sheet.save(ROOT/path);outputs[kind]=sheet
            entry=entries[path]
            entry.update(size=list(sheet.size),frame=[width,height],grid=grid,max_colors=20 if kind=='battle' else 16,palette='assets/palette/natural.gpl',source='generated',tool='imagegen + Python/Pillow',author='RPG-maker / Codex（魔物化原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-29',original_file=cutouts[form]['source'],prompt_record='assets/source_records/kaina-form-generation.json',conversion_record=RECORD,modified='新原画の姿と紺色の布を参照して動作を生成。最近傍縮小・共通16色・二値透過・足元統一。'+('外側1画素の青灰色の縁取り。' if outline else '追加の縁取りなし。'))
            records.append(dict(actor='pc_01',form=form,kind=kind,path=path,source=cutouts[form]['source'],source_sha256=cutouts[form]['source_sha256'],raw=str(raw.relative_to(ROOT)).replace('\\','/'),raw_sha256=sha(raw),boxes=[box for im,box in frames],scale=scale,frame=[width,height],grid=grid,ground_y=height-1,palette=COLORS,outline=1 if outline else 0,output_sha256=sha(ROOT/path),poses=[dict(bbox=list(im.getbbox()),opaque_pixels=int((np.array(im)[:,:,3]>0).sum()),sha256=hashlib.sha256(im.tobytes()).hexdigest()) for im in normalized]))
        draw.text((12,row*244+4),label+'：新原画 ／ 戦闘 待機・攻撃・被弾（96pxの2倍表示）',font=font,fill='#162835')
        ref=Image.open(OUT/f'{form}-reference.png');ref.thumbnail((230,200),Image.Resampling.NEAREST)
        comparison.paste(ref,(12+(230-ref.width)//2,row*244+36),ref)
        battle=outputs['battle'].resize((576,192),Image.Resampling.NEAREST);comparison.paste(battle,(260,row*244+38),battle)
        draw.text((858,row*244+34),'実表示72px×2',font=font,fill='#162835')
        small=outputs['battle'].crop((0,0,96,96)).resize((72,72),Image.Resampling.NEAREST).resize((144,144),Image.Resampling.NEAREST)
        comparison.paste(small,(875,row*244+75),small)
        wd.text((row*210+10,6),label,font=font,fill='#162835')
        walk=outputs['walk'].resize((192,384),Image.Resampling.NEAREST);walking.paste(walk,(row*210+8,40),walk)
        wd.text((row*210+10,445),'下・左・右・上\n各3コマ\n32×48px',font=font,fill='#162835')
    registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/RECORD).write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    comparison.save(REVIEW/'source-battle-comparison.png');walking.save(REVIEW/'walk-eight.png')
    print('KAINA_FORMS_IMPORTED: forms=8 sheets=16 battle_frames=24 walk_frames=96 palette=16')

if __name__=='__main__':main()
