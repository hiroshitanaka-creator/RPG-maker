# 037 装備基盤036の独立レビュー

## 作業前計画

対象 `dbceae8f68e18939a40ace71f3a24a1a1953e653`、基点 `98290621204a16cbd7b4f35155edde35a153728d`、037登録 `fade1a7c6943afcab84905265ddda057c2909869`、対象PR27。開始時は基点のworkブランチ、未コミット変更なし。指定リモートをfetchし037登録へcheckoutした。関連 `.agents/skills` はcheckout・/workspaceの双方に存在せず。追加委譲なし。

036依頼書・034設計・035候補と採用追記・装備原本・既存依存先・実コード・検査器・実行証拠を読む。基点から対象までの全変更パスと登録後の依頼書差分、実行証拠の3ファイルハッシュを照合する。指定Godot4.7.2を別取得し、対象完全SHAの一時checkoutでimport、新検査、R-01〜08・保護検査を独立再実行する。追加の固定入力・不正入力・カタログ異常の反証は一時領域だけで行い、本番を修正しない。対象CIと自分の提出CIを分けて確認する。

永続書込みは本報告と037依頼書自身の状態行だけ。保存・支給・実戦効果・通常ゲーム接続・CI接続は後続責任として区別する。main更新・マージ・036状態更新なし。

## 判定：差し戻し（本番修正なし）

正常カタログ・通常の正規化入力の装備投影は、新検査5394項目/400切替と独立追加検査で確認できた。ただし、**不正定義の初期化中断後に有効・成功と誤判定する問題（F1）**と、**request操作種別の型不正がSCRIPT ERRORになる問題（F2）**を再現した。既存APIの失敗契約と型不正拒否の範囲内の指摘であり、未採用機能の追加要求ではない。数値の表現範囲について低優先の指摘F3も併記する。

### F1／P2（中）：定義読込み中の型・必須キーエラーが成功扱いへ流れる

- 対象：`scripts/game/equipment_rules.gd:24`、`:30`、`:73`（後段 `:91`、`:160`、`:304`）。
- 再現条件：対象SHAのコードを一切変えない一時プロジェクトで、カタログの `legacy_source` を削除、nullに変更、または `jobs.warrior=null` とする。旧原本の `weapons[0]=null` でも再現。各ケースは元データに独立に1変更。
- 期待：型・必須項目を安全に検証して `definition_errors()` が非空となり、検証・計画・補正が明示的に失敗する。未完了のカタログを正常として公開しない。
- 実際：`_load_definitions` がSCRIPT ERRORで中断するが、`new()` はオブジェクトを返す。`definition_errors()==[]`、空装備の正規化stateに `validate_equipment_state()==[]`、`set_abilities []` の計画が `ok=true/reason_code=ok/candidateあり`。欠落legacy_sourceではカタログ0件、job nullでは14件の半初期化状態。job nullの `can_equip` はさらに123行でNil→DictionaryのSCRIPT ERRORを出す。
- 生ログ抜粋（4.7.2、終了0。終了0を成功とは扱わない）：

```text
SCRIPT ERROR: Invalid access to property or key 'legacy_source' on a base object of type 'Dictionary'.
 at: _load_definitions (res://scripts/game/equipment_rules.gd:24)
{"catalog_size":0,"definitions":[],"valid":[],"plan":{"ok":true,"reason_code":"ok","candidate":{...}}}
```

- 影響：呼出側が公開APIの「空エラー＝整合」「ok＝有効な候補」を信用すると、読込みに失敗した基盤を成功として扱える。通常ゲームはまだ未接続であり、現行配布カタログで発生したとは主張しない。入力defectをfail-closedにできていないことが差し戻し理由。
- 反証：カタログのファイル欠落、壊れたJSON、旧原本ファイル欠落はログにJSONエラーが出るが、definition_errorsは非空・計画falseになった。未知分類と小数1.5のbonusも明示拒否できる。すべての読込み失敗が誤成功になる、という指摘ではない。

### F2／P2（中）：request.kindの非文字列で実行時エラー

- 対象：`scripts/game/equipment_rules.gd:283`〜`:285`、呼出し `:308`。
- 再現条件：無改変の対象SHA・正常カタログ・有効な空装備stateに `plan_equipment_change(state,"a",{"kind":true})`。0、1.5、[]、{}でも同じ型比較エラー。
- 期待：Dictionary requestの不正型を通常の `invalid_request` として拒否し、SCRIPT ERRORなし・candidateなし・入力不変。
- 実際：`kind` をVariantのままStringと比較してSCRIPT ERROR。返却自体は `ok=false/reason_code=invalid_request`、candidateなし、入力不変であり、誤装備・状態破壊は再現していない。

