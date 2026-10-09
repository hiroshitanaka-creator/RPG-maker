"""059実process/Future/原record正負検証。057の12検証は別に全て維持する。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from unittest.mock import patch
from process_capture import ProcessCapture, save
ROOT=Path(__file__).resolve().parents[3]
FIXTURE=Path(__file__).with_name('tree_fixture059.py')
BATCH_FIXTURE=Path(__file__).with_name('capture_fixture.py')


def driver():
    spec=importlib.util.spec_from_file_location('driver059',ROOT/'tools/check_equipment_save_transaction_platform.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def main(args):
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False);rows=[];d=driver()
    def record(name,fn):
        start=time.monotonic()
        try:
            evidence=fn()
            rows.append(dict(case=name,status='PASS',seconds=time.monotonic()-start,evidence=evidence))
        except Exception as exc:rows.append(dict(case=name,status='FAIL',seconds=time.monotonic()-start,exception=repr(exc)))
        save(output/'tests.json',dict(platform=sys.platform,argv=sys.argv,cases=rows,status='FAIL' if any(r['status']=='FAIL' for r in rows) else 'PASS',scope='059 dedicated capture; 全取引と実174/180秒境界ではない'))
    def suite(name):
        class CapturedSuite(d.Suite):
            def capture(self,argv,log,record,env):
                return super().capture([sys.executable,str(BATCH_FIXTURE),'batch',argv[-1]],log,record,env)
        value=CapturedSuite(argparse.Namespace(godot=sys.executable,fixture_root=str(output/(name+'-qa')),output=str(output/(name+'-results'))))
        value.deadline=time.monotonic()+3;value.cleanup_deadline=value.deadline
        root=value.area/'root';root.mkdir();return value,root
    def prelaunch(name,stage,direct=False):
        value,root=suite(name);error=None
        if stage=='config':(root/'restarted-batch.json').mkdir()
        if stage=='queue-config':(root/'first-config.json').mkdir()
        if stage=='env':value.env=lambda _:(_ for _ in ()).throw(OSError('env準備fixture失敗'))
        if stage=='capture':value.capture=lambda *a:(_ for _ in ()).throw(OSError('capture構築fixture失敗'))
        if stage=='log':(value.output/'batches/batch-000000.log').mkdir(parents=True)
        if stage=='capture-record':(value.output/'batches/batch-000000-execution.json').mkdir(parents=True)
        if stage=='request-record':(value.output/'requests/request-000000-execution.json').mkdir(parents=True)
        if stage=='unstarted-batch-record':
            value.env=lambda _:(_ for _ in ()).throw(OSError('env準備fixture失敗'))
            (value.output/'batches/batch-000000-execution.json').mkdir(parents=True)
        try:
            if direct:value.run(root,dict(root=str(root)), 'first')
            else:value.restarts.submit(root,dict(root=str(root),operation='normal'))
        except Exception as exc:error=repr(exc)
        assert error
        value.restarts.close();queue=d.load(value.output/'restart-queue.json');request=queue['requests'][0];row=request['terminal_row']
        if stage not in ('request-record',):
            saved=d.load(value.output/request['planned_record']);assert saved==row
        if stage in ('capture-record','request-record','unstarted-batch-record'):
            assert not queue['recovery_complete'] and queue['evidence_errors']
        else:assert queue['recovery_complete'],queue['evidence_errors']
        assert row['request_id']==request['request_id'] and row['terminal'] and row['ended_utc']
        if stage!='request-record':
            assert row['pid'] is None and row['argv'] is None and row['log'] is None and row['exit_code'] is None and row['exit_unavailable_reason']
        assert not request['completed']
        return dict(error=error,queue=queue)
    for stage in ['config','env','capture','log','capture-record','request-record','unstarted-batch-record']:
        record('prelaunch-'+stage,lambda stage=stage:prelaunch(stage,stage))
    record('suite-run-queue-before-config',lambda:prelaunch('queue-config','queue-config',direct=True))
    def four_roots():
        value,first=suite('four');roots=[first]+[value.area/('root-'+str(i)) for i in range(1,4)]
        for r in roots[1:]:r.mkdir()
        # 実queueをまとめて投入し、同じ4root batchを確実に検証（worker/batch数変更なし）。
        gate=threading.Barrier(4)
        def submit(r):gate.wait();return value.restarts.submit(r,dict(root=str(r),operation='normal'))
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(submit,roots))
        errors,unreaped=value.reconcile_requests()
        assert not errors and not unreaped and len({r['request_id'] for r in value.accepted})==4
        batches={r['batch_id'] for r in value.accepted}
        # 複数workerへ分散するraceも記録。4root共有batchはrun_restart_batchへ実4rootを別途渡す。
        direct=[]
        for i in range(4):
            r=value.area/('shared-'+str(i));r.mkdir();request=value.accept_request(r,dict(root=str(r),operation='normal'),'restarted')
            now=time.monotonic();request.update(batch_id='four-shared',worker_started=now,batch_started=now);direct.append(request)
        shared=value.run_restart_batch(direct,'four-shared');value.restarts.close();q=d.load(value.output/'restart-queue.json')
        assert q['recovery_complete'] and len(shared)==4
        batch=d.load(value.output/'batches/four-shared-execution.json')
        assert len(batch['request_ids'])==4 and len(set(batch['request_ids']))==4
        for request,row in zip(direct,shared):
            assert row['request_id']==request['request_id'] and row['pid']==batch['pid']
            assert (value.output/row['log']).read_bytes()==Path(batch['log']).read_bytes()
        return dict(queue=q,queued_batches=sorted(batches),shared_batch=batch)
    record('four-root-shared-batch',four_roots)
    def damage(name):
        value,root=suite('damage-'+name)
        if name=='unstarted-batch':
            (root/'restarted-batch.json').mkdir()
            try:value.restarts.submit(root,dict(root=str(root),operation='normal'))
            except OSError:pass
            else:raise AssertionError('実config失敗が必要')
        else:value.restarts.submit(root,dict(root=str(root),operation='normal'))
        value.restarts.close()
        request=value.accepted[0];path=value.output/request['planned_record'];original=path.read_bytes()
        if name=='missing':path.rename(path.with_suffix('.saved'))
        elif name=='broken':path.write_bytes(b'{broken')
        elif name=='id':row=d.load(path);row['request_id']='different-ID';save(path,row)
        elif name=='batch':row=d.load(value.output/'batches/batch-000000-execution.json');row['request_ids']=[];save(value.output/'batches/batch-000000-execution.json',row)
        elif name in ('batch-content','unstarted-batch'):
            row=d.load(value.output/'batches/batch-000000-execution.json');row['exception']='原batch改変';save(value.output/'batches/batch-000000-execution.json',row)
        value.restarts.close();q=d.load(value.output/'restart-queue.json')
        assert not q['recovery_complete'] and q['evidence_errors']
        # 照合失敗は親へ非0。記録の存在だけで成功にしない。
        forged=dict(q,recovery_complete=True,evidence_errors=[])
        save(value.output/'forged-complete.json',forged)
        argv=[sys.executable,__file__,'--inventory-check',str(value.output/'forged-complete.json')]
        p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        assert p.returncode==1;pout=value.output/'damage-validation.log';pout.write_bytes(p.stdout)
        return dict(queue=q,expected_exit=1,exit_code=p.returncode,argv=argv,original_sha256=__import__('hashlib').sha256(original).hexdigest())
    for name in ['missing','broken','id','batch','batch-content','unstarted-batch']:record('record-'+name,lambda name=name:damage(name))
    def concurrent_close():
        value,root=suite('concurrent-close');value.restarts.submit(root,dict(root=str(root),operation='normal'))
        with ThreadPoolExecutor(max_workers=4) as pool:assert all(not v for v in pool.map(lambda _:value.restarts.close(),range(4)))
        first=(value.output/'requests/request-000000-execution.json').read_bytes();value.restarts.close()
        assert (value.output/'requests/request-000000-execution.json').read_bytes()==first
        q=d.load(value.output/'restart-queue.json');assert q['recovery_complete'];return q
    record('close-race-and-repeated',concurrent_close)
    def accepting_during_close():
        value,root=suite('accept-close');entered=threading.Event();release=threading.Event();closing=threading.Event()
        original=value.planned_argv
        def paused_argv(path):
            entered.set();assert release.wait(timeout=2);return original(path)
        value.planned_argv=paused_argv
        def close():closing.set();return value.restarts.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            accepted=pool.submit(value.accept_request,root,dict(root=str(root)),'restarted')
            assert entered.wait(timeout=1)
            closed=pool.submit(close);assert closing.wait(timeout=1)
            try:
                try:closed.result(timeout=.2)
                except TimeoutError:blocked=True
                else:blocked=False
            finally:release.set()
            request=accepted.result(timeout=1);closed.result(timeout=1)
        q=d.load(value.output/'restart-queue.json')
        assert blocked and len(q['requests'])==1 and q['requests'][0]['request_id']==request['request_id']
        assert not q['recovery_complete'] and q['evidence_errors'],'受付途中を存在しない扱いにしない'
        return dict(queue=q,close_waited_for_acceptance=blocked)
    record('acceptance-close-race',accepting_during_close)
    def process_tree(name,mode,zero=False,fail=False):
        area=output/name;area.mkdir();sentinel_area=area/'sentinel';sentinel_area.mkdir()
        sentinel=subprocess.Popen([sys.executable,str(FIXTURE),'--mode','sentinel','--area',str(sentinel_area)])
        cap=None
        try:
            until=time.monotonic()+2
            while not (sentinel_area/'sentinel.json').exists() and time.monotonic()<until:time.sleep(.005)
            assert sentinel.poll() is None
            argv=[sys.executable,str(FIXTURE),'--mode',mode,'--area',str(area)]
            start=time.monotonic();cap=ProcessCapture(argv,area/'tree.log',area/'process.json',cwd=ROOT,deadline=start+.5,cleanup_deadline=start+1.2)
            error=None
            try:
                if fail:
                    with patch('process_capture.OwnedTree',side_effect=OSError('監督設定fixture失敗')):
                        with cap:cap.wait()
                else:
                    with cap:
                        until=time.monotonic()+.4
                        while not (area/'parent-ready').exists() and time.monotonic()<until:time.sleep(.002)
                        assert (area/'grandchild.json').exists(),'実孫起動確認'
                        if zero:cap.deadline=time.monotonic();cap.cleanup_deadline=cap.deadline
                        cap.wait()
            except Exception as exc:error=repr(exc)
            row=json.loads((area/'process.json').read_bytes())
            assert sentinel.poll() is None,'無関係専用sentinelを終了してはならない'
            if fail:
                assert row['pid'] is None and row['argv'] is None and row['log'] is None and error
            elif mode=='unowned' and os.name!='nt':
                assert row['supervision']['stopped'] is False and 'ownership token' in row['supervision']['reason']
                heartbeat=area/'grandchild.heartbeat';before=heartbeat.read_text();time.sleep(.04)
                assert heartbeat.read_text()!=before,'所有不明の孫を終了してはならない'
                assert row['exit_code'] is None and error
            elif zero:
                assert row['supervision']['stopped'] is False and 'deadline' in row['supervision']['reason'] and error
            else:
                assert row['supervision']['configured'] and row['supervision']['stopped'] is True,row
                assert row['wait']['ok'] and row['exit_code'] is not None
                heartbeat=area/'grandchild.heartbeat';before=heartbeat.read_text();time.sleep(.04)
                assert heartbeat.read_text()==before,'監督済み孫の実行停止を確認'
                if mode=='early':assert row['exit_code']==0 and row['supervision']['stop_attempted']
                else:assert row['kill']['ok'] and row['timed_out']
            return dict(execution=row,exception=error,sentinel_survived=True,scale='0.5秒、実174/180秒検査ではない')
        finally:
            # ケース終了後、専用fixtureのreleaseと自分のPopenだけwait。検査予算へ成功を補わない。
            (area/'release').write_bytes(b'cleanup');(sentinel_area/'release').write_bytes(b'cleanup')
            sentinel.wait(timeout=2)
            if cap is not None and cap.child is not None:cap.child.wait(timeout=2)
    record('outer-kill-owned-grandchild',lambda:process_tree('outer-tree','parent'))
    record('parent-exits-first-log-holder',lambda:process_tree('early-tree','early'))
    record('nested-capture-stays-in-outer-supervision',lambda:process_tree('nested-tree','nested'))
    record('ownership-unknown-preserved',lambda:process_tree('unknown-tree','unowned'))
    record('zero-deadline-unconfirmed',lambda:process_tree('zero-tree','parent',zero=True))
    record('supervision-setup-failure',lambda:process_tree('setup-failure','parent',fail=True))
    def launch_races():
        area=output/'races';area.mkdir();results=[]
        for i in range(12):
            cap=ProcessCapture([sys.executable,'-c','print("exit-race",flush=True)'],area/(str(i)+'.log'),area/(str(i)+'.json'),cwd=ROOT,budget=1)
            with cap:cap.wait()
            assert cap.row['exit_code']==0 and cap.row['supervision']['stopped'] is True
            results.append(cap.row)
        return results
    record('assignment-exit-races',launch_races)
    def ownership_exit_race():
        area=output/'ownership-exit-race';area.mkdir()
        cap=ProcessCapture([sys.executable,str(BATCH_FIXTURE),'sleep'],area/'child.log',area/'process.json',cwd=ROOT,budget=2)
        with cap:
            until=time.monotonic()+1
            while (area/'child.log').stat().st_size==0 and time.monotonic()<until:time.sleep(.005)
            if os.name=='nt':
                # Windowsは専用Jobからの退出raceを同じ残量内で確認する。
                cap.kill();cap.wait()
            else:
                original=cap.tree.belongs;hit=[]
                def exiting(pid,fields):
                    if pid==cap.child.pid and not hit:
                        hit.append(pid);cap.child.kill();cap.child.wait(timeout=.5)
                        raise PermissionError('実子exit直後のenviron読取りrace')
                    return original(pid,fields)
                cap.tree.belongs=exiting
                assert cap.tree.finish(cap.cleanup_deadline)
                assert hit and cap.child.returncode is not None
                cap.wait()
        assert cap.row['supervision']['stopped'] is True and cap.row['wait']['ok']
        return cap.row
    record('ownership-read-child-exit-race',ownership_exit_race)

    def assignment_failure():
        from process_tree059 import OwnedTree
        area=output/'assignment-failure';area.mkdir()
        cap=ProcessCapture([sys.executable,'-c','import time;time.sleep(2)'],area/'process.log',area/'process.json',cwd=ROOT,budget=1)
        original=OwnedTree.launch
        def failed_launch(tree,*a,**kw):
            original(tree,*a,**kw);tree.configured=False
            raise OSError('Linux所属確定失敗fixture（実子作成後）')
        target='assign' if os.name=='nt' else 'launch'
        replacement={'side_effect':OSError('Windows所属確定失敗fixture（suspend中）')} if os.name=='nt' else {'new':failed_launch}
        error=None
        try:
            with patch.object(OwnedTree,target,**replacement):
                with cap:cap.wait()
        except OSError as exc:error=repr(exc)
        row=json.loads((area/'process.json').read_bytes())
        assert error and row['pid'] is not None and row['wait']['ok'] and row['exit_code'] is not None
        assert row['supervision']['stopped'] is False and row['exit_code']!=0
        return dict(execution=row,error=error,scope='Windowsでは所属前のsuspend子。Linuxでは作成後失敗。子孫未確認を維持')
    record('created-before-supervision-failure',assignment_failure)

    status='FAIL' if any(r['status']=='FAIL' for r in rows) else 'PASS'
    for r in rows:print(r['case']+': '+r['status']+' '+r.get('exception',''))
    print('CAPTURE059_'+status+': cases='+str(len(rows)))
    return 1 if status=='FAIL' else 0


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output');p.add_argument('--inventory-check');a=p.parse_args()
    if a.inventory_check:
        path=Path(a.inventory_check);q=json.loads(path.read_bytes());d=driver();value=d.Suite.__new__(d.Suite)
        value.output=path.parent;value.accepted=q['requests']
        for request in value.accepted:request['root']=Path(request['root'])
        errors,unreaped=value.reconcile_requests();print('受付原record照合: '+str(errors)+' 未回収:'+str(unreaped));sys.exit(1 if errors or unreaped else 0)
    sys.exit(main(a))
