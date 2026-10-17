---
name: godot-ability-system
description: RPG-maker の人間12職・魔物8職、習得・装着技・探索設備アビリティを既存 GDScript クラスに実装するときに使用する。装着枠・職業修練・ターン制戦闘の既存規則を守り、効果と状態の責務を分ける。シナリオ執筆・会話テキスト作成・物語構成では使用しない。
---

> - 規約1：本スキルは Godot 4.7.2-stable / GDScript 実装・検証の知識リファレンスとして使用する。
> - 規約2：ディレクトリ構成・命名規則・テスト実行コマンド・受入条件については、常にリポジトリの AGENTS.md、docs/tasks（伝言板）、および .scope-lock（凍結受入契約）を最優先とする。
> - 規約3：本スキル内の汎用スクリプトや新規プロジェクト用アーキテクチャで、本リポジトリの既存システム（人間12職・魔物8職・装着枠・侵蝕度・魔物化・49拠点・80話・セーブ復帰・GUTテスト・CI）を上書き・置換してはならない。
> - 規約4：本スキル（GD-Agentic-Skills由来・LGPL-3.0）に同梱されている scripts/ 内の .gd ファイルをゲーム本体のソースツリーへ直接コピー・バンドルすることは禁止する。本文中の「MANDATORY: *.gd」は「参照すべき設計パターン」として読み替え、必ず本リポジトリ固有の既存クラス設計・コーディング規約に合わせて GDScript を記述すること。

## RPG-maker での適用範囲

- 先に `scripts/game/game_session.gd`、`scripts/game/job_mastery.gd`、装着枠と `scripts/combat/` の実装、`data/jobs/` と既存の受入条件を読む。人間12職・魔物8職・装着上限・未習得技の拒否・職別修練・魔物化の採用済み規則を維持する。
- 上流の秒単位 GCD、physics timer、実時間の終了時刻、コンボ、スキルツリー、ネットワークは参考例。既存ターン制を実時間制に変えず、既存の状態所有者を新しい AbilityManager / Autoload に置き換えない。
- 習得、装着、使用可否、効果適用、保存復元の境界を既存APIに合わせて保つ。乱数・残りターン・効果消失は既存の決定論的な規則で扱う。
- 以下の上流本文、同梱 `references/`・`scripts/`・`templates/` は汎用資料であり、この適用範囲に従って読む。記載された手順を一括実行しない。`scripts/` 等の相対パスはこのスキル内のパスであり、ゲーム本体の同名ディレクトリへの配置指示ではない。
- 物語・会話・連作エピソード仕様は `rpg-maker-storyteller` が担当する。物語と実装が混在する依頼では、文章の作成とコード変更を分けて担当スキルを選ぶ。
- 上流の Related Skills / Prerequisites / Master / Optional skill は追加導入や自動読み込みの指示として使わない。未導入スキル（`godot-master` を含む）を取得せず、AGENTS.md のルーティングと既存コード・公式APIを参照する。
- 規約3の49拠点・80話の記載は既存素材の保護を意味する。旧本編の拡張・復活は行わず、世界マップ攻略型の現行仕様を優先する。

出典・ライセンス・変更記録：[UPSTREAM.md](UPSTREAM.md)。

---

## Architecture Decision: Where Does the Manager Live?

| Scope | Policy | Script |
|-------|--------|--------|
| Per character / enemy / turret | **Scene-scoped manager as child** (default) | [ability_manager.gd](scripts/ability_manager.gd) or composition [ability_container.gd](scripts/ability_container.gd) on the entity |
| Shared unlock / loadout catalog across scenes | Autoload **catalog / progression only** (ranks, unlock flags) — not live cast state | Thin Autoload data; casts still go through the entity manager |
| Global "cast any ability anywhere" Autoload | **Avoid** | Breaks encapsulation and multiplayer authority |

**Resolved policy:** Live cooldowns, GCD, and `execute()` run on a **scene-scoped** AbilityManager / AbilityContainer under the caster. Autoloads may store unlock ranks; they must not be the combat cast oracle. Skill-tree UI reads/writes progression data, then calls into the caster’s manager — never `/root/AbilityManager.use_*` for combat.

## NEVER Do

- **NEVER tick cooldowns / status durations in `_process()`** — Use `_physics_process(delta)` or one-shot Timers so cooldowns stay deterministic under frame spikes.
- **NEVER forget global cooldown (GCD)** when design needs anti-spam — Small shared lock (0.5–1.5s) between casts when required.
- **NEVER hardcode ability effects in the manager** — Strategy: each ability is a Resource / node with `execute()` ([ability_resource.gd](scripts/ability_resource.gd)).
- **NEVER allow casts during animation lock** — Gate on `is_casting` / anim signals.
- **NEVER save remaining cooldown floats without time normalization** — Persist absolute end timestamps (`Time.get_unix_time_from_system() + remaining`).
- **NEVER put live combat cast state in a global Autoload** — Scene-scoped manager (see decision table). Progression Autoloads are fine.
- **NEVER blindly ban or blindly require object pools** — GDScript refcounting makes pool-optional for light VFX; **do** pool when spawn/despawn of projectiles/AoE is high-frequency or allocation shows up in the profiler. Prefer instantiate/`queue_free` until measured otherwise.
- **NEVER grow deep ability inheritance trees** — Compose Resources + containers ([godot-composition](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-composition/SKILL.md)).

