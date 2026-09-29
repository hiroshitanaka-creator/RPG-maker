"""残る3人の魔物化素材を作る。人物別配色、目印、目の光を記録する。"""
import argparse,json,hashlib
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont
from prepare_party_forms import ROOT,RAW,REVIEW,FORMS,NAMES,ACTORS,sha
from validate_assets import load_palette

COLORS={
'pc_02':['250F07','3A2317','5D2717','68422F','90422D','9A6048','BF694D','D09279','3D0B14','74281B','B3433F','314619','657B2A','88A441','B2CA60','C8DB7F','D9CCB4','E9E7CB','EEF6EB','CE9F54'],
'pc_03':['0B1824','162835','254A63','728593','BDC7D3','EEF6EB','3C3B35','58544C','726C61','8A8374','A49A88','B5AA95','C4BAA4','D9CCB4','E9E7CB','3A2317','68422F','CE9F54','EDBB5B','F6D275'],
'pc_04':['2C1251','4D267F','7342B7','A778DE','0B1824','153550','254A63','728593','BDC7D3','EEF6EB','3A2317','68422F','CE9F54','D7B778','EDBB5B','F6D275','22221E','58544C','B5AA95','E9E7CB']}
WALK_COLORS={
'pc_02':['250F07','3A2317','68422F','90422D','9A6048','BF694D','D09279','B3433F','314619','657B2A','88A441','C8DB7F','D9CCB4','E9E7CB','EEF6EB','CE9F54'],
'pc_03':['0B1824','254A63','728593','BDC7D3','EEF6EB','3C3B35','58544C','8A8374','B5AA95','C4BAA4','D9CCB4','E9E7CB','3A2317','68422F','CE9F54','F6D275'],
'pc_04':['27172A','53335F','8C5996','D991B5','0B1824','254A63','728593','BDC7D3','EEF6EB','3A2317','68422F','CE9F54','D7B778','22221E','58544C','E9E7CB']}

def split(path):
    im=Image.open(path).convert('RGBA');a=np.array(im);a[:,:,3]=(a[:,:,3]>=160)*255;a[a[:,:,3]==0]=0
    labels,count=ndimage.label(a[:,:,3]>0,structure=np.ones((3,3)))
    areas=np.bincount(labels.ravel());areas[0]=0
    main=np.argsort(-areas)[:15];assert len(main)==15 and min(areas[main])>100
    centers=np.array(ndimage.center_of_mass(a[:,:,3]>0,labels,np.arange(1,count+1)))
    major=centers[main-1]
    assigned=np.argmin(((centers[:,None,:]-major[None,:,:])**2).sum(2),axis=1)+1
    lookup=np.zeros(count+1,dtype=np.int32);lookup[1:]=assigned
    groups=lookup[labels];frames=[]
    for i in range(15):
        piece=a.copy();piece[groups!=i+1]=0;p=Image.fromarray(piece);box=p.getbbox();assert box
        frames.append((p.crop(box),list(box)))
    frames.sort(key=lambda item:(item[1][1]+item[1][3])/2)
    ordered=[]
    for row in range(5):ordered.extend(sorted(frames[row*3:row*3+3],key=lambda item:(item[1][0]+item[1][2])/2))
    return ordered

