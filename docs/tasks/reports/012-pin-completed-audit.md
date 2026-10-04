# 012 完成点固定修正の報告

状態：作業中。009は差し戻しのまま、009/012の確認済み判定は親が行う。

作業前計画: docs/verification/task-012/plan.md。
変更: workflowの009監査対象をce07fdada0466138260ab678c10fd78e61c0c63dへ固定し、別checkoutで当時の検査器を使用。新規tools/test_task012_pinned_audit.pyで独立期待値・実在tree・後続commit反証・改変/誤SHA拒否・012完成範囲を監査。既存検査器とALLOWED・本番・原画・保護・ci.ymlは変更しない。

機能完成commit後に、固定記録commitで012自身の完全SHA/treeと別checkout参照を追加する。固定記録・以後の報告commitは、完成範囲の選択対象を動かさない。
全CI・固定/最新実行SHA・反証の実行結果は取得後に追記する。未検証を成功扱いしない。

機能完成SHA: `c327e7c439c9c8c8f1fd640e6cda6df7550fb26a`、tree: `1a128f883bd555653bd9eea3082c09b875c1f7e5`。固定記録は次のcommit。CIでこの完成版検査器を別checkoutし、012完成差分だけを開始8ed58c0と比較する。新規反証コマンドの外側上限180秒。
