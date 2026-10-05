"""承認された将来のCI追加は受理し、固定登録の改変は拒否する境界の正負例。"""
import argparse,hashlib,importlib.util,json,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
COMPLETED='d258908fbb0397e64d08780694786ef1855c4979'
class FunctionalGateReached(Exception):pass

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--godot',default='godot');args=parser.parse_args()
 import shutil
 exe=str(Path(shutil.which(args.godot) or args.godot).resolve())
 spec=importlib.util.spec_from_file_location('task011_checker',ROOT/'tools/check_task011.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
 original_run=subprocess.run;sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();results=[]
 assert (ROOT/'tools/check_task011.py').read_bytes()==subprocess.check_output(['git','show','HEAD:tools/check_task011.py'],cwd=ROOT),'検査対象の外側検査器は追跡SHAと一致'
 runner_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 with tempfile.TemporaryDirectory(prefix='task011-ci-boundary-') as directory:
  fixture=Path(directory)/'future';original_run(['git','worktree','add','--detach',str(fixture),sha],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  try:
   path=fixture/'.github/workflows/ci.yml';text=path.read_text();extra='''      - name: 後続依頼の正当なCI追加の確認用状態
        run: echo "確認用状態"

''';needle='      - name: 敵の行動予定と連戦の保存を検査';assert text.count(needle)==1;path.write_text(text.replace(needle,extra+needle))
   original_run(['git','add','.github/workflows/ci.yml'],cwd=fixture,check=True)
   original_run(['git','-c','user.name=011確認','-c','user.email=task011@example.invalid','commit','--no-gpg-sign','-m','011 将来のCI追加の確認用状態'],cwd=fixture,check=True,stdout=subprocess.PIPE)
   checker.ROOT=fixture;original_git=checker.git
   def stop_before_functional(command,*pos,**kwargs):
    if command[:3]==['git','worktree','add']:raise FunctionalGateReached()
    return original_run(command,*pos,**kwargs)
   for case in ['approved_future_ci','changed_registered_timeout','wrong_completed_sha','duplicate_registered_step']:
    observed=[]
    def read_git(*parameters):
     observed.append(list(parameters));raw=original_git(*parameters)
     if parameters==('show',checker.REGISTERED+':.github/workflows/ci.yml'):
      if case=='changed_registered_timeout':raw=raw.replace(b'timeout-minutes: 25',b'timeout-minutes: 26')
      if case=='wrong_completed_sha':raw=raw.replace(COMPLETED.encode(),b'0'*40)
      if case=='duplicate_registered_step':
       raw+=b'      - name: '+ '011遺跡の完成版と最新の通行・階段・保存・実描画を検査'.encode()+b'\n        run: echo duplicate\n      - name: dummy\n'
     return raw
    accepted=False
    with patch.object(checker,'git',read_git),patch.object(sys,'argv',['check_task011.py','--completed',COMPLETED,'--godot',exe]),patch.object(subprocess,'run',stop_before_functional):
     try:checker.main()
     except FunctionalGateReached:accepted=True
     except AssertionError:accepted=False
    assert accepted==(case=='approved_future_ci'),case
    assert ['show',checker.REGISTERED+':.github/workflows/ci.yml'] in observed
    assert ['show','HEAD:.github/workflows/ci.yml'] not in observed,'最新のCIへ段階限定条件を要求しない'
    results.append(dict(case=case,accepted=accepted,status='PASS',functional_tests_replaced=False))
  finally:original_run(['git','worktree','remove','--force',str(fixture)],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
 out=ROOT/'docs/verification/task-011/ci-boundary.json';out.write_text(json.dumps(dict(status='PASS',execution_sha=sha,runner_sha256=runner_sha,completed_sha=COMPLETED,registration_sha=checker.REGISTERED,confirmation_state=True,note='CI境界だけの正負例。本番の固定・最新機能検査は省略せず別に全実行する。',cases=results),ensure_ascii=False,indent=2)+'\n')
 print('TASK011_CI_BOUNDARY_PASS: positive=1 negative=3 registered='+checker.REGISTERED)
if __name__=='__main__':main()
