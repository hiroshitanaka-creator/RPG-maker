"""既存の第1地方を保ち、右側と南側に航行用の沿岸海域を接続する。"""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from build_visual_target_mocks import Map
ROOT=Path(__file__).resolve().parents[1]
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
    p=ROOT/'world/first_region_visuals.json';v=json.loads(p.read_text(encoding='utf8'));world=v['maps']['world']
    base_w,base_h=32,18;w,h=72,40
    world['terrain']=[world['terrain'][y][:base_w].ljust(w,'~') if y<base_h else '~'*w for y in range(h)]
    world['layout']=[world['layout'][y][:base_w].ljust(w,'#') if y<base_h else '#'*w for y in range(h)]
    sea=Map('first_coastal_sea',w,h);sea.base('assets/tiles/natural_water.png')
    world['tiles'].update({'coast_'+k:value for k,value in sea.catalog.items()})
    layer={'name':'地面','cells':[[x,y,'coast_'+tile] for x,y,tile in sea.layers[0]['cells']],'coastal_sea':True}
    world['layers']=[layer]+[l for l in world['layers'] if not l.get('coastal_sea')]
    world['width']=w;world['height']=h;write(p,v)
    # 既存の徒歩地形に隣接した水域を、浅瀬の乗降場所として使う。
    ox,oy=world['origin'];pairs=[]
    for y in range(13,17):
        for x in range(19,25):
            if world['layout'][y][x]!='.':continue
            for dx,dy in [(1,0),(0,1)]:
                if world['terrain'][y+dy][x+dx]=='~':pairs.append(([x+ox,y+oy],[x+dx+ox,y+dy+oy]))
    assert pairs
    land,water=pairs[-1]
    config=dict(version=1,return_name='帰還の風',return_mp=2,sea_bounds=[24,40,95,79],
        docks=[dict(id='port',name='港町の桟橋',land=dict(layer='interior',node='first_port',room=0,cell=[30,18]),ship_cell=[59,48],display_cell=[30,17]),dict(id='shallows',name='第1地方の浅瀬',land=dict(layer='world',node='',room=0,cell=land),ship_cell=water)],
        destinations=[dict(id='start_village',name='ミルフェ村',entrance='village_entrance'),dict(id='first_castle',name='エルヴァ城下町・城',entrance='castle_entrance'),dict(id='first_port',name='港町',entrance='port_entrance')],
        encounter=dict(chance=.025,enemies=['river_beast']))
    write(ROOT/'world/first_region_travel.json',config)
    out=ROOT/'docs/verification/sprint5-travel'
    layout=Image.open(out/'map-00.png').convert('RGBA')
    ship=Image.open(ROOT/'assets/vehicles/owner_ship.png').convert('RGBA').crop((96,0,192,96)).resize((192,192),Image.Resampling.NEAREST)
    px,py=config['docks'][0]['display_cell'];layout.alpha_composite(ship,(px*32+16-96,py*32+32-192))
    layout.convert('RGB').save(out/'port-with-ship-layout.png')
    canvas=Image.new('RGB',(1440,610),'#162835');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),20)
    for i,path in enumerate([ROOT/'docs/reference/visual-targets/port-town.png',out/'port-with-ship-layout.png']):
        im=Image.open(path).convert('RGB');im.thumbnail((700,550),Image.Resampling.NEAREST);canvas.paste(im,(i*720+(720-im.width)//2,48));draw.text((i*720+12,10),'目標 IMG_1008' if i==0 else '配置データと停泊船の見本（実画面ではない）',font=font,fill='white')
    canvas.save(out/'bay-with-ship-comparison.png')
    print('COASTAL_TRAVEL_BUILD: bounds=72x40 return_mp=2 shallow='+str(land))
if __name__=='__main__':main()
