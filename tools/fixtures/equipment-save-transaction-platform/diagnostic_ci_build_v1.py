#!/usr/bin/env python3
"""066 latest専用runner。旧commandと上限・失敗を保持し、固定065と最新を分離。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import native_build_contract_v1 as n
import generation_contract as g
from diagnostic_ci057 import capture_diagnostic, blocked_dependencies
from process_capture import save

ROOT=n.ROOT
COMMANDS=(*g.COMMANDS,'native-tests','native-fixed-tests','native-completed-contract','native-generation-tests')
SETUP=(*g.SETUP,'fixed065-checkout','native-fixed-checkouts')
BUDGETS=dict(g.BUDGETS,**{'fixed065-checkout':30,'native-tests':30,'native-fixed-tests':30,
                         'native-completed-contract':30,'native-generation-tests':30,'native-fixed-checkouts':30})


def execute(label,argv,budget,out,cwd,previous):
    blocked=blocked_dependencies(label,previous)
    if label in ('generation-contract','generation-tests'):
        blocked += [r['label'] for r in previous if r['label']=='fixed065-checkout' and r['exit_code']!=0]
    if label in ('native-fixed-tests','native-completed-contract'):
        blocked += ['native-fixed-checkouts'] if not any(r['label']=='native-fixed-checkouts' and
                    r['exit_code']==0 and r.get('supervision',{}).get('stopped') is True for r in previous) else []
    cap,errors=capture_diagnostic(argv,out/(label+'.log'),out/(label+'-process.json'),cwd,budget,
                                   pins=label=='generation-pins',blocked_by=sorted(set(blocked)))
    row=dict(cap.row,label=label)
    try:g.record_ok(cap.row,budget,ROOT)
    except Exception as exc:errors.append(str(exc))
    try:print((out/(label+'.log')).read_text(errors='replace'),flush=True)
    except OSError as exc:errors.append(str(exc))
    return row,errors


def exec_build(args):
    evidence=Path(args.output).resolve();area=evidence.parent/'native-build-v1'
    argv=[sys.executable,str(ROOT/'native/equipment_save_io/build.py'),'--platform',args.platform,'--output',str(evidence/'build')]
    # snapshotと同じ高分解能の単調時計。WindowsのGetTickCount64では別処理も同時刻になる。
    record=dict(argv=argv,started_ns=time.perf_counter_ns(),pid=None,exit_code=None,waited=False)
    # stdout/stderrは別々の原bytes。外側のOwnedTreeはwrapperとbuildの全子を監督する。
    try:
        with (area/'build-stdout.log').open('xb') as stdout,(area/'build-stderr.log').open('xb') as stderr:
            child=subprocess.Popen(argv,cwd=ROOT,stdout=stdout,stderr=stderr)
            record['pid']=child.pid;save(area/'build-child.json',record)
            record['exit_code']=child.wait();record['waited']=True
    finally:
        record['ended_ns']=time.perf_counter_ns()
        for stream in ('stdout','stderr'):
            path=area/('build-'+stream+'.log')
            record[stream+'_sha256']=n.digest(path.read_bytes()) if path.exists() else None
        save(area/'build-child.json',record)
    return record['exit_code'] if record['exit_code'] is not None else 1


def build(args):
    evidence=Path(args.output).resolve();area=evidence.parent/'native-build-v1';ident=n.identity(args)
    n.validate_prefix(area,ident,'after-shipped')
    dep=ROOT/'native/equipment_save_io/.deps/godot-cpp'
    preparation=[]
    if not dep.exists():
        for label,argv,cwd in (
            ('dependency-clone',['git','clone','--no-checkout',n.DEP_URL,str(dep)],ROOT),
            ('dependency-checkout',['git','checkout','--detach',n.PIN],dep)):
            row,errors=execute(label,argv,30,area,cwd,preparation);preparation.append(row)
            save(area/'dependency-processes.json',preparation)
            n.require(not errors,'依存準備失敗:'+str(errors))
    n.dependency(ROOT)
    n.capture(ROOT,area,'before-build',ident)
    before_byproducts=n.begin_byproducts(ROOT,area,evidence,ident)
    argv=[sys.executable,str(Path(__file__).resolve()),'--exec-build','--output',str(evidence),'--platform',args.platform]
    cap,errors=capture_diagnostic(argv,area/'build-supervisor.log',area/'build-process.json',ROOT,600)
    # 失敗後も直後の実物を保存。元buildの非0/timeout/停止未確認を成功に補完しない。
    snapshot_errors=[]
    try:n.preserve_byproducts(ROOT,area,evidence,ident,before_byproducts)
    except Exception as exc:snapshot_errors.append('副産物保全: '+str(exc))
    try:n.capture(ROOT,area,'after-build',ident)
    except Exception as exc:snapshot_errors.append(str(exc))
    n.write_new(area/'build-observation.json',dict(errors=errors+snapshot_errors,process=cap.row))
    n.validate_build(area,evidence,ident)
    n.byproduct_stage(area,evidence,ident,'after-build',record=True)
    n.require(not errors and not snapshot_errors,'build/直後照合失敗')
    return 0


def diagnostic(args):
    evidence=Path(args.output).resolve();out=evidence/'task059';out.mkdir(parents=True,exist_ok=False)
    source=g.git(ROOT,'rev-parse','HEAD').decode().strip()
    fixture=ROOT/g.FIXTURE
    baseline=evidence.parent/'qa059-baseline058';fixed=evidence.parent/'qa065-fixed059';fixed065=evidence.parent/'qa066-fixed065'
    fixed066=evidence.parent/'qa066-baseline';completed066=evidence.parent/'qa066-completed'
    engine=evidence/'bin'/('Godot_v4.7.2-stable_win64.exe' if args.platform=='windows' else 'Godot_v4.7.2-stable_linux.x86_64')
    commands=[
        ('capture-tests',[sys.executable,str(fixture/'test_capture057.py'),'--output',str(out/'capture-tests')],ROOT),
        ('scope059',[sys.executable,str(fixed/g.FIXTURE/'scope059.py'),'--checkout',str(fixed),'--code-sha',g.FIXED059,'--source-sha',g.FIXED059,'--self-test','--output',str(out/'scope.json')],fixed),
        ('capture059',[sys.executable,str(fixture/'test_capture059.py'),'--output',str(out/'capture059')],ROOT),
        ('baseline058',[sys.executable,str(fixture/'reproduce058.py'),'--checkout',str(baseline),'--output',str(out/'baseline058')],ROOT),
        ('measurements',[sys.executable,str(fixture/'diagnostics057.py'),'--godot',str(engine),'--output',str(out/'measurements')],ROOT),
        ('generation-contract',[sys.executable,str(fixed065/g.FIXTURE/'generation_contract.py'),'--source-sha',n.BASE,'--code-sha',n.CODE065,'--output',str(out/'generation.json')],fixed065),
        ('generation-tests',[sys.executable,str(fixed065/g.FIXTURE/'test_generation_contract.py'),'--code-sha',n.CODE065,'--output',str(out/'generation-tests')],fixed065),
        ('native-tests',[sys.executable,str(fixture/'test_native_build_contract_v1.py'),'--output',str(out/'native-tests')],ROOT),
        ('native-fixed-tests',[sys.executable,str(fixed066/g.FIXTURE/'test_native_build_contract_v1.py'),'--output',str(out/'native-fixed-tests')],fixed066),
        ('native-completed-contract',[sys.executable,str(completed066/g.FIXTURE/'native_build_contract_v1.py'),'--completed-contract',
                                      '--checkout',str(completed066),'--output',str(out/'completed066.json')],completed066),
        ('native-generation-tests',[sys.executable,str(fixture/'native_build_contract_v1.py'),'--generation-tests',
                                   '--output',str(out/'native-generation-tests')],ROOT)]
    setups=[
        ('generation-pins',[sys.executable,str(fixture/'generation_contract.py'),'--fetch-pins','--output',str(out/'pins.json')],ROOT),
        ('baseline-checkout',['git','worktree','add','--detach',str(baseline),g.BASE059],ROOT),
        ('fixed059-checkout',['git','worktree','add','--detach',str(fixed),g.FIXED059],ROOT),
        ('fixed065-checkout',['git','worktree','add','--detach',str(fixed065),n.BASE],ROOT),
        ('native-fixed-checkouts',[sys.executable,str(fixture/'native_build_contract_v1.py'),'--prepare-generations','--output',str(out)],ROOT)]
    report=dict(schema=5,source_sha=source,fixed059=g.FIXED059,fixed065=n.BASE,code065=n.CODE065,identity=n.identity(args),
                checkout=str(ROOT),setup=[],commands=[],failures=[],status='RUNNING')
    try:report['generation_approval']=n.generation_policy()
    except Exception as exc:report['generation_approval']=None;report['failures'].append('承認未提供: '+str(exc))
    save(out/'execution.json',report)
    try:n.validate_prefix(evidence.parent/'native-build-v1',report['identity'],'after-tests')
    except Exception as exc:report['failures'].append('実QA前後:'+str(exc))
    for kind,items in (('setup',setups),('commands',commands)):
        for label,argv,cwd in items:
            if label=='scope059':
                try:report['fixed059_before']=g.fixed_checkout(fixed)
                except Exception as exc:report['failures'].append(str(exc))
            if label=='generation-contract':
                try:
                    n.require(g.git(fixed065,'rev-parse','HEAD').decode().strip()==n.BASE,'065固定HEAD')
                    n.require(not g.git(fixed065,'status','--porcelain','--untracked-files=all'),'065固定dirty')
                    g.scope(fixed065,n.CODE065,n.BASE)
                    report['fixed065_before']=g.snapshot(fixed065/g.FIXTURE)
                except Exception as exc:report['failures'].append(str(exc))
            if label in ('native-fixed-tests','native-completed-contract') and report['generation_approval'] is not None:
                try:
                    sha=report['generation_approval']['baseline_sha' if label=='native-fixed-tests' else 'completion_sha']
                    report[label+'-before']=n.fixed_generation_state(cwd,sha)
                except Exception as exc:report['failures'].append(str(exc))
            row,errors=execute(label,argv,BUDGETS[label],out,cwd,report['setup']+report['commands'])
            report[kind].append(row);report['failures'].extend(label+': '+x for x in errors)
            if label=='scope059':
                try:report['fixed059_after']=g.fixed_checkout(fixed)
                except Exception as exc:report['failures'].append(str(exc))
            if label=='generation-tests':
                try:
                    # __pycache__はGit対象外。原固定codeはGit diffとtracked原bytesで照合する。
                    n.require(not g.git(fixed065,'status','--porcelain','--untracked-files=all'),'065固定実行後dirty')
                    for path in g.CODE:
                        n.require((fixed065/path).read_bytes()==g.git(ROOT,'show',n.CODE065+':'+path),'旧065 code原bytes')
                    report['fixed065_after']=dict(sha=n.BASE,code_sha=n.CODE065,tracked_clean=True)
                except Exception as exc:report['failures'].append(str(exc))
            if label in ('native-fixed-tests','native-completed-contract') and report['generation_approval'] is not None:
                try:
                    sha=report['generation_approval']['baseline_sha' if label=='native-fixed-tests' else 'completion_sha']
                    report[label+'-after']=n.fixed_generation_state(cwd,sha)
                    n.require(report[label+'-before']==report[label+'-after'],'066固定検査器/対象差替え')
                except Exception as exc:report['failures'].append(str(exc))
            save(out/'execution.json',report)
    try:
        n.capture(ROOT,evidence.parent/'native-build-v1','after-diagnostics',report['identity'])
        n.byproduct_stage(evidence.parent/'native-build-v1',evidence,report['identity'],'after-diagnostics',record=True)
    except Exception as exc:report['failures'].append('診断後原bytes:'+str(exc))
    report['status']='FAIL' if report['failures'] else 'PASS';save(out/'execution.json',report)
    save(out/'generation-manifest.json',g.snapshot(out,('generation-manifest.json',)))
    print('DIAGNOSTIC_BUILD_V1_'+report['status'],flush=True)
    return 1 if report['failures'] else 0


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--platform',choices=('linux','windows'),required=True)
    p.add_argument('--phase',choices=('transaction','primitives'),default='primitives');p.add_argument('--profile',default='latest')
    p.add_argument('--run-id',default='local-066');p.add_argument('--exec-build',action='store_true');p.add_argument('--build',action='store_true')
    args=p.parse_args()
    try:sys.exit(exec_build(args) if args.exec_build else build(args) if args.build else diagnostic(args))
    except Exception as exc:print('DIAGNOSTIC_BUILD_V1_FAIL: '+type(exc).__name__+': '+str(exc),flush=True);sys.exit(1)
