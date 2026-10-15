# 071 070案内本文と旧導入データ照合の両立 — ローカル報告

- 状態：指定4ファイルのローカル実装・検証済み。正式保存・全CI・PR・統合は親の担当で未実施。
- 正式071登録：`255572021d547c1856087616cec27c149b96f565`
- 前提の070提出：`8a53e94e24be3e1e49c03abd052af60821c310f6`
- 旧main対照：`8f2bc17b8c36b4304eb17de1a29e91e67a21cf57`
- ブランチ：`codex/task-071-guidance-scope-check`
- 原資料：`/workspace/task071-evidence/`。正規Libraryの確定ID・ZIPサイズ・SHA256は引渡し応答とcheckout外の`delivery.json`に記録する。

## 変更と設計

編集4ファイルは `tools/check_first_region_gado_data.py`、新規 `tools/check_task070_guidance_scope.py`、依頼書 `docs/tasks/071-guidance-scope-check.md` の状態行、この報告書のみ。

実装前に `design-before-implementation.md` を記録した。新helperは両JSONのfirst_castle／部屋9／castle_home_residentを一意に特定し、既存の部屋名・kind・sprite・座標・話者、textのlist型・1要素・str型・正式070採用文字列の完全一致を照合する。対象IDの一意性は全サイト全室で検査する。生成元を実行せずASTで対応するサイト、main内のhome定義、部屋順、npc呼出しと引数を照合する。生成元の旧座標と本番配置の既存差は維持した。

両JSONと生成元の照合後にのみdeepcopyを作り、その指定text[0]だけを明示した旧本文へ戻す。元データを書き戻さない。既存検査の全体ハッシュ照合にそのコピーを渡す。実データの旧本文・誤字を無条件に旧文へ変換する処理ではない。変換するのは各JSONで1要素だけであることを `normalization-proof.json` でも確認した。

既存ファイルは4行の呼出し追加と、既存deepcopyの参照元1行の変更だけ。元BASE／BASE_HASHESの行bytes、既存26個のassertionのASTが全て一致した。全体ハッシュassert、導入イベント・素材・原画・台帳・経路・競合拒否・生成2回の既存判定を残した。新helperの正負例は既存mainから必ず呼ぶ。直接実行もでき、workflow変更・skip・失敗の握り潰し・予算延長はない。

## 事前確認と取得

AGENTS全文、scope-lock、tasks/README、正式070依頼・報告、元検査、正式071依頼全文を確認した。依頼書の明示承認（2026-10-15 14:34 JST）の限定範囲を適用した。一般的なpush・リポジトリ内成果物保管の指示に対しては今回の委任に従い、GitHub書込みと決定記録は親、子の原資料はcheckout外とLibraryとした。

公式GitHub接続のアカウントhiroshitanaka-aiとブランチを確認。071は登録SHAとidentical、070提出との差は依頼書追加1コミットのみ。公式取得した原bytesを隔離worktreeへ反映し、070／071のtreeおよび既存commit SHA完全一致を確認した。071 treeは `88156db7fd73143cec04716a399c8475c36d293b`。原応答と既存commit原bytesを`source/`へ保存した。

旧台帳を参照する既存検査には、既にローカルに保持されていた導入commitと必要なtree/blobの4オブジェクトを、元SHA一致で使用した。原記録は`source/provenance.json`。remote fetch・push・PR・merge・認証設定変更なし。取得拒否の迂回なし。

指定されたgodot-dev-director／godot-game-verificationはローカルおよび利用可能なcloud catalogに未導入。追加していない。既存検査と本依頼の検証原則を適用した。Libraryスキルで原資料を引き渡す。

## 元検査の対照

| 対象 | 元コマンド | 結果 |
| --- | --- | --- |
| 旧main 8f2bc17 | `python -B tools/check_first_region_gado_data.py` | exit0、INTRO_DATA_PASS、生成2回 |
| 070適用版／071登録時 | 同上（元ファイルのまま） | exit1、76行目のcanonical_hash(stripped)==BASE_HASHES[...]でAssertionError |

