# 081 CIの帰還先一覧失敗：再現と互換修正案

現状：CI失敗を再現済み。本番修正はまだ行っていない。正式完了ではない。

## 原因と固定条件

失敗元headは `a04172a134971610e6760f7ff602451901130642`。CIと同じ `python tools/check_task009_assertion_map.py` は成功、`python tools/check_region2_village_regression.py --commit "$GITHUB_SHA" --godot ../godot` は7630判定中1件でexit1。5つのrestartは全PASS。原出力・runtime JSON・保存は `docs/verification/task-081-ci-fix/before*` に保持。

失敗assertionは既存 `tools/check_region2_village_regression.gd:372` の `FirstRegionTravel.destinations()==contract["destinations"]`（既存帰還先の全件と村の船先）。既存の無引数APIの閉じた5件を081で直接6件へ拡張したことが原因。世界2セルや新dockの静的到達性を理由にこの失敗を無視しない。lifecycleの正例も同じ継続検査を呼ぶため、無関係なNPC正例までこの1件で失敗する。

既存5件のID・順序・入口・船先・MP条件はすべて保持する。009のassertion分類・固定fixture・最新回帰・故障注入・CI・保護・契約・上限は変更しない。

## 先に示す両立案（互換APIの追加）

1. `FirstRegionTravel.destinations()` は既存の無引数APIとして5件・全フィールド・順序を元通り維持する。新港をvisitedに含む保存を渡していない呼出しでも結果は同じで、検査プロセス・環境変数・呼出元を判別しない。
2. 保存状態を明示的に受け取る `destinations_for(saved)` を追加する。既存5件はそのまま、新港を実際に訪問済みの保存では採用済み新港の帰還先だけを追加する。これは従来UIの「訪問済みだけを表示」という既存規則を使う本番用の拡張であり、新フラグ・新規則・第2の転移機能は作らない。
3. 本番の帰還画面と帰還実行は同じ `destinations_for(saved)` を使う。新港の通常メニュー帰還、MP2、生存者条件、人物/船の着地、未訪問・未知先の拒否を維持する。既存の無引数APIを使う既存クライアント/回帰は完全互換。
4. 専用の非保護検証で、無引数の5件完全一致（新港訪問の前後も一致）、旧保存時の候補不変、新港訪問済み時の拡張候補、未訪問拒否、通常UIの新港帰還を確認する。既存009検証・lifecycle故障注入は無変更のまま全て再実行する。

新港を無効化したり、既存検査からだけ新港を隠したりする修正ではない。既存APIの契約を維持し、本番の保存文脈を扱う互換拡張として接続する。固定条件そのものを変更する段階移行はこの案では不要と判断する。正式な契約変更が必要だと分かった場合は実装で回避せず具体条件を報告する。

## 変更予定の全ソースと証拠

- scripts/world/first_region_travel.gd（既存APIを復元し文脈APIを追加、帰還実行の参照先を変更）
- scripts/ui/first_region_screen.gd（帰還UIの参照先を同じ文脈APIへ変更）
- tools/check_task081_return_catalog.gd と .uid（追加の互換・新港の正負例）
- docs/tasks/reports/081-ci-return-catalog-compatibility.md、本体081報告の最新状態
- docs/verification/task-081-ci-fix/ の再現・修正後・原コマンド・全差分/SHA・画像

海域2セル・dock・原画・5室・保存形式・既存検査・保護・CI・親台帳は変更予定なし。変更が必要になった場合は先に追記する。調査・実装・証拠の既存commitは保持し、通常commit/pushで進める。
