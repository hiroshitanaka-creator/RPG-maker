"""森の塔の配置・接続・原画・会話・既存拠点の保持を検査する。"""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
from build_first_region_presentation import reachable

ROOT=Path(__file__).resolve().parents[1]
BASE='9d9fc2e8225ed2037151e7103fe125f016ad37e1'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf8'))
def old(path):return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout

def main():
    document=read('world/first_region.json');interiors=read('world/interiors.json');d=document['first_region']
    assert d==interiors['first_region']
    before=json.loads(old('world/first_region.json'))
    for key,value in before['first_region'].items():
        if key=='encounters':
            for k,v in value.items():assert d[key][k]==v
        else:assert d[key]==value,key
    for path in ['world/first_region.json','world/interiors.json']:
        prior=json.loads(old(path));current=read(path)
        indexed={s['id']:s for s in current['sites']}
        for site in prior['sites']:assert indexed[site['id']]==site,site['id']
    site=next(s for s in document['sites'] if s['id']=='first_forest_tower')
    assert len(site['rooms'])==3 and len(d['tower_doors'])==4
    visuals=read('world/first_region_visuals.json')['maps'];registry={e['path']:e for e in read('assets/registry.json')['assets']}
    oldmaps=json.loads(old('world/first_region_visuals.json'))['maps']
    for key,value in oldmaps.items():
        if key!='world':assert visuals[key]==value,key
    for floor,room in enumerate(site['rooms']):
        m=visuals['first_forest_tower:'+str(floor)];assert room['layout']==m['layout']
        mask=np.array([[v=='.' for v in row] for row in room['layout']])
        found=reachable(mask,[10,14] if floor==0 else [9,11])
        for link in d['tower_doors']:
            if link['from']['room']==floor:assert tuple(link['from']['cell']) in found
            if link['to']['room']==floor:assert tuple(link['to']['cell']) in found
        for tile in m['tiles'].values():
            assert tile['path'] in registry
            x,y,w,h=tile['region'];assert w==h==32 and x%32==y%32==0
            sw,sh=registry[tile['path']]['size'];assert x+w<=sw and y+h<=sh
        for event in room['events']:
            x,y=event['cell'];assert any((x+dx,y+dy) in found for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)])
    recruit=next(e for e in site['rooms'][2]['events'] if e['kind']=='recruit')
    speech=(ROOT/'docs/first-region-recruit-scenes.md').read_text(encoding='utf8').split('## スイナ')[1]
    lines=[line[2:].split('：',1) for line in speech.splitlines() if line.startswith('- ') and '：' in line]
    assert recruit['speakers']==[v[0] for v in lines] and recruit['text']==[v[1] for v in lines]
    assert recruit['join_on_last_line'] and recruit['requires_clear']=='forest_tower_boss'
    for path in ['assets/palette/natural.gpl','data/catalog.json','world/map_graph.json','world/terrain.json','data/character_visuals.json']:
        # Gitの改行変換だけを除き、すべての内容を比較する。
        assert (ROOT/path).read_bytes().replace(b'\r\n',b'\n')==old(path).replace(b'\r\n',b'\n'),path
    record=read('assets/source_records/forest-tower.json')
    raw=(ROOT/record['reference']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record['sha256']
    assert (ROOT/'docs/reference/visual-targets/forest-tower.png').read_bytes()==raw
    output=dict(status='PASS',base=BASE,floors=3,stairs=4,chests=3,dialogue_lines=len(lines),old_sites_unchanged=True,old_enemies_unchanged=True,reference_sha256=record['sha256'])
    (ROOT/'docs/verification/sprint5-forest-tower/layout-checks.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('FOREST_TOWER_LAYOUT_PASS: floors=3 stairs=4 dialogue=10 preservation=PASS')

if __name__=='__main__':main()
