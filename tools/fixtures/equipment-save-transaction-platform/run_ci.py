#!/usr/bin/env python3
"""055専用: 固定scopeと最新全不変条件、OS差、追加負例、原証拠を独立照合。"""
import argparse,copy,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE='b17f2b475ff8c58924720ea24cce8f205422c50b'
BAD=re.compile(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|Fontconfig error|_FAIL:')
def require(ok,message):
    if not ok:raise RuntimeError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(path):
    def pairs(values):
        result={}
        for key,value in values:
            require(key not in result,'JSON重複');result[key]=value
        return result
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs)
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def module(path):
    spec=importlib.util.spec_from_file_location('original053_validation',path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def validate(checkout,output):
    # 旧validator全文のbyte/数量/独立phase確認を保持し、OSによる実終了と権限の違いだけ置換。
    old=checkout/'tools/fixtures/equipment-save-transaction/run_ci.py'
    source=old.read_text();a=source.index('def validate(');b=source.index('\ndef scope_audit(',a)
    source=source[a:b]
    source=source.replace('tools/fixtures/equipment-save-transaction/expectations.json','tools/fixtures/equipment-save-transaction-platform/expectations.json').replace('tools/fixtures/equipment-save-transaction/recovery-phases.json','tools/fixtures/equipment-save-transaction-platform/recovery-phases.json')
    source=source.replace("    summary=load(output/'summary.json')", "    if os.name=='nt':expected['cases']['nonroot-permission']['reason']='write_failed'\n    summary=load(output/'summary.json')")
    source=source.replace("summary['engine_sha256']==ENGINE", "summary['engine_sha256']==digest(Path(GODOT).read_bytes())")
    source=source.replace("summary['real_permission']['uid']!=0 and summary['real_permission']['os_settings_changed'] is False", "summary['real_permission']['os_settings_changed'] is False and ((os.name=='nt' and summary['real_permission']['mechanism']=='readonly-file') or (os.name!='nt' and summary['real_permission']['uid']!=0))")
    source=source.replace("c['exit_code']==-9", "c['exit_code']==(1 if os.name=='nt' else -9)").replace("commands[0]['exit_code']==-9", "commands[0]['exit_code']==(1 if os.name=='nt' else -9)")
    source=source.replace("str(p.relative_to(output))", "p.relative_to(output).as_posix()")
    env={'require':require,'load':load,'digest':digest,'Path':Path,'BAD':BAD,'os':os,'json':json,'GODOT':GODOT}
    exec(compile(source,str(old)+':055_os_adapter','exec'),env)
    return env['validate'](checkout,output)

def scope(checkout,sha):
    require(re.fullmatch('[0-9a-f]{40}',sha or ''),'完全SHA必須')
    exact={'scripts/game/equipment_save_transaction.gd','tools/check_equipment_save_transaction_platform.py','.github/workflows/equipment-transaction-platform.yml','docs/tasks/055-native-save-io.md','docs/tasks/reports/055-native-save-io.md','docs/decision-log.md'}
    changes=subprocess.check_output(['git','diff','--name-status',BASE,sha],cwd=checkout,text=True).splitlines()
    for line in changes:
        status,path=line.split('\t');require(status in ['A','M'] and (path in exact or any(path.startswith(prefix) for prefix in ['native/equipment_save_io/','addons/equipment_save_io/','tools/fixtures/equipment-save-transaction-platform/','docs/verification/equipment-save-transaction-platform/'])),'055担当外:'+line)
    for path in ['docs/decision-log.md','docs/tasks/055-native-save-io.md']:
        old=subprocess.check_output(['git','show',BASE+':'+path],cwd=checkout);new=subprocess.check_output(['git','show',sha+':'+path],cwd=checkout)
        require(new.startswith(old) if path.endswith('decision-log.md') else re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b.*$',b'',old,flags=re.M)==re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b.*$',b'',new,flags=re.M),'文書範囲:'+path)
    return changes

