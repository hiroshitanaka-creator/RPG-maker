# 054 保存復旧の独立レビューとWindows未達の修正案
- 状態：未着手
- 担当：Codex GPT-6 Astra／Medium（独立レビュー・技術修正案）
- 依頼日：2026-10-09 JST
- 作業ブランチ：codex/task-054-review-save-transaction
- 対象：053提出10de1ff1c78d7a62e96f51b52f6135f82bc3fea0
- 固定コード：e003b126de6695fa131e07a3db14c3011fb74f2e
- 前提：対象push/PR全78 CI成功。053担当は正式終了、未commit/未pushなし。ただしWindows対応・実ENOSPC・実別volumeは未達/未検証。

## 目的と変更範囲
053の契約と040 S3を独立に検証し、現状での受入可否と再現可能な指摘を返す。Windows向けゲームであるのに本体がLinux限定のため、その問題をCI成功と混同しない。修正は実装せず、既存契約を維持する最小の技術案・必要パス・検証環境・追加承認の要否を報告する。
変更できるのは本依頼の状態行と docs/tasks/reports/054-review-save-transaction.md だけ。本番/検査/workflow/fixture/過去証拠/保護/原画は読取りのみ。専用QAの一時probeは作成可だが、提出コードを書き換えて合格させない。実ユーザー保存・通常UI接続、OS/ユーザー権限設定変更、main反映、新PR、強制push、削除、追加委譲なし。



## 今回特有の未達を独立に確認
- path_ok のOS制限、GNU stat/ps/mv、symlink leaseが本体にあることを確認。Linux上の独立実行と、Windowsで機能しないコード上の根拠を分ける。実Windowsを動かさず「Windowsで試験した」と書かない。
- Godot標準APIだけで排他作成・no-clobber rename・生存owner判定・パス/同一volume/hardlink検査を満たせるか、公式APIと実コードを照合。できなければ最小の内部native I/O層等を案として比較する。Linuxだけ通る実装をWindows対応とせず、新しい外部依存・配布物・ビルド工程が必要なら具体化する。
- 053の既存172/2178/97kill/14伝播/scope2を弱めず、Windows実QAとLinux回帰で維持する修正範囲を提案する。実ENOSPC/別volume未検証を解消する専用QA案を、注入と実failureの違い・必要権限込みで示す。ユーザーPCの設定を勝手に変更しない。
- 単一writerの排他、PID再使用、recover/inspectの書込み有無、全失敗境界、同一raw別名、外部改変、キャッシュ依存、receiptと原物の矛盾を重点確認。実害と再現を示し、未検証だけで想像上のバグを断定しない。
- 専用QAという前提と、将来の本番公開に必要な保証を区別。S4/S5を今回勝手に実装しない。

## 完了条件
PASSまたは差し戻しを明示し、指摘ごとの重大度・対象・再現・期待/実際・最小修正範囲・未実行を報告。親が次の修正依頼を作れる情報を残す。
対象CIの原ログ/証拠と独立実行を区別し、実行予算・原assertを保持する。検査失敗は隠さず報告。自身状態を報告済み、指定branchへcommit/pushし最終SHAの全CI終了も確認。実装は行わず、判断案の採否は親・ユーザーに残す。
