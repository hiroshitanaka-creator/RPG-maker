"""011の原画を変更せず、背景・通行・上層と敵を決定論的に取り込む。"""
from pathlib import Path
from fractions import Fraction
from scipy.ndimage import label
import argparse,hashlib,json
from collections import deque
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from backdrop_common import ROOT,palette
from build_region2_village_backdrops import nearest,nearest_resize,upper_layers
from build_region2_port_town_backdrop import pack
from import_owner_desert_monsters import cut_grey,convert_cutout
from village_png import save as save_png
import task011_ruins_defs as D
RECORD='assets/source_records/task011-ruins.json'
VERIFY='docs/verification/task-011'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def mask(shapes,size,scale,offset):
 im=Image.new('1',size);draw=ImageDraw.Draw(im)
 for shape in shapes:draw.polygon([(round(x*scale)+offset[0],round(y*scale)+offset[1]) for x,y in shape],fill=1)
 return np.array(im,dtype=bool)
def coverage(m,cols,rows):return m.reshape(rows,32,cols,32)[:,16:32,:,8:24].mean((1,3))
def quantize(raw,limit):
 bank=palette().astype(np.int32);indices=nearest(raw,bank)
 weights=np.bincount(indices.ravel(),minlength=len(bank));chosen=sorted(np.argsort(-weights,kind='stable')[:limit])
 return bank[chosen][nearest(raw,bank[chosen])].astype('uint8')
def connectivity(layout,start):
 todo=[tuple(start)];seen=set(todo)
 for x,y in todo:
  for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if 0<=yy<len(layout) and 0<=xx<len(layout[0]) and layout[yy][xx]=='.' and (xx,yy) not in seen:seen.add((xx,yy));todo.append((xx,yy))
 return seen

