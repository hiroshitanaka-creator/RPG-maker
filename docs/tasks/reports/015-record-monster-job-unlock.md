# 015 魔物職の解放の分け方と4体の主：記録・読み取り調査報告

## 作業前に確認した3点

1. `git fetch origin main codex/task-015-record-monster-job-unlock` と `git ls-remote origin refs/heads/main refs/heads/codex/task-015-record-monster-job-unlock` を実行。main・親が作成したリモート作業ブランチとも `8081c9f89d2fb9305d29c230fe356f5275c8b0f5`。同SHAからローカルの指定ブランチを作り、`git merge --ff-only origin/main` は `Already up to date.`。作業前の未コミット変更なし、origin/mainに対する未pushコミットなし。
2. mainの `docs/design/characters/ner.md` は存在する。010は「確認済み」、011も確認済み。他の依頼書に「状態：作業中」の行はない。親の指示どおり、この一件だけを扱い、014・追加委譲・原画PR #15の作業は行わない。
3. `docs/experience-spec-v2.md` の変更前の節目6と未決事項（物語・世界）は下記のとおり。

```markdown
| 6 | 中盤 | 第2地方の島々 | モンスター職の解放 | 第2地方の奥地 |
```

```markdown
- [ ] 魔物職8種類を、一度に解放するか、何回かに分けて解放するか
- [ ] 魔物職の解放の場面の具体的な流れと台詞、ネルが引用する古い記録の言葉

- [ ] 城と城下町の正式名称（仮称：エルヴァ城下町・エルヴァ城）

- [ ] ゲームの題名（物語の細部が決まった後に決める）
- [ ] 地方・町・村の正式名称（最後の地「夕照の都」は確定）
- [x] 洞窟の人の名前と魔物の系統（2026年10月3日採用・mainへ実装済み。名称と本文は採用データ、検査は [導入の技術記録](first-region-intro-implementation.md) に分離。2026年10月4日の名前と甲殻の姿の確認は [洞窟の人物との出会い](#洞窟の人物との出会い2026年10月3日の追加作業) を参照）
- [ ] もう一組の冒険者4人の名前・性格の細部・具体的な登場場面と一時同行の実装方法（侵蝕で戻れなくなった仲間の治療法を探す4人組という目的は確定）
- [ ] 神々・精霊・死神・鍛冶の親方などの役と配置
- [ ] 旧本編80話のうち、どの話を本筋・寄り道・使わないに分けるか
- [ ] 第2地方のオアシスの村（仮）の新住人10人の具体案（名前・人物像・台詞・初の見た目・巡回担当・役割の細部）と店の商品内容
- [ ] 魔物職解放の未決の場面・条件（場所は第2地方のオアシスの村（仮）の祠、解放してくれる人物はネルと決定済み。組み立ては [ネルの人物記録](design/characters/ner.md) を参照）、遺跡の未採用の登場位置・2↔3階の穴の扱い・敵追加と既存36種検査との整合・鍵の名称と受取り方・鍵付き扉の接続先（[10月4日の採用範囲と段階順](#2026年10月4日の採用範囲と段階順) の後続依存。新しい品揃え・装備規則・効果・数値の採用は含まない）

```

## 作った文書と書き換えた箇所

- `docs/design/monster-job-unlock.md`：指定の冒頭文を置き、依頼書の「依頼者の決定」本文を原文のまま転記。「台詞の方向の例（未決）」の見出しを追加し、2つの例は未決のまま保持。
- `docs/design/characters/ner.md`：ネルが解放する4種類を追記し、8種類の分け方の未決を2026-10-04の決定と正本参照へ置き換え。既存の人物記録・組み立て・正式原画の記録は維持。
- `docs/experience-spec-v2.md`：担当指定の「進行表」「戦闘・職業・アビリティ・魔物化」「未決事項」だけを更新。節目6と8種の時期表記を4＋4へ合わせ、節目7の鍵は維持。分け方の未決を外し、残す未決5項目を重複なく記録。
- `docs/roadmap-v2.md`：「2026年10月4日の決定：魔物職の解放の分け方と4体の主」を追加。旧段階制作の未決表記は当時の記録として保持し、新節に今回の決定が優先することを明記。
- `docs/tasks/015-record-monster-job-unlock.md`：状態行だけを更新。本文は改変しない。
- `docs/tasks/reports/015-record-monster-job-unlock.md`：本報告書。

