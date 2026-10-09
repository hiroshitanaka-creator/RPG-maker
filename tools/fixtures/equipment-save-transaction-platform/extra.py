#!/usr/bin/env python3
"""native排他/identity/不正pathとF2/F3を専用file/processだけで実測。"""
import argparse,concurrent.futures,hashlib,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BAD=re.compile(rb'SCRIPT ERROR|ERROR:|WARNING:|Parse Error|Fontconfig error|_FAIL:')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
class Suite:
    def __init__(self,args):
        self.godot=str(Path(args.godot).resolve());self.output=Path(args.output).resolve();self.output.mkdir(parents=True,exist_ok=False);self.rows=[];self.legacy=args.legacy_checkout;self.start=time.monotonic();self.deadline=self.start+174
        self.env=os.environ.copy()
        for key in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME','APPDATA','LOCALAPPDATA']:
            p=self.output/'profile'/key;p.mkdir(parents=True);self.env[key]=str(p)
    def new(self,name):
        p=self.output/name;p.mkdir();return p
    def run(self,root,operation,script='native_probe.gd',label='result',hold=None,env=None,checkout=None,**values):
        config={'root':str(root),'operation':operation,'result':label+'.json',**values};request=root/(label+'-config.json');write(request,config)
        probe='res://tools/fixtures/equipment-save-transaction-platform/'+script
        if script=='worker':probe='res://tools/equipment_save_transaction_probe.gd'
        argv=[self.godot,'--headless','--path',str(checkout or ROOT),'--script',probe,'--',str(request)]
        start=time.monotonic();limit=min(30,self.deadline-start);assert limit>0
        log=root/(label+'.log')
        with log.open('wb') as stream:
            child=subprocess.Popen(argv,env=env or self.env,stdout=stream,stderr=subprocess.STDOUT)
            if hold is None:child.wait(timeout=limit)
            else:
                marker=root/'paused.json'
                while not marker.exists():
                    assert child.poll() is None,'境界前終了:'+log.read_text()
                    assert time.monotonic()-start<limit,'子30秒';time.sleep(.005)
                hit=load(marker);assert hit['pid']==child.pid and hit['point']==values['kill_point']
                hold(child)
                if child.poll() is None:(root/'release').write_bytes(b'continue')
                child.wait(timeout=max(.001,limit-(time.monotonic()-start)))
        raw=log.read_bytes();assert not BAD.search(raw),raw.decode(errors='replace')
        result=load(root/(label+'.json')) if (root/(label+'.json')).exists() else {}
        record={'argv':argv,'seconds':time.monotonic()-start,'budget_seconds':30,'exit_code':child.returncode,'log_sha256':digest(raw),'result':result}
        write(root/(label+'-execution.json'),record);return record
    def check(self,name,ok,evidence):
        assert ok,name;self.rows.append({'case':name,'checks_passed':True,'evidence':evidence})
    def dependency(self,name):
        root=self.new('dependency-'+name);argv=[self.godot,'--headless','--path',str(ROOT),'--script','res://tools/fixtures/equipment-save-transaction-platform/dependencies.gd','--',str(root),name]
        start=time.monotonic();p=subprocess.run(argv,env=self.env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=min(30,self.deadline-start));(root/'raw.log').write_bytes(p.stdout)
        value=load(root/'dependency-result.json');expected_positive=name in ['control','source_build']
        ok=p.returncode==0 and not BAD.search(p.stdout) and value['before'] and value['prepared'] and value['same_ok']==value['fresh_ok']==expected_positive and value['candidate_equal'] and value['same_reason']==value['fresh_reason'] and (value['commit'].get('committed') is True if name=='control' else value['commit']['ok'] is False)
        self.check('dependency-'+name,ok,{'result':value,'exit_code':p.returncode,'seconds':time.monotonic()-start,'log_sha256':digest(p.stdout)})
    def fixture(self,root,**options):return self.run(root,'fixture','worker',label='fixture',**options)['result']
    def main(self):
        for name in ['control','job_progression','jobs','abilities','source_build','session']:self.dependency(name)
        root=self.new('kernel-live-query-failure');self.fixture(root)
        if os.name!='nt':
            stub=self.output/'ps-stub';stub.mkdir();ps=stub/'ps';ps.write_text('#!/bin/sh\nexit 2\n');ps.chmod(0o700);fault_env=dict(self.env,PATH=str(stub)+os.pathsep+self.env['PATH'])
        else:fault_env=dict(self.env,PATH='Z:\\055-unavailable-tools')
        held={}
        def contender(child):
            other=self.run(root,'full','worker',label='contender',env=fault_env);held['value']=other;held['owner_alive']=child.poll() is None
        owner=self.run(root,'full','worker',label='owner',kill_point='lease.acquire.after',hold=contender)
        self.check('kernel-live-query-failure',held['owner_alive'] and held['value']['result'].get('reason_code')=='busy' and owner['result'].get('phase')=='committed',{'owner':owner,'contender':held})
        root=self.new('kernel-kill-release');self.fixture(root)
        terminated=self.run(root,'full','worker',label='terminated',kill_point='kernel.lock.after',hold=lambda p:p.kill())
        recovered=self.run(root,'full','worker',label='recovered')
        self.check('kernel-kill-release',terminated['exit_code']==(1 if os.name=='nt' else -9) and recovered['result'].get('phase')=='committed',{'terminated':terminated,'recovered':recovered})
        root=self.new('pid-reuse-metadata');self.fixture(root);first=self.run(root,'prepare','worker',label='first');tx=root/'transactions'/first['result']['token'];lease=sorted((tx/'leases').glob('lease-*'))[-1];value=load(lease);value['pid']=os.getpid();write(lease,value)
        second=self.run(root,'commit','worker',label='second',token=first['result']['token']);self.check('pid-reuse-metadata',second['result'].get('phase')=='committed',second)
        root=self.new('simultaneous-first-lock');tx=root/'transactions/native-probe';tx.mkdir(parents=True)
        def launch(label):
            request=root/(label+'-config.json');write(request,{'root':str(root),'operation':'lock','kill_point':'native.lock.after','result':label+'.json'})
            stream=(root/(label+'.log')).open('wb');return subprocess.Popen([self.godot,'--headless','--path',str(ROOT),'--script','res://tools/fixtures/equipment-save-transaction-platform/native_probe.gd','--',str(request)],env=self.env,stdout=stream,stderr=subprocess.STDOUT),stream
        a,sa=launch('a');b,sb=launch('b');deadline=time.monotonic()+30
        while not (root/'paused.json').exists():assert time.monotonic()<deadline;time.sleep(.005)
        winner=load(root/'paused.json')['pid'];loser=b if winner==a.pid else a;loser.wait(timeout=30);(root/'release').write_bytes(b'continue');a.wait(timeout=30);b.wait(timeout=30);sa.close();sb.close()
        values=[load(root/'a.json'),load(root/'b.json')];self.check('simultaneous-first-lock',sorted(v['ok'] for v in values)==[False,True] and all(p.returncode==0 for p in [a,b]) and all(not BAD.search((root/(l+'.log')).read_bytes()) for l in ['a','b']),values)
        root=self.new('native-primitives');tx=root/'transactions/native-probe';tx.mkdir(parents=True);sentinel=b'preexisting bytes';existing=tx/'existing.bin';existing.write_bytes(sentinel)
        value=self.run(root,'exclusive',path=str(existing));self.check('exclusive-no-truncate',not value['result']['ok'] and existing.read_bytes()==sentinel,value)
        value=self.run(root,'same_file_rename',label='same-file',path=str(existing),to=str(existing).swapcase() if os.name=='nt' else str(existing))
        self.check('same-file-rename-denied',not value['result']['ok'] and existing.read_bytes()==sentinel,value)
        value=self.run(root,'replace',label='replace-final',path=str(existing));self.check('replace-final-denied',not value['result']['ok'] and existing.read_bytes()==sentinel,value)
        tmp=tx/'owned.tmp';value=self.run(root,'replace',label='tmp-new',path=str(tmp));before=tmp.read_bytes();value=self.run(root,'replace',label='tmp-reuse',path=str(tmp),bytes='retry owned tmp');self.check('owned-tmp-reuse',value['result']['ok'] and before==b'native exact bytes' and tmp.read_bytes()==b'retry owned tmp',value)
        link=tx/'hard.tmp';os.link(existing,link);value=self.run(root,'replace',label='hardlink',path=str(link));self.check('hardlink-reuse-denied',not value['result']['ok'] and existing.read_bytes()==sentinel,value)
        value=self.run(root,'rename',label='collision',path=str(tx/'collision.tmp'),to=str(existing));self.check('rename-no-clobber',not value['result']['ok'] and existing.read_bytes()==sentinel and (tx/'collision.tmp').read_bytes()==b'native exact bytes',value)
        value=self.run(root,'rename',label='receipt-contract',path=str(tx/'misnamed.tmp'),to=str(existing),receipt_replace=True);self.check('receipt-replace-is-separate',not value['result']['ok'] and existing.read_bytes()==sentinel,value)
        value=self.run(root,'unowned_write',label='unowned',path=str(root/'outside-tx.tmp'));self.check('unowned-write-denied',value['result'].get('reason_code')=='busy' and not (root/'outside-tx.tmp').exists(),value)
        source=root/'source.json';source.write_bytes(b'original identity')
        def swap(child):
            other=root/'other.json';other.write_bytes(source.read_bytes());source.rename(root/'source-preserved.json');other.rename(source)
        value=self.run(root,'swap',label='file-swap',path=str(source),kill_point='native.swap.after',hold=swap);self.check('file-swap-same-bytes-denied',not value['result']['ok'] and source.read_bytes()==(root/'source-preserved.json').read_bytes(),value)
        if os.name=='nt':
            def swap_alias(child):
                other=root/'other-alias.json';other.write_bytes(source.read_bytes());source.rename(root/'source-alias-preserved.json');other.rename(source)
            value=self.run(root,'swap',label='file-swap-alias',path=str(source),reopen_path=str(source).swapcase(),kill_point='native.swap.after',hold=swap_alias)
            self.check('file-swap-case-alias-denied',not value['result']['ok'] and source.read_bytes()==(root/'source-alias-preserved.json').read_bytes(),value)
        paths={'root-prefix':str(root)+'-outside/file','parent':str(root/'../escape'),'dot':str(root)+'/./file','nonascii-space':str(root/'保存 領域'/'file.tmp')}
        if os.name=='nt':paths.update({'drive-relative':'C:save.json','unc':'//server/share/save.json','ads':str(root/'save.json:stream'),'reserved':str(root/'CON.txt'),'dot-suffix':str(root/'file.'),'space-suffix':str(root/'file '),'case-alias':str(root).swapcase()+'/file.tmp','long-path':str(root)+'/'+('/'.join(['long_component'*3]*8))+'/file.tmp','other-drive':'Z:/055/save.json'})
        else:paths.update({'long-path':str(root)+'/'+('/'.join(['long_component'*3]*8))+'/file.tmp'})
        for name,path in paths.items():
            value=self.run(root,'path',label='path-'+name,path=path);self.check('path-'+name,value['result']['ok']==(name in ['nonascii-space','case-alias','long-path']),value)
        for name,part in [('nonascii-space','保存 領域/file.tmp'),('long-path','/'.join(['long_component'*3]*8)+'/file.tmp')]:
            path=str(tx/part);value=self.run(root,'roundtrip',label='io-'+name,path=path)
            self.check('io-'+name,value['result']['ok'] and (Path(path+'.done')).read_bytes()=='保存 native exact bytes'.encode(),value)
        value=self.run(root,'process',label='query-unknown',pid=0);self.check('query-unknown-is-not-dead',value['result']['state']==-1,value)
        if os.name=='nt':
            path=str(tx/'case.tmp').swapcase();value=self.run(root,'roundtrip',label='io-case',path=path);self.check('io-case-alias',value['result']['ok'] and Path(path+'.done').read_bytes()=='保存 native exact bytes'.encode(),value)
            outside=self.new('junction-destination');junction=root/'junction'
            p=subprocess.run(['cmd','/c','mklink','/J',str(junction),str(outside)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);(root/'junction-command.log').write_bytes(p.stdout);assert p.returncode==0,'専用QA junction作成失敗'
            value=self.run(root,'path',label='junction',path=str(junction/'file.tmp'));self.check('junction-denied',not value['result']['ok'] and not (outside/'file.tmp').exists(),value)
        root=self.new('transaction-source-alias');seed=self.fixture(root);nested=root/'transactions/other/source.json';nested.parent.mkdir(parents=True);nested.write_bytes((root/'source.json').read_bytes())
        source=str(nested).swapcase() if os.name=='nt' else str(nested)
        value=self.run(root,'prepare','worker',label='transaction-source',source=source);self.check('transaction-source-alias-denied',value['result'].get('reason_code')=='same_file' and not (root/'transactions'/seed['token']).exists(),value)
        root=self.new('inspect-recover-write-zero');seed=self.fixture(root,typed=True,trial=True,history='normal');done=self.run(root,'full','worker',label='done')
        def snapshot():
            return {p.relative_to(root).as_posix():(p.stat().st_size,p.stat().st_mtime_ns,digest(p.read_bytes())) for p in [root/'source.json',*list((root/'history').glob('*')),*list((root/'transactions').rglob('*'))] if p.is_file()}
        before=snapshot();self.run(root,'inspect','worker',label='inspect');self.run(root,'recover','worker',label='recover',token=done['result']['token']);self.check('inspect-recover-write-zero',before==snapshot(),{'before':before,'after':snapshot()})
        root=self.new('native-target-last-race');self.fixture(root);sentinel=b'last boundary sentinel';location={}
        def collide(child):
            tx=next((root/'transactions').iterdir());(tx/'converted.json').write_bytes(sentinel);location['file']=tx/'converted.json'
        value=self.run(root,'full','worker',label='last-race',kill_point='commit.native.rename.before',hold=collide);self.check('target-last-race',not value['result']['ok'] and location['file'].read_bytes()==sentinel,value)
        if os.name!='nt':
            assert self.legacy,'旧053 checkout必須'
            root=self.new('legacy-dead-recovery');self.fixture(root,typed=True,trial=True,history='normal')
            before=self.run(root,'prepare','worker',label='old-prepared',checkout=self.legacy)
            token=before['result']['token'];tx=root/'transactions'/token
            old_files={p.relative_to(root).as_posix():p.read_bytes() for p in [root/'source.json',*list((root/'history').glob('*')),*list(tx.rglob('*'))] if p.is_file()}
            recovered=self.run(root,'commit','worker',label='native-commit',token=token)
            self.check('legacy-dead-recovery',recovered['result'].get('phase')=='committed' and recovered['result'].get('quantity')==12 and all((root/name).read_bytes()==raw for name,raw in old_files.items() if name.endswith(('source.json','source.bin','history.bin')) or '/leases/' in name),{'before':before,'after':recovered,'preserved':{name:digest(raw) for name,raw in old_files.items()}})
            root=self.new('legacy-live-owner');self.fixture(root)
            blocked={}
            def legacy_contender(child):
                blocked['native']=self.run(root,'full','worker',label='native-blocked');blocked['owner_alive']=child.poll() is None
            old_owner=self.run(root,'full','worker',label='old-owner',checkout=self.legacy,kill_point='lease.acquire.after',hold=legacy_contender)
            self.check('legacy-live-owner',blocked['owner_alive'] and blocked['native']['result'].get('reason_code')=='busy' and old_owner['result'].get('phase')=='committed',{'owner':old_owner,'native':blocked})
            root=self.new('legacy-after-native');self.fixture(root)
            prepared=self.run(root,'prepare','worker',label='native-prepared');tx=root/'transactions'/prepared['result']['token'];candidate=(tx/'converted.tmp').read_bytes()
            old=self.run(root,'commit','worker',label='old-blocked',checkout=self.legacy,token=prepared['result']['token'])
            self.check('legacy-after-native',old['result'].get('reason_code')=='recovery_required' and not (tx/'converted.json').exists() and (tx/'converted.tmp').read_bytes()==candidate,old)
        new_boundaries={'kernel.lock.before':'incomplete','kernel.lock.after':'incomplete','intent.native.rename.before':'incomplete','source.native.rename.before':'incomplete','history.native.rename.before':'incomplete','commit.native.rename.before':'prepared'}
        for point,phase in new_boundaries.items():
            root=self.new('boundary-'+point);seed=self.fixture(root,typed=True,trial=True,history='normal');raw=(root/'source.json').read_bytes();history={p.name:p.read_bytes() for p in (root/'history').glob('*')}
            stopped=self.run(root,'full','worker',label='stopped',kill_point=point,hold=lambda p:p.kill())
            resumed=self.run(root,'resume','worker',label='resumed',token=seed['token']);result=resumed['result'];tx=root/'transactions'/seed['token'];output=(tx/'converted.json').read_bytes()
            self.check('boundary-'+point,stopped['exit_code']==(1 if os.name=='nt' else -9) and result.get('phase')=='committed' and result.get('quantity')==12 and result['recovery_before']['phase']==phase and stopped.get('result')=={} and result['pid']!=load(root/'paused.json')['pid'] and (root/'source.json').read_bytes()==raw and (tx/'source.bin').read_bytes()==raw and {p.name:p.read_bytes() for p in (root/'history').glob('*')}==history and digest(output)==result['candidate_sha256'] and (tx/'history.bin').read_bytes()==next(iter(history.values())),{'stopped':stopped,'resumed':resumed})
        expected=load(ROOT/'tools/fixtures/equipment-save-transaction-platform/extra-expectations.json')
        names={row['case'] for row in self.rows};require=expected['windows' if os.name=='nt' else 'linux'];assert names==set(require) and len(names)==len(self.rows),'追加固定集合'
        summary={'status':'PASS','cases':self.rows,'case_count':len(self.rows),'seconds':time.monotonic()-self.start,'budget_seconds':180,'platform':os.name,'real_enospc':'未提供: 専用小容量volumeなし','real_cross_volume':'未提供: 専用nested別volumeなし'}
        assert summary['seconds']<=180;write(self.output/'summary.json',summary);write(self.output/'sha256.json',{p.relative_to(self.output).as_posix():digest(p.read_bytes()) for p in self.output.rglob('*') if p.is_file() and p.name!='sha256.json'})
        print('NATIVE_EXTRA_PASS:',summary['case_count'],round(summary['seconds'],3))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--godot',required=True);p.add_argument('--output',required=True);p.add_argument('--legacy-checkout')
    try:Suite(p.parse_args()).main()
    except Exception as exc:print('NATIVE_EXTRA_FAIL:',exc);sys.exit(1)
