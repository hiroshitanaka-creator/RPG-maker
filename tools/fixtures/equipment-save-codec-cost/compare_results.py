#!/usr/bin/env python3
"""060原物の欠落/改変・on/off意味差・担当外変更を独立した条件で拒否する。"""
import argparse
import base64
import copy
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tarfile
import tempfile
import os

ROOT=Path(__file__).resolve().parents[3]
BASE='6695d7b802137e9d6b7e468a1414c04d658a5380'
REGISTERED='e37ddbaf4e84526c8e3f2816438dc9626875c00e'
CODE=['tools/check_equipment_save_codec_cost.gd','tools/check_equipment_save_codec_cost.py','tools/fixtures/equipment-save-codec-cost/cases.json','tools/fixtures/equipment-save-codec-cost/instrument_copy.py','tools/fixtures/equipment-save-codec-cost/compare_results.py']
PREFIX='docs/verification/task060-save-codec-cost/'
TASK='docs/tasks/060-measure-save-codec-cost.md'
REPORT='docs/tasks/reports/060-measure-save-codec-cost.md'
FILES={'argv.json','environment.json','measurements.json','results.json','stdout.log','stderr.log','exit.json','inputs.json','generated-diff.patch','hashes.json'}


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def load(path):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'重複JSONキー:'+key);result[key]=value
        return result
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs)


