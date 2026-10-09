import sys,importlib.util,json,time
from pathlib import Path
sys.path.insert(0,'/workspace/RPG-maker/tools/fixtures/equipment-save-transaction-platform')
spec=importlib.util.spec_from_file_location('qa057validator','/workspace/RPG-maker/tools/fixtures/equipment-save-transaction-platform/run_ci.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.GODOT='/tmp/qa057/engine/Godot_v4.7.2-stable_linux.x86_64';start=time.monotonic();root=Path('/workspace/RPG-maker');output=Path('/tmp/qa057/propagation-baseline/results')
rows=m.propagation(root,output);scope=m.scope_tests(root,'0a44409c99b06569b9e6088ffeb46c2238c821fa',Path('/tmp/qa057/propagation-baseline/scope055'))
m.write('/tmp/qa057/propagation-baseline/execution.json',dict(baseline_source_sha='c8f22dbe4edb8ff5e4dcd699ce0887a25f9b0974',current_validator_sha=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),acceptance='過去の正常証拠への改変伝播。現在版172件の成功ではない',propagation=rows,scope055=scope,seconds=time.monotonic()-start));print('PROPAGATION_PASS',len(rows),len(scope),flush=True)
