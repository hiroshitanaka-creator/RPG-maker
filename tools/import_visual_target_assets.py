#!/usr/bin/env python3
"""今回の生成原画だけを分割・減色する。目標JPEGの絵は素材へ使用しない。"""
from pathlib import Path
import json
import hashlib
import shutil
from collections import deque
import numpy as np
from PIL import Image
from validate_assets import load_palette, check_asset

ROOT=Path(__file__).resolve().parents[1]
RECORD='assets/source_records/visual-target-generation.json'
PAL=np.array(sorted(load_palette(ROOT/'assets/palette/natural.gpl')),dtype=np.int32)
OUT=ROOT/'docs/verification/art-review-2'

def quantize(im):
    a=np.array(im.convert('RGBA'));opaque=a[:,:,3]>=245
    values,inv=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
    chosen=((values.astype(np.int32)[:,None,:]-PAL[None,:,:])**2).sum(axis=2).argmin(axis=1)
    a[:,:,:3]=PAL[chosen[inv]].reshape(a.shape[:2]+(3,))
    a[:,:,3]=opaque*255;a[~opaque,:3]=0
    return Image.fromarray(a)

def crop(im):
    im=im.copy();im.putalpha(im.getchannel('A').point(lambda a:255 if a>=245 else 0))
    box=im.getchannel('A').getbbox()
    if box is None:raise ValueError('空の生成原画')
    return im.crop(box)

