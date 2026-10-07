# 036 装備基盤の実装報告

## 作業前の計画・境界

基点main `98290621204a16cbd7b4f35155edde35a153728d`、登録 `79caadbe71e13ba7060aab598dc460035b04cab9`、作業ブランチ `codex/task-036-equipment-core`。開始時の未コミット変更なし。mainに対する未push扱いの登録コミットは依頼書の1件だけで、既にリモートに存在する。関連する checkout `.agents/skills` と `/workspace/.agents/skills` は存在せず、追加skill・追加委譲なし。

1. 固定期待の正負検査を先に作り、未実装時の失敗を保存。
2. 既存6武器の読取り互換、新8品、20職の可否、全人物の個体所有検証を実装。
3. 入力不変の手動装備・職変更・能力変更と補正集計を実装。
4. 指定Godot 4.7.2で追加検査、素材取込み、既存R・保護照合を実行。
5. 許可されたファイルだけcommit/pushし、draft PRと最終SHA全CIを確認。

変更可能範囲は036依頼書の担当ファイルに限定。既存接続・保存・UI・戦闘・支給・移行・workflow・保護検査・原画は触らない。職解放・不可逆・戦闘中禁止は後続のGameSession責任であり、この計画器の成功は実ゲームの転職許可を意味しない。

## 変更ファイル

- `data/equipment_rules.json`：規則版1・カタログ版1、12人間職/8魔物職、既存6品の互換原本、新8品の仮値。
- `scripts/game/equipment_rules.gd`：定義整合・所有・枠/型/版・職別可否、純粋変更計画、補正導出。
- `tools/check_equipment_rules.gd`：本番から期待を生成しない固定fixture、20×20職切替、正負例。
- `docs/design/equipment-content-options.md`：採用原文・日時・名称訂正・仮値を追記。歴史的なB案/旧本文を保持。
- `docs/decision-log.md`：入力構造・能力整理・主武器補正の技術判断と戻し方。
- `docs/tasks/036-equipment-core.md`：自身の状態行だけ。
- 本報告、`docs/verification/equipment-core/`：未実装時の失敗、指定版実行、R/素材/保護、固定SHA/ソースハッシュ、差分の証拠。

Godotが生成する新2スクリプトの `.gd.uid` は担当パス外なのでコミットしていない。スクリプトはパスpreloadで読み込めることを別checkoutの検査で確認する。

## 実API契約

`preload("res://scripts/game/equipment_rules.gd").new()` で生成する独立 `RefCounted`。既存ゲームはこのスクリプトを読込まない。コンストラクタは本カタログ、旧 `data/integrated_rules.json` と既存 `data/jobs/*.json` を読取り、6品の全互換辞書・ID/名前/攻撃値と20職のtypeを照合する。保存stateの読込み・書込みやGameSessionへの依存はない。

| public関数 | 型・結果・責任 |
| --- | --- |
| `definition_errors() -> Array` | 定義の対象 `target` と `reason_code`。空なら整合。deep copyで返す |
| `catalog() -> Dictionary` | `{item_id: definition}` のdeep copy。`kind/weapon_category/armor_rank/bonuses/provisional`、既存6品だけ `legacy` に旧原本全フィールド（tags・on_hit含む）。JSON由来のrankは整数相当の数値、bonusesはintへ検証変換 |
| `can_equip(job_id: String, equipped_abilities: Array, item_id: String, slot: String, index: int = 0) -> bool` | `slot` はweapon/armor/accessory、indexは0始まり。20職の可否・能力排他・武器枠上限を判定。未知品/職・不正枠false。人物の習得・職変更許可はこれだけでは判定しない |
| `validate_equipment_state(state: Dictionary) -> Array` | 全party/reserveの所有・個体・版/型/枠・能力の習得/重複/容量/排他を検査。各エラーは `target/reason_code`。空配列なら装備投影として有効 |
| `plan_equipment_change(state: Dictionary, actor_id: String, request: Dictionary) -> Dictionary` | 成功：`ok=true/reason_code=ok/candidate/moves/stats_before/stats_after`。失敗：`ok=false/reason_code/moves=[]/errors`、candidateなし。入力state/request・他人物・個体台帳・非装備情報は不変。候補は共有参照なし |
| `equipment_bonuses(state: Dictionary, actor_id: String) -> Dictionary` | 成功：`ok/reason_code/bonuses={hp:int,mp:int,attack:int,defense:int}`。attackは主武器だけ、armor/accessory補正は本人に合算。hp/mpは上限の加算値を返すだけ。無効state/人物は失敗 |
| `two_handed_active(state: Dictionary, actor_id: String) -> bool` | 有効状態、人間職、能力装着、blade1本、二刀流なしの発動条件を導出。威力・打数・戦闘処理は変更しない |

