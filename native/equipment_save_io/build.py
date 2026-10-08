#!/usr/bin/env python3
"""固定依存のdebug/releaseを構築し、実argv/hash/コンパイラを保存する。"""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
REPO=BASE.parents[1]
PIN=json.loads((BASE/'dependencies.json').read_text())['godot_cpp']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def build(args):
    dep=Path(args.cpp).resolve() if args.cpp else BASE/'.deps/godot-cpp'
    if not dep.exists():
        subprocess.run(['git','clone','--no-checkout',PIN['url'],str(dep)],check=True)
        subprocess.run(['git','checkout','--detach',PIN['commit']],cwd=dep,check=True)
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=dep,text=True).strip()!=PIN['commit']:raise RuntimeError('godot-cpp完全commit不一致')
    env=os.environ.copy();env['EQUIPMENT_GODOT_CPP']=str(dep)
    entries=[]
    for target in ['template_debug','template_release']:
        argv=[sys.executable,'-m','SCons','-C',str(BASE),f'build_profile={BASE / "build-profile.json"}',f'platform={args.platform}',f'target={target}','arch=x86_64',f'-j{args.jobs}']
        if args.mingw:argv+=['use_mingw=yes','use_llvm=yes',f'mingw_prefix={Path(args.mingw).resolve()}']
        start=time.monotonic();child=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600)
        output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
        (output/(target+'.log')).write_bytes(child.stdout)
        entries.append({'argv':argv,'seconds':time.monotonic()-start,'budget_seconds':600,'exit_code':child.returncode,'log_sha256':hashlib.sha256(child.stdout).hexdigest()})
        if child.returncode:raise RuntimeError('ビルド失敗:'+target)
    binary_root=REPO/'addons/equipment_save_io/bin'
    files={p.relative_to(REPO).as_posix():sha(p) for p in binary_root.glob('equipment_save_io.*') if p.suffix in ['.so','.dll']}
    (binary_root.parent/'manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
    compiler=[str(Path(args.mingw)/'bin/x86_64-w64-mingw32-clang++'),'--version'] if args.mingw else ['cl'] if args.platform=='windows' else ['c++','--version']
    version=subprocess.run(compiler,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout.decode(errors='replace')
    metadata={'godot_cpp':PIN,'scons':subprocess.check_output([sys.executable,'-m','SCons','--version'],env=env,text=True),'compiler':version,'commands':entries,'files':files,'source_files':{p.relative_to(REPO).as_posix():sha(p) for p in BASE.rglob('*') if p.is_file() and '.deps' not in p.parts and p.suffix in ['.cpp','.h','.json']}}
    (Path(args.output)/'build.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--platform',choices=['windows','linux'],required=True);p.add_argument('--cpp');p.add_argument('--mingw');p.add_argument('--jobs',type=int,default=4);p.add_argument('--output',required=True)
    build(p.parse_args())
