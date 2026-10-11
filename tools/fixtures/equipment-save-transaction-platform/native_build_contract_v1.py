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


def legacy_scope(root, source, *, fixed=None):
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


# 2026-10-11 条件付きA/世代分離B。承認原文・hash・正式SHAの受領前は未設定。
# 環境変数や検査対象ファイルから許可hashを生成/補完しない。
# 値の設定は親の具体承認後の別段階。旧BASE/REGISTER/CODE065/pinは変更しない。
GENERATION_APPROVAL = None
TEST67 = FIXTURE + 'test_native_build_contract_v1.py'
TEST67_SHA256 = 'fba1d492e1fbef4ea1296b82626707e7f3b216d9092e88c678c8f7000f83e8f7'
DRIVE_INDEX = EVIDENCE + 'drive-evidence-index.json'
DECISION_LOG = 'docs/decision-log.md'
IMPLEMENTATION = frozenset(set(CODE) - {TEST67} | {WORKFLOW})
DOCUMENT_HASH_KEYS = {TASK:'task_body_sha256', DRIVE_INDEX:'drive_index_sha256', DECISION_LOG:'decision_log_sha256'}
# 親から受領した独立期待値。検査対象から生成しない。原文取得/正式SHA承認は別記録。
APPROVED_DOCUMENT_HASHES = {
    'task_body_sha256':'9cbdb54a558f04d45bcbea85fd05150416a2181ea0b61fe4054469f69cdb9f60',
    'drive_index_sha256':'4ca246c9f280adb6ee954e0a0bd92e58bed899307dbd69c2441b0634d2d58724',
    'decision_log_sha256':'7aa6b1ad4866e1a9b7ddc074c5a98ac170091d79efb767362a02954eefb6225c',
}
EVIDENCE_LINE = '親が保存できるよう変更全ファイルの原bytes'.encode()


def generation_policy():
    require(isinstance(GENERATION_APPROVAL,dict), 'generation-approval-missing')
    require(set(GENERATION_APPROVAL)=={'baseline_sha','baseline_tree'},'generation-baseline-approval-keys')
    # 自己参照commit SHAをコード内へ埋めない。親の明示承認後にCIの管理値で固定する。
    # 未設定時にHEADやcode-fixed-sha.txtへフォールバックしない。
    return policy_value(dict(GENERATION_APPROVAL,**APPROVED_DOCUMENT_HASHES,
                             code_sha=os.environ.get('RPG066_CODE_SHA'),
                             completion_sha=os.environ.get('RPG066_COMPLETION_SHA')))


def policy_value(value):
    require(isinstance(value, dict), 'generation-approval-missing')
    keys={'baseline_sha','baseline_tree','code_sha','completion_sha',*DOCUMENT_HASH_KEYS.values()}
    require(set(value)==keys, 'generation-approval-keys')
    for key in ('baseline_sha','baseline_tree','code_sha','completion_sha'):
        old.sha(value[key])
    for key in DOCUMENT_HASH_KEYS.values():
        require(isinstance(value[key],str) and re.fullmatch('[0-9a-f]{64}',value[key]), 'generation-approval-hash:'+key)
    return dict(value)


def status_parts(raw):
    require(isinstance(raw,bytes), 'status-raw-bytes')
    # LF区切りを保持。CRLFもそのまま残し、デコードや改行正規化はしない。
    lines=raw.split(b'\n')
    hits=[i for i,line in enumerate(lines) if line.startswith('状態：'.encode())]
    require(len(hits)==1, 'status-count')
    sections=[i for i,line in enumerate(lines) if line.startswith(b'##')]
    require(lines[0].startswith(b'# ') and sections and 0<hits[0]<sections[0], 'status-metadata-position')
    index=hits[0]
    require(index<len(lines)-1 and b'\r' not in lines[index].rstrip(b'\r'), 'status-line-termination')
    line=lines[index]+b'\n'
    body=b'\n'.join(lines[:index]+lines[index+1:])
    return line,body