`logs/original-old-main.log`、`logs/original-070.log`、`logs/control-commands.json`が原記録。期待した失敗も保存した。旧main側の生成報告を保存後、対照checkoutのtracked bytesを復元した。本番データの変更なし。

## 正負例

正例1件：正式採用本文を持つ両JSONと生成元が一致し、限定変換後の両JSONが元固定ハッシュに一致。

負例44件を全て拒否した。個別名と拒否理由は `logs/guidance-scope.log` および `logs/intro-data.log` に全件記録。

| 分類 | 個別変化 | 件数 |
| --- | --- | ---: |
| JSONの各片側を個別に変更 | 旧本文、1文字、2ページ、text非list、ページ非str、空text、ID、座標、話者、kind、sprite | 11×2=22 |
| JSONの各片側で構造・他データを変更 | 別イベント本文、削除、同室重複、別室重複、サイトID、別室へ移動 | 6×2=12 |
| 両JSON | 両方とも旧本文 | 1 |
| 生成元だけ変更 | 旧本文、1文字、2ページ、ID、座標、話者、サイト、部屋、ID重複 | 9 |

別イベントの変更は元の全体ハッシュ不一致で拒否。期待値は正式070の明示リテラルと変更しない既存BASE_HASHESで、判定対象から生成していない。各例で入力オブジェクト不変も確認した。既存検査経由でも同じ45例が実行された。

## 実行結果

