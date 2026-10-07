# 045 CI比較の原検査記録検証を修正する

- 状態：確認済み
- 担当：Codex GPT-6.1 Sol／High
- 依頼日：2026-10-07 JST
- 前提：044レビュー成果確認済み、043差し戻し。基点9010b9b18e468e5e03c47ac285d4d1ad80045660
- ブランチ：codex/task-045-fix-ci-artifact-validation
- 担当の場所：043で新設したtools/run_equipment_ci.py、必要時のみ新.github/workflows/equipment-save.ymlの固定証拠取得、docs/verification/equipment-ci-fix/、自身の状態/報告、decision-log今回追記
- 禁止：既存3workflow・原検査器・本番・data・素材・test/.scope-lock/契約・旧証拠・他の依頼/報告

## 目的
044 F1/P2を修正する。今回承認済みの専用CI追加の品質修正として、原検査記録・fixture・旧比較出力の欠落や偽成功を拒否する。検査を弱めず追加する。

## 作業内容
1. AGENTS、043/044全文と反例を読み、現比較でversion記録5個やtrue command、PASSなしlog、空fixture辞書、boolだけの旧出力を受理する問題を再現する。
2. version/前保護/import/legacy原検査/後保護の各コマンドの種類・一意性・対象checkout・予算・実行結果・logのPASS行を検証する。文字列の見かけだけで別検査を受理しない。
3. fixture5件を固定041原本の実hashに照合。3artifactが同じだけで正しいとしない。旧出力の固定ケースID・必須フィールド・型・値/metrics/history等を検証する。失敗/欠落/重複/別SHA/古いartifactは拒否。
4. 044の反例すべてを新しい失敗伝播fixtureに追加し、修正前失敗・修正後拒否・正常対照成功を実行。元35fixtureの省略/変更で成功させない。固定/最新の原検査は変更しない。
5. 全14新jobと既存20jobを維持。予算延長なし。固定原本参照が必要な場合だけ新workflowへ必要な読取りfetchを加え、権限や対象を広げない。証拠は今回の新ディレクトリへ。

## 計画・自己点検
開始SHA/未コミット/未push、修正箇所と独立固定期待を報告冒頭へ。scope外変更、削除、強制push、追加委譲、main書込み/マージなし。原検査の意味や固定SHA・全assertを維持。正常全結果と再現反例の拒否、ログ/fixture/outputの検証を実物で示す。

## 報告・完了条件
docs/tasks/reports/045-fix-ci-artifact-validation.mdへF1対応表、変更パス、前後再現コマンド/件数/hash、全CI結果、未検証を記録。実コードを完全SHAへ固定して証拠を保存し、最終同一SHAの全34以上job成功を確認。依頼書は状態行だけ報告済みにしてcommit/push。PR30は親が後で通常取り込みするので別PR不要。
