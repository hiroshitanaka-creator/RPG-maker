# 082 検証証拠の入口

最終本番SHA：`e675aca03d7a726379f88ad1529a2597f38de405`。
基点main：`6c996d5c37fd384e679bb23dd59113c99494790c`。

- `final-validation/`：最終SHAの集中293条件・原R-01〜R-08・関連回帰と保護照合、19コマンド。原ログはgzip、実行環境/コマンド/上限/終了/判定/原ログhashは `execution.json`。
- `latest/`：3216b3aの集中290条件・19コマンド。最終SHAの代用にはしない。
- `final/`：eb423adの補助全体回帰64コマンド。62件PASS、011通知fixture撮影の180秒timeoutと081旧段階比較の2件FAILを保持。詳細な生成JSONと子検査ログは `regression-records.tar.gz`。
- `execution.json` / `first-pass/`：初回2ea3c32の記録。描画環境不足などの失敗も保持。Python/Godotの同名ログは参照名だけ分離し、元のraw hashを保持した。再取得した出力にも元hashとの完全一致を要求した。
- `historical-stage-081.json`：081旧段階の原検査を無変更で、完成SHAでは1235件全PASS、082基点mainでは親文書2件だけFAILと確認した対応。最終側の親文書は082基点から不変。
- `development-attempts.json`：作業中の失敗・修正・再実行。終了0でもSCRIPT ERRORや警告のある実行を成功扱いしない。
- `environment.json`：クラウド内だけのGodot/Xvfb/Mesaの出所・hash・ICD設定。ユーザーのコンピューターは使用していない。
- `scope-audit-final.json`：本番変更8パスと、親担当文書・原画・world・CI・保護対象の不変照合。
- `pr-blocker.json` / `draft-pr.md`：自動承認レビューの拒否記録と未送信の具体的なドラフトPR原稿。
- `evidence-manifest.json` / `changed-paths.txt`：証拠ファイルのhashと、基点からの全変更パス。

原検査・期待値・判定・上限を変更せず、失敗をPASSへ変換していない。初の人物配置と視覚統合の採否、任意4職の取得/移行規則は別の未達事項。通常UI検査は人工の入口状態から開始し、新規ゲームからS10までの通し到達や最終的な人物配置の完成証拠とは区別する。
