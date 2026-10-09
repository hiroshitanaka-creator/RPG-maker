"""059専用所有processの監督。全体/name killやOS設定変更は行わない。"""
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
import uuid

SESSION_KEY='EQUIPMENT_QA059_SESSION'
OWNER_KEY='EQUIPMENT_QA059_OWNERS'


class OwnedTree:
    def __init__(self):
        self.child=None
        self.job=None
        self.session=None
        self.group=None
        self.outer=False
        self.token=uuid.uuid4().hex
        self.configured=False
        self.row={'mechanism':None,'configured':False,'ownership':None,'stopped':None,
                  'stop_attempted':False,'reason':'not_started','observed_members':[]}
        if os.name=='nt':self._windows_job()
        elif not sys.platform.startswith('linux'):
            raise OSError('059監督非対応OS: '+sys.platform)

    def _windows_job(self):
        import ctypes as C
        from ctypes import wintypes as W
        self.C=C;self.W=W;self.api=C.WinDLL('kernel32',use_last_error=True)
        self.api.CreateJobObjectW.argtypes=[C.c_void_p,W.LPCWSTR];self.api.CreateJobObjectW.restype=W.HANDLE
        self.api.SetInformationJobObject.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD];self.api.SetInformationJobObject.restype=W.BOOL
        self.api.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE];self.api.AssignProcessToJobObject.restype=W.BOOL
        self.api.TerminateJobObject.argtypes=[W.HANDLE,W.UINT];self.api.TerminateJobObject.restype=W.BOOL
        self.api.QueryInformationJobObject.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.c_void_p];self.api.QueryInformationJobObject.restype=W.BOOL
        self.api.CloseHandle.argtypes=[W.HANDLE];self.api.CloseHandle.restype=W.BOOL
        class BASIC(C.Structure):
            _fields_=[('process_time',C.c_int64),('job_time',C.c_int64),('flags',W.DWORD),('min_ws',C.c_size_t),('max_ws',C.c_size_t),('active_limit',W.DWORD),('affinity',C.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]
        class IO(C.Structure):
            _fields_=[(name,C.c_uint64) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
        class EXT(C.Structure):
            _fields_=[('basic',BASIC),('io',IO),('process_memory',C.c_size_t),('job_memory',C.c_size_t),('peak_process',C.c_size_t),('peak_job',C.c_size_t)]
        self.job=self.api.CreateJobObjectW(None,None)
        if not self.job:raise C.WinError(C.get_last_error())
        limits=EXT();limits.basic.flags=0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE、breakawayなし
        if not self.api.SetInformationJobObject(self.job,9,C.byref(limits),C.sizeof(limits)):
            error=C.WinError(C.get_last_error());self.close();raise error
        self.row['mechanism']='Windows Job Object; suspended launch -> assign -> resume; no breakaway'

    def launch(self,argv,*,cwd,env,stream):
        child_env=dict(os.environ if env is None else env)
        self.launch_argv=list(argv)
        child_env[OWNER_KEY]=child_env.get(OWNER_KEY,'')+','+self.token
        if os.name=='nt':
            self.child=subprocess.Popen(argv,cwd=cwd,env=child_env,stdout=stream,stderr=subprocess.STDOUT,creationflags=0x4)
            # 主threadを止めたまま所属を確定し、未所属の孫起動raceをなくす。
            handle=int(self.child._handle)
            self.assign(handle)
            self.configured=True
            self.row.update(configured=True,ownership={'job_handle':int(self.job),'root_pid':self.child.pid},reason=None)
            ntdll=self.C.WinDLL('ntdll');resume=ntdll.NtResumeProcess
            resume.argtypes=[self.W.HANDLE];resume.restype=self.C.c_long
            status=resume(handle)
            if status!=0:raise OSError('NtResumeProcess status='+hex(status & 0xffffffff))
        else:
            # 自分の外側監督者が渡した同一sessionだけ継承。入れ子は新sessionへ逃がさない。
            inherited=child_env.get(SESSION_KEY)
            if inherited is not None:
                sid=int(inherited)
                if sid!=os.getsid(0):
                    raise OSError('専用外側sessionの所属を確認できない')
                self.session=sid
                self.child=subprocess.Popen(argv,cwd=cwd,env=child_env,stdout=stream,stderr=subprocess.STDOUT,process_group=0)
            else:
                # 子はexec前にsetsid済み。自分が起動したPIDだけを所有根拠にする。
                self.outer=True
                if shutil.which(str(argv[0]),path=child_env.get('PATH')) is None:
                    raise FileNotFoundError(str(argv[0]))
                self.launch_argv=[sys.executable,str(Path(__file__).with_name('process_exec059.py')),*argv]
                self.child=subprocess.Popen(self.launch_argv,cwd=cwd,env=child_env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                self.session=self.child.pid
            self.group=self.child.pid
            self.configured=True
            self.row.update(mechanism='Linux dedicated session' if self.outer else 'Linux nested group + inherited ownership token in outer session',configured=True,
                            ownership={'session':self.session,'group':self.group,'root_pid':self.child.pid,'token':self.token},reason=None)
        return self.child

    def assign(self, handle):
        if not self.api.AssignProcessToJobObject(self.job,handle):
            raise self.C.WinError(self.C.get_last_error())

    def belongs(self, pid, fields):
        if int(fields[3])!=self.session:return False
        # 同一専用session内でも兄弟QAを終了しない。exec前から渡した自分のtokenだけ。
        raw=Path('/proc',str(pid),'environ').read_bytes()
        prefix=(OWNER_KEY+'=').encode()
        owners=next((item[len(prefix):] for item in raw.split(b'\0') if item.startswith(prefix)),b'')
        if not owners:raise OSError('専用session内processのownership token未確認。終了しない')
        return self.token.encode() in owners.split(b',')

    def members(self):
        if not self.configured:raise OSError('所有監督が設定されていない')
        if os.name=='nt':
            class ACCOUNT(self.C.Structure):
                _fields_=[('total_user',self.C.c_int64),('total_kernel',self.C.c_int64),('period_user',self.C.c_int64),('period_kernel',self.C.c_int64),('page_faults',self.W.DWORD),('total',self.W.DWORD),('active',self.W.DWORD),('terminated',self.W.DWORD)]
            value=ACCOUNT()
            if not self.api.QueryInformationJobObject(self.job,1,self.C.byref(value),self.C.sizeof(value),None):
                raise self.C.WinError(self.C.get_last_error())
            return [{'active_count':value.active}] if value.active else []
        rows=[]
        for path in Path('/proc').iterdir():
            if not path.name.isdecimal():continue
            try:
                raw=(path/'stat').read_text();fields=raw[raw.rindex(')')+2:].split()
            except FileNotFoundError:continue
            # unreadable statは未確認へ伝播。全process終了を許可するものではない。
            pid=int(path.name);group=int(fields[2]);session=int(fields[3])
            if fields[0] in ('Z','X'):
                if session==self.session and (self.outer or group==self.group):
                    rows.append({'pid':pid,'state':fields[0],'group':group,'session':session,'start_ticks':int(fields[19])})
                continue
            try:owned=self.belongs(pid,fields)
            except (FileNotFoundError,ProcessLookupError):continue
            except OSError:
                # stat取得後に兄弟QAがexitするとenvironが空/EACCESになる。
                # 同じPID世代の終端を再読取りで確認できた時だけ除外する。
                try:
                    refreshed=(path/'stat').read_text();current=refreshed[refreshed.rindex(')')+2:].split()
                except (FileNotFoundError,ProcessLookupError):continue
                if int(current[19])==int(fields[19]) and current[0] in ('Z','X'):continue
                raise
            if owned:
                rows.append({'pid':pid,'state':fields[0],'group':group,'session':session,'start_ticks':int(fields[19])})
        self.row['observed_members']=rows
        # zombieは実行/handle保持を終えている。直接子waitと区別して記録する。
        return [row for row in rows if row['state'] not in ('Z','X')]

    def stop(self):
        self.row['stop_attempted']=True
        if not self.configured:
            self.row.update(stopped=False,reason='監督設定失敗。所有する直接子だけ停止、子孫未確認')
            if self.child is not None and self.child.poll() is None:self.child.kill()
            return
        if os.name=='nt':
            if not self.api.TerminateJobObject(self.job,1):raise self.C.WinError(self.C.get_last_error())
        else:
            # pidfdは観測PID再利用raceを防ぐ。同じ所属とstart_ticksを再確認後だけsignal。
            for row in self.members():
                try:
                    fd=os.pidfd_open(row['pid'])
                    try:
                        raw=Path('/proc',str(row['pid']),'stat').read_text();fields=raw[raw.rindex(')')+2:].split()
                        if fields[0] in ('Z','X'):continue
                        if int(fields[19])!=row['start_ticks'] or not self.belongs(row['pid'],fields):
                            raise OSError('所属/PID世代が変化。終了しない')
                        signal.pidfd_send_signal(fd,signal.SIGKILL)
                    finally:os.close(fd)
                except (ProcessLookupError,FileNotFoundError):continue

    def finish(self,deadline):
        # 直接子waitと所属停止の再確認を分ける。残量0なら追加待機しない。
        if not self.configured:
            self.stop();return False
        if time.monotonic()>=deadline:
            try:self.stop()
            except OSError as exc:self.row['stop_error']=repr(exc)
            self.row.update(stopped=False,reason='cleanup deadline exhausted; 所属停止の確認を行えない; '+self.row.get('stop_error',''));return False
        members=[];last_error=None
        while time.monotonic()<deadline:
            try:
                members=self.members()
                if not members:
                    self.row.update(stopped=True,reason=None);return True
                self.stop()
                last_error=None
            except OSError as exc:
                # 所有不明へsignalを送らない。同じ期限内の観測だけ再試行する。
                last_error=repr(exc)
            remaining=deadline-time.monotonic()
            if remaining>0:time.sleep(min(.002,remaining))
        self.row.update(stopped=False,reason=last_error or 'cleanup deadline exhausted; owned members='+str(members))
        return False

    def close(self):
        if self.job:
            self.api.CloseHandle(self.job);self.job=None
