"""実台帳で既存項目の変更・削除・重複・順序変更が拒否されることを検査する。"""
import copy
import json
from pathlib import Path
from sprint_registry_scope import at_commit,verified_scope,INTRO_COMMIT

ROOT=Path(__file__).resolve().parents[1]

def main():
    current=json.loads((ROOT/'assets/registry.json').read_text(encoding='utf-8'))
    shipped=at_commit(ROOT,INTRO_COMMIT)
    assert verified_scope(current,shipped)==shipped
    trials=[]
    changed=copy.deepcopy(current);changed['assets'][0]['author']='異常検出入力';trials.append(changed)
    deleted=copy.deepcopy(current);del deleted['assets'][0];trials.append(deleted)
    duplicate=copy.deepcopy(current);duplicate['assets'].append(copy.deepcopy(duplicate['assets'][0]));trials.append(duplicate)
    swapped=copy.deepcopy(current);swapped['assets'][0],swapped['assets'][1]=swapped['assets'][1],swapped['assets'][0];trials.append(swapped)
    structure=copy.deepcopy(current);structure['unapproved_group']=[];trials.append(structure)
    for trial in trials:
        try:verified_scope(trial,shipped)
        except AssertionError:continue
        raise AssertionError('既存台帳の異常を受け入れた')
    print('REGISTRY_SPRINT_SCOPE_PASS: actual_registry=PASS negative_cases=5')
    return 0

if __name__=='__main__':raise SystemExit(main())
