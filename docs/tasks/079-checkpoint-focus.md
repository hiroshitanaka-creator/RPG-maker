# 079 タイトルの自動保存復帰とキーボード選択

- 状態：依頼済み
- 担当：Codex GPT-6 Astra／High。正式保存・CIは親。
- 基点：8f2bc17b8c36b4304eb17de1a29e91e67a21cf57
- 日付：2026-10-20 JST

## 根拠と範囲
game_root.gd の _render_menu で checkpoint.disabled を保存ファイルの不存在から設定しているが、focus_mode同期がない。通常タイトルから無効操作へ選択が止まる可能性であり実害は未再現。まず既存RPG_QA_SAVE_PREFIXで隔離した保存なし状態から実入力で再現する。成立した場合だけ当該checkpoint Buttonのfocusをdisabledと同期する。disabled条件・保存読込/破損拒否・回復規則は変えない。既存のbattle-recovery-v1、experience-spec-v2の自動保存復帰機能を維持する。
変更予定は scripts/ui/game_root.gd の当該focus、docs/tasks/079-checkpoint-focus.md状態、docs/tasks/reports/079-checkpoint-focus.mdの3件。074〜078差分は混入しない。世界地図等の別ボタン・親記録へ拡大しない。main/066/利用者PC/保護/test/検査器/CI/registry/project.godot/原画/物語/規則変更禁止。

## 検証
AGENTS・関連仕様・配置済スキルを確認。保存なしのTab/ShiftTabと方向キー、Enter/マウスを前後同一入力で測定。画面/選択/ゲーム全状態を記録。保存ありでは有効選択と既存の正常復帰を確認。破損保存では現行の拒否/通知/状態保持を維持。手動保存と別管理、再表示・戻る・取消・連続入力・新規開始後のタイトルも確認し、正常到達と診断注入を区別する。実保存を削除せず隔離領域のみ、他タスクの証拠不変。focus強制やsignal直呼びを実入力証明にしない。原PNG確認。未再現なら本番修正なしで報告。
固定Godot4.7.2、editor/headless import、assets strict、frozen、R01〜08と既存回復/画面検査を既存上限で実行。弱体化/省略/上限延長なし。途中失敗と警告、物理controller/利用者実機未検証を明記。

## 引渡し
3payload全文・適用検証patch・元ソース・前後status・未push一覧・原ログ/PNG/JSON/ハーネス/manifestをcheckout外ZIPに保存しLibrary ID/bytes/SHAを返す。原PNGは加工しない。新規commit/remote push/PR/mergeは親担当。拒否操作再試行やアクセス迂回なし、結果不明なら照会。正式保存・全CIまで完了としない。
