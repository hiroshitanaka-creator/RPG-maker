# 016 F1固定参照・F2カウンター裏NPCの差し戻し修正

## 対象と変更

- 開始 `cc86765d7b5bba158dca8b828a626aad98610f12`、main `5be5aeecf1a3c73a5242d18f75975eb02fa55cda`（開始時に祖先）。開始時未commit0、無関係な未push0。
- 機能完成 `6706397e2674ffa382852e0f33ce23edf5c76634`。treeは `docs/verification/task-016/completed-audit.json` に保存。固定記録/毎回の範囲監査を追加した提出コード `9f1a18892273ac06d9776d2ddf8dbcc1c6423453`。
- 原画、本番scripts/world/data/assets、test、.scope-lock、addons、project.godot、AGENTS、既存ci.yml、固定006/009/012の検査器・完成記録は開始点からGit blob不変。保護26/26。証拠 `docs/verification/task-016/unchanged.json`。
- 変更は新規 `tools/check_task016_fixed_anchor.py`・`tools/test_task016_fixed_anchor.py`・`tools/check_task016_scope.py`、最新 `tools/check_region2_village_regression.gd`、正負例 `tools/test_task009_lifecycle.py`、専用workflowへの必須追加、assertion-map.mdのS06/A082補足、decision-log、016状態/報告、016専用証拠のみ。撮影器の実在名は `tools/capture_task009_village_regression.gd`。本番機能、007以降の作業は変更していない。全変更ファイル一覧は `docs/verification/task-016/changed-files.json`。

## 修正前の同条件再現

`docs/verification/task-016/before/` に実測を保存。

- F1：012状態行だけ違う子commitへmanifestのSHA/tree、workflowのenv/checkoutを同時変更し、実checkoutも子commitにする。変更していない元012検査器は終了0、17/17 PASS。コピーの完全SHAと所要秒はf1.json。013の自己一致を再現した。
- F2：元013と同じ、item室2のeventsのみをNPC `[8,4]` に変更。固定版Godotで旧回帰は終了1、7644 checks、20.268秒。失敗はBFSの客側・家具前後到達と本番移動経路 `[8,4]` の2件。地形・ゲームコード・旧検査器はこの実験で変更していない。

## F1の修正と反証

新照合器の定数 `TRUST_RECORD = 9e647b3d6d0f91b061f7de974dbb5411937a2bb9` から当時記録をgit showする。この既存信頼基点から得る012完成SHA `c327e7c439c9c8c8f1fd640e6cda6df7550fb26a` / tree `1a128f883bd555653bd9eea3082c09b875c1f7e5` が期待値である。最新manifest自身、CLI、文書、git logから期待値を生成しない。

最新manifestの全記録、workflowのenvと別checkout参照、固定012実checkoutのHEAD/tree/当時ソースのdirtyを照合する。欠損時のlatestへのfallbackはない。旧012の17件は当時の別checkoutで無変更・必須実行し、新照合と14正負例を追加した。

14件は承認済みHEAD、状態子commitへのmanifest+workflow+checkout参照同時付替え、片側だけの変更、誤tree、不正/不存在SHA、記録フィールド欠損/不正JSON/ファイル欠損、checkout欠損、実checkout付替え、当時検査器改変、信頼基点オブジェクト欠損を含む。`anchor-cases/summary.json` に拒否理由と入力SHAを保存。元F1の**実checkoutも同時に付替えた完全CLI実行**は終了1・独立信頼基点不一致を要求し、`anchor-cli/simultaneous-rebinding.json` / `.log` に保存した。

## F2の修正と反証

最新 `maps -> target_checks` は非占有の固定目標に従来どおりBFSと本番全一歩を要求する。家具裏のNPC占有目標は、リンクを通らず同室の隣接へ通常歩行し、位置を確認してNPC側を向く。足元通行拒否、実移動拒否、拒否前後の**全状態一致**を要求する。客側/front・アーチは占有による代替を認めない。8扉・全床/隣接・入口出口・20保存後の実退出・5別プロセスは維持した。

外観 `[20,25]` の元7正負例を保持し、店内 `[8,4]` 正例、通常入力/描画正例、占有無視、拒否時coins破壊、客側 `[8,6]` 閉塞、室外扉 `[8,11]` 閉塞を追加した。負例は終了1・実assertion失敗を要求し、timeout/parse errorを成功扱いしない。F2ローカルの実測は `f2-local/`、CIの全13件は後掲artifactに保存する。

現在の撮影器のfront `[8,6]`、item behind `[4,2]`、weapon behind `[13,3]` はNPC `[8,4]` と重ならない。経路は既存本番UIのwalkable_cellsから求めるため、撮影器変更は不要と判断した。NPC付きjourney全28枚、人物全画素/部分遮蔽、扉と村外退出を180秒以内に必須再実行する。

