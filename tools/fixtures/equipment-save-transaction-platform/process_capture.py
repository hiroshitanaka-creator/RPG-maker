"""057専用: 出力を先行保存し、例外でも終了の事実と未回収理由を残す。"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


class ProcessCapture:
    def __init__(self, argv, log, record, *, cwd, env=None, deadline=None,
                 cleanup_deadline=None, budget=30, timeout_kind='child_30_seconds'):
        self.argv, self.log, self.record = argv, Path(log), Path(record)
        self.cwd, self.env = cwd, env
        self.deadline = deadline if deadline is not None else time.monotonic()+budget
        self.cleanup_deadline = cleanup_deadline if cleanup_deadline is not None else self.deadline
        self.budget, self.kind = budget, timeout_kind
        self.child = None
        self.stream = None
        self.lock = threading.Lock()
        self.start = time.monotonic()
        self.row = dict(argv=argv, cwd=str(cwd), pid=None, started_utc=utc(),
                        started_monotonic=self.start, ended_utc=None, ended_monotonic=None,
                        seconds=0, budget_seconds=budget, exit_code=None, timed_out=False,
                        timeout_kind=None, exception=None, exit_unavailable_reason='not_started',
                        deadline_remaining_start=self.deadline-self.start,
                        deadline_remaining_end=None, kill={'attempted':False,'ok':None},
                        wait={'attempted':False,'ok':None}, streams='stdout+stderr',
                        log=str(self.log), log_sha256=None, result={}, kill_point=None)

    def __enter__(self):
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.log.open('wb', buffering=0)
        save(self.record, self.row)
        try:
            if time.monotonic() >= self.deadline:
                raise TimeoutError('suite_inner_174_seconds: 起動前に締切')
            self.child = subprocess.Popen(self.argv, cwd=self.cwd, env=self.env,
                                          stdout=self.stream, stderr=subprocess.STDOUT)
            self.row.update(pid=self.child.pid, exit_unavailable_reason='running')
            save(self.record, self.row)
        except BaseException as exc:
            self.__exit__(type(exc), exc, exc.__traceback__)
            raise
        return self

    def kill(self):
        with self.lock:
            if self.child is not None and self.child.poll() is None:
                self.row['kill']['attempted'] = True
                try:
                    self.child.kill()
                    self.row['kill']['ok'] = True
                except OSError as exc:
                    self.row['kill'].update(ok=False, reason=repr(exc))

    def wait(self):
        remaining = self.deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError(self.kind+': 子待機の締切')
        self.row['wait']['attempted'] = True
        self.child.wait(timeout=remaining)
        self.row['wait']['ok'] = True

    def __exit__(self, kind, exc, traceback):
        if exc is not None:
            self.row['exception'] = type(exc).__name__+': '+str(exc)
            self.row['timed_out'] = isinstance(exc, (TimeoutError, subprocess.TimeoutExpired))
            if self.row['timed_out']:
                self.row['timeout_kind'] = self.kind
        if self.child is not None:
            if self.child.poll() is None:
                self.kill()
            self.row['wait']['attempted'] = True
            try:
                # 親の予算を越えて待たない。poll済みでもwaitを実行し回収を確認する。
                self.child.wait(timeout=max(0, self.cleanup_deadline-time.monotonic()))
                self.row['wait']['ok'] = True
            except (OSError, subprocess.TimeoutExpired) as error:
                self.row['wait'].update(ok=False, reason=repr(error))
            self.row['exit_code'] = self.child.returncode
            self.row['exit_unavailable_reason'] = None if self.child.returncode is not None else 'kill/wait未回収: '+str(self.row['wait'])
        else:
            self.row['exit_unavailable_reason'] = 'not_started: '+str(self.row['exception'])
        if self.stream is not None:
            self.stream.close()
        now = time.monotonic()
        self.row.update(ended_utc=utc(), ended_monotonic=now, seconds=now-self.start,
                        deadline_remaining_end=self.deadline-now,
                        log_sha256=hashlib.sha256(self.log.read_bytes()).hexdigest() if self.log.exists() else None)
        save(self.record, self.row)
        return False


def run_command(argv, log, record, *, cwd, env=None, budget=30, timeout_kind='outer_command'):
    # cleanupを含め元command予算。通常の子待機に上限を足さない。
    deadline = time.monotonic()+budget
    capture = ProcessCapture(argv, log, record, cwd=cwd, env=env, deadline=deadline,
                             cleanup_deadline=deadline, budget=budget, timeout_kind=timeout_kind)
    with capture:
        capture.wait()
    return capture.row
