---
name: godot-dev-director
description: RPG-maker の複数システムにまたがる GDScript 改修について、影響範囲・実装順序・既存セーブと実行状態の保護・回帰検証を計画するときに使用する。単独機能は担当スキルを選ぶ。シナリオ執筆・会話テキスト作成・物語構成では使用しない。
---

> - 規約1：本スキルは Godot 4.7.2-stable / GDScript 実装・検証の知識リファレンスとして使用する。
> - 規約2：ディレクトリ構成・命名規則・テスト実行コマンド・受入条件については、常にリポジトリの AGENTS.md、docs/tasks（伝言板）、および .scope-lock（凍結受入契約）を最優先とする。
> - 規約3：本スキル内の汎用スクリプトや新規プロジェクト用アーキテクチャで、本リポジトリの既存システム（人間12職・魔物8職・装着枠・侵蝕度・魔物化・49拠点・80話・セーブ復帰・GUTテスト・CI）を上書き・置換してはならない。

## RPG-maker での適用範囲

- 本リポジトリは既存の2D・ターン制 RPG。上流の3D、ホラー、手続き生成、新規プロジェクト向けの導線を適用しない。専門領域は AGENTS.md の導入済み8スキルの表で選ぶ。
- 変更前に既存クラス、公開API、セーブの版と復元経路、乱数とフラグの所有者を確認する。既存状態を保持した小さな変更として実装し、新規開始・旧保存・復帰の影響を既存検査で確かめる。
- このスキルは複数エージェントの起動や範囲拡張を許可しない。既存の権限と依頼書に従う。
- 以下の上流本文、同梱 `references/`・`scripts/`・`templates/` は汎用資料であり、この適用範囲に従って読む。記載された手順を一括実行しない。`scripts/` 等の相対パスはこのスキル内のパスであり、ゲーム本体の同名ディレクトリへの配置指示ではない。
- 物語・会話・連作エピソード仕様は `rpg-maker-storyteller` が担当する。物語と実装が混在する依頼では、文章の作成とコード変更を分けて担当スキルを選ぶ。
- 上流の Related Skills / Prerequisites / Master / Optional skill は追加導入や自動読み込みの指示として使わない。未導入スキル（`godot-master` を含む）を取得せず、AGENTS.md のルーティングと既存コード・公式APIを参照する。
- 規約3の49拠点・80話の記載は既存素材の保護を意味する。旧本編の拡張・復活は行わず、世界マップ攻略型の現行仕様を優先する。

出典・ライセンス・変更記録：[UPSTREAM.md](UPSTREAM.md)。

---

# Godot development director

Turn the requested change into a playable, reviewable result. This pack is
strongest in GDScript and procedural 3D. Adapt to the existing project; do not
convert languages, renderers, scene architecture or test frameworks by default.

## Establish the working contract

1. Read the project's instructions, `project.godot`, relevant scenes/scripts and
   existing checks. Record the installed Godot version and target platform.
2. State the intended behavior and smallest existing check that can verify it.
   For visual changes, identify one representative camera, scene and light setup.
3. Find the ownership boundary: generated data, live scene nodes, persistent
   state, presentation, or tools. Keep unrelated systems out of the change.
4. Build and check one representative case before expanding assets, themes or
   level variants. Preserve a reproducible seed/state when generation is involved.

For an empty project, first establish one working loop and its controls. For an
existing game, extend its architecture and preserve its look and player rules.
Ask only for decisions that materially affect the result and cannot be inferred.

## Select guidance

Load an installed specialist only when it helps the task. Specialists are
optional, not hard dependencies; if missing, inspect the equivalent project
tools and proceed with a focused workflow. Do not assume sibling installation.

| Task | Optional skill |
| --- | --- |
| Imports, runtime checks, captures, regressions | `godot-game-verification` |
| Seeded rooms, streaming, object state, live rebuilds | `godot-procedural-worlds` |
| Hitches, loading, navigation or rendering costs | `godot-performance-workflows` |
| Blender/GLB props, materials, collision, placement | `godot-3d-prop-integration` |
| Coordinating scares, quiet periods and witnessed events | `godot-horror-pacing` |
| VHS/CRT, camera interference and in-world displays | `godot-analog-presentation` |
| Cause-based aging, stains, contact wear and overlays | `godot-environment-wear` |

For 2D, multiplayer, C#, console deployment or a renderer-specific feature,
recognize the pack's limited coverage and consult that project's tools and the
matching official documentation. Do not impose procedural 3D patterns on them.

## Execute proportionately

- Use existing interfaces and tests. Isolate pure decisions from scene effects
  where that makes the requested behavior reproducible.
- Keep gameplay RNG separate from visual/event RNG so cosmetic work cannot
  silently change layouts or encounters.
- Treat loaded Resources as potentially shared. Duplicate mutable per-instance
  materials deliberately; retain reuse for immutable geometry and textures.
- Keep old collision/state valid while replacements are prepared. Report any
  engine/thread restrictions before moving construction to a worker thread.
- If delegation is available and authorized, assign disjoint ownership and a
  concrete deliverable; retain integration and final verification locally.
  The skills do not require delegation, a model, a paid API or an agent host.

## Verify and hand over

Import after adding scripts/assets when the project requires it. Run the
smallest behavioral checks, inspect real rendered output for visual changes,
and exercise movement/transitions for temporal changes. Expand only for an
affected dependency, a failure, or a project-required gate.

Report changed behavior, evidence with paths, and remaining limitations.
Separate source inspection, headless assertions, actual rendering and target
hardware measurements. Passing one category does not establish the others.
Keep evidence outside source assets and leave publishing to an authorized task.

Example request: “Use $godot-dev-director to add a streamed warehouse wing while
preserving saved door states and the current lighting.”
