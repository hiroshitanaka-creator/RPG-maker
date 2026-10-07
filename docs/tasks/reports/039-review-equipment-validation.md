# 039 装備入力検証038の独立再レビュー

## 作業前計画と固定点

指定ブランチ `codex/task-039-review-equipment-validation` をfetchし、登録 `50afaeeada04bd32bd98e1bfb8e15f9dcee83b5a` へcheckout。開始時の未コミット変更・未pushコミットはゼロ。対象は `45a58b7faf09809d916954353a3a1fe0c3d2d035`、038登録は `2547e91d36c59ed6d59f46be15c5c40b20a6b184`。対象の別checkout `/tmp/review039/target` にdetachし、本番を無改変で実行する。標準Godot 4.6.3は版照会のみでゲーム検査には使わない。公式4.7.2 ZIPを取得し、CI指定SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と一致。実行版 `/tmp/review039/bin/godot` は `4.7.2.stable.official.ed1daf0bf`。専用PATH/XDGを使用する。

AGENTS、034設計、035採用追記、036/037/038依頼・報告、本番・追加ハーネス・実行証拠を確認し、全tree差分と証拠のhashを照合する。import後に通常5394項目/400切替、追加93assertion、異常202ケース/1576assertion、独自のF1〜F3反証、R全8・保護26・素材検査の順で進める。実行時エラーも検査し、対象CIとレビュー提出CIを分離する。checkoutに `.agents/skills` は存在しない。

永続変更は039依頼書自身の状態行と本報告の2文書だけ。一時検査・ログは `/tmp/review039/` に置く。追加委譲、本番修正、main・PR27・他ブランチ更新、検査弱化や時間上限延長は行わない。

## 判定：PASS（038のF1〜F3修正）

追加の差し戻し指摘なし。定義読込みの失敗、操作種別の型不正、整数変換・合算の表現域超過は明示的に拒否される。正常5394項目/400切替と追加93assertionを対象完全SHAで再実行し、元の条件を保持していることを確認した。通常ゲームへの統合・装備全体の完成・main受入の判定ではない。

| 指摘 | 対象実コード | 独立判定 |
| --- | --- | --- |
| F1 | `equipment_rules.gd:20–132` の型・読取り検証と局所候補、`:178`以降の公開API | PASS。root/legacy_source/旧weapon/職規則/職原本の欠落・null・不正型でdefinition_errors非空、validate非空、catalog空。plan/bonus失敗、candidate/bonusesなし、can_equip=false、two_handed_active=false。正常カタログ14品と正常操作は維持 |
| F2 | 同`:325–345`、呼出し`:353` | PASS。kind欠落/null/bool/int/float/Array/Dictionary/未知文字列はinvalid_request、候補なし、state/request不変、SCRIPT ERRORなし。正常equip/change_job/set_abilitiesは成功 |
| F3 | 同`:20–26`、`:83–89`、`:402–409`、`:445–464` | PASS。floatは有限・整数性と[-2^63,2^63)を満たす場合のみint化。native intは往復なし。合算前の両端検証と前後補正失敗の伝播を確認。候補側だけのoverflowもnumeric_overflowで候補なし。正負の端値から内側へ1戻る正常計画も成功 |

整数範囲はエンジンの表現可能域であり、新しいゲームバランス上限ではない。dataは不変、clamp・新商品・新公開API・通常ゲーム接続の追加なし。負の術杖・合法負値・採用仮値も保持している。

### JSON境界の実測と限界

| JSONの十進表記 | 対象版の観測 |
| --- | --- |
| `1e30`, `-1e30`, `9223372036854775808` | invalid_bonus、定義不正として全API拒否。符号反転した成功値なし |
| `9223372036854775807` | JSONが2^63へ丸めるため拒否 |
| `9223372036854774784` | 正確に保持、計画成功 |
| `-9223372036854775808` | 正確に保持、計画成功 |
| `-9223372036854775809` | JSON解析後は-2^63へ丸まるため、その値として受理 |
| `-9223372036854777856` | 下限外として拒否 |
| `-2`, `2.0`, `0` | それぞれ整数-2、2、0を保持 |

