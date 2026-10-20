# 077 編成画面の無効な装着ボタンとキーボード選択

- 状態：依頼済み
- 担当：Codex GPT-6 Astra／High。親が正式保存・CI検収。
- 基点：8f2bc17b8c36b4304eb17de1a29e91e67a21cf57
- 日付：2026-10-20 JST

## 対象・根拠
既存 _render_party の装着Buttonは技候補0件/転職未解放でdisabledとなるがfocus_mode未調整。076通常ニューゲームの原JSONでTab/ShiftTabが空の技選択横の装着へ入ることを確認した。ただしdisabled値とEnter後挙動は未測定。先に通常入力で実害を再現し、成立した場合のみ装着Buttonに限定した最小focus修正。OptionButton/PopupMenuは説明閲覧に必要なため除外しない。職業・清める等へ対象を拡大しない。

## 範囲
変更予定はscripts/ui/game_root.gd、docs/tasks/077-party-disabled-focus.md状態行、docs/tasks/reports/077-party-disabled-focus.mdの3件のみ。074/075/076の変更を混入しない。076スクロール不具合は基点既知として区別。main統合保留、066/利用者PC/保護/test/既存検査器/CI/registry/project.godot/原画/物語/規則/装着条件不変。docs/decision-log.mdとdocs/tasks/README.mdは親担当。

## 検証
AGENTS.md・素材規約・該当仕様・配置済みGodotスキルを確認。現行ニューゲームからEscape→編成へ通常キーで入り、focus所有者/disabled/Enter無反応/全状態不変を記録。注入ケースは通常到達と区別。前後同一入力で無効装着をスキップし、有効装着と戻るへ到達できること。3/4人・正逆順、技0/1/複数、未解放/解放、空枠/満枠、仲間変更・装着解除後再生成、技説明閲覧・マウス操作を検証。focus強制/pressed直呼びで成功にしない。未再現なら無変更。
固定Godot4.7.2、editor import/headless import、validate_assets.py --strict、check_frozen_files.py、run_locked_checks.py、関連既存画面検査を従来上限で実行。失敗・警告を保持し、弱体化/省略/上限延長なし。原PNGを実確認し、実機コントローラー未検証と仮想入力を区別。

## 引渡し
作業前後差分・未push一覧、3payload全文・適用検証patch、原画像/ログ/ハーネス/manifestをcheckout外へ保全し、Library ZIPのID/bytes/SHAを返す。remote push/PR/mergeなし。親が正式保存と全CIを担当し、その前に正式完了としない。転送不可は原テキストを通常assistantメッセージで分割する。未達・必要な承認は具体的に報告。
