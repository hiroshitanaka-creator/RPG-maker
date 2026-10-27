# 実行記録（UTC）

全検査は固定Godot 4.7.2とクラウド内の隔離コピーを使用。各行に対応するJSONにはcwd・環境変数・開始終了時刻・所要秒・exitを、同名stdout/stderr.logには原出力を保持。R-01〜R-08の内部出力は既存run_locked_checks.pyの仕様どおりstdout/stderr結合原ログをresults/project/tool-output/verification/に保持。verify各300秒、import各600秒、境界検査前後各180秒。

| 記録名 | コマンド | 開始UTC | 終了UTC | 秒 | exit |
|---|---|---|---|---:|---:|
| before-engine-version | `godot --version` | 2026-10-22T09:14:15.640761+00:00 | 2026-10-22T09:14:15.687714+00:00 | 0.047 | 0 |
| before-frozen | `python tools/check_frozen_files.py` | 2026-10-22T09:14:15.688628+00:00 | 2026-10-22T09:14:15.738417+00:00 | 0.050 | 0 |
| before-editor-import | `timeout 600 godot --headless --editor --import --quit` | 2026-10-22T09:14:15.738708+00:00 | 2026-10-22T09:15:45.034368+00:00 | 89.296 | 0 |
| before-coastal-boundary | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 2026-10-22T09:15:45.036851+00:00 | 2026-10-22T09:18:45.047362+00:00 | 180.011 | 124 |
| after-engine-version | `godot --version` | 2026-10-22T09:19:11.542840+00:00 | 2026-10-22T09:19:11.579600+00:00 | 0.037 | 0 |
| after-editor-import | `timeout 600 godot --headless --editor --import --quit` | 2026-10-22T09:19:11.579958+00:00 | 2026-10-22T09:19:17.578363+00:00 | 5.998 | 0 |
| after-coastal-boundary | `timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd` | 2026-10-22T09:19:17.578903+00:00 | 2026-10-22T09:19:24.894432+00:00 | 7.316 | 0 |
| after-prescribed-import | `timeout 600 godot --headless --import` | 2026-10-22T09:19:24.894947+00:00 | 2026-10-22T09:19:31.394999+00:00 | 6.500 | 0 |
| after-assets-strict | `python tools/validate_assets.py --strict` | 2026-10-22T09:19:31.395404+00:00 | 2026-10-22T09:19:41.529715+00:00 | 10.134 | 0 |
| after-port-layout | `python tools/check_port_town.py` | 2026-10-22T09:19:41.530570+00:00 | 2026-10-22T09:19:41.853749+00:00 | 0.323 | 0 |
| after-coastal-assets | `python tools/check_coastal_assets.py` | 2026-10-22T09:19:41.854040+00:00 | 2026-10-22T09:19:42.160296+00:00 | 0.306 | 0 |
| after-second-coast | `timeout 180 godot --headless --path . --script res://tools/check_second_region_coast.gd` | 2026-10-22T09:19:42.160895+00:00 | 2026-10-22T09:19:44.687602+00:00 | 2.527 | 0 |
| after-region-ui | `timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd` | 2026-10-22T09:19:44.688465+00:00 | 2026-10-22T09:19:49.221759+00:00 | 4.533 | 0 |
| after-region2-port | `timeout 180 godot --headless --path . --script res://tools/check_region2_port.gd` | 2026-10-22T09:19:49.222095+00:00 | 2026-10-22T09:19:53.444221+00:00 | 4.222 | 0 |
| after-village-regression | `timeout 180 godot --headless --path . --script res://tools/check_region2_village_regression.gd` | 2026-10-22T09:19:53.445262+00:00 | 2026-10-22T09:20:30.427923+00:00 | 36.983 | 0 |
| after-saved-position | `timeout 120 godot --headless --path . --script res://tools/check_saved_position_relocation.gd` | 2026-10-22T09:20:30.428299+00:00 | 2026-10-22T09:20:34.092870+00:00 | 3.665 | 0 |
| after-locked-checks | `python tools/run_locked_checks.py` | 2026-10-22T09:20:34.093343+00:00 | 2026-10-22T09:22:55.595819+00:00 | 141.503 | 0 |
| after-frozen | `python tools/check_frozen_files.py` | 2026-10-22T09:22:55.597018+00:00 | 2026-10-22T09:22:55.665207+00:00 | 0.068 | 0 |
| source-after-frozen | `python tools/check_frozen_files.py` | 2026-10-22T09:22:55.665485+00:00 | 2026-10-22T09:22:55.708065+00:00 | 0.043 | 0 |
