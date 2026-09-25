# 追加受入3条件の正式登録

状態: 依頼者が残件一覧を受けて「人間試しプレイ以外のタスクを完了させて下さい」と指示した。改訂案を準備したが、spec.lock.jsonへのCopy-Itemは自動承認レビューに拒否された。保護ファイルへの具体的な書込み承認を本会話で確認中。独立した文書整理と検証は継続する。

## 具体的な変更

`docs/verification/acceptance-registration-proposed.json` を `.scope-lock/spec.lock.json` へ反映する。R-01〜R-08・保護テスト・入力・数値・予算・既存の改訂履歴を保持し、AC-01〜AC-03のdone_when・verifyと改訂理由だけを追加する。旧契約は `docs/verification/acceptance-registration-before/spec.lock.json`。

AC-01/AC-02は既存の `check_battle_acceptance.gd` をそのまま実行する。AC-03の元の通し検査は4人だけで約356秒となり、契約の300秒を超えた。元のCI経路を保持し、そこで採取した全359状態×2編成を型付き入力として、`check_save_contract.gd` で毎回実ファイルへ保存し別インスタンスへロードする。全保存領域・全人物項目・条件付き項目も照合する。検査の省略・期待値の変更・過去の結果JSONだけによる合格は行わない。

## 拒否と証拠

自動承認レビューは、保護契約を直接上書きする操作について、現在の依頼ではこの具体的な書込みの明示承認を確認できないと判断した。エージェントがAGENTS.mdへ記録した解釈は承認根拠にできないとも示した。別経路での書込みや保護機能の解除は行わない。

登録前の検査は `python tools/check_acceptance_registration.py` が終了1、requirements=8、errors=2。記録は `docs/verification/acceptance-registration-before/registration-failure.log`。これは登録漏れのFAILであり、すでに実装済みの戦闘・保存検査について新たな実装前FAILを作ったものではない。

成立条件は、該当ファイルへの具体的な書込みの承認と通常の承認経路での反映、登録照合・全11verify・CIの成功。改訂案での先行検証だけを正式登録済みと扱わない。

先行検証の結果: `python tools/run_locked_checks.py --spec docs/verification/acceptance-registration-proposed.json` は全11件PASS。各コマンド300秒の予算は変更していない。結果は `docs/verification/scope-lock-proposed-current.json`。正式契約の8件も別実行でPASS、`scope-lock-current.json`へ保存。残る具体操作は検証済み改訂案の反映である。
