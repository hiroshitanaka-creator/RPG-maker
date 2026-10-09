"""未改変058基点の反例を両OSで再現。今回作った孫へreleaseを渡して後始末する。"""
import argparse
import importlib.util
import json
from pathlib import Path
import os
import subprocess
import sys
import time


def main(args):
    checkout=Path(args.checkout).resolve(); output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(checkout/'tools/fixtures/equipment-save-transaction-platform'))
    spec=importlib.util.spec_from_file_location('baseline_driver058',checkout/'tools/check_equipment_save_transaction_platform.py')
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    from process_capture import ProcessCapture
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()
    assert source=='579ca1f463aaf9e93275039a59cf9d1ffb86adb5'
    suite=driver.Suite(argparse.Namespace(godot=sys.executable,fixture_root=str(output/'qa'),output=str(output/'results')))
    r=suite.area/'root';r.mkdir();(r/'restarted-batch.json').mkdir()
    start=time.monotonic();error=None
    try:suite.restarts.submit(r,dict(root=str(r),operation='normal'))
    except Exception as exc:error=repr(exc)
    live=suite.restarts.close();queue=json.loads((suite.output/'restart-queue.json').read_bytes())
    records=list(suite.output.rglob('*-execution.json'))
    assert error and 'IsADirectoryError' in error and not live and not records and queue['recovery_complete']
    a=dict(exception=error,seconds=time.monotonic()-start,execution_records=len(records),queue=queue)
    area=output/'tree';area.mkdir();fixture=Path(__file__).parent/'tree_fixture059.py'
    argv=[sys.executable,str(fixture),'--mode','parent','--area',str(area)]
    start=time.monotonic();cap=ProcessCapture(argv,output/'outer.log',output/'outer.json',cwd=checkout,deadline=start+.5,cleanup_deadline=start+.5)
    error=None
    try:
        with cap:cap.wait()
    except Exception as exc:error=repr(exc)
    # 孫自身のheartbeat継続を確認。PID存在だけでzombieを生存と呼ばない。
    path=area/'grandchild.heartbeat';before=path.read_text();time.sleep(.04);after=path.read_text()
    alive=before!=after
    assert alive and cap.row['timed_out']
    b=dict(exception=error,execution=cap.row,grandchild=json.loads((area/'grandchild.json').read_bytes()),heartbeat_before=before,heartbeat_after=after,grandchild_executing_after_outer_kill=alive,scope='0.5秒縮尺、実180秒検査ではない')
    (area/'release').write_bytes(b'fixture cleanup only')
    cap.child.wait(timeout=1)
    value=dict(source_sha=source,platform=sys.platform,argv=sys.argv,f5a=a,f5b=b,cleanup='今回fixtureのreleaseだけ。global/name killなし')
    (output/'counterexamples.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('BASELINE058_REPRODUCED: F5-a execution欠落/誤完全、F5-b専用孫heartbeat継続')
    return 0


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkout',required=True);p.add_argument('--output',required=True);sys.exit(main(p.parse_args()))
