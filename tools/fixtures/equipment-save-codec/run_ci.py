#!/usr/bin/env python3
"""049専用: 固定SHAの原検査を別checkoutで実行し、失敗/警告/欠落を伝播する。"""
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
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
BASE = '5f5aab4fbe48e77f7e217b71672a043be2839d34'
FIXED049 = '99e9d03d4e095b4627b510efd4806f82276617c9'
REGISTER051 = '329567e79d2a6ace2e4c3b10b729f1e76cd27071'
ORIGINAL_CASES = 112
ORIGINAL_CHECKS = 723
VERSION = '4.7.2.stable.official.ed1daf0bf'
ENGINE = '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
BAD = re.compile(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|_FAIL:|Fontconfig error')
FILES = ['scripts/combat/battle_catalog.gd', 'scripts/game/game_session.gd',
         'scripts/game/integrated_progression.gd', 'scripts/game/equipment_document_validation.gd',
         'scripts/game/equipment_save_codec.gd', 'data/equipment_abilities.json',
         'tools/check_equipment_save_codec.gd', 'tools/fixtures/equipment-save-codec/legacy.json',
         'tools/fixtures/equipment-save-codec/fixtures.gd',
         'tools/fixtures/equipment-save-codec/expectations.json',
         'tools/fixtures/equipment-save-codec/run_ci.py',
         'tools/fixtures/equipment-save-codec/validation-expectations.json']

def require(value, message):
    if not value: raise RuntimeError(message)

def digest(value): return hashlib.sha256(value).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'JSON重複キー')
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def validate(checkout, output):
    expected = load(checkout/'tools/fixtures/equipment-save-codec/expectations.json')
    addition = load(checkout/'tools/fixtures/equipment-save-codec/validation-expectations.json')
    require(addition['original_case_count']==ORIGINAL_CASES and addition['original_checks']==ORIGINAL_CHECKS, '原固定112/723期待')
    require(len(expected['cases'])==ORIGINAL_CASES and not set(expected['cases']) & set(addition['cases']), '原/追加IDの独立')
    expected['cases'].update(addition['cases'])
    result = load(output/'codec.json')
    for key in ['original_case_count','original_checks','additional_case_count','additional_checks','case_count','checks']:
        require(type(result.get(key)) is int and result[key]==addition[key], '独立固定件数/条件数:'+key)
    require(addition['case_count']==ORIGINAL_CASES+len(addition['cases']) and addition['checks']==ORIGINAL_CHECKS+addition['additional_checks'], '追加固定ID/条件数')
    logs = (output/'codec.log').read_text()
    require(not BAD.search(logs), '原検査logの警告/失敗')
    cases = result.get('cases')
    require(isinstance(cases,list) and len(cases)==len(set(cases)) and set(cases)==set(expected['cases']), '原検査ケース集合/重複/欠落')
    require(type(result.get('case_count')) is int and result['case_count']==len(cases) and result.get('failures')==[], '原検査件数/失敗')
    require(type(result.get('checks')) is int and result['checks']>0, '原検査条件数')
    require(re.findall(r'^EQUIPMENT_CODEC_PASS: (\d+)ケース / (\d+)条件 / 失敗0$',logs,re.M)==[(str(len(cases)),str(result['checks']))], '唯一の原PASS行と結果不一致')
    records = result.get('observations')
    require(isinstance(records,list) and [r.get('case') for r in records]==cases,'全観測のID/順')
    for record in records:
        id = record['case']; code=expected['cases'][id]
        require(record.get('expected')==code and record.get('actual')==code,'固定成否期待')
        raw = output/id/'input.bin'
        require(raw.is_file() and digest(raw.read_bytes())==record.get('input_sha256') and raw.stat().st_size==record.get('input_bytes'),'入力実物hash/長さ/欠落')
        require(isinstance(record.get('errors'),list),'errorsの型')
        if code!='ok':require(record['errors'] and all(isinstance(e.get('target'),str) and e['target'] for e in record['errors']),'拒否のパス/理由')
        elif record['operation']!='validate':
            document=output/id/'document.gdv'
            require(document.is_file(),'成功document実物欠落')
            require(type(record.get('document_bytes')) is int and record['document_bytes']>0 and document.stat().st_size==record['document_bytes'] and digest(document.read_bytes())==record.get('document_sha256'), '成功document実物hash/長さ/空')
            if record['operation']=='encode':
                raw=output/id/'encoded.bin'
                require(raw.is_file() and digest(raw.read_bytes())==record.get('output_sha256'),'符号化実物hash/欠落')
    require(logs.startswith('Godot Engine v'+VERSION),'Godot原log版')
    return result