## 調査結果

調査対象は基準SHA `8081c9f89d2fb9305d29c230fe356f5275c8b0f5` のコード・データ・保護検査。すべて読み取りだけで、下の対応方法は後続依頼で検討する案であり、採用・実装はしていない。

### R-02：職業の修練

- `.scope-lock/spec.lock.json` のR-02のverifyは `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_actions.gd -gexit`。
- `test/unit/test_job_actions.gd` は全20職について、JPだけではマスターしないこと、職別成功行動回数との両条件、進捗の保存と転職後の保持、予約・不発・多段・二重反映の不加算、旧保存のマスター維持と未記録回数を補完しないことを検査する。盗賊10回・僧侶5回・獣系20回の固定条件も保持。
- `test/support/game_test.gd` の `new_game()` は `GameSession.new_game()` を使う。各職への変更は `change_job()`、修練は `tools/mastery_action_fixture.gd` の実行で検査する。通常進行の解放判定 `choose_job()` / `job_unlocked()` は使っていない。
- **解放の時期・地方・節目・8種の一括解放を受入条件にしていない。** 全職を検査できる基礎APIを前提とするが、ゲーム内の解放場面を前提とするものではない。後続で通常進行の入口に個別取得判定を追加し、基礎API・JPと行動回数の判定は維持する案なら、R-02を変えずに済む。

### R-04：魔物化

- `.scope-lock/spec.lock.json` のR-04のverifyは `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_monster_form.gd -gexit`。
- `test/unit/test_monster_form.gd` の `test_all_eight_masteries_transform_and_apply_defined_effects()` は魔物職を数え、各職ごとに独立した `new_game()` で `change_job()` → `master_job()` → 魔物化を検査する。能力値・技・誤った解除条件での不変・正しい条件での解除・検査総数8を確認する。
- **「8」は職業定義の総数であり、8種類を同時に取得するイベントの要求ではない。** 解放の時期・主撃破・受取りは前提としない。R-02でJPだけの不変も検査され、R-04の契約はJPと職別行動回数の両条件を保持する。
- `change_job()` 自体へ通常進行の新しいロックを入れると、両検査の初期状態からの転職を壊す。通常UIの `choose_job()` 側で個別取得を扱う案を優先し、基礎API・魔物化の効果・侵蝕・解除条件は変更しない。

### 現行の解放の仕組み・データと衝突点