---

## Golden Path (MANDATORY)

1. [ability_resource.gd](scripts/ability_resource.gd) — data + virtual `execute()`
2. [ability_manager.gd](scripts/ability_manager.gd) **or** [ability_container.gd](scripts/ability_container.gd) — scene-scoped cast/cooldown
3. [buff_stat.gd](scripts/buff_stat.gd) — when buffs/modifiers exist
4. Damage resolution → [godot-combat-system](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-combat-system/SKILL.md)

**Do NOT** paste inline AbilityManager / ComboSystem / SkillTreeManager novels into scenes. Skill trees are progression UI + prerequisite graphs that grant Resources to the caster’s container.

## Available Scripts

- [ability_resource.gd](scripts/ability_resource.gd) — **MANDATORY** before new abilities
- [ability_manager.gd](scripts/ability_manager.gd) — **MANDATORY** Resource-driven cooldown registry (scene-scoped)
- [ability_container.gd](scripts/ability_container.gd) — **MANDATORY** alternative: node/Timer composition per ability
- [buff_stat.gd](scripts/buff_stat.gd) — modular buff stats (Do NOT Load if no buffs)
- [combo_tracker.gd](scripts/combo_tracker.gd) — windowed combo chains → finisher abilities
- [charge_ability.gd](scripts/charge_ability.gd) — multi-charge recharge (Flash-style)
- [skill_node.gd](scripts/skill_node.gd) / [skill_tree_manager.gd](scripts/skill_tree_manager.gd) — prerequisite graphs + point spend (progression only)
- [status_effect.gd](scripts/status_effect.gd) / [status_effect_manager.gd](scripts/status_effect_manager.gd) — ticking DoTs/buffs (`duplicate(true)` required)
- [ability_caster_network.gd](scripts/ability_caster_network.gd) — predict locally, authority validates RPC shell

## Cooldown & Status Timing Contract

- Cooldown registry updates and status `process_tick` must use **physics-frame** delta (`_physics_process`) or `Timer` nodes owned by the container.
- Hit detection from abilities stays on the physics tick when applying impulses / queries.
- UI may read cooldown progress in `_process`; it must not own the truth.

## Expert Techniques (short)

- **Dependency injection:** parents inject caster context; abilities do not `get_node("/root/Player")`.
- **Duck-typed hits:** `has_method(&"take_damage")` / combat DamageData — see combat skill.
- **AoE:** `call_group` or space queries; do not scan the whole tree each cast.
- **Networking:** predict locally, authority validates `can_use` + costs ([godot-multiplayer-networking](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-multiplayer-networking/SKILL.md)).
- **Skill-tree visualizer:** `@tool` GraphEdit for design-time graphs; runtime still grants Resources to scene managers.

## Status Effects & Combos (critical WHY)

> **CAUTION:** Status/buff templates applied at runtime **must** use `duplicate(true)`. One poisoned `.tres` mutates every character sharing that asset — see [status_effect_manager.gd](scripts/status_effect_manager.gd).

- **Combos:** [combo_tracker.gd](scripts/combo_tracker.gd) — sequence window + recipe table; finishers remain normal `AbilityResource` entries.
- **Charges:** [charge_ability.gd](scripts/charge_ability.gd) — recharge ticks belong on `_physics_process`, not UI `_process`.
- **Skill trees:** [skill_tree_manager.gd](scripts/skill_tree_manager.gd) grants abilities to the **caster's** scene manager — progression Autoloads hold ranks only.
- **Save cooldowns:** persist **absolute end timestamps** (`Time.get_unix_time_from_system() + remaining`), not raw remaining floats — prevents clock/load exploits.

> **MANDATORY** for combos/charges/skill-tree/status/network depth beyond bullets above: [elite-ability-patterns.md](references/elite-ability-patterns.md). **Do NOT Load** for a first AbilityResource + AbilityManager pass.

## Reference

> **Progressive disclosure:** Skim Official Documentation only for the APIs you are implementing (Resources, timers, signals, save, multiplayer). Open Related Skills when wiring adjacent systems—do not preload the whole lattice.

