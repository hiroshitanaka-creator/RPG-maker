# 068 Windowsでセーブが消える隙間をふさぐ
- 状態：報告済み
- 担当：Codex（GPT-6 Astra / High、ルッカ経由）
- 依頼日：2026-10-12
- 前提：なし。最新main 9070038523ded3277fa45bf7615cf023aa08e786を基点とする。066系列とは独立。
- ブランチ：codex/task-068-safe-save-replace
- 担当の場所：scripts/game/game_session.gd の save_game・load_game、scripts/game/play_session_metrics.gd の write_json、この依頼書の状態行、docs/tasks/reports/068-safe-save-replace.md。必要最小限の新規テスト test/unit/test_safe_save_replace.gd と固定版Godotが生成する同名.uidの追加を許可する。
- 変えてはいけない場所：上記以外のゲーム規則・数値・画面、既存テスト、既存検査・期待値・締切、AGENTS.md、.scope-lock/、CI設定、固定SHA、066・067の既存ブランチと成果物。docs/decision-log.md・docs/tasks/README.mdはCodexが編集しない。

## 目的
Windowsの既存ファイル置換で、本物のセーブが一時的に失われる隙間をGDScriptのみでふさぐ。保存形式と旧セーブ互換性を維持し、現在の読み込み検証を一つも緩めない。

## 背景
依頼者はGodot 4.7.2のWindows DirAccess.rename_absoluteが、付け替え先の存在時に削除してから移動することを確認した。現mainのsave_gameは.tmpへの書込み後に本物へ直接renameし、load_gameは.tmpを読まない。
AGENTS.md、docs/tasks/README.md、素材規約と指定企画書、現行save_game/load_game/write_jsonを読む。066関連は依頼者により一時停止しており、この作業で再開・統合しない。

## 作業内容
1. 保存は、一時ファイルへ書込み・flush・エラー確認後、本物があれば付け替え先が存在しない状態で.bakへrenameし、その後.tmpを本物へrenameする。成功後に.bakを消す。失敗時は本物か.bakを失わない順序を守る。古い.bakや復旧元がある場合も最後の有効なコピーを途中で失わないよう扱う。初回保存に旧本物がない場合は復旧候補.tmpの保全を確かめる。
2. load_gameは本物が無い、または既存の全検証に失敗したときだけ、.bak、.tmpの順に同じ全検証を行う。JSON解析・SavedDocument.decode・数値/型復元・_valid_state・metrics・trial_id等の既存条件を残す。最初に通った候補を読み、候補が.bakまたは.tmpなら安全な手順で本物へ保存し直す。全部無効ならfalse。失敗した候補の副作用を次候補や現在状態に漏らさない。
3. PlaySessionMetrics.write_jsonも同じ保存順にする。既存のファイル形式、ゲーム規則、数値、画面を変えない。
4. 最小限の新規テストで下記を確認する。既存テストは変更しない。新規test/追加は今回依頼者が明示許可しており、GitHub上のCODEOWNERS承認を受ける前提。
5. LinuxとWindowsの実行結果を分けて記録する。Wineや模擬ファイル操作だけをWindows実機成功として扱わない。環境が使えなければ未実施と理由を報告する。

## 守ること
- GDScriptのみ。別の保存基盤・native addon・066の機構を持ち込まない。
- 検査の新しい手続き、固定SHAや世代証拠の仕組みを増やさない。今回の依頼者の明示指示により、この修正に見合う最小限の動作検証と既存回帰にとどめる。
- 既存検査の変更、skip、期待値緩和、時間延長、履歴改変、force pushは禁止。
- GitHub保存は公式GitHubのhiroshitanaka-ai経路のみ。クラウド内pushやMSIからの書込みを使わず、親が正式保存する。原資料は指定Drive、lucca-workspaceは報告等の文字のみ。
- PRは通常PR、レビュー要求先hiroshitanaka-creator。mainへマージしない。
- 実装上必要な小さな補助処理も、指定した保存・読込みの責務と2ファイル内に限定する。他の機能や共有保存機構へ範囲を広げない。

## 作業の前にしてほしいこと（計画）
基点・未コミット/未push・Godot実版を確認する。変更ファイルを列挙し、最後の有効な保存コピーが各段階でどこにあるかを整理してから実装する。Linux/Windowsの実行経路を確認する。

## 作業の後にしてほしいこと（自己点検）
LinuxとWindowsそれぞれで以下を実行し、結果を個別に記録する。
- 本物だけが有効
- 本物なし・.bakだけ有効
- 本物なし・.tmpだけ有効
- 本物破損・.bakが有効
- 全部破損：false
- 保存途中の各段階の中断状態からの復旧
- 旧形式の互換性、候補の優先順、同じ全検証、復旧後の本物、write_jsonの保存順
既存R-01〜R-08、素材strict、保護ファイル照合を実行する。変更対象が指定範囲内、既存テスト/期待値/締切不変であることを差分で確かめる。未実行は成功と書かない。

## 報告
docs/tasks/reports/068-safe-save-replace.mdに、変更ファイル、保存・読込みの手順、各状態のLinux/Windows別結果、実コマンド・既存検査結果、未確認・制限、自己点検を記載する。原ログと前後ファイルの照合情報をLibraryで親へ引き渡し、親がDriveに保全する。報告と状態を混同して完了を装わない。

## 完了の条件
指定の修正と各OSの実検証・既存検査・差分点検を終え、公式経路で正式保存と読み戻しを確認する。通常PRを作成してhiroshitanaka-creatorへレビュー要求し、結果を報告して停止する。未達があれば明示し、マージしない。
