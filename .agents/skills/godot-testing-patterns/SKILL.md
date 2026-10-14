---
name: godot-testing-patterns
description: RPG-maker の既存 GUT による GDScript 単体テスト・結合テスト・シグナルテスト、モック・スタブ、テスト間の状態分離を実装するときに使用する。上流の GdUnit4 例は設計参考のみとし、テスト基盤を追加・置換しない。シナリオ執筆・会話テキスト作成・物語構成では使用しない。
---

> - 規約1：本スキルは Godot 4.7.2-stable / GDScript 実装・検証の知識リファレンスとして使用する。
> - 規約2：ディレクトリ構成・命名規則・テスト実行コマンド・受入条件については、常にリポジトリの AGENTS.md、docs/tasks（伝言板）、および .scope-lock（凍結受入契約）を最優先とする。
> - 規約3：本スキル内の汎用スクリプトや新規プロジェクト用アーキテクチャで、本リポジトリの既存システム（人間12職・魔物8職・装着枠・侵蝕度・魔物化・49拠点・80話・セーブ復帰・GUTテスト・CI）を上書き・置換してはならない。
> - 規約4：本スキル（GD-Agentic-Skills由来・LGPL-3.0）に同梱されている scripts/ 内の .gd ファイルをゲーム本体のソースツリーへ直接コピー・バンドルすることは禁止する。本文中の「MANDATORY: *.gd」は「参照すべき設計パターン」として読み替え、必ず本リポジトリ固有の既存クラス設計・コーディング規約に合わせて GDScript を記述すること。

## RPG-maker での適用範囲

- 上流の本文・同梱例は GdUnit4 用であり、そのまま動く GUT 例ではない。GdUnit4 を導入せず、既存の `addons/gut/` と `test/support/game_test.gd` の設計を優先する。
- `GdUnitTestSuite` / `before_test` / GdUnit の assertion はそのまま使わない。既存 GUT の `GutTest`、`before_each` / `after_each`、`double` / `stub`、`watch_signals` / `assert_signal_emitted`、`add_child_autofree` / `add_child_autoqfree` の現物APIに合わせる。
- 同梱の headless runner、スナップショット初回自動生成、期待画像の削除・上書きを受入手順へ導入しない。凍結 verify と CI の既存コマンドを維持する。`test/**` は保護対象であり、このスキルは書き込み許可を与えない。
- 以下の上流本文、同梱 `references/`・`scripts/`・`templates/` は汎用資料であり、この適用範囲に従って読む。記載された手順を一括実行しない。`scripts/` 等の相対パスはこのスキル内のパスであり、ゲーム本体の同名ディレクトリへの配置指示ではない。
- 物語・会話・連作エピソード仕様は `rpg-maker-storyteller` が担当する。物語と実装が混在する依頼では、文章の作成とコード変更を分けて担当スキルを選ぶ。
- 上流の Related Skills / Prerequisites / Master / Optional skill は追加導入や自動読み込みの指示として使わない。未導入スキル（`godot-master` を含む）を取得せず、AGENTS.md のルーティングと既存コード・公式APIを参照する。
- 規約3の49拠点・80話の記載は既存素材の保護を意味する。旧本編の拡張・復活は行わず、世界マップ攻略型の現行仕様を優先する。

出典・ライセンス・変更記録：[UPSTREAM.md](UPSTREAM.md)。

---

## Decision Tree → Scripts

| Need | Choice | Script (MANDATORY when chosen) |
| :--- | :--- | :--- |
| Pure logic / no tree | Unit | [basic_unit_test.gd](scripts/basic_unit_test.gd), [mock_dependency_test.gd](scripts/mock_dependency_test.gd), [test_data_factory.gd](scripts/test_data_factory.gd) |
| Node interaction after instantiate | Scene integration | [scene_integration_test.gd](scripts/scene_integration_test.gd), [integration_test_base.gd](scripts/integration_test_base.gd) |
| Signal contracts | Unit or scene | [signal_emission_test.gd](scripts/signal_emission_test.gd) |
| Multi-frame / physics step | Async scene | [wait_for_frame_test.gd](scripts/wait_for_frame_test.gd), [physics_collision_test.gd](scripts/physics_collision_test.gd) |
| Flaky physics / timing races | Frame step gate | **MANDATORY** [wait_for_frame_test.gd](scripts/wait_for_frame_test.gd) — never wall-clock sleep |
| CI / no display | Headless gate | **MANDATORY** [headless_test_runner.gd](scripts/headless_test_runner.gd) |
| Save/UI regression | Snapshot | **MANDATORY** [snapshot_tester.gd](scripts/snapshot_tester.gd) |
| RPC without live peers | Mock network | **MANDATORY** [mock_network_provider.gd](scripts/mock_network_provider.gd) |
| Perf budget in CI | Benchmark gate | [performance_benchmark_runner.gd](scripts/performance_benchmark_runner.gd) |
| Orphans after suite | Leak detect | [memory_leak_detector.gd](scripts/memory_leak_detector.gd) |
| Edge input space | Fuzz | [parameter_fuzz_tester.gd](scripts/parameter_fuzz_tester.gd) |

