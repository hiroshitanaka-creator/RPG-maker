# 070 城の案内本文の修正報告

- 状態：ローカル実装・検証済み。正式GitHub保存・全CI・PR・統合は親が行う。
- 基点main：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`
- 正式依頼登録：`f467780a46e640a67b445de5405a404bcf501a6a`
- 作業ブランチ：`codex/task-070-castle-guidance-text`
- 原資料保存先：`/workspace/task070-evidence/`（checkout外）

## 変更

`castle_home_resident` の既存1ページ本文を、正式依頼書指定の「森の塔へ進むには、王の許しが必要です。」へ揃えた。`world/first_region.json`、実ロード先 `world/interiors.json`、生成元 `tools/build_castle_town.py` の対応文字列各1件だけを変更した。新しい地名・人物・設定・許可条件を追加していない。

編集は上記3ファイル、依頼書の状態行、この専用報告書の5ファイル。JSON全体の再整形なし。JSONの対象 `text[0]` 以外の全値、全イベント順序、ID、話者、1ページ構成、画像、数値、フラグ、扉、座標は完全一致する。Pythonは指定文字列のbytes置換だけで構文も有効。現配置 `[11,6]` と生成元の旧座標 `[10,7]` の既存差を維持し、生成元実行・全マップ再生成はしていない。

依頼書は状態行だけを「報告済み」に変更した。READMEとdecision-logは親の担当として編集していない。元の本文へは3箇所を戻す通常コミットで復旧できる。

## 事前確認・確認票

公式GitHub接続の認証先 `hiroshitanaka-ai` を確認。開始時の登録ブランチは登録コミットとidenticalで、070の既存実装はなかった。基点mainと取得時mainもidentical。登録コミットとの差分は依頼書追加1件のみ。既存の検証済みmainをローカルcloneし、公式取得した依頼書原bytesと既存登録commit原bytesを、blob/tree/commit SHA完全一致で再現した。登録treeは `15eeb188b7574e5dc0247c2c9116158be2d87202`。公式原記録は `source/` に保存した。

AGENTS、scope-lock、伝言板README、依存関係、experience-spec-v2とstorytellerのSKILL/canon/audit/formatsを読み、069の確認済み状態を確認した。`rpg-maker-storyteller` を使用。`godot-game-verification` は未導入で、追加せず既存検査・通常入力・実画面・原ログの原則を適用した。

確認票：場面は城下町の民家、時点は王の許可前後、話者は既存の「町の人」。目的は既存の許可条件と実際の進行先の案内を一致させること。現物とcanonの今回に関する食い違いなし。新しい決定事項・組込み機構・要決定事項なし。監査21項目を確認した。`storyteller-audit.json` に記録。形式Bの既存NPC text配列は次の1ページである。

```json
["森の塔へ進むには、王の許しが必要です。"]
```

AGENTSの一般的なpush・成果物置場・decision-log記録の指示については、今回の明示委任に従い、原資料はcheckout外とLibrary、公式保存・CI・統合・決定記録は親が担当する。保護契約や検査の変更はない。

## 検証結果

Godotは公式4.7.2 ZIPを既定SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` で再照合し、ZIPメンバーと実行ファイルbytesも一致。実行版は `4.7.2.stable.official.ed1daf0bf`。前回の公式取得物を再利用し、system installや認証設定変更なし。公式URL・検証結果は `environment.json`。

| 検査 | 終了コード | 秒 | 実行証拠 |
|---|---:|---:|---|
| import | 0 | 87.109 | PASS |
| assets-strict | 0 | 8.959 | PASS |
| frozen | 0 | 0.066 | 保護26件一致 |
| R-01 | 0 | 5.285 | 2 tests / 765 assertions、pending/failed=0 |
| R-02 | 0 | 14.885 | 5 tests / 946 assertions、pending/failed=0 |
| R-03 | 0 | 5.438 | 2 tests / 73 assertions、pending/failed=0 |
| R-04 | 0 | 6.288 | 1 tests / 293 assertions、pending/failed=0 |
| R-05 | 0 | 5.941 | 2 tests / 79 assertions、pending/failed=0 |
| R-06 | 0 | 6.109 | 2 tests / 87 assertions、pending/failed=0 |
| R-07 | 0 | 85.215 | A01〜A14 全14項目 |
| R-08 | 0 | 32.424 | 25 tests / 3046 assertions、pending/failed=0 |
| first-region-screen | 0 | 25.248 | 既存画面10項目 |
| 通常画面 before | 0 | 171.773 | 34観測PASS |
| 通常画面 after | 0 | 94.947 | 24観測PASS |

