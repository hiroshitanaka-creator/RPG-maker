#!/usr/bin/env python3
"""公式engine archive固定hashと実体hashを区別して専用CIを起動する。"""
import argparse,hashlib,json,os,subprocess,sys,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PIN={'nt':('win64.exe','731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953'),'posix':('linux.x86_64','cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4')}
def main(args):
    area=Path(args.output).resolve();area.mkdir(parents=True,exist_ok=True);platform,expected=PIN[os.name]
    name='Godot_v4.7.2-stable_'+platform;archive=area/(name+'.zip');url='https://github.com/godotengine/godot-builds/releases/download/4.7.2-stable/'+name+'.zip'
    urllib.request.urlretrieve(url,archive);actual=hashlib.sha256(archive.read_bytes()).hexdigest();assert actual==expected,'公式ZIP hash'
    # console wrapperは別PIDのengineをCreateProcessする。本体を直接起動しkill PIDを照合する。
    bin_dir=area/'bin';zipfile.ZipFile(archive).extractall(bin_dir);engine=bin_dir/name
    if os.name!='nt':engine.chmod(0o700)
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    fixed_path=ROOT/'docs/verification/equipment-save-transaction-platform/code-fixed-sha.txt';fixed=fixed_path.read_text().strip() if fixed_path.exists() else ''
    (area/'engine.json').write_text(json.dumps({'archive_sha256':actual,'executable_sha256':hashlib.sha256(engine.read_bytes()).hexdigest(),'url':url,'source_sha':sha},indent=2)+'\n')
    argv=[sys.executable,str(ROOT/'tools/fixtures/equipment-save-transaction-platform/run_ci.py'),'--godot',str(engine),'--source-sha',sha,'--profile',args.profile,'--output',str(area/'results')]
    if fixed:argv+=['--fixed-sha',fixed]
    subprocess.run(argv,cwd=ROOT,check=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--profile',required=True);main(p.parse_args())