def self_test(checkout, output):
    # 実正常結果を複製し、別Pythonの実exitで判定する。原証拠は変更しない。
    mutations = ['control','exit-log','warning','missing-case','duplicate-case','actual','missing-input','input-hash','missing-document','missing-encoded','missing-summary','pass-missing','pass-count','checks-one','document-empty','document-modified','document-size','document-hash']
    rows=[]
    for name in mutations:
        target=output.parent/(output.name+'-propagation-'+name)
        shutil.copytree(output,target)
        data=load(target/'codec.json')
        text=(target/'codec.log').read_text()
        if name=='exit-log':text+='EQUIPMENT_CODEC_FAIL: 注入\n'
        if name=='warning':text+='WARNING: 注入\n'
        if name=='missing-case':data['cases'].pop()
        if name=='duplicate-case':data['cases'].append(data['cases'][0])
        if name=='actual':data['observations'][0]['actual']='forged'
        if name=='missing-input':(target/data['cases'][0]/'input.bin').rename(target/'hidden-input.bin')
        if name=='input-hash':data['observations'][0]['input_sha256']='0'*64
        if name=='missing-document':(target/'M09-new-typed/document.gdv').rename(target/'hidden-document.gdv')
        if name=='missing-encoded':(target/'M09-new-typed/encoded.bin').rename(target/'hidden-encoded.bin')
        if name=='pass-missing':text='\n'.join(line for line in text.splitlines() if not line.startswith('EQUIPMENT_CODEC_PASS:'))
        if name=='pass-count':text=text.replace('ケース /','0ケース /')
        if name=='checks-one':
            text=text.replace(str(data['checks'])+'条件','1条件');data['checks']=1
        if name=='document-empty':(target/'M09-new-typed/document.gdv').write_bytes(b'')
        if name=='document-modified':
            doc=target/'M09-new-typed/document.gdv';raw=bytearray(doc.read_bytes());raw[-1]^=1;doc.write_bytes(raw)
        if name in ['document-size','document-hash']:
            record=next(r for r in data['observations'] if r['case']=='M09-new-typed')
            record['document_bytes' if name=='document-size' else 'document_sha256']=1 if name=='document-size' else '0'*64
        write(target/'codec.json',data)
        (target/'codec.log').write_text(text)
        if name=='missing-summary':(target/'codec.json').rename(target/'hidden-summary.json')
        argv=[sys.executable,str(Path(__file__).resolve()),'--validate-only','--checkout',str(checkout),'--output',str(target)]
        child=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        (target/'validation.log').write_bytes(child.stdout)
        rows.append({'case':name,'expected_exit':0 if name=='control' else 1,'observed_exit':child.returncode,'argv':argv})
        require(child.returncode==(0 if name=='control' else 1),'失敗伝播:'+name)
    return rows

def scope_target(profile, source_sha):
    return FIXED049 if profile in ['latest','fixed051'] else source_sha

def scope_audit(repo, source_sha):
    changed=subprocess.check_output(['git','diff','--name-status',BASE,source_sha],cwd=repo).decode().splitlines()
    allowed=set(FILES)|{'docs/tasks/049-equipment-save-codec.md','docs/tasks/reports/049-equipment-save-codec.md','docs/decision-log.md','.github/workflows/equipment-codec.yml'}
    for line in changed:
        status,path=line.split('\t',1)
        require(status in ['A','M'] and (path in allowed or path.startswith(('tools/fixtures/equipment-save-codec/','docs/verification/equipment-save-codec/')) or (path.endswith('.uid') and path[:-4] in FILES)), '担当外差分:'+line)
    return changed

def implementation_scope(repo, source_sha):
    require(re.fullmatch('[0-9a-f]{40}',source_sha or ''),'051固定は完全SHA')
    changed=subprocess.check_output(['git','diff','--name-status',REGISTER051,source_sha],cwd=repo).decode().splitlines()
    allowed={'scripts/game/equipment_document_validation.gd','scripts/game/equipment_save_codec.gd','tools/check_equipment_save_codec.gd','.github/workflows/equipment-codec.yml','docs/tasks/051-fix-equipment-codec-validation.md','docs/tasks/reports/051-fix-equipment-codec-validation.md','docs/decision-log.md'}
    for line in changed:
        status,path=line.split('\t',1)
        require(status in ['A','M'] and (path in allowed or path.startswith(('tools/fixtures/equipment-save-codec/','docs/verification/equipment-codec-validation/'))),'051担当外差分:'+line)
    return changed

def scope_self_test(repo, output):
    # 独立Git objectの追加文書treeで正例と範囲逸脱負例を実行する。
    rows=[]
    with tempfile.TemporaryDirectory(prefix='codec-scope-') as area:
        env=os.environ.copy();env['GIT_INDEX_FILE']=str(Path(area)/'index')
        for name, path, profile, expected in [
            ('later-document','docs/tasks/scope-later-probe.md','latest',0),
            ('fixed-outside','scope-probe-outside.txt','fixed049',1)]:
            subprocess.run(['git','read-tree',FIXED049],cwd=repo,env=env,check=True)
            blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=b'scope fixture\n',cwd=repo).decode().strip()
            subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,path],cwd=repo,env=env,check=True)
            tree=subprocess.check_output(['git','write-tree'],cwd=repo,env=env).decode().strip()
            source=subprocess.check_output(['git','-c','user.name=QA','-c','user.email=qa@example.invalid','commit-tree',tree,'-p',FIXED049],input=b'scope fixture\n',cwd=repo).decode().strip()
            argv=[sys.executable,str(Path(__file__).resolve()),'--scope-only','--checkout',str(repo),'--profile',profile,'--source-sha',source,'--output',str(output)]
            child=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
            (output/('scope-'+name+'.log')).write_bytes(child.stdout)
            rows.append({'case':name,'source_sha':source,'scope_sha':scope_target(profile,source),'expected_exit':expected,'observed_exit':child.returncode,'argv':argv})
            require(child.returncode==expected,'範囲世代伝播:'+name)
    return rows

