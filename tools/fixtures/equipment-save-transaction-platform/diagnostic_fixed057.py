"""059世代配線だけ。057完全SHA checkoutの当時helper/検査/期待を実行する。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main(args):
    root=Path(args.checkout).resolve();area=Path(args.output).resolve();out=area/'task057-fixed';out.mkdir(parents=True,exist_ok=False)
    code='3cf4b6c293f6796220b43cf566f8eb792c3932ec'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==code
    fixture=root/'tools/fixtures/equipment-save-transaction-platform';sys.path.insert(0,str(fixture))
    from process_capture import run_command,save
    engine=area/'bin'/('Godot_v4.7.2-stable_win64.exe' if sys.platform=='win32' else 'Godot_v4.7.2-stable_linux.x86_64')
    commands=[('capture-tests',[sys.executable,str(fixture/'test_capture057.py'),'--output',str(out/'capture-tests')],180),
              ('scope057',[sys.executable,str(fixture/'scope057.py'),'--code-sha',code,'--source-sha',code,'--self-test','--output',str(out/'scope.json')],30),
              ('measurements',[sys.executable,str(fixture/'diagnostics057.py'),'--godot',str(engine),'--output',str(out/'measurements')],180)]
    rows=[];failures=[]
    for label,argv,budget in commands:
        path=out/(label+'-process.json')
        try:run_command(argv,out/(label+'.log'),path,cwd=root,budget=budget)
        except Exception as exc:failures.append(label+': '+repr(exc))
        row=json.loads(path.read_bytes());rows.append(dict(row,label=label))
        print((out/(label+'.log')).read_text(errors='replace'),flush=True)
        if row['exit_code']!=0:failures.append(label+': exit='+str(row['exit_code']))
        save(out/'execution.json',dict(source_sha=code,code_sha=code,status='FAIL' if failures else 'PASS',commands=rows,failures=failures,acceptance='057固定。当時のprocess_capture/test_capture/scope/diagnostics。059へscope不変を適用しない'))
    return 1 if failures else 0


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkout',required=True);p.add_argument('--output',required=True);sys.exit(main(p.parse_args()))