```text
SCRIPT ERROR: Invalid operands 'bool' and 'String' in operator '=='.
 at: _request_valid (res://scripts/game/equipment_rules.gd:285)
REQUEST_BAD_KIND {"errors":[],"moves":[],"ok":false,"reason_code":"invalid_request"} input_unchanged=true
```

- 影響：公開APIに求めた型不正拒否がGDScriptの実行中断に依存する。エラーなしを要求する036機械検査をこの負例で拡張すると不合格になる。現行検査器の未知操作は文字列 `unsupported` だけで、この境界は未検出。

### F3／P3（低）：整数へ変換できないbonusを受理して符号反転する

- 対象：`scripts/game/equipment_rules.gd:54`〜`:57`、合算 `:405`。
- 再現条件：一時カタログだけで `guard_stitched_bracelet.bonuses.defense=1e30`。同品1個体を人間の装飾枠0へ割当てて補正取得。
- 期待：GDScript intで表現できない定義値を拒否し、指定値と別の値を有効補正として返さない。
- 実際：有限かつfloor一致の検査を通り、`int(value)` は `-9223372036854775808` へ変換。definition_errors空、所有検証有効、補正・計画ともokで同じ巨大負値を返す。SCRIPT ERRORなし。
- 影響と限界：同梱14品の小さな採用仮値には影響せず、外部定義の表現範囲の問題。商品バランス上限や新効果を決める提案ではない。F1/F2と別の低優先事項として親へ渡す。

## 固定差分・仕様・責任の照合

- 基点→036提出は29パス。新コード/データ/検査3件、候補書の採用追記、decision-logの今回3判断、036依頼書・報告、equipment-core証拠22件。範囲外の本番・原画・保護・既存検査・workflow差分なし。
- 036依頼書は登録 `79caadbe71e13ba7060aab598dc460035b04cab9` から自身の状態1行だけ変更。採用追記は旧本文/B案を残して末尾追加。Q1A「鉄の短剣」、Q2A、Q3Aと新8品の仮値ラベルが一致。旧6品の名前/ID/値/legacy辞書全体・封緘効果を維持し、旧原本自体は不変。
- `can_equip` は職別分類・枠・二刀流/両手持ち排他の判定。習得・形態別能力可否すべてを扱うAPIではない。全state側の習得/重複/容量検査と区別する。転職解放・不可逆・戦闘中禁止・形態遷移/能力使用可否はGameSessionの後続責任として、コード冒頭と036報告に明記されている。400切替の成功を実ゲームでの許可と扱わない。
- party/reserveを横断する個体所有、未知品/個体、重複、孤児、人物ID重複、版/型/枠、旧新混在、仲間所有品指定は通常カタログで拒否。成功時は台帳不変・本人と袋だけ変更、失敗時candidateなし。reserve本人を明示した操作は可能。無関係の保存全体の検証や移行はこのAPIの責任としない。
- 12人間職×5武器分類/防具3段階/装飾枠と8魔物職、全400投影切替、同率従前/従前枠順/item→instance順、負値実物、候補なし、袋最強・他人除外、二刀流解除返却、両能力排他、容量整理を検査器の固定期待と実実行で確認。武器分類は5つで刀を第6分類にしていない。
- 同名別個体の装飾1/2/3個は本人だけ合算。人間第3枠は拒否。主武器だけattack加算、防具+装飾は合算、現在HP/MP・HP0は不変。`encounter_effects.gd:245` の主武器差替え式と整合する導出であり、戦闘接続の成功を意味しない。
- 追加75assertではroot欠落・人物/所有キーの型・requestキーの型、partyの2人とreserve本人への操作、候補の台帳/袋/人物能力/装飾/無関係の深い配列を書き換えた際の元state不変、request配列とcandidateの分離、catalogの深い分離、中盤+形態の容量4→3を検査。assertは75成功だがkind負例でSCRIPT ERROR5件があるため、検査全体をPASSとはしない。

## ソース同一性

実装SHA `993929b43f311ec6beec8e340fe2c422274171f5` →対象036提出までの3ファイルはbyte一致。対象SHAのGit blobを独立にSHA-256計算し、036 `execution.json` の3件すべてと一致した。

| ファイル | SHA-256 |
| --- | --- |
| scripts/game/equipment_rules.gd | `54fa9ddd95bdf7a1142c7889bc12cbe2aa8b02b7f9ae4cc7352ee4330c9667b4` |
| data/equipment_rules.json | `9e52fb78f74834382c50671da1a6c4de01fe377017b78ae64db8ab0871e91892` |
| tools/check_equipment_rules.gd | `0361f34670ab0fdc96ae96b742b26fb214e93919a205994fe5d0f6a61f793de0` |