公式Godot4.7.2 ZIPを既定SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` で再照合し、ZIP内メンバーと実行ファイルbytesも一致。実行版は `4.7.2.stable.official.ed1daf0bf`。公式URL・原取得物の場所・再照合は`environment.json`。新しい専用cacheへimport後に実行した。

| 項目 | exit | 秒 | 実結果 |
| --- | ---: | ---: | --- |
| import | 0 | 74.504 | PASS |
| guidance-scope | 0 | 0.668 | 正例1・負例44・入力不変 |
| intro-data | 0 | 1.268 | INTRO_DATA_PASS、生成2回、5 variants、pending_art=0 |
| intro-runtime | 0 | 7.491 | INTRO_RUNTIME_PASS、1988 checks、pending_art=0 |
| assets-strict | 0 | 8.893 | 問題なし |
| frozen | 0 | 0.064 | 保護26件一致 |
| R-01 | 0 | 2.472 | 2 tests / 765 assertions、failed/pending=0 |
| R-02 | 0 | 10.408 | 5 tests / 946 assertions、failed/pending=0 |
| R-03 | 0 | 2.622 | 2 tests / 73 assertions、failed/pending=0 |
| R-04 | 0 | 3.583 | 1 tests / 293 assertions、failed/pending=0 |
| R-05 | 0 | 2.625 | 2 tests / 79 assertions、failed/pending=0 |
| R-06 | 0 | 3.127 | 2 tests / 87 assertions、failed/pending=0 |
| R-07 | 0 | 70.813 | A01〜A14 全14項目 |
| R-08 | 0 | 28.15 | 25 tests / 3046 assertions、failed/pending=0 |

実コマンドは次のとおり。cwdは `/workspace/RPG-maker-071`、Godotは上記検証済みbinaryがPATHの先頭。原コマンド、上限、exit、成功マーカー、原ログ監査、既存judge_outputの判定は`logs/commands.json`、実行スクリプトは`run_checks.py`。

```text
godot --headless --path /workspace/RPG-maker-071 --editor --import --quit
python -B tools/check_task070_guidance_scope.py
python -B tools/check_first_region_gado_data.py
godot --headless --path . --script res://tools/check_first_region_gado.gd
python -B tools/validate_assets.py --strict
python -B tools/check_frozen_files.py
godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_data.gd -gexit
godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_job_actions.gd -gexit
godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_ability_slots.gd -gexit
godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_monster_form.gd -gexit
godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_battle_loop.gd -gexit
godot --headless --path . -s addons/gut/gut_cmdln.gd -gtest=res://test/unit/test_save_roundtrip.gd -gexit
godot --headless --path . --script res://tools/smoke_first_region.gd
godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test/unit -gprefix=test_ -gexit
```

既存Rコマンド・上限300秒、import600秒、導入runtime180秒を維持した。補助Pythonコマンドにも300秒の外側上限を置いた。既存run_locked_checks.pyのjudge_outputをそのまま使い、GUT件数・assertions・pending・parse・実行結果を確認した。R-07は今回も新規開始から実行した。

導入runtimeは既存headlessコマンドで、人工境界入力と通常UI操作の検査。native_render=falseであり、今回新たな通常描画画像を取得したとは扱わない。070の通常画面の再受入・全編試遊の代用ではない。

## 原ログ・範囲点検

上記14コマンドのSCRIPT ERROR／ERROR／WARNING／Parse Error／実リソースリーク／TIMEOUT／FAILは0件。新旧対照の期待したAssertionErrorは別に保持した。初期のversion照会では、専用XDG cacheを設定する前に `Fontconfig error: No writable cache directories` がstderrに出た（exit0）。原文を`logs/environment-initial.log`に記録し、その後の専用書込可能cacheを使ったimport・検査では発生していない。環境全体の警告ゼロとはしない。

既存検査が出力するdata/media/runtime報告は`generated-reports/`に原bytesを保存し、checkout側は基点bytesへ復元した。Godot import生成の未追跡UID2件も`generated-local/`へ保全し、製品変更へ含めない。import cacheはcheckout外に保持した。失敗した元検査を消したり、判定を緩めて再実行したりしていない。

全trackedファイルの事前SHA256と照合し、指定既存2ファイルの変更、新規2ファイルの追加だけであることを確認した。JSON・生成元・ゲームコード、原67／066、過去証拠、他の検査・期待値・締切・workflow・.scope-lock・test・保護26件は不変。依頼書は状態行だけを報告済みに変更。`scope-validation.json`、`implementation-check.json`、`tracked-before.json`が照合記録。

## 引渡しと未検証

編集4ファイル原bytesを`changed-files/`、差分を`task071.patch`、ローカルcommit情報を`local-commit.json`へ保存する。原ログ・対照・設計・生成報告・公式取得原応答・SHA256/サイズmanifestをZIPへ収録し正規Libraryへ引き渡す。ZIP全体の確定ID・サイズ・SHA256は引渡し応答と`delivery.json`に記録する。

指定されたローカル実装・検証に未達なし。正式GitHub保存・070/071を含む提出SHAの全CI・必要なGitHub承認・PR／main統合は親が行う。今回、全編3人／4人・正順／逆順の受入、約60時間実測、人間プレイ、PC/MSIを再実行していない。これらの既存条件を変更していない。ローカル成功を正式CI成功や作品全体の完成とは扱わない。


## 親の提出検収（2026-10-15 14:56 JST）
- Library libfile_a82b083bb1708191a886be10d2ba0ac8、ZIP492,828 bytes、SHA256 0e516ae0bed9880e314afa329142f23251da059478ba1431e1a678073e3fa5dcを親が実取得・一致確認。原73manifest全件と正負45例・R全8・保護26・runtime1988の原ログを独立確認、阻害欠陥なし。全checkout/GodotbinaryはZIP外のため、親の再実行/全7724件独立再計算とは扱わない。
- 子の4ファイルに、親のtasks/READMEとdecision-log追記を加えて正式提出する。本番070本文・元固定値・26assertionは保持。正式CIと必要なGitHub承認・main統合はこの記録時点で未実施。
- 原ZIPのDrive保全は安全判定で未完、具体保存許可の再確認待ち。Library原本は保持。予定先folder1xtZJy8yuVLSuGq7fFpNuGN9FAxSut3h7、Drive file IDは未発行。
