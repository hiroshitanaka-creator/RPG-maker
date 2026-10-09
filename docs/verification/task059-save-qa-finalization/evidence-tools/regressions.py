from pathlib import Path
import os,sys,re,json,subprocess
sys.path.insert(0,'/workspace/RPG-maker/tools/fixtures/equipment-save-transaction-platform')
from process_capture import ProcessCapture,save
root=Path('/tmp/qa059/regression');out=Path('/tmp/qa059/regression-logs');out.mkdir();env=os.environ.copy();env['PATH']='/tmp/qa059/regression-bin:'+env['PATH']
for key in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME']:
 p=out/'profile'/key;p.mkdir(parents=True);env[key]=str(p)
godot='/tmp/qa059/engine/Godot_v4.7.2-stable_linux.x86_64';rows=[]
commands=[('frozen-before',[sys.executable,'tools/check_frozen_files.py'],30),('import',[godot,'--headless','--editor','--import','--quit'],600),('R01-R08',[sys.executable,'tools/run_locked_checks.py'],900),('equipment',[godot,'--headless','--path','.', '--script','res://tools/check_equipment_rules.gd'],240),('S1',[godot,'--headless','--path','.', '--script','res://tools/check_equipment_save_migration.gd'],120),('S2',[godot,'--headless','--path','.', '--script','res://tools/check_equipment_save_codec.gd'],120),('legacy142-10',[godot,'--headless','--path','.', '--script','res://tools/fixtures/equipment-save/legacy_equivalence.gd'],120),('assets',[sys.executable,'tools/validate_assets.py','--strict'],120),('frozen-after',[sys.executable,'tools/check_frozen_files.py'],30)]
for name,argv,budget in commands:
 cap=ProcessCapture(argv,out/(name+'.log'),out/(name+'-process.json'),cwd=root,env=env,budget=budget)
 try:
  with cap:cap.wait()
 except Exception as exc:print(name,repr(exc),flush=True)
 raw=(out/(name+'.log')).read_bytes();row=dict(cap.row,name=name,warning_or_error=bool(re.search(rb'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|Fontconfig error|_FAIL:',raw)));rows.append(row);save(out/'commands.json',rows);print(name,row['exit_code'],round(row['seconds'],3),row['warning_or_error'],flush=True)
 if name=='R01-R08' and (root/'docs/verification/scope-lock-current.json').exists():(out/'R01-R08.json').write_bytes((root/'docs/verification/scope-lock-current.json').read_bytes())
print('REGRESSIONS',all(r['exit_code']==0 and not r['warning_or_error'] and r['supervision']['stopped'] is True for r in rows),flush=True)
