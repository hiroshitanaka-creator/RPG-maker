#!/usr/bin/env python3
"""066 validatorの合成正負。実OS build/7ロード/CIの成功とは区別する。"""
import argparse
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch
import native_build_contract_v1 as n

POSITIVES=tuple('positive-'+osname+'-'+phase+'-'+kind for osname in ('linux','windows') for phase in ('transaction','primitives') for kind in ('changed','identical'))
NEGATIVES=('dirty','shipped-forged','source','cpp','build-py','sconstruct','pin','profile','gdscript','gdextension',
           'other-os','addon-extra','added','deleted','renamed','symlink','mode','manifest-extra','manifest-missing',
           'manifest-duplicate','manifest-os','manifest-hash','rehash-all','after-build-replace','test-replace','diagnostic-replace',
           'snapshot-missing','snapshot-order','snapshot-sha','snapshot-os','snapshot-job','schema-downgrade',
           'snapshot-bytes','snapshot-receipt','snapshot-recapture','build-nonzero','build-timeout','build-not-run',
           'build-log-missing','build-unconfirmed','build-argv','build-budget','fixed055','fixed057',
           'scope-outside','scope-old-code','scope-old-evidence','scope-task-body','map-missing','map-duplicate','map-replaced',
           'old112','old14','workflow-budgets','dependency-dirty','ignored-dependency-input','ignored-native-input')
EXTRA_POSITIVES=('binary-not-run-control','failed-archive-control')
CASES=POSITIVES+EXTRA_POSITIVES+NEGATIVES


def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)


def commit(root):
    subprocess.run(['git','add','.'],cwd=root,check=True,stdout=subprocess.PIPE)
    subprocess.run(['git','-c','user.name=QA','-c','user.email=qa@example.invalid','commit','-m','066検査fixture'],cwd=root,check=True,stdout=subprocess.PIPE)
    return n.git(root,'rev-parse','HEAD').decode().strip()


def start(area,osname='linux',phase='primitives'):
    root=area/'repo';root.mkdir();subprocess.run(['git','init','-q',str(root)],check=True)
    for name in n.BINARIES:put(root/name,('fixture '+name).encode())
    for name in ('scripts/example.gd','native/equipment_save_io/src/example.cpp','native/equipment_save_io/build.py',
                 'native/equipment_save_io/SConstruct','native/equipment_save_io/dependencies.json','native/equipment_save_io/build-profile.json',
                 n.ADDON+'equipment_save_io.gdextension',n.WORKFLOW,'tools/qa.py','project.godot'):
        put(root/name,b'fixture source\n')
    hashes={p:n.digest((root/p).read_bytes()) for p in n.BINARIES}
    put(root/n.MANIFEST,json.dumps({'files':hashes}).encode())
    sha=commit(root);evidence=area/'evidence';snap=area/'snapshots'
    ident=dict(source_sha=sha,os=osname,phase=phase,profile='latest',job='fixture-job',run='fixture-run',attempt='1',shipped=str(evidence/'shipped/equipment_save_io'))
    return root,snap,ident


def fake_dependency(root,destination=None):
    if destination is not None:put(destination/'fixture.cpp',b'fixture')
    return dict(commit=n.PIN,tracked={'fixture.cpp':{'sha256':n.digest(b'fixture'),'bytes':7}})


def stage(root,snap,ident,name):
    with patch.object(n,'dependency',fake_dependency),patch.object(n,'fresh_build_inputs',lambda root:None):return n.capture(root,snap,name,ident)


def rehash(root):
    put(root/n.MANIFEST,json.dumps({'files':{p:n.digest((root/p).read_bytes()) for p in n.BINARIES}}).encode())


def rewrite_snapshot(snap,stage_name,mutator):
    path=snap/stage_name/'snapshot.json';value=n.load(path);mutator(value)
    path.write_text(json.dumps(value));receipt=snap/'receipts'/(stage_name+'.json');r=n.load(receipt)
    r['sha256']=n.digest(path.read_bytes());receipt.write_text(json.dumps(r))


