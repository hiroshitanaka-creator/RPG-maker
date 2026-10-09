"""057ログ回収検証専用の実子。取引成功の代用には使わない。"""
import json
from pathlib import Path
import sys
import time
print('stdout-capture-fixture',flush=True)
print('stderr-capture-fixture',file=sys.stderr,flush=True)
mode=sys.argv[1]
if mode=='sleep':time.sleep(35)
elif mode=='abnormal':sys.exit(3)
elif mode=='batch':
    request=json.loads(Path(sys.argv[2]).read_bytes())
    for options in request:
        if options.get('operation')=='bad':raise RuntimeError('fixture child abnormal')
        Path(options['root'],options['result']).write_text(json.dumps({'capture_fixture':True,'pid':__import__('os').getpid()})+'\n')

elif mode=='boundary':
    config=json.loads(Path(sys.argv[2]).read_bytes())
    root=Path(config['root'])
    (root/'paused.json').write_text(json.dumps({'point':config['kill_point'],'pid':__import__('os').getpid()}))
    while not (root/'release').exists():time.sleep(.005)
    (root/config['result']).write_text(json.dumps({'capture_fixture':True}))
