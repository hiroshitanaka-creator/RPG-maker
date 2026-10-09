"""実成功/過去の実失敗/欠落証拠を使い、独立診断ZIPと非0伝播を照合する。"""
import hashlib,json,sys,zipfile
from pathlib import Path
root=Path('/workspace/RPG-maker');fixture=root/'tools/fixtures/equipment-save-transaction-platform'
sys.path.insert(0,str(fixture))
from process_capture import run_command,save
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/qa059/compact-validation');out.mkdir(exist_ok=False)
missing=out/'missing-input';(missing/'task059').mkdir(parents=True)
helper_sha256=hashlib.sha256((fixture/'diagnostic_evidence059.py').read_bytes()).hexdigest()
rows=[]
for label,area,source,code,expected in [
 ('actual-pass',Path('/tmp/qa059/resume351/native-evidence'),'351ec408e62c22c5ab509c0c0624808ffdc60613','55a56d09d7c74becaeacdecede16836d93ba8cbc',0),
 ('actual-old-failure',Path('/tmp/qa059/compact-old-failure/native-evidence'),'7f91d0460298dd074cb6974733aa5a16ba484139','faa459ee5cc101e708477792b1c7891a9ba4beea',1),
 ('missing-execution',missing,'351ec408e62c22c5ab509c0c0624808ffdc60613','55a56d09d7c74becaeacdecede16836d93ba8cbc',1)]:
 destination=out/label
 argv=[sys.executable,str(fixture/'diagnostic_evidence059.py'),'--output',str(area),'--destination',str(destination),'--source-sha',source,'--code-sha',code]
 run_command(argv,out/(label+'.log'),out/(label+'-process.json'),cwd=root,budget=30,timeout_kind='diagnostic_evidence_test_30_seconds')
 process=json.loads((out/(label+'-process.json')).read_bytes());assert process['exit_code']==expected and process['supervision']['stopped']
 summary=json.loads((destination/'summary.json').read_bytes());assert summary['status']==('PASS' if expected==0 else 'FAIL')
 archive=destination/summary['archive']['file'];assert hashlib.sha256(archive.read_bytes()).hexdigest()==summary['archive']['sha256']
 index=json.loads((destination/'original-index.json').read_bytes())
 with zipfile.ZipFile(archive) as z:
  for row in index['files']:
   raw=z.read('task059/'+row['path']);assert raw==(area/'task059'/row['path']).read_bytes()
   assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
  assert len(z.namelist())==len(index['files'])+1
 if label=='actual-old-failure':
  failed=summary['tests']['capture-tests']['failures'];assert any(r['case']=='shutdown-active-and-futures' for r in failed)
  assert '::error title=059診断内訳::' in (out/(label+'.log')).read_text()
 rows.append(dict(case=label,expected_exit=expected,process=process,archive=summary['archive'],summary=summary))
 save(out/'validation.json',dict(status='PASS',helper_sha256=helper_sha256,cases=rows,original_final_job='113978145324 remains UNCONFIRMED'))
 print(label,process['exit_code'],summary['archive']['bytes'],len(index['files']),flush=True)