def status_record(before,after):
    a,body_a=status_parts(before);b,body_b=status_parts(after)
    return dict(before_hex=a.hex(),after_hex=b.hex(),changed=a!=b,
                before_body_sha256=digest(body_a),after_body_sha256=digest(body_b))


def evidence_only(before,after):
    _,a=status_parts(before);_,b=status_parts(after)
    # 形式は差分位置の特定だけに使用する。受入にはdocumentsの承認本文hashが必須。
    heading='## 証拠の保存（2026-10-11 依頼者決定）\n'.encode()
    boundary='## 契約の必須条件\n'.encode()
    if heading not in a and heading in b:
        require(b.count(heading)==1 and a.count(boundary)==b.count(boundary)==1,
                'task-outside-evidence')
        start=a.index(boundary);end=b.index(boundary)
        require(b[:start]==a[:start] and b[start:].startswith(heading) and
                end>start and b[end:]==a[start:], 'task-outside-evidence')
        return
    # 既存の段落差分の位置検査と拒否理由も保持。ここだけでは承認しない。
    lines=a.splitlines(keepends=True)
    hits=[i for i,line in enumerate(lines) if line.startswith(EVIDENCE_LINE)]
    require(len(hits)==1, 'task-evidence-anchor')
    index=hits[0];prefix=b''.join(lines[:index]);suffix=b''.join(lines[index+1:])
    require(b.startswith(prefix) and (not suffix or b.endswith(suffix)) and
            len(b)>=len(prefix)+len(suffix), 'task-outside-evidence')


def documents(before,after,policy,*,final):
    a,b=before(TASK),after(TASK);record=status_record(a,b)
    if record['before_body_sha256']!=record['after_body_sha256']:
        evidence_only(a,b)
        require(policy is not None and record['after_body_sha256']==policy['task_body_sha256'], 'task-approved-hash')
    if final:
        require(record['after_body_sha256']==policy['task_body_sha256'], 'task-approved-hash')
        require(digest(after(DRIVE_INDEX))==policy['drive_index_sha256'], 'drive-approved-hash')
        old_log,new_log=before(DECISION_LOG),after(DECISION_LOG)
        require(old_log.endswith(b'\n') and new_log.startswith(old_log), 'decision-original-bytes')
        addition=new_log[len(old_log):]
        # 旧原bytesから追記1行を切り出す。形式のみでは通さず全文hashで固定する。
        require(addition.endswith(b'\n') and
                addition.count(b'\n')==1 and b'\r' not in addition, 'decision-one-line')
        require(digest(new_log)==policy['decision_log_sha256'], 'decision-approved-hash')
    return record


def test67_bytes(raw):
    require(len(raw)==13249 and digest(raw)==TEST67_SHA256, 'test67-original-bytes')


def transition(rows,before_tree,after_tree,before,after,policy,*,final):
    test67_bytes(after(TEST67))
    allowed=ALLOWED | {DRIVE_INDEX,DECISION_LOG}
    for status,path in rows:
        require(status in ('A','M'), 'transition-operation:'+path)
        require(path in allowed, 'transition-path:'+path)
        require(path in after_tree, 'transition-missing:'+path)
        require(after_tree[path]['mode']==before_tree.get(path,{'mode':'100644'})['mode'] and
                after_tree[path]['mode'] in ('100644','100755'), 'transition-mode:'+path)
        # 21内でも専用の本文/67制約を上書きしない。
        if path==TEST67:test67_bytes(after(path))
    record=documents(before,after,policy,final=final)
    if not final:
        for _,path in rows:
            if path in (DRIVE_INDEX,DECISION_LOG):
                require(policy is not None, 'document-approval-missing:'+path)
                require(digest(after(path))==policy[DOCUMENT_HASH_KEYS[path]], 'document-approved-hash:'+path)
                if path==DECISION_LOG:
                    old_log,new_log=before(path),after(path)
                    require(new_log.startswith(old_log), 'decision-original-bytes')
                    addition=new_log[len(old_log):]
                    require(old_log.endswith(b'\n') and addition.endswith(b'\n') and
                            addition.count(b'\n')==1 and b'\r' not in addition,'decision-one-line')
    return record


