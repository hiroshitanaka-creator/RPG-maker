"""依頼者原画から第2港の部品と室内、原画を基準に生成した住人歩行を作る。"""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from import_job_costumes import parts

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'assets/_incoming/owner-2026-10-01-region2-port'
OUT=ROOT/'docs/verification/region2-port'
RECORD='assets/source_records/region2-port-assets.json'
EXTERIOR='FE4B1B12-C9B1-4DB0-B374-81F51D061BA6.PNG'
NAMES=['innkeeper','item_clerk','weapon_clerk','armor_clerk','shrine_keeper','sailor','fisher','merchant','child','traveller']
LABELS=['宿の主人','道具屋','武器屋','防具屋','祠の世話役','港務所の船員','漁師','露店の商人','水がめの子','旅人']
ROOMS={
 'inn':'75462BFD-D5F5-4BEC-94EF-2241C7A1D0C7.PNG',
 'item':'7BDBE31E-F3AF-49E2-AD04-6505CCEA796C.PNG',
 'weapon':'C9A48E60-3050-4DE6-AB1F-5399C014323B.PNG',
 'armor':'A57472FD-36AF-4085-BA41-25B571A3F2AF.PNG',
 'shrine':'FBE86B94-685C-4745-85C0-B45FF36DCCFF.PNG',
 'harbor':'4D2815AA-E544-49BB-9714-0B9E8FB43D94.PNG',
}
# 原画上の多角形。砂・空・海を背景ごと四角く貼らず、部品の輪郭を抜く。
CUTS={
 'inn':([224,160],[(406,48),(556,48),(556,77),(619,77),(620,148),(650,154),(657,247),(621,263),(372,263),(351,241),(354,144),(400,129)]),
 'item':([192,128],[(778,85),(919,87),(924,159),(950,168),(953,254),(738,263),(730,232),(741,174),(777,171)]),
 'weapon':([192,160],[(89,218),(241,218),(244,289),(294,291),(306,382),(272,399),(82,400),(56,369),(62,288),(87,284)]),
 'armor':([192,160],[(949,265),(1074,265),(1078,312),(1121,333),(1131,428),(1080,442),(895,433),(879,388),(916,365),(929,306),(948,300)]),
 'shrine':([128,160],[(1105,88),(1122,102),(1144,116),(1158,146),(1165,207),(1150,229),(1155,245),(1139,255),(1066,255),(1055,238),(1061,145),(1075,115),(1093,106)]),
 'harbor':([192,128],[(1167,432),(1232,430),(1233,448),(1338,449),(1358,472),(1367,545),(1376,577),(1364,611),(1145,611),(1127,581),(1120,548),(1146,526),(1165,506)]),
 'home_a':([192,128],[(211,486),(242,486),(244,497),(306,496),(310,575),(333,592),(331,671),(282,693),(115,695),(72,670),(75,554),(112,552),(114,540),(204,540)]),
 'home_b':([192,128],[(362,540),(440,540),(441,560),(519,560),(520,599),(540,604),(549,679),(522,698),(390,697),(359,681)]),
 'arch':([128,128],[(108,22),(126,21),(139,34),(198,36),(219,17),(245,12),(251,28),(248,129),(217,135),(190,122),(182,70),(161,66),(141,77),(137,128),(98,132),(104,56)]),
 'well':([96,96],[(565,297),(635,297),(641,331),(630,334),(630,354),(648,367),(649,389),(628,407),(580,402),(558,389),(558,370),(571,356),(571,334),(562,333)]),
 'stall_red':([96,96],[(410,297),(477,278),(517,299),(521,322),(510,328),(515,365),(487,379),(413,365),(400,350),(407,322)]),
 'stall_blue':([96,96],[(692,286),(717,270),(777,287),(788,314),(781,333),(803,355),(796,379),(744,383),(691,359),(678,329)]),
 'stall_gold':([96,96],[(442,412),(469,397),(520,415),(539,439),(533,452),(541,477),(510,495),(443,476),(431,454)]),
 'stall_sand':([96,96],[(652,411),(674,405),(723,429),(739,450),(737,472),(708,489),(660,477),(644,447)]),
 'pillar':([64,128],[(1227,22),(1260,23),(1260,53),(1255,61),(1258,92),(1268,100),(1274,111),(1260,134),(1224,139),(1208,122),(1212,105),(1229,93),(1231,59),(1224,52)]),
 'wall':([128,64],[(599,50),(625,48),(631,62),(664,58),(670,70),(700,66),(704,102),(672,109),(644,97),(620,99),(601,91)]),
 'rocks':([96,96],[(1438,233),(1466,215),(1487,226),(1505,218),(1527,244),(1533,277),(1522,299),(1497,306),(1485,290),(1455,300),(1431,282),(1425,253)]),
 'boat':([64,96],[(704,631),(722,630),(739,647),(755,678),(754,701),(742,716),(722,709),(706,692),(691,662),(695,640)]),
}

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def palette():
    colors=[]
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
        p=line.split()
        if len(p)>=3 and all(x.isdigit() for x in p[:3]):colors.append(list(map(int,p[:3])))
    return np.array(colors,dtype=np.int32)

