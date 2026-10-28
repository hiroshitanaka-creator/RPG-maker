#!/usr/bin/env python3
"""古い画面からの決定通知修正後の固定SHAで、全verifyと直接関係するUI回帰を実行する。"""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT=Path("/workspace/task082-latest-verification")
OUT=Path(__file__).resolve().parent/"latest"
OUT.mkdir(parents=True,exist_ok=True)
ENGINE=Path("/workspace/RPG-maker/.tools/godot/4.7.2/godot")
sys.path.insert(0,str(ROOT/"tools"))
from run_locked_checks import judge_output

sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
env=dict(os.environ,RPG_QA_SAVE_PREFIX="task082_latest",PYTHONDONTWRITEBYTECODE="1",VK_DRIVER_FILES="/workspace/RPG-maker/.tools/task082/lvp_icd.json")
env["PATH"]=str(ENGINE.parent)+os.pathsep+env["PATH"]
for kind in ["CACHE","CONFIG","DATA"]:
    folder=ROOT/".tools/task082"/kind.lower();folder.mkdir(parents=True,exist_ok=True)
    env["XDG_"+kind+"_HOME"]=str(folder)
paths=subprocess.check_output(["git","diff","--name-only","6c996d5c37fd384e679bb23dd59113c99494790c",sha],cwd=ROOT,text=True).splitlines()
document={"source_sha":sha,"cwd":str(ROOT),"runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"environment":{key:value for key,value in env.items() if key.startswith(("XDG_","RPG_QA_","VK_","PYTHONDONT"))},"source_sha256":{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in paths},"checks":[]}

def run(name,command,limit,requirement=False):
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        p=subprocess.run(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit)
        code,raw,timed_out=p.returncode,p.stdout,False
    except subprocess.TimeoutExpired as error:
        code,raw,timed_out=124,error.stdout or b"",True
    text=raw.decode("utf-8",errors="replace")
    result=judge_output(name,shlex.join(command),code,text,timed_out) if requirement else {"status":"PASS" if code==0 and not timed_out and not re.search(r"SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL:|Fontconfig error",text) else "FAIL"}
    path=OUT/(f"{len(document['checks'])+1:02d}-"+name+".log.gz");path.write_bytes(gzip.compress(raw,mtime=0))
    document["checks"].append({"name":name,"source_sha":sha,"command":shlex.join(command),"cwd":str(ROOT),"started":start,"finished":datetime.datetime.now(datetime.timezone.utc).isoformat(),"timeout_seconds":limit,"exit_code":code,"timed_out":timed_out,"result":result,"log":path.name,"raw_sha256":hashlib.sha256(raw).hexdigest()})
    (OUT/"execution.json").write_text(json.dumps(document,ensure_ascii=False,indent=2)+"\n")
    print(name,code,result["status"],flush=True)

run("import",[str(ENGINE),"--headless","--editor","--import","--quit"],600)
run("frozen-before",[sys.executable,"tools/check_frozen_files.py"],30)
run("approved-data",[sys.executable,"tools/check_region2_shrine_story_data.py"],120)
run("shrine",[str(ENGINE),"--headless","--path",".","--script","res://tools/check_region2_shrine_story.gd"],180)
for req in json.loads((ROOT/".scope-lock/spec.lock.json").read_text())["requirements"]:
    run(req["id"],shlex.split(req["verify"]),300,True)
for name,limit in [("first_region_gado",180),("first_region_screen",180),("battle_recovery",180),("saved_value_types",60),("saved_position_relocation",120),("task081_port_runtime",120)]:
    run(name,[str(ENGINE),"--headless","--path",".","--script","res://tools/check_"+name+".gd"],limit)
run("frozen-after",[sys.executable,"tools/check_frozen_files.py"],30)
raise SystemExit(0 if all(row["result"]["status"]=="PASS" for row in document["checks"]) else 1)