038報告と一致。元の十進表記を任意精度で保持・判定する実装ではない。下限直下の十進値が丸めで受理される制約を「全ての元十進域外値を拒否」と言い換えない。native intのINT_MAX/INT_MINは一時インスタンスの補正辞書へ直接設定し、JSON境界と分離して両端保持、候補だけの±1 overflow拒否、逆方向の±1成功を実証した。

## 独立反証の構成

038のハーネスを再実行するだけでなく、一時Python/GDScriptを独立作成した。固定対象SHAから本番とdata/jobsをGit blobで抽出した最小プロジェクトに、各ケースで1箇所だけデータを変更し、毎回元のbyteへ戻す。期待値は手書き。プロセス上限30秒、観測結果1件、終了0、失敗配列空、SCRIPT ERROR/ERROR:/WARNING:/Parse Errorゼロをすべて要求した。

合計65ケース・528assertion、65/65成功：

- 正常対照1ケース内でkind不正12入力（欠落、null、false、true、0、1、-1、0.0、1.5、空Array、空Dictionary、bogus文字列）、正常3操作、native int両端と候補overflow/内側へ戻る計画を検証。
- カタログ・旧原本・職原本の各3ファイルに、欠落、壊れたJSON `{`、root=null/Array/bool/Stringを注入：18ケース。
- カタログのlegacy_source/items/jobs/jobs.warriorに、キー欠落、null、bool、int、float、Array、Dictionary：28ケース。
- 旧weapons[0]のnull/bool/int/Array/Dictionary：5ケース。職原本id/type欠落：2ケース。
- 上表の数値11ケース。装着したguard_stitched_braceletのdefenseを確認。

正常化stateはparty人物1名 `review`、warrior、空形態・空習得/装着能力、武器/防具/装飾は空、hp=0/mp=1、reserve空、midgame_slots=false。数値ケースだけ腕輪1個体を装飾0へ割当てる。全例で元state不変。不正定義では正常set_abilitiesを要求しても成功に流れないことと、両手条件APIもfalseとなることを追加確認した。

## 実行コマンドと結果

実行時は `source /tmp/review039/env.sh` でPATH先頭を指定バイナリにし、XDG_CACHE_HOME/DATA_HOME/CONFIG_HOMEを `/tmp/review039/xdg/` 以下へ設定。通常検査・R・素材は対象別checkoutで実行。そこで生じた検査記録は本作業ブランチへコピーしない。

| 実コマンド | 実測結果 |
| --- | --- |
| `timeout 600 godot --headless --editor --import --quit` | exit0、エラー警告0 |
| `python tools/check_frozen_files.py`（前後） | 両方exit0、26/26一致 |
| `timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd` | exit0、5394項目/400切替/失敗0、追加93assertion/失敗0、エラー警告0 |
| `python tools/check_equipment_invalid_definitions.py --source-sha 45a58b7faf09809d916954353a3a1fe0c3d2d035 --godot /tmp/review039/bin/godot --output /tmp/review039/invalid` | exit0、202ケース/1576assertion/202成功、全ケースのエラー警告0 |
| `python /tmp/review039/independent.py` | exit0、上記65ケース/528assertion、全ケースのエラー警告0 |
| `python tools/run_locked_checks.py` | exit0、R-01〜08全PASS、tests_ran=True/parser_failed=False、未実行・失敗0 |
| `python tools/validate_assets.py --strict` | exit0、素材1154・音15・パレット3・字体2、問題なし |
| `python /tmp/review039/audit.py` | exit0、全784パス、ソース同一性、固定fixture、保存ログhash、gzip展開hashの照合成功 |

Rの内訳はR-01=2tests/765assertions、R-02=5/946、R-03=2/73、R-04=1/293、R-05=2/79、R-06=2/87、R-08=17/2302。いずれもfailed=0/pending=0/invalid=false。R-07はA01〜A14全PASSと最終FIRST_REGION_PASSを既存判定器で確認。契約・verify・時間予算を変更していない。

