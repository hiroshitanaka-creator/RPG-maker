"""059専用: 起動準備から終端記録を所有し、今回起動したprocessだけ監督する。"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from process_tree059 import OwnedTree


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    # 競合中に半JSONを読ませない。既存fileだけatomic replace、directoryは失敗を維持。
    fd,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


class ProcessCapture:
    def __init__(self, argv, log, record, *, cwd, env=None, deadline=None,
                 cleanup_deadline=None, budget=30, timeout_kind='child_30_seconds'):
        self.argv,self.log,self.record=list(argv),Path(log),Path(record)
        self.cwd,self.env=cwd,env
        self.deadline=deadline if deadline is not None else time.monotonic()+budget
        self.cleanup_deadline=cleanup_deadline if cleanup_deadline is not None else self.deadline
        self.budget,self.kind=budget,timeout_kind
        self.child=None;self.stream=None;self.tree=None
        self.lock=threading.RLock();self.finalized=False
        self.start=time.monotonic()
        self.row=dict(planned_argv=self.argv,argv=None,cwd=str(cwd),pid=None,
                      started_utc=None,started_monotonic=None,accepted_utc=utc(),accepted_monotonic=self.start,
                      ended_utc=None,ended_monotonic=None,terminal=False,
                      seconds=0,budget_seconds=budget,exit_code=None,timed_out=False,
                      timeout_kind=None,exception=None,exit_unavailable_reason='not_started',
                      deadline_remaining_start=self.deadline-self.start,deadline_remaining_end=None,
                      kill={'attempted':False,'ok':None},wait={'attempted':False,'ok':None},
                      streams='stdout+stderr',planned_log=str(self.log),log=None,log_sha256=None,
                      result={},kill_point=None,record_path=str(self.record),record_saved=False,
                      supervision={'configured':False,'stopped':None,'reason':'not_started'})

    def persist(self):
        try:
            self.row['record_saved']=True
            save(self.record,self.row)
        except BaseException as exc:
            self.row.update(record_saved=False,record_error=type(exc).__name__+': '+str(exc))
            raise

    def __enter__(self):
        try:
            self.persist()
            self.log.parent.mkdir(parents=True,exist_ok=True)
            self.stream=self.log.open('wb',buffering=0)
            if time.monotonic()>=self.deadline:
                raise TimeoutError(self.kind+': 起動前に締切')
            self.tree=OwnedTree()
            try:
                self.child=self.tree.launch(self.argv,cwd=self.cwd,env=self.env,stream=self.stream)
            finally:
                self.child=self.tree.child
                if self.child is not None:
                    self.row.update(pid=self.child.pid,argv=self.tree.launch_argv,started_utc=utc(),
                                    started_monotonic=time.monotonic(),log=str(self.log),exit_unavailable_reason='running')
            self.row['supervision']=dict(self.tree.row)
            self.persist()
        except BaseException as exc:
            self.__exit__(type(exc),exc,exc.__traceback__)
            raise
        return self

    def kill(self):
        with self.lock:
            if self.finalized:return
            if self.child is not None:
                self.row['kill']['attempted']=True
                try:
                    self.tree.stop()
                    self.row['kill']['ok']=True
                except OSError as exc:self.row['kill'].update(ok=False,reason=type(exc).__name__+': '+str(exc))

    def wait(self):
        remaining=self.deadline-time.monotonic()
        if remaining<=0:raise TimeoutError(self.kind+': 子待機の締切')
        self.row['wait']['attempted']=True
        self.child.wait(timeout=remaining)
        self.row['wait']['ok']=True

    def __exit__(self, kind, exc, traceback):
        with self.lock:
            if self.finalized:
                # 再closeは保存失敗を成功に変えず、元の終端記録を保持。
                if not self.row['record_saved']:raise OSError(self.row.get('record_error','終端保存失敗'))
                return False
            if exc is not None:
                self.row['exception']=type(exc).__name__+': '+str(exc)
                self.row['timed_out']=isinstance(exc,(TimeoutError,subprocess.TimeoutExpired))
                if self.row['timed_out']:self.row['timeout_kind']=self.kind
            if self.child is not None:
                if self.child.poll() is None:self.kill()
                # 初回停止が一時失敗しても、waitで残量を使い切る前に所有treeを再確認する。
                self.tree.finish(self.cleanup_deadline)
                self.row['wait']['attempted']=True
                try:
                    self.child.wait(timeout=max(0,self.cleanup_deadline-time.monotonic()))
                    self.row['wait']['ok']=True
                except (OSError,subprocess.TimeoutExpired) as error:self.row['wait'].update(ok=False,reason=repr(error))
                self.row['exit_code']=self.child.returncode
                self.row['exit_unavailable_reason']=None if self.child.returncode is not None else 'kill/wait未回収: '+str(self.row['wait'])
            else:self.row['exit_unavailable_reason']='not_started: '+str(self.row['exception'])
            if self.tree is not None:
                self.row['supervision']=dict(self.tree.row)
                self.tree.close()
            if self.stream is not None:self.stream.close()
            # 未起動の空fileを子logと呼ばない。
            if self.child is not None:
                try:self.row['log_sha256']=hashlib.sha256(self.log.read_bytes()).hexdigest()
                except OSError as error:self.row['log_error']=repr(error)
            now=time.monotonic()
            self.row.update(ended_utc=utc(),ended_monotonic=now,terminal=True,seconds=now-self.start,
                            deadline_remaining_end=self.deadline-now,cleanup_remaining_end=self.cleanup_deadline-now)
            self.finalized=True
            self.persist()
        return False


def run_command(argv, log, record, *, cwd, env=None, budget=30, timeout_kind='outer_command'):
    deadline=time.monotonic()+budget
    capture=ProcessCapture(argv,log,record,cwd=cwd,env=env,deadline=deadline,
                           cleanup_deadline=deadline,budget=budget,timeout_kind=timeout_kind)
    with capture:capture.wait()
    if capture.child is not None and capture.row['supervision'].get('stopped') is not True:
        raise RuntimeError('owned tree終了未確認: '+str(capture.row['supervision']))
    return capture.row
