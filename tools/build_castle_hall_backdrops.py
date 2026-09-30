"""城の大広間（新設）・謁見の間・港町の灯台の見張り部屋を、依頼者の一枚絵の背景＋見えない通行地図へ置き換える。

あわせて、城の部屋のつながりを次のとおりに作り直す（2026年9月30日の依頼）。
  城の外 → 中庭 → 大広間 → 奥の中央の扉 → 謁見の間
                          → 奥の左の扉   → 宝物庫
                          → 奥の右の扉   → 書庫
大広間は部屋番号11（末尾に追加。既存の部屋番号は変えない）。謁見の間は部屋番号2のまま、下の扉だけにする。

build_port_inn_backdrop.py と同じ規則：原画全体を最近傍で縮小し、natural.gpl へ最近傍で減色する。
拡大・ぼかし・半透明・色調補正はしない。歩ける場所は「人物の足元（マスの下半分）が床に乗るマス」を手で書いた。
"""
import json
from pathlib import Path
import numpy as np
from backdrop_common import ROOT,scaled_backdrop,overlay,grid
from build_first_region_presentation import reachable

VERIFY=ROOT/'docs/verification/castle-hall-backdrops'
INCOMING='assets/_incoming/owner-2026-09-30-interiors/'
PRIOR='assets/_incoming/owner-2026-09-29-interiors/'
CASTLE='first_castle';PORT='first_port'
HALL=11;THRONE=2;TREASURY=3;LIBRARY=10;COURT=1;LIGHTHOUSE=8

def rows(spec,columns,count):
    """{行:[歩ける列…]} から '#'/'.' の行文字列を作る。"""
    out=[]
    for y in range(count):
        cells=set()
        for item in spec.get(y,[]):cells.update(range(item[0],item[1]+1) if isinstance(item,tuple) else [item])
        out.append(''.join('.' if x in cells else '#' for x in range(columns)))
    return out

# --- 大広間（IMG_1160）。縮尺1/3：小さな扉が1マス、両開きの扉が2マス、床のマス目が人物と釣り合う。
HALL_ART=dict(original=INCOMING+'IMG_1160.jpg',sha256='417785708e5391b89b590321d07d49f7f7fabd87b5853b674d1a23749d8f811d',scale=1/3,columns=18,rows=12,offset=(2,0),output='assets/interiors/castle_great_hall.png')
# 上の扉：左(5,2)＝宝物庫、中央(8..9,2)＝謁見の間（手前に3段の階段）、右(12,2)＝書庫。下の両開き(8..9,9)＝中庭。
# 柱(4,x)(13,x)と燭台(3,3)(3,8)(14,3)(14,8)は通れない。柱の外側の細い通路は入口がないので歩けない扱い。
HALL_LAYOUT=rows({2:[5,8,9,12],3:[(5,12)],4:[(5,12)],5:[(5,12)],6:[(5,12)],7:[(5,12)],8:[(5,12)],9:[8,9]},18,12)

# --- 謁見の間（IMG_1133）。縮尺0.457：両開きの扉が2マス幅（64px）になる。
THRONE_ART=dict(original=PRIOR+'IMG_1133.png',sha256=None,scale=0.457,columns=24,rows=17,offset=(-6,18),output='assets/interiors/castle_throne_room.png')
# 玉座の壇(10..13,4..5)は通れない。王は壇の前(12,5)に立ち、絨毯の上(12,6)から話しかける。
# 柱は上段(4,7,8,15,18,19 の 4〜6行)と下段(同8〜12行)。7行目は柱の間を抜ける通路。下の両開き(11..12,14)＝大広間。
THRONE_LAYOUT=rows({
    4:[5,6,16,17,20],5:[5,6,9,12,14,16,17,20],6:[5,6,9,10,11,12,13,14,16,17,20],7:[(3,20)],
    8:[3,5,6,9,10,11,12,13,14,16,17,20],9:[3,5,6,9,10,11,12,13,14,16,17,20],10:[3,5,6,9,10,11,12,13,14,16,17,20],
    11:[3,5,6,9,10,11,12,13,14,16,17,20],12:[3,5,6,9,10,11,12,13,14,16,17,20],13:[11,12],14:[11,12]},24,17)

