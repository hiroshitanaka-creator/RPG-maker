"""魔物化の戦闘素材用。明部と目の光を分けて既存パレットへ対応する。"""
import numpy as np
from scipy import ndimage
from PIL import Image

BATTLE_COLORS=['0B1824','153550','254A63','215380','336C95','3174AC','5D98C4','728593','BDC7D3','EEF6EB','3A2317','68422F','9A6048','CE9F54','D7B778','53335F','D6AA61','EDBB5B','F6D275','E9E7CB']
# 採用済み96pxコマ上の目・花の中心の範囲。口・爪・くちばしは含めない。
KAINA_EYE_ZONES={
 'slime':[(16,34,39,54),(14,33,34,52),(19,50,38,64)],
 'beast':[(28,27,35,33),(34,33,41,39),(55,20,64,28)],
 'undead':[(24,15,43,31),(25,18,44,33),(48,10,66,26)],
 'plant':[(24,26,67,41),(33,29,72,46),(36,19,78,39)],
 'shell':[(21,51,44,66),(35,51,56,65),None],
 'spirit':[(15,27,46,48),(23,42,46,56),(20,22,46,38)],
 'dragon':[(10,17,33,27),(12,23,33,33),(27,11,52,24)],
 'bird':[(21,49,28,54),(31,53,37,58),(29,47,35,51)],
}

def recolor(frame, form, pose, eye_zones=KAINA_EYE_ZONES):
    """形・アルファを維持し、記録した範囲内の暖色だけを発光色へ対応する。"""
    a=np.array(frame);rgb=a[:,:,:3].astype(np.float64);opaque=a[:,:,3]>0
    palette=np.array([[int(c[i:i+2],16) for i in (0,2,4)] for c in BATTLE_COLORS])
    gamma=0.64 if form=='plant' else 0.78
    adjusted=255*(rgb/255)**gamma
    # 最も暗い線は保ち、体の中間色と明部の差を残す。
    adjusted=np.where((rgb.max(2)<18)[:,:,None],rgb,adjusted)
    nearest=((adjusted[:,:,None,:]-palette[None,None,:,:])**2).sum(3).argmin(2)
    result=palette[nearest].astype(np.uint8)
    zone=eye_zones[form][pose];eye=np.zeros(opaque.shape,dtype=bool)
    if zone is not None:
        x1,y1,x2,y2=zone;eye[y1:y2,x1:x2]=True
        eye&=opaque&(rgb[:,:,0]>rgb[:,:,1]*1.08)&(rgb[:,:,1]>rgb[:,:,2]*1.2)&(rgb[:,:,0]>45)
    groups,count=ndimage.label(eye,structure=np.ones((3,3)))
    cores=[]
    for label in range(1,count+1):
        mask=groups==label;coords=np.argwhere(mask)
        if len(coords)<1:continue
        light=(rgb[mask]*[.2126,.7152,.0722]).sum(1)
        # 茶色の虹彩を残しつつ、中心を明るい黄土色、光点をパレット最明色へ。
        result[mask]=[206,159,84]
        upper=coords[light>=np.quantile(light,.50)]
        result[upper[:,0],upper[:,1]]=[237,187,91]
        upper=coords[light>=np.quantile(light,.80)]
        result[upper[:,0],upper[:,1]]=[246,210,117]
        # 72pxへの最近傍縮小で残る画素を光点に選ぶ。
        sample_axis=np.array(Image.fromarray(np.arange(96,dtype=np.int32)[None,:]).resize((72,1),Image.Resampling.NEAREST))[0]
        sampled=set(sample_axis)&set(np.floor((np.arange(72)+.5)*96/72).astype(int))
        survivors=[i for i,(y,x) in enumerate(coords) if y in sampled and x in sampled]
        if survivors:
            best=max(survivors,key=lambda i:light[i]);y,x=coords[best]
        else:
            y,x=coords[light.argmax()]
            candidates=[(yy,xx) for yy in range(max(y-1,zone[1]),min(y+2,zone[3])) for xx in range(max(x-1,zone[0]),min(x+2,zone[2])) if yy in sampled and xx in sampled and opaque[yy,xx]]
            if candidates:y,x=min(candidates,key=lambda p:(p[0]-y)**2+(p[1]-x)**2)
        result[y,x]=[238,246,235];cores.append([int(x),int(y)])
    a[:,:,:3]=result;a[~opaque]=0
    return a,dict(gamma=gamma,eye_zone=zone,eye_pixels=int(eye.sum()),light_cores=cores,closed_eye=(zone is None))
