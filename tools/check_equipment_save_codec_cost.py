#!/usr/bin/env python3
"""060: 固定本番の専用checkoutで計測対照を監督し、指定名へ原物を保存する。"""
from __future__ import annotations
import argparse
import base64
import collections
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'tools/fixtures/equipment-save-codec-cost'
sys.path.insert(0, str(FIXTURE))
from instrument_copy import BASE, HASHES, instrument
sys.path.insert(0, str(ROOT/'tools/fixtures/equipment-save-transaction-platform'))
from process_capture import ProcessCapture
BAD = re.compile(rb'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|Fontconfig error|_FAIL:')
RUN_FILES = ['argv.json','environment.json','measurements.json','results.json','stdout.log','stderr.log','exit.json','inputs.json','generated-diff.patch','hashes.json']


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def environment(engine, mode, source):
    return dict(os=platform.platform(),cpu=next((x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.startswith('model name')),platform.processor()) if sys.platform.startswith('linux') else platform.processor(),cpu_count=os.cpu_count(),python=sys.version,engine=str(engine),engine_sha256=digest(engine.read_bytes()),source_sha=source,base_sha=BASE,mode=mode,case_workers=8 if os.name=='nt' else 16,restart_workers=2 if os.name=='nt' else 4,batch_roots=4,budgets=dict(codec=120,transaction_outer=180,transaction_inner=174,transaction_child=30,import_seconds=600),clock='monotonic microseconds per process; parallel cumulative is not wall',limits={p:Path(p).read_text().strip() for p in ['/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/memory.max'] if Path(p).exists()})


def profile(area):
    env = os.environ.copy()
    for key in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME','APPDATA','LOCALAPPDATA']:
        path = area/'profile'/key; path.mkdir(parents=True,exist_ok=True); env[key]=str(path)
    return env


def command(argv, area, cwd, env, budget):
    area.mkdir(parents=True,exist_ok=True)
    save(area/'exec.json',dict(argv=argv,stdout=str(area/'stdout.log'),stderr=str(area/'stderr.log'),cwd=str(cwd)))
    deadline=time.monotonic()+budget
    capture=ProcessCapture([sys.executable,str(Path(__file__).resolve()),'--exec-json',str(area/'exec.json')],area/'supervisor.log',area/'process.json',cwd=cwd,env=env,deadline=deadline,cleanup_deadline=deadline,budget=budget,timeout_kind='cost060_outer_'+str(budget))
    error=None
    try:
        with capture:capture.wait()
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    row=dict(capture.row,requested_argv=argv,runner_error=error)
    row['clean_logs']=not any(BAD.search(p.read_bytes()) for p in [area/'stdout.log',area/'stderr.log',area/'supervisor.log'] if p.exists())
    row['ok']=row['exit_code']==0 and row['supervision'].get('stopped') is True and row['clean_logs'] and not row['timed_out']
    save(area/'execution.json',row)
    return row


def archive(area):
    # 一時project/キャッシュは入れない。旧検査が出す原証拠は全regular fileを保持。
    files={}
    for path in sorted(area.rglob('*')):
        if path.is_file() and not path.is_symlink():
            rel=path.relative_to(area).as_posix()
            if 'profile' in path.relative_to(area).parts and path.suffix!='.log':continue
            files[rel]=path.read_bytes()
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w') as tar:
        for name,raw in files.items():
            member=tarfile.TarInfo(name);member.size=len(raw);member.mtime=0;member.mode=0o644;tar.addfile(member,io.BytesIO(raw))
    packed=gzip.compress(buffer.getvalue(),mtime=0)
    return dict(format='tar+gzip+base64',sha256=digest(packed),bytes=len(packed),data=base64.b64encode(packed).decode(),members={name:dict(bytes=len(raw),sha256=digest(raw)) for name,raw in files.items()}),files


