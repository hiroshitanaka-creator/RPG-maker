# 保護台帳反映後の確認一覧

2026年9月25日。「保護フックが拒否した1ファイルを反映」と「人間の試しプレイ以外の残タスク一覧」の依頼に対応する。物語の内容は記載しない。

## 今回反映したもの

`.scope-lock/frozen-files.json` に準備済み23件の台帳を反映した。旧21件から既存3件の承認済みハッシュを更新し、新規テストとUIDの2件を追加。`python tools/check_frozen_files.py` は23件一致、終了0。テストや実装、閾値は今回変更していない。自動承認レビューの最初の拒否に対し、AGENTS.mdの承認済み例外を示して同じ操作を再審査し、許可された。保護機能を解除していない。

## 人間試遊以外の残項目

| 項目 | 状態・依存関係 | 完了を確認する方法 |
|---|---|---|
| 台帳反映後のCIを確認し、改訂をmainへ取り込む | この反映コミットのCI成功を確認してから取り込む。以前のCIの成功や部分検査の成功を流用しない | GitHub Actionsの対象headSha・全ジョブの成功、origin/mainのコミットを照合する |
| AC-01〜AC-03をscope-lock本体へ正式登録する | 専用検査とCI接続は実装済みだが、spec.lock.jsonのrequirementsはR-01〜R-08の8件のみ。additional-acceptance-v1.md末尾にも正式登録未実施と記載。今回指定された保護台帳1ファイルの反映とは別の契約変更 | 保護契約の改訂手続きを経て3条件とverifyを登録し、既存8件と追加3件を実行する。固定入力・閾値を変更しない |
| 古い進捗文書の入口を整理する | development-status.mdには「60時間の内容制作は未完了」「職別行動条件は未解決」等の旧状態が現在形で残る。remaining-v1-work.md等も複数時点を含む。履歴の保存は必要だが現在の残件との混同がある | 現行状況への参照と履歴の境界を統一し、古いFAILや未制作件数を現在の作業表へ再計上しないことを文書間で照合する |

ゲーム機能の追加実装を必要とする未達は、今回照合した現行作業表・改訂記録からは新たに確認されなかった。ただし「人間試遊以外は残件0」とはしない。上記の契約登録と文書整理は残る。未知の不具合がないという主張ではない。

## 範囲を分けて扱うもの

- 提供画像の外部生成条件・他用途の許諾は提供者情報が未確認。現在の個人利用の制作範囲に公開・配布は含まれないため、今回のゲーム実装の停止条件にはしない。
- 人間による初見時間・面白さ・理解・難易度等はPLAYTEST_QUEUE.mdに分離し、本一覧の件数から除外する。約60時間を自動操作から実測済みにしない。
- 依頼の空欄だった「3.」には内容がなく、新しいタスクを推測して追加しない。

## 照合元と限界

AGENTS.md、spec.lock.json、保護台帳、open配下のエスカレーション4件、remaining-v1-work.md、spec-status.md、development-status.md、human-playtest-readiness.md、long-campaign-finish.md、integrated-task-closure.md、mastery-actions-delivery.md、v1-final-values.md、additional-acceptance-v1.md、CI定義と既存の実行記録を照合した。GitHubのopen Issueは取得時0件。

scripts/・tools/・test/のTODO/FIXME/NotImplemented/単独passの検索では、battle_state.gdの通常攻撃分岐にpassが1件ある。直前のenemy/physicalの既定値を使う分岐であり、未実装スタブとしては数えない。全コードの新規網羅監査や人間試遊を実施したという記録ではない。

この文書作成時点では反映後CIの実行前。CI結果とmainへの取込みはGitHubの対象コミットで判定し、今回の最終報告に実際の結果を記載する。