## 全差分・正常互換・証拠の監査

`git diff --name-status 2547e91d36c59ed6d59f46be15c5c40b20a6b184 45a58b7faf09809d916954353a3a1fe0c3d2d035` の全784件を取得し、証拠778ファイル＋担当6ファイルだけ、削除ゼロとassertした。300パス制限の比較APIには依存しない。

担当6件は本番equipment_rules.gd、既存check_equipment_rules.gd、新check_equipment_invalid_definitions.py、decision-logの末尾3判断、038状態行、038報告。test/・.scope-lock/・data/・assets/・.github/・AGENTS.md、036/037の依頼・報告・過去証拠への差分なし。038依頼は状態1行だけ。新検査のCI接続はない。

実行版 `ada5c87e3aa660a8f04ed92b0c68348e3da9c633` →対象提出のソース3件とdataのbyte一致、報告のSHA-256一致を独立計算した：

| パス | SHA-256 |
| --- | --- |
| scripts/game/equipment_rules.gd | `abdf6e33c78939b0706b6c1d385007923646a99f6261ec0067879bda014d3b52` |
| tools/check_equipment_rules.gd | `9dd861a51f4170041e5f5bc94e0ebede2c2bb5460cf9eba14513880276b236f6` |
| tools/check_equipment_invalid_definitions.py | `ce42568f246aeacfe081c9a34283f4f46279d2846e2e6792914d56e0dc333445` |
| data/equipment_rules.json | `9e52fb78f74834382c50671da1a6c4de01fe377017b78ae64db8ab0871e91892` |

旧検査の全関数本文（旧_initializeより前）が追加検査直前までbyte一致。initializeの旧呼出し順・版検査も保持し、旧件数と追加件数を分離する変更だけ。固定のHUMAN/WEAPONS/ARMORS表と期待袋・枠、他人/reserve、入力・台帳・deep copy、HP/MP、主武器だけ加算、同点順・合法負値の既存条件を読んで確認した。期待値を本番関数から作る変更なし。既存の失敗分岐continueは成功数400のassertで欠落を検出し、新規の黙ったskipではない。

before-final/after-finalはcase名・期待設定・fixture_path・fixture_sha256を202件全照合して一致。それぞれ202生ログのSHA-256もresults.jsonに一致。修正前39成功/163不合格、修正後202成功で、どちらも1576assertion。execution.jsonの8実行ログhashも一致。compressed-logs.jsonのRログ7件は圧縮byteと展開後byteの両hashが一致した。

失敗履歴を最終成功と混同しない。初回beforeは172ケース/1336assertion/38成功で、root=null注入器の誤りを含む。after-probeは172ケース/162成功で、正常対照も防具の数値型照合で失敗していた。最終202件はこれらと別の修正済みハーネス・ソースに固定されている。before-coreの追加117件/失敗6・SCRIPT ERROR7件と、after-coreの追加93件/失敗0は、成功candidate分岐で実行assert数が増減するため。旧5394条件の省略ではない。実際に旧失敗ログと最終成功ログを読み分けた。

## 対象CIと提出CI

GitHub読取りAPIでhead_sha/branch/eventと全jobを直接取得。対象038のpush、head=`45a58b7faf09809d916954353a3a1fe0c3d2d035`：

- [CI 37564448939](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37564448939)：3/3 completed/success。
- [固定受入・最新回帰 37564448937](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37564448937)：17/17 completed/success。

全20成功。039起点作成時に同じ038 SHAへ生じたrunは対象038の20件にも本報告の最終CIにも含めない。未接続の装備検査2本は上記ローカル固定版で別実行しており、CI成功で代用しない。

本報告自身の最終SHAとpush後の全CI終了結果は、自己参照で文書SHAを更新し続けないため最終返答へ記す。報告作成時点で未発生のレビュー提出CIの成功を主張しない。

## 未検証・後続・範囲

