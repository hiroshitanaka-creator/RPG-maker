#!/usr/bin/env python3
"""066: 失敗も全原物を保存し、独立再展開と段階間照合を行う。"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile
import native_build_contract_v1 as n
import generation_contract as g
from diagnostic_ci_build_v1 import COMMANDS, SETUP, BUDGETS


def validate_diagnostics(out,identity):
    v=g.load(out/'execution.json')
    n.require(v['schema']==4 and v['identity']==identity and v['source_sha']==identity['source_sha'] and
              (v['fixed059'],v['fixed065'],v['code065'])==(g.FIXED059,n.BASE,n.CODE065),'診断世代/schema')
    n.require(v['status']=='PASS' and v['failures']==[],'元診断失敗')
    n.require([r['label'] for r in v['setup']]==list(SETUP) and [r['label'] for r in v['commands']]==list(COMMANDS),'全準備/診断集合')
    n.require(g.load(out/'generation-manifest.json')==g.snapshot(out,('generation-manifest.json',)),'診断原bytes集合')
    pins=g.load(out/'pins.json')
    n.require(pins.get('method')=='verified-offline-git-objects' and pins.get('code_sha')==n.CODE065 and
              pins.get('registration_sha')==g.BASE and pins.get('network_used') is False and
              pins.get('all_object_bytes_verified') is True,'065固定資料')
    n.require(v['fixed059_before']==v['fixed059_after']==dict(sha=g.FIXED059,scope_sha256=g.FIXED_SCOPE_SHA256,clean=True),'059固定原物')
    n.require(v['fixed065_after']==dict(sha=n.BASE,code_sha=n.CODE065,tracked_clean=True) and v['fixed065_before'],'065固定原物')
    scripts=dict(zip(COMMANDS,('test_capture057.py','scope059.py','test_capture059.py','reproduce058.py','diagnostics057.py',
                              'generation_contract.py','test_generation_contract.py','test_native_build_contract_v1.py')))
    for row in v['setup']+v['commands']:
        label=row['label'];g.record_ok(row,BUDGETS[label],v['checkout'])
        n.require(g.load(out/(label+'-process.json'))=={k:x for k,x in row.items() if k!='label'},'原process記録')
        raw=(out/(label+'.log')).read_bytes();n.require(raw and n.digest(raw)==row['log_sha256'],'診断原log')
        argv=row['planned_argv']
        if label in COMMANDS:
            cwd=Path(v['checkout']) if label not in ('scope059','generation-contract','generation-tests') else Path(row['cwd'])
            n.require(Path(row['cwd'])==cwd and Path(argv[1])==cwd/g.FIXTURE/scripts[label],'診断実argv/cwd')
            if label=='scope059':
                n.require(cwd.name=='qa065-fixed059' and argv[argv.index('--code-sha')+1]==g.FIXED059 and
                          argv[argv.index('--source-sha')+1]==g.FIXED059,'固定059 argv')
            if label in ('generation-contract','generation-tests'):
                n.require(cwd.name=='qa066-fixed065' and argv[argv.index('--code-sha')+1]==n.CODE065,'固定065 argv')
            if label=='generation-contract':n.require(argv[argv.index('--source-sha')+1]==n.BASE,'065固定提出')
    for label,expected in (('capture-tests',g.CASES057),('capture059',g.CASES059)):
        tests=g.load(out/label/'tests.json')
        n.require(tests.get('status')=='PASS' and [r['case'] for r in tests['cases']]==list(expected) and
                  all(r.get('status')=='PASS' for r in tests['cases']),'全12/27正負')
    fixed=g.load(out/'scope.json')
    n.require((fixed.get('base'),fixed.get('registration'),fixed.get('code_sha'),fixed.get('source_sha'))==
              (g.BASE059,g.REGISTER059,g.FIXED059,g.FIXED059),'固定059世代')
    n.require([r['case'] for r in fixed['propagation']]==list(g.SCOPE_CASES),'固定059全10')
    for index,row in enumerate(fixed['propagation']):
        n.require(row['exit_code']==row['expected_exit']==(0 if index==0 else 1),'固定059正負exit')
        n.require((out/'scope059'/(row['case']+'.log')).is_file(),'059原log')
    measure=g.load(out/'measurements/diagnostics.json')
    n.require(measure.get('source_sha')==identity['source_sha'] and measure.get('status')=='PASS' and measure.get('failures')==[],'最新計測')
    n.require([(s['seed'],s['mode']) for s in measure['samples']]==[(s,m) for s in ('typed','plain','granted','trial-missing','trial-corrupt','trial-unclean') for m in ('off','on')],'12sample')
    contract=g.load(out/'generation.json')
    n.require((contract['source_sha'],contract['code_sha'],contract['fixed059_sha'])==(n.BASE,n.CODE065,g.FIXED059),'旧065契約')
    from test_generation_contract import CASES,expected_exit
    tests=g.load(out/'generation-tests/tests.json')
    n.require(tests['status']=='PASS' and [r['case'] for r in tests['cases']]==list(CASES) and len(CASES)==56 and
              all(r['exit_code']==r['expected_exit']==expected_exit(r['case']) for r in tests['cases']),'旧065全56')
    from test_native_build_contract_v1 import CASES as NEW_CASES
    tests=g.load(out/'native-tests/tests.json')
    n.require(tests['status']=='PASS' and [r['case'] for r in tests['cases']]==list(NEW_CASES) and
              all(r['status']=='PASS' for r in tests['cases']),'066全正負')
    return v


BINARY_CASES=('debug-load','missing-manifest','malformed-manifest','missing-binary','corrupt-binary','binary-rehash','release-load')

def binary_results(evidence):
    commands=g.load(evidence/'commands.json') if (evidence/'commands.json').exists() else []
    result={}
    for label in ('binary-checks','shipped-binary-checks'):
        records=[r for r in commands if r['name']==label]
        if not records:
            result[label]=dict(status='NOT_RUN',reason='run_ciが当該commandへ未到達');continue
        n.require(len(records)==1,'binary process重複');row=records[0];g.record_ok(row,180,Path(row['cwd']))
        n.require(g.load(evidence/(label+'-process.json'))=={k:v for k,v in row.items() if k!='name'},'binary原process')
        raw=(evidence/(label+'.log')).read_bytes();n.require(raw and n.digest(raw)==row['log_sha256'],'binary原log')
        summary=g.load(evidence/label/'summary.json')
        n.require(summary.get('status')=='PASS' and summary.get('case_count')==7 and
                  [r['case'] for r in summary['cases']]==list(BINARY_CASES),'binary全7')
        for case in summary['cases']:
            folder='release' if case['case']=='release-load' else case['case']
            raw=(evidence/label/folder/'raw.log').read_bytes()
            n.require(case['exit_code']==0 and case['argv'] and raw and n.digest(raw)==case['log_sha256'],'binary実process/log')
        result[label]=dict(status='PASS',count=7)
    return result


def archive_originals(roots,destination):
    destination.mkdir(parents=True,exist_ok=False)
    archive=destination/'native-build-originals.zip';members=[];links=[];directories=[]
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for prefix,root in roots.items():
            if not root.exists():continue
            for path in sorted(root.rglob('*')):
                name=prefix+'/'+path.relative_to(root).as_posix()
                if path.is_symlink():links.append(dict(path=name,target_hex=os.fsencode(os.readlink(path)).hex()))
                elif path.is_dir():directories.append(name)
                elif path.is_file():
                    raw=path.read_bytes();members.append(dict(path=name,bytes=len(raw),sha256=n.digest(raw)));z.writestr(name,raw)
                else:raise ValueError('特殊原file:'+str(path))
        index=dict(files=members,links=links,directories=directories,omitted_regular_files=[])
        z.writestr('original-index.json',json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    # 原物を独立directoryへ再展開し、member集合/hash/長を照合。任意path抽出はしない。
    with tempfile.TemporaryDirectory(prefix='native066-unpack-',dir=destination.parent) as folder:
        root=Path(folder)
        with zipfile.ZipFile(archive) as z:
            n.require(z.namelist()==[r['path'] for r in members]+['original-index.json'],'archive全member')
            n.require(json.loads(z.read('original-index.json'))==index,'archive索引')
            for row in members:
                name=row['path'];n.require(not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name,'archive path')
                raw=z.read(name);n.require(len(raw)==row['bytes'] and n.digest(raw)==row['sha256'],'archive原bytes')
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        # 同じ生成時inventoryの確認だけで終えず、再展開から段階契約を再計算。
        replay_errors=[]
        try:
            identity=g.load(root/'snapshots/before-shipped/snapshot.json')['identity']
            n.validate_prefix(root/'snapshots',identity,'after-diagnostics')
            n.validate_build(root/'snapshots',root/'evidence',identity,recorded_evidence=roots['evidence'])
            validate_diagnostics(root/'evidence/task059',identity)
        except Exception as exc:replay_errors.append(str(exc))
    n.write_new(destination/'original-index.json',index)
    return dict(file=archive.name,bytes=archive.stat().st_size,sha256=n.digest(archive.read_bytes()),members=len(members),replay_errors=replay_errors)


def collect(evidence,destination,identity):
    snapshots=evidence.parent/'native-build-v1';errors=[];binary={}
    for label,call in (
        ('snapshots',lambda:n.validate_prefix(snapshots,identity,'after-diagnostics')),
        ('build',lambda:n.validate_build(snapshots,evidence,identity)),
        ('diagnostic',lambda:validate_diagnostics(evidence/'task059',identity)),
        ('original-run-ci',lambda:n.require(g.load(evidence/'execution.json')['status']=='PASS','原run_ci非成功/未終端'))):
        try:call()
        except Exception as exc:errors.append(label+': '+type(exc).__name__+': '+str(exc))
    try:binary=binary_results(evidence)
    except Exception as exc:errors.append('binary: '+str(exc))
    if any(r['status']!='PASS' for r in binary.values()):errors.append('binary未到達を保持')
    archive=archive_originals(dict(evidence=evidence,snapshots=snapshots),destination)
    errors.extend('再展開: '+x for x in archive['replay_errors'])
    result=dict(schema=1,identity=identity,status='FAIL' if errors else 'PASS',errors=errors,binary_checks=binary,archive=archive,
                scope='066段階間契約。旧失敗を取消さず、保存全体/F1/S3/UI受入とは別。',
                trust='固定入力と観測build・段階間同一性。再現可能build、compiler正当性、同権限悪意processへの完全防御は未実証。job原receiptは親が照合する。')
    n.write_new(destination/'summary.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--destination',required=True)
    p.add_argument('--source-sha');p.add_argument('--platform',required=True);p.add_argument('--phase',required=True);p.add_argument('--profile',default='latest');p.add_argument('--run-id',default='local-066')
    a=p.parse_args()
    try:
        ident=n.identity(a)
        if a.source_sha:ident['source_sha']=g.sha(a.source_sha)
        r=collect(Path(a.output).resolve(),Path(a.destination).resolve(),ident);print(json.dumps(r,ensure_ascii=False));sys.exit(0 if r['status']=='PASS' else 1)
    except Exception as exc:print('EVIDENCE_BUILD_V1_FAIL: '+str(exc));sys.exit(1)
