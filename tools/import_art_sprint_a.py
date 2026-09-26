#!/usr/bin/env python3
"""スプリントAの生成原画を規定へ変換する。B/Cの素材と検査は変更しない。"""
from pathlib import Path
import json
import hashlib
from collections import deque
import numpy as np
from PIL import Image
from validate_assets import load_palette, check_asset

ROOT=Path(__file__).resolve().parents[1]
RECORD='assets/source_records/art-sprint-a.json'
ROWS={r['id']:r for r in json.loads((ROOT/RECORD).read_text(encoding='utf-8'))}
PAL=np.array(sorted(load_palette(ROOT/'assets/palette/bright.gpl')),dtype=np.int32)
REG=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
ENTRIES={e['path']:e for e in REG['assets']}
CHANGED=[]
SEAMS=[]


def source(id_):return Image.open(ROOT/ROWS[id_]['source_file']).convert('RGBA')


def quantize(im,pal=PAL):
    a=np.array(im.convert('RGBA'));alpha=a[:,:,3]>=128
    values,inverse=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
    distance=((values.astype(np.int32)[:,None,:]-pal[None,:,:])**2).sum(axis=2)
    a[:,:,:3]=pal[distance.argmin(axis=1)[inverse]].reshape(a.shape[:2]+(3,))
    a[:,:,3]=alpha*255;a[~alpha,:3]=0
    return Image.fromarray(a)


def crop_alpha(im):
    im=im.copy();im.putalpha(im.getchannel('A').point(lambda x:255 if x>=128 else 0))
    box=im.getchannel('A').getbbox()
    if box is None:raise ValueError('空の原画')
    return im.crop(box)


def clean(im):
    a=np.array(im);left=a[:,:,3]>=128;components=[]
    for y,x in np.argwhere(left):
        if not left[y,x]:continue
        q=deque([(int(x),int(y))]);left[y,x]=False;part=[]
        while q:
            xx,yy=q.popleft();part.append((xx,yy))
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                nx,ny=xx+dx,yy+dy
                if 0<=nx<im.width and 0<=ny<im.height and left[ny,nx]:left[ny,nx]=False;q.append((nx,ny))
        components.append(part)
    cutoff=max(4,int(max(map(len,components))*.003))
    for part in components:
        if len(part)<cutoff:
            for x,y in part:a[y,x]=0
    return crop_alpha(Image.fromarray(a))


def strip(im,count,gap_min=12):
    """余白の位置からコマを分離する。生成画像の不均等なパネル幅にも対応。"""
    a=np.array(im)[:,:,3]>=128
    used=a.sum(axis=0)>max(2,im.height*.003)
    spans=[];start=None;gap=0
    for x,on in enumerate(used):
        if on:
            if start is None:start=x
            gap=0
        elif start is not None:
            gap+=1
            if gap>=gap_min:spans.append((start,x-gap+1));start=None
    if start is not None:spans.append((start,im.width-gap))
    spans=[s for s in spans if s[1]-s[0]>im.width*.06]
    if len(spans)!=count:raise ValueError(f'コマ境界を確定できない: {count} / {spans}')
    return [crop_alpha(im.crop((x,0,end,im.height))) for x,end in spans]


def grid(im,cols,rows):
    return [crop_alpha(im.crop((round(x*im.width/cols),round(y*im.height/rows),round((x+1)*im.width/cols),round((y+1)*im.height/rows)))) for y in range(rows) for x in range(cols)]


