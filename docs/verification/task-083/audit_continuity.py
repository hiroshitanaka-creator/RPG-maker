#!/usr/bin/env python3
"""083基点との差分と、081から最新へ継続する出所判定を独立照合する。"""
import ast,hashlib,json,subprocess,types,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import validate_assets
BASE='a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf'
OUT=ROOT/'docs/verification/task-083'
checks=[]
def old(path,ref=BASE):return subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT)
def check(value,label):
 checks.append({'ok':bool(value),'label':label})
 if not value:print('CONTINUITY_FAIL:',label)
def main():
 before=types.ModuleType('before083');before.__file__=str(ROOT/'tools/validate_assets.py');exec(compile(old('tools/validate_assets.py'),before.__file__,'exec'),before.__dict__)
 key='assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png'
 expected=dict(before.OWNER_ADOPTED_ROOM_ORIGINALS);expected[key]='7fb285a7c31839ff33350c328f39dfd97e94ea57a0fe6567ef862f8fb19a9aa5'
 check(validate_assets.OWNER_ADOPTED_ROOM_ORIGINALS==expected,'既存許可一覧はchibi固定path/SHAの1件だけ増加')
 source=ast.parse((ROOT/'tools/validate_assets.py').read_text());base=ast.parse(old('tools/validate_assets.py'))
 def drop(tree):
  return ast.dump(ast.Module(body=[n for n in tree.body if not isinstance(n,ast.Assign) or not any(isinstance(t,ast.Name) and t.id=='OWNER_ADOPTED_ROOM_ORIGINALS' for t in n.targets)],type_ignores=[]))
 check(drop(source)==drop(base),'出所拒否関数・素材検査・CLI判定を含む全ASTは許可辞書以外不変')
 registry=json.loads(old('assets/registry.json'))
 for category in ['assets','audio','fonts']:
  for e in registry[category]:check(validate_assets.check_provenance(e)==before.check_provenance(e),'既存出所の許可/拒否不変: '+e['path'])
 paths=['scripts/world/first_region.gd','scripts/ui/game_root.gd','scripts/world/region2_shrine_story.gd','data/region2_shrine_scenes.json','docs/tasks/README.md','docs/decision-log.md','project.godot']
 for p in paths:check((ROOT/p).read_bytes()==old(p),'083基点から不変: '+p)
 historical='7d85b1100b7d8bea9cdffdad67c4ece72c739bbf'
 for p in ['world/region3_port.json','scripts/world/region3_port.gd','assets/town_backdrops/region3_port.png','assets/source_records/region3-port-081.json']:
  check((ROOT/p).read_bytes()==old(p,historical),'081完成版から継続不変: '+p)
 result={'base':BASE,'implementation_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'status':'PASS' if all(c['ok'] for c in checks) else 'FAIL','checks':checks,'historical_mapping':[{'original_condition':'081の許可一覧は外観1件だけ増加','fixed':'7d85b1100b7d8bea9cdffdad67c4ece72c739bbf 原assertionを全保持','latest':'083基点の許可一覧へchibi固定path/SHAだけ追加。関数AST不変・既存出所判定全件一致。'}, {'original_condition':'081の台帳は外観1件だけ追加、別地方/親台帳不変','fixed':'同上。081当時の比較基点と全期待値を維持','latest':'check_s10_static_display.pyで083基点から台帳1件・村イベント1件だけ追加を確認。親台帳と082本文はbytes不変。region3素材/定義は完成版とbytes一致。'}]}
 (OUT/'continuity-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('CONTINUITY_'+result['status']+': checks='+str(len(checks)));return result['status']!='PASS'
if __name__=='__main__':raise SystemExit(main())
