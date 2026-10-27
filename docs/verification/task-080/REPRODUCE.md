# 080の再現

1. 基点 `e677896d3e61b8fe8136ef60c5c76f41ad76701d` を含むrepoでZIPの `changes.patch` を確認し、親の正式保存対象checkoutに適用する。PR49をmergeしない。payloadは差分全ファイルの原bytes。
2. CI固定Godot 4.7.2-stableをPATHへ置く。ZIP SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`。基点を取り込んだ後は最初に次を実行する。

```bash
godot --headless --editor --import --quit
```

3. 利用者保存と分離した空のXDG領域で、通常描画の開発用直接起動。

```bash
export XDG_DATA_HOME=/tmp/task080-qa/data
export XDG_CONFIG_HOME=/tmp/task080-qa/config
export XDG_CACHE_HOME=/tmp/task080-qa/cache
export RPG_QA_SAVE_PREFIX=task080
godot --path . tools/adopted_room_foundation.tscn -- --room=inn
```

1〜5は宿/道具/武器/祠/防具の順。矢印・WASDで歩き、入口最下段を踏んで退出、上へ歩いて再入室。Escで終了。通常タイトルから入る接続はない。

4. 構造・固定目視probe・負例、および通常入力と描画。

```bash
export ADOPTED_ROOM_OUTPUT=/tmp/task080-qa/evidence
python3 tools/check_adopted_room_foundation.py --output "$ADOPTED_ROOM_OUTPUT"
for ADOPTED_ROOM_INDEX in 0 1 2 3 4; do
  export ADOPTED_ROOM_INDEX
  timeout 180 godot --display-driver x11 --audio-driver Dummy --path . --script res://tools/check_adopted_room_foundation.gd
done
```

X11が必要。今回の同環境では `/usr/bin/Xorg :80 -config /etc/X11/xorg.conf -noreset -nolisten tcp -logfile /workspace/task080/evidence/xorg.log` を使い `DISPLAY=:80` とした。headlessでも移動検査は可能だがPNG/画素比較は行われないため、描画検証の代わりにはしない。上のforは個別exitと最終JSONをそれぞれ確認する。

5. 既存検査。変更されていないR-01〜R-08のverifyコマンドは `.scope-lock/spec.lock.json` にある。各300秒以内で実行し、既存run_locked_checks.pyのjudge_outputを使う外部実行器を証拠のreproduction/locked.py.txtへ収録。元のtools/run_locked_checks.pyも実行可能だが、docs/verification/scope-lock-current.jsonへ記録を生成するのでQAコピーで使う。出力先だけを分ける際も合否判定・時間上限・検査条件は変えない。

```bash
python3 tools/check_frozen_files.py
python3 tools/validate_assets.py --strict
timeout 60 godot --headless --path . --script res://tools/check_saved_value_types.gd
timeout 120 godot --headless --path . --script res://tools/check_saved_position_relocation.gd
timeout 180 godot --headless --path . --script res://tools/check_second_region_coast.gd
timeout 180 godot --headless --path . --script res://tools/check_region2_port.gd
timeout 180 godot --headless --path . --script res://tools/check_first_region_screen.gd
timeout 180 godot --headless --path . --script res://tools/check_battle_recovery.gd
timeout 180 godot --headless --path . --script res://tools/check_coastal_travel.gd
```

素材strictは候補で5件のowner原画パス拒否、旧coastalは基点/候補でDictionary参照エラーとexit124が今回の実測。成功を期待するコマンドとして隠さない。旧coastal検査は基点の隔離コピーでもimportを先行して同じ180秒で実行する。

6. 通常起動口の負例：

```bash
godot --headless --path . tools/adopted_room_foundation.tscn -- --room=harbor_office
```

期待exit2、unknown room通知。未知室へ進まない。

証拠の*.execution.jsonは当時の絶対cwd・コマンド・上限・実exit・時間、各検査JSONは入力と判定を含む。reproduction/の外部実行器は当時の `/workspace/RPG-maker` と `/workspace/task080` を使うため、別環境では作業/出力先だけを対応するパスへ変更する。Godot条件・制限・期待値は維持する。初回失敗・初回描画はfirst-pass/、家具の足元順同値を解消する前の宿描画はbefore-depth-alignment/に分離。

reproduction/build_definition.py.txt は最初の手配置を作った原記録であり、最終world/adopted_room_foundation.jsonを再生成するためのものではない。最終の祠北側床・家具足元の調整はpayloadのJSONを正とする。
