"""建物の中の一枚絵の背景に重ねる、見えない通行地図と配置の定義（手書き）。

各部屋は16×12マス（512×384px）。書式：行番号 -> 歩ける列（"5-9,13" のように書く）。
書かれていない行・列は通れない（"#"）。規則は docs/port-inn-backdrop.md の「足元の規則」：
人物の足元（マスの下半分）が床の上に乗るマスだけ歩ける。店員の立つマスは、客が入れない
場所に置き、カウンターの手前1マス（reach）を隔てて客が話す。
"""
COLUMNS,ROWS=16,12

def spec(rows:dict[int,str])->list[str]:
    out=[]
    for y in range(ROWS):
        walk=set()
        for part in rows.get(y,'').split(','):
            part=part.strip()
            if not part:continue
            a,_,b=part.partition('-');walk.update(range(int(a),int(b or a)+1))
        out.append(''.join('.' if x in walk else '#' for x in range(COLUMNS)))
    return out

DOOR_ROWS={10:'8',11:'8'}

def merged(rows:dict[int,str])->dict[int,str]:
    r=dict(rows)
    for y,c in DOOR_ROWS.items():r[y]=(r[y]+','+c) if y in r and r[y] else c
    return r

# 名前 -> 定義。cap: 縮小倍率の上限（1712px幅の原画は0.34、1168px幅は0.50）。
# events: 配置する住人・店員のマス（ここに書かれたものだけ動かす）。reach: カウンター越しに話せる距離。
# door: 出入口（扉の内側の着地マス land、外へ出る踏み段 exit）。書かない部屋は (8,10)/(8,11) のまま。
ROOMS={
 'kaina_home':dict(node='start_village',room=0,title='カイナの家',file='IMG_1123.png',cap=0.34,
   rows={4:'5-6,10-11',5:'5-9,13',6:'5-9,13',7:'5-9,12-13',8:'5-13',9:'5-13'},events={},start=[6,7],door=True),
 'milfe_inn':dict(node='start_village',room=2,title='ミルフェ村・宿屋',file='IMG_1124.png',cap=0.34,
   rows={3:'5,8-10,13',4:'5,8-10,13',5:'4-13',6:'8-9',7:'5-9,12-13',8:'5-9',9:'3-13',10:'3-13'},events={'village_inn':[12,7]},door=True),
 'milfe_item':dict(node='start_village',room=3,title='ミルフェ村・道具屋',file='IMG_1125.png',cap=0.34,
   rows={4:'8',5:'3-4,12-13',6:'3-4,12-13',7:'3-13',8:'3-13',9:'2-13'},events={'village_item':[8,4]},reach={'village_item':3},door=True),
 'milfe_weapon':dict(node='start_village',room=4,title='ミルフェ村・武器屋',file='IMG_1126.png',cap=0.34,
   rows={4:'8',5:'13',6:'5-13',7:'5-13',8:'2-13',9:'2-14'},events={'village_weapon':[8,4]},door=True),
 'castle_inn':dict(node='first_castle',room=4,title='城下町の宿屋',file='IMG_1127.png',cap=0.34,
   rows={2:'8',3:'8',4:'8',5:'8',6:'6-10',7:'3-11,13',8:'5-11',9:'3-13'},events={'castle_inn':[13,7]}),
 'castle_item':dict(node='first_castle',room=5,title='城下町の道具屋',file='IMG_1128.jpg',cap=0.50,
   rows={3:'8',5:'4-12',6:'4-12',7:'3-13',8:'4-13',9:'4-13'},events={'castle_item_shop':[8,3]}),
 'castle_weapon':dict(node='first_castle',room=6,title='城下町の武器屋',file='IMG_1129.png',cap=0.34,
   rows={3:'8',5:'2-13',6:'4-14',7:'4-14',8:'2-14',9:'2-14',10:'2-6,10-14'},events={'castle_weapon_shop':[8,3]}),
 'castle_armor':dict(node='first_castle',room=7,title='城下町の防具屋',file='IMG_1130.png',cap=0.50,
   rows={5:'8',7:'2-14',8:'2-14',9:'2-14',10:'2-7,9-14'},events={'castle_armor_clerk':[8,5]}),
 'castle_shrine':dict(node='first_castle',room=8,title='城下町の祠',file='IMG_1131.png',cap=0.50,
   rows={3:'4-6,10-12',4:'3-6,10-13',5:'3,7-9,13',6:'3,7-9,13',7:'3,7-9,13',8:'3,7-9,13',9:'3-13'},events={'castle_shrine':[10,4]}),
 'castle_home':dict(node='first_castle',room=9,title='城下町の民家',file='IMG_1132.png',cap=0.34,
   rows={4:'7-8,12',5:'4,7-12',6:'2-11',7:'2-10,14',8:'2-10,14',9:'2-11,13-14',10:'2-6,10-14'},events={'castle_home_resident':[11,6]}),
 'castle_library':dict(node='first_castle',room=10,title='城の書庫',file='IMG_1139.png',cap=0.34,
   rows={3:'3-13',4:'3-6,8,10-13',5:'3-5,11-13',6:'3-5,11-13',7:'3-6,8,10-13',8:'3-13',9:'3-13'},events={'castle_librarian':[11,6]}),
 'castle_treasury':dict(node='first_castle',room=3,title='城の宝物庫',file='IMG_1140.png',cap=0.34,
   rows={3:'3-13',4:'3-13',5:'3-13',6:'3-13',7:'3-13',8:'3-13',9:'6-13',10:'3-6,10-13'},events={'castle_supplies':[8,5],'treasury_keeper':[10,7]}),
 'castle_court':dict(node='first_castle',room=1,title='エルヴァ城 中庭',file='IMG_1136.png',cap=0.34,
   rows={1:'8',2:'6-11',3:'5-12',4:'4-13',5:'4-6,10-13',6:'4-6,10-13',7:'4-6,10-13',8:'4-12',9:'6-11',10:'6-11',11:'8'},
   events={'court_guard_left':[7,2],'court_guard_right':[9,2]},court=True),
 'port_item':dict(node='first_port',room=2,title='港町の道具屋',file='IMG_1141.png',cap=0.50,
   rows={3:'8',4:'3,13',5:'3-13',6:'4-13',7:'3-13',8:'3-13',9:'3-13'},events={'port_item_shop':[8,3]}),
 'port_weapon':dict(node='first_port',room=3,title='港町の武器屋',file='IMG_1142.png',cap=0.34,
   rows={3:'8',4:'3,13-14',5:'3-14',6:'3-14',7:'2-14',8:'2-14',9:'8'},events={'port_weapon_shop':[8,3]}),
 'port_armor':dict(node='first_port',room=4,title='港町の防具屋',file='IMG_1143.png',cap=0.34,
   rows={3:'8',4:'3,12-13',5:'3-13',6:'2-14',7:'2-14',8:'2-14',9:'2-14'},events={'port_armor_clerk':[8,3]}),
 'port_shrine':dict(node='first_port',room=5,title='港町の祠',file='IMG_1144.png',cap=0.34,
   rows={3:'4-12',4:'3-6,10-13',5:'4-6,10-12',6:'4-12',7:'3-13',8:'3-13',9:'8'},events={'port_shrine':[8,6]}),
 'port_home':dict(node='first_port',room=6,title='港町の民家',file='IMG_1145.png',cap=0.50,
   rows={5:'7-9,13-14',6:'2-9,13-14',7:'2-9,13',8:'2-6,8-10,12-13',9:'8'},events={'port_home':[9,7]}),
 'port_harbor':dict(node='first_port',room=7,title='港の荷受け所',file='IMG_1146.png',cap=0.50,
   rows={3:'8',5:'3-13',6:'3-13',7:'2-14',8:'3-13',9:'8'},events={'harbor_keeper':[8,3]},reach={'harbor_keeper':2}),
}
