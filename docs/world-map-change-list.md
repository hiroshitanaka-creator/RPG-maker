# ワールドマップの変更ファイル一覧

> 履歴資料: 以下の進捗・未達・暫定値は記録時点の状態です。現在の実装・受入・残作業は [現在地](current-status.md) を参照してください。

Phase 3・4と、新規拠点の内部・ゲーム接続に含めたファイル。実装と検証範囲は [接続記録](world-map-playable.md) を参照。

| パス | 役割 |
|---|---|
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | CI検査の登録 |
| [PLAYTEST_QUEUE.md](../PLAYTEST_QUEUE.md) | 説明・作業記録 |
| [README.md](../README.md) | 説明・作業記録 |
| [docs/verification/screens/world_after_battle.png](../docs/verification/screens/world_after_battle.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_after_retry.png](../docs/verification/screens/world_after_retry.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_atlas.png](../docs/verification/screens/world_atlas.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_battle.png](../docs/verification/screens/world_battle.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_field.png](../docs/verification/screens/world_field.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_flight_pc_01.png](../docs/verification/screens/world_flight_pc_01.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_flight_pc_02.png](../docs/verification/screens/world_flight_pc_02.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_flight_pc_03.png](../docs/verification/screens/world_flight_pc_03.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_flight_pc_04.png](../docs/verification/screens/world_flight_pc_04.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_interior.png](../docs/verification/screens/world_interior.png) | Godotによる実描画の証拠 |
| [docs/verification/screens/world_ship.png](../docs/verification/screens/world_ship.png) | Godotによる実描画の証拠 |
| [docs/verification/world-integration-3.json](../docs/verification/world-integration-3.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-integration.json](../docs/verification/world-integration.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-map-phase2.json](../docs/verification/world-map-phase2.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-state-boundaries.json](../docs/verification/world-state-boundaries.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-terrain-boundaries.json](../docs/verification/world-terrain-boundaries.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-terrain-realtime-phase3.json](../docs/verification/world-terrain-realtime-phase3.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-terrain-realtime.json](../docs/verification/world-terrain-realtime.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-terrain.json](../docs/verification/world-terrain.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-ui-headless.json](../docs/verification/world-ui-headless.json) | 機械検証結果・実時間測定 |
| [docs/verification/world-ui-native.json](../docs/verification/world-ui-native.json) | 機械検証結果・実時間測定 |
| [docs/world-map-change-list.md](../docs/world-map-change-list.md) | 説明・作業記録 |
| [docs/world-map-phase1.md](../docs/world-map-phase1.md) | 説明・作業記録 |
| [docs/world-map-phase2.md](../docs/world-map-phase2.md) | 説明・作業記録 |
| [docs/world-map-playable.md](../docs/world-map-playable.md) | 説明・作業記録 |
| [scripts/game/game_session.gd](../scripts/game/game_session.gd) | 本番実装・スクリプト識別子 |
| [scripts/ui/game_root.gd](../scripts/ui/game_root.gd) | 本番実装・スクリプト識別子 |
| [scripts/world/expedition_view.gd](../scripts/world/expedition_view.gd) | 本番実装・スクリプト識別子 |
| [scripts/world/expedition_view.gd.uid](../scripts/world/expedition_view.gd.uid) | 本番実装・スクリプト識別子 |
| [scripts/world/world_expedition.gd](../scripts/world/world_expedition.gd) | 本番実装・スクリプト識別子 |
| [scripts/world/world_expedition.gd.uid](../scripts/world/world_expedition.gd.uid) | 本番実装・スクリプト識別子 |
| [scripts/world/world_movement.gd](../scripts/world/world_movement.gd) | 本番実装・スクリプト識別子 |
| [scripts/world/world_movement.gd.uid](../scripts/world/world_movement.gd.uid) | 本番実装・スクリプト識別子 |
| [scripts/world/world_terrain.gd](../scripts/world/world_terrain.gd) | 本番実装・スクリプト識別子 |
| [scripts/world/world_terrain.gd.uid](../scripts/world/world_terrain.gd.uid) | 本番実装・スクリプト識別子 |
| [tools/build_world_interiors.py](../tools/build_world_interiors.py) | 生成・検証・スクリプト識別子 |
| [tools/build_world_terrain.py](../tools/build_world_terrain.py) | 生成・検証・スクリプト識別子 |
| [tools/check_map_graph_definition.gd](../tools/check_map_graph_definition.gd) | 生成・検証・スクリプト識別子 |
| [tools/check_world_integration.gd](../tools/check_world_integration.gd) | 生成・検証・スクリプト識別子 |
| [tools/check_world_integration.gd.uid](../tools/check_world_integration.gd.uid) | 生成・検証・スクリプト識別子 |
| [tools/check_world_realtime_record.py](../tools/check_world_realtime_record.py) | 生成・検証・スクリプト識別子 |
| [tools/check_world_state_boundaries.gd](../tools/check_world_state_boundaries.gd) | 生成・検証・スクリプト識別子 |
| [tools/check_world_state_boundaries.gd.uid](../tools/check_world_state_boundaries.gd.uid) | 生成・検証・スクリプト識別子 |
| [tools/check_world_terrain.gd](../tools/check_world_terrain.gd) | 生成・検証・スクリプト識別子 |
| [tools/check_world_terrain.gd.uid](../tools/check_world_terrain.gd.uid) | 生成・検証・スクリプト識別子 |
| [tools/check_world_terrain_boundaries.gd](../tools/check_world_terrain_boundaries.gd) | 生成・検証・スクリプト識別子 |
| [tools/check_world_terrain_boundaries.gd.uid](../tools/check_world_terrain_boundaries.gd.uid) | 生成・検証・スクリプト識別子 |
| [tools/check_world_terrain_realtime.gd](../tools/check_world_terrain_realtime.gd) | 生成・検証・スクリプト識別子 |
| [tools/check_world_terrain_realtime.gd.uid](../tools/check_world_terrain_realtime.gd.uid) | 生成・検証・スクリプト識別子 |
| [tools/check_world_ui.gd](../tools/check_world_ui.gd) | 生成・検証・スクリプト識別子 |
| [tools/check_world_ui.gd.uid](../tools/check_world_ui.gd.uid) | 生成・検証・スクリプト識別子 |
| [world/interiors.json](../world/interiors.json) | 構造・地形・拠点内部のデータ |
| [world/map_graph.json](../world/map_graph.json) | 構造・地形・拠点内部のデータ |
| [world/terrain.json](../world/terrain.json) | 構造・地形・拠点内部のデータ |
