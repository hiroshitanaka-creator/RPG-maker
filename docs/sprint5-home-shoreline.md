# スプリント5：カイナの家と世界全体の水際

2026年9月28日の依頼者指示による区切り。先に城下町と城の左右の壁を低い石垣へ直し、画像を報告した後、家と水際へ進んだ。

## 今回の決定事項

- 仮称はエルヴァ城下町・エルヴァ城。正式名称は物語の細部が決まった後に見直す。
- 防具屋は今回は建物・店員・会話まで。購入と装備の仕組みは最初の地方を作り終えるまでに決める。
- メニュー画面の見た目の統一を計画へ記録。転職の灰色の選択欄は今回変更しない。

## カイナの家

部屋の16×9セル、開始位置(4,4)、出口(8,8)は維持した。左に寝床、右に食卓と収納、上側に炉をまとめ、中央から出口へ通り抜けられる配置にした。窓・漆喰・木の梁・継ぎ目をずらした板床・敷物を使う。

村の目標画像の木材と色を参考に、組み込みimagegenで新しい家具と表面の原画2枚を作成。元の画像は `assets/_incoming/home-2026-09-28/`、指示全文とハッシュは `assets/source_records/home-generation.json`。既存画像を上書きせず、家専用の素材8点として自然色パレット64色以内・二値透過・32pxの倍数へ変換した。処理と配置は `tools/build_cozy_home.py`、変換記録は `assets/source_records/home-conversion.json`。

## 水際

最初の地方だけでなく、256×256の世界全体に共通の水際を用意した。周囲9セルの水・陸から連続した輪郭を計算する512種類の接続タイルを使う。水と土の模様を縮めず、元の32pxの大きさで描く。素材そのものはぼかさず、透明範囲も0/255の二値である。

生成処理は `tools/build_world_shoreline.py`、接続番号は `world/shoreline.json`、共通描画は `WorldShoreline`。最初の地方の描画と広域描画へ接続した。世界の地形データ `world/terrain.json`、通行判定、関所の条件、拠点の配置、移動の解放条件は変更しない。陸上の木道は水域に数えず、実際の水に接する橋だけを水際計算へ含める。

保存形式は、不透明な色画像 `world_connected_water.png` と、明暗2色で透明範囲を記録した `world_water_alpha_mask.png`。Godotで一度だけ合成して共有する。合成結果は元の透明な水際画像と全画素一致することを確認する。既存の素材検査は変更していない。検査改訂案は不採用・未適用の検討記録として `docs/proposals/shoreline-validation.*` に残した。

## 確認画像と検査

`docs/verification/sprint5-home-shoreline/` に保存。

- `home-before-after.png`：家の変更前後の実画面。
- `home-target-comparison.png`：村の目標画像の木材・色と、家の配置の比較。
- `gate-shore-before-after.png`：関所の水際の変更前後。
- `shore-target-comparison.png`：川の目標画像との比較。
- `global-coasts.png`：世界4方面の海岸の描画確認。未解放の地方へ実際に到達した記録ではない。
- `runtime/`：既存の通常入力による9場面と、広域描画4場面。

`tools/capture_home_shoreline.gd` は既存の撮影・R-07を変更せず利用し、撮影先を今回の記録へ分ける。全世界の色・透明範囲を合成した画像のハッシュと、広域画面に実際に描かれた水面の画素も確認する。生成時には4096の地形配置について8192か所の共有境界の連続性、512形のセル中心、全65536セルへの適用を確認する。

```powershell
. ./tools/prepare_scope_env.ps1
python tools/build_cozy_home.py
python tools/build_world_shoreline.py
python tools/validate_assets.py --strict
python tools/check_frozen_files.py
godot --headless --editor --import --quit
godot --path . --rendering-method gl_compatibility --script res://tools/capture_home_shoreline.gd
python tools/build_home_shore_review.py
python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .
```

この区切りの報告後は採用を待つ。森の塔・スイナ加入、港町・転移・船にはまだ進まない。

ローカルでは素材658件・音14件・パレット3件・字体2件の検査、保護対象26件の一致、R-01〜R-08がすべて成功した。家から関所までの通常入力による14項目と、世界4方面の実描画・水面画素の照合も成功。新10素材・配置4ファイルは再生成してバイト一致した。既存648素材、パレット、world/terrain.json、tools/validate_assets.pyは変更していない。記録は確認画像フォルダの `preservation.json`・`r01-r08.txt`・`runtime/checks.json`。CIは終了を確認して最終報告へ記載する。