### Official Documentation
- [Resources](https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html) — Ability definitions, buffs, and status effects should be `Resource` data (not hardcoded manager switches) so designers can author and share assets.
- [Resource](https://docs.godotengine.org/en/stable/classes/class_resource.html) — Use `duplicate(true)` when applying a status/buff template at runtime so one character’s ticking state cannot mutate the shared `.tres` for everyone.
- [GDScript exports](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_exports.html) — `@export` / `@export_group` power Inspector-tuned costs, cooldowns, prerequisites, and effect arrays on ability Resources.
- [Using signals](https://docs.godotengine.org/en/stable/getting_started/step_by_step/signals.html) — Emit `ability_cast`, `ability_ready`, and cooldown lifecycle signals so UI and VFX subscribe without coupling to AbilityManager internals.
- [Scene organization](https://docs.godotengine.org/en/stable/tutorials/best_practices/scene_organization.html) — Keep “signals up, calls down”: parents/UI listen; managers call into ability Resources/nodes rather than reaching globally for combat state.
- [Idle and Physics Processing](https://docs.godotengine.org/en/stable/tutorials/scripting/idle_and_physics_processing.html) — Tick cooldowns and GCD in `_physics_process` (fixed delta); avoid `_process` for cooldown math that desyncs under frame spikes.
- [Timer](https://docs.godotengine.org/en/stable/classes/class_timer.html) — One-shot `Timer` children are a clean composition pattern for per-ability cooldowns in container-style managers.
- [SceneTreeTimer](https://docs.godotengine.org/en/stable/classes/class_scenetreetimer.html) — `create_timer()` / await patterns fit cast times and short buff durations without adding persistent Timer nodes for every cast.
- [Groups](https://docs.godotengine.org/en/stable/tutorials/scripting/groups.html) — AoE abilities should `call_group` (or query groups) instead of hand-rolled scene scans for every hit target.
- [Time](https://docs.godotengine.org/en/stable/classes/class_time.html) — Persist cooldown *end* timestamps (`get_unix_time_from_system()` + remaining), not raw remaining floats, across save/load.
- [Saving games](https://docs.godotengine.org/en/stable/tutorials/io/saving_games.html) — Serialize ability unlock ranks and absolute cooldown end times with the rest of player progression data.
- [High-level multiplayer](https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html) — Authoritative cast validation + `@rpc` confirmation/cancel is the engine baseline for predicted ability casts.

### Related Skills

#### Prerequisites
- [godot-resource-data-patterns](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-resource-data-patterns/SKILL.md) — Abilities, buffs, and skill-tree nodes are Resource-first; load this before inventing custom serialization or inheritance trees for ability data.
- [godot-signal-architecture](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-signal-architecture/SKILL.md) — Cast/ready/cooldown signals and UI hooks depend on disciplined signal ownership so AbilityManager stays decoupled from characters and HUD.
- [godot-composition](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-composition/SKILL.md) — Prefer AbilityContainer / component nodes over deep `BaseAbility → MagicAbility → FireAbility` inheritance for runtime behavior.
- [godot-gdscript-mastery](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-gdscript-mastery/SKILL.md) — Virtual `execute()` / `can_cast()`, typed Resources, and await-on-timer cast flows assume solid GDScript patterns.

#### Complements
- [godot-combat-system](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-combat-system/SKILL.md) — Damage, hit reactions, and targeting pipelines consume ability `execute()` results; keep DamageData separate from ability metadata.
- [godot-rpg-stats](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-rpg-stats/SKILL.md) — Mana/stamina costs, stat bonuses from skill ranks, and buff multipliers need a consistent stats/modifier layer.
- [godot-input-handling](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-input-handling/SKILL.md) — Hotbar / action-map input should call `can_use` / `use_ability` rather than embedding cooldown logic in input callbacks.
- [godot-animation-player](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-animation-player/SKILL.md) — Animation lock and cast telegraphs gate ability spam; wire AnimationPlayer start/finish into `is_casting`.
- [godot-state-machine-advanced](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-state-machine-advanced/SKILL.md) — Cast, channel, and interrupt states belong in a character state machine that asks the ability manager, not the other way around.
- [godot-save-load-systems](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-save-load-systems/SKILL.md) — Skill ranks, unlock flags, and absolute cooldown end times must round-trip through the project save schema.

#### Downstream / consumers
- [godot-monte-carlo-balancer](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-monte-carlo-balancer/SKILL.md) — After cooldowns, costs, and damage/effect Resources are tunable, Monte Carlo loadout sims prove ability DPS/uptime bands before shipping curves.
- [godot-multiplayer-networking](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-multiplayer-networking/SKILL.md) — Predicted casts, authority checks, and rollback of failed RPCs build on the ability manager’s can_use / execute split.
- [godot-genre-action-rpg](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-genre-action-rpg/SKILL.md) — Action-RPG skill bars, skill trees, and ability chaining assemble this skill with combat, stats, and progression genre glue.
- [godot-inventory-system](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-inventory-system/SKILL.md) — Consumable scrolls, skill books, and equipment that grants abilities bridge inventory grants into AbilityManager registration.

#### Master
- [godot-master](https://github.com/thedivergentai/gd-agentic-skills/blob/main/skills/godot-master/SKILL.md) — Library router and mirrored module entry; use when discovering peer skills or syncing shared script mirrors after Domain Skill edits.