### 正規化stateの必要キー

- root：`equipment_rules_version: int=1`、`equipment_stock: Dictionary`、`party: Array[Dictionary]`、`first_region.reserve: Array[Dictionary]`、`progress_flags.midgame_slots: bool`。reserveがない独立入力でも明示的な空配列を渡す。
- stock：`instances: Dictionary{非空String instance_id: 既知String item_id}`、`bag: Array[String instance_id]`。
- 全人物：`id: 非空String（全人物で一意）`、`job_id: 既知String`、`monster_form: String（空または既知魔物職）`、`learned_abilities/equipped_abilities: Array[非空String]`、`equipment: Dictionary`。
- equipmentはちょうど `weapons: Array[String]`（空/1/二刀流時2、空要素なし）、`armor: String`（空可）、`accessories: Array[String]`（3要素固定、空可）。人間の3番目は空、魔物職は武器防具空。
- 容量は既存方式の `min(4, (midgame_slots ? 3 : 2) + (monster_form非空 ? 1 : 0))`。職typeとmonster_formは別入力。旧 `integrated.armory` と人物の旧 `integrated.weapons` の混在を拒否。旧state・未知版を自動移行しない。
- 残りのゲーム情報は複製して保持する。これは保存文書全体の検証器ではなく、形式2・修練規則・能力カタログ/形態別使用可能性・進行の全検証は接続側の責任。

### requestと変更の範囲

| request | 動作 |
| --- | --- |
| `{kind:"equip", slot:String, index:int, instance_id:String}` | 空Stringで解除、袋の個体を手動装着。同じ本人の同種枠間は交換可能。他人/reserve所有は拒否（reserve本人を明示対象にした操作は可能）。武器配列は順を保持して詰める。主武器なしでindex1へ飛ばす指定は拒否 |
| `{kind:"change_job", job_id:String, monster_form?:String, equipped_abilities?:Array[String]}` | 許可済みの職・任意の形態/整理済み能力を候補へ。能力配列省略時は既存順の先頭を新容量まで保持。能力検証後に本人の従前装備＋袋から自動選択。負値合法実物も選択。装飾の1/2は保持、人間復帰時3を袋へ |
| `{kind:"set_abilities", equipped_abilities:Array[String]}` | 完全な装着配列を検証して置換。二刀流が外れたら第2武器だけ返却。能力追加だけでは最強装備へ変更しない。二刀流/両手持ち同時、未習得、重複、容量超過を拒否 |

余分なrequestキー、不正型、未知操作を拒否する。計画器は新習得や装備生成をせず、全instanceの総数と所有を保存する。強さ同率は従前instance・従前枠順、最後にitem_id→instance_idで固定。袋は既存順を保持して引出し、返却品を従前枠順で末尾へ。movesはinstance_id順、`{instance_id,from,to}`、場所はbagまたは `party|reserve/actor_id/slot/index`。

**責任分界**：通常/強制の職変更を許可するか、職解放、不可逆、戦闘中禁止、形態遷移・能力の使用可能性、状態世代、履歴、一括適用は後続GameSessionが担当する。400職切替は装備投影だけのfixtureであり、不可逆人物の実ゲーム人間復帰や未解放職への転職成功を意味しない。

## 採用と仮値

2026-10-07 10:26 JST のQ1A（鉄の短剣へ訂正）/Q2A/Q3Aを候補書に追記済み。既存6品を維持。新5品と装飾3品を登録し、攻撃+0、防御+1/+2/+3、HP+10/MP+2/防御+1に `provisional: true` を付けた。萎縮免疫品・効果は登録しない。装飾の同名別個体は1/2/3個を合算。同一個体の複数所有は拒否し、人間3枠目は無効。HP0でも補正導出は現在値を変更せず、回復・蘇生を行わない。

## 指定版での実行証拠

実装・検査器の最終コードSHAは `993929b43f311ec6beec8e340fe2c422274171f5`。同じ環境内の別checkout `/tmp/equipment-036-checkout` をこのSHAにdetachして実行した。後続の報告コミットでは本番コード・データ・検査器を変更しない。実行SHA、完全なソースSHA-256、コマンド/終了コードは `execution.json`、件数と失敗は `checks.json`、生ログは `pinned-check.log`。

