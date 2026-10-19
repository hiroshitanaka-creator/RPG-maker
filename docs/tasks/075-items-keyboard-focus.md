# 075 どうぐメニューの無効項目とキーボード操作

- 状態：依頼中
- 担当：Codex GPT-6 Astra／High。正式保存・検収はルッカ。
- 基点：8f2bc17b8c36b4304eb17de1a29e91e67a21cf57
- ブランチ：codex/task-075-items-keyboard-focus
- 日付：2026-10-20 JST

## 1. 契約と事前確認
AGENTS.md、.scope-lock、docs/tasks/README.md、素材規約、既存どうぐ使用仕様を読む。3人/4人・正順/逆順、原画、状態・保存・回復薬効果と条件、全既存受入を維持。074は別PR50で未統合・制作終了済み。074差分をこの提出へ混ぜない。

## 2. 使用スキル
$godot、$godot-game-verification、$godot-dev-director。存在と内容を確認、未配置なら導入せず明記。リポジトリ契約優先、同梱コードの直接コピーなし。

## 3. 対象と具体要件
予定変更は scripts/ui/first_region_screen.gd、docs/tasks/075-items-keyboard-focus.md の状態行、docs/tasks/reports/075-items-keyboard-focus.md の3件だけ。親は現行_itemsが無所持の地図・満HP/戦闘不能/薬なしの仲間をdisabledにするが、_buttonは無効項目のfocusを除外していないことを読取り確認。実害は未確定。通常メニューからキーボードだけでどうぐを開き、無効項目へ選択枠が移り決定しても反応しない等の再現があるか先に確かめる。再現した場合だけitemsの無効項目を適切に除外する最小UI修正。原因不一致なら推測で直さない。
有効対象へ移動・決定、薬使用後の画面再生成、戻る・再表示、地図所持/未所持、薬0/1/複数、満HP/負傷/戦闘不能、全員使用不可を確認。ゲームの使用可否判定や薬効果・個数・死亡条件は変更しない。ハーネスからfocus強制やButton.pressed直呼びで成功化しない。マウス既存操作も保持。
066、074ブランチ、main、.scope-lock、test、保護検査、既存checker、CI、registry、project.godot、物語・規則・画像は変更禁止。docs/decision-log.mdとdocs/tasks/README.mdは親のみ。

## 4. 検証と受入
変更前失敗と同じ入力で変更後成功、状態全体の変化/不変を独立期待値と照合。診断注入と通常到達を区別。3人/4人・正順/逆順で上記境界を検査、実画像で選択枠/文字を確認。新規一時ハーネスと原ログはcheckout外 /workspace/task075-items-focus-evidence/ に置く。
固定Godot4.7.2照合、既存上限でeditor import、headless import、validate_assets.py --strict、check_frozen_files.py、run_locked_checks.py、該当画面既存検査を実行。成功マーカー・SCRIPT ERROR・パース・警告・リークを監査し失敗を保持、時間延長/省略なし。実害がなければ変更せず証拠を返す。
原bytes・diff・ログ・画像・manifestを返す。既存担当に許可された親保存方式で、remote push/PR/mergeなし。GitHub正式保存とCIは親が実施。Libraryが失敗すれば同じ要求を連打せず、完全なソース/ログ/manifestを通常assistantメッセージで分割引渡し。正式保存・全CI以前に完了としない。