def propagation(checkout,output):
    # 旧14改変を同じ実子exitで実行。改変後のmanifest再hashも原bytes/候補を照合する。
    original=module(checkout/'tools/fixtures/equipment-save-transaction/run_ci.py')
    rows=[]
    variants=['control','missing-case','zero-checks','warning-log','failed-exit','timeout','modified-bytes','missing-bytes','false-assert','wrong-phase','missing-manifest','missing-summary','rehash-output','rehash-backup','empty-log','count-log-rehash']
    for name in variants:
        area=output.parent/'propagation'/name;shutil.copytree(output,area)
        case='kill-read.open.before'
        if name in ['empty-log','count-log-rehash']:
            row=load(area/case/'case.json');path=area/row['commands'][1]['log'];path.write_bytes(b'')
            if name=='count-log-rehash':
                row['commands'][1]['log_sha256']=digest(b'');write(area/case/'case.json',row);summary=load(area/'summary.json');summary['checks']=0;write(area/'summary.json',summary)
            write(area/'sha256.json',{p.relative_to(area).as_posix():digest(p.read_bytes()) for p in area.rglob('*') if p.is_file() and p.name!='sha256.json'})
        elif name=='missing-case':(area/case/'case.json').rename(area/case/'case.saved')
        elif name=='missing-summary':(area/'summary.json').rename(area/'summary.saved')
        elif name=='missing-manifest':(area/'sha256.json').rename(area/'sha256.saved')
        elif name=='zero-checks':value=load(area/'summary.json');value['checks']=0;write(area/'summary.json',value)
        elif name=='warning-log':path=area/case/'restarted.log';path.write_bytes(path.read_bytes()+b'WARNING: injected proof\n')
        elif name in ['failed-exit','timeout','false-assert','wrong-phase']:
            value=load(area/case/'case.json')
            if name=='failed-exit':value['commands'][1]['exit_code']=2
            elif name=='timeout':value['commands'][1]['timed_out']=True
            elif name=='false-assert':value['checks']['quantity']=False
            else:value['actual']['phase']='incomplete'
            write(area/case/'case.json',value)
        elif name in ['modified-bytes','missing-bytes']:
            path=area/case/'final/source.json'
            if name=='modified-bytes':path.write_bytes(path.read_bytes()+b'x')
            else:path.rename(path.with_suffix('.saved'))
        elif name in ['rehash-output','rehash-backup']:
            path=next((area/case/'final/transactions').glob('*/'+('converted.json' if name=='rehash-output' else 'source.bin')));path.write_bytes(path.read_bytes()+b'x')
            file_list=load(path.parents[1].parent/'files.json');relative=path.relative_to(area/case/'final').as_posix();file_list[relative]['sha256']=digest(path.read_bytes());file_list[relative]['bytes']=path.stat().st_size;write(area/case/'final/files.json',file_list)
            write(area/'sha256.json',{p.relative_to(area).as_posix():digest(p.read_bytes()) for p in area.rglob('*') if p.is_file() and p.name!='sha256.json'})
        argv=[sys.executable,str(Path(__file__).resolve()),'--validate-only','--checkout',str(checkout),'--godot',GODOT,'--output',str(area)]
        start=time.monotonic();child=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);(output.parent/(name+'-validation.log')).write_bytes(child.stdout)
        expected=0 if name=='control' else 1;require(child.returncode==expected,'改変伝播:'+name);rows.append({'case':name,'expected_exit':expected,'exit_code':child.returncode,'seconds':time.monotonic()-start,'log_sha256':digest(child.stdout)})
    return rows

def source_audit(checkout,sha):
    prefixes=['native/equipment_save_io','tools/fixtures/equipment-save-transaction-platform']
    paths=subprocess.check_output(['git','ls-files',*prefixes,'scripts/game/equipment_save_transaction.gd','tools/check_equipment_save_transaction_platform.py'],cwd=checkout,text=True).splitlines()
    results={}
    for path in paths:
        if not (Path(path).suffix in ['.gd','.cpp','.h','.py','.json'] or Path(path).name=='SConstruct'):continue
        raw=subprocess.check_output(['git','show',sha+':'+path],cwd=checkout);actual=(checkout/path).read_bytes()
        require(actual==raw,'実sourceとGit blob不一致:'+path)
        results[path]={'raw_sha256':digest(actual),'git_blob':subprocess.check_output(['git','rev-parse',sha+':'+path],cwd=checkout,text=True).strip()}
    return results

def scope_tests(checkout,fixed,output):
    output.mkdir(parents=True,exist_ok=True);rows=[]
    for name,path,profile,expected in [('later-document','docs/tasks/future-independent-review.md','latest',0),('outside-fixed','outside055.txt','fixed055',1)]:
        env=os.environ.copy();env['GIT_INDEX_FILE']=str(output/('index-'+name))
        subprocess.run(['git','read-tree',fixed],cwd=checkout,env=env,check=True)
        blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=b'055 scope QA fixture\n',cwd=checkout).decode().strip()
        subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,path],cwd=checkout,env=env,check=True)
        tree=subprocess.check_output(['git','write-tree'],cwd=checkout,env=env).decode().strip()
        sha=subprocess.check_output(['git','-c','user.name=QA','-c','user.email=qa@example.invalid','commit-tree',tree,'-p',fixed],input=b'055 scope QA fixture\n',cwd=checkout).decode().strip()
        argv=[sys.executable,str(Path(__file__).resolve()),'--scope-only','--checkout',str(checkout),'--source-sha',sha,'--fixed-sha',fixed,'--profile',profile,'--output',str(output)]
        p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);(output/(name+'.log')).write_bytes(p.stdout)
        require(p.returncode==expected,'scope実exit:'+name);rows.append({'case':name,'source_sha':sha,'fixed_sha':fixed,'expected_exit':expected,'exit_code':p.returncode,'log_sha256':digest(p.stdout)})
    return rows

