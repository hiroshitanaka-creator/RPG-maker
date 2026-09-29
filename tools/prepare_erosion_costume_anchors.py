"""衣装ごとの顔と両腕の位置候補を作り、確認用画像へ部位を示す。"""
import json
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/erosion-costumes'
JOBS=['warrior','martial_artist','priest','mage','thief','hunter','apothecary','bard','knight','sage','swordsman','shaman']
NAMES=['戦士','武闘家','僧侶','魔法使い','盗賊','狩人','薬師','吟遊詩人','騎士','賢者','剣士','祈祷師']

def landmarks(frame,kind,pose,facing,job,actor):
    a=np.array(frame);rgb=a[:,:,:3].astype(float);mask=a[:,:,3]>0;h,w=mask.shape
    box=frame.getbbox();x1,y1,x2,y2=box;scale=w/96 if kind=='battle' else .43
    warm=mask&(rgb[:,:,0]>=180)&(rgb[:,:,1]>=100)&(rgb[:,:,0]>rgb[:,:,1]*1.1)&(rgb[:,:,0]<rgb[:,:,1]*1.35)&(rgb[:,:,2]<rgb[:,:,0]*.8)
    labels,count=ndimage.label(warm)
    candidates=[]
    for k,sl in enumerate(ndimage.find_objects(labels),1):
        if sl is None:continue
        yy,xx=sl
        # 肌が首・胸まで連結する衣装では、上側の顔の高さだけを位置決めに使う。
        yy=slice(yy.start,min(yy.stop,yy.start+max(3,round(19*scale))))
        area=int((labels[yy,xx]==k).sum());bw=xx.stop-xx.start;bh=yy.stop-yy.start
        cx=(xx.start+xx.stop-1)/2;cy=(yy.start+yy.stop-1)/2
        if area<max(2,8*scale*scale) or bw<max(2,6*scale) or bh<max(2,6*scale) or bw>26*scale or bw>bh*2.6:continue
        if not(y1+(y2-y1)*.06<=cy<=y1+(y2-y1)*.55):continue
        if not(x1+(x2-x1)*.18<=cx<=x1+(x2-x1)*.83):continue
        fraction=.38 if job=='mage' else .33 if job in ['bard','shaman'] else .26
        target=(w*.49,y1+(y2-y1)*fraction)
        score=min(area,65*scale*scale)*.2-(cx-target[0])**2*.3-(cy-target[1])**2*.7
        candidates.append((score,[xx.start,yy.start,xx.stop,yy.stop]))
    if candidates and facing!=3:
        head=max(candidates)[1];cx=(head[0]+head[2]-1)/2;bottom=head[3]-1
    else:
        cx=w*.5;bottom=(y1+(y2-y1)*.38) if kind=='battle' else (20 if facing==3 else 19)
        head=[round(cx-5*scale),round(bottom-9*scale),round(cx+5*scale),round(bottom)]
    overrides={
      ('pc_01','martial_artist',1):[36,24,54,41],
      ('pc_02','martial_artist',1):[33,27,50,44],
      ('pc_04','martial_artist',1):[34,23,53,39],
      ('pc_02','apothecary',0):[33,29,51,47],
      ('pc_02','apothecary',1):[35,29,54,47],
    }
    manual=kind=='battle' and (actor,job,pose) in overrides
    if manual:
        head=overrides[actor,job,pose];cx=(head[0]+head[2]-1)/2;bottom=head[3]-1
    if kind=='walk':
        # 小さい歩行は3方向の向きに合わせ、顔の手前側を選ぶ。
        left=(cx-6,bottom+11);right=(cx+6,bottom+11)
        if facing==1:left=(cx+3,bottom+12);right=(cx-2,bottom+11)
        if facing==2:left=(cx-3,bottom+12);right=(cx+2,bottom+11)
    else:
        left=(cx-17,bottom+(10 if pose==1 else 24));right=(cx+16,bottom+20)
        profiles={
          'martial_artist':[((-11,10),(18,16)),((-27,3),(22,13)),((-22,8),(10,12))],
          'hunter':[((-13,18),(8,18)),((-28,5),(11,6)),((-11,17),(8,15))],
          'apothecary':[((-11,13),(24,26)),((-26,7),(26,20)),((-3,13),(9,14))],
          'bard':[((-8,18),(9,17)),((-12,16),(8,13)),((-7,16),(9,17))],
          'sage':[((-10,17),(12,17)),((-25,5),(10,18)),((-7,14),(8,17))],
          'mage':[((-19,12),(19,14)),((-24,2),(21,7)),((-24,-3),(12,12))],
          'priest':[((-19,16),(19,24)),((-28,2),(17,14)),((-23,1),(17,20))],
          'shaman':[((-14,13),(16,21)),((-27,5),(8,15)),((-10,12),(9,14))],
        }
        if job in profiles:
            l,r=profiles[job][pose];left=(cx+l[0],bottom+l[1]);right=(cx+r[0],bottom+r[1])
        # 手の肌色が読めるときはそれを使い、袖・鎧の場合は同じ腕の位置を基準にする。
        for side,target in [('left',left),('right',right)]:
            valid=[]
            for k,sl in enumerate(ndimage.find_objects(labels),1):
                if sl is None:continue
                yy,xx=sl;area=int((labels[sl]==k).sum());px=(xx.start+xx.stop-1)/2;py=(yy.start+yy.stop-1)/2
                if not(2<=area<=70 and bottom-10<=py<=min(h-8,bottom+32)):continue
                if (side=='left' and px>cx-4) or (side=='right' and px<cx+4):continue
                valid.append(((px-target[0])**2+(py-target[1])**2,(px,py)))
            if valid and min(valid)[0]<=64:
                point=min(valid)[1]
                if side=='left':left=point
                else:right=point
    def clamp(point):return [int(np.clip(round(point[0]),1,w-2)),int(np.clip(round(point[1]),1,h-2))]
    def arm(hand,side):
        shoulder_width=6 if kind=='battle' and job in ['apothecary','bard','sage'] and pose==2 else (10 if kind=='battle' else 4)
        shoulder=(cx+side*shoulder_width,bottom+(5 if kind=='battle' else 3))
        elbow=((shoulder[0]+hand[0])/2+side*(2 if kind=='battle' else 1),(shoulder[1]+hand[1])/2)
        return [clamp(shoulder),clamp(elbow),clamp((elbow[0]-side*(2 if kind=='battle' else 1),elbow[1]+2)),clamp(hand)]
    cheek=[] if facing==3 else [clamp((cx-2*scale,bottom-3*scale)),clamp((cx+scale,bottom-scale)),clamp((cx+4*scale,bottom-3*scale))]
    neck=[clamp((cx-3*scale,bottom+2*scale)),clamp((cx,bottom+5*scale)),clamp((cx+4*scale,bottom+2*scale))]
    result=dict(head_box=head,cheek=cheek,arm=arm(left,-1),other_arm=arm(right,1),neck=neck,face_detected=bool(candidates and facing!=3),manual_head_adjustment=manual)
    arm_overrides={
      ('pc_02','martial_artist',1):{'arm':[[41,41],[30,39],[26,40],[11,37]]},
      ('pc_01','martial_artist',2):{'other_arm':[[63,39],[61,44],[58,44],[55,42]]},
      ('pc_03','martial_artist',2):{'other_arm':[[64,38],[65,42],[62,46],[57,43]]},
    }
    if kind=='battle' and (actor,job,pose) in arm_overrides:
        result.update(arm_overrides[actor,job,pose]);result['manual_arm_adjustment']=True
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True);records=[]
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),18)
    for ai in range(1,5):
        actor=f'pc_{ai:02}';canvas=Image.new('RGB',(900,12*220),'#d8d4c7');d=ImageDraw.Draw(canvas)
        for ji,job in enumerate(JOBS):
            d.text((5,ji*220+2),NAMES[ji],font=font,fill='#162835')
            for kind,w,h,rows in [('battle',96,96,1),('walk',32,48,4)]:
                path=f'assets/characters/{actor}/jobs/{job}/{kind}.png';sheet=Image.open(ROOT/path).convert('RGBA');frames=[]
                for row in range(rows):
                    for col in range(3):
                        frame=sheet.crop((col*w,row*h,(col+1)*w,(row+1)*h));points=landmarks(frame,kind,col,row if kind=='walk' else 0,job,actor);frames.append(points)
                        if kind=='battle':
                            large=frame.resize((192,192),Image.Resampling.NEAREST);x=100+col*260;y=ji*220+25;canvas.paste(large,(x,y),large)
                            for part,color in [('cheek','#00d8ff'),('arm','#ff4020'),('other_arm','#00a050'),('neck','#ffdf00')]:
                                if points[part]:d.line([(x+p[0]*2,y+p[1]*2) for p in points[part]],fill=color,width=2)
                records.append(dict(actor=actor,job=job,kind=kind,base=path,frames=frames))
        canvas.save(OUT/f'{actor}-anchor-review.png')
    (ROOT/'assets/source_records/erosion-costume-anchors.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('EROSION_ANCHORS: 48衣装・戦闘144コマ・歩行576コマの部位候補')

if __name__=='__main__':main()