## 元assertion・016範囲・予算

元135箇所＝当時だけ10・最新継続121・007置換4、未分類0。固定006で当時の全項目を毎回実行。`assertion-map.json` は元ソースとの完全一致を要求する既存列挙器を保つため無変更。S06/A082、A052/A053/A054、撮影A017/A024の詳細は同map.mdと `task-016/assertion-correspondence.json` に記録した。最新maps/歩行helperと撮影の対応先は存在し、正負例が意味を検証する。007の6人・会話・宿・祠サービスは未着手/未検証で、固定側の無反応4箇所も残る。

016の範囲は機能完成6706397の別checkoutだけを開始点cc86765と比較する。最新HEAD全体へ016の許可範囲を適用しない。後続状態編集・依頼書登録・両方同時・別範囲編集の各子commitで監査対象と結果不変を確認し、完成差分内の本番改変は拒否した。6件 `scope-checks.json`。006/009/012のALLOWED・固定記録を拡張していない。

専用workflowは既存各job15分、import600秒、各Godot/描画180秒、旧012 180秒、内部180000ms/600移動/3000入力/300ターンを維持。新照合・14反証・016範囲反証も各180秒の必須追加。通常CI35分/25分/素材未指定、R各verify300秒も不変。既存workflowの全行が追加のみで保持されることを完成差分で監査する。項目削除、黙ったskip、continue-on-error、時間延長は追加していない。既存matrixの反対世代の条件分岐は維持し、未実行を成功の根拠にはしていない。

## 実行コマンドと結果

- Git fetch/ls-remote：最新mainと登録SHAを確認。mainは既に取り込み済み。
- 固定Godot ZIPを取得・SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と照合。version `4.7.2.stable.official.ed1daf0bf`。
- `timeout 600 <固定Godot> --headless --path . --editor --import --quit`：終了0、SCRIPT ERROR/ERROR/WARNING/Parse Errorなし。commit前importであり、これだけでSHA付き回帰成功とは扱わない。
- `timeout 180 python tools/check_task016_fixed_anchor.py --fixed012-path <c327e7c-checkout> --latest-sha 9f1a188...`：終了0、独立SHA/tree一致。
- `timeout 180 python tools/test_task016_fixed_anchor.py --fixed012-path <c327e7c-checkout> --latest-sha 9f1a188...`：終了0、14件PASS。
- `timeout 180 python <c327e7c>/tools/test_task012_pinned_audit.py --current-path . --fixed009-path <ce07fda> --completed012-sha c327e7c... --latest-sha 9f1a188...`：終了0、17件PASS。
- `timeout 180 python tools/check_task016_scope.py --completed-sha 6706397... --fixed-path <6706397-checkout> --latest-sha 9f1a188...`：終了0、6件PASS。
- `python tools/check_region2_village_regression.py --commit 9f1a188... --godot <固定Godot>`：終了0、runtime7662/20保存、restart10/27/38/52/44全部PASS。`local/latest/` は今回のroot結果と保存入力のみを保管し、古い描画結果を流用しない。
- `PATH=<固定Godotのあるdir>:$PATH python tools/run_locked_checks.py`：各verifyの上限300秒を保持し、R-01〜R-08全PASS。`local/locked/`。最初に環境既定4.6.3で誤って実行した結果はR-08 FAILであり、指定版の合格に数えない。固定版をPATHへ置いて全8件を再実行した。
- `python tools/check_task009_assertion_map.py`：135箇所・未分類0・fixture固定006。`python tools/check_frozen_files.py`：26/26。`python tools/validate_assets.py --strict`：終了0。`python -m py_compile` / `git diff --check`：終了0。
- 一時cloneが/tmp容量へ達した初回固定016checkoutは失敗であり、成功に数えない。作業コピーを/workspaceへ移し、再cloneと全検証をやり直した。クラウドで仮想画面導入を試したがsudoなし/apt取得403であり、描画正例は指定版のGitHub CIで実行した。上限延長や検査省略は行っていない。

## 全CI実物・画像証拠

提出コード `9f1a18892273ac06d9776d2ddf8dbcc1c6423453` の [通常CI 37202293904](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293904) 全3件と [専用CI 37202293927](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927) 全17件、**全20job completed/success** をGitHub APIで直接確認した。全step、実行SHA、started_at/completed_at、時間を `ci/code-all-jobs.json` に保存。全20jobのログを直接取得し、当時/最新の実行JSON、R-01〜R-08、26/26、描画のchecks/imagesを `ci/verified-log-excerpts.json` と `ci/audit-log-excerpts.json` に保存した。過去レビューの転載ではない。以下はAPIのjob開始〜終了秒（課金時間ではない）。全jobのHEADは上記9f1a188、固定実行側の対象006/009/012/016はそれぞれ別checkoutの記録SHAである。

