# 043 装備と保存移行の専用CI追加

## 作業前の確認と変更範囲

指定branch `codex/task-043-equipment-ci`、登録/開始SHA `fae00564540d58a256444940eada2fc45dc2a006`、基点main `a5cbeb0bb6f239958b2330d414afc0752c4fe36a` をfetch・照合した。開始時の未コミット/未pushはゼロ。登録との差分は043依頼書のみ。main・他branchへの書込み、マージ、追加委譲なし。

AGENTS、素材規約、職業・魔物化企画、素材台帳、036/038/041/042報告と指定原検査器を確認した。checkoutに `.agents/skills` は存在せず、`/workspace/.agents` は空。catalogの verification-before-completion を適用し、実終了値・件数・原ログ・CIの終了を根拠に判定する。`start.json` に開始状態・既存workflowの全SHA256・予算・計画を保存した。

変更は新 `.github/workflows/equipment-save.yml`、新 `tools/run_equipment_ci.py`、今回の `docs/verification/equipment-ci/`、043自身の状態行/本報告、decision-logの今回追記のみ。既存3workflow・検査・本番・data・素材・原画・test・scope-lock・契約・他依頼/報告・過去証拠にbyte差分はない。

## ジョブ・完全SHA・予算

全14jobはpush/PRで毎回実行する。権限は `contents: read` のみ。秘密追加なし。全job15分、matrixは `fail-fast: false`。失敗時にも保護照合とartifact保存を行い、欠落artifactをエラーにする。continue-on-error、検査省略、黙ったskip、上限延長はない。

| 対象 | 完全SHA |
| --- | --- |
| 固定036 | `dbceae8f68e18939a40ace71f3a24a1a1953e653` |
| 固定038 | `45a58b7faf09809d916954353a3a1fe0c3d2d035` |
| 固定041 | `8d3c1848d09b588fa41bcf6345d3aab6e12a5347` |
| 旧入口基点 | `821448b384d37edc041152beb5d6b6f560ad771d` |
| 最新 | pushは `github.sha`、PRは `github.event.pull_request.head.sha`。checkout HEADを完全SHAとして記録・再照合 |

| job名 | 全実行する原コマンドと個別上限 | 判定 |
| --- | --- | --- |
| equipment-core (036) | `godot --headless --path <checkout> --script res://tools/check_equipment_rules.gd` / 240秒 | 5394条件・400切替・失敗0 |
| equipment-core (038) / (041) / (latest) | 同上 / 各240秒 | 5394＋93＝5487条件・400切替・失敗0 |
| equipment-invalid (038) / (041) / (latest) | `python tools/check_equipment_invalid_definitions.py --source-sha <対象完全SHA> --godot <公式実体> --output <別出力>` / 原検査の各子30秒 | 202ケース・1576条件・202成功。全ケースのID・期待・件数・生ログを照合 |
| equipment-migration (041) / (latest) | `godot --headless --path <checkout> --script res://tools/check_equipment_save_migration.gd` / 各120秒 | 61ケース・2828条件・失敗0。全63観測（leaf改変の集計2件を含む）照合 |
| equipment-legacy (baseline) / (041) / (latest) | `godot --headless --path <checkout> --script res://tools/fixtures/equipment-save/legacy_equivalence.gd` / 各120秒 | 検証142入力・更新10入力、失敗0 |
| equipment-legacy-comparison | 3artifactを同一最新SHA・対象SHA・成功記録・fixture hash・生ログhashで確認し、旧出力を基点へbyte照合 | 固定/最新の双方が基点と完全一致。欠落/失敗/別SHAを拒否 |
| equipment-failure-propagation | `python tools/run_equipment_ci.py --suite self-test --latest-sha <HEAD> --output <別出力>` | 専用fixture35件：正常対照5件exit0、拒否30件は別Pythonの実exit1 |