def build(dest):
 maps={};rooms=[];records={};paths=[]
 out=dest/VERIFY;out.mkdir(parents=True,exist_ok=True)
 for n,spec in enumerate(D.MAPS):
  source=ROOT/(D.A+D.FILES[n]);original=Image.open(source).convert('RGB');s=Fraction(*spec['scale']);scale=float(s);offset=spec['offset'];sw,sh=round(original.width*s),round(original.height*s)
  cols,rows=(sw+offset[0]+31)//32,(sh+offset[1]+31)//32;size=(cols*32,rows*32)
  small=nearest_resize(original,(sw,sh));canvas=Image.new('RGB',size,original.getpixel((0,0)));canvas.paste(small,tuple(offset));raw=np.array(canvas)
  rgb=quantize(raw,64);image=Image.fromarray(rgb).convert('RGBA')
  walk=coverage(mask(spec['floor'],size,scale,offset),cols,rows)>=.70
  masks={};feet={}
  for item in spec['objects']:
   m=mask([item['shape']],size,scale,offset);foot=coverage(mask([item['foot']],size,scale,offset),cols,rows)>=.25
   masks[item['name']]=m;feet[item['name']]=foot;walk&=~foot
  for shape in spec['blocks']:walk&=coverage(mask([shape],size,scale,offset),cols,rows)<.25
  layout=[''.join('.' if c else '#' for c in row) for row in walk]
  # 孤立マスを隠して捨てない。入口から全床へ到達できることを提出前に検査する。
  seen=connectivity(layout,spec['landings'][0]);isolated=int(walk.sum())-sum(layout[y][x]=='.' for x,y in seen)
  pieces=upper_layers(masks,feet,walk,dict(rows=rows,columns=cols));atlas,table=pack(pieces,rgb)
  padded=Image.new('RGBA',(atlas.width,(atlas.height+31)//32*32));padded.paste(atlas)
  background=f'assets/interiors/region2_ruins_floor{n+1}.png';upper=f'assets/interiors/region2_ruins_floor{n+1}_upper.png'
  for p,im in [(background,image),(upper,padded)]:
   (dest/p).parent.mkdir(parents=True,exist_ok=True);save_png(im,dest/p);paths.append(p)
  mapdata=dict(name=f'遺跡・{n+1}階（仮）' if n<3 else '遺跡・最下層（仮）',origin=[0,0],width=cols,height=rows,layout=layout,tiles={},layers=[],surround='assets/tiles/natural_stone_wall.png',backdrop=dict(path=background,offset=[0,0]),overlays=dict(path=upper,pieces=table))
  maps[f'region2_ruins:{n}']=mapdata
  rooms.append(dict(title=mapdata['name'],layout=layout,events=[],spawn=spec['landings'][0]))
  records[str(n)]=dict(original=str(source.relative_to(ROOT)),original_sha256=sha(source),source_size=list(original.size),scale=spec['scale'],offset=offset,size=list(size),floor=spec['floor'],objects=spec['objects'],blocks=spec['blocks'],foot_box=[8,16,24,32],floor_coverage=.70,obstacle_coverage=.25,walkable_cells=int(walk.sum()),isolated=isolated,background=background,upper=upper,upper_pieces=table,landings=spec['landings'],treasure_candidates=spec['treasure'],probes=spec['probes'])
  review=image.convert('RGB');d=ImageDraw.Draw(review,'RGBA')
  for y in range(rows):
   for x in range(cols):
    d.rectangle((x*32,y*32,x*32+31,y*32+31),fill=(0,220,70,65) if walk[y,x] else (230,0,30,70),outline=(255,255,255,60));d.text((x*32+1,y*32+1),f'{x},{y}',fill=(255,255,255,255))
  for ax,ay,w,h,x,y,bottom,name in table:d.rectangle((x,y,x+w-1,y+h-1),outline=(40,150,255,255),width=2)
  for floor,cell,other,landing,facing in D.LINKS:
   if floor==n:d.rectangle((cell[0]*32,cell[1]*32,cell[0]*32+31,cell[1]*32+31),outline=(255,220,0,255),width=3)
  panel=Image.new('RGB',(size[0],size[1]+32),(18,28,42));panel.paste(review,(0,32));font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),18);ImageDraw.Draw(panel).text((8,3),'確認用状態 / '+mapdata['name']+' / 緑:通行 赤:不通 青:上層 黄:階段',font=font,fill='white');panel.save(out/f'floor{n+1}-overview.png')
  print('floor',n,'size',size,'walk',int(walk.sum()),'isolated',isolated,'landings',[(c,layout[c[1]][c[0]]) for c in spec['landings']], 'triggers',[(c,layout[c[1]][c[0]]) for f,c,_,_,_ in D.LINKS if f==n])
 links=[dict(from_room=f,from_cell=c,to_room=t,to_cell=landing,facing=face) for f,c,t,landing,face in D.LINKS]
 document=dict(version=1,node='region2_ruins',site=dict(id='region2_ruins',rooms=rooms),maps=maps,stairs=links,world_connection=dict(enabled=False,cells=[[17,21],[18,21],[19,21]],note='1階下の入口。世界マップ接続は後続依頼'),encounters_enabled=False,boss_enabled=False)
 write(dest/'world/region2_ruins.json',document)
 record=dict(version=1,base_sha='0f781630fa75b620f06e5d71430979a1c5162ef4',palette_sha256=sha(ROOT/'assets/palette/natural.gpl'),maps=records,method='全原画の最近傍縮小＋最多使用64色以内のnatural.gpl最近傍減色。上層は同一RGBを切出し。原本不変。')
 write(dest/RECORD,record)
 # 新しい敵は本番遭遇台帳と分けて候補台帳へ保存。既存36種・戦闘規則は維持。
 enemies=[];monster_source=ROOT/'assets/_incoming/owner-2026-10-04-grok-region3/region3-killer-machine-spear.png';source=Image.open(monster_source)
 specs=[('ruins_sandstone_doll','砂岩の人形（仮）',0,264,'medium',80,(185,0,22,24,0,9,7)),('ruins_cursed_beetle','呪われた甲虫（仮）',264,576,'medium',72,(150,12,17,28,8,10,9)),('ruins_sand_spirit','砂の霊（仮）',576,843,'large',92,(135,24,9,8,24,18,18)),('ruins_tomb_hound','墓守の番犬（仮）',843,1168,'medium',80,(175,10,26,13,4,10,20))]
 for ident,name,left,right,category,extent,values in specs:
  slot=source.crop((left,0,right,source.height));clean=cut_grey(slot);
  if ident in ['ruins_cursed_beetle','ruins_tomb_hound']:
   a=np.array(clean);groups,total=label(a[:,:,3]>0,np.ones((3,3)));counts=np.bincount(groups.ravel());counts[0]=0;a[groups!=counts.argmax()]=0;clean=Image.fromarray(a)
  if ident=='ruins_sand_spirit':
   left,right=543,912;slot=source.crop((left,0,right,source.height));clean=cut_grey(slot);a=np.array(clean);region=Image.new('1',slot.size);ImageDraw.Draw(region).polygon([(x-left,y) for x,y in [(543,170),(844,170),(911,300),(911,382),(838,439),(815,573),(580,573),(580,449),(543,401)]],fill=1);a[~np.array(region,dtype=bool)]=0;clean=Image.fromarray(a)
  box=clean.getbbox();body=convert_cutout(clean,box,extent,palette().astype(np.int32));im=Image.new('RGBA',(96,96));im.alpha_composite(body,((96-body.width)//2,94-body.height));p=f'assets/monsters/{ident}/idle.png';(dest/p).parent.mkdir(parents=True,exist_ok=True);save_png(im,dest/p);paths.append(p)
  enemies.append(dict(id=ident,name=name,sprite_id=ident,location='遺跡',size_class=category,monster_tier='normal',stats=dict(zip(['hp','mp','attack','defense','magic','resistance','speed'],values)),abilities=[],weaknesses=[],jp=20,design_status='既存第2地方の敵を基準にした仮値。遭遇未登録',path=p,original_file=str(monster_source.relative_to(ROOT)),original_sha256=sha(monster_source),split_rect=[left,0,right,source.height],segmentation='8近傍で最大の連結体だけを残す' if ident in ['ruins_cursed_beetle','ruins_tomb_hound'] else '原画座標の多角形で他の個体を除く' if ident=='ruins_sand_spirit' else '外周灰色背景だけを除く',crop_box=list(box),extent=extent))
 boss_source=ROOT/(D.A+'chat-image-5-aa5c2020.png');a=np.array(Image.open(boss_source).convert('RGBA'));opaque=(a[:,:,3]>=128)&~np.all(a[:,:,:3]<25,axis=2);a[~opaque]=0;a[opaque,3]=255;clean=Image.fromarray(a);box=clean.getbbox();body=convert_cutout(clean,box,152,palette().astype(np.int32));im=Image.new('RGBA',(192,160));im.alpha_composite(body,((192-body.width)//2,158-body.height));p='assets/monsters/ruins_sandstone_colossus/idle.png';(dest/p).parent.mkdir(parents=True,exist_ok=True);save_png(im,dest/p);paths.append(p)
 enemies.append(dict(id='ruins_sandstone_colossus',name='砂岩の巨像（仮）',sprite_id='ruins_sandstone_colossus',location='遺跡',size_class='boss',monster_tier='boss',stats=dict(zip(['hp','mp','attack','defense','magic','resistance','speed'],(800,30,36,30,24,22,9))),abilities=[],weaknesses=[],jp=50,design_status='既存ボスを基準にした仮値。ボス戦未登録',path=p,original_file=str(boss_source.relative_to(ROOT)),original_sha256=sha(boss_source),crop_box=list(box),extent=152))
 for ident,name,values in [('desert_mummy','ミイラ（仮）',(160,12,20,14,12,12,8)),('stone_gargoyle','石の翼像（仮）',(185,0,22,26,0,13,14))]:
  enemies.append(dict(id=ident,name=name,sprite_id=ident,location='遺跡',size_class='medium',monster_tier='normal',stats=dict(zip(['hp','mp','attack','defense','magic','resistance','speed'],values)),abilities=[],weaknesses=['fire'] if ident=='desert_mummy' else ['ice'],jp=20,design_status='取り込み済み控え素材。仮値。遭遇未登録',path=f'assets/monsters/{ident}/idle.png',existing_sha256=sha(ROOT/f'assets/monsters/{ident}/idle.png')))
 battle_source=ROOT/'assets/_incoming/owner-2026-10-03-region3-port/05-ruins-battle.png';battle=Image.open(battle_source).convert('RGB').resize((512,288),Image.Resampling.NEAREST);p='assets/backgrounds/region2_ruins.png';(dest/p).parent.mkdir(parents=True,exist_ok=True);save_png(Image.fromarray(quantize(np.array(battle),64)).convert('RGBA'),dest/p);paths.append(p)
 for row in enemies:
  im=Image.open(dest/row['path'] if row['path'] in paths else ROOT/row['path']);row['size']=list(im.size);box=im.getbbox();row['visible_size']=[box[2]-box[0],box[3]-box[1]];row['output_sha256']=sha(dest/row['path'] if row['path'] in paths else ROOT/row['path'])
 write(dest/'assets/source_records/task011-enemies.json',dict(version=1,location='遺跡',status='候補台帳。通常遭遇・ボス戦は有効化しない',enemies=enemies,battle_background=dict(path=p,original_file=str(battle_source.relative_to(ROOT)),original_sha256=sha(battle_source),size=[512,288],scale=[4,15])))
 registry=json.loads((ROOT/'assets/registry.json').read_text());registry['assets']=[e for e in registry['assets'] if e['path'] not in paths]
 for path in paths:
  im=Image.open(dest/path);entry=dict(path=path,size=list(im.size),max_colors=32 if '/monsters/' in path else 64,status='required',palette='assets/palette/natural.gpl',source='owner',license='LicenseRef-Owner-Provided',author='依頼者',provided_at='2026-10-05',modified='原画から決定論的な切出し・最近傍縮小・最近傍減色。二値透過。原本不変。')
  if '/monsters/' in path:
   row=next(e for e in enemies if e['path']==path);entry.update(kind='monster_idle',facing='front' if row['id']!='ruins_tomb_hound' else 'right',size_class=row['size_class'],monster_tier=row['monster_tier'],visible_size=row['visible_size'],original_file=row['original_file'],conversion_record='assets/source_records/task011-enemies.json#'+row['id'])
  elif '/backgrounds/' in path:entry.update(kind='battle_background',original_file=str(battle_source.relative_to(ROOT)),conversion_record='assets/source_records/task011-enemies.json#battle_background')
  else:
   n=int(path.split('floor')[1][0])-1;entry.update(kind='town_overlay' if '_upper' in path else 'interior_backdrop',original_file=D.A+D.FILES[n],conversion_record=RECORD+'#'+str(n))
  entry.update(source='generated',tool='依頼者提供原画 + Python/Pillow（派生変換）',author='RPG-maker / Codex（原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-10-05',prompt_record=entry['conversion_record'])
  entry.pop('provided_at',None)
  registry['assets'].append(entry)
 write(dest/'assets/registry.json',registry)
 return paths
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT);args=parser.parse_args();build(args.output)