**Do NOT Load** assert-catalog tutorials or manual gameplay checklists into context — pick a row, read the script, implement.

## MANDATORY Triggers

- **CI / `--headless`**: always read [headless_test_runner.gd](scripts/headless_test_runner.gd) first (`OS.exit_code`, GdUnit4 CLI: `godot --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://test`).
- **State or visual golden files**: read [snapshot_tester.gd](scripts/snapshot_tester.gd) before writing JSON/image goldens. **Approve workflow:** first run saves reference; intentional UI change → delete or overwrite `res://tests/snapshots/<name>.png`, re-run to regenerate, commit new golden; never hand-edit PNG bytes.
- **Any RPC / MultiplayerSynchronizer test**: read [mock_network_provider.gd](scripts/mock_network_provider.gd) before standing up real peers.

## Available Scripts

### [basic_unit_test.gd](scripts/basic_unit_test.gd)
Minimal GdUnit4 (`GdUnitTestSuite`) structure for pure logic.

### [signal_emission_test.gd](scripts/signal_emission_test.gd)
Signal emission monitoring for decoupled architectures.

### [mock_dependency_test.gd](scripts/mock_dependency_test.gd)
Mocks/doubles to isolate external services.

### [scene_integration_test.gd](scripts/scene_integration_test.gd) / [integration_test_base.gd](scripts/integration_test_base.gd)
Scene lifecycle + node interaction fixtures.

### [headless_test_runner.gd](scripts/headless_test_runner.gd)
CI headless orchestration and exit codes.

### [snapshot_tester.gd](scripts/snapshot_tester.gd)
Dictionary/UI golden snapshot comparison.

### [mock_network_provider.gd](scripts/mock_network_provider.gd)
Loopback / offline multiplayer peer for RPC tests.

### [performance_benchmark_runner.gd](scripts/performance_benchmark_runner.gd)
Microsecond timers + Performance monitor gates.

### [memory_leak_detector.gd](scripts/memory_leak_detector.gd)
Orphan node detection across long suites.

### [parameter_fuzz_tester.gd](scripts/parameter_fuzz_tester.gd)
Randomized ranges for edge crashes.

### [wait_for_frame_test.gd](scripts/wait_for_frame_test.gd) / [physics_collision_test.gd](scripts/physics_collision_test.gd)
Frame/physics-step async verification.

### [test_data_factory.gd](scripts/test_data_factory.gd)
Schema-compliant fixture builders.

## NEVER Do in Testing (GdUnit4)

- **NEVER test private implementation details** — Assert public behavior only.
- **NEVER share mutable state between tests** — Fresh setup per test (`before_test` / equivalent).
- **NEVER use wall-clock `sleep` / blind timers** — Prefer frame steppers from wait_for_frame patterns.
- **NEVER skip cleanup** — Free instantiated nodes after each test.
- **NEVER test randomness without seeding**.
- **NEVER assert signals without the GdUnit signal assert/monitor helpers** from [signal_emission_test.gd](scripts/signal_emission_test.gd).
- **NEVER mix GUT and GdUnit4 APIs** in one suite.
- **NEVER rely on editor-only features for CI** — Headless-compatible tests only.
- **NEVER default to full-level integration tests** — Prefer unit + small scene tests; escalate only when the decision tree says so.
- **NEVER hardcode brittle absolute file paths** in fixtures.
- **NEVER test third-party plugin internals** — Test your integration only.

## Expert Gates (short)

- **Snapshot**: serialize → compare golden ([snapshot_tester.gd](scripts/snapshot_tester.gd)); regenerate reference PNG on approved visual changes.
- **CI**: `--headless` + `OS.exit_code` non-zero on failure ([headless_test_runner.gd](scripts/headless_test_runner.gd)).
- **Network**: mock peer before real ENet (`mock_network_provider.gd`).
- **Perf**: `Performance` monitors / draw-call caps in benchmark runner.