# --- 灯台の見張り部屋（IMG_1159）。縮尺0.36：扉が約1マス幅、樽が1マス、机・望遠鏡が人物と釣り合う。
LIGHT_ART=dict(original=INCOMING+'IMG_1159.jpg',sha256='7a45a39f46d04032c198c8d652795a7910ad230d413db658c5cb85ba69c0ab5a',scale=0.36,columns=19,rows=13,offset=(-4,0),output='assets/interiors/lighthouse_lookout.png')
# 望遠鏡(7,3)・机(4..5,4..5)・椅子・樽(14,4..6)は通れない。扉(9,10)の手前(9,9)は扉の上半分の位置。
LIGHT_LAYOUT=rows({2:[8,9,10],3:[6,(8,13)],4:[(6,13)],5:[(6,13)],6:[(4,14)],7:[(5,14)],8:[(5,13)],9:[9],10:[9]},19,13)

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def link(node,a,ac,b,bc):return {'from':{'layer':'interior','node':node,'room':a,'cell':list(ac)},'to':{'layer':'interior','node':node,'room':b,'cell':list(bc)}}

def npc(id,cell,label,text,sprite,**extra):
    return dict(id=id,kind='npc',sprite=sprite,cell=list(cell),label=label,text=list(text),**extra)

def main():
    import hashlib
    THRONE_ART['sha256']=hashlib.sha256((ROOT/THRONE_ART['original']).read_bytes()).hexdigest()
    document=json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'));d=document['first_region']
    interiors=json.loads((ROOT/'world/interiors.json').read_text(encoding='utf8'))
    visuals=json.loads((ROOT/'world/first_region_visuals.json').read_text(encoding='utf8'))
    castle=next(s for s in document['sites'] if s['id']==CASTLE);port=next(s for s in document['sites'] if s['id']==PORT)
    old_hall=castle['rooms'][THRONE]
    assert old_hall['title'].endswith('謁見の間')
    made={}
    for name,art,layout in [('great_hall',HALL_ART,HALL_LAYOUT),('throne_room',THRONE_ART,THRONE_LAYOUT),('lighthouse',LIGHT_ART,LIGHT_LAYOUT)]:
        assert len(layout)==art['rows'] and all(len(r)==art['columns'] for r in layout),name
        image,size,colors=scaled_backdrop(art['original'],art['sha256'],art['scale'],art['columns'],art['rows'],art['offset'])
        (ROOT/art['output']).parent.mkdir(parents=True,exist_ok=True);image.save(ROOT/art['output'])
        made[name]=(image,size,colors)
        grid(image,art['columns'],art['rows']).save(VERIFY/f'{name}-grid.png')

    # ---- 部屋の内容 ----
    # 謁見の間：人物（王・側近・兵士2人）と台詞は今のまま。立ち位置だけ新しい絵に合わせる。
    # 兵士(右)の台詞「西に宝物庫、東に書庫があります。」は、謁見の間から左右の扉がなくなるため、大広間の案内へ改めた。
    ev={e['id']:e for e in old_hall['events']}
    ev['king']['cell']=[12,5];ev['advisor']['cell']=[14,5]
    ev['hall_guard_left']['cell']=[10,12];ev['hall_guard_right']['cell']=[13,12]
    ev['hall_guard_right']['text']=['宝物庫と書庫へは、大広間の奥の左右の扉からどうぞ。']
    throne={'title':old_hall['title'],'layout':list(THRONE_LAYOUT),'events':[ev[k] for k in ['king','advisor','hall_guard_left','hall_guard_right']]}
    great={'title':castle['rooms'][COURT]['title'].replace('中庭','大広間'),'layout':list(HALL_LAYOUT),'events':[]}
    castle['rooms'][THRONE]=throne
    if len(castle['rooms'])==HALL:castle['rooms'].append(great)
    else:castle['rooms'][HALL]=great
    assert len(castle['rooms'])==HALL+1
    # 中庭の兵士の案内も、扉の先が大広間になったので合わせる。
    court_events={e['id']:e for e in castle['rooms'][COURT]['events']}
    court_events['court_guard_left']['text']=['正面の扉が大広間です。奥の中央の扉が謁見の間です。']
    lookout=port['rooms'][LIGHTHOUSE];assert lookout['title']=='灯台の見張り部屋'
    lookout['layout']=list(LIGHT_LAYOUT)
    lookout['events'][0]['cell']=[8,4]

    # ---- 扉のつながり ----
    doors=d['castle_doors']
    def touches(l,rooms):return l['from']['room'] in rooms or l['to']['room'] in rooms
    kept=[l for l in doors if not (touches(l,{THRONE,TREASURY,LIBRARY,HALL}) or (l['from']['room']==COURT and l['to']['room']==THRONE))]
    kept=[l for l in kept if not (l['from']['room']==COURT and l['from']['cell']==[16,10])]
    new=[]
    new+=[link(CASTLE,COURT,(16,10),HALL,(8,8)),link(CASTLE,HALL,(8,9),COURT,(16,11)),link(CASTLE,HALL,(9,9),COURT,(16,11))]
    new+=[link(CASTLE,HALL,(8,2),THRONE,(11,13)),link(CASTLE,HALL,(9,2),THRONE,(12,13)),link(CASTLE,THRONE,(11,14),HALL,(8,3)),link(CASTLE,THRONE,(12,14),HALL,(9,3))]
    new+=[link(CASTLE,HALL,(5,2),TREASURY,(8,10)),link(CASTLE,TREASURY,(8,11),HALL,(5,3))]
    new+=[link(CASTLE,HALL,(12,2),LIBRARY,(8,10)),link(CASTLE,LIBRARY,(8,11),HALL,(12,3))]
    d['castle_doors']=kept+new
    # 灯台：港町側の扉の着地と、部屋側の出口を新しい扉(9,10)へ。
    pd=d['port_doors']
    for l in pd:
        if l['from']['room']==0 and l['to']['room']==LIGHTHOUSE:l['to']['cell']=[9,8]
        if l['from']['room']==LIGHTHOUSE and l['to']['room']==0:l['from']['cell']=[9,10]

    # ---- 到達確認 ----
    def check(node_doors,room_index,layout,start,events,door_cells):
        mask=np.array([[c=='.' for c in r] for r in layout]);blocked=mask.copy()
        for e in events:
            if e['kind']=='npc':blocked[e['cell'][1],e['cell'][0]]=False
        found=reachable(blocked,start)
        for c in door_cells:assert tuple(c) in found,('扉へ到達できない',room_index,c)
        for e in events:
            assert any((e['cell'][0]+dx,e['cell'][1]+dy) in found for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]),('人物へ到達できない',e['id'])
        for l in node_doors:
            if l['to']['room']==room_index:assert layout[l['to']['cell'][1]][l['to']['cell'][0]]=='.',('着地が通れない',l)
            if l['from']['room']==room_index:assert layout[l['from']['cell'][1]][l['from']['cell'][0]]=='.',('出口が通れない',l)
        return found
    hall_doors=[l['from']['cell'] for l in d['castle_doors'] if l['from']['room']==HALL]
    check(d['castle_doors'],HALL,HALL_LAYOUT,[8,8],[],hall_doors)
    throne_doors=[l['from']['cell'] for l in d['castle_doors'] if l['from']['room']==THRONE]
    found=check(d['castle_doors'],THRONE,THRONE_LAYOUT,[11,12],throne['events'],throne_doors)
    assert (12,6) in found,'王へ話しかける位置に行けない'
    check(d['port_doors'],LIGHTHOUSE,LIGHT_LAYOUT,[9,8],lookout['events'],[[9,10]])

    # ---- 保存 ----
    for s in interiors['sites']:
        if s['id']==CASTLE:s['rooms']=castle['rooms']
        if s['id']==PORT:s['rooms']=port['rooms']
    interiors['first_region']=d
    surround=visuals['maps'][f'{CASTLE}:{THRONE}'].get('surround','assets/tiles/castle_wall.png')
    for key,art,layout,idx in [(f'{CASTLE}:{HALL}',HALL_ART,HALL_LAYOUT,'castle_great_hall'),(f'{CASTLE}:{THRONE}',THRONE_ART,THRONE_LAYOUT,'castle_hall'),(f'{PORT}:{LIGHTHOUSE}',LIGHT_ART,LIGHT_LAYOUT,None)]:
        m=visuals['maps'].get(key,{'version':1,'tile_size':32,'origin':[0,0],'surround':surround})
        if idx:m['id']=idx
        m.update(width=art['columns'],height=art['rows'],tiles={},layers=[],layout=list(layout),backdrop=dict(path=art['output'],offset=[0,0],size=[art['columns']*32,art['rows']*32]))
        visuals['maps'][key]=m
    write(ROOT/'world/first_region.json',document);write(ROOT/'world/interiors.json',interiors);write(ROOT/'world/first_region_visuals.json',visuals)

    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    paths={a['output'] for a in (HALL_ART,THRONE_ART,LIGHT_ART)}
    registry['assets']=[e for e in registry['assets'] if e['path'] not in paths]
    notes={'great_hall':('城の大広間','castle-great-hall-backdrop.json','IMG_1160。倍率1/3で最近傍縮小、左に2px寄せ。右端は外周の暗色。'),
           'throne_room':('城の謁見の間','castle-throne-room-backdrop.json','IMG_1133。倍率0.457で最近傍縮小。左6pxと下0.5pxの外周の暗色を切り、上へ18pxの暗色を足した。'),
           'lighthouse':('港町の灯台の見張り部屋','lighthouse-lookout-backdrop.json','IMG_1159。倍率0.36で最近傍縮小。左右の外周の暗色を4pxずつ切った。')}
    for name,art,layout in [('great_hall',HALL_ART,HALL_LAYOUT),('throne_room',THRONE_ART,THRONE_LAYOUT),('lighthouse',LIGHT_ART,LIGHT_LAYOUT)]:
        title,record,note=notes[name];_,size,colors=made[name]
        registry['assets'].append(dict(path=art['output'],kind='interior_backdrop',size=[art['columns']*32,art['rows']*32],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Claude Code（原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-30',original_file=art['original'],prompt_record='assets/source_records/'+record,conversion_record='assets/source_records/'+record,modified=title+'：依頼者の原画全体を最近傍縮小し、natural.gplへ最近傍減色。'+note+'切り抜き・描き足し・色調補正・ぼかしなし。'))
        write(ROOT/'assets/source_records'/record,dict(original=art['original'],sha256=art['sha256'],source='依頼者の原画（'+title+'）。バイト列を変更せず保管。',method='一枚絵の背景＋見えない通行地図。最近傍縮小、natural.gplへ最近傍減色。',scale=art['scale'],offset=list(art['offset']),scaled_size=list(size),canvas=[art['columns']*32,art['rows']*32],colors=colors,layout=layout))
    write(ROOT/'assets/registry.json',registry)

    marks={'great_hall':{(8,2):'door',(9,2):'door',(5,2):'door',(12,2):'door',(8,9):'door',(9,9):'door'},
           'throne_room':{(11,14):'door',(12,14):'door',(12,5):'npc',(14,5):'npc',(10,12):'npc',(13,12):'npc'},
           'lighthouse':{(9,10):'door',(8,4):'npc'}}
    for name,art,layout in [('great_hall',HALL_ART,HALL_LAYOUT),('throne_room',THRONE_ART,THRONE_LAYOUT),('lighthouse',LIGHT_ART,LIGHT_LAYOUT)]:
        overlay(made[name][0],layout,marks[name]).save(VERIFY/f'{name}-collision-overlay.png')
    print('CASTLE_HALL_BACKDROP_BUILD_PASS: '+' '.join(f'{n}={made[n][1]} colors={made[n][2]}' for n in made))

if __name__=='__main__':main()
