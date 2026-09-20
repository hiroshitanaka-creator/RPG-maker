"""自分で起動した検査用Godotだけを終了し、履歴復旧を別プロセスで確認する。"""
import argparse
import os
from pathlib import Path
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parent.parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--godot',required=True)
    args=parser.parse_args()
    token=uuid.uuid4().hex
    marker=ROOT/'.tools'/f'restart-ready-{token}.json'
    executable=Path(args.godot).resolve()
    if os.name=='nt' and executable.name.endswith('_console.exe'):
        executable=executable.with_name(executable.name.replace('_console.exe','.exe'))
    base=[str(executable),'--headless','--path','.','--script','res://tools/check_record_restart.gd','--']
    output_path=ROOT/'.tools'/f'restart-{token}.log'
    error_path=ROOT/'.tools'/f'restart-{token}-errors.log'
    output_file=output_path.open('wb')
    error_file=error_path.open('wb')
    options={'cwd':ROOT,'stdout':output_file,'stderr':error_file,'stdin':subprocess.DEVNULL}
    if os.name=='nt':
        startup=subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        options['startupinfo']=startup
    process=subprocess.Popen(base+['--writer',token],**options)
    try:
        deadline=time.monotonic()+20
        while not marker.exists() and time.monotonic()<deadline and process.poll() is None:
            time.sleep(.05)
        if not marker.exists():
            if process.poll() is None:process.kill()
            process.wait(timeout=10)
            raise AssertionError('保存完了の合図が来ない: '+output_path.read_text(encoding='utf-8',errors='replace')+error_path.read_text(encoding='utf-8',errors='replace'))
        assert process.poll() is None, '強制終了前に子が終了した'
        process.kill()
        process.wait(timeout=10)
        reader=subprocess.run(base+['--reader',token],timeout=30,**options)
        output=output_path.read_text(encoding='utf-8',errors='replace')
        errors=error_path.read_text(encoding='utf-8',errors='replace')
        print(output)
        assert reader.returncode==0 and 'RESTART_PASS:' in output and not errors,(reader.returncode,errors)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        output_file.close()
        error_file.close()
        if marker.exists():marker.unlink()

if __name__=='__main__':main()