def summarize(files):
    labels={};roots=[];errors=[];groups=[]
    for name,raw in files.items():
        if not name.endswith('.log') or name=='supervisor.log' or '/profile/' in name:continue
        for line in raw.splitlines():
            if not line.startswith(b'COST060 '):continue
            try:
                group=json.loads(line[8:]);spans=group['spans'];identity=(group['pid'],group['sequence'])
                if identity in groups:raise ValueError('spanの重複')
                groups.append(identity)
                for index,span in enumerate(spans):
                    elapsed=span['end_us']-span['start_us'];children=[s for s in spans if s['parent']==index]
                    exclusive=elapsed-sum(s['end_us']-s['start_us'] for s in children)
                    assert exclusive>=0 and elapsed>=0
                    for child in children:assert span['start_us']<=child['start_us']<=child['end_us']<=span['end_us']
                    row=labels.setdefault(span['label'],dict(count=0,inclusive_us=0,exclusive_us=0,parents=collections.Counter()))
                    row['count']+=1;row['inclusive_us']+=elapsed;row['exclusive_us']+=exclusive
                    row['parents'][spans[span['parent']]['label'] if span['parent']>=0 else '(root)']+=1
                    if span['parent']==-1:roots.append(dict(log=name,pid=group['pid'],sequence=group['sequence'],label=span['label'],start_us=span['start_us'],end_us=span['end_us']))
            except Exception as exc:errors.append(dict(log=name,line=line.decode(errors='replace'),error=str(exc)))
    return dict(labels=labels,roots=roots,errors=errors,units='microseconds',scope='完結したspanのみ。kill/timeout時の未出力部分は未測。並行累積をwall寄与率にしない。',group_count=len(groups))


def inputs(files, cases):
    observations=[]
    for name,raw in files.items():
        if not (name.endswith('/source.json') or name.endswith('/input.bin')):continue
        row=dict(path=name,bytes=len(raw),sha256=digest(raw),storage='native-or-invalid',metadata=None)
        try:
            doc=json.loads(raw);row['storage']='plain'
            if isinstance(doc,dict):
                if doc.get('_storage_format')=='gzip-json-v1':
                    row['storage']='gzip';doc=json.loads(gzip.decompress(base64.b64decode(doc['payload'])))
                row['metadata']='_saved_value_types' in doc
        except (ValueError,TypeError,KeyError,OSError):
            # Godot native Variant/壊れJSONはJSONとして再解釈しない。
            row['not_json_reason']='native Variantまたは拒否対象raw。原bytesで照合する。'
        observations.append(row)
    return dict(expected_transaction_cases=cases['transaction_cases'],initial_seed_distribution=cases['seed_distribution'],observed=observations)


