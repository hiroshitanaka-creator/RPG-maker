#!/usr/bin/env python3
"""実子process・Future・workerでF5を検査。取引の固定期待は変えない。"""
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
from process_capture import ProcessCapture, run_command, save
ROOT=Path(__file__).resolve().parents[3]
FIXTURE=Path(__file__).parent/'capture_fixture.py'


def driver():
    spec=importlib.util.spec_from_file_location('platform_driver057',ROOT/'tools/check_equipment_save_transaction_platform.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def main(args):
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False);rows=[];d=driver()
    def record(name,fn):
        start=time.monotonic()
        try:
            evidence=fn();rows.append(dict(case=name,status='PASS',seconds=time.monotonic()-start,evidence=evidence))
        except Exception as exc:
            rows.append(dict(case=name,status='FAIL',seconds=time.monotonic()-start,exception=repr(exc)))
        save(output/'tests.json',dict(cases=rows,status='FAIL' if any(r['status']=='FAIL' for r in rows) else 'PASS',scope='capture fixture; not transaction acceptance'))
    def single(name,mode,budget=2,parent_exception=False,kill=False,deadline_only=False):
        start=time.monotonic();log=output/(name+'.log');path=output/(name+'.json')
        kind='suite_inner_174_seconds' if deadline_only else 'child_30_seconds'
        argv=[sys.executable,str(FIXTURE),mode]
        cap=ProcessCapture(argv,log,path,cwd=ROOT,deadline=start+budget,cleanup_deadline=start+budget+1,timeout_kind=kind)
        error=None
        try:
            with cap:
                if parent_exception:
                    # 出力が実際に書かれた後で親に例外を起こす。
                    until=time.monotonic()+1
                    while log.stat().st_size==0 and time.monotonic()<until:time.sleep(.005)
                    raise RuntimeError('fixture parent exception')
                if kill:
                    until=time.monotonic()+1
                    while log.stat().st_size==0 and time.monotonic()<until:time.sleep(.005)
                    cap.kill()
                cap.wait()
        except Exception as exc:error=type(exc).__name__
        row=json.loads(path.read_bytes());raw=log.read_bytes()
        assert b'stdout-capture-fixture' in raw and b'stderr-capture-fixture' in raw
        assert row['pid'] and row['ended_utc'] and row['ended_monotonic']>=row['started_monotonic'] and row['wait']['ok']
        assert row['exit_code'] is not None and row['exit_unavailable_reason'] is None
        if mode=='abnormal':assert row['exit_code']==3 and not row['timed_out']
        elif parent_exception:assert error=='RuntimeError' and not row['timed_out'] and row['kill']['ok']
        elif kill:assert row['exit_code']==(1 if os.name=='nt' else -9) and not row['timed_out']
        elif mode=='sleep':assert row['timed_out'] and row['timeout_kind']==kind and row['kill']['ok']
        else:assert row['exit_code']==0 and error is None
        return row
    record('normal',lambda:single('normal','normal'))
    record('abnormal-child',lambda:single('abnormal','abnormal'))
    record('parent-exception',lambda:single('parent-exception','sleep',parent_exception=True))
    record('forced-child-kill',lambda:single('forced-kill','sleep',kill=True))
    record('child-real-30-seconds',lambda:single('child30','sleep',budget=30))
    record('suite-inner-deadline',lambda:single('inner','sleep',budget=.2,deadline_only=True))
    def launch_failure():
        cap=ProcessCapture([str(output/'nonexistent-executable')],output/'launch.log',output/'launch.json',cwd=ROOT)
        try:
            with cap:cap.wait()
        except OSError:pass
        row=json.loads((output/'launch.json').read_bytes());assert row['pid'] is None and row['exit_code'] is None and row['exit_unavailable_reason'].startswith('not_started:') and row['ended_utc']
        return row
    record('launch-failure',launch_failure)
    def batch_test(name,bad=False,stop=False):
        class CapturedSuite(d.Suite):
            def capture(self,argv,log,record,env):
                argv=[sys.executable,str(FIXTURE),'sleep' if stop else 'batch',argv[-1]]
                return super().capture(argv,log,record,env)
        suite=CapturedSuite(argparse.Namespace(godot=sys.executable,fixture_root=str(output/(name+'-qa')),output=str(output/(name+'-results'))))
        suite.deadline=time.monotonic()+2;suite.cleanup_deadline=suite.deadline+1
        roots=[suite.area/('root-'+str(i)) for i in range(8)]
        for root in roots:root.mkdir()
        caught=[]
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures=[pool.submit(suite.restarts.submit,r,dict(root=str(r),operation='bad' if bad else 'normal')) for r in roots]
            if stop:
                until=time.monotonic()+1
                while not suite.active and time.monotonic()<until:time.sleep(.005)
                suite.restarts.close()
            for future in futures:
                try:future.result()
                except Exception as exc:caught.append(type(exc).__name__+': '+str(exc))
        live=suite.restarts.close();assert not live
        queue=json.loads((suite.output/'restart-queue.json').read_bytes());assert len(queue['requests'])==8 and queue['recovery_complete']
        for request in queue['requests']:
            path=suite.output/Path(request['root']).name/'restarted-execution.json'
            assert path.exists(), 'dequeued but not launched request must retain termination record'
            row=json.loads(path.read_bytes())
            if row['pid'] is None:
                assert row['exit_code'] is None and row['exit_unavailable_reason'].startswith('not_started_queue_shutdown:')
                assert row['argv'] is None and row['log'] is None and row['ended_utc']
                assert row['batch_id']==request['batch_id']
        if bad or stop:assert caught and all(not r['completed'] for r in queue['requests'])
        else:assert not caught and all(r['completed'] for r in queue['requests'])
        batches=list((suite.output/'batches').glob('*-execution.json'));assert batches
        for path in batches:
            row=json.loads(path.read_bytes());assert row['ended_utc'] and row['wait']['ok'] and row['exit_code'] is not None
            assert len(row['root_completion'])==len(row['batch_roots'])
            for root in row['batch_roots']:
                assert (suite.output/Path(root).name/'restarted-execution.json').exists()
                assert (suite.output/Path(root).name/'restarted.log').read_bytes()==Path(row['log']).read_bytes()
        return dict(queue=queue,unique_batches=len(batches),caught=caught)
    def suite_parent_exception():
        class BoundarySuite(d.Suite):
            def capture(self,argv,log,record,env):
                return super().capture([sys.executable,str(FIXTURE),'boundary',argv[-1]],log,record,env)
        suite=BoundarySuite(argparse.Namespace(godot=sys.executable,fixture_root=str(output/'boundary-qa'),output=str(output/'boundary-results')))
        root=suite.area/'parent';root.mkdir()
        try:
            def mutate(child):raise RuntimeError('suite parent fixture exception')
            try:suite.run(root,dict(root=str(root),kill_point='fixture.boundary'),'mutate',mutate=mutate)
            except RuntimeError as exc:assert 'fixture exception' in str(exc)
            row=json.loads((suite.output/'parent/mutate-execution.json').read_bytes())
            assert row['exception'].startswith('RuntimeError:') and row['kill']['ok'] and row['wait']['ok'] and row['exit_code'] is not None
            assert row['kill_point']['pid']==row['pid'] and (suite.output/row['log']).read_bytes()
            return row
        finally:assert not suite.restarts.close()
    record('suite-run-parent-exception',suite_parent_exception)
    record('parallel-batch-normal',lambda:batch_test('parallel'))
    record('parallel-worker-exception',lambda:batch_test('worker-exception',bad=True))
    record('shutdown-active-and-futures',lambda:batch_test('shutdown',stop=True))
    def outer():
        start=time.monotonic()
        try:run_command([sys.executable,str(FIXTURE),'sleep'],output/'outer.log',output/'outer.json',cwd=ROOT,budget=.2,timeout_kind='outer_180_seconds')
        except subprocess.TimeoutExpired:pass
        row=json.loads((output/'outer.json').read_bytes());assert row['timed_out'] and row['timeout_kind']=='outer_180_seconds' and row['kill']['ok'] and row['ended_utc']
        assert (output/'outer.log').read_bytes()
        # budget縮尺fixture。実180秒の受入は同CIの全取引commandで別検査する。
        row['test_seconds']=time.monotonic()-start;return row
    record('outer-timeout-scaled',outer)
    status='FAIL' if any(r['status']=='FAIL' for r in rows) else 'PASS'
    print('CAPTURE057_'+status+': cases='+str(len(rows)))
    return 1 if status=='FAIL' else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);sys.exit(main(p.parse_args()))
