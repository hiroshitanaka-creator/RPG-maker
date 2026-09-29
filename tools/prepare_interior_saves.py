"""港町の手前の通常保存（.tools/port-departure.json）から、各町の入口へ置いた撮影用の保存を作る。

建物の中の歩行・会話・買い物・出入りを町ごとに確かめる撮影検査（capture_interior_rooms.gd）用。
位置だけを町の入口（定義の *_spawn）へ変える。編成・所持品・進行は元の保存のまま。
.tools/ は .gitignore の対象で、コミットしない。
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPAWN={'village':'village_spawn','castle':'castle_spawn','port':'port_spawn'}

def main()->None:
    raw=(ROOT/'.tools/port-departure.json').read_bytes()
    region=json.loads((ROOT/'world/first_region.json').read_text(encoding='utf8'))['first_region']
    for town,key in SPAWN.items():
        state=json.loads(raw)
        spawn=region[key]
        state['overworld'].update(layer='interior',node=spawn['node'],room=spawn['room'],cell=list(spawn['cell']),facing=3,entry_lock='')
        (ROOT/f'.tools/interior-{town}.json').write_text(json.dumps(state,ensure_ascii=False),encoding='utf8')
    print('INTERIOR_SAVES: village castle port')

if __name__=='__main__':main()
