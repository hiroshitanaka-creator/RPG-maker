# 素材規約（asset-spec）

対象: `assets/` 配下のすべての画像。
この規約に適合しない画像はコミットしない。適合判定は `python tools/validate_assets.py --strict` で行う。

---

## 1. 基本仕様

| 項目 | 値 |
| --- | --- |
| 内部解像度 | 512 × 288 px（16:9、タイル 16 × 9 枚ぶん） |
| タイル | 32 × 32 px |
| 拡大 | 整数倍表示（×2 = 1024×576、×3 = 1536×864、×4 = 2048×1152） |
| 補間 | 最近傍（Nearest）。ぼかし禁止 |
| 形式 | PNG（RGBA 8bit） |

Godot 側の対応設定（`project.godot`）:

```
[display]
window/size/viewport_width=512
window/size/viewport_height=288
window/stretch/mode="canvas_items"
window/stretch/aspect="keep"

[rendering]
textures/canvas_textures/default_texture_filter=0   # Nearest
```

## 2. 色と透過

2026年9月26日改訂：旧素材は `base.gpl`、新絵柄の素材は台帳の `palette` 欄で指定する `assets/palette/natural.gpl` を使う。素材スプリント以降の新絵柄は、人物の識別色と輪郭を保って自然色へ再配色する。`bright.gpl` は以前の素材作成記録として残す。`palette` がない項目は `defaults.palette` に従う。各パレットは64色以内とし、以下の1素材あたりの色数とアルファの規則は変えない。`base.gpl` は変更しない。

- 共通パレット: `assets/palette/base.gpl`（GIMP パレット形式。Aseprite / Libresprite / GIMP で読める）
- パレット全体の上限: **64 色**
- 1つのキャラクター素材で使える色: **16 色以内**
- 不透明ピクセルの色は、必ずパレットに含まれる色であること
- **アルファ値は 0 か 255 のみ。** 中間値（半透明・アンチエイリアスの縁）を含めない

最後の項目が最重要。生成AIが出力した画像は縁がぼけているため、そのまま入れるとドット絵に見えなくなる。取り込み時に必ず二値化する。

パレットが未作成の場合は、既存素材から作る:

```bash
python tools/build_palette.py assets/characters --max-colors 64 -o assets/palette/base.gpl
```

## 3. ディレクトリと命名

```
assets/
  palette/
    base.gpl
  characters/<char_id>/
    walk.png            歩行
    battle.png          戦闘
  monsters/<monster_id>/
    idle.png
  tiles/
    <tileset_id>.png
  ui/
    <name>.png
  registry.json
```

- `<char_id>` `<monster_id>` `<tileset_id>` は半角英小文字・数字・アンダースコアのみ。日本語・空白・大文字を使わない。
- 一度決めた ID を変更しない（シナリオ側の参照が切れるため）。

2026年9月26日追加のディレクトリ：戦闘背景は `assets/backgrounds/<id>.png`、物は `assets/objects/<id>.png`、拠点アイコン・会話窓・カーソルは `assets/ui/<id>.png` に置く。音は後述の「音」に従う。IDの命名規則は既存と同じ。

## 4. フレーム規定

### 4.1 歩行（`walk.png`）

| 項目 | 値 |
| --- | --- |
| 1コマ | 32 × 48 px |
| 並び | 横 3 コマ × 縦 4 行 |
| シート全体 | 96 × 192 px |
| 行の順序 | 上から 下向き / 左向き / 右向き / 上向き |
| 列の意味 | 0 = 直立、1 = 左足前、2 = 右足前 |
| 再生順 | 0 → 1 → 0 → 2 → （繰り返し） |
| 1コマの表示時間 | 0.15 秒を基準 |

左向きを右向きの反転で済ませない（髪型・装備の左右が入れ替わるため）。4行すべて用意する。

足の接地ラインは 4 行 12 コマすべてで一致させる。ずれると歩行が上下に跳ねる。検査は次で行う:

```bash
python tools/validate_assets.py --strict
```

### 4.2 戦闘（`battle.png`）

| 項目 | 値 |
| --- | --- |
| 1コマ | 48 × 48 px |
| 並び | 横 3 コマ × 縦 1 行 |
| シート全体 | 144 × 48 px |
| 列の意味 | 0 = 待機、1 = 攻撃、2 = 被弾 |
| 向き | 左向き固定（敵は画面左に配置） |

v1 では詠唱・勝利ポーズを作らない。必要になった段階で列 3 以降を追加する。

### 4.3 モンスター（`idle.png`）

| 項目 | 値 |
| --- | --- |
| サイズ | 32の倍数。最大 96 × 96 px |
| コマ数 | 1（静止） |
| 向き | 右向き固定（敵は画面左、プレイヤーは画面右） |

魔物化した味方ユニットも、戦闘表示はこの規定に従う（`characters/<char_id>/battle_monster.png`、48 × 48 × 3コマ）。

### 4.4 タイルセット

| 項目 | 値 |
| --- | --- |
| サイズ | 幅・高さとも 32 の倍数 |
| 推奨 | 512 × 512 px（16 × 16 タイル） |
| 余白 | タイル間の隙間・余白を入れない（0 spacing / 0 margin） |

