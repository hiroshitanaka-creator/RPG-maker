from pathlib import Path
import json,hashlib,statistics
T=Path('/tmp/qa057');E=Path('/workspace/RPG-maker/docs/verification/task057-save-qa-diagnostics')
def read(p):return json.loads(p.read_bytes())
def union(rows):
 rows=sorted(rows);last=None;total=0
 for a,b in rows:
  if last is None:last=(a,b)
  elif a<=last[1]:last=(last[0],max(last[1],b))
  else:total+=last[1]-last[0];last=(a,b)
 if last:total+=last[1]-last[0]
 return total
summaries=[]
for folder in sorted(T.glob('ci-*-verified')):
 if not (folder/'evidence').exists():continue
 row={'evidence':folder.name,'archive_sha256':read(folder/'archive-meta.json')['archive_sha256']}
 cmd=folder/'evidence/commands.json'
 if cmd.exists():row['wrapper_commands']=[{k:x.get(k) for k in ['name','argv','seconds','exit_code','timed_out','timeout_kind']} for x in read(cmd)]
 build=folder/'evidence/build/build.json'
 if build.exists():row['build']=read(build)
 diag=folder/'evidence/task057/measurements/diagnostics.json'
 if diag.exists():
  d=read(diag);row.update({'diagnostic_source_sha':d['source_sha'],'environment':d['environment'],'diagnostic_status':d['status'],'diagnostic_wall_seconds':d['wall_seconds'],'seed_pairs':[]})
  for seed in sorted({x['seed'] for x in d['samples']}):
   xs=[x for x in d['samples'] if x['seed']==seed];on=next(x for x in xs if x['mode']=='on');off=next(x for x in xs if x['mode']=='off');r=on['raw'];t=on['timing'];labels=t['labels']
   row['seed_pairs'].append({'seed':seed,'control_output_equal':on['raw']['output_sha256']==off['raw']['output_sha256'],'control_quantity_equal':on['raw']['quantity']==off['raw']['quantity'],'memory_unchanged':r['memory_unchanged'] and off['raw']['memory_unchanged'],'off_execution_seconds':off['execution_seconds'],'on_execution_seconds':on['execution_seconds'],'on_child_initialize_enter_seconds':r['initialize_enter_us']/1e6,'on_dependency_seconds':(r['dependency_end_us']-r['dependency_start_us'])/1e6,'transaction_wall_seconds':t['transaction_wall_us']/1e6,'plan_verify_union_seconds':t['plan_verify_union_us']/1e6,'plan_verify_percent':t['plan_verify_union_us']/t['transaction_wall_us']*100,'native_overlap_union_seconds':t['native_union_us']/1e6,'labels':labels})
  row['acceptance']='diagnostic sample only; not 172/2178/97kill'
 results=folder/'evidence/results';q=results/'restart-queue.json'
 if q.exists():
  v=read(q);requests=v['requests'];waits=[x['worker_started']-x['queued'] for x in requests if x.get('worker_started') is not None];timing=read(results/'timing.json');snaps=timing['observations'];batches=[read(p) for p in sorted((results/'batches').glob('*-execution.json'))]
  row['full_suite_timing']={'queue_requests':len(requests),'unique_batches':len(batches),'queue_wait_cumulative_seconds':sum(waits),'queue_wait_max_seconds':max(waits,default=0),'snapshot_count':len(snaps),'snapshot_cumulative_seconds':sum(x['end']-x['start'] for x in snaps),'snapshot_wall_union_seconds':union([(x['start'],x['end']) for x in snaps]),'batch_process_cumulative_seconds':sum(x['seconds'] for x in batches),'batch_process_wall_union_seconds':union([(x['started_monotonic'],x['ended_monotonic']) for x in batches]),'live_workers':v['live_workers'],'recovery_complete':v['recovery_complete'],'unreaped_process_records':v.get('unreaped_process_records'),'warning':'Cumulative parallel intervals and projected per-root batch records must not be added to suite wall-time.'}
 summaries.append(row)
(E/'measurement-summary.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'evidence':x['evidence'],'pairs':len(x.get('seed_pairs',[])),'queue':x.get('full_suite_timing')} for x in summaries],ensure_ascii=False))
