from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,os
r=Path(__file__).resolve().parent;s=Path('/workspace/RPG-maker');repo=r/'repo';rows=[]
def run(args,cwd=repo):
 d={'command':args,'cwd':str(cwd),'started_at_utc':datetime.now(timezone.utc).isoformat()}
 p=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);d.update(ended_at_utc=datetime.now(timezone.utc).isoformat(),exit=p.returncode)
 rows.append(d)
 with (r/'prepare.log').open('ab') as f:f.write(p.stdout)
 (r/'prepare-execution.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 assert p.returncode==0,p.stdout.decode(errors='replace')
 return p.stdout.decode().strip()
run(['git','clone','--shared','--no-checkout',str(s),str(repo)],r)
run(['git','remote','set-url','origin','https://github.com/hiroshitanaka-creator/RPG-maker.git'])
run(['git','fetch','origin','main'])
latest=run(['git','rev-parse','FETCH_HEAD']);assert latest=='bc5d827457e2b67164a217ce41bf7ca1a9b1e67b'
base='e677896d3e61b8fe8136ef60c5c76f41ad76701d'
run(['git','checkout','-b','codex/task-080-original-20261027',base])
patch='/workspace/task080/approved-20261021T035317Z/delivery/changes.patch'
run(['git','apply','--check','--index',patch]);run(['git','apply','--index',patch])
tree=run(['git','write-tree']);assert tree=='524b72d4cb8682b4d77197a9934defea247a199e'
run(['git','diff','--cached','--check'])
run(['git','config','user.name','Codex']);run(['git','config','user.email','codex@users.noreply.github.com'])
run(['git','commit','-m','080：採用済み5室の検証済み原候補を不変保存'])
snapshot=run(['git','rev-parse','HEAD']);assert run(['git','rev-parse','HEAD^{tree}'])==tree
run(['git','checkout','-b','codex/task-080-walking-foundation-20261027'])
run(['git','merge','--no-ff',latest,'-m','080：最新mainのcoastal修正と受入記録を統合'])
integrated=run(['git','rev-parse','HEAD'])
assert run(['git','diff',latest,'--','docs/decision-log.md','docs/tasks/README.md'])==''
run(['git','merge-base','--is-ancestor',latest,'HEAD'])
files=run(['git','diff','--name-only',snapshot,'HEAD']).splitlines()
(r/'main-integration-files.txt').write_text('\n'.join(files)+'\n')
(r/'main-agents-diff.txt').write_text(run(['git','diff',base,latest,'--','AGENTS.md']))
(r/'main-integration.diff').write_text(run(['git','diff',snapshot,'HEAD']))
info={'repo':str(repo),'base':base,'latest_main':latest,'snapshot_commit':snapshot,'snapshot_tree':tree,'integrated_commit':integrated,'snapshot_branch':'codex/task-080-original-20261027','integration_branch':'codex/task-080-walking-foundation-20261027'}
(r/'state.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info))
