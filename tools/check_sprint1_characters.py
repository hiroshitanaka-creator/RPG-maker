#!/usr/bin/env python3
"""スプリント1の仕様同期と人物取り込みを、その最終Git版で検査する。"""
from pathlib import Path
import argparse, hashlib, io, json, re, subprocess, sys, tarfile, tempfile
from collections import defaultdict
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='f288ed442731c4b1ae33649219647bca0a1a26e6'
FINAL_REF='refs/tags/sprint-1-characters-2026-09-27'

def previous(path):
    return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

def plain(text):
    lines=[]
    for line in text.splitlines():
        if re.fullmatch(r'[ |:\-]+',line):continue
        line=re.sub(r'^#+\s*','',line).replace('`','').replace('|','').replace('\t','')
        lines.append(re.sub(r'\s+','',line))
    return ''.join(lines)

def audit():
    from import_owner_characters import source_rows, palettes, render, PAIRS
    from validate_assets import check_asset, check_provenance, load_palette
    road=(ROOT/'docs/roadmap-v2.md').read_text(encoding='utf8')
    spec=(ROOT/'docs/experience-spec-v2.md').read_text(encoding='utf8')
    old_spec=previous('docs/experience-spec-v2.md').decode('utf8')
    appendix=road[road.index('## 物語の大筋'):].strip()
    assert spec.count(appendix)==1
    assert spec.index('## 物語の構成と旧本編の再配置')<spec.index(appendix)<spec.index('## 既存仕様・契約の変更方針')
    removed=spec.replace(appendix+'\n\n','',1)
    assert removed.split('## 画面と演出の仕様')[0].strip()==old_spec.split('\n画面と演出の仕様')[0].strip()
    old_screen=old_spec.split('\n画面と演出の仕様',1)[1].split('## 未決事項',1)[0]
    screen=spec.split('## 画面と演出の仕様',1)[1].split('## 未決事項',1)[0]
    assert plain(screen)==plain(old_screen),'画面仕様の本文が変化している'
    assert screen.count('### ')==11 and '`docs/reference/visual-targets/`' in screen
    pending=road.split('6. 決まっていない事項\n',1)[1].split('付録A：',1)[0]
    actual=spec.split('## 未決事項',1)[1].replace('- [ ] ','')
    assert plain(actual)==plain(pending)
    rules=[r for r in road.split('3. 共通ルール\n',1)[1].split('4. スプリント計画',1)[0].splitlines() if r.strip()][1:]
    assert len(rules)==7
    agents=(ROOT/'AGENTS.md').read_text(encoding='utf8')
    assert agents==previous('AGENTS.md').decode('utf8').rstrip()+'\n\n'+'\n'.join('- '+r for r in rules)+'\n'
    record=json.loads((ROOT/'assets/source_records/owner-characters.json').read_text(encoding='utf8'))
    rows=source_rows();banks=palettes(rows);imported=record['imported']
    assert len(rows)==len(imported)==118
    assert len({r['id'] for r in rows})==34 and sum(r['pose']=='standing' for r in rows)==34
    assert record['god_pairs']==[list(p) for p in PAIRS]
    assert [p[0] for p in PAIRS]==['太陽','月','海','戦い','実り']
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));old=json.loads(previous('assets/registry.json'))
    entries={e['path']:e for e in registry['assets']};old_entries={e['path']:e for e in old['assets']}
    paths={r['path'] for r in imported}
    assert len(paths)==118 and set(entries)-set(old_entries)==paths and len(entries)==527
    palette=load_palette(ROOT/'assets/palette/natural.gpl');group_colors=defaultdict(set)
    for r,original in zip(imported,rows):
        assert r['id']==original['id'] and r['pose']==original['pose'] and r['crop']==original['crop']
        source=(ROOT/r['original_file']).read_bytes()
        assert source==previous(r['original_file']) and hashlib.sha256(source).hexdigest()==r['original_sha256']
        im=Image.open(ROOT/r['path']).convert('RGBA')
        assert im.size==(32,48) and im.tobytes()==render(original['part'],banks[r['id']]).tobytes()
        assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['output_sha256']
        a=np.array(im);colors=set(map(tuple,a[:,:,:3][a[:,:,3]>0]));group_colors[r['id']]|=colors
        assert colors and colors<=palette and len(colors)<=16 and set(np.unique(a[:,:,3]))=={0,255}
        assert not check_asset(entries[r['path']],palette)[0] and not check_provenance(entries[r['path']])
        assert entries[r['path']]['frame']==[32,48] and entries[r['path']]['grid']==[1,1]
    assert all(len(colors)<=16 for colors in group_colors.values())
    assert registry['audio']==old['audio'] and registry['defaults']==old['defaults']
    for p,e in old_entries.items():assert entries[p]==e and (ROOT/p).read_bytes()==previous(p),p
    files=subprocess.run(['git','ls-tree','--full-tree','-r','--name-only',BASE],cwd=ROOT,capture_output=True,check=True).stdout.decode().splitlines()
    fixed=[p for p in files if p.startswith(('scripts/','scenes/','world/','data/','test/','addons/','.scope-lock/','.github/','assets/palette/','assets/audio/','assets/_incoming/','docs/reference/','docs/verification/art-review/')) or p in ('project.godot','docs/roadmap-v2.md','docs/asset-spec.md','tools/check_owner_monsters.py','tools/check_size_rock_review.py','tools/check_owner_supplement.py','tools/check_visual_target_assets.py','tools/validate_assets.py','tools/smoke_first_region.gd','tools/smoke_chapter1.gd')]
    assert fixed
    for p in fixed:assert (ROOT/p).read_bytes()==previous(p),p
    print('SPRINT1_DOCS_PASS: appendix=verbatim pending=roadmap screen_body=unchanged rules=7')
    print(f'SPRINT1_CHARACTERS_PASS: characters=34 poses=84 files=118 replayed=118 colors_per_character<=16 alpha=0/255 unchanged_images=409 fixed_files={len(fixed)}')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default=FINAL_REF);parser.add_argument('--snapshot',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args()
    if args.snapshot:
        assert '.tools' in ROOT.parts and ROOT.name.startswith('sprint1-snapshot-');audit();return
    revision=subprocess.run(['git','rev-parse','--verify',args.revision],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()
    raw=subprocess.run(['git','archive','--format=tar',revision],cwd=ROOT,capture_output=True,check=True).stdout
    parent=ROOT/'.tools';parent.mkdir(exist_ok=True);destination=Path(tempfile.mkdtemp(prefix='sprint1-snapshot-',dir=parent)).resolve()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
        for member in tar.getmembers(): assert (destination/member.name).resolve().is_relative_to(destination)
        tar.extractall(destination,filter='data')
    print('SPRINT1_FIXED_REVISION: '+revision,flush=True)
    result=subprocess.run([sys.executable,str(destination/'tools/check_sprint1_characters.py'),'--snapshot'],cwd=destination)
    raise SystemExit(result.returncode)

if __name__=='__main__':main()
