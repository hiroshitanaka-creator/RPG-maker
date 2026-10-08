#!/usr/bin/env python3
"""053: 完成SHAの範囲と、最新のS3動作/原証拠/実exitを分けて検証する。"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
BASE='e2c28474b55bd3a9e3dee00be768661ba87e09c4'
VERSION='4.7.2.stable.official.ed1daf0bf'
ENGINE='8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
BAD=re.compile(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|Fontconfig error|_FAIL:')


def require(ok,message):
    if not ok:raise RuntimeError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def load(path):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'JSON重複キー')
            result[key]=value
        return result
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def validate(checkout,output):
    expected=load(checkout/'tools/fixtures/equipment-save-transaction/expectations.json')
    require(len(expected['cases'])==172 and len(expected['points'])==97,'独立固定172ケース/97境界')
    require({kind:sum(v['kind']==kind for v in expected['cases'].values()) for kind in ['kill','fault','special']}=={'kill':97,'fault':24,'special':51},'全群の固定件数')
    require(set(expected['points'])=={v['point'] for v in expected['cases'].values() if v['kind']=='kill'},'全kill地点の固定集合')
    require(sum(len(v['checks']) for v in expected['cases'].values())==2178,'固定2178条件')
    phase_expectations=load(checkout/'tools/fixtures/equipment-save-transaction/recovery-phases.json')['phases']
    require(set(phase_expectations)==set(expected['points']),'全97地点の独立phase期待')
    summary=load(output/'summary.json')
    require(summary['status']=='PASS' and summary['failures']==[],'検査成功の実観測')
    require(summary['case_count']==172 and summary['checks']==2178,'全ケース/条件数')
    require(summary['budget_seconds']==180 and 0<summary['seconds']<=180,'全体180秒')
    require(summary['engine_sha256']==ENGINE,'公式実体hash')
    require(set(summary['cases'])==set(expected['cases']) and len(summary['cases'])==172,'ID集合/一意性')
    require(summary['real_permission']['uid']!=0 and summary['real_permission']['os_settings_changed'] is False,'実非root権限拒否')
    manifest=load(output/'sha256.json')
    actual={str(p.relative_to(output)):digest(p.read_bytes()) for p in output.rglob('*') if p.is_file() and p.name!='sha256.json'}
    require(actual==manifest,'全raw証拠のhash/集合')
    for name,spec in expected['cases'].items():
        row=load(output/name/'case.json')
        require(row['case']==name and row['expected']==spec,'独立期待一致:'+name)
        reason=spec.get('reason','ok')
        require(row['actual'].get('reason_code')==reason and row['actual'].get('ok')==(reason=='ok'),'実成否:'+name)
        if spec['kind']=='kill':
            require(row['actual'].get('phase')=='committed' and row['actual'].get('quantity')==12 and row['actual'].get('applied') is False,'kill後確定/適用なし:'+name)
            files=load(output/name/'at-kill'/'files.json')
            token=row['actual']['token'];relative='transactions/'+token+'/converted.tmp'
            phase=phase_expectations[spec['point']]
            if phase=='candidate_bytes':phase='prepared' if files.get(relative,{}).get('sha256')==row['actual']['candidate_sha256'] else 'incomplete'
            require(row['actual']['recovery_before']['phase']==phase,'独立期待phase:'+name)
            if phase=='prepared':require(files.get(relative,{}).get('sha256')==row['actual']['candidate_sha256'],'kill時の準備済み全bytes:'+name)
            if phase=='committed':require(files.get('transactions/'+token+'/converted.json',{}).get('sha256')==row['actual']['candidate_sha256'],'kill時の確定済み全bytes:'+name)
        require(set(row['checks'])==set(spec['checks']) and all(value is True for value in row['checks'].values()),'全assertの実結果:'+name)
        commands=row['commands'];require(commands,'実コマンド欠落:'+name)
        killed=[c for c in commands if c['exit_code']==-9]
        if spec['kind']=='kill':
            require(len(killed)==1 and killed[0]['kill_point']['point']==spec['point'],'前後kill地点:'+name)
            require(commands[0]['exit_code']==-9 and commands[1]['exit_code']==0,'kill→別子再起動:'+name)
            require(commands[0]['kill_point']['pid']!=commands[1]['result'].get('pid'),'別process:'+name)
        else:require(not killed and all(c['exit_code']==0 for c in commands),'実exit:'+name)
        for command in commands:
            require(not command['timed_out'] and 0<command['seconds']<=30 and command['budget_seconds']==30,'子30秒:'+name)
            raw=(output/command['log']).read_bytes()
            require(digest(raw)==command['log_sha256'] and not BAD.search(raw.decode()),'原log警告/改変:'+name)
            if command['exit_code']==0:
                require(command['result'].get('memory_unchanged') is True,'実メモリ不変:'+name)
                require('TRANSACTION_PROBE:' in raw.decode(),'空実行拒否:'+name)
        candidate_hashes={c['result']['candidate_sha256'] for c in commands if c['result'].get('phase')=='committed' and c['result'].get('candidate_sha256')}
        snapshots=list((output/name).glob('*/files.json'))
        require(snapshots,'ファイル一覧欠落:'+name)
        for snapshot in snapshots:
            entries=load(snapshot)
            require(entries,'空ファイル一覧:'+name)
            for relative,entry in entries.items():
                if entry['kind']=='directory':continue
                path=snapshot.parent/(relative+'.link.txt' if entry['kind']=='link' else relative)
                raw=path.read_bytes()
                require(len(raw)==entry['bytes'] and digest(raw)==entry['sha256'],'全bytes/size/hash:'+name+'/'+relative)
                if Path(relative).name=='converted.json' and candidate_hashes and name!='output-changed':
                    require(digest(raw) in candidate_hashes,'実操作の候補hashと確定bytes:'+name)
                    document=load(path);stock=document['equipment_stock'];expected_quantity=22 if name=='normal-granted' else 12
                    owners=list(stock['bag'])
                    for actor in document['party']+document.get('first_region',{}).get('reserve',[]):
                        equipped=actor['equipment'];owners+=equipped['weapons']+[x for x in [equipped['armor']]+equipped['accessories'] if x]
                    require(len(stock['instances'])==expected_quantity and len(owners)==expected_quantity and set(owners)==set(stock['instances']) and len(set(owners))==expected_quantity,'固定数量/全所有/二重付与0:'+name)
                    migration=document['equipment_migration']
                    expected_id=digest(json.dumps(['equipment-migration-v1',migration['source_sha256'],'equipment-q1a-q2a-q3a-v1',1],separators=(',',':')).encode())
                    require(migration['migration_id']==expected_id and document['equipment_rules_version']==1,'raw識別/新版:'+name)
                if Path(relative).name=='source.bin':
                    intent_path=path.parent/'intent.json'
                    if intent_path.exists():
                        source_hash=load(intent_path)['source_sha256']
                        require((digest(raw)!=source_hash) if name=='backup-changed' else (digest(raw)==source_hash),'元raw/backup識別:'+name)
                    else:require(name in ['backup-hardlink','backup-collision'],'未所有backupの拒否証拠:'+name)
    return summary


def scope_audit(repo,sha):
    require(re.fullmatch('[0-9a-f]{40}',sha or ''),'完成対象は完全SHA')
    lines=subprocess.check_output(['git','diff','--name-status',BASE,sha],cwd=repo,text=True).splitlines()
    exact={'scripts/game/equipment_save_transaction.gd','scripts/game/equipment_save_transaction.gd.uid',
           'tools/check_equipment_save_transaction.py','tools/equipment_save_transaction_probe.gd','tools/equipment_save_transaction_probe.gd.uid',
           'docs/tasks/053-equipment-save-transaction.md','docs/tasks/reports/053-equipment-save-transaction.md','docs/decision-log.md',
           '.github/workflows/equipment-transaction.yml'}
    for line in lines:
        status,path=line.split('\t')
        require(status in ['A','M'] and (path in exact or path.startswith('tools/fixtures/equipment-save-transaction/') or path.startswith('docs/verification/equipment-save-transaction/')),'担当外差分:'+line)
    old=subprocess.check_output(['git','show',BASE+':docs/decision-log.md'],cwd=repo)
    new=subprocess.check_output(['git','show',sha+':docs/decision-log.md'],cwd=repo)
    require(new.startswith(old),'decision-logは今回末尾だけ')
    old=subprocess.check_output(['git','show',BASE+':docs/tasks/053-equipment-save-transaction.md'],cwd=repo).decode()
    new=subprocess.check_output(['git','show',sha+':docs/tasks/053-equipment-save-transaction.md'],cwd=repo).decode()
    strip=lambda text:re.sub(r'^- 状態：.*$', '- 状態：',text,flags=re.M)
    require(strip(old)==strip(new),'053は状態行だけ')
    return lines


def scope_self_test(repo,fixed,output):
    output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name,path,profile,expected in [('later-document','docs/tasks/future-independent-review.md','latest',0),('fixed-outside','outside053.txt','fixed053',1)]:
        index=output/('index-'+name)
        env=os.environ.copy();env['GIT_INDEX_FILE']=str(index)
        subprocess.run(['git','read-tree',fixed],cwd=repo,env=env,check=True)
        blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=b'QA scope fixture\n',cwd=repo).decode().strip()
        subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,path],cwd=repo,env=env,check=True)
        tree=subprocess.check_output(['git','write-tree'],cwd=repo,env=env).decode().strip()
        source=subprocess.check_output(['git','-c','user.name=QA','-c','user.email=qa@example.invalid','commit-tree',tree,'-p',fixed],input=b'QA scope fixture\n',cwd=repo).decode().strip()
        argv=[sys.executable,str(Path(__file__).resolve()),'--scope-only','--checkout',str(repo),'--source-sha',source,'--fixed-sha',fixed,'--profile',profile,'--output',str(output)]
        start=time.monotonic();child=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        (output/(name+'.log')).write_bytes(child.stdout)
        rows.append(dict(case=name,expected_exit=expected,exit_code=child.returncode,source_sha=source,fixed_sha=fixed,seconds=time.monotonic()-start,argv=argv))
        require(child.returncode==expected,'範囲世代正負の実exit:'+name)
    return rows


def self_test(checkout,output):
    rows=[]
    # 全証拠を別専用コピーで改変し、manifestを作り直さず実exitを確認する。
    variants=['control','missing-case','zero-checks','warning-log','failed-exit','timeout','modified-bytes','missing-bytes','false-assert','wrong-phase','missing-manifest','missing-summary','rehash-output','rehash-backup']
    for name in variants:
        area=output.parent/'propagation'/name
        shutil.copytree(output,area)
        case='kill-read.open.before'
        if name=='missing-case':(area/case/'case.json').rename(area/case/'case.saved')
        elif name=='missing-summary':(area/'summary.json').rename(area/'summary.saved')
        elif name=='missing-manifest':(area/'sha256.json').rename(area/'sha256.saved')
        elif name=='zero-checks':
            value=load(area/'summary.json');value['checks']=1;write(area/'summary.json',value)
        elif name=='warning-log':
            path=area/case/'restarted.log';path.write_bytes(path.read_bytes()+b'WARNING: injected proof\n')
        elif name in ['failed-exit','timeout','false-assert','wrong-phase']:
            value=load(area/case/'case.json')
            if name=='failed-exit':value['commands'][1]['exit_code']=1
            elif name=='timeout':value['commands'][1]['timed_out']=True
            elif name=='false-assert':value['checks']['quantity']=False
            else:value['actual']['phase']='incomplete';value['checks']['committed_bytes']=False
            write(area/case/'case.json',value)
        elif name in ['modified-bytes','missing-bytes']:
            path=area/case/'final'/'source.json'
            if name=='modified-bytes':raw=bytearray(path.read_bytes());raw[-1]^=1;path.write_bytes(raw)
            else:path.rename(path.with_suffix('.saved'))
        if name in ['rehash-output','rehash-backup']:
            path=area/case/'final'/'transactions'
            target=next(path.glob('*/'+('converted.json' if name=='rehash-output' else 'source.bin')))
            raw=bytearray(target.read_bytes());raw[-1]^=1;target.write_bytes(raw)
            file_list=load(area/case/'final'/'files.json');relative=str(target.relative_to(area/case/'final'))
            file_list[relative]['sha256']=digest(raw);write(area/case/'final'/'files.json',file_list)
            write(area/'sha256.json',{str(p.relative_to(area)):digest(p.read_bytes()) for p in area.rglob('*') if p.is_file() and p.name!='sha256.json'})
        argv=[sys.executable,str(Path(__file__).resolve()),'--validate-only','--checkout',str(checkout),'--output',str(area)]
        start=time.monotonic();child=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        (output.parent/(name+'-validation.log')).write_bytes(child.stdout)
        expected=0 if name=='control' else 1
        rows.append(dict(case=name,expected_exit=expected,exit_code=child.returncode,seconds=time.monotonic()-start,argv=argv,log_sha256=digest(child.stdout)))
        require(child.returncode==expected,'証拠/失敗伝播実exit:'+name)
    return rows


def main(args):
    output=Path(args.output).absolute();output.mkdir(parents=True,exist_ok=True)
    checkout=Path(args.checkout).absolute() if args.checkout else ROOT
    if args.validate_only:validate(checkout,output);return
    target=args.source_sha if args.profile=='fixed053' else args.fixed_sha
    if args.scope_only:scope_audit(checkout,target);return
    require(re.fullmatch('[0-9a-f]{40}',args.source_sha or ''),'sourceは完全SHA')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()==args.source_sha,'実checkout SHA')
    godot=Path(args.godot).absolute()
    require(digest(godot.read_bytes())==ENGINE,'公式Godot実体')
    commands=[]
    env=os.environ.copy()
    for key in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME']:
        value=output.parent/'profile'/key;value.mkdir(parents=True,exist_ok=True);env[key]=str(value)
    def command(label,argv,limit):
        start=time.monotonic()
        child=subprocess.run(argv,cwd=checkout,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit)
        raw=child.stdout;(output.parent/(label+'.log')).write_bytes(raw)
        commands.append(dict(name=label,argv=argv,seconds=time.monotonic()-start,budget_seconds=limit,exit_code=child.returncode,log_sha256=digest(raw)))
        write(output.parent/'commands.json',commands)
        require(child.returncode==0 and not BAD.search(raw.decode()),'コマンド失敗/警告:'+label)
        return raw
    version=command('version',[str(godot),'--version'],30)
    require(VERSION in version.decode(),'4.7.2公式版')
    command('frozen-before',[sys.executable,'tools/check_frozen_files.py'],30)
    try:
        command('import',[str(godot),'--headless','--editor','--import','--quit'],600)
        command('transaction',[sys.executable,'tools/check_equipment_save_transaction.py','--godot',str(godot),'--fixture-root',str(output.parent/'qa'),'--output',str(output)],180)
    finally:command('frozen-after',[sys.executable,'tools/check_frozen_files.py'],30)
    summary=validate(checkout,output)
    scope=scope_audit(checkout,target)
    propagation=self_test(checkout,output)
    scope_results=scope_self_test(checkout,args.fixed_sha,output.parent/'scope') if args.fixed_sha else []
    write(output.parent/'execution.json',{'engine_sha256':ENGINE,'independent_phase_checks':97,'source_files':{path:digest((checkout/path).read_bytes()) for path in ['scripts/game/equipment_save_transaction.gd','tools/equipment_save_transaction_probe.gd','tools/check_equipment_save_transaction.py','tools/fixtures/equipment-save-transaction/probe_worker.gd','tools/fixtures/equipment-save-transaction/expectations.json','tools/fixtures/equipment-save-transaction/recovery-phases.json','tools/fixtures/equipment-save-transaction/run_ci.py']},'status':'PASS','source_sha':args.source_sha,'fixed_sha':args.fixed_sha,'scope_sha':target,'scope_changes':scope,'commands':commands,'summary':summary,'propagation':propagation,'scope_propagation':scope_results})
    print('TRANSACTION_CI_PASS: source='+args.source_sha+' cases=172 checks=2178 propagation=14 scope='+str(len(scope_results)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-sha');parser.add_argument('--fixed-sha');parser.add_argument('--profile',choices=['fixed053','latest'])
    parser.add_argument('--godot');parser.add_argument('--output',required=True);parser.add_argument('--checkout')
    parser.add_argument('--validate-only',action='store_true');parser.add_argument('--scope-only',action='store_true')
    try:main(parser.parse_args())
    except Exception as exc:print('TRANSACTION_CI_FAIL: '+str(exc));sys.exit(1)