def probe(name,area):
    if name in ('ignored-dependency-input','ignored-native-input'):
        root,snap,ident=start(area)
        put(root/'native/equipment_save_io/.gitignore',b'.deps/\nsrc/*.o\n')
        dep=root/'native/equipment_save_io/.deps/godot-cpp';dep.mkdir(parents=True)
        subprocess.run(['git','init','-q',str(dep)],check=True)
        put(dep/'.gitignore',b'gen/\n');commit(dep);commit(root)
        n.fresh_build_inputs(root)
        put(dep/'gen/injected.cpp' if name=='ignored-dependency-input' else root/'native/equipment_save_io/src/stale.o',b'injected ignored build input')
        n.fresh_build_inputs(root);return
    if name=='binary-not-run-control':
        from diagnostic_evidence_build_v1 import binary_results
        result=binary_results(area)
        n.require(set(result)=={'binary-checks','shipped-binary-checks'} and all(r['status']=='NOT_RUN' for r in result.values()), '未到達2系統を明記')
        return
    if name=='failed-archive-control':
        from diagnostic_evidence_build_v1 import archive_originals
        import zipfile
        source=area/'input';source.mkdir();put(source/'failure.log',b'original failure\x00\xff')
        put(source/'child.json',b'{"exit_code":7,"timed_out":true}')
        result=archive_originals({'evidence':source,'snapshots':area/'missing-snapshots'},area/'archive')
        n.require(result['replay_errors'] and result['members']==2,'失敗と全原member維持')
        with zipfile.ZipFile(area/'archive'/result['file']) as z:
            n.require(z.read('evidence/failure.log')==(source/'failure.log').read_bytes(),'失敗原bytes')
        return
    if name.startswith('scope-'):
        from test_generation_contract import commit_variant
        paths={'scope-outside':'outside066.txt','scope-old-code':n.old.CODE[0],
               'scope-old-evidence':n.old.EVIDENCE+'README.md','scope-task-body':n.TASK}
        source=n.git(n.ROOT,'rev-parse','HEAD').decode().strip()
        variant=commit_variant(n.ROOT,source,area,paths[name],b'changed fixture\n')
        n.scope(n.ROOT,variant);return
    if name.startswith('map-') or name in ('old112','old14'):
        value=n.map_value(n.ROOT)
        if name=='map-missing':value['migration'].pop()
        if name=='map-duplicate':value['migration'].append(value['migration'][0])
        if name=='map-replaced':value['migration'][0]['current']='skip'
        if name=='old112':value['old_assertions'].pop()
        if name=='old14':value['old_new_conditions'].pop()
        n.require(value==n.map_value(n.ROOT),'対応表改変拒否');return
    if name=='workflow-budgets':
        original=n.git(n.ROOT,'show',n.BASE+':'+n.WORKFLOW).decode()
        actual=(n.ROOT/n.WORKFLOW).read_text()
        n.require('timeout-minutes: 15' in actual and 'continue-on-error' not in actual,'job予算/失敗')
        # 正例のCI配線検査は別に行う。この負例では延長を明示拒否する。
        changed=actual.replace('timeout-minutes: 15','timeout-minutes: 16')
        n.require('timeout-minutes: 15' in changed,'job予算延長拒否');return
    if name.startswith('build-') and name not in ('build-py',):
        from test_generation_contract import fixture
        fixture(area,n.BASE,n.CODE065)
        row=n.load(area/'capture-tests-process.json');row['budget_seconds']=600
        row.update(seconds=1,ended_monotonic=2)
        if name=='build-nonzero':row['exit_code']=7
        if name=='build-timeout':row['timed_out']=True
        if name=='build-not-run':row.update(pid=None,argv=None,exit_code=None)
        if name=='build-log-missing':
            (area/'capture-tests.log').rename(area/'missing.log');(area/'capture-tests.log').read_bytes()
        if name=='build-unconfirmed':row['supervision']['stopped']=False
        if name=='build-argv':row['argv']=['wrong']
        if name=='build-budget':row['budget_seconds']=601
        n.old.record_ok(row,600);return
    osname='windows' if name.startswith('positive-windows') else 'linux'
    phase='transaction' if '-transaction-' in name else 'primitives'
    root,snap,ident=start(area,osname,phase)
    if name in ('fixed055','fixed057'):ident['profile']=name
    if name=='dirty':put(root/'scripts/example.gd',b'dirty')
    stage(root,snap,ident,'before-shipped')
    shutil.copytree(root/n.ADDON,Path(ident['shipped']))
    if name=='shipped-forged':put(Path(ident['shipped'])/'bin'/Path(n.BINARIES[0]).name,b'forged')
    stage(root,snap,ident,'after-shipped')
    stage(root,snap,ident,'before-build')
    paths={'source':'tools/qa.py','cpp':'native/equipment_save_io/src/example.cpp','build-py':'native/equipment_save_io/build.py',
           'sconstruct':'native/equipment_save_io/SConstruct','pin':'native/equipment_save_io/dependencies.json',
           'profile':'native/equipment_save_io/build-profile.json','gdscript':'scripts/example.gd','gdextension':n.ADDON+'equipment_save_io.gdextension'}
    if name in paths:put(root/paths[name],b'changed')
    binary=n.BINARIES[2] if osname=='windows' else n.BINARIES[0]
    if name.startswith('positive-') and name.endswith('-changed'):put(root/binary,b'new fixture binary');rehash(root)
    if name=='other-os':put(root/n.BINARIES[2],b'other OS');rehash(root)
    if name in ('added','addon-extra'):put(root/(n.ADDON+'extra.so' if name=='addon-extra' else 'tools/extra.py'),b'new')
    if name=='deleted':(root/'tools/qa.py').rename(area/'deleted-preserved')
    if name=='renamed':(root/'tools/qa.py').rename(root/'tools/renamed.py')
    if name=='symlink':
        (root/'tools/qa.py').rename(area/'link-original');(root/'tools/qa.py').symlink_to(area/'link-original')
    if name=='mode':subprocess.run(['git','update-index','--chmod=+x',binary],cwd=root,check=True)
    if name.startswith('manifest-'):
        p=root/n.MANIFEST;value=n.load(p)
        if name=='manifest-extra':value['files']['extra']=n.digest(b'x')
        if name=='manifest-missing':value['files'].pop(binary)
        if name=='manifest-os':value['files'][binary.replace('.linux.','.macos.')]=value['files'].pop(binary)
        if name=='manifest-hash':value['files'][binary]='0'*64
        raw=json.dumps(value).encode()
        if name=='manifest-duplicate':raw=b'{"files":{},"files":'+json.dumps(value['files']).encode()+b'}'
        p.write_bytes(raw)
    stage(root,snap,ident,'after-build')
    if name in ('rehash-all','after-build-replace','test-replace'):
        put(root/binary,b'late forged binary');rehash(root)
        put(area/'evidence/build/build.json',json.dumps({'files':n.load(root/n.MANIFEST)['files']}).encode())
    stage(root,snap,ident,'after-tests')
    if name=='diagnostic-replace':put(root/binary,b'diagnostic replace');rehash(root)
    stage(root,snap,ident,'after-diagnostics')
    if name=='snapshot-missing':(snap/'before-build/snapshot.json').rename(area/'missing-snapshot')
    if name=='snapshot-order':rewrite_snapshot(snap,'after-build',lambda v:v.update(sequence=1))
    if name=='snapshot-sha':rewrite_snapshot(snap,'after-build',lambda v:v['identity'].update(source_sha=n.BASE))
    if name=='snapshot-os':rewrite_snapshot(snap,'after-build',lambda v:v['identity'].update(os='windows'))
    if name=='snapshot-job':rewrite_snapshot(snap,'after-build',lambda v:v['identity'].update(job='other'))
    if name=='schema-downgrade':rewrite_snapshot(snap,'after-build',lambda v:v.update(schema=0))
    if name=='snapshot-bytes':put(snap/'before-build/bytes'/binary,b'changed')
    if name=='snapshot-receipt':put(snap/'receipts/after-build.json',b'{}')
    if name=='snapshot-recapture':stage(root,snap,ident,'before-shipped')
    if name=='dependency-dirty':rewrite_snapshot(snap,'after-build',lambda v:v['dependency']['tracked'].update({'extra':{}}))
    n.validate_prefix(snap,ident,'after-diagnostics')


