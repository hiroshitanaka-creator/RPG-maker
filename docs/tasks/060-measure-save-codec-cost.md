# 060 装備保存codecの重複処理の計測と局所改善案

- 状態：未着手
- 作成日：2026-10-10（日本時間）
- 担当案：実験・専用検証はCodex、依頼書と受入はルッカ
- 実行場所案：保存済みRPG-makerクラウド、GPT-6 Astra／High（依頼者の10月中指定）。使用量への影響は不明
- 前提：059提出6695d7b802137e9d6b7e468a1414c04d658a5380を親が照合済み。最終51CIは47成功4失敗。S3全体未受入のまま、その時間未達を調査する独立計測として実行する。059全体を確認済みと偽らない。
- 基点：6695d7b802137e9d6b7e468a1414c04d658a5380
- ブランチ：codex/task-060-measure-save-codec-cost
- 承認：2026-10-10 08:11 JST、依頼者「新しいcodexタスクは進めなさい」（Sentinel_1fd597beb7e88191be765b63adef438e）。確認待ちだった専用計測コードと検証資料の追加、依頼書登録と発注。本番コード・環境設定変更は含まない。
- 発注方式：059に依存するため逐次。別Codexタスクと並列にしない

## 目的
保存全体の174秒締切未達について、重複処理の実際の寄与を測定し、安全境界を保つ最小改善案を提示する。本番最適化の採用・通常UI接続・S3受入をこの調査だけで宣言しない。

## 確認した根拠
- 058報告と059途中報告。約98%という既存値はplan＋verify全体であり、下記2箇所の寄与率ではない。
- ac768dee939783d41b8a6788af4b61551fd96d7b の scripts/game/equipment_save_codec.gd 全文を読み取り：
  1. decode_sourceのpacked経路は展開・parse後にSavedDocument.decodeを呼ぶ。
  2. encode_candidateはmetadata生成後、元metadataをnative_metadata_errorsで再照合する。
- 既存設計 docs/design/equipment-save-integration-plan.md のcodec・S3・検査世代の節、main AGENTS.md、docs/tasks/README.md、_template.mdを参照。
- 見かけの重複を不要と決めつけない。SavedDocument.decodeの入れ子包み拒否や元metadataの不正拒否を失う危険がある。

## 変更予定ファイル案（正式登録前に実在・衝突再確認）
新規専用計測コードだけ：
1. tools/check_equipment_save_codec_cost.gd
2. tools/check_equipment_save_codec_cost.py
3. tools/fixtures/equipment-save-codec-cost/cases.json
4. tools/fixtures/equipment-save-codec-cost/instrument_copy.py
5. tools/fixtures/equipment-save-codec-cost/compare_results.py
6. docs/tasks/060-measure-save-codec-cost.md（登録後は状態行のみ）
7. docs/tasks/reports/060-measure-save-codec-cost.md
8. docs/verification/task060-save-codec-cost/（各実行のraw log、入力識別子・hash、計測JSON、inventory。正式依頼で固定ファイル名と生成規則を列挙）

060は未採番の置き記号。新しい本番依存や未列挙のソース変更はしない。CI設定、assets/registry.json、project.godot、decision-log、tasks READMEをCodexに変更させない。計測用に既存コードへタイマーを入れる場合は、専用一時checkoutへの生成差分だけとし、その差分・hashを証拠に保存。本番branchのscriptsは不変にする。計測用差分の範囲は正式発注時に明記し、無承認で本番変更へ拡大しない。

## 作業
1. 基点・Godot版・OS・CPU・worker/batch・各予算を記録。059から引き継ぐ検査器と証拠の完全SHAを固定。
2. 全取引fixtureのplain/gzip比率、入力サイズ、metadataあり/なし、正常/異常/再開経路を一覧化。正常6seedだけを全体の代表としない。
3. 展開、parse、metadata生成、複製、validateの時間・呼出回数を分離。inclusive/exclusive、wallと並行累積を混同しない。
4. 計測on/offを同じ入力・環境・並列条件で複数回比較。計測自身の負荷と変動幅を記録。重い旧測定と軽い新測定を比べて改善率を作らない。
5. 6つの安全境界と現在データの再読取を保ったまま、1回の呼出し内だけで共有可能な結果を根拠付きで整理。境界をまたぐcacheや検査省略を候補にしない。
6. 候補ごとに、受理/拒否、reason_code/errors、出力bytes/hash・値・型、入力/context/メモリ不変の比較計画を作る。実装を試していない案は未検証と明記。
7. 時間内に終わらない場合も部分ログと終了理由を保存する。制限時間は延長しない。