| 読み取った箇所 | 現在の前提・今回の決定との関係 | 保護検査を維持する対応案（未実装） |
| --- | --- | --- |
| `scripts/game/game_session.gd:569` `change_job()` | 基礎API。職の存在・戦闘中・不可逆の人間職復帰を確認し、進行上の取得時期は確認しない。単体検査が直接使う | 基礎APIを維持し、通常操作で使う取得判定と区別する |
| `scripts/game/game_session.gd:588` `job_unlocked()`、`:609` `choose_job()` | 世界マップ型（`first_region_active()`）では先に転職全体のフラグを確認し、魔物職は単一の `monster_jobs_unlocked` で全系統を制御する。このフラグだけを立てると主からの取得前でも通常の魔物職が開き、4＋4・選択受取りに合わない。ただし精霊系には後述の追加条件もあるので「フラグだけで8種すべてが無条件に選べる」わけではない | ネルの4種類と主の4種類を別々の取得記録で判定する案。主は勝利と受取り確定を区別し、断っただけでは職を取得しない。主の取得を本筋・鍵・飛行の進行条件にはしない。再受取りの扱いは未決のまま残す |
| `data/job_progression_v1.json` の `advanced.spirit`、`game_session.gd:596-605,616-626` | 精霊系は既存の上級扱いで、不死系と僧侶のマスター・侵蝕60以上に加え、世界マップ型では `advanced_jobs_unlocked` も必要。主から受け取ると解放される新決定へ、この条件をそのまま重ねると、受取り後も使えない可能性がある。`_grant_job_unlocks()` が習熟だけで記録する上級職と、主から受け取る職も区別が必要 | 世界マップ型の精霊系取得を主の受取りとして扱い、旧本編の上級条件は旧経路に保持する案。受取り後も追加条件を残す案は今回の原文から確定できず、必要なら後続依頼で依頼者の判断を得る。保護検査を変更する案は採用しない |
| `scripts/game/game_session.gd:475-481` 保存の `actor.unlocked_jobs` 検証 | この配列は `job_progression.advanced` にある職だけを受理。スライム・獣・植物・甲殻・鳥・竜などの取得記録を単純に流用すると保存が不正になる | 上級職の配列を流用せず、進行フラグ等に別の個別取得記録を設け、通常取得・拒否・保存ロードを後続の検査で確かめる案。旧保存の取得済みマスター等の扱いも既存条件を維持して設計する |
| `scripts/ui/game_root.gd:1650-1667` | 通常の職業選択は `job_unlocked()` で未解放表示・転職可否を判定し、操作は `choose_job` に渡す | この入口と共通判定で取得の正負例を追加する案。画面表示だけで制限しない |
| `data/jobs/13_slime.json` 〜 `20_dragon.json` | 8職の定義は最初から存在する。ファイル自体に地方・節目・主撃破・受取り条件はない。職業総数8と能力・修練・魔物化の定義は今回の分割と両立する | 8職の定義とR-01の総数を維持し、進行上の取得だけを別に扱う |
| `scripts/game/game_session.gd:906-941` と全魔物職の `monster_form.release` | 現在の祠の清めは侵蝕89以下、侵蝕−30、魔物専用技消去、90以上の復帰不可。これは解放ではなく解除であり、今回の取得分割と別の仕組み | 解除の条件・数値・代償を維持し、新しい取得場面とは分ける |

`rg` で `scripts/`・`data/`・`world/`・`test/`・`tools/` 全体を読み取り検索した結果、`monster_jobs_unlocked` の本番の参照は上記判定1箇所で、trueを設定する本番処理は存在しない。現行は「一括解放の判定口はあるが、解放イベントは未接続」であり、新決定が既に実装されているとは報告しない。

### 第1地方・第2地方での実際の解放時点

- **第1地方**：`new_first_region()` → 城での通常謁見を最後まで進めた `finish_first_region_audience()`（`game_session.gd:285-292`）で `job_change_unlocked` と北の森の許可を立てる。これは基本の転職と装着の解放で、魔物職解放のフラグは立てない。洞窟の人物との出会いのデータ `data/first_region_gado_scenes.json` と会話確定処理にも、魔物職取得の設定はない。**第1地方では通常操作で魔物職を解放しない。**
- **第2地方の港・沿岸**：`world/region2_port.json` の祠の人物は通常NPCであり、`scripts/world/second_region_coast.gd`、`FirstRegionTravel` の航路と移動、`interact_first_region()` に魔物職を与える処理はない。港の祠は清めの対象にはなるが、新しい魔物職の取得ではない。
- **オアシスの村**：`world/region2_village.json:102-119` の祠（room 4）には現状 `oasis_elder`（村の長老）の通常会話がある。ネルの配置・解放場面は未実装。村への初訪問は行き先追加だけで、職業解放ではない（`scripts/world/first_region.gd:118-123`）。清めは既存の `at_purification_shrine()` が担当する。
- **第2地方の遺跡**：`world/region2_ruins.json` は4階と往復階段の下準備で、各階の `events` は空、`world_connection.enabled`・`encounters_enabled`・`boss_enabled` はfalse。`scripts/world/region2_ruins.gd` は地形と階段だけを扱う。主の戦い・声・選択・魔物職取得は未実装。既存の最下層のボス候補と不死系の主を同じものと決めつけず、主の具体的な配置と実装は後続へ残す。
- `GameSession.new_game()` の旧経路や検査用の初期状態には世界マップ型の時期制限が適用されない。この経路で職の基礎機構を検査できることを、通常の第1・第2地方で取得できる証拠にしない。

## 検査と実際の結果

