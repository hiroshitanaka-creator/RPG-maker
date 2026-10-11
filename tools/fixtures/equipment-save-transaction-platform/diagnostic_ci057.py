#!/usr/bin/env python3
"""既存jobの判定に追加する059最新専用診断（057固定は別checkout）。失敗後にも各独立診断を実行し実exitを保持。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from process_capture import ProcessCapture, save
import generation_contract as generation
ROOT=Path(__file__).resolve().parents[3]


def capture_diagnostic(argv, log, path, cwd, budget, *, pins=False, blocked_by=()):
    start=time.monotonic();hard_deadline=start+budget
    # pinsの実行25秒と回収5秒を元30秒の内側へ置く。全体上限は延長しない。
    deadline=hard_deadline-budget/6 if pins else hard_deadline
    capture=ProcessCapture(argv,log,path,cwd=cwd,deadline=deadline,cleanup_deadline=hard_deadline,
                           budget=budget,timeout_kind='pins_execution_with_cleanup_inside_budget' if pins else 'diagnostic_outer_'+str(budget)+'_seconds')
    failures=[]
    if blocked_by:
        reason='依存失敗により未起動: '+', '.join(blocked_by)
        capture.row['blocked_by']=list(blocked_by)
        capture.row['execution_status']='NOT_RUN'
        # 未起動を0や停止済みに補完しない。予定argvと親の理由logだけを保存する。
        Path(log).write_text(reason+'\n',encoding='utf-8')
        error=RuntimeError(reason)
        capture.__exit__(type(error),error,None)
        failures.append(reason)
    else:
        try:
            with capture:capture.wait()
        except Exception as exc:failures.append(type(exc).__name__+': '+str(exc))
    return capture,failures


def blocked_dependencies(label, previous):
    required={'scope059':('fixed059-checkout',),'baseline058':('baseline-checkout',),
              'generation-contract':('generation-pins',),'generation-tests':('generation-pins',)}.get(label,())
    # 起動したtreeの終了が未確認なら、新しい子を起動してGit書込み等を競合させない。
    unsafe=[row['label'] for row in previous if row.get('pid') is not None and
            row.get('supervision',{}).get('stopped') is not True]
    failed=[name for name in required if not any(row['label']==name and row.get('exit_code')==0 and
            row.get('supervision',{}).get('stopped') is True for row in previous)]
    return sorted(set(unsafe+failed))

def main(args):
    area=Path(args.output).resolve();out=area/'task059';out.mkdir(parents=True,exist_ok=False)
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    code=(ROOT/'docs/verification/task059-save-qa-finalization/code-fixed-sha.txt').read_text().strip()
    generation_code=generation.pin(ROOT)
    generation.require(code == generation.FIXED059, '059固定SHAすり替え')
    engine=area/'bin'/('Godot_v4.7.2-stable_win64.exe' if sys.platform=='win32' else 'Godot_v4.7.2-stable_linux.x86_64')
    fixture=Path(__file__).parent
    baseline=area.parent/'qa059-baseline058' # 原checkoutは証拠archive対象の外。原証拠だけoutに保存する。
    fixed=area.parent/'qa065-fixed059'
    commands=[('capture-tests',[sys.executable,str(fixture/'test_capture057.py'),'--output',str(out/'capture-tests')],180),
              ('scope059',[sys.executable,str(fixed/generation.FIXTURE/'scope059.py'),'--checkout',str(fixed),'--code-sha',code,'--source-sha',code,'--self-test','--output',str(out/'scope.json')],30),
              ('capture059',[sys.executable,str(fixture/'test_capture059.py'),'--output',str(out/'capture059')],180),
              ('baseline058',[sys.executable,str(fixture/'reproduce058.py'),'--checkout',str(baseline),'--output',str(out/'baseline058')],30),
              ('measurements',[sys.executable,str(fixture/'diagnostics057.py'),'--godot',str(engine),'--output',str(out/'measurements')],180),
              ('generation-contract',[sys.executable,str(fixture/'generation_contract.py'),'--source-sha',source,'--output',str(out/'generation.json')],30),
              ('generation-tests',[sys.executable,str(fixture/'test_generation_contract.py'),'--output',str(out/'generation-tests')],30)]
    rows=[];setup=[];failures=[]
    report=dict(schema=3,source_sha=source,code_sha=code,generation_code_sha=generation_code,checkout=str(ROOT),
                targets={label:code if label=='scope059' else source for label in generation.SETUP+generation.COMMANDS},
                status='RUNNING',setup=setup,commands=rows,failures=failures,acceptance='059固定範囲と最新継続診断。既存job/全取引結果は独立維持')
    save(out/'execution.json',report)
    def execute(label,argv,budget,destination):
        blocked=blocked_dependencies(label,setup+rows)
        if label=='scope059' and not blocked:
            try:report['fixed_checkout_before']=generation.fixed_checkout(fixed)
            except Exception as exc:failures.append('固定checkout開始: '+str(exc))
        path=out/(label+'-process.json')
        capture,errors=capture_diagnostic(argv,out/(label+'.log'),path,fixed if label=='scope059' else ROOT,budget,
                                         pins=label=='generation-pins',blocked_by=blocked)
        failures.extend(label+': '+error for error in errors)
        # 保存失敗時も所有captureの実状態を上位に残す。欠落を未起動へ補完しない。
        row=dict(capture.row,label=label);destination.append(row)
        try:
            persisted=json.loads(path.read_bytes())
            if persisted!=capture.row:failures.append(label+': 原process記録と所有状態が不一致')
        except (OSError,ValueError) as exc:failures.append(label+': process記録未確認: '+str(exc))
        try:print((out/(label+'.log')).read_text(errors='replace'),flush=True)
        except OSError as exc:failures.append(label+': log未確認: '+str(exc))
        if row['supervision'].get('stopped') is not True:failures.append(label+': 専用tree停止未確認')
        if row['exit_code']!=0:failures.append(label+': exit='+str(row['exit_code']))
        if not row['record_saved']:failures.append(label+': 原process記録の保存失敗')
        if label=='scope059' and not blocked:
            try:report['fixed_checkout_after']=generation.fixed_checkout(fixed)
            except Exception as exc:failures.append('固定checkout終了: '+str(exc))
        try:generation.record_ok(row,budget)
        except (ValueError,KeyError,TypeError) as exc:failures.append(label+': '+str(exc))
        report['status']='FAIL' if failures else 'RUNNING';save(out/'execution.json',report)
    execute('generation-pins',[sys.executable,str(fixture/'generation_contract.py'),'--fetch-pins','--output',str(out/'pins.json')],30,setup)
    execute('baseline-checkout',['git','worktree','add','--detach',str(baseline),'579ca1f463aaf9e93275039a59cf9d1ffb86adb5'],30,setup)
    execute('fixed059-checkout',['git','worktree','add','--detach',str(fixed),code],30,setup)
    for label,argv,budget in commands:execute(label,argv,budget,rows)
    report['status']='FAIL' if failures else 'PASS';save(out/'execution.json',report)
    save(out/'generation-manifest.json',generation.snapshot(out,('generation-manifest.json',)))
    try:generation.validate_execution(out,source,generation_code)
    except Exception as exc:
        failures.append('原証拠契約: '+type(exc).__name__+': '+str(exc))
        report['status']='FAIL';save(out/'execution.json',report)
        save(out/'generation-manifest.json',generation.snapshot(out,('generation-manifest.json',)))
    print('DIAGNOSTIC_CI059_'+('FAIL' if failures else 'PASS')+' source='+source)
    return 1 if failures else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);sys.exit(main(p.parse_args()))
