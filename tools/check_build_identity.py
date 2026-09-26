"""GDScriptとの指紋一致と、版・履歴の不一致を実ファイルで検査する。"""
import json
import shutil
import tempfile
from pathlib import Path
from build_identity import ROOT, EXPECTED_ENGINE, identity
from summarize_playtest import summarize

def main():
    recorded=json.loads((ROOT/'docs/verification/nonhuman-v1-checks.json').read_text(encoding='utf-8'))['build']
    current=identity(EXPECTED_ENGINE)
    assert recorded==current, 'GodotとPythonの実行版IDが一致しない'
    temporary_root=(ROOT/'.tools').resolve()
    temporary_root.mkdir(exist_ok=True)
    directory=Path(tempfile.mkdtemp(prefix='build-id-',dir=temporary_root)).resolve()
    assert directory.is_relative_to(temporary_root)
    try:
        for folder in ['scripts','scenes','data','world']:
            shutil.copytree(ROOT/folder,directory/folder)
        files=['project.godot','assets/registry.json','assets/palette/base.gpl']
        files += [e['path'] for e in json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))['assets']]
        files += ['assets/palette/bright.gpl']
        files += ['assets/palette/natural.gpl']
        files += [e['path'] for e in json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8')).get('audio', [])]
        for relative in files:
            target=directory/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,target)
        assert identity(EXPECTED_ENGINE,directory)==current
        for relative in ['data/jobs/01_warrior.json','data/catalog.json','data/story_v1.json','scripts/combat/battle_math.gd','world/terrain.json','world/interiors.json','world/map_graph.json','assets/palette/bright.gpl','assets/palette/natural.gpl']:
            path=directory/relative
            original=path.read_bytes()
            path.write_bytes(original+b'\n')
            assert identity(EXPECTED_ENGINE,directory)['id'] != current['id'],relative
            path.write_bytes(original)
        fixture={'source':'automated','game':{'engine':EXPECTED_ENGINE,'build_id':current['id'],'build_identity_version':1,'content_revision':1}}
        assert summarize(fixture)['current_content']
        assert summarize(fixture)['status']=='NOT_ACCEPTED'
        fixture['game']['engine']='different-engine'
        assert not summarize(fixture)['current_content']
        del fixture['game']['build_id']
        assert not summarize(fixture)['current_content']
    finally:
        # 自分で作った検査用ディレクトリだけを削除する。
        assert directory.is_relative_to(temporary_root) and directory.name.startswith('build-id-')
        shutil.rmtree(directory)
    print('BUILD_ID_PASS: 実行版の一致・職業/敵/物語/処理の変更検出・旧記録と混在の非受入')

if __name__=='__main__':main()
