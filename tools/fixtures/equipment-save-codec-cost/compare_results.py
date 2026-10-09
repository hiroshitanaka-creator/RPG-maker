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


def normalized(value):
    if isinstance(value,dict):return {k:normalized(v) for k,v in value.items() if k not in ['pid','user_dir']}
    if isinstance(value,list):return [normalized(v) for v in value]
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
    differences=[];matched=[]
    for case in sorted(set(lcases)&set(rcases)):
        a,b=lcases[case],rcases[case]
        if normalized(a['actual'])!=normalized(b['actual']):differences.append(case+':受理拒否/reason/結果')
        if a['checks']!=b['checks']:differences.append(case+':既存条件')
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
    return dict(common_cases=matched,missing_off=missing_left,missing_on=missing_right,differences=differences,complete=not (missing_left or missing_right or differences),normalization='process pidと専用user_dirだけを比較投影から外す。原JSONは全保存。')


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
    require(json.loads(files['execution.json'])==load(path/'exit.json'),'原実行記録対応')
    module_spec=importlib.util.spec_from_file_location('cost060_driver',ROOT/'tools/check_equipment_save_codec_cost.py');driver=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(driver)
    require(driver.summarize(files)==load(path/'measurements.json'),'原spanから再計算不一致')
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
    result=dict(evidence_integrity=True,pairs=pairs,times=times,code_scope=code_scope,latest_scope=scope(head),self_tests=[])
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
