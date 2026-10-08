#!/usr/bin/env python3
"""独立mini projectで欠落・不正binary/manifestを実入力し、取引書込み0を確認。"""
import argparse,hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BAD=re.compile(rb'SCRIPT ERROR|Parse Error|_FAIL:')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(args):
    area=Path(args.output).resolve();area.mkdir(parents=True,exist_ok=False)
    template=area/'template';template.mkdir();(template/'.godot').mkdir()
    for d in ['scripts','data','world','addons/equipment_save_io']:shutil.copytree(ROOT/d,template/d)
    shutil.copy(ROOT/'project.godot',template/'project.godot')
    for filename in ['global_script_class_cache.cfg','extension_list.cfg']:shutil.copy(ROOT/'.godot'/filename,template/'.godot'/filename)
    shutil.copy(ROOT/'tools/fixtures/equipment-save-transaction-platform/binary_probe.gd',template/'probe.gd')
    platform='windows' if os.name=='nt' else 'linux';suffix='.dll' if os.name=='nt' else '.so';rel='addons/equipment_save_io/bin/equipment_save_io.'+platform+'.template_debug.x86_64'+suffix
    rows=[];env=os.environ.copy()
    for key in ['XDG_CACHE_HOME','XDG_DATA_HOME','XDG_CONFIG_HOME','APPDATA','LOCALAPPDATA']:
        p=area/'profile'/key;p.mkdir(parents=True);env[key]=str(p)
    for case in ['missing-manifest','malformed-manifest','missing-binary','corrupt-binary','binary-rehash']:
        project=area/case;shutil.copytree(template,project);root=project/'qa';root.mkdir();source=root/'source.json';source.write_bytes(b'preserve source bytes');config=root/'config.json';config.write_text(json.dumps({'root':str(root),'operation':'fail-closed'}),encoding='utf8')
        manifest=project/'addons/equipment_save_io/manifest.json';binary=project/rel
        if case=='missing-manifest':manifest.rename(manifest.with_suffix('.preserved'))
        elif case=='malformed-manifest':manifest.write_bytes(b'{bad manifest')
        elif case=='missing-binary':binary.rename(binary.with_suffix('.preserved'))
        elif case in ['corrupt-binary','binary-rehash']:
            raw=binary.read_bytes();binary.with_suffix('.preserved').write_bytes(raw);binary.write_bytes(b'not a shared library')
            if case=='binary-rehash':value=json.loads(manifest.read_bytes());value['files'][rel]=digest(binary);manifest.write_text(json.dumps(value),encoding='utf8')
        argv=[str(Path(args.godot).resolve()),'--headless','--path',str(project),'--script','res://probe.gd','--',str(config)]
        start=time.monotonic();child=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);(project/'raw.log').write_bytes(child.stdout)
        result=json.loads((root/'result.json').read_bytes());assert child.returncode==0 and result.get('ok') is False and result.get('reason_code')=='path_invalid' and not (root/'transactions').exists() and source.read_bytes()==b'preserve source bytes' and not BAD.search(child.stdout),case
        # DLL/SOが欠落/不正のengine loader errorは期待された負例。manifest負例はclean logを要求。
        if case in ['missing-manifest','malformed-manifest']:assert b'ERROR:' not in child.stdout and b'WARNING:' not in child.stdout
        rows.append({'case':case,'argv':argv,'exit_code':child.returncode,'seconds':time.monotonic()-start,'log_sha256':hashlib.sha256(child.stdout).hexdigest(),'result':result,'source_sha256':digest(source),'native_writes':0,'expected_loader_error':case not in ['missing-manifest','malformed-manifest']})
    root=area/'release';root.mkdir();config=root/'config.json';config.write_text(json.dumps({'root':str(root),'operation':'release'}),encoding='utf8')
    argv=[str(Path(args.godot).resolve()),'--headless','--path',str(ROOT),'--script','res://tools/fixtures/equipment-save-transaction-platform/binary_probe.gd','--',str(config)]
    p=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);(root/'raw.log').write_bytes(p.stdout);result=json.loads((root/'result.json').read_bytes());assert p.returncode==0 and result['ok'] and b'ERROR:' not in p.stdout and not BAD.search(p.stdout),'release実ロード'
    rows.append({'case':'release-load','argv':argv,'exit_code':p.returncode,'result':result,'log_sha256':hashlib.sha256(p.stdout).hexdigest()})
    (area/'summary.json').write_text(json.dumps({'status':'PASS','cases':rows,'case_count':6},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('BINARY_CHECKS_PASS: 6')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--godot',required=True);p.add_argument('--output',required=True);main(p.parse_args())
