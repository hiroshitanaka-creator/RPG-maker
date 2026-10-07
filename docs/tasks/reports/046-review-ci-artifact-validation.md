# 046 CI比較修正の独立再レビュー

## 開始状態・計画

開始／登録SHA `6fe91f90ac8bb01b4846857ab1db7995cb8ab681`、指定branch `codex/task-046-review-ci-artifact-validation`。remoteをfetchして一致を確認し切り替えた。開始時の未コミット／未pushは0。対象045は `e8d50eac2698ed603b64663c666af5608f607898`、実装は `858164c25224ff8467b75a3d9044f00b6c0ccb05`。対象→登録の差は046依頼書だけ。mainへの書込み／マージ・追加委譲・コード修正は行わない。

計画：(1) AGENTS・043〜045依頼／報告・原コード／固定証拠を照合、(2) F1原反例・42プローブ・元35／全77fixture・独自境界例を再実行、(3) 別checkoutで代表固定／最新原検査と旧3版比較、(4) 対象と提出の全34CI・artifactを直接確認、指定2文書だけcommit/push。

AGENTS、素材規約、職業・魔物化企画、体験仕様の関連箇所、素材台帳の構造、043〜045依頼／報告、044再現付録、wrapper／新workflow全文、装備／異常定義／S1／旧入口原検査、固定期待を確認した。checkoutに `.agents/skills` は存在せず `/workspace/.agents` は空。catalogの [verification-before-completion](skill://plugins~Plugin_60aea7460bd4819199fd97a9553a5e12/verification-before-completion/SKILL.md) を適用した。読取り対象の物語内容は報告しない。

## 判定・指摘

**044 F1/P2は解消。今回の独立検証で新たなP0／P1／P2指摘なし。** 正常原検査の成功と、不正artifactの拒否を別に実証した。S1までのCI比較修正に対する判定であり、S2以降の機能完成を意味しない。

| F1原反例 | 修正前exit | 修正後exit | 独立確認した拒否根拠 |
| --- | --- | --- | --- |
| version記録5個へ置換 | 0 | 1 | 5種類の順・一意性・argv・log名 |
| legacy commandをtrueへ置換 | 0 | 1 | 同一実体と原scriptのargv全文 |
| PASSなしlegacy.log、hash更新 | 0 | 1 | Godot冒頭・一意な142/10/失敗0行 |
| 3版のfixture hashを空辞書へ | 0 | 1 | 固定041の5原本blobのキー／hash |
| 3版を同じboolだけ偽成功JSONへ | 0 | 1 | 固定旧出力のキー・配列順・型・全値 |

必須記録はversion／前保護／import／legacy原検査／後保護の5件。cwdが同一絶対checkout、Godot／Python実体が各argvで一致、予算が30/30/600/120/30秒、実時間は有限かつ予算内、exitはintの0、timed_outはFalse、警告なしを確認する。各logは実hashとmanifestの両方へ照合され、version／保護件数／import完走／legacy PASSはそれぞれの出力契約で確認される。source/profile/latest SHA、engine実体hash、wrapper原本hash、source blob hashも固定対象へ照合される。

旧期待は `ddf2153e0f47513eb7906ddd68ab03b645edacd7` の `docs/verification/equipment-save-migration/legacy-before.json.gz`。展開後SHA256は `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。対象実装から生成していない。142検証／10更新のID・順、valid、副作用、入力／純粋変換／前後state、types、metrics/events、upgraded／second／往復を含む全キー・型・値を再帰照合した後、3版の生JSONもbyte比較する。辞書のキー順には意味を持たせず、配列のケース順・履歴順は保持する。JSON重複キー・非有限数も拒否する。

## 全tree・固定／最新・元35保持

045登録 `5899ee42c60495135f1187561bef248d2d9a92bd` →対象の全tree差分40パスは、許可されたwrapper、新workflowの固定fetch、045状態／報告、新証拠、decision-log追記のみ。削除0、decision-log過去本文prefix一致。044基点 `9010b9b` →045登録に親が行った043／044状態変更を、045担当差分に混同しない。

統合基点 `a5cbeb0bb6f239958b2330d414afc0752c4fe36a` →対象の全586パスも、043〜045の許可記録と専用CI追加に限定。既存3workflow・本番・data・素材／原画・test／.scope-lock／addons・原検査／旧証拠は不変。実装858164c→対象e8d50eaでtools／workflow／本番コード不変、対象→登録でもコード不変を確認した。

| 既存workflow | SHA256（基点から不変） |
| --- | --- |
| ci.yml | `e375c073123be06d67dacc48fe06d3b3c36de7f1b0b406533ed294f7be6b1019` |
| legacy-campaign.yml | `a9f4bd9619401bb8986de6af08caf1d790130f9f43f09d140748c9cda400a7d5` |
| region2-village-connections.yml | `4fd051de4c2295681c4bcc19b9e9b568cdd1519e3922e107921817dd60d0a24d` |

新workflow差分はcomparison／failure-propagationへ固定基点・041・当時証拠SHAをfetchする2stepだけ。全14job＝core4／invalid3／migration2／legacy3／comparison1／failure-propagation1、既存20job、push/PR実行、PR head SHA、contents:read、15分、fail-fast:false、失敗時保護照合／artifact保存を保持。個別上限延長・assert省略・continue-on-errorなし。

`assertion-map.json` の固定原本5ソースhashと全323行のstatement／行番号／omitted=falseを照合。038以降のcore／invalid、041のmigration／legacy原本は最新とbyte一致。036原本文は038の追加より前で保持。固定036/038/041のscope検査は当時SHA間だけ。coreの手書き職・品・数値表、invalidの固定境界／理由、S1の固定 `expectations.json`、旧基点実出力を期待とし、最新実装の自己一致を使わない。M07「現GameSessionは新保存を拒否」は固定041に残り、最新もまだS1なので実行する。S2での置換・接続は今回行っていない。

元35は旧wrapperを独立ロードして再実行し、修正版77件の先頭35とID・順・expected_exit・observed_exit全一致。旧self_test関数と新関数のASTは、正常legacy fixtureの代入と追加comparison_fixtures呼出しだけを除くと同一だった。欠落／失敗／重複／roundtripの元拒否変異と5正常／30拒否を維持。正常fixtureを固定旧原本へ完全化した変更は、合格に必要な省略フィールド／正しいIDの補充であり拒否期待の変更ではない。従来の不完全な正常fixture自体は追加fake_success_jsonで拒否する。

045 `evidence-sha256.json` の保存34ファイルについて実byte／byte数、圧縮の展開後hash／byte数、tar全5340 file member hashを再照合した。実装SHAの保存CI14ZIPも全2028 member／digest／原結果／比較を再実行して一致。

## 独立実行コマンド・結果

出力は `/tmp/review046/` の新規パスのみ。原証拠は上書きしていない。環境既定Godotは4.6.3で版照会時にFontconfig警告があり、本検査には使っていない。別取得した公式4.7.2 ZIPのSHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実体 `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` を照合。wrapperはXDGを隔離し、個別予算は原設定のまま。

```sh
git show 5899ee42c60495135f1187561bef248d2d9a92bd:tools/run_equipment_ci.py > /tmp/review046/old.py
python docs/verification/equipment-ci-fix/probes.py --module /tmp/review046/old.py --output /tmp/review046/before --require-rejection
python docs/verification/equipment-ci-fix/probes.py --output /tmp/review046/after --require-rejection
python tools/run_equipment_ci.py --suite self-test --latest-sha 6fe91f90ac8bb01b4846857ab1db7995cb8ab681 --output /tmp/review046/self-test
```

42プローブは旧版：対照1 exit0、不正41中32誤受理／9拒否でハーネスexit1。新版：対照1 exit0、不正41すべてexit1でハーネスexit0。元35再実行exit0、全77＝正常6 exit0／拒否71 exit1、ハーネスexit0。

044の付録スクリプトも、当時PR run `37613514157` の原3artifact（baseline `11478742156`、041 `11478988309`、latest `11478812039`）を新たにダウンロードして再実行した。付録の出力Tだけbefore／after別の新ディレクトリへ変更、sourceを展開先へ固定し、beforeのmoduleだけ上記old.pyへ変更。対象SHA `73e09c7714ad3766ea6dfdc04c19cca57e4c1231` と全12変異本文は保持。旧版：対照＋F1の5件exit0／他6拒否。新版：対照exit0／不正11すべてexit1。045の別コードSHA artifactによる42プローブと、044原artifactによる再現を区別する。

代表原検査は以下の共通コマンドをsuite/profileごとに実行した。latest実行対象は登録6fe91f9（対象045とコード同一）、固定はwrapper内の完全SHAを使用する。

```sh
python tools/run_equipment_ci.py --suite SUITE --profile PROFILE \
  --latest-sha 6fe91f90ac8bb01b4846857ab1db7995cb8ab681 \
  --godot /tmp/review046/bin/Godot_v4.7.2-stable_linux.x86_64 \
  --output /tmp/review046/local/equipment-SUITE-PROFILE
python tools/run_equipment_ci.py --suite compare \
  --latest-sha 6fe91f90ac8bb01b4846857ab1db7995cb8ab681 \
  --inputs /tmp/review046/local --output /tmp/review046/local/comparison
```

| suite / profile | 原検査秒 / import秒 | 結果 | 出力JSON SHA256 |
| --- | --- | --- | --- |
| legacy / baseline | 2.682 / 56.608 | exit0、142検証／10更新 | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| legacy / 041 | 2.982 / 58.907 | exit0、142検証／10更新 | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| legacy / latest | 3.036 / 57.338 | exit0、142検証／10更新 | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| core / 036 | 0.566 / 59.5 | exit0、5394条件／400切替 | `d6fcec3060432492ee78705079b7b11783040a4181d853b7926a38da689c8b4d` |
| core / latest | 1.143 / 67.039 | exit0、5487条件／400切替 | `1ad52c7843eaeb6f290eb36a0e090838dd2cd97b22a6fda2105e36c2529085c5` |
| migration / 041 | 25.36 / 65.746 | exit0、61ケース／2828条件／63観測 | `635b4f4ce3535b77d25d54e2660308cc30ff8ef00dd4c8191683c4505f7dbbaf` |
| migration / latest | 20.984 / 59.016 | exit0、61ケース／2828条件／63観測 | `81cd43534cdc6e60866f38fd4b222e2204180bc1d41a35fff127c1efb5e5fc07` |
| invalid / latest | 73.642 / 不要 | exit0、202ケース／1576条件 | `b1ed3743feb95dfe3348857731fa3f8e84a94e68b0d98ddfe2952dc26f2337b2` |

旧比較exit0、3版すべて固定旧出力hashと一致。S1固定／最新の全63観測と全61ケース、異常定義の全202ケースのfixture hash／期待／観測全文を当時固定原証拠へ独立照合した。全原コマンドexit0／timeoutなし／警告0、各予算内、前後保護26/26一致。

`python tools/check_frozen_files.py` は26/26一致、`python tools/validate_assets.py --strict` は画像1154／音15／字体2／パレット3・問題0。`python -m py_compile tools/run_equipment_ci.py`、`git diff --check` もexit0。

## CI・artifactの実物確認

GitHub CLIのActions API読取りはForbiddenだった。GitHub connectorのGETで同じ対象を取得できたため、CI照会は継続した。artifactの署名URLをcurlで取得する経路も失敗したが、connectorのdownload_workflow_artifact→download_fileで全原ZIPを取得できた。未取得を成功扱いしていない。

対象045 `e8d50eac2698ed603b64663c666af5608f607898` のpush全3run／34jobはすべてcompleted／successを直接確認した。同じSHAの046 branch作成時runは別runとして扱い、045提出時の終了結果に混ぜない。

| workflow / run | 全job | 結果 |
| --- | --- | --- |
| [Equipment and Save CI / 37624597873](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37624597873) | 14 | 全success |
| [006固定受入と最新回帰 / 37624597933](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37624597933) | 17 | 全success |
| [CI / 37624597955](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37624597955) | 3 | 全success |

新14ZIPはGitHub digest、全2028 memberのCRC／manifest hash、source/latest/wrapper SHA、全原コマンド・終了値・警告・予算、core4／invalid3／migration2／legacy3の全結果、77fixtureを照合。ローカルで旧比較も再実行し保存comparisonと一致した。

```sh
python docs/verification/equipment-ci-fix/verify_evidence.py \
  --sha e8d50eac2698ed603b64663c666af5608f607898 \
  --inputs /tmp/review046/target-artifacts --output /tmp/review046/target-verified
python docs/verification/equipment-ci-fix/verify_evidence.py \
  --sha 858164c25224ff8467b75a3d9044f00b6c0ccb05 \
  --inputs docs/verification/equipment-ci-fix/ci-code --output /tmp/review046/ci-code
```

両コマンドexit0。次は対象045の実artifact ID／digestである。

| 名前 | ID | ZIP SHA256 |
| --- | --- | --- |
| equipment-migration-041 | 11484320215 | `26c762fa1bd125a1976b4c742f03104889d2cb81d421548319d2713cbeef543b` |
| equipment-legacy-041 | 11484300172 | `cdac67798bf1bbb78b1877920507a8cd2c87ecde380a037c8d51112a28950bf1` |
| equipment-legacy-comparison | 11484200981 | `886dd6afa7930551536577f2eb3375b746694aafb0e401394510d6b52477dba1` |
| equipment-core-041 | 11484135459 | `0a24c2f945698868ffc4a71d7291e65b9afd8ef7083d01d83b3f42867a382250` |
| equipment-core-038 | 11484005796 | `cca760c2270b488c8142295831860faf18a691d5074dd99764705eb698f34375` |
| equipment-core-latest | 11483980726 | `941476f9cec7f2b261c69954e9690e24cbce26dd96d1fb1913993218182f5251` |
| equipment-invalid-038 | 11483935708 | `ed0f7a78564850f551668c4d3c91917fc00431781d1d90f9ec5aa451ccc7f69c` |
| equipment-core-036 | 11483920742 | `b12ef32879ee3cde22760811a2e52fe4fd7d5620976ba9da70b5597c08d2f11a` |
| equipment-invalid-latest | 11483865908 | `6dda944f9af09113ceed98dbc358c857f4b0ae1e72336defb21e960feeacd0fa` |
| equipment-migration-latest | 11483502422 | `5a86c8af04195a09c9b4fbe5d5dc78267eafe0451259f99840d4678e1b07e681` |
| equipment-invalid-041 | 11483422356 | `c15c33b8fcee7cccc3d156e64327f812982970284df773a108e15f301f77d595` |
| equipment-legacy-latest | 11483283919 | `14129bc61a9edc4fbd818a462ecdd5dd3b4a976549dd3f2bdd72a76389f1d390` |
| equipment-legacy-baseline | 11483104065 | `760a9694531e25d9ec9e4658a2be10ccb75ed109dfc359a708cf550d3e4118cc` |
| equipment-failure-propagation | 11483093871 | `c9f68c50c485ecb82876a1d7105a096a87514ed89b94387f035ad15768c415e2` |

既存19artifactも全ZIPを取得し、同一対象SHA・非expired・digest・全7225 memberのCRCを確認した。Godot artifactのscope-lock-current.jsonと原ログでR-01〜R-08の全PASS／exit0／tests_ran=true／parser_failed=false／timed_out=false／failure_messages空を確認。R-08は17テスト・2302assertion、失敗／保留0。既存描画画像の目視再評価と各過去JSONの意味の再検証は行っていない。

## 未実行・提出

ローカルではcore038／core041／invalid038／invalid041を重複実行せず、固定版の原CI artifactを直接検証した。既存R-01〜R-08／描画／ライフサイクルの全ローカル再実行、手動旧本編workflow、042独立付録は未実行。S2〜S5、新版完全codec／通常保存・復旧I/O／実ユーザー保存／通常戦闘UI接続は未実装・保証外。今回のレビュー範囲に未達・追加判断事項なし。

変更は046依頼書の状態行と本報告のみ。最終提出SHAとpush後の同一SHA全CIの終了結果は、自己参照の再コミットを避け最終応答に記載する。未終了を成功とは扱わない。

## 独自境界例の再現付録

上記対象045の新14artifactをverify_evidenceで `/tmp/review046/target-verified` へ展開後、次を新規パスで実行する。正常対照1と不正19の計20件。変異後は全manifestを更新し、意味の検証による拒否を確かめる。各別Pythonの実exitは、正常0／不正1に全件一致した。

```python
import copy,hashlib,json,pathlib,shutil,subprocess,sys
R=pathlib.Path('/workspace/RPG-maker'); T=pathlib.Path('/tmp/review046/boundaries');T.mkdir()
SOURCE=pathlib.Path('/tmp/review046/target-verified');SHA='e8d50eac2698ed603b64663c666af5608f607898'
names=['control','reordered_commands','six_commands','relative_engine','engine_split','negative_seconds','float_budget','false_timeout_int','argv_extra','missing_exit','same_false_fixture','same_reversed_cases','same_bool_count','same_missing_second','same_changed_history','duplicate_json_key','nonfinite_json','log_embedded_warning','duplicate_pass_suffix','profile_swap']
def save(p,v):p.write_text(json.dumps(v))
out=[]
for name in names:
 d=T/name;d.mkdir();i=d/'inputs';i.mkdir();o=d/'out';o.mkdir()
 for profile in ['baseline','041','latest']:shutil.copytree(SOURCE/('equipment-legacy-'+profile),i/('equipment-legacy-'+profile))
 p=i/'equipment-legacy-latest';ep=p/'execution.json';e=json.loads(ep.read_text());c=e['commands'][3]
 if name=='reordered_commands':e['commands'][1],e['commands'][4]=e['commands'][4],e['commands'][1]
 if name=='six_commands':e['commands'].append(copy.deepcopy(c))
 if name=='relative_engine':e['commands'][0]['command'][0]='godot'
 if name=='engine_split':c['command'][0]='/other/bin/godot'
 if name=='negative_seconds':c['seconds']=-0.001
 if name=='float_budget':c['timeout_seconds']=120.0
 if name=='false_timeout_int':c['timed_out']=0
 if name=='argv_extra':c['command'].append('--editor')
 if name=='missing_exit':del c['exit_code']
 if name=='profile_swap':e['profile']='041'
 if name in ['log_embedded_warning','duplicate_pass_suffix']:
  lp=p/'legacy.log';text=lp.read_text();text+='WARNING: injected\n' if name=='log_embedded_warning' else 'LEGACY_EQUIVALENCE_PASS: validation=142 upgrade=10 failures=0 extra\n';lp.write_text(text);c['log_sha256']=hashlib.sha256(lp.read_bytes()).hexdigest()
 save(ep,e)
 for profile in ['baseline','041','latest']:
  q=i/('equipment-legacy-'+profile)
  if name=='same_false_fixture':
   v=json.loads((q/'execution.json').read_text());v['fixture_sha256']={k:'f'*64 for k in v['fixture_sha256']};save(q/'execution.json',v)
  if name.startswith('same_') and name!='same_false_fixture':
   v=json.loads((q/'legacy.json').read_text())
   if name=='same_reversed_cases':v['validation'].reverse()
   if name=='same_bool_count':v['validation_count']=True
   if name=='same_missing_second':del v['upgrades'][0]['second']
   if name=='same_changed_history':v['upgrades'][0]['metrics_after']['events'].append({'fake':True})
   save(q/'legacy.json',v)
  if name=='duplicate_json_key':
   raw=(q/'legacy.json').read_text();(q/'legacy.json').write_text(raw.replace('{','{"validation_count":142,',1))
  if name=='nonfinite_json':
   raw=(q/'legacy.json').read_text();(q/'legacy.json').write_text(raw.replace('142','NaN',1))
  save(q/'sha256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in q.iterdir() if f.is_file() and f.name!='sha256.json'})
 code=f'import importlib.util,pathlib;s=importlib.util.spec_from_file_location("m",{str(R/"tools/run_equipment_ci.py")!r});m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.compare_legacy(pathlib.Path({str(i)!r}),pathlib.Path({str(o)!r}),{SHA!r})'
 with (d/'log').open('w') as f:r=subprocess.run([sys.executable,'-c',code],stdout=f,stderr=subprocess.STDOUT,timeout=10)
 expected=0 if name=='control' else 1;out.append([name,expected,r.returncode]);print(out[-1])
 assert r.returncode==expected
save(T/'results.json',out)
```
