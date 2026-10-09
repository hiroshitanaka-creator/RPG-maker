import sys,importlib.util,subprocess,time
from pathlib import Path
root=Path('/workspace/RPG-maker');sys.path.insert(0,str(root/'tools/fixtures/equipment-save-transaction-platform'))
spec=importlib.util.spec_from_file_location('validator059',root/'tools/fixtures/equipment-save-transaction-platform/run_ci.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.GODOT='/tmp/qa059/engine/Godot_v4.7.2-stable_linux.x86_64';start=time.monotonic();output=Path('/tmp/qa059/propagation-baseline/results')
m.validate(root,output)
rows=m.propagation(root,output);scope=m.scope_tests(root,'0a44409c99b06569b9e6088ffeb46c2238c821fa',output.parent/'scope055')
m.write(output.parent/'execution.json',dict(baseline_source_sha='c8f22dbe4edb8ff5e4dcd699ce0887a25f9b0974',current_validator_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),acceptance='原057に保存された過去正常証拠を独立再照合後、現059 validatorへ16改変を適用。現059の全取引成功とは別',propagation=rows,scope055=scope,seconds=time.monotonic()-start));print('PROPAGATION059_PASS',len(rows),len(scope),flush=True)
