#!/usr/bin/env python3
"""055: 053全論理不変条件を保持し、Windows終了/専用失敗条件を明示する。"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import queue
import threading
from concurrent.futures import Future
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools/fixtures/equipment-save-transaction-platform"))
from process_capture import ProcessCapture, utc

ROOT = Path(__file__).resolve().parents[1]
BAD = re.compile(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|Fontconfig error|_FAIL:')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('重複JSONキー:'+key)
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


class RestartBatch:
    """killのwait済み要求だけをまとめる。受付・future・workerを終了時に確定する。"""
    def __init__(self, suite):
        self.suite = suite
        self.queue = queue.Queue()
        self.stopping = threading.Event()
        self.lock = threading.Lock()
        self.requests = []
        self.next_batch = 0
        self.threads = [threading.Thread(target=self.worker, name='restart-'+str(i), daemon=True)
                        for i in range(2 if os.name=='nt' else 4)]
        for thread in self.threads:thread.start()

    def submit(self, root, cfg):
        future = Future()
        request = dict(root=root, cfg=cfg, future=future, queued=time.monotonic(),
                       queued_utc=utc(), worker_started=None, batch_id=None, completed=False)
        with self.lock:
            if self.stopping.is_set():raise RuntimeError('restart_shutdown: 受付終了')
            self.requests.append(request)
            self.queue.put(request)
        try:
            return future.result(timeout=max(.01, self.suite.deadline-time.monotonic()))
        except TimeoutError as exc:
            # Future timeoutの空文字をsuite/子timeoutと区別する。
            raise TimeoutError('restart_future_deadline: root='+str(root)+' batch='+str(request['batch_id'])) from exc

    def worker(self):
        while not self.stopping.is_set():
            try:first = self.queue.get(timeout=.06)
            except queue.Empty:continue
            first['dequeued'] = time.monotonic()
            requests = [first]
            for _ in range(3):
                try:
                    request = self.queue.get(timeout=.06)
                    request['dequeued'] = time.monotonic()
                    requests.append(request)
                except queue.Empty:break
            with self.lock:
                batch = 'batch-%06d' % self.next_batch
                self.next_batch += 1
                for request in requests:
                    request.update(batch_id=batch, worker_started=request['dequeued'], batch_started=time.monotonic(), worker=threading.current_thread().name)
            try:
                if self.stopping.is_set():raise RuntimeError('restart_shutdown: 未実行batch')
                results = self.suite.run_restart_batch(requests, batch)
                for request, result in zip(requests, results):
                    if not request['future'].done():request['future'].set_result(result)
                    request['completed'] = True
            except BaseException as exc:
                for request in requests:
                    request['exception'] = type(exc).__name__+': '+str(exc)
                    if not request['future'].done():request['future'].set_exception(exc)
            finally:
                for request in requests:request['worker_finished'] = time.monotonic()

    def close(self):
        self.stopping.set()
        with self.lock:
            for request in self.requests:
                if not request['future'].done():
                    request['future'].set_exception(RuntimeError('restart_shutdown: 未完future'))
        self.suite.stop_children()
        for thread in self.threads:
            thread.join(timeout=max(0, self.suite.cleanup_deadline-time.monotonic()))
        rows = [{key:(str(value) if key=='root' else value) for key,value in request.items()
                 if key not in ['future','cfg']} for request in self.requests]
        live = [thread.name for thread in self.threads if thread.is_alive()]
        write(self.suite.output/'restart-queue.json', dict(requests=rows, live_workers=live,
              recovery_complete=not live, deadline_remaining=self.suite.cleanup_deadline-time.monotonic()))
        return live


class Suite:
    def __init__(self, args):
        self.godot = Path(args.godot).resolve()
        self.area = Path(args.fixture_root).absolute()
        self.output = Path(args.output).absolute()
        if self.area.exists():
            raise RuntimeError('fixture-rootは未存在の専用QAを指定する')
        self.area.mkdir(parents=True)
        self.output.mkdir(parents=True, exist_ok=True)
        self.expected = load(ROOT/'tools/fixtures/equipment-save-transaction-platform/expectations.json')
        if os.name=='nt':self.expected['cases']['nonroot-permission']['reason']='write_failed'
        self.start = time.monotonic()
        self.deadline = self.start + 174
        self.cleanup_deadline = self.start + 180
        self.active_lock = threading.Lock()
        self.active = set()
        self.timings = []
        self.seeds = {}
        self.restarts=RestartBatch(self)
        self.rows = []
        self.failures = []

    def config(self, root, **values):
        return dict(root=str(root), operation='full', generation='g1', session_token='g1', **values)

    def env(self, root):
        env = os.environ.copy()
        for key in ['XDG_CACHE_HOME', 'XDG_DATA_HOME', 'XDG_CONFIG_HOME']:
            value = root/'profile'/key
            value.mkdir(parents=True, exist_ok=True)
            env[key] = str(value)
        if os.name=='nt':
            env['APPDATA']=str(root/'profile'/'APPDATA');env['LOCALAPPDATA']=str(root/'profile'/'LOCALAPPDATA')
        return env

    def stop_children(self):
        with self.active_lock:
            for capture in self.active:capture.kill()

    def capture(self, argv, log, record, env):
        start = time.monotonic()
        remaining = self.deadline-start
        return ProcessCapture(argv, log, record, cwd=ROOT, env=env,
                              deadline=min(start+30, self.deadline), cleanup_deadline=self.cleanup_deadline,
                              timeout_kind='suite_inner_174_seconds' if remaining<30 else 'child_30_seconds')

    def run(self, root, cfg, label, kill=False, mutate=None):
        config_path = root/(label+'-config.json')
        cfg = dict(cfg, result=label+'-result.json')
        write(config_path, cfg)
        argv = [str(self.godot), '--headless', '--path', str(ROOT), '--script',
                'res://tools/equipment_save_transaction_probe.gd', '--', str(config_path)]
        if not kill and mutate is None:return self.restarts.submit(root,cfg)
        log_path = self.output/root.name/(label+'.log')
        record = self.output/root.name/(label+'-execution.json')
        capture = self.capture(argv, log_path, record, self.env(root))
        with self.active_lock:self.active.add(capture)
        try:
            with capture:
                child = capture.child
                marker = root/'paused.json'
                while not marker.exists():
                    if child.poll() is not None:
                        raise RuntimeError('境界到達前に終了:'+label+' '+log_path.read_text())
                    if time.monotonic()>=capture.deadline:
                        raise TimeoutError(capture.kind+': 境界待機超過')
                    time.sleep(.005)
                hit = load(marker)
                capture.row['kill_point'] = hit
                if hit['point'] != cfg['kill_point'] or hit['pid'] != child.pid:
                    raise RuntimeError('kill地点/PID不一致')
                if kill:capture.kill()
                else:
                    mutate(child)
                    (root/'release').write_bytes(b'continue')
                capture.wait()
                result_path = root/(label+'-result.json')
                capture.row['result'] = load(result_path) if result_path.exists() else {}
        finally:
            capture.row['log'] = str(log_path.relative_to(self.output))
            write(record, capture.row)
            with self.active_lock:self.active.discard(capture)
        return capture.row

    def run_restart_batch(self, requests, batch_id):
        configurations = [dict(r['cfg'], result=r['cfg'].get('result','restarted-result.json')) for r in requests]
        first = requests[0]['root']
        path = first/(configurations[0]['result'].removesuffix('-result.json')+'-batch.json')
        write(path, configurations)
        argv = [str(self.godot), '--headless', '--path', str(ROOT), '--script',
                'res://tools/equipment_save_transaction_probe.gd', '--', str(path)]
        log = self.output/'batches'/(batch_id+'.log')
        record = self.output/'batches'/(batch_id+'-execution.json')
        capture = self.capture(argv, log, record, self.env(first))
        capture.row.update(batch_id=batch_id, batch_roots=[str(r['root']) for r in requests])
        with self.active_lock:self.active.add(capture)
        rows = []
        try:
            with capture:
                capture.wait()
                for request, options in zip(requests, configurations):
                    root = request['root']
                    result = load(root/options['result'])
                    request['result_observed'] = True
                    rows.append(dict(result=result))
        finally:
            # 子timeout/異常exit/JSON例外にも全rootへlogと終了記録を残す。
            capture.row['root_completion'] = []
            raw = log.read_bytes() if log.exists() else b''
            for request, options in zip(requests, configurations):
                root = request['root'];label = options['result'].removesuffix('-result.json')
                result_path = root/options['result']
                result = {}
                try:
                    if result_path.exists():result = load(result_path)
                    reason = None if result else 'result file未取得'
                except Exception as exc:reason = type(exc).__name__+': '+str(exc)
                status = dict(root=str(root), result_observed=bool(result), missing_reason=reason)
                capture.row['root_completion'].append(status)
                root_log = self.output/root.name/(label+'.log')
                root_log.parent.mkdir(parents=True, exist_ok=True);root_log.write_bytes(raw)
                row = dict(capture.row, result=result, batch_record=record.relative_to(self.output).as_posix(),
                           log=root_log.relative_to(self.output).as_posix(),
                           queue_seconds=(request['worker_started']-request['queued']),
                           coalesce_seconds=request['batch_started']-request['worker_started'], root_completion=status)
                write(self.output/root.name/(label+'-execution.json'), row)
                for index, item in enumerate(requests):
                    if item is request and index<len(rows):rows[index] = row
            write(record, capture.row)
            with self.active_lock:self.active.discard(capture)
        return rows

    def seed(self, name, **options):
        root = self.area/('seed-'+name)
        root.mkdir()
        cfg = self.config(root)
        cfg.update(operation='fixture', **options)
        execution = self.run(root, cfg, 'fixture')
        if execution['exit_code'] or BAD.search((self.output/ execution['log']).read_text()):
            raise RuntimeError('fixture生成の実エラー')
        self.seeds[name] = root

    def new(self, name, seed='typed'):
        root = self.area/name
        root.mkdir()
        shutil.copyfile(self.seeds[seed]/'source.json', root/'source.json')
        if (self.seeds[seed]/'history').exists():
            shutil.copytree(self.seeds[seed]/'history', root/'history')
        return root

    def token(self, source):
        return digest(json.dumps(['equipment-migration-v1',digest(source),'equipment-q1a-q2a-q3a-v1',1], separators=(',',':')).encode())

    def snapshot(self, root, label):
        start = time.monotonic()
        try:return self._snapshot(root, label)
        finally:self.timings.append(dict(kind="snapshot", root=str(root), label=label, start=start, end=time.monotonic()))

    def _snapshot(self, root, label):
        destination = self.output/root.name/label
        destination.mkdir(parents=True, exist_ok=True)
        files = {}
        for path in sorted(root.rglob('*')):
            if 'profile' in path.relative_to(root).parts:
                continue
            if path.is_symlink():
                raw = os.readlink(path).encode()
                files[path.relative_to(root).as_posix()] = {'kind':'link','bytes':len(raw),'sha256':digest(raw),'target':raw.decode()}
                target = destination/(path.relative_to(root).as_posix()+'.link.txt')
            elif path.is_file():
                raw = path.read_bytes()
                files[path.relative_to(root).as_posix()] = {'kind':'file','bytes':len(raw),'sha256':digest(raw)}
                target = destination/path.relative_to(root)
            else:
                files[path.relative_to(root).as_posix()] = {'kind':'directory'}
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        write(destination/'files.json', files)
        return files

    def quantities(self, path, expected, token):
        doc = load(path)
        stock = doc['equipment_stock']
        owned = list(stock['bag'])
        for actor in doc['party']+doc.get('first_region',{}).get('reserve',[]):
            eq = actor['equipment']
            owned += eq['weapons']+[x for x in [eq['armor']]+eq['accessories'] if x]
        return (len(stock['instances'])==expected and len(owned)==expected and
                len(set(owned))==expected and set(owned)==set(stock['instances']) and
                doc['equipment_migration']['migration_id']==token and
                len(doc['equipment_migration']['equipment_audit']['generated'])==expected)

    def common(self, root, commands, source, history, last, reason, expected_exit=None):
        source_path = root/'source.json'
        actual_history = {p.relative_to(root).as_posix():p.read_bytes() for p in (root/'history').glob('*')} if (root/'history').exists() else {}
        return {
            'process_exit':[c['exit_code'] for c in commands]==(expected_exit or [0]*len(commands)) and all(not c['timed_out'] and c['seconds']<=30 for c in commands),
            'clean_logs':all(not BAD.search((self.output/c['log']).read_text()) for c in commands),
            'memory_unchanged':all(c['result'].get('memory_unchanged') is True for c in commands if c['exit_code']==0),
            'source_bytes':source_path.read_bytes()==source,
            'history_bytes':actual_history==history,
            'qa_user_dir':all(Path(c['result'].get('user_dir','')).is_relative_to(self.area) for c in commands if c['exit_code']==0),
            'expected_result':last.get('reason_code')==reason and last.get('ok')==(reason=='ok'),
            'file_evidence':bool(self.snapshot(root,'final')),
        }

    def run_case(self, name, spec):
        root = self.new(name, 'granted' if name=='normal-granted' else 'plain' if name=='absent-id' else name if name in ['trial-missing','trial-corrupt','trial-unclean'] else 'typed')
        source = (root/'source.json').read_bytes()
        token = self.token(source)
        tx = root/'transactions'/token
        history = {p.relative_to(root).as_posix():p.read_bytes() for p in (root/'history').glob('*')} if (root/'history').exists() else {}
        commands = []
        checks = {}
        expected_exit = None
        cfg = self.config(root)
        kind = spec['kind']
        reason = spec.get('reason','ok')
        if kind=='kill':
            cfg['kill_point']=spec['point']
            commands.append(self.run(root,cfg,'killed',kill=True))
            killed_files=self.snapshot(root,'at-kill')
            cfg=self.config(root);cfg.update(operation='resume',token=token)
            commands.append(self.restarts.submit(root,cfg))
            result=commands[-1]['result']
            before=result.get('recovery_before',{})
            after_commit=spec['point']=='commit.rename.after' or spec['point'].startswith('receipt-committed.')
            expected_exit=[1 if os.name=='nt' else -signal.SIGKILL,0]
            complete=tx/'converted.json'
            checks.update({
                'recovery_phase':before.get('ok') is True and before.get('phase') in (['committed'] if after_commit else ['incomplete','prepared']),
                'same_migration':result.get('migration_id')==token,
                'quantity':result.get('quantity')==12 and self.quantities(complete,12,token),
                'preserved_backups':(tx/'source.bin').read_bytes()==source and (tx/'history.bin').read_bytes()==next(iter(history.values())),
                'committed_bytes':result.get('phase')=='committed' and digest(complete.read_bytes())==result.get('candidate_sha256') and result.get('applied') is False,
                'no_double_grant':self.quantities(complete,12,token),
                'boundary_files':self.boundary_files(spec['point'],killed_files,token,source,history),
            })
        elif kind=='fault':
            cfg['fail_point']=spec['point']
            commands.append(self.run(root,cfg,'injected'))
            first=commands[-1]['result']
            recovered_cfg=self.config(root);recovered_cfg.update(operation='resume',token=token)
            self.snapshot(root,'at-failure')
            commands.append(self.restarts.submit(root,recovered_cfg))
            result=first
            checks.update({
                'recovery_phase':commands[-1]['result'].get('phase')=='committed' and (not spec['point'].startswith('receipt-committed') or first.get('phase')=='committed' and first.get('receipt_updated') is False),
                'quantity':self.quantities(tx/'converted.json',12,token),
                'no_double_grant':commands[-1]['result'].get('quantity')==12,
            })
        else:
            commands,result,source,history,specific=self.special(name,root,source,history,token,tx,cfg)
            checks['specific_invariant']=specific
        checks.update(self.common(root,commands,source,history,result,reason,expected_exit))
        if set(checks)!=set(spec['checks']):
            raise RuntimeError('固定assert一覧不一致:'+name)
        row={'case':name,'expected':spec,'actual':result,'checks':checks,'commands':commands}
        write(self.output/name/'case.json',row)
        return row

    def boundary_files(self, point, files, token, source, history):
        base='transactions/'+token+'/'
        past_source = point.startswith(('history.','candidate.','receipt-','commit.')) or point=='source.rename.after'
        past_history = point.startswith(('candidate.','receipt-','commit.')) or point=='history.rename.after'
        committed = point=='commit.rename.after' or point.startswith('receipt-committed.')
        def full(name, raw):
            value=files.get(base+name,{})
            return value.get('sha256')==digest(raw) and value.get('bytes')==len(raw)
        return (('source.json' in files) and
                (not past_source or full('source.bin',source)) and
                (not past_history or full('history.bin',next(iter(history.values())))) and
                ((base+'converted.json' in files)==committed))

    def special(self,name,root,source,history,token,tx,cfg):
        commands=[]
        specific=True
        def run(operation='full',**options):
            custom=self.config(root);custom.update(operation=operation,**options)
            command=self.run(root,custom,'step-'+str(len(commands)))
            commands.append(command)
            return command['result']
        if name in ['normal-pending','normal-granted','absent-id']:
            result=run()
            specific=self.quantities(tx/'converted.json',22 if name=='normal-granted' else 12,token) and result.get('history',{}).get('status')==('absent_id' if name=='absent-id' else 'normal')
            decoded=run('decode',source=str(tx/'converted.json'))
            specific=specific and decoded.get('ok') is True and decoded.get('quantity')==(22 if name=='normal-granted' else 12)
        elif name in ['trial-missing','trial-corrupt','trial-unclean']:
            # fixtureの期待rawを専用ファイルへ設定。履歴の消去はしない。
            result=run()
            expected={'trial-missing':'missing','trial-corrupt':'corrupt','trial-unclean':'unclean'}[name]
            specific=result.get('history',{}).get('status')==expected and result['history'].get('history_complete') is False and (expected=='missing' and not (tx/'history.bin').exists() or expected!='missing' and (tx/'history.bin').read_bytes()==next(iter(history.values())))
        elif name in ['inspect-readonly','inspect-prepared','inspect-committed']:
            if name=='inspect-prepared':run('prepare')
            if name=='inspect-committed':run()
            before={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            result=run('inspect')
            specific=result.get('source_sha256')==digest(source) and result.get('decoder',{}).get('ok') is True and (not (root/'transactions').exists() if name=='inspect-readonly' else result.get('existing',{}).get('phase')==('prepared' if name=='inspect-prepared' else 'committed')) and all((root/p).read_bytes()==raw for p,raw in before.items())
        elif name=='same-raw-alias':
            first=run()
            shutil.copyfile(root/'source.json',root/'alias.json')
            result=run(source=str(root/'alias.json'))
            specific=result.get('token')==first.get('token')==token and self.quantities(tx/'converted.json',12,token)
        elif name=='different-raw':
            first=run()
            other=b'  '+source+b'\n';(root/'alias.json').write_bytes(other)
            result=run(source=str(root/'alias.json'))
            other_token=self.token(other)
            specific=token!=other_token and result.get('token')==other_token and self.quantities(tx/'converted.json',12,token) and self.quantities(root/'transactions'/other_token/'converted.json',12,other_token)
        elif name=='new-input':
            run(); before=(tx/'converted.json').read_bytes()
            result=run(source=str(tx/'converted.json'))
            specific=(tx/'converted.json').read_bytes()==before and self.quantities(tx/'converted.json',12,token)
        elif name in ['stale-current','stale-committed']:
            run('prepare' if name=='stale-current' else 'full');result=run('commit',token=token,generation='g2',session_token='g2');specific=(tx/'converted.json').exists()==(name=='stale-committed')
        elif name=='inspect-missing':result=run('inspect',source=str(root/'missing.json'));specific=not tx.exists()
        elif name=='inspect-null-context':result=run('inspect',context='null-session');specific=result.get('decoder',{}).get('reason_code')=='invalid_context' and not tx.exists()
        elif name=='stale-prepare':result=run('prepare',session_token='g2');specific=not tx.exists()
        elif name=='stale-commit':run('prepare');result=run('commit',token=token,session_token='g2');specific=not (tx/'converted.json').exists()
        elif name=='wrong-hash':result=run('prepare',expected_sha='a'*64);specific=not tx.exists()
        elif name.startswith('candidate-'):result=run('prepare',candidate=name.split('-',1)[1]);specific=not tx.exists()
        elif name=='source-changed':
            run('prepare');source=b' '+source;(root/'source.json').write_bytes(source)
            result=run('commit',token=token);specific=not (tx/'converted.json').exists()
        elif name in ['receipt-corrupt','receipt-intent','receipt-phase-stale','backup-changed','output-changed','intent-changed','history-changed']:
            run()
            if name=='receipt-corrupt':(tx/'receipt.json').write_bytes(b'{bad receipt')
            elif name in ['receipt-intent','receipt-phase-stale']:
                value=load(tx/'receipt.json')
                if name=='receipt-intent':value['intent']['source_size']+=1
                else:value['phase']='prepared'
                write(tx/'receipt.json',value)
            elif name=='backup-changed':(tx/'source.bin').write_bytes(b' '+source)
            elif name=='output-changed':
                value=load(tx/'converted.json');value['party'][0]['hp']-=1;write(tx/'converted.json',value)
            elif name=='intent-changed':
                value=load(tx/'intent.json');value['candidate_size']+=1;write(tx/'intent.json',value)
            else:
                path=next((root/'history').glob('*'));path.write_bytes(b' '+path.read_bytes());history={path.relative_to(root).as_posix():path.read_bytes()}
            mutated=self.snapshot(root,'external-change')
            result=run('recover',token=token)
            specific=all((root/path).read_bytes()==(self.output/root.name/'external-change'/path).read_bytes() for path,data in mutated.items() if data['kind']=='file')
        elif name=='parent-path':result=run('prepare',source=str(root/'..'/'outside.json'));specific=not tx.exists()
        elif name=='outside-path':result=run('prepare',source=str(self.area/'outside.json'));specific=not tx.exists()
        elif name=='source-link':
            (root/'link.json').symlink_to(root/'source.json');result=run('prepare',source=str(root/'link.json'));specific=not tx.exists()
        elif name=='directory-link':
            outside=self.area/(name+'-outside');outside.mkdir();(outside/'sentinel').write_bytes(b'preserve')
            (root/'transactions').symlink_to(outside,target_is_directory=True)
            result=run('prepare');specific=(outside/'sentinel').read_bytes()==b'preserve' and len(list(outside.iterdir()))==1
        elif name=='output-link':
            run('prepare');(tx/'converted.json').symlink_to(self.area/'outside-output.json')
            result=run('commit',token=token);specific=(tx/'converted.json').is_symlink() and not (self.area/'outside-output.json').exists()
        elif name=='owner-corrupt':
            run('prepare');link=sorted((tx/'leases').glob('lease-*'))[-1];owner=link.resolve()
            value=load(owner);value['pid']=0;write(owner,value);altered=owner.read_bytes()
            result=run('commit',token=token);specific=not (tx/'converted.json').exists() and owner.read_bytes()==altered
        elif name=='initial-tmp-hardlink':
            tx.mkdir(parents=True);os.link(root/'source.json',tx/'source.bin.tmp')
            result=run('prepare');specific=os.path.samefile(root/'source.json',tx/'source.bin.tmp') and (root/'source.json').read_bytes()==source
        elif name=='receipt-tmp-hardlink':
            run('prepare');os.link(root/'source.json',tx/'receipt.tmp')
            result=run('commit',token=token);specific=result.get('phase')=='committed' and result.get('receipt_updated') is False and (root/'source.json').read_bytes()==source
        elif name=='backup-hardlink':
            # 既存backupとsourceが同一inodeなら、同bytesでも再開拒否。
            tx.mkdir(parents=True);os.link(root/'source.json',tx/'source.bin')
            result=run('prepare');specific=os.path.samefile(root/'source.json',tx/'source.bin')
            # 初期衝突でintentを書かないことも受入条件。専用実装はconflictを先に返す。
        elif name=='transaction-source':
            (root/'transactions').mkdir();inside=root/'transactions'/'raw.json';inside.write_bytes(source)
            result=run('prepare',source=str(inside));specific=inside.read_bytes()==source
        elif name=='token-invalid':result=run('recover',token='../escape');specific=not tx.exists()
        elif name=='target-collision':
            run('prepare');(tx/'converted.json').write_bytes(b'preexisting target')
            result=run('commit',token=token);specific=(tx/'converted.json').read_bytes()==b'preexisting target'
        elif name=='backup-collision':
            tx.mkdir(parents=True);(tx/'source.bin').write_bytes(b'preexisting backup')
            result=run('prepare');specific=(tx/'source.bin').read_bytes()==b'preexisting backup'
        elif name in ['null-session','null-abilities']:result=run('prepare',context=name);specific=not tx.exists()
        elif name=='nonroot-permission':
            if os.name=='nt':
                # 自分が作った専用fileのreadonly属性による実OS拒否。ACL/OS設定を変えない。
                import stat
                run('prepare')
                candidate=tx/'converted.tmp';candidate.chmod(stat.S_IREAD)
                result=run('prepare');specific=result.get('reason_code')=='write_failed' and not (tx/'converted.json').exists()
            else:
                os.mkdir(root/'transactions',0o500)
                result=run('prepare');specific=os.geteuid()!=0 and not tx.exists()
        elif name=='writer-busy':
            cfg['kill_point']='candidate.open.before'
            holder={}
            def concurrent(child):
                first=run('prepare');holder['result']=first;holder['pid']=child.pid
            command=self.run(root,cfg,'holder',mutate=concurrent);commands.append(command)
            result=holder['result'];specific=command['result'].get('phase')=='committed' and self.quantities(tx/'converted.json',12,token)
        elif name in ['commit-source-race','commit-target-race','commit-tmp-race']:
            cfg['kill_point']='commit.rename.before'
            def mutate(child):
                nonlocal source
                if name=='commit-source-race':source=b' '+source;(root/'source.json').write_bytes(source)
                elif name=='commit-target-race':(tx/'converted.json').write_bytes(b'preexisting target')
                else:(tx/'converted.tmp').write_bytes(b'changed tmp')
            command=self.run(root,cfg,'race',mutate=mutate);commands.append(command)
            result=command['result'];specific=(not (tx/'converted.json').exists() if name!='commit-target-race' else (tx/'converted.json').read_bytes()==b'preexisting target')
        elif name=='injected-enospc':result=run('prepare',fail_point='candidate.store.before');specific=result.get('reason_code')=='injected_io_failure' and not (tx/'converted.json').exists()
        else:raise RuntimeError('未定義case:'+name)
        return commands,result,source,history,specific

    def cases(self):
        self.seed('typed',typed=True,trial=True,history='normal')
        self.seed('plain')
        self.seed('granted',typed=True,trial=True,history='normal',unlocked=True)
        self.seed('trial-missing',typed=True,trial=True,history='missing')
        self.seed('trial-corrupt',typed=True,trial=True,history='corrupt')
        self.seed('trial-unclean',typed=True,trial=True,history='unclean')
        with ThreadPoolExecutor(max_workers=8 if os.name=='nt' else 16) as workers:
            pending={workers.submit(self.run_case,name,spec):name for name,spec in self.expected['cases'].items()}
            for future in as_completed(pending):
                name=pending[future]
                try:
                    row=future.result();self.rows.append(row)
                    for check,passed in row['checks'].items():
                        if passed is not True:self.failures.append(name+':'+check)
                except Exception as exc:
                    self.failures.append(name+':'+type(exc).__name__+': '+str(exc))
    def main(self):
        try:self.cases()
        except Exception as exc:self.failures.append(type(exc).__name__+': '+str(exc))
        finally:
            live = self.restarts.close()
            if live:self.failures.append('worker未回収:'+','.join(live))
            write(self.output/'timing.json', dict(suite_started=self.start, observations=self.timings,
                  units='monotonic_seconds', snapshot='inclusive; 累積並行時間、wall-timeへ単純加算禁止'))
        self.rows.sort(key=lambda row:row['case'])
        summary={'status':'FAIL' if self.failures else 'PASS','case_count':len(self.rows),
                 'checks':sum(len(r['checks']) for r in self.rows),'failures':self.failures,
                 'seconds':time.monotonic()-self.start,'budget_seconds':180,'cases':[r['case'] for r in self.rows],
                 'engine_sha256':digest(self.godot.read_bytes()),'limits':{'real_enospc':'unverified: dedicated small filesystem unavailable; injection is separate','power_loss':'unverified','platform':os.name,'termination':'TerminateProcess/exit1' if os.name=='nt' else 'SIGKILL/exit-9','directory_toctou':'unverified hostile concurrent directory replacement','real_cross_volume':'unverified dedicated nested volume unavailable'},
                 'real_permission':{'uid':os.geteuid() if hasattr(os,'geteuid') else None,'mechanism':'readonly-file' if os.name=='nt' else 'directory-mode-0500','os_settings_changed':False}}
        if summary['seconds']>180:self.failures.append('全体180秒超過');summary['status']='FAIL'
        write(self.output/'summary.json',summary)
        write(self.output/'sha256.json',{p.relative_to(self.output).as_posix():digest(p.read_bytes()) for p in sorted(self.output.rglob('*')) if p.is_file() and p.name!='sha256.json'})
        print('TRANSACTION_'+summary['status']+': cases='+str(summary['case_count'])+' checks='+str(summary['checks'])+' seconds='+str(round(summary['seconds'],3)))
        for failure in self.failures:print(failure)
        return 1 if self.failures else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--godot',required=True);parser.add_argument('--fixture-root',required=True);parser.add_argument('--output',required=True)
    try:sys.exit(Suite(parser.parse_args()).main())
    except Exception as exc:print('TRANSACTION_FAIL: '+str(exc));sys.exit(1)