def paint(frame,actor,form,pose,kind,palette):
    a=np.array(frame);rgb=a[:,:,:3].astype(float);opaque=a[:,:,3]>0
    gamma=1.0 if actor=='pc_03' else (.8 if form=='plant' else .88)
    target=255*(rgb/255)**gamma
    target=np.where((rgb.max(2)<16)[:,:,None],rgb,target)
    nearest=((target[:,:,None,:]-palette[None,None,:,:])**2).sum(3).argmin(2)
    out=palette[nearest].astype(np.uint8)
    if actor=='pc_04':
        # 青紫をRGB距離だけで選ぶと淡い桃色へ偏る。紫の段階から明度が近い色を選ぶ。
        purple=(rgb[:,:,2]>rgb[:,:,1]*1.3)&(rgb[:,:,0]>rgb[:,:,1]*1.15)&(rgb[:,:,0]>rgb[:,:,2]*.5)
        ramp=np.array([[44,18,81],[77,38,127],[115,66,183],[167,120,222],[238,246,235]]) if kind=='battle' else np.array([[39,23,42],[83,51,95],[140,89,150],[217,145,181],[238,246,235]])
        lum=(target*[.2126,.7152,.0722]).sum(2)
        levels=(ramp*[.2126,.7152,.0722]).sum(1)
        indices=abs(lum[:,:,None]-levels).argmin(2)
        out[purple]=ramp[indices[purple]]
    # 目・発光部は原画の明るい有彩色を拾う。人物の体色に合わせて判定を分ける。
    if actor=='pc_02':glow=(rgb[:,:,1]>rgb[:,:,0]*1.3)&(rgb[:,:,1]>rgb[:,:,2]*1.3)&(rgb[:,:,1]>130)
    elif actor=='pc_03':glow=(rgb[:,:,0]>rgb[:,:,1]*1.2)&(rgb[:,:,1]>rgb[:,:,2]*1.25)&(rgb[:,:,0]>65)
    else:glow=(rgb[:,:,0]>rgb[:,:,1]*1.3)&(rgb[:,:,2]>rgb[:,:,1]*1.5)&(rgb[:,:,0]>190)&(rgb[:,:,2]>215)
    yy,xx=np.indices(opaque.shape)
    if actor=='pc_03':glow&=yy<frame.height*.64 # 足・爪の暖色を除く。目の手動確認記録と併用する。
    glow&=opaque
    if kind=='walk':glow[:]=False # 小さい目印の1画素を白へ置き換えず、識別色を保持する。
    labels,n=ndimage.label(glow,structure=np.ones((3,3)));cores=[]
    axis=np.array(Image.fromarray(np.arange(frame.width,dtype=np.int32)[None,:]).resize((72 if kind=='battle' else frame.width,1),Image.Resampling.NEAREST))[0]
    sampled=set(axis)
    for k in range(1,n+1):
        coords=np.argwhere(labels==k)
        if len(coords)<1:continue
        # 目印も同色の原画は光の上位部分を残す。白い体の広い部分を発光扱いにしない。
        luminance=(rgb[labels==k]*[.2126,.7152,.0722]).sum(1)
        candidates=[i for i,(y,x) in enumerate(coords) if x in sampled and (kind!='battle' or y in sampled)]
        if candidates:y,x=coords[max(candidates,key=lambda i:luminance[i])]
        else:
            y,x=coords[luminance.argmax()]
            nearby=[(cy,cx) for cy in range(max(0,y-1),min(frame.height,y+2)) for cx in range(max(0,x-1),min(frame.width,x+2)) if cy in sampled and cx in sampled and opaque[cy,cx]]
            if not nearby:continue
            y,x=min(nearby,key=lambda point:(point[0]-y)**2+(point[1]-x)**2)
        out[y,x]=[238,246,235];cores.append([int(x),int(y)])
    a[:,:,:3]=out;a[~opaque]=0
    return Image.fromarray(a),dict(gamma=gamma,light_cores=cores,source_glow_pixels=int(glow.sum()))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--actors',nargs='+',default=list(ACTORS));parser.add_argument('--forms',nargs='+',default=FORMS);parser.add_argument('--kinds',nargs='+',choices=['battle','walk'],default=['battle','walk']);args=parser.parse_args()
    registry_path=ROOT/'assets/registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8'));entries={e['path']:e for e in registry['assets']}
    visuals=json.loads((ROOT/'data/character_visuals.json').read_text(encoding='utf-8'))
    sources={(r['actor'],r['form']):r for r in json.loads((ROOT/'assets/source_records/party-form-cutouts.json').read_text(encoding='utf-8'))}
    record_path=ROOT/'assets/source_records/party-form-conversion.json'
    records=json.loads(record_path.read_text(encoding='utf-8')) if record_path.exists() else []
    records=[r for r in records if not(r['actor'] in args.actors and r['form'] in args.forms and r['kind'] in args.kinds)]
    full_palette=load_palette(ROOT/'assets/palette/natural.gpl')
    for actor in args.actors:
        for form in args.forms:
            raw=RAW/f'{actor}-{form}-motions.png';all_frames=split(raw)
            order=list(range(15))
            if actor=='pc_03' and form=='bird':
                # 生成原画の左右歩行の3コマ目が逆の行にある。反転せず正しい向きの行へ戻す。
                order[8],order[11]=order[11],order[8]
                all_frames=[all_frames[i] for i in order]
            source=sources[actor,form]
            for kind,frames,width,height,grid in [('battle',all_frames[:3],96,96,[3,1]),('walk',all_frames[3:],32,48,[3,4])]:
                if kind not in args.kinds:continue
                codes=COLORS[actor] if kind=='battle' else WALK_COLORS[actor]
                palette=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in codes],dtype=np.int32)
                assert len(codes)<=(20 if kind=='battle' else 16) and set(map(tuple,palette.tolist()))<=full_palette
                scale=min((height-4)/max(im.height for im,_ in frames),(width-4)/max(im.width for im,_ in frames))
                sheet=Image.new('RGBA',(width*3,height*grid[1]));poses=[]
                for i,(im,box) in enumerate(frames):
                    im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
                    a=np.array(im);a[:,:,3]=(a[:,:,3]>=160)*255;a[a[:,:,3]==0]=0;im=Image.fromarray(a);im=im.crop(im.getbbox())
                    frame=Image.new('RGBA',(width,height));frame.alpha_composite(im,((width-im.width)//2,height-im.height))
                    frame,details=paint(frame,actor,form,i,kind,palette)
                    assert frame.getbbox()[3]==height
                    sheet.alpha_composite(frame,(i%3*width,i//3*height))
                    poses.append(dict(bbox=list(frame.getbbox()),sha256=hashlib.sha256(frame.tobytes()).hexdigest(),**details))
                assert len({r['sha256'] for r in poses})==len(poses),'同じ動作コマがある'
                path=visuals['actors'][actor]['forms'][form][kind];sheet.save(ROOT/path)
                entries[path].update(size=list(sheet.size),frame=[width,height],grid=grid,max_colors=20 if kind=='battle' else 16,palette='assets/palette/natural.gpl',source='generated',tool='imagegen + Python/Pillow',author='RPG-maker / Codex（魔物化原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-29',original_file=source['source'],prompt_record=f'assets/source_records/party-form-generation/{actor}-{form}.json',conversion_record='assets/source_records/party-form-conversion.json',modified='新原画の姿と目印を基準に動作を生成。最近傍縮小・人物別20色以内（歩行16色）・二値透過・接地行統一。原画の明部と目の光を保持。')
                records.append(dict(actor=actor,form=form,kind=kind,path=path,source=source['source'],source_sha256=source['source_sha256'],reference=source['reference'],reference_sha256=source['reference_sha256'],raw=str(raw.relative_to(ROOT)).replace('\\','/'),raw_sha256=sha(raw),boxes=[box for im,box in frames],frame_order=order[:3] if kind=='battle' else order[3:],scale=scale,frame=[width,height],grid=grid,palette=codes,output_sha256=sha(ROOT/path),poses=poses))
            prompt_path=ROOT/f'assets/source_records/party-form-generation/{actor}-{form}.json'
            prompt=json.loads(prompt_path.read_text(encoding='utf-8'));prompt['reference_sha256']=sha(ROOT/prompt['reference']);prompt['raw_sha256']=sha(ROOT/prompt['raw'])
            prompt_path.write_text(json.dumps(prompt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
            print('PARTY_FORM_IMPORTED:',actor,form,flush=True)
    registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    records.sort(key=lambda r:(r['actor'],FORMS.index(r['form']),0 if r['kind']=='battle' else 1))
    record_path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':main()
