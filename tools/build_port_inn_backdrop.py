"""港町の宿屋を、依頼者の一枚絵を背景に敷く方式で作る（試作）。

原画 inn-reception-and-rooms.jpg（1168×784）を、ベッド・扉の幅が1マス（32px）に
なる倍率 384/784 で最近傍縮小し、natural.gpl へ最近傍減色する。拡大・ぼかし・
半透明は使わない。歩ける場所は、人物の足元（マスの下半分）が床に乗るマスだけを
「.」にした手書きの見えない地図で決める。原本は変更しない。
"""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_first_region_presentation import reachable

ROOT=Path(__file__).resolve().parents[1]
NODE='first_port';ROOM=1;KEY=NODE+':'+str(ROOM)
ORIGINAL='assets/_incoming/owner-2026-09-29/port-town-images/inn-reception-and-rooms.jpg'
ORIGINAL_SHA256='618f823f0455d13886b63b5ec51b24fbbec4fb7a40256cf27b16d26a683eaaa7'
OUTPUT='assets/interiors/port_inn.png'
RECORD='assets/source_records/port-inn-backdrop.json'
VERIFY=ROOT/'docs/verification/port-inn-backdrop'
COLUMNS,ROWS=18,12
SCALE=ROWS*32/784
# 通行地図（18×12）。「.」だけ歩ける。扉(8,11)・着地(8,10)は既存の港町の扉接続のまま。
# 左の寝室：(3..5,3..4)、出入口(4,5)(4,6)。右の寝室：敷物の上(8..11,2..4)、机(10,3)は通れない。
# 右の寝室の出入口(8,5)(9,5)(9,6)。広間：石畳(3..9,7..9)と受付台の前(10..11,9)。
# 受付台の裏(11..14,7)は店の人の場所で、広間とはつながらない。受付台の右脚と植木は通れない。
LAYOUT=[
    '##################',
    '##################',
    '########....######',
    '###...##..#.######',
    '###...##....######',
    '####.###..########',
    '####.####.########',
    '###.......#....###',
    '###.......########',
    '###.........######',
    '########.#########',
    '########.#########',
]
INNKEEPER=[11,7]

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def palette():
    colors=[]
    for line in (ROOT/'assets/palette/natural.gpl').read_text().splitlines():
        p=line.split()
        if len(p)>=3 and all(v.isdigit() for v in p[:3]):colors.append(tuple(map(int,p[:3])))
    return np.array(colors,float)

def backdrop():
    raw=(ROOT/ORIGINAL).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==ORIGINAL_SHA256,'原本が記録と一致しない'
    source=Image.open(ROOT/ORIGINAL).convert('RGB')
    width=round(source.width*SCALE);height=round(source.height*SCALE)
    assert height==ROWS*32 and width<=COLUMNS*32,(width,height)
    small=np.array(source.resize((width,height),Image.Resampling.NEAREST),float)
    rgb=palette();index=((small[:,:,None,:]-rgb[None,None])**2).sum(3).argmin(2)
    quantized=rgb[index].astype('uint8')
    # 右端の余白（4px）は、原画の外周と同じ暗い色で埋める。
    canvas=np.zeros((ROWS*32,COLUMNS*32,3),'uint8');canvas[:,:]=quantized[-1,-1];canvas[:,:width]=quantized
    image=Image.fromarray(canvas).convert('RGBA')
    colors=len({tuple(c) for c in canvas.reshape(-1,3)})
    assert colors<=64,colors
    (ROOT/OUTPUT).parent.mkdir(parents=True,exist_ok=True);image.save(ROOT/OUTPUT)
    return image,(width,height),colors

def overlay(image,events):
    """背景に通行地図を重ねた確認画像（緑=歩ける、赤=通れない、黄=扉、青=宿の主人）。"""
    big=image.convert('RGB').resize((COLUMNS*64,ROWS*64),Image.Resampling.NEAREST)
    tint=Image.new('RGBA',big.size,(0,0,0,0));d=ImageDraw.Draw(tint)
    for y,row in enumerate(LAYOUT):
        for x,c in enumerate(row):
            box=[x*64,y*64,x*64+63,y*64+63]
            if [x,y]==INNKEEPER:d.rectangle(box,fill=(40,120,255,110),outline=(40,120,255,255),width=2)
            elif (x,y) in [(8,10),(8,11)]:d.rectangle(box,fill=(255,220,0,90),outline=(255,220,0,255),width=2)
            elif c=='.':d.rectangle(box,fill=(40,220,80,70),outline=(40,220,80,200),width=1)
            else:d.rectangle(box,fill=(230,40,40,55),outline=(230,40,40,120),width=1)
    out=Image.alpha_composite(big.convert('RGBA'),tint).convert('RGB')
    font=ImageFont.truetype(str(ROOT/'assets/fonts/notosansjp/NotoSansJP.ttf'),13);d=ImageDraw.Draw(out)
    for y in range(ROWS):
        for x in range(COLUMNS):d.text((x*64+3,y*64+1),f'{x},{y}',font=font,fill=(255,255,255))
    return out