## 独立実行と対象CI

実行checkout `/tmp/equipment037-target` は対象完全SHAにdetach。標準godotは4.6.3のため検査には使わず、公式4.7.2 ZIPを新規取得した。ZIP SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実バージョン `4.7.2.stable.official.ed1daf0bf`。PATHの先頭は `/tmp/equipment037-bin`、XDG_CACHE_HOME/DATA_HOME/CONFIG_HOMEを専用/tmpへ設定。時間上限は変更していない。

一時検査の生成物と生ログは `/tmp/equipment037-evidence` に置き、永続成果物は本報告へ必要な再現入力・生出力・結果を収録する。対象checkoutの本番3ファイルは未修正。カタログ異常は別の最小プロジェクト `/tmp/equipment037-catalog` のデータコピーだけに注入した。追加検査器は本番リポジトリに追加していない。

対象CIは接続済みGitHubツールでrunのhead_sha/event/branch、各jobの終了状態を独立取得。CLIのGH_TOKEN認証は無効だったため使用していない。

| 036対象run（すべてhead_sha=dbceae8…） | イベント | 全job結果 |
| --- | --- | --- |
| [37558494616](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37558494616) | PR27 | 17/17 completed/success |
| [37558494611](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37558494611) | PR27 | 3/3 completed/success |
| [37558491652](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37558491652) | 036 push | 17/17 completed/success |
| [37558491610](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37558491610) | 036 push | 3/3 completed/success |

合計40/40成功。matrixの反対側用stepが条件skipなのは既存の分岐であり、job省略ではない。037作成前の同じdbceae8をheadとする037ブランチ起点のrun 37560530646/37560530647も一覧にあったが、036の40jobや037の最終提出CIに混ぜない。**新check_equipment_rulesは既存CIに未接続**なので、40job成功で5394項目を代用していない。


### ローカル再実行結果（対象SHA）

| 実行コマンド | 実測結果 |
| --- | --- |
| `timeout 600 godot --headless --editor --import --quit` | exit0、SCRIPT ERROR/ERROR:/WARNING:/Parse Errorなし |
| `timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd` | exit0、`EQUIPMENT_CORE_PASS: checks=5394 transitions=400 failures=0`、エラー警告なし |
| `python tools/run_locked_checks.py` | exit0、R-01〜R-08の全8件PASS。CI生ログの代用ではなく対象固定checkoutで直接実行 |
| `python tools/check_frozen_files.py`（前後） | 両方exit0、保護26件/一致26件 |
| `python tools/validate_assets.py --strict` | exit0、素材1154・音15・パレット3・字体2、問題なし |
| `timeout 60 godot --headless --path /tmp/equipment037-target --script /tmp/equipment037-input-probe.gd` | exit0、75assert失敗0だがSCRIPT ERROR5件（F2）。全体PASS扱い禁止 |
| `timeout 30 godot --headless --path /tmp/equipment037-target --script /tmp/equipment037-repro.gd` | exit0、F2のbool最小例を独立再現。入力不変true |
| `python /tmp/equipment037-catalog-run.py` | 正常対照+11異常ケースを別コピーで実行。各Godot exit0。F1/F3の誤成功と正常な拒否を上記のとおり区別 |
| F3の装着付き再現 `timeout 30 godot --headless --path /tmp/equipment037-catalog --script res://probe.gd` | exit0、補正defense=-9223372036854775808/ok=trueを確認 |
| `git diff --check`（037作業差分） | exit0 |
| `git diff --check 9829062… dbceae8…`（036固定差分） | exit2。R-01〜06/R-08の生ログ7件に末尾空行。コード問題ではなく参考所見。036報告の作業ツリーに対するdiff成功と固定全差分検査を区別 |

初回の独立入力プローブは検査側のbool/String比較に誤りがあり途中停止した。該当プロセスを停止し、一時検査側だけに型ガードを足して再実行した。初回を本番不具合の証拠や成功数へ含めていない。F2は修正後の75assertプローブと別の最小スクリプトの両方で本番285行に再現した。

Rの実測内訳（本番の判定器を変更していない）：

