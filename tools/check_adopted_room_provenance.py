#!/usr/bin/env python3
"""080の限定承認を検証する。原画への書込み・複製・既存検査の変更をしない。"""
from pathlib import Path
from unittest import mock
import argparse,copy,hashlib,importlib.util,json,subprocess,types
import validate_assets as current
import check_adopted_room_foundation as foundation

ROOT=Path(__file__).resolve().parent.parent
BASE='e677896d3e61b8fe8136ef60c5c76f41ad76701d'
PREVIOUS='19f0ef9e08b546ad3b9d9143e5b6b97e59ba6d31'
SOURCE='84f446e48cbaef2a199da1d464311992daf13938'
# 承認された固定PRの原画パス/SHA。実装の辞書から期待値を生成しない。
EXPECTED={
 'assets/_incoming/owner-2026-10-04-grok-region3-rooms/region3-room-inn.png':'abc509dd6cecd1eccf94fd7139032f30c97061384ff3353838537bf9f30e5b25',
 'assets/_incoming/owner-2026-10-04-grok-region3-rooms/region3-room-item-shop.png':'ef7d8b0f92ffef7cc08079a83307736231882e26e9e654fa2474e6e93f441abf',
 'assets/_incoming/owner-2026-10-04-grok-region3-rooms/region3-room-weapon-shop.png':'f0dacceef429dd73a3eef411da1aa409fb52d0a043c153324ca9f1e4971c6310',
 'assets/_incoming/owner-2026-10-04-grok-region3-rooms/region3-room-shrine.png':'f826665f70b18404e118a2c4b654cd70797ad812297fe57f890409ec60e223e2',
 'assets/_incoming/owner-2026-10-04-grok-region3-rooms/region3-room-armor-shop.png':'cf21d589f47cbdf128c9d6e79094334a5a8da67f3ee5f71d76f0a207b6161fe6',
}

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
 checks=[]
 def check(ok,label,details=None):
  checks.append({'ok':bool(ok),'case':label,'details':details})
  if not ok:print('PROVENANCE_FAIL:',label,details)
 baseline_code=git('show',BASE+':tools/validate_assets.py')
 prior_code=git('show',PREVIOUS+':tools/validate_assets.py')
 actual_code=(ROOT/'tools/validate_assets.py').read_bytes()
 check(baseline_code==prior_code,'old-candidate-validator-is-base')
 # 最新基点からの2箇所限定差分が固定PRの差分と同一。全ファイル置換の主張には使わない。
 expected_delta=git('diff',BASE,SOURCE,'--','tools/validate_assets.py')
 actual_delta=git('diff',BASE,'--','tools/validate_assets.py')
 check(actual_delta==expected_delta,'exact-approved-validator-delta',{'sha256':hashlib.sha256(actual_delta).hexdigest()})
 check(current.OWNER_ADOPTED_ROOM_ORIGINALS==EXPECTED,'exact-five-path-hash-whitelist')
 old=types.ModuleType('baseline_asset_validator');old.__file__=str(ROOT/'tools/validate_assets.py')
 exec(compile(baseline_code,'<unchanged-baseline-validate_assets.py>','exec'),old.__dict__)
 registry=json.loads((ROOT/'assets/registry.json').read_text())
 adopted=[x for x in registry['assets'] if x.get('original_file') in EXPECTED]
 check(len(adopted)==5,'five-adopted-entries')
 raw={name:(ROOT/name).read_bytes() for name in EXPECTED}
 originals_before={name:hashlib.sha256(b).hexdigest() for name,b in raw.items()}
 check(originals_before==EXPECTED,'five-real-originals-exist-and-hash-match',originals_before)
 read_bytes=Path.read_bytes;is_file=Path.is_file
 other_file='assets/_incoming/owner-2026-10-04-grok-region3-rooms/region3-room-harbor-office.png'
 check((ROOT/other_file).is_file(),'unapproved-same-folder-file-really-exists')
 for entry in adopted:
  name=entry['original_file'];p=ROOT/name
  check(not current.check_provenance(entry),'real-positive:'+name)
  check(bool(old.check_provenance(entry)),'old-rejection-retained-in-evidence:'+name)
  for label,value in [
   ('unapproved-other-file',other_file),
   ('traversal',str(Path(name).parent/'..'/Path(name).parent.name/Path(name).name)),
   ('noncanonical-double-slash',name.replace('/region3-room-','//region3-room-')),
   ('wrong-path',name.replace('owner-2026-10-04','owner-2026-10-05')),
  ]:
   bad=copy.deepcopy(entry);bad['original_file']=value;errors=current.check_provenance(bad)
   check(bool(errors),label+':'+name,{'input_path':value,'errors':errors})
  changed=bytes([raw[name][0]^1])+raw[name][1:]
  other=next(v for k,v in raw.items() if k!=name)
  for label,body in [('modified-hash',changed),('other-original-bytes',other)]:
   # ファイルシステム読取の観測だけを置換する。原画本体は1バイトも変更しない。
   reads=[]
   def observed_read(path):
    reads.append(str(path));return body if path==p else read_bytes(path)
   with mock.patch.object(Path,'read_bytes',autospec=True,side_effect=observed_read):errors=current.check_provenance(entry)
   check(bool(errors) and str(p) in reads,label+':'+name,{'observed_sha256':hashlib.sha256(body).hexdigest(),'expected_sha256':EXPECTED[name],'read_paths':reads,'errors':errors,'fixture':'memory-only read observation; no original write/copy'})
  def observed_exists(path):return False if path==p else is_file(path)
  with mock.patch.object(Path,'is_file',autospec=True,side_effect=observed_exists):errors=current.check_provenance(entry)
  check(bool(errors),'missing-original:'+name,{'errors':errors,'fixture':'memory-only is_file=False observation'})
  for field in ['author','provided_at','original_file','modified','license']:
   bad=copy.deepcopy(entry);bad.pop(field,None);errors=current.check_provenance(bad)
   check(bool(errors),'required-owner-field:'+name+':'+field,errors)
  for field,value in [('author','別の作者'),('license','CC0-1.0')]:
   bad=copy.deepcopy(entry);bad[field]=value;errors=current.check_provenance(bad)
   check(bool(errors),'owner-mismatch:'+name+':'+field,errors)
 # 5件以外の画像・音・字体の出所判定結果は、全実エントリで旧判定と一致する。
 other_count=0;owner_count=0
 for category in ['assets','audio','fonts']:
  for entry in registry[category]:
   if entry in adopted:continue
   before=old.check_provenance(entry);after=current.check_provenance(entry);other_count+=1
   check(after==before,'existing-entry:'+entry['path'],{'baseline':before,'candidate':after})
   if entry.get('source')!='owner':continue
   owner_count+=1
   for field in ['author','provided_at','original_file','modified','license']:
    bad=copy.deepcopy(entry);bad.pop(field,None);b=old.check_provenance(bad);c=current.check_provenance(bad)
    check(bool(c) and c==b,'legacy-owner-missing-field:'+entry['path']+':'+field,{'baseline':b,'candidate':c})
   for field,value in [('author','別の作者'),('license','CC0-1.0'),('original_file','assets/_incoming/owner-2026-09-26/../missing.png'),('original_file','assets/_incoming/owner-2026-09-26/__missing_080__.png')]:
    bad=copy.deepcopy(entry);bad[field]=value;b=old.check_provenance(bad);c=current.check_provenance(bad)
    check(bool(c) and c==b,'legacy-owner-invalid:'+entry['path']+':'+field+':'+value,{'baseline':b,'candidate':c})
 check({name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED}==EXPECTED,'real-original-bytes-unchanged-after-negative-tests')
 # 旧段階の厳密な範囲チェックは元の固定treeで実行する。現在は承認2ファイル以外の旧候補bytesを全件保持。
 changes=[]
 for item in git('ls-tree','-r','-z',PREVIOUS).split(b'\0'):
  if not item:continue
  meta,name=item.split(b'\t',1);path=name.decode();expected_blob=meta.split()[2].decode();body=(ROOT/path).read_bytes()
  actual_blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
  if actual_blob!=expected_blob:changes.append(path)
 check(sorted(changes)==['docs/tasks/reports/080-adopted-room-walking-foundation.md','tools/validate_assets.py'],'previous-candidate-preservation-except-approved-change-and-report',changes)
 definition=json.loads((ROOT/'world/adopted_room_foundation.json').read_text())
 check(not foundation.inspect(definition),'foundation-continuing-structure')
 negatives=[]
 for label,mutate in [
  ('missing-room',lambda d:d['rooms'].pop()),
  ('wrong-image',lambda d:d['rooms'][1].update(path=d['rooms'][0]['path'])),
  ('furniture-pass',lambda d:d['rooms'][1]['layout'].__setitem__(8,'##..........##')),
  ('closed-entry',lambda d:d['rooms'][0]['layout'].__setitem__(10,'##############')),
  ('unapproved-world-link',lambda d:d['rooms'][0].update(world_connection='world'))]:
  bad=copy.deepcopy(definition);mutate(bad);errors=foundation.inspect(bad);negatives.append({'case':label,'errors':errors});check(bool(errors),'foundation-negative:'+label,errors)
 for room,expected in zip(definition['rooms'],foundation.HASHES):check(hashlib.sha256((ROOT/room['path']).read_bytes()).hexdigest()==expected,'adopted-image-bytes:'+room['id'])
 # 台帳5件の出所も前候補から一切変更しない。
 check((ROOT/'assets/registry.json').read_bytes()==git('show',PREVIOUS+':assets/registry.json'),'registry-provenance-unchanged')
 result={'base':BASE,'previous_candidate':PREVIOUS,'source':SOURCE,'checks':checks,'failed':sum(not c['ok'] for c in checks),'other_actual_entries_compared':other_count,'legacy_owner_entries_compared':owner_count,'original_hashes':originals_before,'foundation_negatives':negatives}
 (out/'provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 (out/'probes.json').write_text(json.dumps(foundation.PROBES,ensure_ascii=False,indent=2)+'\n')
 print('ADOPTED_PROVENANCE: checks=%d failed=%d other_entries=%d legacy_owner=%d'%(len(checks),result['failed'],other_count,owner_count))
 return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