Godotは公式 `4.7.2.stable.official.ed1daf0bf`。ZIPのSHA256は既存指定 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実行ファイルは `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。素材を使う各checkoutは先に `godot --headless --path <checkout> --editor --import --quit` を600秒以内で実行する。異常検査は原ハーネスが別の最小fixtureプロジェクトを使い、本プロジェクトのimportを要求しない。

wrapperの起動は `python tools/run_equipment_ci.py --suite <core|invalid|migration|legacy> --profile <段階|latest> --latest-sha <HEAD完全SHA> --godot <公式実体> --output <新出力先>`。原検査器のコマンド・子予算・assert・期待を改変しない。終了0だけでなく、SCRIPT ERROR/ERROR:/WARNING:/Parse Error/_FAIL:、PASS行の件数・重複・欠落、JSONの件数/失敗/ケースID/期待/版、異常各子の生ログと観測の一致を検査する。S1には対象SHAと別の出力先を環境変数で渡す。

各対象はdetached worktree、XDGは一時ディレクトリへ隔離する。原検査の固定名出力は使い捨てcheckoutだけに生成する。旧入口fixtureは041完成SHAの原本5ファイルを、基点・041・最新へ同じbyteで置く。基点や対象の実装からfixture・期待を作らない。出力先は新規のみで、既存証拠を上書きしない。

## 固定/最新の全assert対応

`assertion-map.json` は原検査5種類の静的assert呼出し位置323件を、完全SHA・ソースhash・行・関数・全文・固定job・最新job・分類・省略なしで列挙する。静的呼出し数をループ展開後の実行件数と混同しない。展開後は上表の件数と全ケースIDで機械照合する。

| 原検査の全条件群 | 完成版固定で保持 | 最新継続で実行 |
| --- | --- | --- |
| 036の指定版・定義/旧6品/採用8品、20職の可否、400切替、同率/負値/本人/party/reserve/所有/袋、手動/能力排他/両手持ち条件、補正/HPMP不変、deep copy、異常state、追加境界の全5394条件 | core (036)。当時の検査本文をそのまま使用 | core (latest)の旧5394。038原検査の旧全関数本文が036とbyte一致することも固定scopeで検証 |
| 038 F2の欠落/null/全不正型/未知kind、正常3操作、F3 native整数両端・既存/候補補正overflowの全93追加条件 | core (038)、core (041) | core (latest) |
| 038 F1の定義・旧参照・職原本の必須キー/型、F3 JSON数値の上下境界・丸め・負値・合算・正常対照の全202ケース/1576条件 | invalid (038)、invalid (041) | invalid (latest)。元ハーネスの全期待と各assert件数を固定038原証拠へ照合 |
| 041 run_case共通の入力/state/jobs/能力context/metrics/history不変、決定性、候補/監査参照分離、失敗候補なし/理由パス | migration (041)、原検査全実行 | migration (latest)、原検査全実行 |
| M01〜M08の数量・所有・順、合法従前、形式1P+2/JP/忘却、reserve/既得master、共通10一回性、加入fixture/同職再転職の生成0、M10型/履歴/進捗/311leaf等、M11未知版/所有/台帳/型/混在/overflowの全61ケース/2828条件 | migration (041) | migration (latest)。ケース・63観測のID/成否/leaf集計も確認 |
| 旧全体入口142入力、純粋upgrade/import/upgrade_rules/再更新/型/値/metrics/history/旧save-load往復10入力の全条件 | legacy (baseline)/(041)と出力比較 | legacy (latest)と出力比較 |
| 当時だけの担当範囲・未接続条件 | 036は登録79caadb→完成036、038は登録2547e91→完成038、041は基点821448b→完成コード041の完全SHA間を全treeで照合。保護・workflow・原画不変、036/038の既存接続ゼロ | 最新treeの将来の接続を禁止するscope照合には転用しない |
| 041「現GameSessionは新保存を拒否」の段階限定assert | 固定041で必ず保持 | 今回は最新もS1であるため原検査全実行。承認済みS2へ進む際は当該行を固定側に残し、新全状態/codec受理の正負検査へ分類・対応付けする必要がある。今回のassert削除/置換はゼロ |
| R-01〜R-08・既存固定受入/最新回帰/描画/ライフサイクル全検査 | 既存20jobのworkflow・上限・原検査をbyte不変で維持 | 最終提出SHAでも既存20jobをすべて実行。新14jobで代用しない |

S2以降の新機能を追加せず、承認済み新機能で置き換えた現在条件は今回ゼロ。全原assertを保持した。段階の未接続/担当範囲と、純粋APIの継続する動作条件を区別した。固定成功から最新成功を推定せず、両側の原出力を別々に保存する。

## 実検証・失敗伝播・原証拠

コード提出SHAは `f8ae80b34589f2c0f2c3b5ef3b6d9ddd2e86c94a`。ローカル初期の固定036/038と旧基点は登録SHAのwrapper起動、最新S1と既存R8等はコード提出SHAの別checkoutで実行した。各 `execution.json` に実対象・wrapper hash・コマンド・秒数・終了値がある。wrapperの初稿と完成版を区別する。

- 固定036：5394条件/400切替成功、固定038異常：202/202・1576条件成功。
- 最新正常：5394＋93条件/400切替成功、最新S1：61ケース/2828条件成功。
- 旧基点：142検証/10更新成功。前後byte照合の正式結果は専用CIの比較artifactを使う。
- `python tools/run_locked_checks.py`：R-01〜R-08全8件PASS、tests_ran=true、parser_failed/timed_out=false。既存各300秒上限。R-07はA01〜A14全成功、R-08は17テスト/2302assertion・失敗/保留0。
- `python tools/validate_assets.py --strict`：画像1154・音15・パレット3・字体2、問題0。`check_frozen_files.py`：前後26/26一致。
- 失敗伝播35fixture：実exit1、警告/構文エラー/FAIL表示、timeout、PASS欠落/重複/件数、正常装備/異常/S1/旧入口の欠落/重複/失敗を拒否。対照5件だけexit0。これらは本番結果の失敗を許容する仕組みではない。
- 別の欠落artifact fixtureで、比較wrapperの実exit1と `execution.json.status=FAIL` を確認した。
- 初回固定041の本体検査は61/2828でexit0だったが、wrapperがleaf集計観測に存在しないreason_codeを読んでexit1となった。wrapperを63観測の実形式へ直し、固定/最新を再検証した。初回FAILは `local/migration-041-first-failed/` に保持し、成功に数えない。原検査器・本番・上限を変えていない。
- `git diff --check`、既存workflow hash、担当外blob、decision-log過去本文のprefixを照合した。

原証拠は `local/` と `ci-code/`。生ログと大きいJSONはgzipで可逆保存し、`local/sha256.json` に展開後/保存後hashを記録する。CI artifactはZIP原byteを `.zip.gz` として可逆保存し、ZIP digestと全member hashを確認した。展開例は `gzip -dc <artifact>.zip.gz > /tmp/equipment-evidence.zip`。圧縮で検査内容/出力を省略しない。

## CI・最終提出

[draft PR #30](https://github.com/hiroshitanaka-creator/RPG-maker/pull/30)。コード提出SHAの専用CI push run `37612300178` は全14job終了・success、全14artifactの原ZIP digestと全member hash一致を確認した。旧比較の基点/041/最新の出力SHA256はすべて `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。原コマンドの実時間も全個別予算・job15分以内である。

`ci-code/results.json` はコードSHAの中間記録（新push14成功、既存/PRの一部未終了）であり、全CI成功とは扱わない。artifactのID/digest/全実行値は `ci-code/artifacts.json`。本報告を含む最終SHAでは新14＋既存20jobをpush/PRの双方ですべて終了まで照合する。自己参照で本文を書き換え続けず、最終応答とPR本文の「最終提出確認」に同一SHAの全6run・全68job・成果物を記載する。最終提出の確定記録はそこを正本とする。未終了を成功と報告しない。

未実装・未検証：S2〜S5の新版完全codec/全保存stats/通常save-load/原本保管と復旧I/O/通常解放・加入・転職・戦闘・UI接続、実ユーザー保存、手動旧本編workflow。042付録の独立レビュー専用59条件・91型ケース/273条件は、本043で指定された原検査器の専用CIとは別で、追加していない。新機能の空jobは作らない。追加判断事項なし。
