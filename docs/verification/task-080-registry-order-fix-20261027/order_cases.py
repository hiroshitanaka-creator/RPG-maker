"""登録順・非対象値・新規追加・再適用を独立した具体値で検証する。"""
from pathlib import Path
import sys,json,copy
repo=Path('/workspace/task080/github-save-20261027/repo');sys.path.insert(0,str(repo/'tools'))
from build_region2_village_backdrops import merge_asset_entries
serialize=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'))
checks=[]
def check(ok,label):checks.append({'case':label,'ok':bool(ok)})
foreign1={'path':'foreign-before','source':'owner','nested':{'z':1,'a':2}}
foreign2={'path':'foreign-middle','custom':[3,1]}
foreign3={'path':'foreign-after','license':'unchanged'}
existing=[foreign1,{'path':'owned-a','value':'old'},foreign2,{'path':'owned-b','value':'old'},foreign3]
generated=[{'path':'owned-b','value':'new-b'},{'path':'new-z','value':7},{'path':'owned-a','value':'new-a'},{'path':'new-a','value':8}]
expected=[foreign1,{'path':'owned-a','value':'new-a'},foreign2,{'path':'owned-b','value':'new-b'},foreign3,{'path':'new-z','value':7},{'path':'new-a','value':8}]
before_existing=serialize(existing);before_generated=serialize(generated)
result=merge_asset_entries(existing,generated)
check(serialize(result)==serialize(expected),'既存位置・非対象値とキー順を維持し新規を生成順に追加')
check(serialize(existing)==before_existing and serialize(generated)==before_generated,'入力を変更しない')
check(serialize(merge_asset_entries(result,generated))==serialize(expected),'再適用で全bytes不変')
check(serialize(merge_asset_entries([],generated))==serialize(generated),'初回登録は生成順に決定的追加')
check(serialize(merge_asset_entries(existing,[]))==before_existing,'生成対象なしは既存を全保持')
check(serialize(merge_asset_entries([],[]))=='[]','両方空')
owned={x['path'] for x in generated}
legacy=[x for x in existing if x['path'] not in owned]+generated
check(serialize(legacy)!=serialize(expected),'旧末尾移動アルゴリズムを負例として検出')
bad_cases=[]
bad=copy.deepcopy(expected);bad.pop(0);bad_cases.append(('非対象削除',bad))
bad=copy.deepcopy(expected);bad[0]['nested']={'a':2,'z':1};bad_cases.append(('非対象キー順変更',bad))
bad=copy.deepcopy(expected);bad[0]['source']='generated';bad_cases.append(('非対象値変更',bad))
bad=copy.deepcopy(expected);bad.append(copy.deepcopy(bad[-1]));bad_cases.append(('新規重複追加',bad))
bad=copy.deepcopy(expected);bad[-2:]=reversed(bad[-2:]);bad_cases.append(('新規追加順逆転',bad))
bad=copy.deepcopy(expected);bad.pop();bad_cases.append(('新規項目欠落',bad))
for label,bad in bad_cases:check(serialize(bad)!=serialize(expected),'負例拒否:'+label)
data={'checks':checks,'failed':sum(not x['ok'] for x in checks),'expected':expected,'observed':result,'source':'独立した固定入力・期待値。旧アルゴリズムと破損出力の負例を含む'}
Path(sys.argv[1]).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print('REGISTRY_ORDER_CASES:',len(checks),'failed',data['failed']);raise SystemExit(bool(data['failed']))