def unpack(value):
    raw=base64.b64decode(value['data'],validate=True)
    require(sha(raw)==value['sha256'] and len(raw)==value['bytes'],'archive hash/bytes')
    files={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
        for member in tar:
            require(member.isfile() and member.name not in files and not member.name.startswith('/') and '..' not in Path(member.name).parts,'archive member')
            data=tar.extractfile(member).read();files[member.name]=data
    require(set(files)==set(value['members']),'原member集合')
    for name,data in files.items():require(value['members'][name]==dict(bytes=len(data),sha256=sha(data)),'原member hash:'+name)
    return files


def scope(target):
    changes=subprocess.check_output(['git','diff','--name-status',REGISTERED,target],cwd=ROOT,text=True).splitlines()
    for row in changes:
        status,path=row.split('\t')
        require(status in ['A','M'] and (path in CODE+[TASK,REPORT] or path.startswith(PREFIX)),'060担当外:'+row)
    before=subprocess.check_output(['git','show',REGISTERED+':'+TASK],cwd=ROOT)
    after=subprocess.check_output(['git','show',target+':'+TASK],cwd=ROOT)
    require(re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b.*$',b'',before,flags=re.M)==re.sub(rb'^- \xe7\x8a\xb6\xe6\x85\x8b.*$',b'',after,flags=re.M),'依頼書本文不変')
    return dict(target=target,base=REGISTERED,changes=changes,production_old_evidence_protected_unchanged=True)


def normalized(value, root=""):
    if isinstance(value,str) and root and (value==root or value.startswith(root+"/")):return "$QA"+value[len(root):]
    if isinstance(value,dict):return {k:normalized(v,root) for k,v in value.items() if k not in ['pid','user_dir']}
    if isinstance(value,list):return [normalized(v,root) for v in value]
    return value


def compare_codec(left,right):
    require(left['evidence/codec.json']==right['evidence/codec.json'],'codec成否/reason/errors/観測結果の差')
    names={name for name in left if name.startswith('evidence/')}
    require(names=={name for name in right if name.startswith('evidence/')},'codec原入力/出力の集合欠落')
    for name in names:require(left[name]==right[name],'codec値/型/bytes差:'+name)
    summary=json.loads(left['evidence/codec.json'])
    require(not summary['failures'],'codec既存条件失敗')
    return dict(cases=summary['case_count'],checks=summary['checks'],input_output_native_bytes_equal=True,reason_errors_equal=True,input_context_memory_assertions='原検査の全条件成功')


def compare_transaction(left,right,expected):
    lcases={name.split('/')[1]:json.loads(raw) for name,raw in left.items() if re.fullmatch('evidence/[^/]+/case.json',name)}
    rcases={name.split('/')[1]:json.loads(raw) for name,raw in right.items() if re.fullmatch('evidence/[^/]+/case.json',name)}
    def root(files):
        argv=json.loads(files['exec.json'])['argv'];return str(Path(argv[argv.index('--fixture-root')+1]).parent)
    left_root,right_root=root(left),root(right)
    differences=[];matched=[]
    for case in sorted(set(lcases)&set(rcases)):
        a,b=lcases[case],rcases[case]
        if normalized(a['actual'],left_root)!=normalized(b['actual'],right_root):differences.append(case+':受理拒否/reason/結果')
        if a['checks']!=b['checks']:differences.append(case+':既存条件')
        project=lambda row,root:[{key:normalized(command.get(key),root) for key in ['result','exit_code','timed_out','kill_point']} for command in row['commands']]
        if project(a,left_root)!=project(b,right_root):differences.append(case+':初回/異常/再開の全command結果')
        for relative in ['source.json']:
            path=f'evidence/{case}/final/{relative}'
            if left.get(path)!=right.get(path):differences.append(case+':source bytes')
        paths={p for p in left if p.startswith(f'evidence/{case}/final/transactions/') and p.endswith(('/converted.json','/source.bin','/history.bin'))}
        other={p for p in right if p.startswith(f'evidence/{case}/final/transactions/') and p.endswith(('/converted.json','/source.bin','/history.bin'))}
        if paths!=other:differences.append(case+':保存原物集合')
        for path in paths&other:
            if left[path]!=right[path]:differences.append(case+':保存原物bytes:'+path)
        matched.append(case)
    missing_left=sorted(set(expected)-set(lcases));missing_right=sorted(set(expected)-set(rcases))
    return dict(common_cases=matched,missing_off=missing_left,missing_on=missing_right,differences=differences,complete=not (missing_left or missing_right or differences),normalization='process pidと専用user_dirを除き、実argvで確定した試行rootだけ$QAへ対応付ける。errorsの相対target/reason/他の値は保持。原JSONは全保存。')



def transaction_breakdown(files, expected):
    sys.path.insert(0,str(ROOT/'tools'))
    from check_equipment_save_codec_cost import canonical_logs
    argv=json.loads(files['exec.json'])['argv'];work=str(Path(argv[argv.index('--fixture-root')+1]).parent)
    totals={};groups=0;assignment_errors=[]
    for name,raw in canonical_logs(files):
        record_name=name.removesuffix('.log')+'-execution.json'
        configurations=[]
        if record_name in files:
            record=json.loads(files[record_name]);config_path=record.get('argv',[])[-1]
            relative=config_path[len(work)+1:] if config_path.startswith(work+'/') else ''
            if relative in files:
                value=json.loads(files[relative]);configurations=value if isinstance(value,list) else [value]
        current=0
        for line in raw.splitlines():
            if line.startswith(b'TRANSACTION_PROBE: '):current+=1;continue
            if not line.startswith(b'COST060 '):continue
            config=configurations[current] if current<len(configurations) else {}
            case=Path(config.get('root','')).name;operation=config.get('operation')
            role='fixture' if operation=='fixture' else 'restart' if operation=='resume' else 'interrupted' if config.get('kill_point') else 'abnormal' if config.get('fail_point') else 'normal' if case.startswith('normal-') or case=='absent-id' else 'special' if config else 'unassigned'
            if not config:assignment_errors.append(dict(log=name,index=current))
            spans=json.loads(line[8:])['spans'];groups+=1
            for index,span in enumerate(spans):
                elapsed=span['end_us']-span['start_us']
                child=sum(x['end_us']-x['start_us'] for x in spans if x['parent']==index)
                row=totals.setdefault(role,{}).setdefault(span['label'],dict(count=0,inclusive_us=0,exclusive_us=0))
                row['count']+=1;row['inclusive_us']+=elapsed;row['exclusive_us']+=elapsed-child
    return dict(by_operation=totals,groups=groups,assignment_errors=assignment_errors,units='process内wall microsecondsの並行累積。全体wallと加算/除算しない。',classification='一意batch原logを元config順/TRANSACTION_PROBE終端で対応。operation/kill_point/fail_pointで正常・注入異常・kill前・再開・specialを分離。codec単体154件の各成否別時間は未測（値と成否は全件対照）。')


def validate_run(output,item):
    path=output/item['name'];require(path.is_dir(),'run欠落:'+item['name'])
    require({p.name for p in path.iterdir()}==FILES,'run固定file集合')
    require(sha((path/'hashes.json').read_bytes())==item['hashes_sha256'],'run索引hash')
    hashes=load(path/'hashes.json');require(set(hashes)==FILES-{'hashes.json'},'file hash集合')
    for name,record in hashes.items():
        raw=(path/name).read_bytes();require(record==dict(sha256=sha(raw),bytes=len(raw)),'file改変:'+name)
    result=load(path/'results.json');files=unpack(result['archive'])
    require(result['phase']==item['phase'] and result['mode']==item['mode'] and result['repetition']==item['repetition'],'run対応')
    summary='evidence/codec.json' if item['phase']=='codec' else 'evidence/summary.json'
    require(result['summary']==(json.loads(files[summary]) if summary in files else None),'原summary対応')
    for stream in ['stdout.log','stderr.log']:require(files.get(stream,b'')==(path/stream).read_bytes(),'原stream対応')
    execution=load(path/'exit.json')
    require(json.loads(files['execution.json'])==execution,'原実行記録対応')
    require(all(item[key]==execution[key] for key in ['seconds','exit_code','ok']),'索引の実行判定対応')
    require(load(path/'environment.json')['case_workers']==(8 if load(path/'environment.json')['os'].startswith('Windows') else 16),'worker条件')
    require(load(path/'argv.json')['budget']==(120 if item['phase']=='codec' else 180),'固定予算')
    module_spec=importlib.util.spec_from_file_location('cost060_driver',ROOT/'tools/check_equipment_save_codec_cost.py');driver=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(driver)
    require(driver.summarize(files)==load(path/'measurements.json'),'原spanから再計算不一致')
    require(not load(path/'measurements.json')['errors'],'span不整合を成功扱いしない')
    case_contract=load(Path(__file__).with_name('cases.json'))
    require(driver.inputs(files,case_contract)==load(path/'inputs.json'),'入力索引再計算不一致')
    return files


def scope_negatives(target):
    result=[]
    for name,path in [('production','scripts/game/equipment_save_codec.gd'),('old-evidence','docs/verification/task059-save-qa-finalization/code-fixed-sha.txt'),('decision-log','docs/decision-log.md'),('workflow','.github/workflows/ci.yml'),('unlisted-code','tools/unlisted060.py'),('task-body',TASK)]:
        with tempfile.TemporaryDirectory(prefix='scope060-') as tmp:
            env=dict(os.environ,GIT_INDEX_FILE=tmp+'/index')
            subprocess.run(['git','read-tree',target],cwd=ROOT,env=env,check=True)
            blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input='060 担当外の負例\n'.encode(),cwd=ROOT).decode().strip()
            subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,path],cwd=ROOT,env=env,check=True)
            tree=subprocess.check_output(['git','write-tree'],cwd=ROOT,env=env).decode().strip()
            commit=subprocess.check_output(['git','-c','user.name=QA','-c','user.email=qa@example.invalid','commit-tree',tree,'-p',target],input='060 scope負例\n'.encode(),cwd=ROOT).decode().strip()
            child=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--scope-sha',commit],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
            require(child.returncode==1,'scope負例を受理:'+name)
            result.append(dict(name=name,sha=commit,expected_exit=1,exit_code=child.returncode,log=child.stdout.decode()))
    return result


