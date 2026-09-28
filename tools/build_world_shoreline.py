"""周囲9セルから連続した水際を生成する。全256×256セルの通行地形は変更しない。"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DIRS=[(-1,-1),(0,-1),(1,-1),(-1,0),(0,0),(1,0),(-1,1),(0,1),(1,1)]

def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def field(mask,x,y):
    samples=np.array([(mask>>i)&1 for i in range(9)],dtype=float).reshape(3,3)
    gx=(x-16)/32+1;gy=(y-16)/32+1
    ix=np.floor(gx).astype(int);iy=np.floor(gy).astype(int);fx=gx-ix;fy=gy-iy
    return samples[iy,ix]*(1-fx)*(1-fy)+samples[iy,ix+1]*fx*(1-fy)+samples[iy+1,ix]*(1-fx)*fy+samples[iy+1,ix+1]*fx*fy

def topology(water,x,y):
    h,w=water.shape
    return sum((1<<i) if (bool(water[y+dy,x+dx]) if 0<=x+dx<w and 0<=y+dy<h else True) else 0 for i,(dx,dy) in enumerate(DIRS))

def main():
    water_path=ROOT/'assets/tiles/natural_water.png';bank_path=ROOT/'assets/tiles/natural_dirt.png'
    water=np.array(Image.open(water_path).convert('RGBA'));bank=np.array(Image.open(bank_path).convert('RGBA'))
    atlas=Image.new('RGBA',(1024,8192));alpha_atlas=Image.new('RGBA',(1024,512));visible=set()
    rendered=Image.new('RGBA',(1024,8192))
    yy,xx=np.mgrid[-2:34,-2:34]+.5
    for mask in range(512):
        extended=field(mask,xx,yy)>=.5;shape=extended[2:34,2:34]
        if shape.any():visible.add(mask)
        alpha_pixels=np.empty((32,32,4),dtype=np.uint8)
        alpha_pixels[:,:,:3]=np.where(shape[:,:,None],[238,246,235],[11,24,36]);alpha_pixels[:,:,3]=255
        alpha_atlas.paste(Image.fromarray(alpha_pixels),(mask%32*32,mask//32*32))
        interior=np.ones((32,32),bool)
        for dy in range(5):
            for dx in range(5):interior &= extended[dy:dy+32,dx:dx+32]
        rim=shape&~interior
        for py in range(4):
            for px in range(4):
                y,x=np.mgrid[:32,:32];w=water[(y+py*32)%water.shape[0],(x+px*32)%water.shape[1]];b=bank[(y+py*32)%bank.shape[0],(x+px*32)%bank.shape[1]]
                pixels=np.where(rim[:,:,None],b,w).copy();pixels[:,:,3]=shape*255;pixels[~shape]=0
                index=(py*4+px)*512+mask
                rendered.paste(Image.fromarray(pixels),(index%32*32,index//32*32))
                pixels[~shape,:3]=[11,24,36];pixels[:,:,3]=255
                atlas.paste(Image.fromarray(pixels),(index%32*32,index//32*32))
    path='assets/tiles/world_connected_water.png';atlas.save(ROOT/path)
    mask_path='assets/tiles/world_water_alpha_mask.png';alpha_atlas.save(ROOT/mask_path)
    # 共有境界そのものの連続値を全4096近傍配置で照合。丸めの見せかけで継ぎ目を隠さない。
    joins=0
    t=np.linspace(0,32,65)
    for bits in range(4096):
        cells=np.array([(bits>>i)&1 for i in range(12)],dtype=bool).reshape(3,4)
        a=topology(cells,1,1);b=topology(cells,2,1)
        assert np.allclose(field(a,np.full_like(t,32),t),field(b,np.zeros_like(t),t));joins+=1
        cells=cells.T;a=topology(cells,1,1);b=topology(cells,1,2)
        assert np.allclose(field(a,t,np.full_like(t,32)),field(b,t,np.zeros_like(t)));joins+=1
    for mask in range(512):assert bool(field(mask,np.array(16.),np.array(16.))>=.5)==bool(mask&16)
    terrain_path=ROOT/'world/terrain.json';before=hashlib.sha256(terrain_path.read_bytes()).hexdigest();global_data=json.loads(terrain_path.read_text(encoding='utf8'))
    kinds=np.array([list(row) for row in global_data['rows']])
    global_water=kinds=='~'
    padded=np.pad(global_water,1)
    adjacent=padded[:-2,1:-1]|padded[2:,1:-1]|padded[1:-1,:-2]|padded[1:-1,2:]
    global_water |= (kinds=='b')&adjacent
    vp=ROOT/'world/first_region_visuals.json';visual=json.loads(vp.read_text(encoding='utf8'));local=visual['maps']['world'];ox,oy=local['origin']
    global_water[oy:oy+local['height'],ox:ox+local['width']]=np.array([[c=='~' for c in row] for row in local['terrain']],bool)
    indices=[[topology(global_water,x,y) for x in range(global_water.shape[1])] for y in range(global_water.shape[0])]
    data={'version':1,'width':global_water.shape[1],'height':global_water.shape[0],'atlas':path,'alpha_mask':mask_path,'columns':32,'shapes':512,'phases':4,'bit_order':['NW','N','NE','W','C','E','SW','S','SE'],'mask_rows':indices,'visible_masks':sorted(visible),'terrain_sha256':before,'render_rgba_sha256':hashlib.sha256(rendered.tobytes()).hexdigest()}
    (ROOT/'world/shoreline.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8',newline='\n')
    cells=[];catalog=local['tiles'];reverse={(t['path'],*t['region']):key for key,t in catalog.items()}
    for y in range(local['height']):
        for x in range(local['width']):
            mask=indices[oy+y][ox+x]
            if mask not in visible:continue
            index=(((oy+y)%4)*4+(ox+x)%4)*512+mask;region=[index%32*32,index//32*32,32,32];key=(path,*region)
            if key not in reverse:
                tile_id='water_'+str(len(reverse));reverse[key]=tile_id;catalog[tile_id]={'path':path,'region':region}
            cells.append([x,y,reverse[key]])
    local['layers']=[l for l in local['layers'] if l['name']!='接続水域']
    bridges=[l for l in local['layers'] if l['name'] in ['bright_bridge','natural_bridge']]
    local['layers']=[l for l in local['layers'] if l not in bridges]+[{'name':'接続水域','cell_size':32,'cells':cells}]+bridges
    write(vp,visual)
    rp=ROOT/'assets/registry.json';registry=json.loads(rp.read_text(encoding='utf8'));entries={e['path']:e for e in registry['assets']}
    entries[path]=dict(path=path,kind='tile',size=[1024,8192],frame=[32,32],grid=[32,256],max_colors=64,status='required',palette='assets/palette/natural.gpl',source='generated',tool='Python/Pillow',author='RPG-maker / Codex',license='LicenseRef-Generated-Project',generated_at='2026-09-28',prompt_record='assets/source_records/visual-target-generation.json#surfaces',modified='水と土の原寸模様を維持した512接続形×16模様位置の不透明な色画像。透明範囲は別画像に保存し、描画時に合成する。既存47接続素材・検査・通行地形は変更しない。',component_sources=['assets/tiles/natural_water.png','assets/tiles/natural_dirt.png'])
    entries[mask_path]=dict(entries[path],path=mask_path,size=[1024,512],grid=[32,16],max_colors=2,modified='512接続形の透明範囲を自然色の明暗2色で符号化した不透明画像。明部だけを合成時に表示する。保存画像と合成結果はいずれもアルファ0/255。')
    registry['assets']=list(entries.values());write(rp,registry)
    out=ROOT/'docs/verification/sprint5-home-shoreline';out.mkdir(parents=True,exist_ok=True)
    write(out/'shoreline-checks.json',{'status':'PASS','shapes':512,'arrangements':4096,'continuous_boundary_checks':joins,'boundary_mismatches':0,'cell_centers_checked':512,'global_cells':int(global_water.size),'terrain_unchanged':before==hashlib.sha256(terrain_path.read_bytes()).hexdigest(),'local_draw_cells':len(cells),'render_rgba_sha256':data['render_rgba_sha256'],'storage':'不透明な色画像と2色の透明範囲画像。合成結果は二値透過。既存の素材検査は変更しない。'})
    print('SHORELINE_PASS: shapes=512 joins=8192 mismatches=0 cells=65536 terrain_unchanged=1')

if __name__=='__main__':main()