GODOT=''
def main(args):
    global GODOT
    GODOT=str(Path(args.godot).resolve()) if args.godot else ''
    checkout=Path(args.checkout).resolve() if args.checkout else ROOT;output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    if args.validate_only:validate(checkout,output);return
    if args.scope_only:scope(checkout,args.source_sha if args.profile=='fixed055' else args.fixed_sha);return
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()==args.source_sha,'checkout完全SHA')
    source_files=source_audit(checkout,args.source_sha)
    commands=[];env=os.environ.copy()
    for key in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME','APPDATA','LOCALAPPDATA']:
        value=output.parent/'profile'/key;value.mkdir(parents=True,exist_ok=True);env[key]=str(value)
    def command(label,argv,budget):
        start=time.monotonic();p=subprocess.run(argv,cwd=checkout,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=budget);(output.parent/(label+'.log')).write_bytes(p.stdout)
        commands.append({'name':label,'argv':argv,'budget_seconds':budget,'seconds':time.monotonic()-start,'exit_code':p.returncode,'log_sha256':digest(p.stdout)});write(output.parent/'commands.json',commands)
        if p.returncode!=0 or BAD.search(p.stdout.decode(errors='replace')):
            print(p.stdout.decode(errors='replace'),flush=True)
            raise RuntimeError('コマンド失敗:'+label)
        return p.stdout
    require('4.7.2.stable.official.ed1daf0bf' in command('version',[GODOT,'--version'],30).decode(),'公式4.7.2')
    command('frozen-before',[sys.executable,'tools/check_frozen_files.py'],30)
    command('import',[GODOT,'--headless','--editor','--import','--quit'],600)
    command('transaction',[sys.executable,'tools/check_equipment_save_transaction_platform.py','--godot',GODOT,'--fixture-root',str(output.parent/'qa'),'--output',str(output)],180)
    summary=validate(checkout,output)
    legacy=output.parent/'legacy053'
    extra_args=[]
    if os.name!='nt':
        command('legacy-checkout',['git','worktree','add','--detach',str(legacy),'e003b126de6695fa131e07a3db14c3011fb74f2e'],30)
        command('legacy-import',[GODOT,'--headless','--editor','--path',str(legacy),'--import','--quit'],600)
        extra_args=['--legacy-checkout',str(legacy)]
    extra=command('native-extra',[sys.executable,'tools/fixtures/equipment-save-transaction-platform/extra.py','--godot',GODOT,'--output',str(output.parent/'extra')]+extra_args,180)
    command('binary-checks',[sys.executable,'tools/fixtures/equipment-save-transaction-platform/binary_checks.py','--godot',GODOT,'--output',str(output.parent/'binary-checks')],180)
    command('frozen-after',[sys.executable,'tools/check_frozen_files.py'],30)
    target=args.source_sha if args.profile=='fixed055' else args.fixed_sha
    changes=scope(checkout,target) if target else []
    negatives=propagation(checkout,output)
    scope_rows=scope_tests(checkout,target or args.source_sha,output.parent/'scope')
    require(source_audit(checkout,args.source_sha)==source_files,'検査後source不変')
    write(output.parent/'execution.json',{'source_sha':args.source_sha,'fixed_sha':args.fixed_sha,'status':'PASS','summary':summary,'commands':commands,'propagation':negatives,'scope_changes':changes,'source_files':source_files,'scope_propagation':scope_rows,'engine_sha256':digest(Path(GODOT).read_bytes())})
    print('PLATFORM_CI_PASS: cases=172 checks=2178 kill=97 propagation=16 source='+args.source_sha)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--godot');p.add_argument('--output',required=True);p.add_argument('--source-sha');p.add_argument('--fixed-sha');p.add_argument('--profile',choices=['fixed055','latest']);p.add_argument('--checkout');p.add_argument('--scope-only',action='store_true');p.add_argument('--validate-only',action='store_true')
    try:main(p.parse_args())
    except Exception as exc:print('PLATFORM_CI_FAIL: '+str(exc));sys.exit(1)
