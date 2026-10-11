# 065 保存QAの固定世代と最新継続検査の分離

- 状態：作業中
- 作成日：2026-10-11 JST
- 担当：Codex実装。受入・タスク表・決定ログはルッカ。
- 環境：保存済みRPG-makerクラウドCodex環境、GPT-6 Astra／High。使用量への影響は不明。
- 基点：061提出6ca6ccea70491cf66c8a4f478b142f1137f23874
- 作業ブランチ：codex/task-065-separate-save-qa-generations
- 承認：依頼者は2026-10-11 08:51 JST、提示済みA（059固定範囲と最新継続検査の世代分離修正、既存診断配線・集約器2件＋専用検査2件＋依頼・報告・証拠、クラウドAstra/High）を採用した。本番最適化・時間延長・原assertion変更の承認ではない。
- 依存：061終了後の逐次発注。062〜064は別原画案件としてmain統合済み。065へmainを取り込まず、指定基点で保存系列を扱う。

## 目的
scope059が059完成後の専用文書・証拠以外を拒否する段階限定条件を、後続060/061の最新HEADへ適用している問題を修正する。059完成時の検査と全正負を固定checkoutで維持し、最新側の監督・回収・bytes不変条件を別に検証する。単純な許可パス追加、失敗無視、検査削除で緑にしない。

## 全変更予定ファイル
変更：
1. tools/fixtures/equipment-save-transaction-platform/diagnostic_ci057.py
2. tools/fixtures/equipment-save-transaction-platform/diagnostic_evidence059.py
3. docs/tasks/065-separate-save-qa-generations.md（状態行のみ）
新規：
4. tools/fixtures/equipment-save-transaction-platform/generation_contract.py
5. tools/fixtures/equipment-save-transaction-platform/test_generation_contract.py
6. docs/tasks/reports/065-separate-save-qa-generations.md
新規証拠（prefix docs/verification/task065-save-qa-generations/）：
7. README.md
8. assertion-map.json
9. code-fixed-sha.txt
10. hashes.json
11. local-results.json
12. local-stdout.log
13. local-stderr.log
14. local-artifacts.tar.gz.b64
15. linux-results.json
16. linux-artifacts.tar.gz.b64
17. windows-results.json
18. windows-artifacts.tar.gz.b64
19. ci-results.json
20. scope-diff.json

追跡する変更は上記20ファイルのみ。原証拠の詳しいargv/exit/log/全bytesは該当archiveに入れ、内部manifestに全memberサイズ/hashを記録する。未実施のOS結果はNOT_RUNと理由をJSONへ書き、架空archiveを成功証拠として作らない。必要な追加ファイルや対象外変更が生じる場合は先に親へ具体的に報告し、自己判断で範囲を広げない。docs/tasks/README.md、docs/decision-log.mdは変更しない。

## 読むもの
AGENTS.md、docs/tasks/README.md、061依頼・報告全文、059依頼/報告、scope059.py、diagnostic_ci057.py、diagnostic_evidence059.py、diagnostic_fixed057.py、run_ci.py、equipment-transaction-platform.yml。旧assertionと固定/最新の実配線を確認してから実装する。

## 実装条件
1. 059固定コード41a34ea33fe184274e6722c88cdbca2a7ffd3708の別checkoutで当時のscope059.pyと全10正負例を実行する。当時の登録/基点/期待値を混同しない。固定SHAは省略形を使わない。
2. 最新側のcapture-tests12件、capture059追加27件、計測12sample、監督・回収・bytes不変条件は最新HEADで実行し、固定版成功で代替しない。
3. 旧assertionを「当時だけ」「最新でも継続」「今回承認された配線・証拠契約の新条件」に分類した機械可読対応表を用意し、未配置・重複による欠落を検査する。当時だけの条件も固定側で毎回残す。
4. generation_contractは本番・監督・原検査等の不変、今回の4専用コードと所定文書/証拠以外の差分拒否を検証する。配線・集約器を包括的に除外せず、専用正負例で新契約を検証する。
5. 世代/SHAすり替え、固定コード改変、最新継続条件欠落、失敗隠蔽、証拠改変、未列挙差分、欠落記録、timeout/終了未確認をすべて非0で拒否する。正例だけで自己一致させない。
6. diagnostic_evidence059の旧schema条件は保持し、新schemaは固定/最新それぞれの完全SHA、argv、exit、原log、全member hashと失敗伝播を厳密に収集する。現状の診断5件/setup1件固定を黙って緩めない。
7. 既存CLI・artifact先を維持し、.github/workflows/の変更なしで両OS・両phaseへ接続する。現workflowが必要SHAをfetchすることを確認。Windows、shallow履歴、15分job予算を実証する。YAML変更が必要なら具体差分と理由を親へ提出して承認待ち、自己変更しない。
8. 今回完成コードのSHAを固定し、完成後の文書・証拠追記と最新回帰を区別する。今回の検査も後続の正常な段階移行を無制限に拒否する作りを再生産しない。

## 維持・禁止
scope059.py、旧固定SHAファイル、原証拠、process_capture、取引driver、本番scripts/native/addons、assets、project.godot、test/、.scope-lock/、保護検査、AGENTS.md、CI YAMLは変更しない。削除・強制push・履歴改変・skip・continue-on-error・成功までの選別再実行・原予算延長は禁止。
172ケース/2178条件/97kill、16伝播、6安全境界、R-01〜R-08、保護26件を維持。本体の時間未達は未達のまま記録し、今回の診断修正でF1/S3成功とはしない。
F4実ENOSPC/別volume、inspect/子timeout原因、本番最適化、Windows060採取、通常UI接続は別範囲。環境設定やmount/VHD等は変更しない。

## 受入・出口
- 059固定全10正負、最新capture12/27/12sample、新世代契約の全正負、証拠原bytes/hash・失敗伝播の機械検証結果を保存する。
- 両OSの現CIで固定/最新/本体/診断を分ける。全最終CIの終了件数と結果を確認する。アクセス拒否は迂回せず未確認として親へ戻す。
- import、素材strict、R8、保護26、全変更20ファイル範囲を確認。検査不能は環境・理由・必要条件を記録する。
- gitの未コミット/未pushを前後で確認。許可された20ファイルだけcommit/pushし、remote一致と最終SHAを報告。
- PR作成・mainマージは今回行わない。親が独立レビューと保存系列全体の受入を判断する。
- 報告に未達/未検証、失敗の原証拠、旧assertion対応表、対象世代を明記。重大な物語の詳細は不要。