def scope(root,source,*,fixed=None):
    """最新67の候補変更を最新HEAD相対で検査。066登録→最新mainの範囲検査ではない。"""
    if fixed is not None:return legacy_scope(root,source,fixed=fixed)
    base=git(root,'rev-parse','HEAD').decode().strip()
    return candidate_scope(root,base,source)


def candidate_scope(root,base,source):
    old.sha(base);old.sha(source)
    before=tree(root,base);after=tree(root,source);rows=old.changes(root,base,source)
    reader=lambda rev,path:git(root,'show',rev+':'+path)
    transition(rows,before,after,lambda p:reader(base,p),lambda p:reader(source,p),None,final=False)
    return rows


def completed_contract(root,policy):
    """登録範囲/承認文書は完成SHAのみ。後続PRのHEADをこの関数へ代入しない。"""
    p=policy_value(policy);base=p['baseline_sha'];code=p['code_sha'];end=p['completion_sha']
    require(git(root,'rev-parse',base+'^{tree}').decode().strip()==p['baseline_tree'], 'baseline-tree')
    for ancestor,child in ((REGISTER,base),(base,code),(code,end)):
        require(subprocess.run(['git','merge-base','--is-ancestor',ancestor,child],cwd=root,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode==0,'generation-ancestry')
    legacy_scope(root,base,fixed=base)
    registered=git(root,'show',REGISTER+':'+TASK);baseline=git(root,'show',base+':'+TASK)
    require(status_parts(registered)[1]==status_parts(baseline)[1], 'baseline-task-body')
    for status,path in old.changes(root,base,code):
        require(status=='M' and path in IMPLEMENTATION, 'code-stage-only:'+path)
    for status,path in old.changes(root,code,end):
        require(status in ('A','M') and path not in set(CODE)|{WORKFLOW}, 'completed-code-changed:'+path)
    require(git(root,'show',end+':'+EVIDENCE+'code-fixed-sha.txt').decode().strip()==code, 'completed-code-pin')
    rows=old.changes(root,base,end)
    record=transition(rows,tree(root,base),tree(root,end),lambda q:git(root,'show',base+':'+q),
                      lambda q:git(root,'show',end+':'+q),p,final=True)
    return dict(schema=2,baseline_sha=base,code_sha=code,completion_sha=end,baseline_tree=p['baseline_tree'],
                approval=p,status=record,changes=rows,scope='固定066完成SHAのみ。最新mainの変更集合を制限しない。')


def latest_contract(root,policy):
    # 固定証拠と最新実体を取り違えず、最新HEADの原67と実入力を検査する。
    p=policy_value(policy);head=git(root,'rev-parse','HEAD').decode().strip()
    test67_bytes(raw_file(root/TEST67,root)[0])
    require((root/TEST67).read_bytes()==git(root,'show',head+':'+TEST67), 'test67-dirty')
    require(not git(root,'status','--porcelain','--untracked-files=all'),'事前dirty')
    check_map(root)
    return dict(source_sha=head,completed=completed_contract(root,p),test67_sha256=TEST67_SHA256,
                latest_scope='実入力/動作の継続検査。登録→最新HEADの066範囲検査は行わない。')


# 最初の行頭##を固定入力で検査する。期待する受入は状態行の前後関係から指定。
STATUS_BOUNDARY_CASES=tuple(
    (f'boundary-{label}-state-{position}-later-space-{later}',marker,eol,position,later)
    for label,marker,eol in (('space-lf',b'## heading',b'\n'),('bare-lf',b'##',b'\n'),
                            ('tab-lf',b'##\theading',b'\n'),('bare-crlf',b'##',b'\r\n'),
                            ('tab-crlf',b'##\theading',b'\r\n'))
    for position in ('before','after') for later in (False,True))

GENERATION_CASES=(
    'approved-document-control','state-only-control','implementation-control','evidence-control','latest-head-control',
    'approval-missing','approval-key-missing','approval-sha-short','approval-sha-one-character',
    'approval-drive-one-character','approval-decision-one-character',
    'status-missing','status-double','status-fake-body','status-body-only','status-not-line-start',
    'status-body-byte-change','task-outside-evidence','task-prefix-change','task-suffix-change',
    'decision-history-change','decision-history-delete','decision-two-lines','decision-approved-hash',
    'drive-approved-hash','extra-file','old-code','old-evidence','test67-change','test67-mode','document-mode',
    'document-delete','document-rename','document-symlink','missing-drive','missing-decision','unapproved-decision',
    'unapproved-drive','candidate-outside-reason','candidate-body-reason','candidate-old-code-reason','candidate-old-evidence-reason')+tuple(r[0] for r in STATUS_BOUNDARY_CASES)


def generation_self_test(output):
    """新世代の独立正負。実承認値の代用品にしない。原67ファイルは書き換えない。"""
    import copy
    import contextlib
    import io
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    baseline={TASK:b'# fixture\n'+ '状態：登録\n'.encode()+b'## body\nkeep\n## evidence\n'+EVIDENCE_LINE+b' fixture\nsuffix\n',
              DECISION_LOG:b'# log\n| old | original |\n',TEST67:(ROOT/TEST67).read_bytes(),
              CODE[0]:b'original implementation',EVIDENCE+'local-results.json':b'original evidence'}
    target=dict(baseline);target[TASK]=baseline[TASK].replace(b' fixture\nsuffix',b' approved evidence\nsuffix')
    target[DECISION_LOG]=baseline[DECISION_LOG]+b'| approved | one line |\n';target[DRIVE_INDEX]=b'{"fixture":true}\n'
    policy=dict(baseline_sha='1'*40,baseline_tree='2'*40,code_sha='3'*40,completion_sha='4'*40,
                task_body_sha256=digest(status_parts(target[TASK])[1]),drive_index_sha256=digest(target[DRIVE_INDEX]),
                decision_log_sha256=digest(target[DECISION_LOG]))
    rows=[]
    for case in GENERATION_CASES:
        area=output/case;area.mkdir();before=dict(baseline);after=dict(target);p=copy.deepcopy(policy)
        boundary=next((r for r in STATUS_BOUNDARY_CASES if r[0]==case),None)
        if boundary is not None:
            _,marker,eol,position,later=boundary
            state='状態：fixture'.encode()+eol
            raw=b'# fixture'+eol+(state+marker+eol if position=='before' else marker+eol+state)
            if later:raw+=b'## later'+eol
            (area/'input.bin').write_bytes(raw)
            accepted=position=='before';expected=None if accepted else 'status-metadata-position';error=None
            try:
                line,body=status_parts(raw)
                require(line==state and body==raw.replace(state,b'',1),'status-boundary-raw-remainder')
            except Exception as exc:error=type(exc).__name__+': '+str(exc)
            ok=error is None if accepted else error=='ValueError: '+expected
            (area/'raw.log').write_text((error or 'ACCEPT: 状態行以外の原bytes保持')+'\n')
            row=dict(case=case,status='PASS' if ok else 'FAIL',expected='accept' if accepted else 'reject',expected_reason=expected,error=error)
            write_new(area/'result.json',row);rows.append(row)
            continue
        final=True;expected=None;error=None;accepted=case.endswith('-control');stream=io.StringIO()
        changes=None;modes={};operation={}
        try:
            with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
                if case=='state-only-control':after=dict(before);after[TASK]=before[TASK].replace('状態：登録'.encode(),'状態：検証中'.encode());final=False
                if case=='implementation-control':after[CODE[0]]=b'new implementation'
                if case=='evidence-control':after[EVIDENCE+'local-results.json']=b'new evidence'
                if case=='latest-head-control':
                    # 実最新HEADの受入正例。登録→HEADの範囲制約を使わない。
                    source=git(ROOT,'rev-parse','HEAD').decode().strip();scope(ROOT,source)
                if case.startswith('approval-'):
                    if case=='approval-missing':expected='generation-approval-missing';policy_value(None)
                    if case=='approval-key-missing':p.pop('drive_index_sha256');expected='generation-approval-keys'
                    if case=='approval-sha-short':p['code_sha']='abc';expected='完全SHA必須'
                    if case=='approval-sha-one-character':p['task_body_sha256']=('0' if p['task_body_sha256'][0]!='0' else '1')+p['task_body_sha256'][1:];expected='task-approved-hash'
                    if case in ('approval-drive-one-character','approval-decision-one-character'):
                        key='drive_index_sha256' if case=='approval-drive-one-character' else 'decision_log_sha256'
                        p[key]=('0' if p[key][0]!='0' else '1')+p[key][1:]
                        expected='drive-approved-hash' if case=='approval-drive-one-character' else 'decision-approved-hash'
                if case=='status-missing':after[TASK]=b''.join(after[TASK].splitlines(keepends=True)[0:1]+after[TASK].splitlines(keepends=True)[2:]);expected='status-count'
                if case=='status-double':after[TASK]=after[TASK].replace(b'## body\n','状態：重複\n'.encode()+b'## body\n');expected='status-count'
                if case=='status-fake-body':after[TASK]+='状態：偽\n'.encode();expected='status-count'
                if case=='status-body-only':
                    line,body=status_parts(after[TASK]);after[TASK]=body+line;expected='status-metadata-position'
                if case=='status-not-line-start':after[TASK]=after[TASK].replace('状態：'.encode(),' 状態：'.encode());expected='status-count'
                if case in ('status-body-byte-change','task-outside-evidence'):after[TASK]=after[TASK].replace(b'keep',b'changed');expected='task-outside-evidence'
                if case=='task-prefix-change':after[TASK]=after[TASK].replace(b'# fixture',b'# changed');expected='task-outside-evidence'
                if case=='task-suffix-change':after[TASK]=after[TASK].replace(b'suffix',b'changed');expected='task-outside-evidence'
                if case=='decision-history-change':after[DECISION_LOG]=after[DECISION_LOG].replace(b'original',b'changed');expected='decision-original-bytes'
                if case=='decision-history-delete':after[DECISION_LOG]=b'# log\n| approved | one line |\n';expected='decision-original-bytes'
                if case=='decision-two-lines':after[DECISION_LOG]+=b'| extra | line |\n';expected='decision-one-line'
                if case=='decision-approved-hash':after[DECISION_LOG]=before[DECISION_LOG]+b'| unapproved | one line |\n';expected='decision-approved-hash'
                if case=='drive-approved-hash':after[DRIVE_INDEX]+=b' ';expected='drive-approved-hash'
                if case in ('extra-file','old-code','old-evidence'):
                    path={'extra-file':'outside066.txt','old-code':old.CODE[0],'old-evidence':old.EVIDENCE+'README.md'}[case]
                    after[path]=b'unapproved';expected='transition-path:'+path
                if case=='test67-change':after[TEST67]+=b'\n';expected='test67-original-bytes'
                if case in ('test67-mode','document-mode','document-symlink'):
                    path=TEST67 if case=='test67-mode' else TASK;modes[path]='120000' if case=='document-symlink' else '100755';expected='transition-mode:'+path
                if case in ('document-delete','document-rename'):operation[TASK]='D' if case=='document-delete' else 'R100';expected='transition-operation:'+TASK
                if case in ('missing-drive','missing-decision'):
                    after.pop(DRIVE_INDEX if case=='missing-drive' else DECISION_LOG);expected='missing-document'
                    if case=='missing-decision':operation[DECISION_LOG]='D';expected='transition-operation:'+DECISION_LOG
                if case in ('unapproved-decision','unapproved-drive'):
                    path=DECISION_LOG if case=='unapproved-decision' else DRIVE_INDEX;after=dict(before);after[path]=target[path];p=None;final=False;expected='document-approval-missing:'+path
                if case.startswith('candidate-'):
                    from test_generation_contract import commit_variant
                    path={'candidate-outside-reason':'outside066.txt','candidate-body-reason':TASK,
                          'candidate-old-code-reason':old.CODE[0],'candidate-old-evidence-reason':old.EVIDENCE+'README.md'}[case]
                    source=git(ROOT,'rev-parse','HEAD').decode().strip();variant=commit_variant(ROOT,source,area,path,b'changed fixture\n')
                    expected='status-count' if path==TASK else 'transition-path:'+path
                    scope(ROOT,variant)
                if p is not None:policy_value(p)
                bt={q:{'mode':'100644','blob':blob_id(v)} for q,v in before.items()}
                at={q:{'mode':modes.get(q,'100644'),'blob':blob_id(v)} for q,v in after.items()}
                changes=[(operation.get(q,'M' if q in bt else 'A'),q) for q in sorted(set(bt)|set(at)) if bt.get(q)!=at.get(q) or q in operation]
                def read(values,q):
                    require(q in values,'missing-document');return values[q]
                observation=transition(changes,bt,at,lambda q:read(before,q),lambda q:read(after,q),p,final=final)
                if case=='state-only-control':require(observation['changed'],'state-record')
        except Exception as exc:error=type(exc).__name__+': '+str(exc)
        ok=error is None if accepted else error=='ValueError: '+str(expected)
        (area/'raw.log').write_text(stream.getvalue());write_new(area/'result.json',dict(case=case,expected_reason=expected,error=error,status='PASS' if ok else 'FAIL'))
        rows.append(dict(case=case,status='PASS' if ok else 'FAIL',expected='accept' if accepted else 'reject',expected_reason=expected,error=error))
    result=dict(schema=2,fixture_only=True,real_approval_used=False,status='PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL',cases=rows)
    write_new(output/'tests.json',result);print('GENERATION2_TESTS '+json.dumps(result,ensure_ascii=False),flush=True)
    return int(result['status']!='PASS')


def fixed_generation_state(root,sha):
    require(git(root,'rev-parse','HEAD').decode().strip()==sha,'fixed-generation-head')
    require(not git(root,'status','--porcelain','--untracked-files=all'),'fixed-generation-dirty')
    files={}
    for path in (*CODE,*old.CODE,WORKFLOW):
        raw,mode=raw_file(root/path,root)
        require(raw==git(root,'show',sha+':'+path),'fixed-generation-bytes:'+path)
        files[path]=dict(bytes=len(raw),sha256=digest(raw),mode=mode)
    test67_bytes((root/TEST67).read_bytes())
    return dict(sha=sha,tree=git(root,'rev-parse',sha+'^{tree}').decode().strip(),files=files)


def generation_objects(root,policy):
    """scopeの独立再検証に必要なcommit/treeと制約対象blobの原bytes。"""
    import base64
    p=policy_value(policy);objects={}
    def take(kind,oid):
        if oid in objects:return
        raw=git(root,'cat-file',kind,oid)
        require(hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,'generation-object-hash')
        objects[oid]=dict(kind=kind,bytes=len(raw),data_base64=base64.b64encode(raw).decode())
        if kind=='tree':
            for mode,name,child in old.tree_entries(raw):
                if mode=='40000':take('tree',child)
    commits=set(git(root,'rev-list',p['completion_sha'],'^'+REGISTER).decode().split())|{REGISTER,p['baseline_sha'],p['code_sha'],p['completion_sha']}
    for sha in sorted(commits):
        take('commit',sha);take('tree',git(root,'rev-parse',sha+'^{tree}').decode().strip())
    for sha in (REGISTER,p['baseline_sha'],p['code_sha'],p['completion_sha']):
        entries=tree(root,sha)
        metadata=tuple(q for q in entries if Path(q).name in ('.gitattributes','.gitmodules'))
        for path in (TASK,DECISION_LOG,DRIVE_INDEX,*CODE,*old.CODE,WORKFLOW,EVIDENCE+'code-fixed-sha.txt',*metadata):
            if path in entries:take('blob',entries[path]['blob'])
    return dict(schema=1,registration=REGISTER,approval=p,objects=objects)


def replay_generation(bundle,expected):
    import base64
    import tempfile
    require(bundle.get('schema')==1 and bundle.get('registration')==REGISTER and
            bundle.get('approval')==expected,'generation-object-identity')
    with tempfile.TemporaryDirectory(prefix='native066-generation-') as folder:
        root=Path(folder);subprocess.run(['git','init','-q',str(root)],check=True)
        for oid,row in sorted(bundle['objects'].items(),key=lambda item:({'blob':0,'tree':1,'commit':2}.get(item[1].get('kind'),3),item[0])):
            old.sha(oid);require(row['kind'] in ('commit','tree','blob'),'generation-object-kind')
            raw=base64.b64decode(row['data_base64'],validate=True)
            require(len(raw)==row['bytes'] and hashlib.sha1(row['kind'].encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,'generation-object-hash')
            actual=subprocess.check_output(['git','hash-object','-w','-t',row['kind'],'--stdin'],cwd=root,input=raw).decode().strip()
            require(actual==oid,'generation-object-write')
        (root/'.git/shallow').write_text(REGISTER+'\n')
        return completed_contract(root,expected)


def prepare_generations(output):
    p=generation_policy();out=Path(output);parent=out.parent.parent
    states={}
    for label,sha in (('qa066-baseline',p['baseline_sha']),('qa066-completed',p['completion_sha'])):
        root=parent/label
        require(not root.exists(),'fixed-generation-already-exists')
        subprocess.run(['git','worktree','add','--detach',str(root),sha],cwd=ROOT,check=True)
        states[label]=fixed_generation_state(root,sha)
    require(states['qa066-baseline']['tree']==p['baseline_tree'],'baseline-tree')
    write_new(out/'fixed066.json',dict(approval=p,states=states))
    print('FIXED066_READY '+json.dumps(states,sort_keys=True),flush=True)


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
    context=area/'generation-context.json'
    value['generation_context_sha256']=digest(context.read_bytes()) if context.exists() else None
    if index:require(value['generation_context_sha256']==previous.get('generation_context_sha256'),'generation-context-changed')
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
    if value.get('generation_context_sha256') is not None:
        raw,_=raw_file(area/'generation-context.json',area)
        require(digest(raw)==value['generation_context_sha256'],'generation-context-bytes')
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
            require(value.get('generation_context_sha256')==values[0].get('generation_context_sha256'),'generation-context-chain')
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
        context=latest_contract(ROOT,generation_policy())
        write_new(area/'generation-context.json',context)
        print('GENERATION2_RECEIPT '+digest((area/'generation-context.json').read_bytes()),flush=True)
    capture(ROOT,area,args.stage,ident)
    if STAGES.index(args.stage)>=3:validate_build(area,Path(args.output).resolve(),ident)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stage',choices=STAGES);mode.add_argument('--generation-tests',action='store_true')
    mode.add_argument('--prepare-generations',action='store_true');mode.add_argument('--completed-contract',action='store_true')
    p.add_argument('--checkout');p.add_argument('--platform',choices=('linux','windows'));p.add_argument('--phase',choices=('transaction','primitives'))
    p.add_argument('--profile',default='latest');p.add_argument('--run-id',default='local-066')
    try:
        args=p.parse_args()
        if args.generation_tests:sys.exit(generation_self_test(args.output))
        elif args.prepare_generations:prepare_generations(args.output)
        elif args.completed_contract:
            root=Path(args.checkout).resolve();policy=generation_policy()
            state=fixed_generation_state(root,policy['completion_sha'])
            result=completed_contract(root,policy);bundle=generation_objects(root,policy)
            require(replay_generation(bundle,policy)==result,'generation-independent-replay')
            write_new(Path(args.output),dict(contract=result,objects=bundle,checkout=state))
            print('COMPLETED066_PASS '+policy['completion_sha'],flush=True)
        else:
            require(args.platform and args.phase,'OS/phase必須');main(args)
    except Exception as exc:print('NATIVE_BUILD_V1_FAIL: '+type(exc).__name__+': '+str(exc),flush=True);sys.exit(1)
