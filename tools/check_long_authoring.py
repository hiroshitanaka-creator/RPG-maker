"""台本・観察・分岐・時間予算を、実測と区別して棚卸しする。"""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def main():
    catalog = json.loads((ROOT/'data/long_campaign_v1.json').read_text(encoding='utf-8'))
    scripts = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'data/long_campaign/arcs').glob('*.json'))]
    episodes = [e for s in scripts for e in s['episodes']]
    assert len(scripts)==20 and len(episodes)==80
    scenes = [scene for e in episodes for scene in e['scenes']]
    assert len(scenes)==320 and all(len(s)>=2 and all(line.strip() for line in s) for s in scenes)
    assert len({json.dumps(e['scenes'],ensure_ascii=False) for e in episodes})==80, '同一本文の冒険を複製しない'
    assert len({json.dumps(scene,ensure_ascii=False) for scene in scenes})==320, '同一場面の本文を複製しない'
    assert all(len(e['choice']['options'])==2 and len(e['choice']['outcomes'])==2 and e['choice']['outcomes'][0]!=e['choice']['outcomes'][1] for e in episodes)
    activities = [a for m in catalog['missions'] for a in m['activities']]
    assert len(activities)==80
    families = {kind:sum(a['kind']==kind for a in activities) for kind in ['sequence','perspective','allocation','route']}
    assert all(n==20 for n in families.values())
    assert sum(len(a['observations']) for a in activities)==160
    report = {'status':'PASS','arcs':20,'episodes':80,'unique_episode_bodies':80,'unique_scene_bodies':320,'field_activities':families,'observations':160,'choice_outcomes':160,'past_scenes':sum(len(e.get('past_scene_indices',[])) for e in episodes),'catalog_sha256':hashlib.sha256((ROOT/'data/long_campaign_v1.json').read_bytes()).hexdigest(),'duration_budget_minutes':3600,'duration_budget_status':'DESIGN_HYPOTHESIS','human_duration':'NOT_RUN','text_quality':'HUMAN_JUDGMENT_NOT_RUN'}
    (ROOT/'docs/verification/long-authoring-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('LONG_AUTHORING_PASS: 20連作80話・本文320場面・観察160・結果160。60時間の実測ではない')

if __name__=='__main__':main()
