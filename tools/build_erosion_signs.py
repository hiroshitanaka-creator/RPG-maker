"""既存コマの輪郭と接地を保ち、侵蝕30の兆候を共通パレット内で作る。"""
import hashlib
import json
from pathlib import Path
from PIL import Image
from validate_assets import load_palette

ROOT=Path(__file__).resolve().parent.parent

def main():
    palette=load_palette(ROOT/'assets/palette/base.gpl')
    colors=sorted(palette)
    registry=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    visuals=json.loads((ROOT/'data/character_visuals.json').read_text(encoding='utf-8'))
    results=[]
    for actor_id,actor in visuals['actors'].items():
        actor['erosion_signs']={}
        for kind in ['walk','battle']:
            source=ROOT/actor[kind]
            image=Image.open(source).convert('RGBA')
            pixels=[]
            changed=0
            for r,g,b,a in list(image.get_flattened_data() if hasattr(image,'get_flattened_data') else image.getdata()):
                color=(r,g,b)
                if a:
                    target=(r*0.70,min(255,g*0.95+12),min(255,b*1.18+18))
                    color=min(colors,key=lambda c:sum((c[i]-target[i])**2 for i in range(3)))
                    changed+=color!=(r,g,b)
                pixels.append((*color,a))
            assert changed>0,source
            output=image.copy()
            output.putdata(pixels)
            relative=f'assets/characters/{actor_id}/erosion_signs/{kind}.png'
            destination=ROOT/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            output.save(destination)
            assert output.getchannel('A').tobytes()==image.getchannel('A').tobytes()
            template=next(e for e in registry['assets'] if e['path']==actor[kind]).copy()
            template.update(path=relative,status='required',source=actor[kind],erosion_threshold=30)
            registry['assets']=[e for e in registry['assets'] if e['path']!=relative]+[template]
            actor['erosion_signs'][kind]=relative
            results.append({'path':relative,'source':actor[kind],'changed_pixels':changed,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()})
    (ROOT/'assets/registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'data/character_visuals.json').write_text(json.dumps(visuals,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'docs/verification/erosion-signs-import.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('兆候の歩行・戦闘8点を作成。原画像・パレット・アルファは不変。')

if __name__=='__main__':main()
