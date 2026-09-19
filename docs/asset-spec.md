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
