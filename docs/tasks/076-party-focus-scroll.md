# 076 編成画面のキーボード選択とスクロール

- 状態：依頼済み
- 担当：Codex GPT-6 Astra／High。正式保存・検収はルッカ。
- 基点：8f2bc17b8c36b4304eb17de1a29e91e67a21cf57
- 日付：2026-10-20 JST

## 対象
既存の編成画面 _render_party の ScrollContainer にフォーカス追従設定がない。画面外の項目へTabで移動した際に選択枠が見えなくなる可能性は静的確認のみ、実害は未確認。現在のゲームから通常到達できる編成画面で先に再現し、成立した場合だけ最小修正する。旧凍結フローだけの問題なら変更せず報告する。

## 変更予定ファイル
scripts/ui/game_root.gd、docs/tasks/076-party-focus-scroll.md の状態行、docs/tasks/reports/076-party-focus-scroll.md の3件のみ。074/075の変更を混入しない。main統合、066、利用者PC、保護・test・CI・既存検査器・registry・project.godot・原画・規則・物語変更は禁止。docs/decision-log.mdとdocs/tasks/README.mdは親担当。

## 検証
AGENTS.md、素材規約、該当仕様・既存検査、存在するGodotスキルを先に読む。通常入力の編成到達、Tab/Shift+Tabと矢印・利用可能なコントローラー入力を区別。焦点所有者、各矩形、可視領域、scroll_verticalを実測。強制grab_focusやpressed直呼びだけで通常到達成功としない。3/4人・正逆順、項目少/多、仲間変更・装着後再生成・戻る再表示、マウス既存操作とゲーム状態不変を確認。変更前失敗と同じ入力で変更後成功、実画面の選択枠も比較する。未再現ならコードを変えない。
固定Godot4.7.2、editor import、headless import、validate_assets.py --strict、check_frozen_files.py、run_locked_checks.pyと該当画面検査を既存上限で実行。警告・SCRIPT ERROR・タイムアウト・失敗を保持し、検査弱体化・省略・時間延長で成功化しない。

## 引渡し
作業前後の追跡差分・未push一覧を記録。checkout外へ原ログ、比較PNG、再現ハーネス、manifestを保存。3ファイル全文と適用検証patchを含むZIPをLibraryへ保存しID/bytes/SHAを返す。remote push/PR/mergeはしない。正式Git保存・全CIは親が担当、そこまで完了としない。転送不可ならソース/ログ/manifestを通常assistantメッセージで分割引渡し。実害・原因が異なる場合は勝手に範囲を拡げない。
