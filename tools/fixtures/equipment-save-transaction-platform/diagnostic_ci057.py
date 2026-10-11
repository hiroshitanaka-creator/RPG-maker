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
        if label=='scope059':
            try:report['fixed_checkout_before']=generation.fixed_checkout(fixed)
            except Exception as exc:failures.append('固定checkout開始: '+str(exc))
        path=out/(label+'-process.json')
        deadline=time.monotonic()+budget
        capture=ProcessCapture(argv,out/(label+'.log'),path,cwd=fixed if label=='scope059' else ROOT,deadline=deadline,cleanup_deadline=deadline,budget=budget,timeout_kind='diagnostic_outer_'+str(budget)+'_seconds')
        try:
            with capture:capture.wait()
        except Exception as exc:failures.append(label+': '+type(exc).__name__+': '+str(exc))
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
        if label=='scope059':
            try:report['fixed_checkout_after']=generation.fixed_checkout(fixed)
            except Exception as exc:failures.append('固定checkout終了: '+str(exc))
        try:generation.record_ok(row,budget)
        except (ValueError,KeyError,TypeError) as exc:failures.append(label+': '+str(exc))
        report['status']='FAIL' if failures else 'RUNNING';save(out/'execution.json',report)
    execute('generation-pins',[sys.executable,str(fixture/'generation_contract.py'),'--fetch-pins'],30,setup)
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
