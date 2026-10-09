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
    area=Path(args.output).resolve();out=area/'task057';out.mkdir(parents=True,exist_ok=False)
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    code=(ROOT/'docs/verification/task057-save-qa-diagnostics/code-fixed-sha.txt').read_text().strip()
    engine=area/'bin'/('Godot_v4.7.2-stable_win64.exe' if sys.platform=='win32' else 'Godot_v4.7.2-stable_linux.x86_64')
    fixture=Path(__file__).parent
    commands=[('capture-tests',[sys.executable,str(fixture/'test_capture057.py'),'--output',str(out/'capture-tests')],180),
              ('scope057',[sys.executable,str(fixture/'scope057.py'),'--code-sha',code,'--source-sha',source,'--self-test','--output',str(out/'scope.json')],30),
              ('measurements',[sys.executable,str(fixture/'diagnostics057.py'),'--godot',str(engine),'--output',str(out/'measurements')],180)]
    rows=[];failures=[]
    for label,argv,budget in commands:
        path=out/(label+'-process.json')
        try:
            run_command(argv,out/(label+'.log'),path,cwd=ROOT,budget=budget,timeout_kind='diagnostic_outer_'+str(budget)+'_seconds')
        except Exception as exc:failures.append(label+': '+type(exc).__name__+': '+str(exc))
        row=json.loads(path.read_bytes());rows.append(dict(row,label=label))
        print((out/(label+'.log')).read_text(errors='replace'),flush=True)
        if row['exit_code']!=0:failures.append(label+': exit='+str(row['exit_code']))
        save(out/'execution.json',dict(source_sha=source,code_sha=code,status='FAIL' if failures else 'PASS',commands=rows,failures=failures,acceptance='追加診断。既存job/全取引結果は独立維持'))
    print('DIAGNOSTIC_CI057_'+('FAIL' if failures else 'PASS')+' source='+source)
    return 1 if failures else 0
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);sys.exit(main(p.parse_args()))
