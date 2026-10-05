"""011の完成時限定の範囲・再生成と、最新でも続ける素材形式を別々に検査する。"""
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from validate_assets import load_palette
ROOT=Path(__file__).resolve().parents[1]
BASE='0f781630fa75b620f06e5d71430979a1c5162ef4'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def scope(completed):
 changed=git('diff','--name-only',BASE,completed).decode().splitlines();old=set(git('ls-tree','-r','--name-only',BASE).decode().splitlines())
 allowed={'assets/registry.json','scripts/world/first_region.gd','scripts/world/first_region_presentation.gd','docs/decision-log.md','docs/tasks/011-ruins-dungeon-groundwork.md','docs/tasks/reports/011-ruins-dungeon-groundwork.md','.github/workflows/ci.yml'}
 for p in changed:
  assert p in allowed or p not in old and (p.startswith('docs/verification/task-011/') or p=='docs/region2-ruins-groundwork.md' or p.startswith('tools/') and 'task011' in p or p in ['world/region2_ruins.json','scripts/world/region2_ruins.gd','scripts/world/region2_ruins.gd.uid','assets/source_records/task011-ruins.json','assets/source_records/task011-enemies.json'] or p.startswith('assets/interiors/region2_ruins_floor') or p.startswith('assets/monsters/ruins_') or p=='assets/backgrounds/region2_ruins.png'),'範囲外: '+p
 assert git('show',BASE+':.github/workflows/ci.yml')==git('show',completed+':.github/workflows/ci.yml'),'完成点の既存CI全文不変。011ステップは後の登録コミットで追加'
 before=json.loads(git('show',BASE+':assets/registry.json'));after=json.loads(git('show',completed+':assets/registry.json'))
 assert {k:v for k,v in before.items() if k!='assets'}=={k:v for k,v in after.items() if k!='assets'}
 previous={e['path'] for e in before['assets']};assert [e for e in after['assets'] if e['path'] in previous]==before['assets'],'既存台帳項目不変'
 assert after['assets'][-10:]==before['assets'][-10:],'村の既存生成器に必要な末尾10項目を保持'
 new=[e['path'] for e in after['assets'] if e['path'] not in previous];assert len(new)==14 and len(after['assets'])==len(before['assets'])+14,'4背景・4上層・5敵・1戦闘背景'
 original=git('show',BASE+':scripts/world/first_region.gd').decode();current=git('show',completed+':scripts/world/first_region.gd').decode()
 for addition in ['\n\t\tRegion2Ruins.apply_to(_data)','\tif node == "region2_ruins":return Region2Ruins.landing(room_index)\n','\tif state["layer"] == "interior" and state["node"] == "region2_ruins":return Region2Ruins.move(state)\n']:
  assert current.count(addition)==1;current=current.replace(addition,'',1)
 current=current.replace('"brine_port","region2_village","region2_ruins"] or room(state).is_empty()','"brine_port","region2_village"] or room(state).is_empty()',1)
 assert current==original,'既存の通行・保存条件・他地域の移動の変更'
 original=git('show',BASE+':scripts/world/first_region_presentation.gd').decode();current=git('show',completed+':scripts/world/first_region_presentation.gd').decode();addition='\n\t\t_data["maps"].merge(Region2Ruins.data()["maps"].duplicate(true))';assert current.count(addition)==1 and current.replace(addition,'',1)==original
 task='docs/tasks/011-ruins-dungeon-groundwork.md';original=git('show',BASE+':'+task).decode();current=git('show',completed+':'+task).decode();assert current.replace('- 状態：報告済み','- 状態：未着手')==original
 return dict(status='PASS',base_sha=BASE,completed_sha=completed,files=changed,new_assets=new,existing_assets_and_places_unchanged=True)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',action='store_true');args=parser.parse_args();head=git('rev-parse','HEAD').decode().strip()
 if args.stage:
  assert git('diff','--name-only','HEAD','--','assets','scripts','world','tools').decode().strip()=='','完成SHAと本番・検査器が一致'
  assert not [p for p in git('ls-files','--others','--exclude-standard').decode().splitlines() if p.startswith(('assets/','scripts/','world/','tools/')) and Path(p).suffix in ['.gd','.py','.json','.png']],'完成SHAに未登録の本番ファイル'
 record=json.loads((ROOT/'assets/source_records/task011-ruins.json').read_text());enemies=json.loads((ROOT/'assets/source_records/task011-enemies.json').read_text());registry=json.loads((ROOT/'assets/registry.json').read_text());entries={e['path']:e for e in registry['assets']};pal=load_palette(ROOT/'assets/palette/natural.gpl');paths=[];originals={};results=[]
 for r in record['maps'].values():
  originals[r['original']]=r['original_sha256'];paths.extend([r['background'],r['upper']])
 for e in enemies['enemies']:
  paths.append(e['path'])
  if 'original_file' in e:originals[e['original_file']]=e['original_sha256']
  else:assert hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()==e['existing_sha256'],'既存控え画像は再生成・再減色しない'
  assert e['stats']['hp']>0 and all(type(n) is int and n>=0 for n in e['stats'].values())
  if args.stage:assert e['name'].endswith('（仮）') and e['location']=='遺跡'
 b=enemies['battle_background'];paths.append(b['path']);originals[b['original_file']]=b['original_sha256']
 assert len(set(paths))==16 and len(enemies['enemies'])==7
 for p,digest in originals.items():
  raw=(ROOT/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==digest and raw==git('show',BASE+':'+p),'原画の全バイト不変: '+p
 for p in paths:
  e=entries[p];im=Image.open(ROOT/p);assert im.mode=='RGBA' and list(im.size)==e['size'];a=np.array(im);assert set(np.unique(a[:,:,3]))<={0,255};colors=set(map(tuple,a[:,:,:3][a[:,:,3]>0]));assert 0<len(colors)<=e['max_colors'] and colors<=pal
  if '/monsters/' in p:
   assert len(colors)<=32 and all(n%32==0 for n in im.size);limit=(192,160) if e['monster_tier']=='boss' else (96,96);assert im.width<=limit[0] and im.height<=limit[1];assert set(np.unique(a[:,:,3]))=={0,255};assert not a[0,:,3].any() and not a[-1,:,3].any()
  elif '/backgrounds/' in p:assert im.size==(512,288) and np.all(a[:,:,3]==255)
  else:assert all(n%32==0 for n in im.size) and len(colors)<=64
  results.append(dict(path=p,size=list(im.size),colors=len(colors),sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()))
 for m in json.loads((ROOT/'world/region2_ruins.json').read_text())['maps'].values():
  bg=np.array(Image.open(ROOT/m['backdrop']['path']));atlas=np.array(Image.open(ROOT/m['overlays']['path']))
  assert bg.shape[:2]==(m['height']*32,m['width']*32)
  for ax,ay,w,h,x,y,bottom,name in m['overlays']['pieces']:
   region=atlas[ay:ay+h,ax:ax+w];opaque=region[:,:,3]>0;assert np.array_equal(region[:,:,:3][opaque],bg[y:y+h,x:x+w,:3][opaque]),'上層は背景と同一画素'
 stage_record=scope(head) if args.stage else None
 if args.stage:
  from build_task011_ruins import build
  with tempfile.TemporaryDirectory(prefix='task011-rebuild-') as directory:
   a=Path(directory)/'one';b=Path(directory)/'two';built=build(a);assert built==build(b)
   for path in built+['assets/registry.json','world/region2_ruins.json','assets/source_records/task011-ruins.json','assets/source_records/task011-enemies.json']:
    assert (a/path).read_bytes()==(b/path).read_bytes(),'2回の再生成全バイト一致: '+path
    if path.endswith('.png'):assert (a/path).read_bytes()==(ROOT/path).read_bytes() and Image.open(a/path).tobytes()==Image.open(ROOT/path).tobytes(),'完成素材の再生成全バイト・全画素一致: '+path
    else:assert (a/path).read_bytes()==(ROOT/path).read_bytes(),'完成データの再生成全バイト一致: '+path
 out=ROOT/'docs/verification/task-011/latest';out.mkdir(parents=True,exist_ok=True);(out/'assets.json').write_text(json.dumps(dict(status='PASS',execution_sha=os.environ.get('TASK011_EXECUTION_SHA',head),stage=args.stage,scope=stage_record,originals=originals,results=results,palette_added_colors=0),ensure_ascii=False,indent=2)+'\n')
 print('TASK011_ASSETS_PASS: originals=7 assets=16 stage='+str(args.stage))
if __name__=='__main__':main()