def main(args):
    output=Path(args.output).resolve()
    if args.scope_only:
        scope_audit(Path(args.checkout),scope_target(args.profile,args.source_sha))
        print('CODEC_SCOPE_PASS')
        return
    if args.validate_only:
        validate(Path(args.checkout),output)
        print('CODEC_EVIDENCE_PASS')
        return
    require(args.source_sha and re.fullmatch('[0-9a-f]{40}',args.source_sha),'対象は完全SHA')
    require(not output.exists(),'証拠先は新規のみ')
    output.mkdir(parents=True)
    execution={'source_sha':args.source_sha,'profile':args.profile,'commands':[],'status':'RUNNING'}
    write(output/'execution.json',execution)
    godot=Path(args.godot).resolve()
    require(digest(godot.read_bytes())==ENGINE,'公式Godot実体hash')
    checkout=Path(tempfile.mkdtemp(prefix='codec049-'))/'checkout'
    try:
        subprocess.run(['git','clone','--quiet','--shared','--no-checkout',str(ROOT),str(checkout)],check=True)
        subprocess.run(['git','checkout','--quiet','--detach',args.source_sha],cwd=checkout,check=True)
        env=os.environ.copy()
        for key, area in [('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config')]:
            env[key]=str(checkout.parent/area);Path(env[key]).mkdir()
        env['EQUIPMENT_CODEC_EVIDENCE']=str(output)
        def command(label,argv,limit):
            start=time.monotonic();expired=False
            try:
                process=subprocess.run(argv,cwd=checkout,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit)
                code=process.returncode;raw=process.stdout
            except subprocess.TimeoutExpired as exc:
                code=124;raw=(exc.stdout or b'')+b'\nTIMEOUT';expired=True
            (output/(label+'.log')).write_bytes(raw)
            execution['commands'].append({'name':label,'argv':argv,'cwd':str(checkout),'budget_seconds':limit,'seconds':time.monotonic()-start,'exit_code':code,'timed_out':expired,'log_sha256':digest(raw)})
            write(output/'execution.json',execution)
            require(code==0 and not expired and not BAD.search(raw.decode()),label+'失敗/警告/timeout')
            return raw
        command('version',[str(godot),'--version'],30)
        command('frozen-before',[sys.executable,'tools/check_frozen_files.py'],30)
        try:
            command('import',[str(godot),'--headless','--editor','--import','--quit'],600)
            command('codec',[str(godot),'--headless','--path','.', '--script','res://tools/check_equipment_save_codec.gd'],120)
        finally:
            command('frozen-after',[sys.executable,'tools/check_frozen_files.py'],30)
        result=validate(checkout,output)
        execution['case_count']=result['case_count'];execution['checks']=result['checks']
        execution['source_files']={path:digest((checkout/path).read_bytes()) for path in FILES}
        execution['engine_sha256']=digest(godot.read_bytes())
        execution['scope_sha']=scope_target(args.profile,args.source_sha)
        execution['scope_changes']=scope_audit(ROOT,execution['scope_sha'])
        execution['implementation_sha']=args.implementation_sha
        execution['implementation_scope_changes']=implementation_scope(ROOT,args.implementation_sha)
        execution['scope_propagation']=scope_self_test(ROOT,output)
        execution['propagation']=self_test(checkout,output)
        execution['status']='PASS'
        write(output/'execution.json',execution)
        write(output/'sha256.json',{str(p.relative_to(output)):digest(p.read_bytes()) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='sha256.json'})
        print(f'CODEC_CI_PASS: source={args.source_sha} cases={result["case_count"]} checks={result["checks"]} propagation={len(execution["propagation"])}')
    except Exception:
        execution['status']='FAIL';write(output/'execution.json',execution)
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--implementation-sha')
    parser.add_argument('--source-sha');parser.add_argument('--profile',choices=['fixed049','fixed051','latest'])
    parser.add_argument('--godot');parser.add_argument('--output',required=True)
    parser.add_argument('--scope-only',action='store_true')
    parser.add_argument('--validate-only',action='store_true');parser.add_argument('--checkout')
    try:main(parser.parse_args())
    except Exception as error:
        print('CODEC_CI_FAIL:',error);sys.exit(1)
