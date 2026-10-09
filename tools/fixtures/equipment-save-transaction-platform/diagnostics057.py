#!/usr/bin/env python3
"""同じ専用CIの同一sourceで6seedの対照と内訳を実測。全取引受入と別にする。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
from process_capture import run_command, save
ROOT=Path(__file__).resolve().parents[3]
BAD=re.compile(rb'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|Fontconfig error|_FAIL:')
SEEDS={'typed':dict(typed=True,trial=True,history='normal'),'plain':{},
       'granted':dict(typed=True,trial=True,history='normal',unlocked=True),
       'trial-missing':dict(typed=True,trial=True,history='missing'),
       'trial-corrupt':dict(typed=True,trial=True,history='corrupt'),
       'trial-unclean':dict(typed=True,trial=True,history='unclean')}


def body(source,name):
    match=re.search(r'^func '+name+r'\(.*?(?=^func |\Z)',source,re.M|re.S)
    return match.group(0).strip().split('\n')[1:]


def instrumentation_contract():
    original=body((ROOT/'scripts/game/equipment_save_transaction.gd').read_text(),'plan')
    measured='\n'.join(body((Path(__file__).parent/'diagnostic_transaction.gd').read_text(),'_plan_observed'))
    replacements={'timed_decode(raw)':'Codec.decode_source(raw,context)',
                  'timed_migration(decoded.document,decoded.source_sha256)':'Migration.new().plan(decoded.document,decoded.source_sha256,context)',
                  'timed_prepare(migrated.candidate_document)':'Validation.prepare_candidate(migrated.candidate_document,context)',
                  'timed_encode(prepared.document)':'Codec.encode_candidate(prepared.document,context)'}
    for observed,actual in replacements.items():measured=measured.replace(observed,actual)
    if '\n'.join(original)!=measured:raise ValueError('plan観測bodyが本番と不一致')
    return {'plan_body_equal_except_forwarding':True,'production_sha256':hashlib.sha256((ROOT/'scripts/game/equipment_save_transaction.gd').read_bytes()).hexdigest(),'plan_functions':replacements}


def union(intervals):
    total=0;end=-1
    for a,b in sorted(intervals):
        total+=max(0,b-max(a,end));end=max(end,b)
    return total


def summarize(value):
    spans=value['spans'];native=value['native_spans'];labels={}
    for index,span in enumerate(spans):
        label=span['label'];inclusive=span['end_us']-span['start_us']
        children=[(s['start_us'],s['end_us']) for s in spans if s['parent']==index]
        row=labels.setdefault(label,dict(count=0,inclusive_us=0,exclusive_us=0))
        row['count']+=1;row['inclusive_us']+=inclusive;row['exclusive_us']+=inclusive-union(children)
    for span in native:
        row=labels.setdefault(span['label'],dict(count=0,inclusive_us=0,exclusive_us=0));row['count']+=1;row['inclusive_us']+=span['end_us']-span['start_us'];row['exclusive_us']=row['inclusive_us']
    plan_verify=[(s['start_us'],s['end_us']) for s in spans if s['label'] in ['plan','verify_candidate']]
    return dict(labels=labels,plan_verify_union_us=union(plan_verify),native_union_us=union([(s['start_us'],s['end_us']) for s in native]),transaction_wall_us=value['transaction_end_us']-value['transaction_start_us'],units='microseconds; child-relative ticks',inclusive_exclusive='exclusive removes immediate nested spans; native is a separate overlapping observation, never add to plan/verify')


def environment(output):
    info=dict(os=platform.platform(),cpu=platform.processor(),cpu_count=os.cpu_count(),python=sys.version,
              fs_device=output.stat().st_dev,worker_count=2 if os.name=='nt' else 4,case_workers=8 if os.name=='nt' else 16,max_batch_roots=4)
    if os.name=='nt':
        p=subprocess.run(['powershell','-NoProfile','-Command','Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json; Get-Volume | Select-Object DriveLetter,FileSystemType | ConvertTo-Json'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        info['cpu_fs_command']=p.stdout.decode(errors='replace');info['cpu_fs_exit']=p.returncode
    else:
        info['cpu_details']=[line for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')][:1]
        info['fs']=subprocess.check_output(['stat','-f','-c','%T',str(output)],text=True).strip()
        for path in ['/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/memory.max']:
            if Path(path).exists():info[path]=Path(path).read_text().strip()
    return info


def main(args):
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False)
    global_start=time.monotonic();rows=[];failures=[]
    report=dict(status='RUNNING',acceptance='diagnostic sample only; not 172/2178/97kill',source_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),environment=environment(output),instrumentation=instrumentation_contract(),commands=rows,samples=[],failures=failures)
    env=os.environ.copy()
    for key in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME','APPDATA','LOCALAPPDATA']:
        p=output/'profile'/key;p.mkdir(parents=True);env[key]=str(p)
    def command(label,argv):
        remaining=global_start+174-time.monotonic()
        if remaining<=0:raise TimeoutError('診断174秒締切')
        try:
            run_command(argv,output/(label+'.log'),output/(label+'-process.json'),cwd=ROOT,env=env,budget=min(30,remaining),timeout_kind='diagnostic_child_30_seconds' if remaining>=30 else 'diagnostic_inner_174_seconds')
        finally:
            row=json.loads((output/(label+'-process.json')).read_bytes())
            row['label']=label;rows.append(row);save(output/'diagnostics.json',report)
        if row['exit_code']!=0 or BAD.search((output/(label+'.log')).read_bytes()):raise ValueError('診断実exit/警告:'+label)
        return row
    try:
        report['godot_version']=command('version',[args.godot,'--version'])
        for name,options in SEEDS.items():
            seed=output/('seed-'+name);seed.mkdir();config=seed/'config.json';save(config,dict(root=str(seed),operation='fixture',result='fixture.json',**options))
            command('seed-'+name,[args.godot,'--headless','--path',str(ROOT),'--script','res://tools/equipment_save_transaction_probe.gd','--',str(config)])
            values={}
            for mode in ['off','on']:
                root=output/(name+'-'+mode);shutil.copytree(seed,root)
                execution=command(name+'-'+mode,[args.godot,'--headless','--path',str(ROOT),'--script','res://tools/fixtures/equipment-save-transaction-platform/diagnostic_sample.gd','--',str(root),mode])
                value=json.loads((root/'timing-result.json').read_bytes());values[mode]=value
                if value['quantity']!=(22 if name=='granted' else 12) or not value['memory_unchanged']:raise ValueError('診断固定数量/メモリ:'+name)
                report['samples'].append(dict(seed=name,mode=mode,execution_seconds=execution['seconds'],timing=summarize(value),raw=value))
            for key in ['source_sha256','output_sha256','quantity','memory_unchanged']:
                if values['off'][key]!=values['on'][key]:raise ValueError('計測有無の対照不一致:'+name+':'+key)
        report['status']='PASS'
    except Exception as exc:
        report['status']='FAIL';failures.append(type(exc).__name__+': '+str(exc))
    finally:
        report['wall_seconds']=time.monotonic()-global_start;save(output/'diagnostics.json',report)
    print('DIAGNOSTICS057_'+report['status']+': samples='+str(len(report['samples']))+' source='+report['source_sha'])
    return 0 if report['status']=='PASS' else 1
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--godot',required=True);p.add_argument('--output',required=True);sys.exit(main(p.parse_args()))