scope-lockに登録されたverifyコマンドをそのまま実行し、既存 `run_locked_checks.py` の `judge_output` で実行件数・assertions・pending・parse・結果を判定した。R-07は通常の新規開始から今回も実行した。終了0だけで成功と判定していない。素材strict・保護26件も成功。各原ログのSCRIPT ERROR / ERROR / WARNING / Parse Error / 実際のリソースリーク警告 / TIMEOUTは0件。詳細は `logs/commands.json`、`logs/runtime-commands.json`。

今回の通常画面ハーネスは、前回の外部ハーネスを専用保存先へ用意し、出力先と正式依頼書からの本文リテラルだけを変更した。既存の保護検査本体・期待値・上限と前回の原ハーネスは変更していない。`tools/smoke_first_region.gd` を継承し、同梱.gdを本番へコピーしたり、Autoload/GUT/常設検査基盤を追加していない。

通常保存の流用は、親が照合済みの前回原ZIP（5,124,073 bytes、SHA256 `e9127a1ede4a64a8ae4da816ab0519b623967cb76bf650db4c0ce09bff689acf`）内の通常操作保存を原bytesでコピーしたもの。タイトルの通常ロードを使い、王の許可取得とその後のメニュー保存は今回再実行した。座標・所持品・編成・フラグ・乱数内部状態の注入なし。`save-provenance.json`、`normal-gate-save.json`、`normal-permission-save.json` を収録。元ZIPも `baseline/` に無変更で収録した。

| 通常入力の確認 | 許可前 | 許可後 |
|---|---|---|
| 初回会話、話者「町の人」、新本文1ページ、決定で終了 | PASS | PASS |
| 民家を退出して再入場、同じ会話、終了 | PASS | PASS |
| 城下町北門→中庭 | 通過可、許可false維持 | 通過可、true維持 |
| 中庭北扉→大広間 | 通過可、false維持 | 通過可、true維持 |
| 大広間中央奥扉→謁見の間 | 通過可、false維持 | 通過可、true維持 |
| 森の塔入口 | 上入力2回とも屋外に留まる | 入場・退出可能 |

王との全5ページ表示中は許可falseで、最後の決定入力後にtrueとなった。前回と同じ58ケースID、位置・向き・許可・転職解放・通行証・画面モード・人数の観測が全件一致した。文面は今回指定の新本文に照合した。`regression-comparison.json` と `cases.json`、各 `cases-before/after.json`、`states/` に原記録がある。物理北門は存在しており、不存在やゲーム全体の不具合という説明はしていない。

描画はVulkan/mobile、X11 dummy、Mesa llvmpipe、1024×576 PNG。対象の許可前/後×初回/再訪の4会話画像と終了画像を含め32枚を実際に開いて確認した。新本文は1行で会話枠内に収まり、話者表示・本文の欠けや重なりはない。門・扉の存在と遷移先、塔の屋外/内部、王との会話終了を確認した。Label矩形は論理viewport座標、PNGは表示解像度で区別する。`visual-review.json`。入力は既存InputEvent経路で、物理キーボードによる手操作とは区別する。

## 原ログ・警告・範囲点検

Xorgには既存のfontディレクトリ不在、mouse/kbd/libinput、system bus不在などの環境メッセージがある。`logs/Xorg.log` と `logs/Xorg-console.log` に原文を保全し、ゲームログの結果と分けた。環境全体の警告ゼロとは報告しない。今回起動した表示サーバーは終了した。

補助ランナーの初回ログ抽出は、正常なテスト名 `test_all_validation_failures_fall_through_without_relocation_leak` の語をリーク警告と誤分類し、ランナーがexit1になった。R-08本体は初回からexit0、既存judge_outputもPASS（25 tests / 3046 assertions、pending/failed=0）。原ログを確認し、テスト名と実際の警告を分けて分類を訂正した。再実行による置換や既存検査の変更はしていない。初回の原判定・ランナーを `attempts/log-classification/` に保全し、理由を `logs/log-classification.json` に記録した。

登録commitの原bytes復元は、初回にタイムゾーンを+0000と仮定したためSHA照合で停止した。元の+0900形式で正式SHAとの完全一致を確認してから実装を開始した。`source/prepare-initial-failure.txt` と当時のスクリプトを保持。取得拒否・認証拒否の迂回はない。

既存画面回帰が生成する `docs/verification/first-region/screen-checks.json` は原出力を `logs/first-region-screen-generated.json` に保存し、基点の原bytesへ戻した。検査の期待値や本体を編集していない。import生成の未追跡UIDとcacheは製品変更から分け、`generated-local.json` に記録した。

最終差分は指定5ファイルのみ。他のtracked bytes、原67/066系列、069本文、保護26件、既存テスト・assertion・期待値・締切・CI・project.godot・素材・台帳は不変。`scope-validation.json`、`final-scope.json`。remote push、PR、merge、GitHub書込み、認証変更は行っていない。ローカルcommitの識別子と変更5ファイル原bytesは `local-commit.json` と `changed-files/` に引き渡す。

