"""カイナの家だけを、板張り・生活のまとまり・出口への通路を持つ配置へ更新する。"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from import_job_costumes import parts
from import_castle_town_assets import quantize

ROOT=Path(__file__).resolve().parents[1]

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf8'));entries={e['path']:e for e in registry['assets']};records=[]
    for name,specs in [('furniture',[('bed',(64,96),'object'),('table',(96,64),'object'),('cupboard',(64,96),'object'),('hearth',(64,96),'object')]),('surfaces',[('floor',(128,128),'tile'),('wall',(128,64),'tile'),('window',(64,64),'object'),('rug',(128,96),'object')])]:
        raw=f'assets/_incoming/home-2026-09-28/{name}.png'
        for (im,box),(identifier,size,kind) in zip(parts(ROOT/raw,2,2),specs):
            if kind=='tile':
                im=im.crop((4,4,im.width-4,im.height-4)).resize(size,Image.Resampling.NEAREST);im.putalpha(255)
            else:
                im.thumbnail((size[0]-2,size[1]-2),Image.Resampling.NEAREST)
                body=im;im=Image.new('RGBA',size);im.alpha_composite(body,((size[0]-body.width)//2,size[1]-body.height))
            im,palette=quantize(im,64)
            rel=f'assets/{"tiles" if kind=="tile" else "objects"}/home_{identifier}.png';im.save(ROOT/rel)
            entries[rel]=dict(path=rel,kind=kind,size=list(size),max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='imagegen + Python/Pillow',author='RPG-maker / Codex（目標画像：依頼者）',license='LicenseRef-Generated-Project',generated_at='2026-09-28',prompt_record='assets/source_records/home-generation.json',conversion_record='assets/source_records/home-conversion.json',modified='村の原画の木材と漆喰に合わせて家専用の家具・表面を生成。切り出し、最近傍縮小、自然色64色以内、二値透過。')
            records.append(dict(path=rel,source=raw,source_sha256=sha(ROOT/raw),box=box,size=list(size),palette=palette,sha256=sha(ROOT/rel)))
    registry['assets']=list(entries.values());write(ROOT/'assets/registry.json',registry);write(ROOT/'assets/source_records/home-conversion.json',records)
    gp=ROOT/'assets/source_records/home-generation.json';generation=json.loads(gp.read_text(encoding='utf8'))
    for item in generation:item['raw_sha256']=sha(ROOT/item['raw']);item['reference_sha256']=sha(ROOT/item['reference'])
    write(gp,generation)
    # 素材の登録を終えてから配置用の台帳を読み込む。
    from build_visual_target_mocks import Map
    from build_first_region_presentation import payload,rows,reachable
    m=Map('kaina_home',16,9);m.base('assets/tiles/home_floor.png')
    mask=np.ones((9,16),bool);mask[:2,:]=False;mask[-1,:]=False;mask[:,[0,15]]=False;mask[8,8]=True
    walls=[[x,y,m.tile('assets/tiles/home_wall.png',((x%4)*32,y%2*32,32,32))] for y in range(2) for x in range(16)]
    walls += [[x,y,m.tile('assets/tiles/home_wall.png',(0,32,32,32))] for y in range(2,9) for x in [0,15]]
    walls += [[x,8,m.tile('assets/tiles/home_wall.png',((x%4)*32,32,32,32))] for x in range(1,15) if x!=8]
    m.layer('壁',walls)
    rug='assets/objects/home_rug.png'
    m.layer('敷物',[[9+x,4+y,m.tile(rug,(x*32,y*32,32,32))] for y in range(3) for x in range(4)])
    def stamp(path,x,y,solid=True):
        m.stamp(path,x,y,block=solid)
        if solid:
            w,h=entries[path]['size'];mask[y:y+h//32,x:x+w//32]=False
    stamp('assets/objects/home_bed.png',2,2)
    stamp('assets/objects/home_table.png',10,4)
    stamp('assets/objects/home_cupboard.png',12,1)
    stamp('assets/objects/home_hearth.png',8,1)
    stamp('assets/objects/home_window.png',3,0,False)
    stamp('assets/objects/home_window.png',10,0,False)
    stamp('assets/objects/natural_barrels.png',1,6)
    stamp('assets/tiles/bright_pot.png',5,2)
    stamp('assets/tiles/bright_house_door.png',8,8,False)
    found=reachable(mask,[4,4]);assert (8,8) in found and mask[4,4]
    document=payload(m);document['layout']=rows(mask);document['surround']='assets/tiles/home_wall.png'
    source=ROOT/'world/first_region.json';definition=json.loads(source.read_text(encoding='utf8'))
    home=next(s for s in definition['sites'] if s['id']=='start_village')['rooms'][0]
    home['layout']=rows(mask);write(source,definition)
    interior_path=ROOT/'world/interiors.json';interiors=json.loads(interior_path.read_text(encoding='utf8'))
    next(s for s in interiors['sites'] if s['id']=='start_village')['rooms'][0]=home;write(interior_path,interiors)
    vp=ROOT/'world/first_region_visuals.json';visual=json.loads(vp.read_text(encoding='utf8'))
    castle_before={k:json.dumps(v,sort_keys=True) for k,v in visual['maps'].items() if k.startswith('first_castle:')}
    visual['maps']['start_village:0']=document
    assert castle_before=={k:json.dumps(v,sort_keys=True) for k,v in visual['maps'].items() if k.startswith('first_castle:')}
    write(vp,visual)
    out=ROOT/'docs/verification/sprint5-home-shoreline';out.mkdir(parents=True,exist_ok=True)
    from build_castle_town import render
    render(document,[]).save(out/'home-layout.png')
    write(out/'home-checks.json',{'status':'PASS','size':[16,9],'start':[4,4],'exit':[8,8],'reachable_cells':len(found),'new_assets':8,'castle_maps_preserved':len(castle_before)})
    print('COZY_HOME_PASS: assets=8 start=4,4 exit=8,8 reachable='+str(len(found)))

if __name__=='__main__':main()
