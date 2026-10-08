# 051 保存codecの不正入力・証拠検証を修正する
- 状態：確認済み
- 担当：Codex GPT-6.1 Sol／High
- 依頼日：2026-10-08 JST
- 基点：050提出 05b6cb9ef4dc0072803824d4808014f1af049d1a
- 対象：050報告F1〜F5。049は差し戻し、050レビュー成果は確認済み
- 作業ブランチ：codex/task-051-fix-equipment-codec-validation

## 目的
050の再現可能な5指摘を解消し、049のS2契約を満たす。ゲーム規則・数値・物語・名称は変更しない。通常保存/UI公開、S3〜S5を実装しない。

## 変更可能な担当場所
- scripts/game/equipment_document_validation.gd：F2/F3の入口検証だけ
- scripts/game/equipment_save_codec.gd：F4の形状事前検証と必要な共通metadata検証への接続だけ
- tools/check_equipment_save_codec.gd、tools/fixtures/equipment-save-codec/：既存全ケース・条件を保持したF1〜F5の追加負例と証拠情報
- .github/workflows/equipment-codec.yml：049完成固定を保持した範囲監査の世代分離と修正版固定検査の必要最小接続
- 新 docs/verification/equipment-codec-validation/、今回依頼の状態行、今回報告 docs/tasks/reports/051-fix-equipment-codec-validation.md、docs/decision-log.md今回追記
保護、test/、.scope-lock/、addons/、原画/素材、既存他workflow・043〜046 wrapper、S1公開API・原検査・fixture、049過去証拠/報告、040計画・他依頼は変更しない。担当外変更が不可欠なら理由と最小差分を報告し、その変更のみ保留。

## 修正と機械受入
1. F1：scopeと未公開段階などの当時条件は049完成コード99e9d03d4e095b4627b510efd4806f82276617c9の当時checkoutに固定して全て維持。latestには継続する原動作・ケース・警告・失敗伝播・証拠完全性を適用し、後続レビュー文書だけで失敗しない。050/051名だけをallowlistへ足す対症療法にしない。元assertの当時/最新/後続対応表と、後続文書追加の正例・範囲逸脱の固定側負例を実行する。
2. F2：prepare_candidateは変更前metadataの構造・native値と型記述の一致を検証し、不正はパス付きerrors、documentなしで返す。050の7反例（null、version99、欠落path、重複path、TYPE_OBJECT、未知キー、float記述欠落）を全て拒否。合法上限変更後のmetadata再生成、HP0維持、回復/蘇生0は保持。
3. F3：context_errorsはcatalog参照の有効性・型・定義エラーを参照前に検証する。null-catalogを含む不正contextでSCRIPT ERRORを出さず必ず明示失敗、bytes/documentなし。GameSession通常入口・旧catalog定義は変更しない。
4. F4：位置検査が利用する構造を新codec側で先に検証する。050のroom=1/cell=[1,1]にparty=null、residents=nullをそれぞれ与える反例を警告/SCRIPT ERRORなしで拒否。既存位置処理・FirstRegion・保護検査を変更せず、合法な位置補正差分の提示と原入力不変は維持。
5. F5：条件数を独立固定期待と照合し、producerとlogが同時に1条件へ偽装されても拒否。成功document.gdvの完全性を原観測hash/サイズ等と実bytesで確認し、空・改変・欠落を拒否。原Godotが成功documentと全値/型/順序往復を保証する点も保持。単に実行後manifestを作って改変bytesを追認しない。固定側の112/723は当時原本で維持し、修正版の追加条件数は独立期待・ID・実際を明示して対応させる。
6. 050付録を変更前/後で再現し、元実装では各不備が再現し、修正版では全拒否と入力不変が成立する証拠を残す。元の原検査112ケース/723条件・13伝播を削除/弱化/期待再生成で通さない。修正版では追加全ケース・全条件を実行し、エラー発生をexit0だけで成功に数えない。
7. 050で成功した合法進行・加入・HP0・共通支給12→22の正例を保持。auditのinstance集合一致を無条件に外さない。将来入手機能・未採用係数を今回の修正へ含めない。

## 証拠・CI・提出
開始時の未commit/未pushと関数契約・050全指摘を確認。作業は隔離QA/専用入力だけで実行し、実ユーザー保存・既存アプリ・設定を操作しない。
Godot4.7.2、既存job/原検査の予算は維持（新codec原検査120秒/import600秒/各job15分）。時間不足は独立分割と証拠で対処し、上限延長・skip・continue-on-errorなし。
049固定原本の全条件、修正版固定コードと最新回帰、新旧原検査・旧142/10全文比較、R全8・保護26・同一最終SHA全CIを検証。コードを完全SHAで固定し、原入力・全結果・ログ・hash・実exit・失敗時証拠を別に保管。固定後の本番・検査・fixture不変を照合。
報告は5件ごとの変更前/後、実コマンド・全ケースID/件数・失敗伝播・型/bytes保持、変更一覧、固定/最新対応、未実行を記載。自身状態を報告済みにし、指定branchへcommit/push。PR32へ親が取り込むため新PR/mergeはしない。main直接書込み・強制push・削除・履歴改変・追加委譲なし。既存ローカル作業を変更しない。
