"""背景土台の追加で本番処理・原本・凍結条件・既存CIを変えていないことを照合する。"""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE='dad3fca1d2d6216c3418999d27a4cf581ca00860'

def main():
    files=['scripts','data','scenes','project.godot','.scope-lock','test','addons','assets/_incoming','assets/palette']
    subprocess.run(['git','diff','--exit-code',BASE,'--',*files],cwd=ROOT,check=True)
    before=subprocess.check_output(['git','show',BASE+':.github/workflows/ci.yml'],cwd=ROOT).decode('utf-8').replace('\r\n','\n')
    after=(ROOT/'.github/workflows/ci.yml').read_text(encoding='utf-8')
    for name in ('村の独立背景・原画不変・再生成・実描画画素を検査','村の独立地形を既存の通行・移動APIで検査'):
        marker='      - name: '+name+'\n'
        assert after.count(marker)==1,'追加CIが欠落・重複: '+name
        start=after.index(marker);end=after.index('      - name:',start+len(marker))
        after=after[:start]+after[end:]
    for line in ('            region2-village-backdrops.log\n','            docs/verification/region2-village-backdrops/runtime-checks.json\n'):
        assert after.count(line)==1,'追加ログ保存が欠落・重複'
        after=after.replace(line,'',1)
    assert after==before,'既存CIのステップ・入力・判定・時間上限が変更されている'
    print('VILLAGE_SCOPE_PASS: production_paths=10 prior_ci_bytes_identical=True')
    return 0

if __name__=='__main__':raise SystemExit(main())