## Deep recipes (on demand)

> LLM-ignorance rule: if a general agent would not know it before reading, it lives here or in `scripts/` — never delete, only move.

| Topic | Reference |
|-------|-----------|
| Snapshot / CI / fuzz / perf | [expert-testing-patterns.md](references/expert-testing-patterns.md) |
| Release smoke checklist | [manual-testing-checklist.md](references/manual-testing-checklist.md) |

## Reference

> Progressive disclosure: open Official Documentation links only when researching a specific API; load Related Skills when routing to a peer domain — do not preload the whole lattice.

### Official Documentation
- [Command line tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html) — `--headless`, `-s`, and exit-code patterns for CI test runners.
- [Overview of debugging tools](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/overview_of_debugging_tools.html) — debugger, profiler, and remote inspect when a failing test needs engine-side diagnosis.
- [Custom performance monitors](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/custom_performance_monitors.html) — `Performance` monitors and custom metrics for benchmark gates and orphan detection.
- [Idle and physics processing](https://docs.godotengine.org/en/stable/tutorials/scripting/idle_and_physics_processing.html) — frame/`_physics_process` timing that `wait_frames` / yield helpers must respect.
- [Using SceneTree](https://docs.godotengine.org/en/stable/tutorials/scripting/scene_tree.html) — tree lifecycle, `quit()`, and process modes used by headless orchestrators.
- [Nodes and scene instances](https://docs.godotengine.org/en/stable/tutorials/scripting/nodes_and_scene_instances.html) — instantiate/add_child/free hygiene for scene integration tests.
- [Instancing with signals](https://docs.godotengine.org/en/stable/tutorials/scripting/instancing_with_signals.html) — signal wiring patterns that signal-emission tests verify.
- [High-level multiplayer](https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html) — RPC/peer APIs mocked via OfflineMultiplayerPeer or latency simulators.
- [Using InputEvent](https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html) — synthetic `InputEvent*` injection for fuzz and UI interaction tests.
- [Random number generation](https://docs.godotengine.org/en/stable/tutorials/math/random_number_generation.html) — seeding for deterministic fuzz and Monte Carlo harnesses.
- [Saving games](https://docs.godotengine.org/en/stable/tutorials/io/saving_games.html) — serialize/deserialize patterns behind golden JSON and save/load integration tests.
- [Physics introduction](https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html) — layers/masks and step timing for collision integration tests.

### Related Skills

#### Prerequisites
- [godot-project-foundations](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-project-foundations/SKILL.md) — project layout, scenes, and resources before standing up a `res://test/` suite.
- [godot-gdscript-mastery](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-gdscript-mastery/SKILL.md) — typed GDScript, `await`, and assert idioms used in every unit/integration test.
- [godot-signal-architecture](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-signal-architecture/SKILL.md) — emit/connect contracts that `watch_signals` / signal monitors assert against.

#### Complements
- [godot-debugging-profiling](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-debugging-profiling/SKILL.md) — profiler and ObjectDB tools when a red test needs runtime evidence, not another assert.
- [godot-scene-management](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-scene-management/SKILL.md) — scene packing/load patterns mirrored in scene integration fixtures.
- [godot-input-handling](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-input-handling/SKILL.md) — action maps and event parsing exercised by fuzz and UI press tests.
- [godot-2d-physics](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-2d-physics/SKILL.md) — layer matrices and body APIs that physics collision tests must keep green.
- [godot-resource-data-patterns](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-resource-data-patterns/SKILL.md) — Resource schemas that test data factories and snapshot dictionaries serialize.
- [godot-save-load-systems](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-save-load-systems/SKILL.md) — persistence pipelines covered by save/load integration and golden-state tests.

#### Downstream / consumers
- [godot-monte-carlo-balancer](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-monte-carlo-balancer/SKILL.md) — seeded headless gameplay sims that reuse these harnesses for Phase 7 golden cells.
- [godot-performance-optimization](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-performance-optimization/SKILL.md) — budgets that CI performance gates (`Performance` monitors, draw-call caps) enforce.
- [godot-multiplayer-networking](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-multiplayer-networking/SKILL.md) — RPC/replication logic validated through mock peers and lag injection.
- [godot-export-builds](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-export-builds/SKILL.md) — headless export/CI pipelines that invoke the same `--headless` test entrypoints.

#### Master
- [godot-master](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-master/SKILL.md) — library router and mirrored module entry for cross-skill discovery.
