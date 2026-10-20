# 078 編成の転職・清めるボタンとキーボード選択

- 状態：依頼済み
- 担当：Codex GPT-6 Astra／High。正式保存・CIは親。
- 基点：8f2bc17b8c36b4304eb17de1a29e91e67a21cf57
- 日付：2026-10-20 JST

## 根拠・対象
077原証拠after-render/results.json events[6]で通常新規開始からTab4回の「この職に転職」がfocus owner/disabled=true/focus_mode=2。清めるはboundary-3-forward-v2のevents[11]/[25]で無効focusを記録、こちらは診断注入であり通常到達と区別。Enter無反応と状態不変は未測定。今回この2Buttonだけを実再現し、成立時にdisabledとfocus_modeを同期する最小修正。初期転職と職選択切替の両方向、有効化時のfocus復帰が必要。disabled式そのものは変えない。

## 変更範囲
scripts/ui/game_root.gd の _render_party の転職・清めるButtonのfocus処理、docs/tasks/078-party-action-focus.md状態行、docs/tasks/reports/078-party-action-focus.mdの3件だけ。OptionButton/PopupMenuの説明閲覧、装着、職・浄化の規則を変更しない。074/075/076/077変更を混ぜない。既知scroll・装着focus問題は別件として保持。main/066/利用者PC/保護/test/既存検査器/CI/registry/project.godot/原画/物語変更禁止。docs/decision-log.mdとdocs/tasks/README.mdは親のみ。

## 検証
AGENTS.md・素材規約・該当仕様・配置済スキルを確認。通常新規開始から転職無効focus/Enterを先に再現。清めるは実到達と診断を区別し、無効状態の実入力と全状態不変を確認。未再現なら該当修正なし。前後同一入力、3/4人・正逆順、解放/未解放、転職候補の有効↔無効往復、仲間切替・再生成・戻る、説明閲覧、マウス操作。有効転職/清めるの既存確認画面・取消・確定とその状態変化を独立期待値で検証し、不可逆フラグ・場所条件を保つ。通常プレイと注入を区別。focus強制/pressed直呼びで成功化しない。原PNG実確認。
固定Godot4.7.2、editor/headless import、validate_assets.py --strict、check_frozen_files.py、run_locked_checks.py、関連既存画面検査を既存上限で実行。弱体化/省略/上限延長なし。途中失敗/警告保持、物理controller未検証を明示。

## 引渡し
作業前後差分・未push一覧、3payload全文・適用検証patch・原ログ/PNG/ハーネス/manifestをcheckout外へ保存しLibraryZIP ID/bytes/SHAを返す。remote push/PR/mergeはせず親が正式保存と全CIを行う。保存成功以前に完了としない。転送不可は原テキストの通常assistant分割引渡し。別のdisabled式非対称などへ範囲を拡大しない。
