from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,gzip,shutil,subprocess
r=Path(__file__).resolve().parent;repo=r/'repo';dest=repo/'docs/verification/task-080-formal-save-20261027';out=r/'verification-2';state=json.loads((r/'state.json').read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=repo)
records=json.loads((out/'execution.json').read_text());assert all(x['exit_code']==0 for x in records)
assert records[0]['name']=='00-editor-import' and all(records[0]['ended_at_utc']<=x['started_at_utc'] for x in records[1:])
locked=json.loads((out/'locked-results.json').read_text());assert len(locked)==8 and all(x['status']=='PASS' for x in locked)
rooms=[]
for n in ['inn','item_shop','weapon_shop','shrine','armor_shop']:
 d=json.loads((out/('render-'+n+'.json')).read_text());assert d['failed']==0;rooms.append({'room':n,'checks':len(d['checks']),'inputs':len(d['inputs']),'failed':d['failed']})
assert sum(x['checks'] for x in rooms)==1191 and sum(x['inputs'] for x in rooms)==1862
def save_raw(p,target):
 target.parent.mkdir(parents=True,exist_ok=True);raw=p.read_bytes()
 if p.suffix=='.log':target=target.with_name(target.name+'.gz');packed=gzip.compress(raw,mtime=0);assert gzip.decompress(packed)==raw;target.write_bytes(packed)
 else:target.write_bytes(raw)
for folder,label in [(r/'verification','failed-runner-attempt'),(out,'latest-runtime')]:
 for p in folder.rglob('*'):
  if p.is_file():save_raw(p,dest/label/p.relative_to(folder))
for n in ['verification-driver.log','verification-2-driver.log','prepare.log','prepare-driver.log','snapshot-push.log','verify.py','finalize.py','collect_handoff.py']:
 save_raw(r/n,dest/n)
restored=[]
for name in filter(None,git('diff','--name-only','-z').decode().split('\0')):
 assert name.startswith('docs/verification/'),name
 p=repo/name;save_raw(p,dest/'generated-tracked-output'/name)
 original=git('show','HEAD:'+name);p.write_bytes(original);restored.append(name)
protected=[]
for x in json.loads((repo/'.scope-lock/frozen-files.json').read_text())['files']:
 name=x['path'];sha=hashlib.sha256((repo/name).read_bytes()).hexdigest();base=hashlib.sha256(git('show',state['base']+':'+name)).hexdigest();latest=hashlib.sha256(git('show',state['latest_main']+':'+name)).hexdigest()
 assert sha==base==latest==x['sha256'];protected.append({'path':name,'base_sha256':base,'latest_main_sha256':latest,'candidate_sha256':sha,'frozen_sha256':x['sha256']})
assert len(protected)==26
(dest/'protected-26-sha256.json').write_text(json.dumps(protected,indent=2)+'\n')
assert not git('diff',state['latest_main'],'--','docs/decision-log.md','docs/tasks/README.md')
entries=json.loads((r/'planned-files.json').read_text())
for e in entries:assert hashlib.sha256((repo/e['path']).read_bytes()).hexdigest()==e['sha256'],e['path']
summary={'tested_commit':state['integrated_commit'],'snapshot_commit':state['snapshot_commit'],'latest_main':state['latest_main'],'records':len(records),'all_exit_zero':True,'import_first':True,'strict_images':1159,'rooms':rooms,'checks':1191,'inputs':1862,'locked_all_pass':True,'protected_files':26,'original_payload_preserved':378,'parent_ledgers_exact_latest_main':True,'restored_generated_tracked_outputs':restored,'ci':'server workflow runs must be checked on final pushed SHA; not inferred from local success','draft_pr':'rejected by auto-review; not created'}
(dest/'local-results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
report=repo/'docs/tasks/reports/080-formal-save-20261027.md'
report.write_text('''# 080 専用ブランチへの正式保存\n\n元ZIP: 164546599 bytes、SHA256 f7d97291e6458b820303434267d2c26bfe39e229b6e8d8d8e3f75975d0fb8019。元ZIP・旧ZIP・原画は保持。\n\n原候補の不変保存: `'''+state['snapshot_commit']+'''`、tree `524b72d4cb8682b4d77197a9934defea247a199e`、ブランチ codex/task-080-original-20261027。全378payloadと一致、親台帳変更なし。\n\n最新main `'''+state['latest_main']+'''` を通常mergeした検証対象: `'''+state['integrated_commit']+'''`。mainのcoastal修正・原証拠・親台帳追記を全件保持。統合後は新しい引渡し資料と本報告だけを追加し、制作・既存検査の変更はしていない。mainへpush/mergeしていない。PR49やPR2には触れていない。\n\nimport先行で素材strict1159件・5室1191判定1862入力・R01〜08・保護26を再実行し全成功。修正済みcoastal境界・保存位置復旧・第2地方海岸・港も全exit0。全コマンド・cwd・上限・UTC開始終了・exit・原ログSHAはlatest-runtime/execution.json。旧080の正負例や3737出所判定は原候補の原記録を保持し、今回のlatest-runtime/current-integrity.jsonで現候補378件一致・構造正負例・main全保持を照合。\n\n初回runnerはgitの日本語パス引用を扱えずFileNotFoundErrorとなった。失敗原ログを保持し、外部runnerのみNUL区切りへ修正。新しいverification-2でimportから再実行した。ゲーム・保護・既存検査器は変更していない。\n\n元ZIP全419項目はoriginal-archive-map.jsonでGitパスへ対応。payload378件は元パス、追加41項目は原bytesまたは可逆gzip。rebuild_original_zip.pyで再構成し、元ZIPの全bytes/SHA一致を実測した。旧ZIP2本も原bytes収録。全ファイル一覧と各SHAは同ディレクトリのformal-change-files.jsonとSHA256SUMS.json。\n\nCIは最終push SHAのGitHub Actions全workflow/jobの結果を親へ別途報告する。ローカル成功をCI成功としていない。Libraryは未保存。draft PR作成は自動承認レビューが「正式PR作成は親担当」として拒否し未実行。別経路による作成はしない。承認・正式検収・マージは親担当。全ゲーム完成・本番進行接続ではない。\n\n引渡し資料: docs/verification/task-080-formal-save-20261027/README.md\n''')
paths=sorted([str(p.relative_to(repo)) for p in dest.rglob('*') if p.is_file()]+[str(report.relative_to(repo))]+['docs/verification/task-080-formal-save-20261027/formal-change-files.json','docs/verification/task-080-formal-save-20261027/SHA256SUMS.json'])
all_changes=sorted(set(git('diff','--name-only',state['latest_main']).decode().splitlines()+paths))
(dest/'formal-change-files.json').write_text(json.dumps(all_changes,ensure_ascii=False,indent=2)+'\n');(r/'formal-planned-files.txt').write_text('\n'.join(all_changes)+'\n')
manifest={str(p.relative_to(repo)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
(dest/'SHA256SUMS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
git('add','--',str(dest.relative_to(repo)),str(report.relative_to(repo)));git('diff','--cached','--check')
assert all(x.startswith(('docs/verification/task-080-formal-save-20261027/','docs/tasks/reports/080-formal-save-20261027.md')) for x in git('diff','--cached','--name-only').decode().splitlines())
print(json.dumps({'local_results':summary,'formal_changed_files':len(all_changes),'staged_files':len(git('diff','--cached','--name-only').decode().splitlines()),'ready_for_commit':True},ensure_ascii=False))
