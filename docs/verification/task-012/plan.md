# 012 作業前計画（2026-10-04 UTC）

開始main: ce07fdada0466138260ab678c10fd78e61c0c63d。開始作業: 8ed58c00f8d7d16e2df24f3273f18019d2406002。開始時未コミット0、mainにないコミットは親登録a1022b6340d772900563b0d2f60969f9adf50b25と012登録8ed58c0の2件のみ。指定ブランチ上の親登録を保持する。mainは開始ブランチの祖先で競合なし。

006固定: 5f1c2ba231191b25b9b32a814b616a9f8d0a54ce。
009固定: ce07fdada0466138260ab678c10fd78e61c0c63d、tree 655312a33364d8e3fe97f09bd9bd3c415ed1ceae。
現行選択: 009依頼書のgit log最終編集点、作業中ならGITHUB_SHA。a1022b6で010/011が差分へ混入するため可変探索を廃止する。

変更予定: .github/workflows/region2-village-connections.yml、tools/test_task012_pinned_audit.py（新規）、docs/verification/task-012/**、docs/tasks/reports/012-pin-completed-audit.md、docs/decision-log.md、012状態行、009状態行だけ。既存検査器・ALLOWED・本番・素材・保護・ci.yml・他依頼書本文不変。

反証: 新規依頼書、009状態のみ、同一commitで状態と010/011追加、将来の別範囲変更、012状態のみ。各ケースで006/009/012固定SHAを独立期待値と照合、当時009検査器の固定監査を実行。旧git log選択は親登録a1022b6へ移り元検査器が010/011を拒否することも再現。誤SHA、不存在SHA、固定009 checkoutの検査器改変、固定009対象の範囲違反commit、012完成範囲の違反commitは終了失敗を要求。既存009の正例3・負例4はそのまま全実行し、最新誤接続と不正保存受理の実assertion失敗を確認。

012は機能完成commitと固定記録commitを分ける。記録commitで独立manifestに完全SHA/treeを記録し、別checkoutの完成版012検査器で完成差分だけを毎回監査。後続HEADの範囲全体へ012の制約を適用しない。後続タスクを再帰要求しない。

上限: 専用全17jobは各15分（増加なし）、import各600秒、Godot各180秒、描画内部180000ms/600移動/3000入力/300ターン。新規Python検査は各子コマンド180秒以内、全体workflow側timeout 180秒。通常CIはpreplay35分、godot-import25分、素材既定を変更しない。凍結verify上限300秒。実測超過は失敗とし、上限延長しない。