def quantize(image,limit):
    a=np.array(image.convert('RGBA'));opaque=a[:,:,3]>=160;pal=palette()
    rgb,inv,counts=np.unique(a[:,:,:3][opaque],axis=0,return_inverse=True,return_counts=True)
    distances=((rgb.astype(np.int32)[:,None]-pal[None])**2).sum(2)
    nearest=distances.argmin(1);weights=np.bincount(nearest,weights=counts,minlength=len(pal))
    selected=np.flatnonzero(weights>0).tolist()
    if len(selected)>limit:
        chosen=[int(weights.argmax())];pp=((pal[:,None]-pal[None])**2).sum(2);best=pp[:,chosen[0]]
        while len(chosen)<limit:
            gain=(np.maximum(best[:,None]-pp,0)*weights[:,None]).sum(0);gain[chosen]=-1
            idx=int(gain.argmax());chosen.append(idx);best=np.minimum(best,pp[:,idx])
        selected=chosen
    nearest=distances[:,selected].argmin(1);a[:,:,:3][opaque]=pal[selected][nearest[inv]]
    a[:,:,3]=opaque*255;a[~opaque]=0
    return Image.fromarray(a),pal[selected].tolist()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));entries={a['path']:a for a in registry['assets']};records=[]
    def save(image,path,source,kind,limit=64,**details):
        image,used=quantize(image,limit);dest=ROOT/path;dest.parent.mkdir(parents=True,exist_ok=True);image.save(dest)
        row=dict(path=path,source=source,source_sha256=sha(ROOT/source),sha256=sha(dest),size=list(image.size),colors=used,**details);records.append(row)
        entry=dict(path=path,kind=kind,size=list(image.size),max_colors=limit,status='required',palette='assets/palette/natural.gpl',source='owner',author='依頼者（動作補完：Codex）' if kind=='character_walk' else '依頼者',license='LicenseRef-Owner-Provided',original_file=source,conversion_record=RECORD,modified='原本は不変。記録した範囲の切り抜き・最近傍縮小・自然色パレット・二値透過。')
        if kind!='character_walk':
            archive=ROOT/'assets/_incoming/owner-2026-09-26/supplement-2026-10-02-region2-port'/Path(source).name
            archive.parent.mkdir(parents=True,exist_ok=True)
            if archive.exists():assert archive.read_bytes()==(ROOT/source).read_bytes(),'保管原本の上書き禁止'
            else:archive.write_bytes((ROOT/source).read_bytes())
            entry.update(provided_at='2026-10-01',received_file=source,original_file=archive.relative_to(ROOT).as_posix())
            row.update(archive_copy=entry['original_file'],archive_sha256=sha(archive))
        if kind=='character_walk':entry.update(source='generated',tool='imagegen + Python/Pillow',license='LicenseRef-Generated-Project',prompt_record='assets/source_records/region2-port-generation.json',frame=[32,48],grid=[3,4],generated_at='2026-10-02')
        entries[path]=entry
        return image
    src=Image.open(RAW/EXTERIOR).convert('RGBA');rel=(RAW/EXTERIOR).relative_to(ROOT).as_posix()
    for name,(size,polygon) in CUTS.items():
        mask=Image.new('L',src.size);ImageDraw.Draw(mask).polygon(polygon,fill=255)
        if name=='arch':ImageDraw.Draw(mask).polygon([(137,128),(138,87),(144,72),(159,66),(172,70),(182,87),(185,129)],fill=0)
        im=src.copy();im.putalpha(mask);box=mask.getbbox();im=im.crop(box);scale=min((size[0]-2)/im.width,(size[1]-2)/im.height)
        im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);canvas=Image.new('RGBA',size);canvas.alpha_composite(im,((size[0]-im.width)//2,size[1]-im.height))
        save(canvas,'assets/objects/region2_'+name+'.png',rel,'object',polygon=polygon,crop=list(box),scale=scale)
    # 葉は緑の原画画素、幹は記録した細い多角形。隣の空・砂は取り込まない。
    box=[12,0,106,133];im=src.crop(box);a=np.array(im);mask=(a[:,:,1]>a[:,:,0]*.9)&(a[:,:,1]>a[:,:,2]*1.12)
    trunk=Image.new('L',im.size);ImageDraw.Draw(trunk).polygon([(52,45),(61,47),(63,117),(56,130),(51,112)],fill=255)
    a[:,:,3]=(mask|(np.array(trunk)>0))*255;im=Image.fromarray(a).resize((96,128),Image.Resampling.NEAREST)
    save(im,'assets/objects/region2_palm.png',rel,'object',crop=box,method='緑の葉の色と幹の多角形で抜く')
    for name,box in [('sand',[700,0,732,32]),('cobble',[290,420,322,452]),('pier',[810,550,842,582]),('water',[850,878,882,910])]:
        save(src.crop(box),'assets/tiles/region2_'+name+'.png',rel,'tileset',crop=box)
    for kind,file in ROOMS.items():
        original=Image.open(RAW/file).convert('RGBA');small=original.resize((584,389),Image.Resampling.NEAREST)
        canvas=Image.new('RGBA',(512,384),original.getpixel((0,0)));canvas.alpha_composite(small,(-20,8))
        save(canvas,'assets/interiors/region2_'+kind+'.png',(RAW/file).relative_to(ROOT).as_posix(),'interior_backdrop',scale=[584/1536,389/1024],offset=[-20,8],method='原画全体を最近傍縮小。外周の暗い余白のみキャンバス外。扉中央は8列目')
    generated=json.loads((ROOT/'assets/source_records/region2-port-generation.json').read_text(encoding='utf8'))
    for pair,row in enumerate(generated['sheets']):
        source=row['file'];frames=parts(ROOT/source,6,4)
        for person in range(2):
            index=pair*2+person;selected=[];boxes=[];operations=[]
            for direction in range(4):
                source_row=3-direction if index==9 and direction in [1,2] else direction
                for column in range(3):
                    im,box=frames[source_row*6+person*3+column];op='なし'
                    if pair==3 and direction==1 and column==2:im=ImageOps.mirror(im);op='誤った右向きを左へ水平反転'
                    if index==9 and direction in [1,2]:op='生成原画の左右行を入れ替え'
                    selected.append(im);boxes.append(box);operations.append(op)
            height=34 if index==8 else 44;scale=min(height/max(im.height for im in selected),30/max(im.width for im in selected));sheet=Image.new('RGBA',(96,192))
            for i,im in enumerate(selected):
                im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST);sheet.alpha_composite(im,(i%3*32+(32-im.width)//2,i//3*48+48-im.height))
            save(sheet,'assets/characters/npc_sand_'+NAMES[index]+'/walk.png',source,'character_walk',16,actor='npc_sand_'+NAMES[index],owner_reference=(RAW/'9BC9CFCF-2A63-4939-83E5-0886F820494B.PNG').relative_to(ROOT).as_posix(),owner_reference_sha256=sha(RAW/'9BC9CFCF-2A63-4939-83E5-0886F820494B.PNG'),boxes=boxes,operations=operations,scale=scale,ground_y=47)
    registry['assets']=list(entries.values());write(ROOT/'assets/registry.json',registry)
    write(ROOT/RECORD,dict(originals_unchanged=True,palette_added=[],entries=records))
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),19);font.set_variation_by_name('Medium')
    poster=Image.new('RGB',(1000,880),'#d9d0b8');d=ImageDraw.Draw(poster)
    for i,name in enumerate(NAMES):
        x=i%5*200;y=i//5*440;d.text((x+4,y+6),LABELS[i],font=font,fill='#1c2830')
        im=Image.open(ROOT/f'assets/characters/npc_sand_{name}/walk.png').resize((192,384),Image.Resampling.NEAREST);poster.paste(im,(x+4,y+42),im)
    poster.save(OUT/'residents-walk.png')
    print('第2港素材:',len(records),'点。原本と既存素材は保持。パレット追加0色。')

if __name__=='__main__':main()
