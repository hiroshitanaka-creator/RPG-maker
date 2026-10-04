"""過去の区切りの全台帳項目を現行から厳密照合する。後続の別素材だけは区別する。"""
import copy
import json
import subprocess

INTRO_COMMIT='c30530cf0a85c6decbaa75da8a6f467ea21ce16d'

def at_commit(root,commit):
    return json.loads(subprocess.check_output(['git','show',commit+':assets/registry.json'],cwd=root))

def verified_scope(current,shipped):
    assert set(current)==set(shipped),'台帳の構造が変更されている'
    result=copy.deepcopy(current)
    for group,previous in shipped.items():
        if isinstance(previous,list):
            paths={entry['path'] for entry in previous}
            selected=[entry for entry in current[group] if entry['path'] in paths]
            assert selected==previous,'既存台帳項目の変更・削除・重複・順序変更: '+group
            result[group]=selected
        else:assert current[group]==previous,'台帳の共通属性の変更: '+group
    return result
