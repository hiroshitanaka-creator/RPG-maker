"""085の採用原稿・厳密41件・原36・旧段階保持・生成再現を独立期待値で検査。"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = '2a4fae60868d59f355839b524d22729704dd54f7'
OUT = ROOT / 'docs/verification/task-085'
IDS = ['ruins_sandstone_doll', 'ruins_cursed_beetle', 'ruins_sand_spirit',
       'ruins_tomb_hound', 'ruins_sandstone_colossus']
STATS = [(185,0,22,24,0,9,7), (150,12,17,28,8,10,9), (135,12,9,8,18,18,18),
         (175,6,22,13,4,10,20), (640,18,30,24,24,18,9)]
SKILLS = [[], ['firm_guard','shell_bash'], ['wind_blade'], ['fang'], ['firm_guard','power_strike']]
PROFILES = ['legacy','guardian','caster','raider','guardian']
checks = []

def check(ok, label):
    checks.append(dict(ok=bool(ok), label=label))
    if not ok: print('S11_DATA_FAIL: '+label)

def original(path):
    return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)

def read(path):
    return json.loads((ROOT/path).read_text())

def catalog_valid(catalog):
    old = json.loads(original('data/catalog.json'))['enemies']
    enemies = catalog['enemies']
    if enemies[:36] != old or len(enemies) != 41 or [e['id'] for e in enemies[36:]] != IDS:
        return False
    for i, e in enumerate(enemies[36:]):
        if e['stats'] != dict(zip(['hp','mp','attack','defense','magic','resistance','speed'], STATS[i])):
            return False
        if e['abilities'] != SKILLS[i] or e['weaknesses'] != [] or e['sprite_id'] != IDS[i] or e.get('family') != 'ruins':
            return False
        if e['jp'] != (50 if i==4 else 20): return False
        if e['tactics'] != dict(profile=PROFILES[i],focus='random',heal_below=65,
                               guard_every=3 if i==4 else 2,reaction_power=0,
                               reaction_speed=0,chorus_guard=100,focus_variation=0):
            return False
    return True

def raw_enemy_records(raw):
    text=raw.decode('utf-8');decoder=json.JSONDecoder()
    cursor=text.index('[',text.index('"enemies": ['))+1;records=[]
    while True:
        while text[cursor].isspace() or text[cursor]==',': cursor+=1
        if text[cursor]==']': return records
        start=cursor;_,cursor=decoder.raw_decode(text,cursor)
        records.append(text[start:cursor].encode('utf-8'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--regenerate',action='store_true');args=parser.parse_args()
    catalog=read('data/catalog.json')
    check(catalog_valid(catalog),'原36全定義不変＋採用5だけ＋厳密41種・全数値/技能/AI')
    check(raw_enemy_records((ROOT/'data/catalog.json').read_bytes())[:36]==raw_enemy_records(original('data/catalog.json')), '元36件のJSON定義は各レコードの全bytesも一致')
    baseline=OUT/'baseline36-catalog.json'
    check(baseline.read_bytes()==original('data/catalog.json'),'比較原本はmain完全SHAのcatalog全bytes')
    cases=[]
    for index in range(36,41):
        bad=copy.deepcopy(catalog);bad['enemies'][index]['stats']['hp']+=1;cases.append(bad)
        bad=copy.deepcopy(catalog);bad['enemies'][index]['abilities'].append('fire');cases.append(bad)
    for index in [0,30,35]:
        bad=copy.deepcopy(catalog);bad['enemies'][index]['jp']+=1;cases.append(bad)
    for mutation in ['missing','extra','held','duplicate']:
        bad=copy.deepcopy(catalog)
        if mutation=='missing':bad['enemies'].pop()
        if mutation=='extra':bad['enemies'].append(dict(bad['enemies'][0]))
        if mutation=='held':bad['enemies'][-1]['id']='desert_mummy'
        if mutation=='duplicate':bad['enemies'][-1]['id']=IDS[0]
        cases.append(bad)
    check(all(not catalog_valid(c) for c in cases),'検査器の負例17件：旧定義/新数値/技能/欠落/余分/保留/重複を拒否')
    scene=read('data/region2_ruins_scenes.json');approved=read('docs/verification/task-085/approved-scene.json')
    check(hashlib.sha256((OUT/'approved-scene.json').read_bytes()).hexdigest()=='5582c1f6fc95b7622cd1797b4dcfad6a839d2b9d06981dc32dcbf7d9b3ed9b00' and scene==approved and len(scene['lines'])==22 and len(scene['revisit'])==2,'採用全文・話者・順序・再訪の固定原本一致')
    for n in range(22):
        changed=copy.deepcopy(scene);changed['lines'][n]['text']+='。'
        check(changed!=approved,'改変本文を拒否 '+str(n))
    document=read('world/region2_ruins.json');old=json.loads(original('world/region2_ruins.json'))
    check(all(document[k]==v for k,v in old.items() if k not in ['encounters_enabled','boss_enabled']),
          '084からの全室/床/上層/階段/spawn/世界接続不変')
    check(document['encounters_enabled'] is True and document['boss_enabled'] is True,'採用範囲だけ有効化')
    check(document['record']==dict(room=3,trigger=[18,15],display_cell=[19,14]),'記録論理点と物体を分離')
    check(document['boss']==dict(room=3,cell=[31,12],enemy=IDS[4]) and
          document['reward_box']==dict(room=3,cell=[31,8]),'ボスと別箱の固定配置')
    expected_groups=[[[IDS[0]],[IDS[1]]],[[IDS[0]],[IDS[1]],[IDS[2]]],[[IDS[3]],[IDS[2]],[IDS[0],IDS[1]]],[]]
    check(document['encounters']==[dict(chance=0.025 if n<3 else 0.0,groups=g) for n,g in enumerate(expected_groups)],'4階の率と全編成完全一致')
    check(document['site']['rooms'][3]['layout'][12][31]=='.' and document['site']['rooms'][3]['layout'][8][31]=='.','ボス/箱は床、旧通路を塞がない')
    for path in ['assets/source_records/task011-enemies.json','scripts/world/first_region.gd',
                 'data/region2_shrine_scenes.json','scripts/world/first_region_travel.gd',
                 'tools/check_enemy_encounters.gd','tools/check_task011.py','tools/check_task027.py','tools/check_task011_runtime.gd',
                 'tools/capture_task011_ruins.gd','tools/check_region2_ruins_connection.gd',
                 'tools/check_region2_ruins_connection.py','docs/tasks/README.md','docs/decision-log.md']:
        check((ROOT/path).read_bytes()==original(path),'旧検査・関連データ不変 '+path)
    before=ast.parse(original('tools/task011_ruins_defs.py'));after=ast.parse((ROOT/'tools/task011_ruins_defs.py').read_text())
    filtered=ast.Module(body=[n for n in after.body if not isinstance(n,ast.Assign) or not any(isinstance(t,ast.Name) and t.id=='S11' for t in n.targets)],type_ignores=[])
    check(ast.dump(before)==ast.dump(filtered),'元MAPS/LINKS/WALLS/WORLD_CONNECTION全statement保持')
    builder=(ROOT/'tools/build_task011_ruins.py').read_text().replace('encounters_enabled=True,boss_enabled=True,**D.S11','encounters_enabled=False,boss_enabled=False')
    check(builder.encode()==original('tools/build_task011_ruins.py'),'生成器はS11メタデータ以外全bytes不変')
    changed=subprocess.check_output(['git','diff','--name-only',BASE,'--','assets','.scope-lock','test','.github','project.godot'],cwd=ROOT,text=True)
    check(not changed.strip(),'原画/派生/台帳/保護/CI不変')
    if args.regenerate:
        from build_task011_ruins import build
        with tempfile.TemporaryDirectory(prefix='task085-rebuild-') as tmp:
            a=Path(tmp)/'a';b=Path(tmp)/'b';build(a);build(b)
            paths=sorted(p.relative_to(a) for p in a.rglob('*') if p.is_file())
            check(paths==sorted(p.relative_to(b) for p in b.rglob('*') if p.is_file()),'生成path集合一致')
            for path in paths:
                check((a/path).read_bytes()==(b/path).read_bytes(),'2回生成全bytes一致 '+str(path))
                if str(path)=='world/region2_ruins.json' or str(path).startswith('assets/') and str(path)!='assets/registry.json':
                    check((a/path).read_bytes()==(ROOT/path).read_bytes(),'本番・生成全bytes一致 '+str(path))
    result=dict(status='PASS' if all(c['ok'] for c in checks) else 'FAIL',base_sha=BASE,checks=checks,
                negative_catalog_cases=len(cases),regenerated=args.regenerate,
                baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest())
    (OUT/'data-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('S11_DATA_'+result['status']+': checks='+str(len(checks)))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
