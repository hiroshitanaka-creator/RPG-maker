#!/usr/bin/env python3
"""既存jobの判定に追加する059最新専用診断（057固定は別checkout）。失敗後にも各独立診断を実行し実exitを保持。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from process_capture import ProcessCapture, save
ROOT=Path(__file__).resolve().parents[3]

def main(args):
    area=Path(args.output).resolve();out=area/'task059';out.mkdir(parents=True,exist_ok=False)
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    code=(ROOT/'docs/verification/task059-save-qa-finalization/code-fixed-sha.txt').read_text().strip()
    engine=area/'bin'/('Godot_v4.7.2-stable_win64.exe' if sys.platform=='win32' else 'Godot_v4.7.2-stable_linux.x86_64')
    fixture=Path(__file__).parent
    baseline=area.parent/'qa059-baseline058' # 原checkoutは証拠archive対象の外。原証拠だけoutに保存する。
    commands=[('capture-tests',[sys.executable,str(fixture/'test_capture057.py'),'--output',str(out/'capture-tests')],180),
              ('scope059',[sys.executable,str(fixture/'scope059.py'),'--code-sha',code,'--source-sha',source,'--self-test','--output',str(out/'scope.json')],30),
              ('capture059',[sys.executable,str(fixture/'test_capture059.py'),'--output',str(out/'capture059')],180),
              ('baseline058',[sys.executable,str(fixture/'reproduce058.py'),'--checkout',str(baseline),'--output',str(out/'baseline058')],30),
              ('measurements',[sys.executable,str(fixture/'diagnostics057.py'),'--godot',str(engine),'--output',str(out/'measurements')],180)]
    rows=[];setup=[];failures=[]
    report=dict(schema=2,source_sha=source,code_sha=code,status='RUNNING',setup=setup,commands=rows,failures=failures,acceptance='追加診断。既存job/全取引結果は独立維持')
    save(out/'execution.json',report)
    def execute(label,argv,budget,destination):
        path=out/(label+'-process.json')
        deadline=time.monotonic()+budget
        capture=ProcessCapture(argv,out/(label+'.log'),path,cwd=ROOT,deadline=deadline,cleanup_deadline=deadline,budget=budget,timeout_kind='diagnostic_outer_'+str(budget)+'_seconds')
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
        report['status']='FAIL' if failures else 'RUNNING';save(out/'execution.json',report)
    execute('baseline-checkout',['git','worktree','add','--detach',str(baseline),'579ca1f463aaf9e93275039a59cf9d1ffb86adb5'],30,setup)
    for label,argv,budget in commands:execute(label,argv,budget,rows)
    report['status']='FAIL' if failures else 'PASS';save(out/'execution.json',report)
    print('DIAGNOSTIC_CI059_'+('FAIL' if failures else 'PASS')+' source='+source)
    return 1 if failures else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);sys.exit(main(p.parse_args()))