- R-01: PASS / exit=0 / tests_ran=True / parser_failed=False / tests=2 / assertions=765 / failed=0 / pending=0
- R-02: PASS / exit=0 / tests_ran=True / parser_failed=False / tests=5 / assertions=946 / failed=0 / pending=0
- R-03: PASS / exit=0 / tests_ran=True / parser_failed=False / tests=2 / assertions=73 / failed=0 / pending=0
- R-04: PASS / exit=0 / tests_ran=True / parser_failed=False / tests=1 / assertions=293 / failed=0 / pending=0
- R-05: PASS / exit=0 / tests_ran=True / parser_failed=False / tests=2 / assertions=79 / failed=0 / pending=0
- R-06: PASS / exit=0 / tests_ran=True / parser_failed=False / tests=2 / assertions=87 / failed=0 / pending=0
- R-07: PASS / exit=0 / tests_ran=True / parser_failed=False / A01〜A14と最終FIRST_REGION_PASSを判定
- R-08: PASS / exit=0 / tests_ran=True / parser_failed=False / tests=17 / assertions=2302 / failed=0 / pending=0

主要生ログのSHA-256（本報告の再現入力と出力抜粋を恒久証拠とし、一時ファイルの永続性には依存しない）：

- `equipment.log`: `b76b9d4e7bb4ce62fb074f718ca03b8da576923ec8ac1b8241d736f1bff610c3`
- `requirements.log`: `1d7888f05efc5f8dd0119fdf0f586c71139801a56c81bd398132001f3386409a`
- `input-probe.log`: `21e936f9bf68b1f77f54f56af76c20e24bf74313753780fe6fcc8f2d14180065`
- `request-kind.log`: `0b0c8a365bdb56adc59144295cb9a80767b6053c5c490bbd87b71c611aa764de`
- `catalog-missing_legacy_source.log`: `c2a9ac35ef3343d98458d8348743efe694d87bbcda6f10eb46d966284f31fba5`
- `catalog-job_null.log`: `e55323f4abc06ed030c6e38b584c879c81137fc8ccb97830d2ea42e11acd89e7`
- `overflow-detail.log`: `5e14f18ac20f0f3d0c6608d44f4cb9fde17b644a1e44626b884fac053a8175cd`

## 後続・未検証

通常ゲーム/保存移行/数量補填・一回支給/初期生成/能力習得/装飾実戦効果/両手持ち威力/HPMP上限縮小時切詰め/UI/CI新検査接続は未接続の後続範囲。採用機能を削る意味ではなく、今回の差し戻し理由にもしていない。人間試遊や正式数値調整も未実施。F1〜F3は再現・報告のみで修正していない。修正は新しい依頼の担当。main未統合、036状態未更新。

## 最小再現手順

指定4.7.2で、対象SHAの一時checkoutを `--path` にし、次のスクリプトを一時ファイルとして `--script` で実行する。F2は元データのまま、F1は別コピーのequipment_rules.jsonからlegacy_sourceだけを削除して同じスクリプトを実行する。F3は元データから守り縫いの腕輪のdefenseだけ1e30に変え、記載の2行を有効にする。各ケースの間はデータを元へ戻す。productionコードの差替えは不要。

```gdscript
extends SceneTree
const Rules = preload("res://scripts/game/equipment_rules.gd")
func _initialize() -> void:
    var r = Rules.new()
    var s = {
        "equipment_rules_version": 1,
        "equipment_stock": {"instances": {}, "bag": []},
        "party": [{"id": "a", "job_id": "warrior", "monster_form": "",
            "learned_abilities": [], "equipped_abilities": [],
            "equipment": {"weapons": [], "armor": "", "accessories": ["", "", ""]}}],
        "first_region": {"reserve": []}, "progress_flags": {"midgame_slots": false}}
    # F3だけ次の2行を有効にする。
    # s.equipment_stock.instances = {"bracelet": "guard_stitched_bracelet"}
    # s.party[0].equipment.accessories[0] = "bracelet"
    print("definitions=", r.definition_errors(), " catalog_size=", r.catalog().size())
    print("validation=", r.validate_equipment_state(s))
    print("plan=", r.plan_equipment_change(s, "a", {"kind": "set_abilities", "equipped_abilities": []}))
    print("bonus=", r.equipment_bonuses(s, "a"))
    print("bad_kind=", r.plan_equipment_change(s, "a", {"kind": true}))
    quit()
```

## 報告側の自己点検

037の状態と本報告のみが変更対象。問題を直すための本番・検査・保護ファイル変更はしていない。未実行と成功、投影と実ゲーム許可、既存CIと未接続新検査、対象CIと自分の最終CIを区別した。追加委譲・mainへの書込み/マージなし。

## 提出と037最終CIの扱い

本報告と037状態だけを `codex/task-037-review-equipment-core` へcommit/pushする。報告自身の完全SHAと、そのpushで生じる同一SHAの全job終了結果は、自己参照による無限の報告更新を避けて最終返答に記載する。この段落をもって、まだ発生していない自分のCI成功を主張しない。036の40jobと、037最終pushの20jobは別記する。作業前後に未コミット/未pushとmain参照を照合する。