def main():
    image,(width,height),colors=backdrop()
    document=json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'));d=document['first_region']
    interiors=json.loads((ROOT/'world/interiors.json').read_text(encoding='utf8'))
    visuals=json.loads((ROOT/'world/first_region_visuals.json').read_text(encoding='utf8'))
    assert len(LAYOUT)==ROWS and all(len(r)==COLUMNS for r in LAYOUT)
    site=next(s for s in document['sites'] if s['id']==NODE);room=site['rooms'][ROOM]
    assert room['title']=='港町の宿屋' and room['events'][0]['id']=='port_inn'
    room['layout']=list(LAYOUT)
    room['events'][0]['cell']=list(INNKEEPER)
    assert room['events'][0]['kind']=='rest' and room['events'][0]['reach']==2
    assert LAYOUT[INNKEEPER[1]][INNKEEPER[0]]=='.' and LAYOUT[INNKEEPER[1]+1][INNKEEPER[0]]=='#' and LAYOUT[INNKEEPER[1]+2][INNKEEPER[0]]=='.'
    # 扉の接続（港町側の扉→宿(8,10)、宿(8,11)→港町）は変えない。
    links=[l for l in d['port_doors'] if ROOM in (l['from']['room'],l['to']['room']) and (l['from']['room']==ROOM)!=(l['to']['room']==ROOM)]
    assert sorted(l['from']['cell'] if l['from']['room']==ROOM else l['to']['cell'] for l in links)==[[8,10],[8,11]],links
    mask=np.array([[c=='.' for c in row] for row in LAYOUT]);blocked=mask.copy();blocked[INNKEEPER[1],INNKEEPER[0]]=False
    found=reachable(blocked,[8,10])
    assert (8,11) in found and (11,9) in found and (4,3) in found and (9,3) in found,'広間・寝室・扉・受付台の前がつながらない'
    assert (INNKEEPER[0],INNKEEPER[1]+1) not in found and (12,7) not in found,'受付台の裏に客が入れてしまう'
    for s in interiors['sites']:
        if s['id']==NODE:s['rooms'][ROOM]=room
    interiors['first_region']=d
    m=visuals['maps'][KEY]
    m.update(width=COLUMNS,height=ROWS,tiles={},layers=[],layout=list(LAYOUT),backdrop=dict(path=OUTPUT,offset=[0,0],size=[COLUMNS*32,ROWS*32]))
    write(ROOT/'world/first_region.json',document);write(ROOT/'world/interiors.json',interiors);write(ROOT/'world/first_region_visuals.json',visuals)
    entry=dict(path=OUTPUT,kind='interior_backdrop',size=[COLUMNS*32,ROWS*32],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Claude Code（原画：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-29',original_file=ORIGINAL,prompt_record=RECORD,conversion_record=RECORD,modified='依頼者の宿屋の原画全体を倍率384/784で最近傍縮小し、natural.gplへ最近傍減色。右端4pxを外周の暗色で埋めた。切り抜き・描き足し・色調補正・ぼかしなし。')
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'))
    registry['assets']=[e for e in registry['assets'] if e['path']!=OUTPUT]+[entry]
    write(ROOT/'assets/registry.json',registry)
    write(ROOT/RECORD,dict(original=ORIGINAL,sha256=ORIGINAL_SHA256,source='依頼者がGrokで描いた港町の宿屋の部屋の絵（2026年9月29日受領）。会話に添付された画像のバイト列をそのまま保管。',method='一枚絵の背景＋見えない通行地図の試作。倍率384/784（ベッド・正面扉の幅が約32px）で最近傍縮小、natural.gplへ最近傍減色。',scale=SCALE,scaled_size=[width,height],canvas=[COLUMNS*32,ROWS*32],colors=colors,layout=LAYOUT,innkeeper=INNKEEPER,door=dict(exit=[8,11],landing=[8,10]),unused_original='assets/_incoming/owner-2026-09-29/port-town-images/inn-fireplace-room.jpg'))
    VERIFY.mkdir(parents=True,exist_ok=True)
    overlay(image,room['events']).save(VERIFY/'collision-overlay.png')
    print('PORT_INN_BACKDROP_BUILD_PASS: size=%dx%d colors=%d walkable=%d'%(COLUMNS*32,ROWS*32,colors,int(mask.sum())))

if __name__=='__main__':main()
