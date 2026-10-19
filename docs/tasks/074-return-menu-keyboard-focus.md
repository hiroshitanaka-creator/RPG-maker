# 074 帰還メニューのキーボード選択を確認・修正

- 状態：未着手
- 担当：Codex GPT-6 Astra／High。正式GitHub保存と検収はルッカ。
- ブランチ：codex/task-074-return-menu-keyboard-focus
- 基点：8f2bc17b8c36b4304eb17de1a29e91e67a21cf57
- 依頼日：2026-10-19 JST
- 前提：既存の帰還機能を維持する品質修正。新しい場面・移動規則は作らない。

## 1. 参照すべき契約と事前確認
AGENTS.md、.scope-lock、docs/tasks/README.md、docs/dependencies.mdと既存帰還機能の仕様・検査を読む。R-01〜R-08、3人/4人・正順/逆順の既存受入、費用・解放条件・訪問済み判定・保存仕様は変更しない。作業前後の未コミット/未pushを確認し、他作業を混入させない。
親が現行mainのfirst_region_screen.gdとgame_root.gdを読取り、travel画面は_readyの初期フォーカス対象に含まれず、game_rootの方向キー時フォーカス補完もbattle/defeatだけであることを確認した。これだけで実害を確定せず、実画面で確認する。

## 2. 今回使用するスキル
$godot-dev-director、$godot-game-verification、$godot。実際の配置を確認して必要部分だけ読む。未導入なら導入しない。AGENTS.mdと.scope-lockを優先し、同梱.gdの直接コピー、新Autoload、GUT改変をしない。

## 3. 実装対象と具体要件
変更可能な全ファイルは scripts/ui/first_region_screen.gd、docs/tasks/074-return-menu-keyboard-focus.md（状態行のみ）、docs/tasks/reports/074-return-menu-keyboard-focus.md の3件。
既存メニューから帰還メニューを開き、マウスを触らず方向キーと決定で使用者と訪問済み目的地を選べるかを再現する。初期フォーカス欠落または使用者選択後の画面再構築で操作が途切れると確認できた場合、そのUIだけを最小修正する。無効ボタンを選択しない。戻る・再表示・使用者を選び直す操作を維持する。
機能不具合を再現できなければ不要なコード変更は行わず、実際の入力手順と結果を返す。別ファイルの変更が必要なら具体的な差分範囲を親へ返す。
帰還MP2・生存条件・訪問済みリスト・船移動・進行フラグ・保存・会話・画像・パレットを変更しない。本体に自動入力や診断フラグを追加しない。親以外はdocs/decision-log.mdとdocs/tasks/README.mdを編集しない。066、.scope-lock、test、既存検査、CI、assets/registry.json、project.godotは変更禁止。

## 4. 検証と受入条件
変更前の再現→最小修正→同じ入力で変更後の成功を確認する。検証用ハーネスはcheckout外 /workspace/task074-return-menu-focus-evidence/ に置く。既存検査の上限・期待値・コマンドを維持する。
3人/4人でメニュー初回表示、方向キー・決定のみの使用者/目的地選択、使用者を選び直す、戻る・再表示を確認。先頭の仲間が戦闘不能またはMP不足のケースで有効ボタンを選べることを確認し、全員不可は既存can_returnの判定を保持する。状態を診断注入した場合は通常到達と区別する。フォーカスを検証ハーネスから強制設定して成功にしない。
通常のreturn実行によるMP・場所・船の変化と、選択/取消のみではゲーム状態が変わらないことを確認。画像を実際に表示し文字・選択枠を確認する。
固定Godot4.7.2を公式URL/固定SHAで照合。godot --headless --editor --import --quit、godot --headless --import、python tools/validate_assets.py --strict、python tools/check_frozen_files.py、python tools/run_locked_checks.py、および既存の帰還/移動を検証する該当検査を実行する。終了コードだけでなく成功マーカー・SCRIPT ERROR・パースエラー・警告・リークを確認。失敗や未実施を分離し、検査を緩めて成功化しない。
提出は3ファイルの原bytes/差分と再現・検証原記録。remote push・PR・mergeは親が公式GitHub接続で行う。既存制約と今回の親保存方式の差を報告に明記。原物保全しLibraryへ返却、転送失敗を実装失敗と混同しない。正式提出SHAの全CIは親が確認する。main取込みは行わない。