## 実行コマンドと再現

作業ディレクトリは `/workspace/RPG-maker-070`。環境は同梱 `env.sh`。取得・構築は `prepare.py` と `source/`、限定差分検証は `python -B /workspace/task070-evidence/validate_scope.py`（PASS）、実行条件は `REPRODUCE.md`。

- `godot --headless --path /workspace/RPG-maker-070 --editor --import --quit` — 0、上限600秒、原ログ `logs/import.log`
- `python -B tools/validate_assets.py --strict` — 0、上限300秒、原ログ `logs/assets-strict.log`
- `python -B tools/check_frozen_files.py` — 0、上限300秒、原ログ `logs/frozen.log`
- `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_data.gd -gexit` — 0、上限300秒、原ログ `logs/R-01.log`
- `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_actions.gd -gexit` — 0、上限300秒、原ログ `logs/R-02.log`
- `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_ability_slots.gd -gexit` — 0、上限300秒、原ログ `logs/R-03.log`
- `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_monster_form.gd -gexit` — 0、上限300秒、原ログ `logs/R-04.log`
- `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_battle_loop.gd -gexit` — 0、上限300秒、原ログ `logs/R-05.log`
- `godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_save_roundtrip.gd -gexit` — 0、上限300秒、原ログ `logs/R-06.log`
- `godot --headless --path . --script res://tools/smoke_first_region.gd` — 0、上限300秒、原ログ `logs/R-07.log`
- `godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test/unit -gprefix=test_ -gexit` — 0、上限300秒、原ログ `logs/R-08.log`
- `godot --headless --path . --script res://tools/check_first_region_screen.gd` — 0、上限180秒、原ログ `logs/first-region-screen.log`
- `godot --path /workspace/RPG-maker-070 --rendering-method mobile --rendering-driver vulkan --audio-driver Dummy --script /workspace/task070-evidence/harness/runtime_guidance.gd` — 0、上限180秒、原ログ `logs/before.log`
- `godot --path /workspace/RPG-maker-070 --rendering-method mobile --rendering-driver vulkan --audio-driver Dummy --script /workspace/task070-evidence/harness/runtime_guidance.gd -- --after` — 0、上限180秒、原ログ `logs/after.log`

## 変更原bytes

| ファイル | bytes | SHA256 |
|---|---:|---|
| `world/first_region.json` | 83922 | `d776e0a3efb184177b890223d6c28017338120ef1d2566c6f927656c72ffa556` |
| `world/interiors.json` | 262155 | `e8f0dde4c1bd8c7d86251f4eec65f6e5c9c633845a94b1f4176642a836cc74e4` |
| `tools/build_castle_town.py` | 15564 | `6a5695f338cd102b9719c61fda04da4abdbb44570933ab3ed26d974a0c206846` |
| `docs/tasks/070-castle-guidance-text.md` | 5435 | `5ded3694b80de7afaa808fb26205655d7d62bd57a2e30a85e42c142fa1e4bfff` |

本報告書を含む5ファイルすべての最終サイズ・SHA256は、自己参照ハッシュを避けるためZIP内の `changed-files-manifest.json` に記録する。差分は `change.patch`。全同梱原資料の照合は `manifest.json`。PNG縮小や要約への置換は行っていない。Godot/Mesaの大容量実行環境とcacheは同梱せず、出典・ハッシュ・再現条件を収録する。

正規Libraryの確定ID・ZIP全体サイズ/SHA256は引渡し時の最終応答と `delivery.json` に記載する。原資料の保存成功を確認してから親へ引き渡す。

## 未達・未検証

ローカルの指定実装・検証に未達なし。正式GitHub保存、全CIの終了・全成功確認、PR・mainへの統合は親の担当で未実施。全編3人/4人・正順/逆順の受入を今回ローカルで再実行しておらず、今回のR検査・58観測をその代用にしない。既存の全編検査やその条件は変更していない。PC/MSIは対象外。追加の作品内容の判断は求めない。


## 親の原資料受領（2026-10-15 JST）
原ZIP：TASK-070-castle-guidance-text.zip、9,690,533 bytes、SHA256 d673fe6c7f27d8366f3c00873f2ca982781572f7ad4a3585dd88219b928b3ea1。Drive ID 1JLmQQZ8E7TyRcAU6MH5yeu0nftYYBwFv、指定070フォルダへ保存し全量読戻しで一致。Library原本libfile_826a078fa5548191ace11cd0efcbff8eも保持。親は公式基点の3ファイルへ指定文字列1件だけを置換した結果と提出原bytesが完全一致すること、依頼書状態1行、実画面を確認。独立レビューはmanifest147件・既存4ファイル基点hash・58観測の前回一致・原検査ログを照合。正式CI・PR・取込後検証はこの時点では未実施。