依頼されたF1〜F3と正常互換性のローカル検証に未達なし。通常ゲーム接続、保存移行、初期生成・一回支給・不足補填、能力習得、実戦効果、上限縮小時の現在値切詰め、通常UI、新検査CI接続は後続であり今回未実施。人間試遊・正式数値調整も未実施。任意精度JSONの実装はない。新しい作品内容・規則の判断事項なし。

永続変更は本報告と039状態行だけ。追加委譲・本番修正・main/PR27/他ブランチ更新なし。main=`98290621204a16cbd7b4f35155edde35a153728d`、PR27の036 head=`dbceae8f68e18939a40ace71f3a24a1a1953e653` をremote参照で照合。対象の受入・マージ・036/038の状態更新は親の次工程。

## 追加の前後再実行とログ識別

同じ対象版ハーネスで `--source-sha 2547e91d36c59ed6d59f46be15c5c40b20a6b184 --output /tmp/review039/before` を実行：期待どおりexit1、202ケース/1576assertion、39成功/163不合格、エラーパターン65件。今回再実行した修正前後のcase/期待/fixture hashも202件一致。修正前のエラーを修正後の成功へ混ぜない。

`git show dbceae8f68e18939a40ace71f3a24a1a1953e653:tools/check_equipment_rules.gd > /tmp/review039/original.gd` 後、対象checkoutで `timeout 240 godot --headless --path . --script /tmp/review039/original.gd` も実行：exit0、旧5394項目/400切替、エラー警告0。

主要ログSHA-256：

| ログ | SHA-256 |
| --- | --- |
| core.log | `0445447eda5da6d950e3f5f579b574ea75ad91d0e12d675f9189f372d6aa80bf` |
| original.log | `b76b9d4e7bb4ce62fb074f718ca03b8da576923ec8ac1b8241d736f1bff610c3` |
| requirements.log | `1d7888f05efc5f8dd0119fdf0f586c71139801a56c81bd398132001f3386409a` |
| independent.log | `b318fa89fe72530288187b38eb93ec8eba346327f2cf5d21bfcf8485b76ebd35` |
| own/results.json | `9af7896e95fe454c579a472cc8bc87f5814fef9ee5afbd0ef44442caac9fcdc1` |
| invalid/results.json | `d36cd934f6797998542f544029f24fc73b30266c72f01ba85c67c5bad1071ccf` |
| before/results.json | `0dad2f132d53476e8de2b09322c3086b550dcac669b7c1c1ae097526273b6f80` |

一時ログは永続成果物としない。独立再現用スクリプトの実体を以下へ収録する。既存ハーネスの再実行は対象Git blobを使える。通常/R/素材の今回ログは上の固定hashと件数で識別する。

<details>
<summary>独立反証GDScript（/tmp/review039/independent.gd）</summary>

