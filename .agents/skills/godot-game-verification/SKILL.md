---
name: godot-game-verification
description: RPG-maker の Godot 4.7.2-stable / GDScript に対するヘッドレス決定論的検証、実行ログのエラー・警告監査、コード変更後の回帰チェックで使用する。既存の凍結 verify・GUT・CI を優先する。シナリオ執筆・会話テキスト作成・物語構成では使用しない。
---

> - 規約1：本スキルは Godot 4.7.2-stable / GDScript 実装・検証の知識リファレンスとして使用する。
> - 規約2：ディレクトリ構成・命名規則・テスト実行コマンド・受入条件については、常にリポジトリの AGENTS.md、docs/tasks（伝言板）、および .scope-lock（凍結受入契約）を最優先とする。
> - 規約3：本スキル内の汎用スクリプトや新規プロジェクト用アーキテクチャで、本リポジトリの既存システム（人間12職・魔物8職・装着枠・侵蝕度・魔物化・49拠点・80話・セーブ復帰・GUTテスト・CI）を上書き・置換してはならない。

## RPG-maker での適用範囲

- 同梱 `scripts/run_checks.py` のPASSはRPG-makerの受入証拠にしない。この補助runner単体は通常WARNINGの全検出と固定Godot版の強制照合を満たさず、既定出力先 `artifacts/checks/` は本リポジトリの一時出力規約にも一致しない。検査の入口は `tools/run_locked_checks.py`、`tools/check_frozen_files.py`、依頼書および既存CIのコマンドとする。固定Godotの取得元・SHA-256・実測版を既存規定で確認し、元の警告判定・成功マーカー・件数・締切を維持する。既存コマンドの一時出力先 `.tools/` を尊重し、保存すべき原資料は依頼書指定先へ残す。出力先だけ変更して同梱runnerの実行許可や受入成功と解釈しない。
- 受入判定は既存の `tools/run_locked_checks.py`、`tools/check_frozen_files.py` と CI のコマンドを使う。同梱 `scripts/run_checks.py` は補助検証用であり、凍結 verify の代替ランナーにしない。
- 上流の `--filter`・`--skip-import` は必須検査や main 取り込み後のインポートを省く許可ではない。元のタイムアウト、成功マーカー、全警告の検出条件を維持し、生ログも確認する。同梱ランナーの成功だけで既存 CI の成功としない。
- 同じ Godot 4.7.2-stable のビルド・固定シード・入力・初期状態で比較する。追加ログの保存先は依頼書に従い、ゲーム素材や既存の検証記録を上書きしない。
- 以下の上流本文、同梱 `references/`・`scripts/`・`templates/` は汎用資料であり、この適用範囲に従って読む。記載された手順を一括実行しない。`scripts/` 等の相対パスはこのスキル内のパスであり、ゲーム本体の同名ディレクトリへの配置指示ではない。
- 物語・会話・連作エピソード仕様は `rpg-maker-storyteller` が担当する。物語と実装が混在する依頼では、文章の作成とコード変更を分けて担当スキルを選ぶ。
- 上流の Related Skills / Prerequisites / Master / Optional skill は追加導入や自動読み込みの指示として使わない。未導入スキル（`godot-master` を含む）を取得せず、AGENTS.md のルーティングと既存コード・公式APIを参照する。
- 規約3の49拠点・80話の記載は既存素材の保護を意味する。旧本編の拡張・復活は行わず、世界マップ攻略型の現行仕様を優先する。

出典・ライセンス・変更記録：[UPSTREAM.md](UPSTREAM.md)。

---

# Godot Game Verification

Run headless Godot checks deterministically and read the report. Use this
skill when adding or running automated Godot verification (scene audits,
determinism gates, content validation). It needs only a Godot binary, a
project, and a manifest — no other skill, root module, or game-specific
setup.

## Workflow

1. Select the affected checks; run the smallest subset that covers the change
   (`--filter SUBSTRING`). Expand for an affected dependency, failure or
   repository-required gate; do not add an unrelated full sweep to a small edit.
2. Run the import pass once per session (it is on by default); pass
   `--skip-import` only for repeat runs in the same unchanged checkout.
3. Run the runner, then read `metadata/report.json` in the run directory:

```bash
python3 /path/to/installed/godot-game-verification/scripts/run_checks.py \
  --project PATH --manifest checks.json
```

For the manifest schema, log capture rules, and timeout behavior, read
[references/checks.md](references/checks.md).

## Constraints

- Godot errors can exit zero or hang: a check passes only with exit 0, its
  success marker, no `SCRIPT ERROR` / parse / compile / `ERROR:` lines, and
  no leak warnings — inside its timeout.
- Structural assertions (node counts, hashes, invariants) are separate from
  rendered captures (screenshots, video); never judge one by the other.
- Reject empty fixtures: a check that ran zero assertions or produced no
  output is a failure, not a pass.
- Never auto-overwrite a golden baseline; regenerating one is an explicit,
  reviewed step with a diff of what changed.
- Pin the Godot version for structural hashes: digests are comparable only
  between runs of the same engine build (the report records the probed
  version).