### 4.5 2026年9月26日追加の大きさの規定

- 戦闘背景：512×288 px。
- 物：幅・高さとも32の倍数。宝箱や門の開閉は同じ大きさのコマを横に並べ、左が閉・右が開とする。
- 拠点アイコン：32×32 px。村・町・城・洞窟・塔を別画像にする。
- 会話窓・メニュー窓：64×64 pxの9分割用画像。四辺各8 pxを固定して拡張する。PNGのアルファは0か255とし、半透明は次の画面実装で表示時に設定する。
- カーソル：32×32 px、背景透過。
- 村人・店員・門番：既存の歩行規定（32×48 px、3×4コマ、16色以内、全コマの接地ライン一致）に従う。

2026年9月26日・目標画像対応の追加：

- 自然色の地面は128×128 px（32pxセル4×4）で模様を保ち、繰り返し境界を整える。
- 自動接続タイルは `assets/tiles/natural_auto_<id>.png`。1セル32×32、8近傍の有効47形と背景1形を模様位相ごとに並べる。台帳の `autotile.masks`・`phase_cells`・`stride`・`background_index` を配置時に使う。対角は隣接する縦横の両セルが同じ地形の場合だけ有効とする。
- わら家・町家・教会・城・井戸・噴水・屋台・壁・柵・洞窟・遺跡の小物は `assets/objects/natural_<id>.png`。幅と高さを32の倍数にし、複数セルの物は32pxの領域に分割して配置する。人物だけは既存の32×48 pxを維持する。

## 5. 素材台帳（`assets/registry.json`）

すべての画像は台帳に登録する。台帳にない画像は、`--strict` で検査エラーになる。

```json
{
  "path": "assets/characters/hero/walk.png",
  "kind": "character_walk",
  "size": [96, 192],
  "frame": [32, 48],
  "grid": [3, 4],
  "max_colors": 16,
  "status": "required"
}
```

`status` の意味:

| 値 | 意味 | ファイルが無いとき |
| --- | --- | --- |
| `required` | v1 に必須 | 検査エラー |
| `placeholder` | 予定済み・未作成 | エラーにせず「不足素材」として一覧に出す |
| `optional` | 無くても成立 | 無視 |

作る予定の素材は、先に `placeholder` で台帳へ登録しておく。こうすると不足分が毎回 CI のログに一覧で出るので、抜けが残らない。

## 6. 外部素材の取り込み（Gemini 等）

生成AIの出力をそのまま `assets/` に入れない。次の順で処理する。

1. 生成物を `assets/_incoming/` に置く（このフォルダは検査対象外）
2. 規定サイズへ縮小し、パレットへ量子化し、アルファを二値化する
3. `assets/` の規定位置へ配置し、`registry.json` を更新する
4. `python tools/validate_assets.py --strict` を通す
5. commit / push

2 の処理はスクリプト化して `tools/` に置く。手作業で毎回やらない。

## 7. 修正の頼み方

既存素材の修正は「描き直して」ではなく、加工内容を指定する。

| 悪い例 | 良い例 |
| --- | --- |
| 左向きの歩き出しを直して | `walk.png` の 2行目 2列目を、同じ行の 1列目を基準に下へ 1px 移動して書き出すスクリプトを作って |
| 色を揃えて | `battle.png` を `base.gpl` へ最近傍量子化して、パレット外の色を 0 にして |
| もう少し大きく | 1コマを 32×48 から 32×64 に変更（規約の改訂が必要。先に提案を出すこと） |

左側の頼み方をすると生成し直しになり、他のコマと整合しなくなる。

## 8. 音（2026年9月26日追加）

- BGM：`assets/audio/bgm/<id>.ogg`。ループ可能なOGG Vorbisで保存する。
- 効果音：`assets/audio/se/<id>.ogg` または `.wav`。
- 画像用の `assets` 一覧とは分け、台帳の最上位 `audio` 一覧へ登録する。`kind` は `bgm` または `se` とし、出典・加工内容を記録する。
- `assets/` 配下の未登録音声は検査エラーにする。取り込み中の `_incoming/` だけは既存の画像と同様に対象外。

## 9. ライセンスの記録（2026年9月26日追加）

新しい外部素材には `source_url`（原作者の配布ページ）、`author`、`license`（SPDX ID）、`retrieved_at`（取得日）、`modified`（変換内容）を必ず記録する。許可する外部ライセンスはCC0・MIT・BSD・Apache-2.0・Unlicense。転載サイトの表示だけでは確認済みにしない。ライセンス文と作者表記は `THIRD_PARTY_NOTICES.md` に残す。

生成素材は `source: "generated"`、`tool`、`generated_at`、生成指示の記録先を記載する。外部から取り込んだ素材のようにCC0等を推測して付けない。`license: "LicenseRef-Generated-Project"` はこのリポジトリ内で生成した素材を識別する記録であり、第三者素材の独自ライセンスを許すものではない。

既存108件の台帳項目と画像は変更せず、新項目にだけこれらの記録を追加する。既存項目の基準一覧は `assets/source_records/legacy-images.json` に保持し、新項目の記録漏れを検査する。
