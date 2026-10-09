"""保存原archive内の結果を参照つきで要約する。成功を追加判定せず原値を転記する。"""
from pathlib import Path
import json
import tarfile

E=Path(__file__).resolve().parents[1]
rows=[]
for archive in json.loads((E/'archives.json').read_bytes()):
    if not archive['archive'].startswith(('astra-','ci-')):continue
    result=dict(archive=archive['archive'],raw_sha256=archive['raw_sha256'],results=[])
    with tarfile.open(E/archive['archive']) as tar:
        for member in tar:
            path=member.name
            if not (member.isfile() or member.islnk()) or not path.endswith('.json'):continue
            wanted=(path=='tests.json' or path in ('evidence/task059/capture-tests/tests.json','evidence/task059/capture059/tests.json','evidence/task059/execution.json','evidence/task059/baseline058/counterexamples.json','evidence/results/summary.json','results/summary.json','evidence/results/restart-queue.json','results/restart-queue.json'))
            if not wanted:continue
            value=json.loads(tar.extractfile(member).read());entry={'member':path}
            for key in ('source_sha','code_sha','status','case_count','checks','seconds','recovery_complete','live_workers','pending_futures','evidence_errors','unreaped_process_records','failures'):
                if key in value:entry[key]=value[key]
            if 'requests' in value:entry['request_count']=len(value['requests'])
            if path.endswith('tests.json'):entry['cases']=[{k:r[k] for k in ('case','status','seconds','exception') if k in r} for r in value['cases']]
            if 'commands' in value:entry['commands']=[dict(label=r.get('label'),argv=r['argv'],seconds=r['seconds'],exit_code=r['exit_code'],supervision_stopped=r.get('supervision',{}).get('stopped')) for r in value['commands']]
            if 'f5a' in value:
                entry['f5a']=dict(exception=value['f5a']['exception'],execution_records=value['f5a']['execution_records'],recovery_complete=value['f5a']['queue']['recovery_complete'])
                entry['f5b']=dict(grandchild_executing_after_outer_kill=value['f5b']['grandchild_executing_after_outer_kill'],scope=value['f5b']['scope'])
            result['results'].append(entry)
    rows.append(result)
(E/'proof-summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print('原archive参照つき要約',len(rows))
