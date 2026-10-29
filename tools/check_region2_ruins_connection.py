"""084の固定座標・独立BFS・旧011全データ/画像算法と再生成を照合する。"""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
BASE='f9169ac4048e98229d34692bc1e9efb6a0a3efaf'
OUT=ROOT/'docs/verification/task-084'
EXPECTED=dict(enabled=True,world_cell=[176,91],return_cell=[176,92],return_facing=0,room=0,landing=[18,19],entry_facing=3,exit_cell=[18,20],cells=[[17,21],[18,21],[19,21]])
checks=[]
def check(ok,label,detail=None):
 checks.append(dict(ok=bool(ok),label=label,detail=detail))
 if not ok:print('RUINS_DATA_FAIL: '+label,detail)
def old(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
def load(path):return json.loads((ROOT/path).read_text())
def bfs(start,goal,blocked):
 coast=load('world/second_region_coast.json');ox,oy=coast['origin'];seen={start:None};todo=[start]
 for x,y in todo:
  if (x,y)==goal:break
  for dx,dy in [(0,1),(-1,0),(1,0),(0,-1)]:
   n=(x+dx,y+dy);xx,yy=n[0]-ox,n[1]-oy
   if n in seen or n in blocked or not (0<=xx<coast['width'] and 0<=yy<coast['height']) or coast['layout'][yy][xx]!='.':continue
   seen[n]=(x,y);todo.append(n)
 if goal not in seen:return []
 result=[];n=goal
 while n is not None:result.append(list(n));n=seen[n]
 return result[::-1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--regenerate',action='store_true');args=parser.parse_args()
 document=load('world/region2_ruins.json');previous=json.loads(old('world/region2_ruins.json'))
 check(document['world_connection']==EXPECTED,'接続メタデータの固定期待値')
 check({k:v for k,v in document.items() if k!='world_connection'}=={k:v for k,v in previous.items() if k!='world_connection'},'全4階の部屋/床/階段/上層/spawn/無効フラグ不変')
 for cell in [[18,19],[18,20]]:check(document['site']['rooms'][0]['layout'][cell[1]][cell[0]]=='.','南着地/接触は既存床',cell)
 for cell in [[17,21],[18,21],[19,21]]:check(document['site']['rooms'][0]['layout'][cell[1]][cell[0]]=='#','旧入口候補は壁を維持',cell)
 check(document['site']['rooms'][0]['spawn']==[18,5],'旧補正spawn不変')
 check(document['world_connection'].get('cells')==previous['world_connection']['cells'],'旧011 stage負例が読む壁候補メタデータを保持')
 # defsを実行せずASTで元の全statementを保持したことを検証する。
 before=ast.parse(old('tools/task011_ruins_defs.py'));after=ast.parse((ROOT/'tools/task011_ruins_defs.py').read_text())
 filtered=ast.Module(body=[n for n in after.body if not isinstance(n,ast.Assign) or not any(isinstance(t,ast.Name) and t.id=='WORLD_CONNECTION' for t in n.targets)],type_ignores=[])
 check(ast.dump(before)==ast.dump(filtered),'旧MAPS/LINKS/WALLS全statement不変')
 builder=(ROOT/'tools/build_task011_ruins.py').read_text();restored=builder.replace('world_connection=D.WORLD_CONNECTION.copy()',"world_connection=dict(enabled=False,cells=[[17,21],[18,21],[19,21]],note='1階下の入口。世界マップ接続は後続依頼')")
 check(restored.encode()==old('tools/build_task011_ruins.py'),'画像/台帳生成算法は接続メタデータ以外全文不変')
 for path in ['assets/registry.json','world/second_region_coast.json','scripts/game/game_session.gd','scripts/world/first_region_travel.gd','data/region2_shrine_scenes.json']:
  check((ROOT/path).read_bytes()==old(path),'範囲外の関連既存データ不変',path)
 assets=subprocess.check_output(['git','diff','--name-only',BASE,'--','assets','.scope-lock','test','.github','project.godot'],cwd=ROOT,text=True)
 check(not assets.strip(),'原画/派生/台帳/保護/CI不変',assets.splitlines())
 paths=[];blocked={(176,91),(169,88),(169,98)}
 for goal in [(168,88),(170,88),(169,99),(156,109)]:
  path=bfs((176,92),goal,blocked);check(bool(path),'独立BFS：入口/村港入口を避け帰路がある',list(goal));paths.append(dict(goal=list(goal),path=path))
 check(len({(176,91),(176,92),(169,88),(169,98),(156,109)})==5,'入口/帰着/村/港/浅瀬の非重複')
 if args.regenerate:
  from build_task011_ruins import build
  with tempfile.TemporaryDirectory(prefix='task084-rebuild-') as tmp:
   a=Path(tmp)/'one';b=Path(tmp)/'two';build(a);build(b)
   fa=sorted(str(p.relative_to(a)) for p in a.rglob('*') if p.is_file());fb=sorted(str(p.relative_to(b)) for p in b.rglob('*') if p.is_file());check(fa==fb,'2回生成の全path一致')
   for path in fa:
    check((a/path).read_bytes()==(b/path).read_bytes(),'2回生成の全bytes一致',path)
    if path=='world/region2_ruins.json' or path.startswith('assets/') and path!='assets/registry.json':check((a/path).read_bytes()==(ROOT/path).read_bytes(),'本番既存画像/出所/接続JSONと再生成全bytes一致',path)
   # 現行台帳の後続項目・挿入順は011生成範囲外。出力を本番へ書かない。
 spec=importlib.util.spec_from_file_location('defs',ROOT/'tools/task011_ruins_defs.py');defs=importlib.util.module_from_spec(spec);spec.loader.exec_module(defs)
 check(getattr(defs,'WORLD_CONNECTION',None)==EXPECTED,'defsの接続は固定期待値と一致')
 ruins=(ROOT/'scripts/world/region2_ruins.gd').read_text()
 target='\treturn {"kind":"moved"}'
 check(ruins.count(target)==old('scripts/world/region2_ruins.gd').decode().count(target)==1,'旧027故障注入の最終通知targetを1か所に保持')
 OUT.mkdir(parents=True,exist_ok=True);result=dict(status='PASS' if all(c['ok'] for c in checks) else 'FAIL',base_sha=BASE,checks=checks,independent_bfs=paths,regenerated=args.regenerate)
 (OUT/'data-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('RUINS_DATA_'+result['status']+': checks='+str(len(checks)))
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