```gdscript
extends SceneTree
const R = preload("res://scripts/game/equipment_rules.gd")
var n := 0
var failures: Array = []
func ck(ok: bool, label: String) -> void:
    n += 1
    if not ok: failures.append(label)
func state() -> Dictionary:
    return {"equipment_rules_version":1,"equipment_stock":{"instances":{},"bag":[]},"party":[{"id":"review","job_id":"warrior","monster_form":"","learned_abilities":[],"equipped_abilities":[],"equipment":{"weapons":[],"armor":"","accessories":["","",""]},"hp":0,"mp":1}],"first_region":{"reserve":[]},"progress_flags":{"midgame_slots":false}}
func _initialize() -> void:
    var r = R.new()
    var s := state()
    var c: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://case.json"))
    var q := {"kind":"set_abilities","equipped_abilities":[]}
    var snapshot := s.duplicate(true)
    if c.mode == "bad":
        ck(not r.definition_errors().is_empty(), "定義エラー")
        ck(r.catalog().is_empty(), "原子的公開")
        ck(not r.validate_equipment_state(s).is_empty(), "検証拒否")
        var p: Dictionary = r.plan_equipment_change(s,"review",q)
        ck(p.get("ok") == false and p.get("reason_code") == "invalid_state" and not p.has("candidate"), "計画拒否")
        var b: Dictionary = r.equipment_bonuses(s,"review")
        ck(b.get("ok") == false and not b.has("bonuses"), "補正拒否")
        ck(not r.can_equip("warrior",[],"practice_blade","weapon"), "装備拒否")
        ck(not r.two_handed_active(s,"review"), "両手条件拒否")
    else:
        ck(r.definition_errors().is_empty() and r.catalog().size() == 14, "正常カタログ")
        if c.mode == "number":
            s.equipment_stock.instances = {"one":"guard_stitched_bracelet"}
            s.party[0].equipment.accessories[0] = "one"
            snapshot = s.duplicate(true)
            var b: Dictionary = r.equipment_bonuses(s,"review")
            ck(b.get("ok") == true and str(b.get("bonuses",{}).get("defense")) == c.expected, "数値固定期待")
            ck(r.plan_equipment_change(s,"review",q).get("ok") == true, "数値計画")
        else:
            var requests: Array = [{}]
            for v in [null,false,true,0,1,-1,0.0,1.5,[],{},"bogus"]: requests.append({"kind":v})
            for req in requests:
                var saved: Dictionary = req.duplicate(true)
                var p: Dictionary = r.plan_equipment_change(s,"review",req)
                ck(p.get("ok") == false and p.get("reason_code") == "invalid_request" and not p.has("candidate"), "kind拒否 " + str(req))
                ck(req == saved and s == snapshot, "kind入力不変")
            for req in [q,{"kind":"change_job","job_id":"knight"},{"kind":"equip","slot":"accessory","index":0,"instance_id":""}]:
                var saved: Dictionary = req.duplicate(true)
                var p: Dictionary = r.plan_equipment_change(s,"review",req)
                ck(p.get("ok") == true and p.has("candidate"), "正常3操作")
                ck(req == saved and s == snapshot, "正常入力不変")
            for edge in [9223372036854775807,-9223372036854775807-1]:
                var nr = R.new()
                nr._items.guard_stitched_bracelet.bonuses.defense = edge
                var t := state()
                t.equipment_stock.instances = {"a":"guard_stitched_bracelet","b":"vitality_braid"}
                t.equipment_stock.bag = ["b"]
                t.party[0].equipment.accessories[0] = "a"
                var b: Dictionary = nr.equipment_bonuses(t,"review")
                ck(b.get("ok") == true and b.get("bonuses",{}).get("defense") == edge, "native int保持")
                nr._items.vitality_braid.bonuses = {"defense":1 if edge > 0 else -1}
                var saved := t.duplicate(true)
                var p: Dictionary = nr.plan_equipment_change(t,"review",{"kind":"equip","slot":"accessory","index":1,"instance_id":"b"})
                ck(p.get("ok") == false and p.get("reason_code") == "numeric_overflow" and not p.has("candidate"), "候補だけoverflow")
                ck(t == saved, "overflow入力不変")
                nr._items.vitality_braid.bonuses.defense = -1 if edge > 0 else 1
                p = nr.plan_equipment_change(t,"review",{"kind":"equip","slot":"accessory","index":1,"instance_id":"b"})
                ck(p.get("ok") == true and p.get("stats_after",{}).get("defense") == (edge - 1 if edge > 0 else edge + 1), "境界から内側へ")
    ck(s == snapshot, "state不変")
    print("REVIEW039 " + JSON.stringify({"checks":n,"failures":failures,"errors":r.definition_errors()}))
    quit(0 if failures.is_empty() else 1)
```

</details>

<details>
<summary>独立反証実行器（/tmp/review039/independent.py）</summary>