def remove_black_border(im):
    """透過指定がRGB黒背景で返った原画だけ、外周へ連なる黒を除く。"""
    a=np.array(im)
    if np.any(a[:,:,3]<255):return im
    candidate=a[:,:,:3].max(axis=2)<=12
    seen=np.zeros(candidate.shape,bool);h,w=candidate.shape;q=deque()
    for x,y in [(x,0) for x in range(w)]+[(x,h-1) for x in range(w)]+[(0,y) for y in range(h)]+[(w-1,y) for y in range(h)]:
        if candidate[y,x] and not seen[y,x]:seen[y,x]=True;q.append((x,y))
    while q:
        x,y=q.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=xx<w and 0<=yy<h and candidate[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((xx,yy))
    a[seen]=0
    return Image.fromarray(a)

def fit(im,size,pad=1):
    im=crop(im);scale=min((size[0]-2*pad)/im.width,(size[1]-2*pad)/im.height)
    im=crop(im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST))
    out=Image.new('RGBA',size);out.alpha_composite(im,((size[0]-im.width)//2,size[1]-pad-im.height))
    return out

def cuts(profile,count):
    bounds=[0];n=len(profile)
    for i in range(1,count):
        center=round(i*n/count);radius=round(n/count*.16)
        candidates=np.arange(center-radius,center+radius+1)
        costs=profile[candidates]*1000+np.abs(candidates-center)
        at=int(candidates[costs.argmin()])
        if profile[at]>max(4,profile.max()*.015):
            raise ValueError(f'生成原画の透明な境界を確定できない: {i}/{count}={profile[at]}')
        bounds.append(at)
    return bounds+[n]

def split(im,cols,rows):
    a=np.array(im.getchannel('A'))>=245;ys=cuts(a.sum(axis=1),rows);parts=[]
    for y,y2 in zip(ys,ys[1:]):
        xs=cuts(a[y:y2].sum(axis=0),cols)
        parts += [im.crop((x,y,x2,y2)) for x,x2 in zip(xs,xs[1:])]
    return parts

def periodic(im):
    a=np.array(im.convert('RGBA')).astype(float)
    for axis in (0,1):
        b=np.swapaxes(a,0,axis)
        for k in range(3):
            left=b[k].copy();right=b[-1-k].copy();w=.5*(1-k/3)
            b[k]=(1-w)*left+w*right;b[-1-k]=(1-w)*right+w*left
        a=np.swapaxes(b,0,axis)
    a[:,:,3]=255
    return quantize(Image.fromarray(np.rint(a).clip(0,255).astype('uint8')))

class Importer:
    def __init__(self):
        self.rows=json.loads((ROOT/RECORD).read_text(encoding='utf-8'))
        self.sources={}
        for row in self.rows:
            rel=f"assets/_incoming/visual-targets/{row['id']}.png"
            dest=ROOT/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():shutil.copyfile(row['path'],dest)
            row['source_file']=rel;row['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
            im=Image.open(dest).convert('RGBA')
            self.sources[row['id']]=im if row['id'] in ('surfaces','wall_surfaces') else remove_black_border(im)
        (ROOT/RECORD).write_text(json.dumps(self.rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        self.registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
        self.entries={e['path']:e for e in self.registry['assets']};self.added=[];self.seams=[]

    def save(self,id_,im,source,kind='object',**extra):
        rel=f'assets/{"tiles" if kind=="tileset" else "objects"}/natural_{id_}.png'
        im=quantize(im);im.save(ROOT/rel)
        entry=dict(path=rel,kind=kind,size=list(im.size),max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='imagegen + Python/Pillow',generated_at='2026-09-26',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',prompt_record=RECORD+'#'+source,modified='新規生成原画の透明境界で分割、最近傍縮小、natural.gpl減色、アルファ245を境に二値化。目標画像の絵は不使用。')
        entry.update(extra);self.entries[rel]=entry;self.added.append(rel)
        errors,exists=check_asset(entry,set(map(tuple,PAL)));assert exists and not errors,errors
        return im

    def props(self):
        singles={'farm_house_a':(224,192),'farm_house_b':(224,192),'town_house_red':(192,192),'town_house_blue':(192,192),'church':(224,256),'castle':(384,320),'manor':(224,192),'bridge':(96,128)}
        for id_,size in singles.items():self.save(id_,fit(self.sources[id_],size),id_)
        groups={
            'farm_props':(3,3,[('cabbage',(32,32)),('carrots',(32,32)),('wheat',(32,64)),('haystack',(64,64)),('well',(96,96)),('barrels',(64,64)),('crates',(64,64)),('flowerbed',(96,64)),('shrine',(64,96))]),
            'town_props':(3,2,[('fountain',(128,128)),('cart',(96,64)),('bench',(64,32)),('sign_item',(32,32)),('sign_inn',(32,32)),('sign_weapon',(32,32))]),
            'market':(2,2,[(f'market_{color}',(96,96)) for color in ('blue','purple','red','ochre')]),
            'wall_kit':(3,2,[('wall_horizontal',(96,64)),('wall_vertical',(64,96)),('wall_corner',(64,64)),('watchtower',(96,128)),('gate_closed',(128,128)),('gate_open',(128,128))]),
            'fence_ortho':(2,2,[('fence_horizontal',(64,32)),('fence_vertical',(32,64)),('fence_corner',(32,32)),('fence_gap',(64,32))]),
            'dungeon_props':(3,2,[('door_closed',(64,64)),('door_open',(64,64)),('barred_gate',(64,64)),('torch',(32,64)),('stairs_up',(64,64)),('stairs_down',(64,64))]),
            'cave_props':(3,2,[('stalagmites',(64,64)),('mushrooms',(32,32)),('campfire',(64,64)),('mine_timbers',(128,96)),('rope_bridge',(128,64)),('rubble',(64,64))]),
            'ruins_props':(3,2,[('pillar',(32,96)),('broken_pillar',(64,64)),('stele',(64,96)),('pool',(128,96)),('overgrown_grass',(64,64)),('broken_statue',(64,96))]),
            'scatter':(3,2,[(id_,(32,32)) for id_ in ('tufts','pebbles','flowers_white','flowers_yellow','flowers_pink','leaves')]),
            'chicken_pattern':(2,1,[('chicken',(32,32)),('floor_pattern',(96,96))]),
        }
        for source,(cols,rows,defs) in groups.items():
            parts=split(self.sources[source],cols,rows)
            for part,(id_,size) in zip(parts,defs):
                normalized=fit(part,size)
                if id_ in ('wall_horizontal','wall_vertical','fence_horizontal'):
                    normalized=crop(part).resize(size,Image.Resampling.NEAREST)
                if id_=='fence_vertical':
                    normalized=crop(part).resize(size,Image.Resampling.NEAREST)
                self.save(id_,normalized,source)
        # 開閉画像は同一フレーム寸法・接地行の横並びにも提供する。
        for id_,size,source in [('gate',128,'wall_kit'),('door',64,'dungeon_props')]:
            out=Image.new('RGBA',(size*2,size))
            for i,state in enumerate(('closed','open')):
                im=crop(Image.open(ROOT/f'assets/objects/natural_{id_}_{state}.png').convert('RGBA'))
                out.alpha_composite(im,(i*size+(size-im.width)//2,size-im.height))
            self.save(id_,out,source,frame=[size,size],grid=[2,1])

    def surfaces(self):
        sets={'surfaces':(3,3,['grass','grass_2','grass_3','dirt','cobble','stone_floor','cave_floor','cave_floor_2','moss_floor']),
              'wall_surfaces':(2,2,['stone_wall','cave_rock','moss_wall','water'])}
        for source,(cols,rows,names) in sets.items():
            im=self.sources[source]
            for i,id_ in enumerate(names):
                x=i%cols;y=i//cols
                part=im.crop((round(x*im.width/cols),round(y*im.height/rows),round((x+1)*im.width/cols),round((y+1)*im.height/rows)))
                # 128pxに模様を保持し、32pxセル16枚で繰り返す。
                result=periodic(part.resize((128,128),Image.Resampling.NEAREST))
                self.save(id_,result,source,'tileset',tile_size=[32,32],repeat_cells=[4,4])
                a=np.array(result);n=int(np.any(a[:,0]!=a[:,-1],axis=1).sum()+np.any(a[0]!=a[-1],axis=1).sum());assert n==0
                self.seams.append({'path':f'assets/tiles/natural_{id_}.png','opposite_edge_mismatches':n})
        # 全草地変種の外縁を共有し、変種の境界にも色の継ぎ目を作らない。
        grass=np.array(Image.open(ROOT/'assets/tiles/natural_grass.png'))
        for id_ in ('grass_2','grass_3'):
            p=ROOT/f'assets/tiles/natural_{id_}.png';a=np.array(Image.open(p));a[0]=grass[0];a[-1]=grass[-1];a[:,0]=grass[:,0];a[:,-1]=grass[:,-1];Image.fromarray(a).save(p)
        patch=np.array(Image.open(ROOT/'assets/tiles/natural_dirt.png').convert('RGBA'))[32:64,32:64].copy()
        yy,xx=np.mgrid[:32,:32];inside=((xx-15.5)/13)**2+((yy-16)/10)**2<1+.12*np.sin(xx*.7)
        patch[~inside]=0
        self.save('dirt_patch',Image.fromarray(patch),'surfaces')

    def finish(self):
        self.registry['assets']=list(self.entries.values())
        (ROOT/'assets/registry.json').write_text(json.dumps(self.registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        (OUT/'new-assets.json').write_text(json.dumps(self.added,indent=2)+'\n',encoding='utf-8',newline='\n')
        (OUT/'surface-seams.json').write_text(json.dumps(self.seams,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(f'NATURAL_IMPORT_PASS: assets={len(self.added)} periodic_surfaces={len(self.seams)} edge_mismatches=0')

def main():
    importer=Importer();importer.props();importer.surfaces();importer.finish()

if __name__=='__main__':main()
