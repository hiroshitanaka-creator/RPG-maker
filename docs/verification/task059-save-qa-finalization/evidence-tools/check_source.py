from pathlib import Path
import json,subprocess
r=Path.cwd();base='579ca1f463aaf9e93275039a59cf9d1ffb86adb5'
# 元の全assertionとケース本文を専用準備/回収経路とは別にbyte照合。
old=subprocess.check_output(['git','show',base+':tools/check_equipment_save_transaction_platform.py']).decode();new=(r/'tools/check_equipment_save_transaction_platform.py').read_text()
a=old.index('    def seed(');b=old.index('    def main(self):',a);x=new.index('    def seed(');y=new.index('    def main(self):',x);assert old[a:b]==new[x:y]
old=subprocess.check_output(['git','show',base+':tools/fixtures/equipment-save-transaction-platform/run_ci.py']).decode();new=(r/'tools/fixtures/equipment-save-transaction-platform/run_ci.py').read_text()
a=old.index('def scope(');b=old.index('def propagation(',a);assert old[a:b]==new[new.index('def scope('):new.index('def propagation(')]
for path in ['tools/fixtures/equipment-save-transaction-platform/test_capture057.py','tools/fixtures/equipment-save-transaction-platform/capture_fixture.py','tools/fixtures/equipment-save-transaction-platform/scope057.py','tools/fixtures/equipment-save-transaction-platform/diagnostics057.py']:
 assert subprocess.check_output(['git','show',base+':'+path])==(r/path).read_bytes(),path
row={'status':'PASS','case_assertions_bytes_unchanged':True,'original055_scope_bytes_unchanged':True,'original_capture057_12_checks_unchanged':True,'limits':{'suite':180,'inner':174,'child':30,'import':600,'job_minutes':15,'linux_restart_workers':4,'windows_restart_workers':2,'linux_case_workers':16,'windows_case_workers':8,'batch_max_roots':4},'expected':{'cases':172,'checks':2178,'kill':97,'propagation':16},'F4':'NOT_RUN real_ENOSPC/nested_cross_volume'}
(r/'docs/verification/task059-save-qa-finalization/method-preservation.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');print('元case/assertion・055scope・057の12検証bytes一致')