```python
import copy,json,subprocess,pathlib,hashlib,re
root=pathlib.Path('/workspace/RPG-maker'); out=pathlib.Path('/tmp/review039/own'); out.mkdir()
project=out/'project'; project.mkdir()
sha='45a58b7faf09809d916954353a3a1fe0c3d2d035'
def blob(p):return subprocess.check_output(['git','show',sha+':'+p],cwd=root)
paths=['scripts/game/equipment_rules.gd','data/equipment_rules.json','data/integrated_rules.json']+subprocess.check_output(['git','ls-tree','-r','--name-only',sha,'data/jobs'],cwd=root,text=True).splitlines()
orig={p:blob(p) for p in paths}
for p,b in orig.items():
 d=project/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(b)
(project/'project.godot').write_text('config_version=5\n[application]\nconfig/name="039独立反証"\n')
(project/'probe.gd').write_bytes(pathlib.Path('/tmp/review039/independent.gd').read_bytes())
cases=[('normal',None,None,'normal','')]
cat='data/equipment_rules.json';old='data/integrated_rules.json';job='data/jobs/01_warrior.json'
for p in [cat,old,job]:
 for label,b in [('missing',None),('broken',b'{'),('null',b'null'),('array',b'[]'),('bool',b'true'),('string',b'"bad"')]: cases.append((p.replace('/','_')+'_'+label,p,b,'bad',''))
for loc in [('legacy_source',),('items',),('jobs',),('jobs','warrior')]:
 for label,value in [('missing',None),('null',None),('bool',True),('int',7),('float',2.5),('array',[]),('dict',{})]:
  d=json.loads(orig[cat]); target=d
  for key in loc[:-1]:target=target[key]
  if label=='missing':target.pop(loc[-1])
  else:target[loc[-1]]=value
  cases.append(('_'.join(loc)+'_'+label,cat,json.dumps(d).encode(),'bad',''))
for label,value in [('null',None),('bool',False),('int',7),('array',[]),('dict',{})]:
 d=json.loads(orig[old]);d['weapons'][0]=value;cases.append(('old_weapon_'+label,old,json.dumps(d).encode(),'bad',''))
for key in ['id','type']:
 d=json.loads(orig[job]);del d[key];cases.append(('job_missing_'+key,job,json.dumps(d).encode(),'bad',''))
for token,mode,expected in [('1e30','bad',''),('-1e30','bad',''),('9223372036854775808','bad',''),('9223372036854775807','bad',''),('9223372036854774784','number','9223372036854774784'),('-9223372036854775808','number','-9223372036854775808'),('-9223372036854775809','number','-9223372036854775808'),('-9223372036854777856','bad',''),('-2','number','-2'),('2.0','number','2'),('0','number','0')]:
 d=json.loads(orig[cat]);d['items'][13]['bonuses']['defense']='TOKEN';b=json.dumps(d).replace('"TOKEN"',token).encode();cases.append(('num_'+token,cat,b,mode,expected))
results=[]
for name,p,b,mode,expected in cases:
 if p:
  if b is None:(project/p).unlink()
  else:(project/p).write_bytes(b)
 (project/'case.json').write_text(json.dumps({'mode':mode,'expected':expected}))
 run=subprocess.run(['/tmp/review039/bin/godot','--headless','--path',str(project),'--script','res://probe.gd'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
 (out/(name+'.log')).write_bytes(run.stdout)
 lines=[json.loads(x[10:]) for x in run.stdout.decode().splitlines() if x.startswith('REVIEW039 ')]
 errors=re.findall(r'SCRIPT ERROR|ERROR:|WARNING:|Parse Error',run.stdout.decode())
 ok=run.returncode==0 and not errors and len(lines)==1 and not lines[0]['failures']
 results.append({'case':name,'exit':run.returncode,'pass':ok,'errors':errors,'observed':lines,'sha256':hashlib.sha256(run.stdout).hexdigest()})
 if p:(project/p).write_bytes(orig[p])
(out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('独立反証',len(results),'cases',sum(r['pass'] for r in results),'PASS',sum(o['checks'] for r in results for o in r['observed']),'assertions')
for r in results:
 if not r['pass']:print(r)
raise SystemExit(0 if all(r['pass'] for r in results) else 1)
```

</details>
