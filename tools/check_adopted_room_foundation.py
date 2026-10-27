#!/usr/bin/env python3
"""080の独立構造・原bytes・変更範囲検査。既存検査は変更しない。"""
import argparse, copy, hashlib, json, subprocess
from collections import deque
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BASE = 'e677896d3e61b8fe8136ef60c5c76f41ad76701d'
SOURCE = '84f446e48cbaef2a199da1d464311992daf13938'
# 原画の目視で選んだ足元。layoutから期待値を作らない。
PROBES = {
 'inn': {'floor': [[6,9],[5,3],[7,4],[9,5],[12,3]], 'solid': [[2,4],[2,6],[8,3],[9,4],[0,5]], 'occluder':0, 'behind':[7,4], 'front':[9,5]},
 'item_shop': {'floor': [[6,9],[2,4],[6,7],[11,7],[11,9]], 'solid': [[6,8],[4,8],[1,4],[12,6],[0,5]], 'occluder':0, 'behind':[6,7], 'front':[6,9]},
 'weapon_shop': {'floor': [[6,9],[3,4],[6,4],[6,6],[10,5]], 'solid': [[6,5],[2,4],[11,3],[1,2],[0,5]], 'occluder':0, 'behind':[6,4], 'front':[6,6]},
 'shrine': {'floor': [[6,9],[6,5],[8,2],[9,3],[3,7]], 'solid': [[6,3],[6,4],[1,3],[0,5],[10,10]], 'occluder':0, 'behind':[8,2], 'front':[6,5]},
 'armor_shop': {'floor': [[6,9],[10,4],[10,5],[6,4],[6,6]], 'solid': [[3,4],[2,6],[11,3],[11,6],[6,5]], 'occluder':2, 'behind':[10,4], 'front':[10,5]},
}
HASHES = ['52723c0560ca54cf9aff695d383a17235b8f224058dda7a2367304e79cb5e007','76bf5d755bf8b98d7125c800abf02fb27b2b5dda080ac43ff1f966a9c65469cb','be55b08fc7da5421f84c8c88001586e523369b9dfff8e950d83bd96500e6d93c','46c00cbdc2ad0d02e1d05662793c15bb2117ea28cb9f0ceeab75f118ce8065c8','eefd5131abf790c2a8e7ff5393054898f8bf126b722cca2982e634a4b21f4b31']

def inspect(d):
 errors=[]
 if [r['id'] for r in d['rooms']] != list(PROBES):errors.append('5室の識別')
 if len({r['path'] for r in d['rooms']}) != 5:errors.append('画像重複')
 for r in d['rooms']:
  rows=r['layout'];floor={(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c=='.'}
  if len(rows)!=12 or any(len(row)!=14 or set(row)-set('.#') for row in rows):errors.append('寸法')
  for kind in ['floor','solid']:
   for xy in PROBES[r['id']][kind]:
    if (tuple(xy) in floor)!=(kind=='floor'):errors.append(r['id']+':目視固定'+str(xy))
  start=tuple(r['spawn']);seen={start};q=deque([start])
  while q:
   x,y=q.popleft()
   for n in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if n in floor and n not in seen:seen.add(n);q.append(n)
  if seen != floor or tuple(r['exit']) not in seen:errors.append(r['id']+':閉じ込め')
  if r.get('events') or r.get('world_connection'):errors.append('未承認接続')
 return errors

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
 d=json.loads((ROOT/'world/adopted_room_foundation.json').read_text());errors=inspect(d);negative=[]
 for label,mutate in [
  ('不足室',lambda x:x['rooms'].pop()),
  ('画像取り違え',lambda x:x['rooms'][1].update(path=x['rooms'][0]['path'])),
  ('家具通過',lambda x:x['rooms'][1]['layout'].__setitem__(8,'##..........##')),
  ('入口閉鎖',lambda x:x['rooms'][0]['layout'].__setitem__(10,'##############')),
  ('未承認接続',lambda x:x['rooms'][0].update(world_connection='world'))]:
  bad=copy.deepcopy(d);mutate(bad);found=inspect(bad);negative.append({'case':label,'rejected':bool(found),'errors':found})
  if not found:errors.append('負例不検出:'+label)
 hashes=[]
 for r,expected in zip(d['rooms'],HASHES):
  raw=(ROOT/r['path']).read_bytes();actual=hashlib.sha256(raw).hexdigest();hashes.append({'path':r['path'],'bytes':len(raw),'sha256':actual})
  if actual!=expected:errors.append('採用bytes変更:'+r['id'])
 # 親台帳・本番コード・保存・世界データ・既存検査の不変をGit基点で検査。
 changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
 existing=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines())
 changed_existing=[x for x in changed if x in existing]
 if changed_existing!=['assets/registry.json']:errors.append('既存差分範囲:'+str(changed_existing))
 original=json.loads(subprocess.check_output(['git','show',BASE+':assets/registry.json'],cwd=ROOT))
 current=json.loads((ROOT/'assets/registry.json').read_text());paths={r['path'] for r in d['rooms']}
 added=[x for x in current['assets'] if x['path'] in paths]
 current['assets']=[x for x in current['assets'] if x['path'] not in paths]
 if current!=original or len(added)!=5:errors.append('台帳既存不変')
 report={'base':BASE,'source':SOURCE,'errors':errors,'negative':negative,'hashes':hashes,'rooms':[{'id':r['id'],'floors':sum(row.count('.') for row in r['layout'])} for r in d['rooms']]}
 (out/'structure.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (out/'probes.json').write_text(json.dumps(PROBES,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
