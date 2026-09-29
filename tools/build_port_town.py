"""IMG_1008を目標に、登録済み素材から港町と桟橋を作る。船・転移は接続しない。"""
import copy,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_visual_target_mocks import Map,ENTRIES,obj,tex,route
from build_first_region_presentation import payload,point,room,rows,reachable
from build_castle_town import Place,furnished,npc,render

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/sprint5-port-town'
NODE='first_port'
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def pier_assets():
    source='assets/objects/natural_bridge.png'
    palette=[]
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
        p=line.split()
        if len(p)>=3 and all(v.isdigit() for v in p[:3]):palette.append(tuple(map(int,p[:3])))
    palette=palette[:64]
    bridge=Image.open(ROOT/source).convert('RGB');left=(bridge.width-32)//2
    a=np.array(bridge.crop((left,48,left+32,80)));rgb=np.array(palette)
    indices=((a[:,:,None,:].astype(float)-rgb[None,None,:,:])**2).sum(axis=3).argmin(axis=2)
    deck=Image.fromarray(rgb[indices].astype('uint8')).convert('RGBA')
    edge=Image.new('RGBA',(32,32));edge.paste(deck.crop((0,0,32,7)),(0,0))
    for x in [3,24]:edge.paste(deck.crop((x,0,x+5,26)),(x,5))
    reg=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    for name,im in [('port_pier_deck',deck),('port_pier_edge',edge)]:
        path='assets/objects/'+name+'.png';im.save(ROOT/path)
        entry=dict(path=path,kind='object',size=[32,32],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-29',prompt_record='assets/source_records/port-town.json',conversion_record='assets/source_records/port-town.json',modified='登録済み木の床の画素を自然色へ対応させた桟橋。既存素材は不変。')
        reg['assets']=[e for e in reg['assets'] if e['path']!=path]+[entry];ENTRIES[path]=entry
    write(ROOT/'assets/registry.json',reg)
    return source

def main():
    OUT.mkdir(parents=True,exist_ok=True);source=pier_assets()
    document=json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'));d=document['first_region']
    visuals=json.loads((ROOT/'world/first_region_visuals.json').read_text(encoding='utf8'))
    town=Place('port_town',36,26,tex('grass'));m=town.m
    shape=Image.new('1',(36,26));ImageDraw.Draw(shape).polygon([(0,0),(33,0),(33,7),(30,10),(28,15),(24,16),(22,19),(19,21),(17,24),(14,25),(0,25)],fill=1)
    land=np.array(shape,dtype=bool);town.mask=land.copy();town.mask[[0,-1],:]=False;town.mask[:,[0,-1]]=False
    m.terrain('river',~land)
    streets=route(m,[(9,0),(9,8),(19,8),(19,17),(17,18),(8,18),(8,24)],3)
    for path in [[(4,7),(9,8),(14,7)],[(9,9),(4,16),(9,18)],[(19,8),(24,8),(24,15)],[(8,18),(13,25)],[(19,17),(24,17)],[(24,8),(31,7)]]:streets|=route(m,path,2)
    m.terrain('cobble',streets&land)
    pier=np.zeros((26,36),bool);pier[15:23,22:24]=True;pier[15:17,23:33]=True;pier[22:24,22:34]=True;pier[20:22,16:23]=True
    m.layer('地面',[[int(x),int(y),m.tile('assets/objects/port_pier_deck.png',(0,0,32,32))] for y,x in np.argwhere(pier)])
    town.mask|=pier
    for y,x in np.argwhere(pier):
        if y+1<26 and not pier[y+1,x] and not land[y+1,x]:m.stamp('assets/objects/port_pier_edge.png',int(x),int(y+1),block=False)
    # 建物の正面の扉だけを通行可能にし、内部と一対一に対応させる。
    buildings=[('natural_farm_house_a',1,1,1,[4,6]),('natural_town_house_red',12,1,2,[15,6]),('natural_town_house_blue',1,10,3,[4,15]),('natural_town_house_red',20,9,4,[23,14]),('natural_church',1,17,5,[4,24]),('natural_farm_house_b',10,19,6,[13,24]),('natural_farm_house_b',21,1,7,[24,6]),('natural_watchtower',30,2,8,[31,5])]
    for name,x,y,index,door in buildings:
        town.stamp('assets/objects/'+name+'.png',x,y)
        town.door(*door)
    for name,x,y in [('market_purple',9,10),('market_blue',13,10),('market_red',9,14),('market_ochre',13,14)]:town.stamp(obj(name),x,y)
    town.stamp(obj('well'),18,1)
    for x,y in [(0,7),(18,4),(27,1),(0,15),(17,23)]:town.stamp('assets/tiles/bright_tree_oak.png',x,y)
    for x,y in [(28,8),(27,12),(17,24)]:
        if not pier[y:y+2,x:x+2].any():town.stamp('assets/objects/natural_rubble.png',x,y)
    for x,y in [(23,18),(28,22),(32,15)]:town.stamp('assets/tiles/bright_barrel.png',x,y)
    for name,x,y in [('sign_inn',8,6),('sign_item',18,6),('sign_weapon',7,15)]:town.stamp(obj(name),x,y,False)
    for y in range(3):town.door(9,y)
    for x in range(4,15):town.door(x,25)
    events=[
        npc('port_greeter',[10,8],'港の住人',['ここは港町。宿は入口の左、道具屋は右だよ。桟橋へは広場から東へ進むんだ。'],'npc_farmer'),
        npc('fishmonger',[10,13],'魚売り',['今朝の水揚げだよ。潮が変わると、魚の寄る場所も変わるんだ。'],'npc_castle_merchant'),
        npc('cloth_seller',[14,13],'布売り',['潮風にさらした布は、よく乾くよ。旅の服も、ほつれを見ておきな。'],'npc_woman'),
        npc('fruit_seller',[10,17],'果物売り',['長く歩いた後は、水分を忘れずにね。日陰でひと息ついていきな。'],'npc_item_clerk'),
        npc('rope_seller',[14,17],'綱を編む人',['結び目は強く引くだけじゃだめさ。ほどくときのことも考えて結ぶんだ。'],'npc_farmer'),
        npc('dock_worker',[22,18],'荷運びの人',['桟橋では走らないでくれ。荷物を運ぶ人と、足元を確かめてすれ違おう。'],'npc_castle_merchant'),
        npc('port_child',[8,21],'港の子',['灯台の上からは、ずっと遠くまで見えるんだって。'],'npc_boy'),
        npc('port_resident',[18,17],'港の住人',['山道を越えてきたのかい。まず宿で身体を休めるといい。'],'npc_woman'),
        npc('pier_watcher',[30,23],'見張りの人',['沖の天気を見ているんだ。雲が低くなる日は、風向きにも気をつける。'],'npc_castle_guard')]
    maps={};rooms=[]
    def add(place,title,residents):
        display,r=place.finish(title,residents);maps[NODE+':'+str(len(rooms))]=display;rooms.append(r)
    add(town,'港町',events)
    descriptions=[
        ('inn','港町の宿屋',[dict(id='port_inn',kind='rest',sprite='npc_innkeeper',cell=[7,4],reach=2,label='宿の主人',text=['潮の音を聞きながら、ゆっくり休んでいってください。'])]),
        ('item','港町の道具屋',[dict(id='port_item_shop',kind='shop',sprite='npc_castle_merchant',cell=[7,4],reach=2,label='道具屋',text=['回復薬を用意しています。山道に戻るときも、忘れずに。'])]),
        ('weapon','港町の武器屋',[dict(id='port_weapon_shop',kind='weapon_shop',sprite='npc_weapon_clerk',cell=[7,4],reach=2,label='武器屋',text=['潮風に当たった武器は、よく拭いておくと長持ちするぞ。'])]),
        ('armor','港町の防具屋',[npc('port_armor_clerk',[7,4],'防具屋',['動きやすさと丈夫さ。どちらも旅には大切ですよ。'],'npc_item_clerk',reach=2)]),
        ('shrine','港町の祠',[npc('port_shrine',[8,5],'祠の世話役',['旅で身体の変化に気づいたら、ここで落ち着いて確かめてください。','この祠の中で編成を開き、清めたい人を選べます。'],'npc_elder_woman',shrine=True)]),
        ('home','港町の民家',[npc('port_home',[10,7],'港の住人',['潮が満ちる時刻を、毎朝ここに書いているの。昨日と同じとは限らないから。'],'npc_woman')]),
        ('home','港の荷受け所',[npc('harbor_keeper',[10,7],'荷受けの係',['荷札と荷物を一つずつ確かめているところだ。慌てると、届け先を間違えるからね。'],'npc_castle_merchant')]),
        ('library','灯台の見張り部屋',[npc('lighthouse_keeper',[10,7],'灯台守',['夜には、あの窓の明かりが帰り道の目印になる。昼のうちに、灯りの具合を確かめておくんだ。'],'npc_elder_man')])]
    for i,(kind,title,residents) in enumerate(descriptions):
        place=furnished('port_room_'+str(i+1),kind)
        add(place,title,residents)
    links=[]
    for name,x,y,index,door in buildings:
        links += [{'from':point(NODE,0,door),'to':point(NODE,index,[8,10])},{'from':point(NODE,index,[8,11]),'to':point(NODE,0,[door[0],door[1]+1])}]
    for index,r in enumerate(rooms):
        mask=np.array([[v=='.' for v in row] for row in r['layout']]);found=reachable(mask,[9,1] if index==0 else [8,10])
        for link in links:
            if link['from']['room']==index:assert tuple(link['from']['cell']) in found,('扉',index,link)
            if link['to']['room']==index:assert tuple(link['to']['cell']) in found,('着地',index,link)
        for event in r['events']:
            x,y=event['cell'];assert any((x+dx,y+dy) in found for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(0,2)]),('会話',index,event['id'])
    d.update(port_entrance=dict(cell=[51,41],outward=[-1,0]),port_spawn=point(NODE,0,[9,2]),port_exit=point(NODE,0,[9,0]),port_doors=links)
    world=visuals['maps']['world'];x,y=51-world['origin'][0],41-world['origin'][1]
    for key,char in [('layout','.'),('terrain','r')]:
        row=list(world[key][y]);row[x]=char;world[key][y]=''.join(row)
    world['tiles']['port_approach']=dict(path='assets/tiles/natural_stone_floor.png',region=[0,0,32,32])
    world['layers']=[l for l in world['layers'] if not l.get('port_approach')]+[dict(name='地面',cells=[[x,y,'port_approach']],port_approach=True)]
    site=dict(id=NODE,type='town',legacy=False,rooms=rooms)
    document['sites']=[s for s in document['sites'] if s['id']!=NODE]+[site]
    interiors=json.loads((ROOT/'world/interiors.json').read_text(encoding='utf8'));interiors['sites']=[s for s in interiors['sites'] if s['id']!=NODE]+[site];interiors['first_region']=d
    visuals['maps'].update(maps)
    write(ROOT/'world/first_region.json',document);write(ROOT/'world/interiors.json',interiors);write(ROOT/'world/first_region_visuals.json',visuals)
    for i,r in enumerate(rooms):render(maps[NODE+':'+str(i)],r['events']).save(OUT/f'map-{i:02}.png')
    reference=ROOT/'assets/_incoming/owner-2026-09-26/reference-pack-2/IMG_1008.PNG'
    (ROOT/'docs/reference/visual-targets/port-town.png').write_bytes(reference.read_bytes())
    write(ROOT/'assets/source_records/port-town.json',dict(reference=str(reference.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),source='依頼者がGrokで生成した完全オリジナル。公開とゲーム使用を承認済み。',derived_assets=['assets/objects/port_pier_deck.png','assets/objects/port_pier_edge.png'],component_sources=[source],method='登録済み木床から自然色64色以内の桟橋を作る。原本は不変。船と転移呪文は別の区切り。'))
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20);canvas=Image.new('RGB',(1440,610),'#162835');draw=ImageDraw.Draw(canvas)
    for i,path in enumerate([reference,OUT/'map-00.png']):
        im=Image.open(path).convert('RGB');im.thumbnail((700,550),Image.Resampling.NEAREST);canvas.paste(im,(i*720+(720-im.width)//2,48));draw.text((i*720+12,10),'目標 IMG_1008' if i==0 else '本番配置データから描画・港町',font=font,fill='white')
    canvas.save(OUT/'target-comparison.png')
    print('PORT_TOWN_BUILD_PASS: rooms=9 residents=17 links=16')

if __name__=='__main__':main()