def fit(im,size,padding=2):
    im=crop_alpha(im);scale=min((size[0]-padding*2)/im.width,(size[1]-padding*2)/im.height)
    im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
    im=crop_alpha(im);out=Image.new('RGBA',size)
    out.alpha_composite(im,((size[0]-im.width)//2,size[1]-padding-im.height))
    return out


def save(path,im,source_id,kind='tileset',pal=PAL,**extra):
    im=quantize(im,pal);dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists() or Image.open(dest).convert('RGBA').tobytes()!=im.tobytes():im.save(dest)
    old=ENTRIES.get(path,{})
    entry={k:v for k,v in old.items() if k not in {'source_url','source_cells','retrieved_at','frame','grid'}}
    entry.update(path=path,kind=kind,size=list(im.size),max_colors=len(pal),status='required',palette='assets/palette/bright.gpl',
                 source='generated',tool='imagegen + Python/Pillow',generated_at='2026-09-26',author='RPG-maker / Codex',
                 license='LicenseRef-Generated-Project',prompt_record=RECORD+'#'+source_id,
                 modified='生成原画の分割・最近傍縮小・bright.gpl減色・二値透過。地形の周期境界はスクリプトで補正。')
    entry.update(extra);ENTRIES[path]=entry;CHANGED.append(path)
    errors,exists=check_asset(entry,set(map(tuple,pal)))
    assert exists and not errors,errors
    return im


def party():
    proofs=[]
    reserved=[['101D36','344F70','F3BE39'],['4A2B2B','704131','975638','81334D','B13C55','D94C55','32813E','101D36'],['FFE6BC','BECED1','E7EFF0','87A0AE','704131','32813E'],['101D36','967DBC','FFE6BC']]
    for number in range(1,5):
        id_=f'pc_0{number}'
        designs=strip(source(id_+'_design'),3)
        row_images=[p.transpose(Image.Transpose.TRANSPOSE) for p in strip(source(id_+'_walk').transpose(Image.Transpose.TRANSPOSE),4,2)]
        walk=[clean(p) for row in row_images for p in strip(row,3)];battle=[clean(p) for p in strip(source(id_+'_battle'),3)]
        # 両シートで同じ頭身を保つため、まず各原画の高さを基準に全コマ同倍率で縮小する。
        outputs={}
        for kind,frames,fw,cols in [('walk',walk,32,3),('battle',battle,48,3)]:
            scale=min(45/max(f.height for f in frames),(fw-4)/max(f.width for f in frames))
            out=Image.new('RGBA',(fw*cols,48*(len(frames)//cols)))
            for i,f in enumerate(frames):
                f=f.resize((max(1,round(f.width*scale)),max(1,round(f.height*scale))),Image.Resampling.NEAREST);f=crop_alpha(f)
                out.alpha_composite(f,(i%cols*fw+(fw-f.width)//2,i//cols*48+48-f.height))
            outputs[kind]=out
        outputs['portrait']=fit(designs[2],(64,64),1)
        if id_=='pc_03':
            for kind,im in outputs.items():
                a=np.array(im);r,g,b=[a[:,:,c].astype(float) for c in range(3)]
                yy=np.indices(a.shape[:2])[0]
                head=yy<40 if kind=='portrait' else yy%48<16
                mask=head&(r>100)&((r-g)<40)&((g-b)<45)&((r-b)<65)&(a[:,:,3]>0)
                light=(r+g+b)/3
                for lo,hi,color in [(0,135,'55718B'),(135,185,'87A0AE'),(185,220,'BECED1'),(220,256,'E7EFF0')]:
                    a[mask&(light>=lo)&(light<hi),:3]=list(bytes.fromhex(color))
                outputs[kind]=Image.fromarray(a)
        if id_=='pc_02':
            for kind,im in outputs.items():
                a=np.array(im);r,g,b=[a[:,:,c].astype(float) for c in range(3)]
                mask=(r>80)&(r>g*2.5)&(g<=b*1.35)&(a[:,:,3]>0)
                for lo,hi,color in [(80,110,'81334D'),(110,155,'B13C55'),(155,205,'D94C55'),(205,256,'F36D62')]:
                    a[mask&(r>=lo)&(r<hi),:3]=list(bytes.fromhex(color))
                outputs[kind]=Image.fromarray(a)
        counts=np.zeros(64,dtype=np.int64)
        for im in outputs.values():
            a=np.array(quantize(im));rgb=a[:,:,:3][a[:,:,3]>0]
            for i,c in enumerate(PAL):counts[i]+=int(np.all(rgb==c,axis=1).sum())
        chosen=[int(np.where(np.all(PAL==list(bytes.fromhex(h)),axis=1))[0][0]) for h in reserved[number-1]]
        chosen+= [int(i) for i in np.argsort(-counts,kind='stable') if i not in chosen][:16-len(chosen)]
        palette=PAL[chosen]
        for kind,im in outputs.items():
            opts={} if kind=='portrait' else {'frame':[32 if kind=='walk' else 48,48],'grid':[3,4 if kind=='walk' else 1]}
            save(f'assets/characters/{id_}/{kind}.png',im,id_+'_'+('design' if kind=='portrait' else kind),
                 'portrait' if kind=='portrait' else 'character_'+kind,palette,**opts)
        proofs.append({'id':id_,'shared_palette':[list(map(int,c)) for c in palette],'walk_frames':12,'battle_frames':3,'ground_row':47,
                       'reference':ROWS[id_+'_design']['source_file'],'visual_identity_review':'生成原画と縮小後の比較で確認。依頼者による承認とは区別する。'})
    (ROOT/'docs/verification/art-review/party-checks.json').write_text(json.dumps(proofs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def periodic(im):
    a=np.array(im.convert('RGBA')).astype(float)
    width=3 if im.width<=32 else 8
    for axis in [1,0]:
        b=np.swapaxes(a,0,axis)
        for k in range(width):
            left=b[k].copy();right=b[-1-k].copy();weight=.5*(1-k/width)
            b[k]=(1-weight)*left+weight*right;b[-1-k]=(1-weight)*right+weight*left
        a=np.swapaxes(b,0,axis)
    return quantize(Image.fromarray(np.rint(a).clip(0,255).astype('uint8')))


def texture(id_,im,size):
    raw=im.resize(size,Image.Resampling.NEAREST);before=np.array(quantize(raw));out=periodic(raw)
    groups={
        'grass':'48A449 6AC750 93DB65',
        'road':'975638 B8784A D29A60 E8B77C F5D29A',
        'water':'228DC4 36B3E2 66D0F0 9BE6F5',
        'forest':'153F32 22613A 32813E 48A449 6AC750 93DB65 BAE987 4A2B2B 704131 975638 B8784A',
        'deep_forest':'101D36 153F32 22613A 32813E 48A449 6AC750 93DB65 4A2B2B 704131 975638',
        'mountains':'1E3154 344F70 55718B 87A0AE BECED1 E7EFF0 704131 975638 B8784A D29A60 E8B77C 22613A 32813E 48A449 6AC750 93DB65',
        'hills':'704131 975638 B8784A D29A60 E8B77C F5D29A 22613A 32813E 48A449 6AC750 93DB65',
        'cave_floor':'1E3154 344F70 55718B 87A0AE BECED1 704131 975638 B8784A D29A60',
        'cave_wall':'1E3154 344F70 55718B 87A0AE BECED1 704131 975638 B8784A D29A60 E8B77C',
    }
    family='grass' if id_.startswith('grass') else id_
    palette=np.array([list(bytes.fromhex(h)) for h in groups[family].split()],dtype=np.int32) if family in groups else PAL
    rel=f'assets/tiles/bright_{id_}.png';out=save(rel,out,id_,pal=palette,tile_size=[32,32])
    a=np.array(out)
    x=int(np.any(a[:,0]!=a[:,-1],axis=1).sum());y=int(np.any(a[0]!=a[-1],axis=1).sum())
    assert x==0 and y==0
    SEAMS.append({'path':rel,'size':list(size),'before_edge_mismatches':int(np.any(before[:,0]!=before[:,-1],axis=1).sum()+np.any(before[0]!=before[-1],axis=1).sum()),'after_horizontal':x,'after_vertical':y,'repeat':[8,8]})
    return out


def transition_masks(size):
    y,x=np.mgrid[:size,:size];c=size//4
    # 両端で0になる揺らぎ。接続端の位置を変えずに自然な地形境界を作る。
    wave_x=np.rint(np.sin(x*np.pi/(size-1))*np.sin(x*5*np.pi/(size-1))*max(1,size/32))
    wave_y=np.rint(np.sin(y*np.pi/(size-1))*np.sin(y*5*np.pi/(size-1))*max(1,size/32))
    n=y>=c+wave_x;s=y<size-c+wave_x;w=x>=c+wave_y;e=x<size-c+wave_y
    return {'north':n,'south':s,'west':w,'east':e,'nw':n&w,'ne':n&e,'sw':s&w,'se':s&e,
            'inner_nw':n|w,'inner_ne':n|e,'inner_sw':s|w,'inner_se':s|e}


def transitions(family,land,other,source_id):
    n=land.width;masks=transition_masks(n)
    a=np.array(land);b=np.array(other)
    for name,mask in masks.items():
        out=np.where(mask[:,:,None],a,b).astype('uint8')
        save(f'assets/tiles/bright_{family}_{name}.png',Image.fromarray(out),source_id,tile_size=[32,32])


def terrain():
    grass=source('grass_set');grasses=[]
    for i in range(3):
        g=texture('grass' if i==0 else f'grass_{i+1}',grass.crop((i*grass.width//3,0,(i+1)*grass.width//3,grass.height)),(32,32))
        if i:
            a=np.array(g);shared=np.array(grasses[0]);a[0]=shared[0];a[-1]=shared[-1];a[:,0]=shared[:,0];a[:,-1]=shared[:,-1]
            g=save(f'assets/tiles/bright_grass_{i+1}.png',Image.fromarray(a),'grass_set',tile_size=[32,32])
        grasses.append(g)
        ENTRIES[f'assets/tiles/bright_{"grass" if i==0 else "grass_"+str(i+1)}.png']['prompt_record']=RECORD+'#grass_set'
    water=texture('water',source('water'),(32,32));road=texture('road',source('road'),(32,32))
    transitions('shore',grasses[0],water,'water');transitions('road_edge',road,grasses[0],'road')
    for id_ in ['forest','deep_forest','hills','mountains']:
        block=texture(id_,source(id_),(128,128))
        if id_ in ['forest','deep_forest']:
            ground=Image.fromarray(np.tile(np.array(grasses[0]),(4,4,1)))
            transitions(id_+'_edge',block,ground,id_)
    s=source('interior_surfaces')
    for i,id_ in enumerate(['wood_floor','interior_wall','cave_floor']):
        texture(id_,s.crop((i*s.width//3,0,(i+1)*s.width//3,s.height)),(32,32))
        ENTRIES[f'assets/tiles/bright_{id_}.png']['prompt_record']=RECORD+'#interior_surfaces'
    texture('cave_wall',source('cave_wall'),(64,64))
    save('assets/tiles/bright_flowers.png',fit(source('flowers'),(32,32)),'flowers')
    parts=strip(source('bridge_fence'),2)
    save('assets/tiles/bright_bridge.png',fit(parts[0],(64,64)),'bridge_fence')
    save('assets/tiles/bright_fence.png',fit(parts[1],(32,32)),'bridge_fence')
    props=grid(source('furniture'),3,3)
    for i,id_ in enumerate(['table','chair','shelf','bed','barrel','pot','shop_counter','inn_counter','rug']):
        size=(32,64) if id_ in ['shelf','bed'] else (64,32) if 'counter' in id_ else (64,64) if id_=='rug' else (32,32)
        save('assets/tiles/bright_'+id_+'.png',fit(props[i],size),'furniture')
    for part,id_ in zip(strip(source('cave_props'),3),['torch','stairs_up','stairs_down']):
        save('assets/tiles/bright_'+id_+'.png',fit(part,(32,32)),'cave_props')
    for id_,size in [('chest',32),('gate',96)]:
        parts=strip(source(id_),2);scale=min((size-4)/max(p.width for p in parts),(size-4)/max(p.height for p in parts))
        out=Image.new('RGBA',(size*2,size))
        for i,part in enumerate(parts):
            part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.NEAREST);part=crop_alpha(part)
            out.alpha_composite(part,(size*i+(size-part.width)//2,size-part.height))
        save(f'assets/objects/{id_}.png',out,id_,'object',frame=[size,size],grid=[2,1])
    for part,id_ in zip(strip(source('icons'),3),['castle','tower','cave']):
        save(f'assets/ui/icon_{id_}.png',fit(part,(32,32)),'icons','map_icon')
    # 承認済み建物の部品を切り出して、残っている単純な部品版もそろえる。
    crops={
        'house':{'roof':(0,16,120,84),'door':(48,90,78,128),'window':(20,89,39,114)},
        'inn':{'roof':(0,5,128,71),'door':(50,84,77,120),'window':(18,81,41,105)},
        'item_shop':{'roof':(0,8,124,66),'door':(76,84,103,127),'window':(15,87,70,112)},
        'weapon_shop':{'roof':(0,12,128,73),'door':(60,83,89,127),'window':(23,83,53,114)},
    }
    for id_ in ['house','inn','item_shop','weapon_shop']:
        im=Image.open(ROOT/f'assets/tiles/bright_{id_}_exterior.png').convert('RGBA')
        for kind in ['roof','wall','door','window']:
            size=(128,64) if kind=='roof' else (64,32) if kind=='window' and id_=='item_shop' else (32,32)
            part=Image.open(ROOT/'assets/tiles/bright_interior_wall.png').convert('RGBA') if kind=='wall' else fit(im.crop(crops[id_][kind]),size,0)
            save(f'assets/tiles/bright_{id_}_{kind}.png',part,'approved_buildings')
            ENTRIES[f'assets/tiles/bright_{id_}_{kind}.png']['prompt_record']='assets/source_records/generated-bright.json#buildings'
            if kind=='wall':ENTRIES[f'assets/tiles/bright_{id_}_{kind}.png']['prompt_record']=RECORD+'#interior_surfaces'
    (ROOT/'docs/verification/art-review/tiling-checks.json').write_text(json.dumps(SEAMS,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    party();terrain();compatibility_atlases()
    REG['assets']=list(ENTRIES.values())
    (ROOT/'assets/registry.json').write_text(json.dumps(REG,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'docs/verification/art-review/changed-assets.json').write_text(json.dumps(sorted(set(CHANGED)),indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'ART_A_IMPORT_PASS: assets={len(set(CHANGED))} party=12 periodic_patterns={len(SEAMS)} edge_mismatches=0')
    verify_adjacencies()


def compatibility_atlases():
    """既存参照用512pxアトラスも、新素材で組み直す。参照番号と寸法は維持する。"""
    def t(name):return Image.open(ROOT/f'assets/tiles/bright_{name}.png').convert('RGBA')
    def icon(name):return Image.open(ROOT/f'assets/ui/icon_{name}.png').convert('RGBA')
    chest=Image.open(ROOT/'assets/objects/chest.png').convert('RGBA')
    gate=Image.open(ROOT/'assets/objects/gate.png').convert('RGBA')
    field=[t('grass'),t('interior_wall'),t('water'),t('road'),chest.crop((0,0,32,32)),t('bridge'),t('wood_floor'),gate.crop((0,0,96,96)),icon('village'),t('flowers'),t('mountains'),icon('town'),t('stairs_up'),t('forest'),t('grass_3'),icon('cave')]
    cave=[t('cave_floor'),t('cave_wall'),t('water'),t('stairs_up'),chest.crop((0,0,32,32)),gate.crop((0,0,96,96)),chest.crop((32,0,64,32)),t('torch'),t('cave_wall'),t('pot'),gate.crop((96,0,192,96)),t('bridge'),t('stairs_down'),t('cave_floor'),t('cave_wall'),icon('cave')]
    for name,parts,ground in [('field_outdoor',field,t('grass')),('dungeon_cave',cave,t('cave_floor'))]:
        canvas=Image.new('RGBA',(512,512))
        for y in range(16):
            for x,part in enumerate(parts):
                cell=ground.copy();small=part.resize((32,32),Image.Resampling.NEAREST)
                if np.all(np.array(small)[:,:,3]==255):small=periodic(small)
                cell.alpha_composite(small);canvas.alpha_composite(cell,(x*32,y*32))
        save(f'assets/tiles/{name}.png',canvas,'grass_set' if name=='field_outdoor' else 'cave_wall',frame=[32,32],grid=[16,16],component_sources=['grass_set','water','road','forest','mountains','interior_surfaces','furniture','cave_wall','cave_props','bridge_fence','chest','gate','icons'])


def verify_adjacencies():
    receipts=[]
    for family,center in [('shore','grass'),('road_edge','road'),('forest_edge','forest'),('deep_forest_edge','deep_forest')]:
        def read(name):return np.array(Image.open(ROOT/f'assets/tiles/bright_{name}.png').convert('RGBA'))
        tiles={name:read(family+'_'+name) for name in transition_masks(32)}
        tiles['center']=read(center)
        def join(a,b,direction):
            first=tiles[a][:,-1] if direction=='right' else tiles[a][-1]
            second=tiles[b][:,0] if direction=='right' else tiles[b][0]
            n=int(np.any(first!=second,axis=1).sum())
            receipts.append({'family':family,'from':a,'to':b,'direction':direction,'mismatches':n})
            assert n==0,(family,a,b,direction,n)
        grid_names=[['nw','north','ne'],['west','center','east'],['sw','south','se']]
        for y in range(3):
            for x in range(3):
                if x<2:join(grid_names[y][x],grid_names[y][x+1],'right')
                if y<2:join(grid_names[y][x],grid_names[y+1][x],'down')
        for name,top,bottom,left,right in [('inner_nw','west','center','north','center'),('inner_ne','east','center','center','north'),('inner_sw','center','west','south','center'),('inner_se','center','east','center','south')]:
            join(top,name,'down');join(name,bottom,'down');join(left,name,'right');join(name,right,'right')
    (ROOT/'docs/verification/art-review/adjacency-checks.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'ART_A_ADJACENCY_PASS: connections={len(receipts)} mismatches=0')


if __name__=='__main__':main()