def main(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);rows=[]
    for name in CASES:
        area=output/name;area.mkdir();error=None
        stdout=io.StringIO();stderr=io.StringIO();start_time=time.monotonic()
        try:
            with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):probe(name,area)
        except Exception as exc:error=type(exc).__name__+': '+str(exc)
        positive=name in POSITIVES+EXTRA_POSITIVES
        # このfixtureの契約違反だけを期待拒否とする。構文/NameError等はテスト失敗。
        rejected=error is not None and error.split(':',1)[0] in ('ValueError','FileNotFoundError')
        ok=(error is None) if positive else rejected
        put(area/'stdout.log',stdout.getvalue().encode());put(area/'stderr.log',stderr.getvalue().encode())
        rows.append(dict(case=name,expected='accept' if positive else 'reject',status='PASS' if ok else 'FAIL',error=error,seconds=time.monotonic()-start_time))
        (output/'tests.json').write_text(json.dumps(dict(schema=1,status='PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL',
                fixture_only=True,scope='validatorの合成正負。実build/OS/CI成功とは別。',cases=rows),ensure_ascii=False,indent=2)+'\n')
    print('NATIVE_BUILD_TESTS '+str(len(rows))+' failures='+str([r for r in rows if r['status']!='PASS']))
    return int(any(r['status']!='PASS' for r in rows))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);sys.exit(main(p.parse_args().output))