| job（実物リンク） | 結果 | 秒 |
| --- | --- | ---: |
| [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293904/job/111436290067) | success | 224 |
| [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293904/job/111436290290) | success | 99 |
| [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293904/job/111436290328) | success | 300 |
| [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290074) | success | 503 |
| [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290185) | success | 120 |
| [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290218) | success | 161 |
| [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290224) | success | 149 |
| [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290240) | success | 127 |
| [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290293) | success | 164 |
| [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290313) | success | 193 |
| [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290322) | success | 233 |
| [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290326) | success | 157 |
| [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290338) | success | 221 |
| [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290343) | success | 180 |
| [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290361) | success | 156 |
| [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290371) | success | 132 |
| [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290383) | success | 220 |
| [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290398) | success | 184 |
| [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290449) | success | 255 |
| [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/job/111436290501) | success | 128 |

追加正負例は13/13 PASS。元F2の店内NPCは7661項目・20保存成功、22.297秒。NPC付き描画は132項目・28枚、119.697秒（180秒内）。占有無視、拒否時状態破壊、客側閉塞、室外扉閉塞はいずれも終了1・該当実assertion失敗を検出し、21.372/21.559/21.371/21.371秒。外観39項目×配置前後、既存回帰7656、元負例も保持。13件のstatus=PASSは負例の実失敗を確認したという意味で、壊れたゲームの成功ではない。

取得した [最新journey artifact 11303805722](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/artifacts/11303805722) はZIP SHA256 `70c2a25e64d09ac6daa81f1cf3d78cf3051e6cb1666e89baaf9c61a724368020` がAPI digestと一致。最新のchecks.jsonは9f1a188・PASS・132項目・28枚。その世代だけを `ci/latest-journey/` に保存した。

取得した [lifecycle artifact 11302869815](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37202293927/artifacts/11302869815) はZIP SHA256 `f3ffe59d5a1fb38a913cff21ac727e2caec60a8b17012200565dd32e0adad207` がAPI digestと一致。今回実行した13正負例とNPC付き描画28枚、独立照合14件・固定範囲6件だけを `ci/negative-cases/`・`ci/counter-capture/` 等へ抽出した。同梱の旧task012/localや過去描画を今回の証拠に数えない。

固定006の7592項目/20保存/5別プロセス（9/26/37/51/43）と固定撮影7mode49枚、最新7662/20保存/5別プロセス（10/27/38/52/44）と最新撮影7mode49枚を当該CIの実行ログで確認した。固定012の17件は全てPASS、固定009の完成差分PASS、016完成差分と後続編集6件PASS。通常CIのR全8・保護・原画再生成/画素検査もsuccess。監査job503秒は15分内であり、どの上限も延長していない。


## Astra/Medium再レビューの最小手順

1. 提出ブランチHEAD、固定012 c327e7c、固定009 ce07fda、固定016 6706397を別checkoutする。`check_task016_fixed_anchor.py` と `test_task016_fixed_anchor.py` を最新の完全SHAで実行する。元F1の同時付替えケースが独立信頼基点不一致で拒否されることを確認する。
2. コピーのitem室eventsだけを `[{"id":"task013_counter_copy","kind":"npc","cell":[8,4],"text":["コピー限定"]}]` にする。固定版import後、最新回帰GD直接実行（故障注入コピーでありclean wrapper成功とは称さない）。占有目標の隣接実到達/全状態保持がPASSで、20保存後に実退出することを確認する。
3. `test_task009_lifecycle.py --fixed-path <固定006> --godot <固定Godot>` を実行。NPC正例と全描画、客側/出口閉塞、占有無視、拒否時状態破壊の負例を確認する。旧外観・誤接続・不正保存負例も残る。
4. 旧012当時の17件と `check_task016_scope.py` の6件を実行。固定SHAと元135箇所/全R/保護/画像のCI実物を独立に照合する。検査分離と正負例で判定し、CI緑だけで009/012を確認済みにしない。

## main・未確認・作業終了

本件は016のみ。mainへの統合は行わず、通常pushで修正ブランチを提出する。009/012は親と新しい独立再レビューが確認するまで差し戻しを保持。007/008/010/011等には着手しない。Astra/Medium再レビュー、007サービス、人間試遊、約60時間実測は本件で未実施。

追加AI委譲・ローカルPC利用なし。使用スキルはverification-before-completionのみ。指定モデル/effortの実効値を照合するAPIは環境にないため、その独立確認を行ったとは記載しない。提出文書commitの最終SHAと、その最終CI全終了結果は最終応答で返す。
