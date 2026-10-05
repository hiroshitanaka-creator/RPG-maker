# 018 016固定監査の独立定数照合だけを補う

- 状態：確認済み（2026-10-05 JST。018修正・019独立レビューと指揮役の実物/全20CI確認を経てmainへ反映）
- 担当：Codex（クラウド）、GPT-6.1 Sol／High
- 依頼日：2026-10-04
- 前提：017報告済み。実装者・レビュー者終了。他の依頼未発注
- ブランチ：codex/task-018-fix-fixed-audit-constant
- 担当の場所：tools/check_task016_scope.py の独立期待値照合と負例追加、必要な既存016テストの同指摘反証部分、docs/verification/task-018/、本依頼書状態とdocs/tasks/reports/018-fix-fixed-audit-constant.md、docs/decision-log.md、016状態行
- 禁止：原画・本番・data/world・.scope-lock/・test/・R・workflow・既存ci.yml・固定006/009/012・その当時検査・AGENTS・他依頼書本文。新しい018用固定manifest/checkout/workflow/監査層を追加しない

## 目的
017のF3だけを最小修正する。元F1/F2は017が反証で解消確認したので作り直さない。新たな固定検査を次々に増やす再帰を止める。

## 背景
読む：docs/tasks/reports/017-review-audit-fixes.md（28c3ecb806b7b24e3bad17ce8fc4c111eddae8f5）。
固定016機能完成SHAは6706397e2674ffa382852e0f33ce23edf5c76634、treeは02105ab24ef39a2acf7405274e040d8cefaa399b、完成記録commitは9f1a18892273ac06d9776d2ddf8dbcc1c6423453。現行check_task016_scope.pyはCLIとlatestmanifestから期待値を作るため、状態だけ違う子commitへのworkflow/manifest/checkout同時付替えを6件PASSで受理する。

## 作業内容
1. 017F3を一時コピーで再現。012/016の既知固定点と対象checker実行場所を確認する。
2. 既存check_task016_scope.pyに、上記の承認済み016完全SHA/tree（または上記固定記録SHAから読む期待記録）を独立定数として持たせる。CLI/latestmanifest/workflow/実checkoutをその定数と照合する。最新側の自己一致だけでは成功しない。
3. 現行016の許可範囲を広げず、既存6項目と正常後続編集を保持。017の状態変更子commit＋workflow/manifest/checkout同時付替え、単独誤SHA/tree、欠損の負例を追加し失敗させる。既存012の17件/固定基点/最新回帰は保持。
4. 当時の016scope差分監査は6706397へ固定したまま。018はその既存検査の実装バグ修正であり、018自身の固定manifestを新設しない。018の許可範囲確認は今回の開始SHAと提出完全SHAの差分を報告書で明示して指揮役が確認する。新たな可変探索・再帰的固定用タスクを導入しない。
5. 全CI・R・保護・原画不変・既存上限維持・元F1/F2が退行していないことを検証。失敗無視/項目削除/skip/時間延長なし。報告済みで通常push、mainは親の再レビュー後にする。007等は開始しない。

## 守ること
既承認の不変完成時検査を満たす修正のみ。物語・機能を変更しない。別モデル/effort/環境/追加委譲なし。既存検査の固定参照自体を新完成SHAへ動かさない。

## 作業前・自己点検
開始SHA、定数、対象行、F3再現を記録。変更ファイルが上記だけ、新しい監査層0、旧検査項目維持、正例成功・同時付替え失敗、CI全成功を確認。

## 報告
docs/tasks/reports/018-fix-fixed-audit-constant.md に対象行、独立期待値、前後実測、全CIURL/SHA/結果、差分、保護不変と残る制約を書く。

## 完了条件
F3解消を実測し既存条件保持、全CI成功、018報告済み。Astra再レビューは親が別途発注する。