- Godot公式4.7.2-stableをCIと同じURLから `/tmp/task015/bin/` に取得。zip SHA-256は `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` で `.github/workflows/ci.yml` と一致。実行版は `4.7.2.stable.official.ed1daf0bf`。既定4.6.3に期待値を合わせていない。
- `/tmp/task015/bin/godot --headless --editor --import --quit`：作業checkoutで終了0、`SCRIPT ERROR|ERROR:|WARNING:|Parse Error` なし。
- `python tools/validate_assets.py --strict`：終了0。画像1154件・音15件・パレット3件・字体2件、問題なし。
- `python tools/check_frozen_files.py`：終了0、保護対象26件・一致26件。
- 原文照合：新文書から冒頭・表題・「台詞の方向の例（未決）」見出しだけを除いた本文が、依頼書の決定本文と完全一致。依頼書は状態行を除き完全一致。コード・素材・データ・検査・保護対象2275件を隔離検査checkoutと全バイト照合して一致。終了0。
- R-01〜R-08は、既存 `tools/run_locked_checks.py` を隔離checkout `/tmp/task015/check` でそのまま実行する。元checkoutで許可外の検証記録を更新しないために隔離した。**初回はimport参照の不足によりR-01〜R-06・R-08がINVALID、R-07がFAIL（終了1）。成功とは扱わない。** 同じ4.7.2で隔離checkoutを取り込み直し、同じverify・判定・各300秒上限で再実行し、**R-01〜R-08すべてPASS、実行全体の終了0**。隔離importも終了0、エラー・警告なし。最終実測は2026-10-06 03:14:56 UTC。原記録 `/tmp/task015/check/docs/verification/scope-lock-current.json` のSHA-256は `7c579538ee3943f44b1cdbce70a7256cd4c6688de12aef0eafa799cbc7d734cc`。許可外のファイルへ証拠を追加せず、本報告に結果を残す。
- `git diff --check`：終了0。
- CI：記録・調査コミット `e083927eefb39a3414f65c332a0e422a536187ff` に対し、2026-10-06 03:39 UTCにpush全20件・PR全20件の **全40ジョブがcompleted/success** であることをGitHubコネクタのチェック一覧とジョブ一覧で確認。PR起動の2ワークフローもcompleted/success。`gh auth status` / `gh run list` はGH_TOKENの認証失敗/Forbiddenだったため、認証済みGitHubコネクタを使用した。実行中のログ取得は404だったが、終了後にGodotジョブログを取得できた。検査の削除・skip・緩和・時間上限の変更はない。

| 要件 | 結果・終了コード | 実行された検査・assertion |
| --- | --- | --- |
| R-01 | PASS・0 | 2テスト・765assertion、失敗0・pending 0・invalid false |
| R-02 | PASS・0 | 5テスト・946assertion、失敗0・pending 0・invalid false |
| R-03 | PASS・0 | 2テスト・73assertion、失敗0・pending 0・invalid false |
| R-04 | PASS・0 | 1テスト・293assertion、失敗0・pending 0・invalid false |
| R-05 | PASS・0 | 2テスト・79assertion、失敗0・pending 0・invalid false |
| R-06 | PASS・0 | 2テスト・87assertion、失敗0・pending 0・invalid false |
| R-07 | PASS・0 | A01〜A14すべてPASS、FIRST_REGION_PASS: checks=14 |
| R-08 | PASS・0 | 17テスト・2302assertion、失敗0・pending 0・invalid false |

### CIのURLと全ジョブの結果

