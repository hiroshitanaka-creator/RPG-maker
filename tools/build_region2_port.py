"""採用された案Aを第2港の独立した本番地図データへ組み立てる。"""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_visual_target_mocks import Map,ENTRIES,route
from build_first_region_presentation import payload,rows,point
from import_region2_port_assets import ROOMS,NAMES,LABELS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/verification/region2-port'
NODE='brine_port'

def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def asset(name):return 'assets/objects/region2_'+name+'.png'
def npc(i,cell,text,kind='npc',**extra):return dict(id='sand_'+NAMES[i],kind=kind,sprite='npc_sand_'+NAMES[i],cell=cell,label=LABELS[i],text=text,**extra)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    plan=json.loads((ROOT/'docs/verification/region2-port-layout/layout-options.json').read_text(encoding='utf8'))['plans'][0]
    town=Map('region2_port',48,32);town.base('assets/tiles/region2_water.png')
    mask=Image.new('1',(48,32));ImageDraw.Draw(mask).polygon([(0,0),(48,0)]+[tuple(p) for p in plan['coast']]+[(0,32)],fill=1)
    land=np.array(mask,dtype=bool);walk=land.copy();walk[[0,-1],:]=False;walk[:,[0,-1]]=False
    def floor(mask,path):town.layer('地面',[[int(x),int(y),town.tile(path,(0,0,32,32))] for y,x in np.argwhere(mask)])
    floor(land,'assets/tiles/region2_sand.png')
    roads=np.zeros_like(land)
    for road in plan['roads']:roads|=route(town,[tuple(p) for p in road],2)
    yy,xx=np.mgrid[:32,:48];roads|=((xx-22)**2/36+(yy-14)**2/25<=1)
    floor(roads&land,'assets/tiles/region2_cobble.png')
    piers=np.zeros_like(land)
    for road in plan['piers']:piers|=route(town,[tuple(p) for p in road],2)
    piers[18:24,39:47]=True;floor(piers,'assets/tiles/region2_pier.png');walk|=piers
    # 岸は原画から抜いた岩の部品で表し、海側の通行は許可しない。
    coast=plan['coast']
    for a,b in zip(coast,coast[1:]):
        steps=max(1,round(np.linalg.norm(np.array(b)-a)/2.5))
        for t in range(steps):
            x,y=np.rint(np.array(a)+(np.array(b)-a)*t/steps).astype(int)
            x=min(45,max(0,x-1));y=min(29,max(0,y-1))
            if not piers[y:y+3,x:x+3].any():town.stamp(asset('rocks'),int(x),int(y),block=False)
    def stamp(name,x,y,solid=True):
        path=asset(name);town.stamp(path,x,y,block=solid)
        if solid:
            w,h=ENTRIES[path]['size'];walk[y:min(32,y+h//32),x:min(48,x+w//32)]=False
    buildings=[('inn',18,3,1,[21,7]),('item',29,4,2,[32,7]),('weapon',4,12,3,[7,16]),('armor',35,11,4,[38,15]),('shrine',40,3,5,[42,7]),('harbor',40,19,6,[43,22]),('home_a',4,23,0,[7,26]),('home_b',14,24,0,[17,27])]
    for name,x,y,room,door in buildings:
        stamp(name,x,y);walk[door[1],door[0]]=True;walk[door[1]+1,door[0]]=True
    stamp('well',21,13)
    for kind,(x,y) in zip(['red','blue','gold','sand'],plan['markets']):stamp('stall_'+kind,x-1,y-1)
    stamp('arch',3,1,False)
    town.objects[-1][2]['name']='gate_open'
    for y in range(1,7):walk[y,4:7]=True
    for x,y in [(1,7),(1,19),(11,2),(15,28),(37,5),(45,12)]:stamp('palm',x,y)
    for x,y in [(2,28),(7,29),(12,29),(33,0),(45,3)]:stamp('pillar',x,y)
    for x,y in [(1,28),(7,29),(30,0),(43,1)]:stamp('wall',x,y)
    for x,y in [(26,23),(43,29),(27,29)]:stamp('boat',x,y,False)
    events=[npc(6,[28,26],['潮が静かなうちに、網のほつれを直しておくんだ。','船に乗るなら中央の桟橋へ。足元に気をつけてな。']),npc(7,[18,19],['日ざしの強い日は、荷物より先に水の残りを確かめな。','井戸のそばで少し休んでいくといい。']),npc(8,[16,21],['この水がめ、両手で持つとこぼれにくいんだ。','急がず、日陰を通って帰るよ。'],patrol=[[16,21],[17,21],[17,22],[16,22]]),npc(9,[12,10],['石のアーチを抜けると砂の道が続いている。','まだ歩いていない道のことは、ここで聞いてから決めようと思ってね。'],patrol=[[12,10],[13,10],[13,11],[12,11]])]
    for e in events:walk[e['cell'][1],e['cell'][0]]=True
    exterior=payload(town);exterior.update(layout=rows(walk),surround='assets/tiles/region2_sand.png')
    room_data=[dict(title='第2地方の港町（仮）',layout=rows(walk),events=events)]
    maps={NODE+':0':exterior};doors=[]
    # 床の足元で判定。壁・棚・台・ベッド・展示を個別に避ける。
    specs={
      'inn':dict(blocks=[(3,2,5,5),(6,2,8,5),(10,3,15,6),(13,6,15,9)],clerk=[12,3],stand=[12,6],reach=3,kind='rest',text=['砂の道を歩いたあとは、水を飲んでひと休みしてください。','部屋を整えてあります。今夜はゆっくりお休みください。']),
      'item':dict(blocks=[(3,2,5,8),(12,2,14,8),(5,4,11,6)],clerk=[8,3],stand=[8,6],reach=3,kind='shop',text=['道中の手当てに使う道具をそろえています。','水がめも薬も、残りを確かめてから出発してくださいね。']),
      'weapon':dict(blocks=[(2,2,5,6),(8,4,15,6)],clerk=[11,3],stand=[11,6],reach=3,kind='weapon_shop',text=['砂が刃の継ぎ目に入ったら、その日のうちに落とすんだ。','手に合うものを、落ち着いて選んでくれ。']),
      'armor':dict(blocks=[(3,2,5,5),(12,2,14,5),(3,6,5,9),(12,6,14,9),(5,3,12,5)],clerk=[11,6],stand=[10,6],reach=1,kind='npc',text=['日ざしを避ける布と、身体を守る鎧。重ね方にも工夫がいるぞ。','品の手入れをしているところだ。今は売買を休んでおる。']),
      'shrine':dict(blocks=[(3,2,5,6),(12,2,14,6),(6,1,10,4)],clerk=[10,4],stand=[10,5],reach=1,kind='npc',text=['遠い旅、お疲れさまです。ここで少し息を整えてください。','奥の石板の模様は、この建物の飾りとして残されています。'],shrine=True),
      'harbor':dict(blocks=[(4,3,6,5),(4,5,6,7),(4,7,6,9),(9,4,14,7)],clerk=[11,3],stand=[11,6],reach=3,kind='npc',text=['船は中央の桟橋に着けてある。乗るときは帆船のそばへ来てくれ。','戻る港を決めたら、風向きと荷物を確かめるんだ。'])}
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),12)
    for index,kind in enumerate(ROOMS,1):
        spec=specs[kind];grid=np.zeros((12,16),bool);grid[2:9,2:15]=True
        if kind=='item' or kind=='shrine':grid[:,2]=False;grid[:,14]=False
        for x0,y0,x1,y1 in spec['blocks']:grid[y0:y1,x0:x1]=False
        grid[9:12,8]=True
        cx,cy=spec['clerk'];sx,sy=spec['stand'];grid[cy,cx]=True;grid[sy,sx]=True
        e=npc(index-1,[cx,cy],spec['text'],spec['kind'],reach=spec['reach'],**({'shrine':True} if spec.get('shrine') else {}))
        if kind=='harbor':e=npc(5,[cx,cy],spec['text'],reach=spec['reach'])
        title='第2港の'+dict(inn='宿屋',item='道具屋',weapon='武器屋',armor='防具屋',shrine='祠',harbor='港務所')[kind]+'（仮）'
        room_data.append(dict(title=title,layout=rows(grid),events=[e]))
        maps[NODE+':'+str(index)]=dict(version=1,id='region2_'+kind,tile_size=32,width=16,height=12,origin=[0,0],tiles={},layers=[],layout=rows(grid),surround='assets/tiles/region2_sand.png',backdrop=dict(path='assets/interiors/region2_'+kind+'.png',offset=[0,0]))
        door=next(b[-1] for b in buildings if b[3]==index)
        doors.extend([dict(**{'from':point(NODE,0,door)},to=point(NODE,index,[8,10])),dict(**{'from':point(NODE,index,[8,11])},to=point(NODE,0,[door[0],door[1]+1]))])
        preview=Image.open(ROOT/maps[NODE+':'+str(index)]['backdrop']['path']).convert('RGBA');d=ImageDraw.Draw(preview)
        for y in range(12):
            for x in range(16):
                d.rectangle((x*32,y*32,x*32+31,y*32+31),outline='#72bd71' if grid[y,x] else '#953939',width=1)
        d.rectangle((cx*32,cy*32,cx*32+31,cy*32+31),outline='cyan',width=3)
        d.rectangle((sx*32,sy*32,sx*32+31,sy*32+31),outline='yellow',width=3)
        preview.save(OUT/(kind+'-walk-map.png'))
    definition=dict(second_port_entrance=dict(cell=[169,98],outward=[0,1]),second_port_spawn=point(NODE,0,[5,6]),second_port_exit=point(NODE,0,[5,1]),second_port_doors=doors)
    dock=dict(id='second_port',name='第2港の中央桟橋（仮）',ship_cell=[155,110],land=point(NODE,0,[36,28]),display_cell=[36,27])
    write(ROOT/'world/region2_port.json',dict(version=1,site=dict(id=NODE,type='town',legacy=False,rooms=room_data),definition=definition,maps=maps,docks=[dock],destinations=[dict(id=NODE,name='第2地方の港町（仮）',entrance='second_port_entrance',ship_cell=dock['ship_cell'])],interaction_positions={str(i+1):dict(cell=specs[k]['stand'],facing=2 if k=='armor' else 3 if k!='shrine' else 3) for i,k in enumerate(ROOMS)},note='案Aを採用。旧本編用の汎用brine_portは保持し、新ゲームのFirstRegionだけへ適用。'))
    print('第2港の本番配置データを保存: 外観48×32、室内6室、住人10人')

if __name__=='__main__':main()
