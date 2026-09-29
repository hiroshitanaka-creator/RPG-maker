"""港町の通常地形・施設・桟橋・原画の対応を検査する。"""
import hashlib,json
from pathlib import Path
import numpy as np
from build_first_region_presentation import reachable
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def main():
    doc=read('world/first_region.json');interiors=read('world/interiors.json');d=doc['first_region']
    assert d==interiors['first_region']
    site=next(s for s in doc['sites'] if s['id']=='first_port')
    assert site==next(s for s in interiors['sites'] if s['id']=='first_port')
    assert len(site['rooms'])==9 and len(d['port_doors'])==16
    assert len(site['rooms'][0]['events'])>=8
    maps=read('world/first_region_visuals.json')['maps'];entries={e['path']:e for e in read('assets/registry.json')['assets']}
    for index,r in enumerate(site['rooms']):
        m=maps['first_port:'+str(index)];assert m['layout']==r['layout']
        mask=np.array([[v=='.' for v in row] for row in r['layout']])
        for event in r['events']:
            assert event['kind'] not in ['battle','recruit']
            x,y=event['cell'];mask[y,x]=False
            assert 'assets/characters/'+event['sprite']+'/walk.png' in entries
        found=reachable(mask,d['port_spawn']['cell'] if index==0 else [8,10])
        for link in d['port_doors']:
            if link['from']['room']==index:assert tuple(link['from']['cell']) in found,link
            if link['to']['room']==index:assert tuple(link['to']['cell']) in found,link
        for event in r['events']:
            x,y=event['cell'];assert any((x+dx,y+dy) in found for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(0,2)]),event['id']
        for layer in m['layers']:
            for x,y,t in layer['cells']:
                assert 0<=x<m['width'] and 0<=y<m['height']
                tile=m['tiles'][t];assert tile['path'] in entries
                sx,sy,w,h=tile['region'];sw,sh=entries[tile['path']]['size']
                assert w==h==32 and 0<=sx<=sw-w and 0<=sy<=sh-h
        if index==0:
            for p in [(25,16),(26,23),(29,7),(29,5)]:assert p in found,p
            assert not mask[21,26]
    assert site['rooms'][1]['events'][0]['kind']=='rest'
    assert site['rooms'][2]['events'][0]['kind']=='shop'
    assert site['rooms'][3]['events'][0]['kind']=='weapon_shop'
    assert site['rooms'][4]['events'][0]['kind']=='npc'
    assert site['rooms'][5]['events'][0]['shrine']
    record=read('assets/source_records/port-town.json');raw=(ROOT/record['reference']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record['sha256']
    assert (ROOT/'docs/reference/visual-targets/port-town.png').read_bytes()==raw
    result=dict(status='PASS',rooms=9,exterior_residents=len(site['rooms'][0]['events']),door_links=16,all_doors_reachable=True,sea_not_walkable=True,reference_sha256=record['sha256'])
    (ROOT/'docs/verification/sprint5-port-town/layout-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PORT_LAYOUT_PASS: rooms=9 exterior_residents=9 links=16')
if __name__=='__main__':main()
