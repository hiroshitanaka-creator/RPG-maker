#!/usr/bin/env python3
"""066: 固定Git原物と、先行記録した実QA対象の段階間bytesを照合する。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import generation_contract as old

ROOT = Path(__file__).resolve().parents[3]
BASE = 'e83bbce4018946da3e5f61f7b9f972474197f9e1'
REGISTER = '962502020acc9446dfba13d8b177c8d3cd3aac84'
CODE065 = '7aa7c6ff6eba620b93b741d58290fb698fb7cf5e'
FIXTURE = old.FIXTURE
EVIDENCE = 'docs/verification/save-native-build-contract-v1/'
TASK = 'docs/tasks/066-save-native-build-contract-v1.md'
WORKFLOW = '.github/workflows/equipment-transaction-platform.yml'
CODE = tuple(FIXTURE + x for x in ('native_build_contract_v1.py', 'test_native_build_contract_v1.py',
                                  'diagnostic_ci_build_v1.py', 'diagnostic_evidence_build_v1.py'))
ALLOWED = frozenset((WORKFLOW, TASK, 'docs/tasks/reports/066-save-native-build-contract-v1.md',
                    *CODE, *(EVIDENCE + x for x in old.EVIDENCE_NAMES)))
ADDON = 'addons/equipment_save_io/'
BINARIES = (
    ADDON + 'bin/equipment_save_io.linux.template_debug.x86_64.so',
    ADDON + 'bin/equipment_save_io.linux.template_release.x86_64.so',
    ADDON + 'bin/equipment_save_io.windows.template_debug.x86_64.dll',
    ADDON + 'bin/equipment_save_io.windows.template_release.x86_64.dll',
)
MANIFEST = ADDON + 'manifest.json'
PIN = 'e83fd0904c13356ed1d4c3d09f8bb9132bdc6b77'
DEP_URL = 'https://github.com/godotengine/godot-cpp.git'
STAGES = ('before-shipped', 'after-shipped', 'before-build', 'after-build', 'after-tests', 'after-diagnostics')
PREFIXES = ('scripts/', 'native/', 'addons/', 'tools/', 'test/', '.scope-lock/', '.github/', 'data/', 'world/')
NEW = ('scope21', 'fixed065', 'old112', 'old14', 'tracked-tree', 'clean-prebuild', 'shipped-git-bytes',
       'dependency-tree', 'fixed-four', 'only-current-three', 'identical-build', 'strict-manifest',
       'ordered-snapshots', 'external-receipts', 'actual-build-process', 'raw-build-logs',
       'post-test-bytes', 'post-diagnostic-bytes', 'binary-seven-or-not-run', 'failure-propagation',
       'complete-archive', 'latest-only', 'unchanged-budgets')
require = old.require
digest = old.digest
load = old.load
git = old.git


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def tree(root, revision):
    result = {}
    for item in git(root, 'ls-tree', '-r', '-z', old.sha(revision)).split(b'\0'):
        if item:
            meta, name = item.split(b'\t', 1)
            mode, kind, blob = meta.decode().split()
            require(kind == 'blob' and mode in ('100644', '100755'), '特殊Git entry:' + name.decode())
            result[name.decode()] = dict(mode=mode, blob=blob)
    return result


def audited(name):
    return name.startswith(PREFIXES) or name == 'project.godot'


def no_links(path, root):
    path = Path(path); root = Path(root)
    require(path == root or root in path.parents, '領域外path')
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'symlink:' + str(part))
        if part == root:
            break


def raw_file(path, root):
    no_links(path, root)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode), '非regular:' + str(path))
    return path.read_bytes(), stat.S_IMODE(info.st_mode)


def blob_id(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def scope(root, source, *, fixed=None):
    old.sha(source)
    rows = old.changes(root, REGISTER, source)
    require(all(s in ('A', 'M') and p in ALLOWED for s, p in rows), '066全21集合外/削除/rename')
    entries = tree(root, source)
    registered = tree(root, REGISTER)
    for _, path in rows:
        require(entries[path]['mode'] == registered.get(path, {'mode': '100644'})['mode'], '066 mode変更')
    strip = lambda raw: re.sub('^状態：.*$'.encode(), b'', raw, flags=re.M)
    require(strip(git(root, 'show', REGISTER + ':' + TASK)) == strip(git(root, 'show', source + ':' + TASK)), '066依頼本文変更')
    require(all(p in entries for p in CODE), '新コード4件欠落')
    if fixed:
        old.sha(fixed)
        later = old.changes(root, fixed, source)
        require(all(s in ('A', 'M') and p in ALLOWED - set(CODE) - {WORKFLOW, EVIDENCE+'assertion-map.json'} for s,p in later), '完成後コード改変')
    return rows


def map_value(root):
    prior = old.load(root / old.EVIDENCE / 'assertion-map.json')
    old.check_map(root, prior)
    return dict(schema=1, registration=REGISTER, fixed065=BASE, code065=CODE065,
                old_assertions=prior['old_assertions'], old_new_conditions=prior['new_conditions'],
                migration=[dict(id=r['id'], original_destination=r['destination'],
                                fixed='fixed065/full-contract-and-56',
                                current=r['destination'] if r['category']=='最新でも継続' else 'fixed059/scope059')
                           for r in prior['old_assertions']],
                conditions=[dict(id=x, destination='latest/native-build-v1') for x in NEW])


def check_map(root):
    value = load(root/EVIDENCE/'assertion-map.json')
    require(value == map_value(root), '旧112/追加14/新条件の欠落・重複・改変')
    require(len(value['old_assertions']) == 112 and len(value['old_new_conditions']) == 14, '旧分母変更')


def current_inventory(root, expected):
    # 全tracked集合/mode/blobを固定し、監査対象はGit indexのstat cacheを信頼せず原bytesを読む。
    index = {}
    for item in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if item:
            meta, name = item.split(b'\t',1); mode, blob, stage = meta.decode().split()
            require(stage == '0', '未解決index')
            index[name.decode()] = dict(mode=mode, blob=blob)
    require(index == expected, 'tracked集合/mode/blob不一致')
    extras = git(root, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
    require(not any(p for p in extras), '未追跡追加file')
    actual_addons={p.relative_to(root).as_posix() for p in (root/'addons').rglob('*') if not p.is_dir() or p.is_symlink()}
    require(actual_addons=={p for p in expected if p.startswith('addons/')}, 'addon未列挙file/削除')
    dirty={p.decode() for p in git(root,'diff','HEAD','--name-only','-z').split(b'\0') if p}
    require(not (dirty-{p for p in expected if audited(p)}), '監査外tracked bytes変更')
    files = {}
    for name, entry in expected.items():
        if audited(name):
            raw, mode = raw_file(root/name, root)
            files[name] = dict(bytes=len(raw), sha256=digest(raw), filesystem_mode=mode, git_mode=entry['mode'])
    return files


def fresh_build_inputs(root):
    ignored=[p.decode() for p in git(root,'ls-files','--others','--ignored','--exclude-standard','-z','--','native/equipment_save_io').split(b'\0') if p]
    require(all(p.startswith('native/equipment_save_io/.deps/godot-cpp/') for p in ignored), 'ビルド前native未登録cache/input')
    dep=root/'native/equipment_save_io/.deps/godot-cpp'
    require(not git(dep,'ls-files','--others','--ignored','--exclude-standard','-z'), 'ビルド前依存未登録cache/input')


def dependency(root, destination=None):
    dep = root/'native/equipment_save_io/.deps/godot-cpp'
    require(git(dep, 'rev-parse', 'HEAD').decode().strip() == PIN, '依存pin')
    expected = tree(dep, PIN)
    require(not git(dep,'status','--porcelain','--untracked-files=all'), '依存dirty/未追跡')
    # dependencyの全tracked原物（PREFIXESと無関係）。build後のignored生成物だけはtracked入力ではない。
    files = {}
    for name, entry in expected.items():
        raw, mode = raw_file(dep/name, dep)
        require(blob_id(raw) == entry['blob'], '依存source bytes:' + name)
        files[name] = dict(**entry, bytes=len(raw), sha256=digest(raw), filesystem_mode=mode)
        if destination is not None:
            target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    return dict(commit=PIN, tracked=files)


def manifest(raw, hashes):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'manifest重複キー'); value[key] = item
        return value
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: require(False, '非有限JSON'))
    require(set(value) == {'files'} and isinstance(value['files'], dict), 'manifest schema')
    require(set(value['files']) == set(BINARIES), 'manifest固定4entry/OS')
    require(value['files'] == {p:hashes[p]['sha256'] for p in BINARIES}, 'manifest原bytes hash')


def _capture(root, area, stage, identity):
    require(stage in STAGES and identity['profile']=='latest', '新stepはlatestのみ')
    require(identity['os'] in ('linux','windows') and identity['phase'] in ('transaction','primitives'), 'OS/phase')
    require(bool(identity['job']) and bool(identity['run']) and bool(identity['attempt']), 'job identity欠落')
    expected_head = old.sha(identity['source_sha'])
    require(git(root, 'rev-parse','HEAD').decode().strip()==expected_head, 'HEADすり替え')
    expected = tree(root, expected_head)
    index = STAGES.index(stage)
    previous = None
    if index:
        previous = read_snapshot(area, STAGES[index-1], identity)
    require(not any((area/s).exists() for s in STAGES[index:]), 'snapshot採り直し/順序逆転')
    if index==2:fresh_build_inputs(root)
    destination = area/stage
    destination.mkdir(parents=True,exist_ok=False)
    files = current_inventory(root, expected)
    for name, row in files.items():
        raw, mode = raw_file(root/name,root)
        require(digest(raw)==row['sha256'] and mode==row['filesystem_mode'], '採取中差替え')
        target = destination/'bytes'/name; target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    shipped = {}
    shipped_root = Path(identity['shipped'])
    if index >= 1:
        wanted = {p:row for p,row in expected.items() if p.startswith(ADDON)}
        actual = {ADDON+p.relative_to(shipped_root).as_posix() for p in shipped_root.rglob('*') if not p.is_dir() or p.is_symlink()}
        require(actual == set(wanted), 'shipped集合')
        for name, entry in wanted.items():
            raw, mode = raw_file(shipped_root/name[len(ADDON):],shipped_root)
            require(blob_id(raw)==entry['blob'], 'shipped Git原blob不一致')
            shipped[name]=dict(bytes=len(raw),sha256=digest(raw),filesystem_mode=mode)
            target=destination/'shipped'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    value=dict(schema=1,stage=stage,identity=identity,sequence=index,monotonic_ns=time.monotonic_ns(),
               previous=digest((area/STAGES[index-1]/'snapshot.json').read_bytes()) if index else None,
               tracked=expected,files=files,shipped=shipped,
               dependency=dependency(root,destination/'dependency-bytes') if index>=2 else None)
    value['build_evidence'] = {}
    if index >= 3:
        evidence = Path(identity['shipped']).parents[1]
        fixed_names = ('build-process.json','build-child.json','build-supervisor.log','build-stdout.log','build-stderr.log')
        paths = {'snapshots/'+x:area/x for x in fixed_names}
        paths.update({'evidence/build/'+x:evidence/'build'/x for x in ('build.json','template_debug.log','template_release.log')})
        for name, path in paths.items():
            if path.is_file():
                raw=path.read_bytes(); value['build_evidence'][name]=digest(raw)
                target=destination/'build-evidence'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    write_new(destination/'snapshot.json',value)
    receipt=dict(stage=stage,sha256=digest((destination/'snapshot.json').read_bytes()),identity=identity,
                 sequence=index,monotonic_ns=value['monotonic_ns'])
    write_new(area/'receipts'/(stage+'.json'),receipt)
    # 以後のbuild/test/diagnostic実行より先にjob stdoutへ固定。ローカルreceiptだけの信頼を主張しない。
    print('NATIVE_BUILD_V1_RECEIPT '+json.dumps(receipt,sort_keys=True),flush=True)
    validate_prefix(area,identity,stage)
    return value


def capture(root, area, stage, identity):
    try:
        return _capture(root,area,stage,identity)
    except Exception as exc:
        # 失敗時の実QA対象も採取する。先行snapshotの置換・採り直しはしない。
        failure=area/('failed-'+stage+'-'+str(time.monotonic_ns()))
        failure.mkdir(parents=True,exist_ok=False)
        observed={};errors=[]
        names={p.decode() for p in git(root,'ls-files','-z').split(b'\0') if p and audited(p.decode())}
        names.update(p.decode() for p in git(root,'ls-files','--others','--exclude-standard','-z').split(b'\0') if p and audited(p.decode()))
        names.update(p.relative_to(root).as_posix() for p in (root/'addons').rglob('*') if not p.is_dir() or p.is_symlink())
        for name in sorted(names):
            path=root/name
            try:
                if path.is_symlink():
                    observed[name]=dict(kind='symlink',target_hex=os.fsencode(os.readlink(path)).hex())
                elif not path.exists():observed[name]=dict(kind='missing')
                else:
                    raw,mode=raw_file(path,root)
                    target=failure/'bytes'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                    observed[name]=dict(kind='file',bytes=len(raw),sha256=digest(raw),mode=mode)
            except Exception as error:errors.append(name+': '+str(error))
        write_new(failure/'failure.json',dict(schema=1,identity=identity,stage=stage,error=type(exc).__name__+': '+str(exc),
                                             files=observed,collection_errors=errors,prior_snapshot_replaced=False))
        print('NATIVE_BUILD_V1_FAILED_OBSERVATION '+digest((failure/'failure.json').read_bytes()),flush=True)
        raise


def read_snapshot(area,stage,identity):
    path=area/stage/'snapshot.json'; value=load(path); receipt=load(area/'receipts'/(stage+'.json'))
    require(value.get('schema')==1 and value.get('stage')==stage and value.get('identity')==identity, 'snapshot schema/SHA/OS/job')
    require(receipt==dict(stage=stage,sha256=digest(path.read_bytes()),identity=identity,
                         sequence=STAGES.index(stage),monotonic_ns=value['monotonic_ns']), '先行receipt不一致')
    for group,folder in (('files','bytes'),('shipped','shipped')):
        expected=value[group]
        actual={p.relative_to(area/stage/folder).as_posix() for p in (area/stage/folder).rglob('*') if not p.is_dir() or p.is_symlink()}
        require(actual==set(expected), 'snapshot原bytes集合')
        for name,row in expected.items():
            raw,_=raw_file(area/stage/folder/name,area)
            require(len(raw)==row['bytes'] and digest(raw)==row['sha256'], 'snapshot原bytes改変')
    if value['sequence']>=2:
        depdir=area/stage/'dependency-bytes'
        expected=value['dependency']['tracked']
        actual={p.relative_to(depdir).as_posix() for p in depdir.rglob('*') if not p.is_dir() or p.is_symlink()}
        require(actual==set(expected), '依存snapshot原bytes集合')
        for name,row in expected.items():
            raw,_=raw_file(depdir/name,area)
            require(digest(raw)==row['sha256'] and len(raw)==row['bytes'], '依存snapshot原bytes')
    actual={p.relative_to(area/stage/'build-evidence').as_posix() for p in (area/stage/'build-evidence').rglob('*') if p.is_file()}
    require(actual==set(value['build_evidence']), 'build先行資料集合')
    for name, expected_hash in value['build_evidence'].items():
        require(digest((area/stage/'build-evidence'/name).read_bytes())==expected_hash,'build先行資料bytes')
    return value


def validate_prefix(area,identity,last):
    values=[]
    for i,stage in enumerate(STAGES[:STAGES.index(last)+1]):
        value=read_snapshot(area,stage,identity); values.append(value)
        require(value['sequence']==i, 'snapshot順序')
        if i:
            require(value['previous']==digest((area/STAGES[i-1]/'snapshot.json').read_bytes()) and
                    value['monotonic_ns']>values[i-1]['monotonic_ns'], 'snapshot先行参照/順序')
            require(value['tracked']==values[0]['tracked'], 'tracked集合変化')
        manifest((area/stage/'bytes'/MANIFEST).read_bytes(),value['files'])
        require(set(value['files'])=={p for p in value['tracked'] if audited(p)}, '監査集合欠落')
        for p,row in value['files'].items():
            if i<=2:
                require(blob_id((area/stage/'bytes'/p).read_bytes())==value['tracked'][p]['blob'], 'ビルド前dirty:'+p)
                if identity['os']=='linux':
                    require(bool(row['filesystem_mode'] & 0o111)==(row['git_mode']=='100755'), 'ビルド前mode:'+p)
            if i:
                prior=values[i-1]['files'][p]
                allowed = {MANIFEST,*[p for p in BINARIES if '.'+identity['os']+'.' in p]}
                if i==3 and p in allowed:
                    require(row['filesystem_mode']==prior['filesystem_mode'] and row['git_mode']==prior['git_mode'], '生成物mode変更')
                else:require(row==prior, '段階間bytes/mode改変:'+p)
        if i>=1:
            require(set(value['shipped'])=={p for p in value['tracked'] if p.startswith(ADDON)}, 'shipped集合')
            for p in value['shipped']:
                require(blob_id((area/stage/'shipped'/p).read_bytes())==value['tracked'][p]['blob'], 'shipped偽造')
            if i>=2:require(value['shipped']==values[1]['shipped'], 'shipped段階間不変')
        if i>=2:
            require(value['dependency']['commit']==PIN and value['dependency']['tracked'], '依存資料欠落')
            if i>=3:require(value['dependency']==values[2]['dependency'], '依存改変')
        if i>=4:require(value['build_evidence']==values[3]['build_evidence'], 'build原記録の事後差替え')
    return values


def validate_build(area, evidence, identity, recorded_evidence=None):
    original = recorded_evidence or evidence
    row=load(area/'build-process.json'); recorded_root=Path(row['cwd']); old.record_ok(row,600,recorded_root)
    require(row['planned_argv']==[sys.executable,str(recorded_root/FIXTURE/'diagnostic_ci_build_v1.py'),'--exec-build',
            '--output',str(original),'--platform',identity['os']], 'build wrapper実argv')
    raw=(area/'build-supervisor.log').read_bytes();require(digest(raw)==row['log_sha256'],'build原supervisor log')
    child=load(area/'build-child.json')
    expected=[sys.executable,str(recorded_root/'native/equipment_save_io/build.py'),'--platform',identity['os'],'--output',str(original/'build')]
    require(child['argv']==expected and child['exit_code']==0 and type(child['exit_code']) is int and
            child['pid']>0 and child['waited'] is True and child['ended_ns']>child['started_ns'], '実build記録')
    for stream in ('stdout','stderr'):
        require(digest((area/('build-'+stream+'.log')).read_bytes())==child[stream+'_sha256'], 'build原log欠落/改変')
    metadata=load(evidence/'build/build.json')
    require(metadata['godot_cpp']['commit']==PIN and len(metadata['commands'])==2,'build pin/command集合')
    for index,target in enumerate(('template_debug','template_release')):
        command=metadata['commands'][index]
        argv=[sys.executable,'-m','SCons','-C',str(recorded_root/'native/equipment_save_io'),
              'build_profile='+str(recorded_root/'native/equipment_save_io/build-profile.json'),'platform='+identity['os'],
              'target='+target,'arch=x86_64','-j4']
        require(command['argv']==argv and command['budget_seconds']==600 and command['exit_code']==0,'SCons実argv/予算/exit')
        require(digest((evidence/'build'/(target+'.log')).read_bytes())==command['log_sha256'],'SCons原log')
    before=read_snapshot(area,'before-build',identity)
    after=read_snapshot(area,'after-build',identity)
    require(before['monotonic_ns'] < child['started_ns'] < child['ended_ns'] < after['monotonic_ns'], 'buildとsnapshotの順序')
    require(set(after['build_evidence'])=={'snapshots/'+x for x in ('build-process.json','build-child.json','build-supervisor.log','build-stdout.log','build-stderr.log')} |
            {'evidence/build/'+x for x in ('build.json','template_debug.log','template_release.log')}, 'build証拠完全集合')
    for name, expected_hash in after['build_evidence'].items():
        path = evidence/name[9:] if name.startswith('evidence/') else area/name[10:]
        require(digest(path.read_bytes())==expected_hash, 'build先行原証拠差替え:'+name)
    require(metadata['files']=={p:after['files'][p]['sha256'] for p in BINARIES},'build.json独立直後bytes')
    return row


def identity(args):
    return dict(source_sha=git(ROOT,'rev-parse','HEAD').decode().strip(),os=args.platform,phase=args.phase,profile=args.profile,
                job=os.environ.get('GITHUB_JOB','local')+':'+args.platform+':'+args.phase,
                run=os.environ.get('GITHUB_RUN_ID',args.run_id),attempt=os.environ.get('GITHUB_RUN_ATTEMPT','1'),
                shipped=str(Path(args.output).resolve()/'shipped/equipment_save_io'))


def main(args):
    area=Path(args.output).resolve().parent/'native-build-v1'; ident=identity(args)
    if args.stage=='before-shipped':
        scope(ROOT,ident['source_sha']);check_map(ROOT)
        fixed=(ROOT/EVIDENCE/'code-fixed-sha.txt').read_text().strip()
        scope(ROOT,ident['source_sha'],fixed=old.sha(fixed))
        require(not git(ROOT,'status','--porcelain','--untracked-files=all'), '事前dirty')
    capture(ROOT,area,args.stage,ident)
    if STAGES.index(args.stage)>=3:validate_build(area,Path(args.output).resolve(),ident)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--stage',choices=STAGES,required=True)
    p.add_argument('--platform',choices=('linux','windows'),required=True);p.add_argument('--phase',choices=('transaction','primitives'),required=True)
    p.add_argument('--profile',default='latest');p.add_argument('--run-id',default='local-066')
    try:main(p.parse_args())
    except Exception as exc:print('NATIVE_BUILD_V1_FAIL: '+type(exc).__name__+': '+str(exc),flush=True);sys.exit(1)
