from pathlib import Path
import shutil,json,gzip,hashlib
r=Path(__file__).resolve().parent;repo=r/'repo';dest=repo/'docs/verification/task-080-formal-save-20261027';old=Path('/workspace/task080/approved-20261021T035317Z')
for name in ['planned-files.txt','planned-files.json','state.json','main-integration-files.txt','main-agents-diff.txt','rebuild-result.json','prepare-execution.json','prepare.py','verify.py','package_evidence.py','rebuild_original_zip.py']:
 shutil.copyfile(r/name,dest/name)
for name in ['task-080-adopted-room-walking-foundation.zip','task-080-timestamped-evidence-20261021T033604Z.zip']:
 to=dest/'earlier-archives'/name;to.parent.mkdir(exist_ok=True);shutil.copyfile(Path('/workspace/task080')/name,to)
for name,folder in [('initial',old),('retry1',old/'library-retry1'),('retry2',old/'library-retry2-20261022'),('bounded2',old/'library-bounded3-20261022/attempt2'),('bounded3',old/'library-bounded3-20261022/attempt3'),('resume1',old/'library-resume-20261027/attempt1'),('resume2',old/'library-resume-20261027/attempt2')]:
 out=dest/'library-failures'/name;out.mkdir(parents=True)
 for file in (['library-upload-stderr.log','library-upload-result.json'] if name=='initial' else ['execution.json','stdout.json','stderr.log']):
  p=folder/file
  if p.exists():shutil.copyfile(p,out/file)
denial={'action':'create draft PR for codex/task-080-walking-foundation-20261027','status':'rejected; no PR created; no retry','review_text':'This action was rejected due to unacceptable risk. Reason: Creating a draft PR is an external repository commitment, while the user authorization covers PR2 and delegation explicitly assigns formal PR creation to the parent, not this task.','next':'parent can create draft PR or provide new explicit approval addressing this rejection; no workaround attempted','independent_work':'normal authorized branch pushes and read-only CI inspection continue'}
(dest/'draft-pr-denial.json').write_text(json.dumps(denial,ensure_ascii=False,indent=2)+'\n')
(dest/'gh-actions-read-denial.txt').write_text('gh run list exit1: failed to get runs: Get "https://api.github.com/repos/hiroshitanaka-creator/RPG-maker/actions/runs?per_page=3&exclude_pull_requests=true&branch=codex%2Ftask-080-original-20261027": Forbidden\nNo gh retry. Authorized GitHub connector GET used for CI reads. No alternative PR creation attempted.\n')
print('original-package metadata, earlier ZIPs, 7 failed upload logs and formal operation record collected')