def run(args):
    assert args.base_sha==BASE,'承認基点以外は禁止'
    engine=Path(args.godot).resolve();output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    assert engine.is_file()
    source=git('rev-parse','HEAD');cases=json.loads((FIXTURE/'cases.json').read_bytes())
    for path,sha in cases['fixed_sources'].items():assert digest((ROOT/path).read_bytes())==sha,'原検査器不変:'+path
    for name,sha in HASHES.items():assert digest((ROOT/'scripts/game'/name).read_bytes())==sha,'最新本番不変:'+name
    area=Path(tempfile.mkdtemp(prefix='qa060-',dir='/workspace'))
    index=dict(base_sha=BASE,code_sha=source,temporary_area=str(area),runs=[],preparation=[],status='RUNNING')
    save(output/'inventory.json',index)
    checkouts={};patch='';generated={}
    for mode in ['off','on']:
        checkout=area/('checkout-'+mode)
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        shutil.copyfile(ROOT/'tools/check_equipment_save_codec_cost.gd',checkout/'tools/check_equipment_save_codec_cost.gd')
        if mode=='on':generated,patch=instrument(checkout)
        checkouts[mode]=checkout
        prep=area/('import-'+mode);env=profile(prep)
        version=command([str(engine),'--version'],prep/'version',checkout,env,30)
        assert version['ok'] and b'4.7.2.stable.official.ed1daf0bf' in (prep/'version/stdout.log').read_bytes(),'指定公式engine未確認'
        imported=command([str(engine),'--headless','--editor','--path',str(checkout),'--import','--quit'],prep/'import',checkout,env,600)
        packed,_=archive(prep);index['preparation'].append(dict(mode=mode,version=version,import_result=imported,archive=packed));save(output/'inventory.json',index)
        if not imported['ok']:raise RuntimeError('import失敗。原logをinventoryへ保存済み:'+mode)
    number=0
    for phase in ['codec','transaction']:
        for repetition,modes in enumerate(cases['order'],1):
            for mode in modes:
                number+=1;name=f'run-{platform.system().lower()}-{mode}-{number:02d}'
                destination=output/name;destination.mkdir(exist_ok=False)
                work=area/name;work.mkdir();checkout=checkouts[mode];env=profile(work)
                save(destination/'environment.json',dict(environment(engine,mode,source),phase=phase,repetition=repetition,fixture_contract_sha256=digest((FIXTURE/'cases.json').read_bytes()),generated=generated if mode=='on' else {}))
                (destination/'generated-diff.patch').write_text(patch if mode=='on' else '')
                if phase=='codec':
                    env['EQUIPMENT_CODEC_EVIDENCE']=str(work/'evidence')
                    argv=[str(engine),'--headless','--path',str(checkout),'--script','res://tools/check_equipment_save_codec.gd'];budget=120
                else:
                    argv=[sys.executable,str(checkout/'tools/check_equipment_save_transaction_platform.py'),'--godot',str(engine),'--fixture-root',str(work/'fixtures'),'--output',str(work/'evidence')];budget=180
                save(destination/'argv.json',dict(argv=argv,budget=budget,cwd=str(checkout),phase=phase,mode=mode,repetition=repetition))
                print('060 START',name,phase,repetition,flush=True)
                row=command(argv,work,checkout,env,budget)
                for stream in ['stdout.log','stderr.log']:
                    (destination/stream).write_bytes((work/stream).read_bytes() if (work/stream).exists() else b'')
                save(destination/'exit.json',row)
                packed,files=archive(work)
                summary_path='evidence/codec.json' if phase=='codec' else 'evidence/summary.json'
                summary=json.loads(files[summary_path]) if summary_path in files else None
                save(destination/'results.json',dict(phase=phase,mode=mode,repetition=repetition,summary=summary,archive=packed))
                save(destination/'measurements.json',summarize(files))
                save(destination/'inputs.json',inputs(files,cases))
                save(destination/'hashes.json',{p.name:dict(sha256=digest(p.read_bytes()),bytes=p.stat().st_size) for p in destination.iterdir() if p.name!='hashes.json'})
                assert sorted(p.name for p in destination.iterdir())==sorted(RUN_FILES)
                index['runs'].append(dict(name=name,phase=phase,mode=mode,repetition=repetition,seconds=row['seconds'],exit_code=row['exit_code'],ok=row['ok'],hashes_sha256=digest((destination/'hashes.json').read_bytes())))
                save(output/'inventory.json',index)
                print('060 END',name,'seconds',round(row['seconds'],3),'exit',row['exit_code'],flush=True)
    index['status']='RECORDED';save(output/'inventory.json',index)
    return 0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--godot');parser.add_argument('--base-sha');parser.add_argument('--output');parser.add_argument('--exec-json')
    args=parser.parse_args()
    if args.exec_json:
        spec=json.loads(Path(args.exec_json).read_bytes())
        with open(spec['stdout'],'wb',buffering=0) as out,open(spec['stderr'],'wb',buffering=0) as err:
            os.dup2(out.fileno(),1);os.dup2(err.fileno(),2)
            os.chdir(spec['cwd']);os.execvpe(spec['argv'][0],spec['argv'],os.environ.copy())
    else:
        try:sys.exit(run(args))
        except Exception as exc:print('COST060_FAIL:',type(exc).__name__,str(exc));sys.exit(1)