## 保持する条件
UTF-8、重複JSONキー、gzip構造/長/hash、入れ子包み、未知metadataキー/不正path/型不一致、encode後decodeと全文比較、実tmp/converted照合を保持。初回plan・prepare・prepare末recover・commit入口・rename直前・rename後の境界を減らさない。
既存172件/2178条件・97kill・16伝播、旧固定版と最新回帰、R-01〜R-08、保護26を保持。テスト弱化・省略・時間延長・警告無視なし。
本番codec、saved_document、validator、native/addons、旧fixture/原証拠/固定SHA、保護対象、原画、実ユーザー保存は変更しない。実ENOSPC/nested別volumeの環境準備は含めない。

## 検証・証拠の案
- Godot importは既存手順・600秒以内。
- 新しい計測の各実行も既存の対応コマンド上限を超えない。独自の長時間予算は新設しない。
- 新規Python driverから専用fixtureと一時checkoutを使用し、exit・argv・実秒・stderr・完全SHA・未達理由を保存する。正式時にCLI引数・上限対応を固定する。
- 固定基点と最新HEADを別に検証し、計測コード自身が担当外を書き換えた負例でscope検査が失敗することを確認。
- 全CIの終了結果は成功/失敗を両方報告。測定完了とF1解消を分ける。

## 完了の条件
列挙した経路の計測結果または未測理由、計測負荷、原ログ、呼出関係、保持すべき検証、候補の対象関数・予測ではない実測範囲が対応していること。変更ファイルが許可集合内、本番/旧証拠/保護26不変、commit/push済み、clean/未push状態と全CI結果が明記されていること。改善効果が未証明ならそのまま未証明とする。

## 承認範囲と未決
- この文書は保存済み下書きに基づく正式な専用計測依頼。本番最適化の許可ではない。
- 機械生成証拠は docs/verification/task060-save-codec-cost/ 以下の run-<OS>-<off|on>-<連番>/ に argv.json、environment.json、measurements.json、results.json、stdout.log、stderr.log、exit.json、inputs.json、generated-diff.patch、hashes.json を保存。最上位は README.md、inventory.json、code-fixed-sha.txt、code-inventory.json、scope-results.json とする。未列挙の新規コードが必要なら先に報告する。
- 本番codecの局所最適化は、計測結果に基づく別の具体範囲として提示する。現在の059承認から自動拡張しない。

## 正式化時の補足
- 専用一時checkoutでのみ、equipment_save_codec.gd、equipment_document_validation.gd、saved_document.gd、saved_value_types.gd の入口/出口・対象区間への時刻/回数採取を生成してよい。差分は計測のみ。条件分岐/return/検査/入力/値/例外の意味を変えない。元hash・生成差分・対応を保存し、branchの本番ファイルは不変。
- tools/fixtures/equipment-save-codec-cost/compare_results.py は、計測on/offの受理拒否・reason_code/errors・出力値/型/bytes/hash・入力非変更の対応と、記録の欠落/改変を拒否する専用検査も兼ねる。元検査器は変更しない。
- 最初の計測は各条件3回、on/offの実行順を交互にし、全試行値と中央値・最小最大を記録。差が不明なら不明とする。全取引の元ケース集合を減らさず、個別計測と全体受入を区別。
- CLI案：python tools/check_equipment_save_codec_cost.py --godot <既存実行体> --base-sha 6695d7b802137e9d6b7e468a1414c04d658a5380 --output <専用QA先>。driverは試行ごとのプロセスを監督し、codec単体120秒、取引外180/内174/子30秒、import600秒を超えない。追加fixture・比較器の引数は開始計画で明示し、この範囲内で定義する。
- 新workflow接続・既存workflow変更は行わない。専用検査のCI未接続を明記する。既存全CIの終了・成功失敗を収集し、旧固定失敗も隠さない。
- F4環境準備、inspect-preparedのQA log不変条件変更、通常UI接続、本番最適化、PR作成/main反映、追加委譲は禁止。decision-logとtasks READMEは更新せず、判断は060報告に記載する。
