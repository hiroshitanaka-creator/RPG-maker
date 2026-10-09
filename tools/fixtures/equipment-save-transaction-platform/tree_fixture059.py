"""059専用の有限寿命process tree。実保存・実174/180秒検査ではない。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main(args):
    area=Path(args.area); area.mkdir(parents=True,exist_ok=True)
    if args.mode in ('grandchild','sentinel'):
        (area/(args.mode+'.json')).write_text(json.dumps({'pid':os.getpid(),'ppid':os.getppid()})+'\n')
        until=time.monotonic()+10
        while not (area/'release').exists() and time.monotonic()<until:
            (area/(args.mode+'.heartbeat')).write_text(str(time.monotonic()))
            time.sleep(.01)
        return 0
    if args.mode=='nested':
        from process_capture import run_command
        try:run_command([sys.executable,__file__,'--mode','parent','--area',str(area)],area/'nested.log',area/'nested.json',cwd=area,budget=5)
        except Exception:return 1
        return 0
    child=subprocess.Popen([sys.executable,__file__,'--mode','grandchild','--area',str(area)])
    until=time.monotonic()+3
    while not (area/'grandchild.json').exists() and time.monotonic()<until:time.sleep(.005)
    print('tree-parent pid='+str(os.getpid())+' child='+str(child.pid),flush=True)
    (area/'parent-ready').write_text(str(os.getpid()))
    if args.mode=='early':return 0
    child.wait(timeout=12)
    return 0


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['parent','early','nested','grandchild','sentinel'],required=True);p.add_argument('--area',required=True)
    sys.exit(main(p.parse_args()))