def main(args):
    if args.scope_sha:
        print(json.dumps(scope(args.scope_sha),ensure_ascii=False));return 0
    output=Path(args.output);index=load(output/'inventory.json');cases=load(Path(__file__).with_name('cases.json'))
    expected={(phase,mode,rep) for phase in ['codec','transaction'] for mode in ['off','on'] for rep in [1,2,3]}
    require(len(index['runs'])==12 and {(r['phase'],r['mode'],r['repetition']) for r in index['runs']}==expected,'全12試行欠落/重複')
    data={};pairs=[]
    for row in index['runs']:data[(row['phase'],row['mode'],row['repetition'])]=validate_run(output,row)
    for phase in ['codec','transaction']:
        for rep in [1,2,3]:
            a=data[(phase,'off',rep)];b=data[(phase,'on',rep)]
            comparison=compare_codec(a,b) if phase=='codec' else compare_transaction(a,b,{c['case'] for c in cases['transaction_cases']})
            pairs.append(dict(phase=phase,repetition=rep,comparison=comparison))
    times={}
    for phase in ['codec','transaction']:
        for mode in ['off','on']:
            values=[r['seconds'] for r in index['runs'] if r['phase']==phase and r['mode']==mode]
            times[phase+'-'+mode]=dict(all=values,median=statistics.median(values),minimum=min(values),maximum=max(values))
    code=(output/'code-fixed-sha.txt').read_text().strip();require(code==index['code_sha'],'計測code固定SHA')
    code_scope=scope(code);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    result=dict(evidence_integrity=True,analysis_code_sha=head,measurement_code_sha=code,transaction_breakdown={str(rep):transaction_breakdown(data[('transaction','on',rep)],{x['case']:x for x in cases['transaction_cases']}) for rep in [1,2,3]},pairs=pairs,times=times,code_scope=code_scope,latest_scope=scope(head),self_tests=[])
    if args.self_test:
        baseline=data[('codec','off',1)];actual=data[('codec','on',1)]
        for name in ['missing-input','changed-native-document','changed-reason']:
            changed=dict(actual)
            if name=='missing-input':changed.pop(next(p for p in changed if p.endswith('/input.bin')))
            elif name=='changed-native-document':
                key=next(p for p in changed if p.endswith('/document.gdv'));changed[key]+=b'changed'
            else:
                value=json.loads(changed['evidence/codec.json']);value['observations'][0]['actual']='tampered';changed['evidence/codec.json']=json.dumps(value).encode()
            rejected=False
            try:compare_codec(baseline,changed)
            except ValueError:rejected=True
            require(rejected,'改変を受理:'+name);result['self_tests'].append(dict(name=name,rejected=True))
        transaction_off=data[('transaction','off',1)];transaction_on=data[('transaction','on',1)]
        for name in ['transaction-missing-case','transaction-error-target','transaction-memory','transaction-output-bytes']:
            altered=dict(transaction_on)
            if name=='transaction-missing-case':altered.pop('evidence/normal-pending/case.json')
            elif name=='transaction-output-bytes':
                key=next(p for p in altered if p.endswith('/converted.json'));altered[key]+=b'changed'
            else:
                key='evidence/fault-source.open.before/case.json';row=json.loads(altered[key])
                if name=='transaction-error-target':row['actual']['errors'][0]['target']+='/different'
                else:row['commands'][-1]['result']['memory_unchanged']=False
                altered[key]=json.dumps(row).encode()
            comparison=compare_transaction(transaction_off,altered,{x['case'] for x in cases['transaction_cases']})
            require(not comparison['complete'],'取引改変受理:'+name)
            result['self_tests'].append(dict(name=name,rejected=True))
        sample=load(output/index['runs'][0]['name']/'results.json')['archive']
        damaged=dict(sample,sha256='0'*64)
        try:unpack(damaged)
        except ValueError:result['self_tests'].append(dict(name='archive-tamper',rejected=True))
        else:raise ValueError('archive改変受理')
        result['scope_negative_tests']=scope_negatives(code)
    result['full_transaction_equivalence']=all(p['comparison']['complete'] for p in pairs if p['phase']=='transaction')
    result['all_commands_pass']=all(r['ok'] for r in index['runs'])
    result['status']='PASS' if result['full_transaction_equivalence'] and result['all_commands_pass'] else 'INCOMPLETE'
    (output/'scope-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('COST060_COMPARE_'+result['status']+': evidence=valid codec_pairs=3 transaction_pairs=3')
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output');parser.add_argument('--self-test',action='store_true');parser.add_argument('--scope-sha')
    try:sys.exit(main(parser.parse_args()))
    except Exception as exc:print('COST060_COMPARE_FAIL:',str(exc));sys.exit(1)
