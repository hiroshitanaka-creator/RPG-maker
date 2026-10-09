"""最新CIの原archiveを変更せず、全受付・共有batch・実log bytesを独立照合する。"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

E=Path(__file__).resolve().parents[1]
CODE='55a56d09d7c74becaeacdecede16836d93ba8cbc'

def audit(name,code=CODE,source=None,require_setup=False):
    path=E/(name+'.tar.gz');catalog=next(r for r in json.loads((E/'archives.json').read_bytes()) if r['archive']==path.name)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==catalog['raw_sha256']
    with tarfile.open(path) as tar:
        # gzipの同じ先頭から受付ごとに再展開せず、照合対象原bytesだけを一巡で読む。
        labels=['capture-tests','scope059','capture059','baseline058','measurements']
        exact={'evidence/task059/'+p for p in ('execution.json','scope.json','capture-tests/tests.json','capture059/tests.json','baseline058/counterexamples.json')}
        for label in labels+['baseline-checkout']:
            exact.update('evidence/task059/'+label+suffix for suffix in ['-process.json','.log'])
        payload={}
        for member in tar:
            selected=member.name in exact or (member.name.startswith('evidence/results/') and member.name.endswith(('-execution.json','.log','restart-queue.json','summary.json')))
            if selected and (member.isfile() or member.islnk()):payload[member.name]=tar.extractfile(member).read()
        # 原recordのWindows区切りをtar memberのPOSIX表記へ対応させる。JSON原値は変更しない。
        def raw(path):return payload[path.replace('\\','/')]
        def data(path):return json.loads(raw(path))
        execution=data('evidence/task059/execution.json');assert execution['code_sha']==code and execution['status']=='PASS'
        if source is not None:assert execution['source_sha']==source
        assert [row['label'] for row in execution['commands']]==labels
        expected_budgets=dict(zip(labels,[180,30,180,30,180]));expected_budgets['baseline-checkout']=30
        if require_setup:assert execution['schema']==2 and [row['label'] for row in execution['setup']]==['baseline-checkout']
        for row in execution.get('setup',[])+execution['commands']:
            label=row['label'];assert row['exit_code']==0 and row['supervision']['stopped'] is True and row['budget_seconds']==expected_budgets[label]
            assert {k:v for k,v in row.items() if k!='label'}==data('evidence/task059/'+label+'-process.json')
            assert hashlib.sha256(raw('evidence/task059/'+label+'.log')).hexdigest()==row['log_sha256']
        scope=data('evidence/task059/scope.json');assert scope['code_sha']==code and scope['source_sha']==execution['source_sha']
        assert len(scope['propagation'])==10 and all(r['exit_code']==r['expected_exit'] for r in scope['propagation'])
        counts={}
        for folder,count in [('capture-tests',12),('capture059',27)]:
            result=data('evidence/task059/'+folder+'/tests.json')
            assert result['status']=='PASS' and len(result['cases'])==count and all(r['status']=='PASS' for r in result['cases'])
            counts[folder]=count
        before=data('evidence/task059/baseline058/counterexamples.json')
        assert before['source_sha']=='579ca1f463aaf9e93275039a59cf9d1ffb86adb5'
        assert before['f5a']['execution_records']==0 and before['f5a']['queue']['recovery_complete'] is True
        assert before['f5b']['grandchild_executing_after_outer_kill'] is True
        prefix='evidence/results/';q=data(prefix+'restart-queue.json')
        assert q['recovery_complete'] is True and not q['live_workers'] and not q['pending_futures'] and not q['evidence_errors'] and not q['unreaped_process_records']
        identities=set();batches=set();started=0;unstarted=0
        for request in q['requests']:
            identity=request['request_id'];assert identity not in identities;identities.add(identity)
            row=data(prefix+request['planned_record'])
            assert row==request['terminal_row']==data(prefix+request['planned_projection'])
            assert row['terminal'] is True and row['request_id']==identity and row['batch_id']==request['batch_id'] and row['planned_record']==request['planned_record']
            assert not request.get('record_error') and request.get('future_done') is not False
            if row['pid'] is None:
                unstarted+=1
                assert all(row.get(k) is None for k in ('argv','log','exit_code','started_utc','started_monotonic')) and row['exit_unavailable_reason']
            else:
                started+=1
                assert row['argv'] and row['exit_code'] is not None and row['wait']['ok'] is True and row['supervision']['stopped'] is True
                assert hashlib.sha256(raw(prefix+row['log'])).hexdigest()==row['log_sha256']
            if row.get('batch_record'):
                batch=data(prefix+row['batch_record']);assert batch==request['batch_terminal_row']
                assert batch['terminal'] is True and batch['batch_id']==request['batch_id'] and identity in batch['request_ids'] and batch['pid']==row['pid']
                if row['pid'] is not None:
                    batchlog=row['batch_record'].removesuffix('-execution.json')+'.log'
                    assert raw(prefix+batchlog)==raw(prefix+row['log'])
                batches.add(row['batch_record'])
        summary=data(prefix+'summary.json')
        return dict(status='PASS',archive=path.name,raw_sha256=catalog['raw_sha256'],head_sha=execution['source_sha'],code_sha=code,platform=before['platform'],checks=counts,scope_cases=10,diagnostic_setup_required=require_setup,diagnostic_process_records_and_logs_match=True,requests=len(identities),started_request_rows=started,unstarted_request_rows=unstarted,unique_batch_records=len(batches),receipt_records_and_log_bytes_match=True,recovery_complete=True,transaction=dict(status=summary['status'],cases=summary['case_count'],checks=summary['checks'],seconds=summary['seconds']),note='受付数と共有process数は別。取引の成功を回収成功で補完しない')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('names',nargs='+');p.add_argument('--output',required=True);p.add_argument('--code-sha',default=CODE);p.add_argument('--source-sha');p.add_argument('--require-setup',action='store_true');a=p.parse_args();rows=[audit(name,a.code_sha,a.source_sha,a.require_setup) for name in a.names];Path(a.output).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rows,ensure_ascii=False))