- 実測版：`4.7.2.stable.official.ed1daf0bf`（Engine表示 `4.7.2-stable (official)`）。既定4.6.3は検証に使用していない。
- 公式ZIP：`https://github.com/godotengine/godot-builds/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip`。
- SHA-256：`cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`。既存CIの固定ハッシュと一致。
- 実行時だけ `PATH=/tmp/equipment-bin:$PATH` で上記実物へのgodotを選択。書込み可能な `XDG_CACHE_HOME/XDG_DATA_HOME/XDG_CONFIG_HOME` を `/tmp/equipment-*` に設定。エンジン・既存workflow・時間上限は変更しない。

| コマンド | 結果・証拠 |
| --- | --- |
| 実装前 `timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd` | exit1。固定期待の検査器を先に保存し、未実装equipment_rules.gdのpreload失敗を記録（`red.log`）。assertion実行成功とは扱わない |
| `godot --headless --editor --import --quit` | 作業checkoutと固定checkoutの双方でexit0。`import.log/pinned-import.log`、エラー/警告なし |
| `timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd` | 固定SHAでexit0、`EQUIPMENT_CORE_PASS: checks=5394 transitions=400 failures=0`。SCRIPT ERROR/ERROR:/WARNING:/Parse Errorなし |
| `python tools/run_locked_checks.py` | 固定SHAで既存verifyコマンドをそのまま実行、exit0。R-01〜R-08全PASS。`requirements.json/requirements.log/R-01.log`〜`R-08.log`。R-07はA01〜A14全PASS、R-08は17テスト/2302assertion、失敗/未実行/構文エラーなし |
| `python tools/validate_assets.py --strict` | exit0、素材1154件・音15件・パレット3件・字体2件、問題なし（`assets.log`） |
| `python tools/check_frozen_files.py` | 前後ともexit0、保護26件/一致26件（`frozen.log/frozen-after.log`） |
| `git diff --check` と固定SHAの変更範囲監査 | 成功。許可された本番3新規ファイルだけ追加。既存コード/保存/戦闘/新規開始/原画/保護/検査/workflowに差分なし（`scope.json`） |
| `git push origin HEAD:refs/heads/codex/task-036-equipment-core` | 実装SHAのpush成功。報告・証拠コミットも同ブランチへpushする |

`gh auth status/gh api` は既存CLIの認証/API接続が利用できなかった。Gitのfetch/pushと接続済みGitHubツールは実際に成功したので、PR作成・CI確認にはそのツールを使用した。

## PR・最終提出の確認先

[draft PR #27](https://github.com/hiroshitanaka-creator/RPG-maker/pull/27)、head `codex/task-036-equipment-core`、baseは指定main `98290621204a16cbd7b4f35155edde35a153728d`。mainマージなし、追加委譲なし。

この報告を含むコミット自身の完全SHAと、そのpush後に終了する同一SHAの全CIジョブ結果は、PR #27本文の「最終提出確認」に記録する。そこを最終提出情報の正本とする。報告書内の上記SHAは実際に別checkoutで実行した本番・検査器のコードSHAであり、報告後のSHAのCI成功を先取りした記録ではない。最終確認では最終HEADの本番3ファイルのハッシュが `execution.json` と一致すること、未コミット/未pushがないこと、main未変更を確認する。

## CI未接続・後続の残り

**新検査のCI組込みは未実施**。現行CI成功だけでは新検査の成功証拠にならず、上記指定版の固定実行を別途保存した。組込みが必要な場所は `.github/workflows/ci.yml` のGodot検査側。承認された後続作業で、同じ4.7.2と240秒以内の新コマンド、終了0/PASS件数/失敗0/エラー警告なし判定、`docs/verification/equipment-core/checks.json` とログの保存を追加する。既存job/コマンドの予算は維持し、予算内に収まらない場合の別job化は後続で判断する。今回 `.github/` は変更しない。

この段階の独立基盤以外は未接続・未検証：新規開始/加入/一回支給、Q2A数量保持・不足補填・形式1専用支給の実移行、移行前保存バイト保持・原子的保存I/O、通常/強制転職の実ゲーム入口、職/形態/能力の既存整理との接続、戦士マスターの両手持ち習得、両手持ち威力・二刀流各打・装飾の実戦効果、HP/MP上限縮小時の切詰め、通常UI、旧保存互換、全接続後の公開、数値調整・正式価格/商品配置。採用機能の削除や全装備機能の完成を意味しない。

追加の作品内容・名前・効果・規則を決めていない。今回の実装範囲について依頼者の新しい判断が必要な事項はない。親による実物確認とAstraレビューはこの報告の受入後段であり、実施済みとは書かない。ルッカ自身の指揮記録は変更していない。