対象SHA：`e083927eefb39a3414f65c332a0e422a536187ff`。独立レビュー用 [draft PR #22](https://github.com/hiroshitanaka-creator/RPG-maker/pull/22) はmain未統合。

| 起動 | ワークフロー | URL | 結果 |
| --- | --- | --- | --- |
| push | CI | [37407973225](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37407973225) | 3/3 completed/success |
| push | 006 固定受入と最新回帰 | [37407973232](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37407973232) | 17/17 completed/success |
| PR | CI | [37408016092](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37408016092) | 3/3 completed/success |
| PR | 006 固定受入と最新回帰 | [37408016117](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37408016117) | 17/17 completed/success |

| ジョブ（全20種類） | push | PR |
| --- | --- | --- |
| Godot・凍結受入テスト | success | success |
| acceptance-and-regression (fixed) | success | success |
| acceptance-and-regression (latest) | success | success |
| lifecycle-audit | success | success |
| normal-input-and-rendering (fixed, details) | success | success |
| normal-input-and-rendering (fixed, journey) | success | success |
| normal-input-and-rendering (fixed, restart-0) | success | success |
| normal-input-and-rendering (fixed, restart-1) | success | success |
| normal-input-and-rendering (fixed, restart-2) | success | success |
| normal-input-and-rendering (fixed, restart-3) | success | success |
| normal-input-and-rendering (fixed, restart-4) | success | success |
| normal-input-and-rendering (latest, details) | success | success |
| normal-input-and-rendering (latest, journey) | success | success |
| normal-input-and-rendering (latest, restart-0) | success | success |
| normal-input-and-rendering (latest, restart-1) | success | success |
| normal-input-and-rendering (latest, restart-2) | success | success |
| normal-input-and-rendering (latest, restart-3) | success | success |
| normal-input-and-rendering (latest, restart-4) | success | success |
| 素材検査 | success | success |
| 試遊前の通常戦闘・案内・画面・復帰検査 | success | success |

本報告確定のコミットは、検査済み実装コミットから本報告書と依頼書の状態行だけを更新する。確定後のHEADでもCIを全ジョブ確認して提出する。確定後のSHA・CIのURLと結果は、[PRのChecks](https://github.com/hiroshitanaka-creator/RPG-maker/pull/22/checks) と提出メッセージで、上に記録した検査済みSHAの証拠と区別して示す。

## 自己点検

1. 決定原文・未実装の冒頭文・例（未決）の区別：PASS。
2. ネルの4種類と未決行から決定行への更新：PASS。
3. 体験仕様の担当3節と未決5項目：PASS。
4. roadmapの指定決定節・正本参照：PASS。
5. 調査結果の記録、変更範囲：本報告に記載。担当の6文書に限定し、コード・データ・素材・検査・保護ファイル・story-outline・他の依頼書と報告書・旧STATUS・director-next-preparationは変更しない。`git diff origin/main...HEAD --name-only` と、担当6ファイルの完全一致照合、体験仕様の節単位照合がすべてPASS。変更された節は担当3節だけ。`git diff --check` も終了0。
6. R-01〜R-08・保護照合・全CI：R-01〜R-08は全PASS、保護26件一致。上記SHAのCIはpush・PR各20ジョブすべてcompleted/success。PASS。

## 提出と未達・未検証

- 最新のユーザー指示により、依頼書・報告書を作業ブランチ `codex/task-015-record-monster-job-unlock` に置き、**mainにはマージしない**。親の独立レビューへ提出する。依頼書本文のmain反映の完了条件は編集せず、今回の提出条件がmain未統合であることをこの報告で区別する。
- 記録と読み取り調査の範囲を超える解放イベント・主との戦い・台詞の制作、014の先取りは行っていない。未決5項目は未決のまま。実装はこの依頼の成果ではない。
- 記録・調査コミット `e083927eefb39a3414f65c332a0e422a536187ff` は指定ブランチへcommit・push済み。検査結果・CI全ジョブのURLと結果は上に記録した。報告確定後のHEADの全CIも終了まで確認し、提出メッセージに最終SHAと結果を記録する。main反映と親の独立レビューは今回の提出後の工程であり、今回の作業では未実施。

## 提出前の追加点検

報告確定コミット `2de28e6d752e4cf349d877bd26f2bd097ce5bfa5` の後、`git diff --check 8081c9f89d2fb9305d29c230fe356f5275c8b0f5...HEAD` が新文書末尾の余分な改行を検出して終了2。`monster-job-unlock.md` 作成時に原文の後ろへ追加した改行1文字だけを取り除いた。決定本文は、追加見出しを除いた全内容が依頼書原文と完全一致のまま。修正後の基準SHAからの全差分検査は終了0。この補正と本報告の追記も同じ作業ブランチへcommit・pushし、そのHEADの全CI結果を提出メッセージに記録する。
