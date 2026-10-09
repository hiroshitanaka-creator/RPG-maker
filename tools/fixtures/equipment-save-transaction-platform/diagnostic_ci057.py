#!/usr/bin/env python3
"""既存jobの判定に追加する057専用診断。失敗後にも各独立診断を実行し実exitを保持。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from process_capture import run_command, save
ROOT=Path(__file__).resolve().parents[3]

def main(args):
    area=Path(args.output).resolve();out=area/'task059';out.mkdir(parents=True,exist_ok=False)
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    code=(ROOT/'docs/verification/task059-save-qa-finalization/code-fixed-sha.txt').read_text().strip()
    engine=area/'bin'/('Godot_v4.7.2-stable_win64.exe' if sys.platform=='win32' else 'Godot_v4.7.2-stable_linux.x86_64')
    fixture=Path(__file__).parent
    commands=[('capture-tests',[sys.executable,str(fixture/'test_capture057.py'),'--output',str(out/'capture-tests')],180),
              ('scope059',[sys.executable,str(fixture/'scope059.py'),'--code-sha',code,'--source-sha',source,'--self-test','--output',str(out/'scope.json')],30),
              ('capture059',[sys.executable,str(fixture/'test_capture059.py'),'--output',str(out/'capture059')],180),
              ('baseline058',[sys.executable,str(fixture/'reproduce058.py'),'--checkout',str(area/'baseline058'),'--output',str(out/'baseline058')],30),
              ('measurements',[sys.executable,str(fixture/'diagnostics057.py'),'--godot',str(engine),'--output',str(out/'measurements')],180)]
    subprocess.run(['git','worktree','add','--detach',str(area/'baseline058'),'579ca1f463aaf9e93275039a59cf9d1ffb86adb5'],cwd=ROOT,check=True,timeout=30)
    rows=[];failures=[]
    for label,argv,budget in commands:
        path=out/(label+'-process.json')
        try:
            run_command(argv,out/(label+'.log'),path,cwd=ROOT,budget=budget,timeout_kind='diagnostic_outer_'+str(budget)+'_seconds')
        except Exception as exc:failures.append(label+': '+type(exc).__name__+': '+str(exc))
        row=json.loads(path.read_bytes());rows.append(dict(row,label=label))
        print((out/(label+'.log')).read_text(errors='replace'),flush=True)
        if row['supervision'].get('stopped') is not True:failures.append(label+': 専用tree停止未確認')
        if row['exit_code']!=0:failures.append(label+': exit='+str(row['exit_code']))
        save(out/'execution.json',dict(source_sha=source,code_sha=code,status='FAIL' if failures else 'PASS',commands=rows,failures=failures,acceptance='追加診断。既存job/全取引結果は独立維持'))
    print('DIAGNOSTIC_CI059_'+('FAIL' if failures else 'PASS')+' source='+source)
    return 1 if failures else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);sys.exit(main(p.parse_args()))
