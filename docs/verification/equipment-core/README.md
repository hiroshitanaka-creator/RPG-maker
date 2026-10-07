# 036 の独立装備基盤の検証

実行コードSHA：`993929b43f311ec6beec8e340fe2c422274171f5`。報告コミットは本番・検査器を変更しない。

- `execution.json`：別checkoutの実行SHA・コマンド・実測エンジン版・公式ZIPと本番3ファイルのSHA-256。
- `checks.json/pinned-check.log`：指定Godot4.7.2、新検査5394件・400職切替・失敗0。現行CIとは別の実行証拠。
- `requirements.json/requirements.log/R-01.log`〜`R-08.log`：既存凍結verifyの全実行・終了コード・件数・失敗一覧。R-07 A01〜A14、R-08全17テスト/2302assertion。
- `import.log/pinned-import.log`：素材取込み、エラー/警告なし。
- `assets.log/frozen.log/frozen-after.log/scope.json`：素材・保護26・許可範囲・既存接続ゼロ。
- `red.log`：実装前の未実装モジュールによるpreload失敗。PASSログではなく、assertion実行証拠には使わない。
- `check.log`：固定前の作業checkoutでの同じ追加検査成功。

報告・API契約・後続未接続は `docs/tasks/reports/036-equipment-core.md`。最終提出SHAと同一SHA全CI結果はdraft PR #27本文の「最終提出確認」を参照。新検査のCI組込みは未実施。ゲームの転職許可、保存移行、支給、UI、実戦効果の成功をこのfixtureから推定しない。
