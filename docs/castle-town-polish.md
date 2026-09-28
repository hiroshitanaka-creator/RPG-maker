# 城下町（エルヴァ城下町・仮称）の見た目の仕上げ

2026年9月28日の依頼者指示。目標は依頼者原画 IMG_0997（`docs/reference/visual-targets/first-castle-town.png`、付録B）。構造（壁・門・広場・噴水・教会・6棟の位置）は初版のまま、次の6点を直す。依頼者が1案を選ぶまで main には取り込まない。

1. 丸い緑の木を20本以上、家の周りと町の縁に置く
2. 門から噴水へまっすぐな十字の石畳にする
3. 噴水のまわりに、柵で囲んだ花壇を4つ置く
4. 大きな屋根の木造の家を中心にし、屋根の色を赤・茶・青程度に絞る
5. 家ごとに庭を区切り、樽・木箱・井戸・花を置く
6. 草地を明るい緑にし、花を点々と咲かせる

## 3つの案

| 案 | 内容 | 新しい素材 |
| --- | --- | --- |
| A | 登録済み素材だけで配置を直す。家は初版の町家・館のまま（屋根は赤・青）。木造の大屋根の家がないため、(4)の「木造の家を中心に」は満たさない。草地は既存の明るい草地2、花壇は既存の柵と花壇を組む | なし |
| B（おすすめ） | 6棟のうち教会以外の5棟を木造の大屋根の家（赤2・青1・茶2）にする。草地は目標画像の明るさに合わせた草地、花壇は細い柵で囲む | 派生素材7点 |
| C | 宿屋と道具屋は初版の町家（台詞の「赤い屋根は宿屋」「青い屋根が道具屋」の見分けを町家の形でも残す）、武器屋と住まい2棟の3棟を木造の家にする。草地は案Bより一段明るい緑 | 派生素材7点（案Bと共通） |

3案とも共通：南北の門を結ぶ4マス幅のまっすぐな石畳、東西の外壁まで2マス幅の石畳、噴水を囲む四角い広場、噴水の斜め四方の花壇4つ、家ごとの庭（柵・樽・木箱・井戸・花）、丸い木20本以上（案A 20本、案B・C 22本）。家の扉と室内の部屋の対応、住人8人の役・絵・台詞は変えていない。住人の立ち位置は新しい配置で通れる場所へ移した。

有効な配置（`world/` の3ファイル）は案Bにしてある。案の切り替えは次のとおり。

```bash
cd tools
CASTLE_TOWN_VARIANT=B python3 build_castle_town.py   # A / B / C、0 は初版（07ac451 とバイト一致）
```

## 派生素材（画像生成なし）

`tools/build_castle_town_polish_assets.py` が、登録済み素材の画素を `natural.gpl` 内の色へ置き換え・切り貼りして作る。決定論的で、再実行するとバイト一致する。記録は `assets/source_records/castle-town-polish.json`、台帳は `assets/registry.json`（`component_sources` に元素材）。

- `natural_wood_house_{red,brown,blue}.png`（224×192）：わら屋根の家A（`natural_farm_house_a.png`）の屋根だけを、手で指定した多角形と色の条件で選び、周囲の平均の明るさで陰影を付けた4段の色に、5画素ごとの段と段ごとにずらした継ぎ目を描いて板葺きにする。壁・扉・樽は元のまま。
- `natural_fenced_flowerbed.png`（96×96）：柵の角材・土・花壇・花の小物を組んだ、柵で囲んだ花壇。
- `natural_fence_low_horizontal.png`（64×32）：柵の角材から組んだ、庭と道を区切る細い柵。
- `natural_grass_meadow.png`（128×128）：草地2の暗い粒を中間の緑へ寄せ、目標画像の草地の明るさへ合わせた地面。花の色は変えない。
- `natural_grass_meadow_light.png`（128×128）：さらに一段明るい緑（案C）。

すべて64色以内・二値透過・32pxの倍数。`python tools/validate_assets.py --strict` で確認した。

## 確認画像（`docs/verification/castle-town-polish/`）

- `overview.png`：目標・変更前・3案の一覧。
- `before-comparison.png`：目標と変更前（07ac451）。
- `variant-X/comparison.png`：目標と、その案の城下町全体。
- `variant-X/full-town.png`：本番の描画クラス `FirstRegionView` で城下町全体（36×26セル）を1枚に描いた画面（`tools/capture_castle_town_full.gd`）。
- `variant-X/runtime/`：新規開始から通常入力で城下町まで歩いた実ゲーム画面（南門の内側・広場・南西の庭・北東の教会前）と `checks.json`。
- `variant-X/runtime-sheet.png`：上の実画面4枚の一覧。
- `variant-X/map-00.png`：配置データだけから描いた確認画像。

比較画像は `python tools/build_castle_town_polish_review.py` で作り直せる。

## 検査

```bash
python tools/build_castle_town_polish_assets.py
(cd tools && CASTLE_TOWN_VARIANT=B python3 build_castle_town.py)
python tools/check_castle_town_polish.py
python tools/validate_assets.py --strict
python tools/check_frozen_files.py
godot --headless --import
CASTLE_CAPTURE_OUTPUT=res://docs/verification/castle-town-polish/variant-B/runtime/ godot --path . --rendering-method gl_compatibility --script res://tools/capture_castle_town.gd
godot --path . --rendering-method gl_compatibility --script res://tools/capture_castle_town_full.gd -- res://docs/verification/castle-town-polish/variant-B/full-town.png
```

`tools/check_castle_town_polish.py` は、比較の相手を作業直前のコミット 07ac451 に固定し、6項目（木の数と位置、十字の石畳、花壇4つ、屋根の色と木造の家の数、庭の小物、明るい草地と花）と、城下町以外の地図・部屋・扉と部屋の対応・住人の台詞が変わっていないことを確かめる。家の絵の扉の列に合わせて、案B・Cでは城下町側の扉セルが2つ（武器屋 (30,15)→(31,15)、民家 (29,22)→(30,22)）動く。部屋との対応は同じ。案Aは (4) の木造の家の数で不合格になる（案Aの性質どおり）。案B・Cは全項目合格。

`tools/capture_castle_town.gd` は、環境変数 `CASTLE_CAPTURE_OUTPUT` を指定したときだけ保存先を変え、城下町の撮影位置を3か所追加する。保護済みのR-07の経路・14項目・上限は変更していない。3案とも追加確認83項目と継承14項目が成功した。

## 作業中に見つけて直したこと

- 案Bの配置で、祠へ来た人（25,9）が教会前の1マス幅の通り道をふさぎ、祠の扉へ歩けなくなった。立ち位置を（24,9）へ移した。配置データ上の通行判定では人物を数えないため、通常操作の撮影で見つかった。
- 城下町へ入った直後の位置（18,24）は南門のアーチの下で、主人公が門の絵に隠れる。初版から同じで、今回は変えていない（下の「判断が必要な事項」）。撮影は門の内側へ3歩進んでから行う。

## 目標画像との残る違い

- 木造の家は、わら屋根の家の屋根を板葺きの模様へ塗り替えたもの。目標画像の家は屋根がさらに大きく、切妻の形がはっきりしている。形そのものを変えるには新しい原画が必要。
- 目標画像の木は大きく、家の周りに密に集まっている。今回の木は64px（2×2セル）の既存素材で、密度も目標より低い。
- 目標画像には南門がなく、南の石垣の切れ目から道が出ている。今回は初版の構造（南北2つの門）を保った。
- 目標画像の花壇は噴水に沿ったL字形。今回は四角い花壇を噴水の斜め四方に置いた。
- 仕様書の「道はゆるく曲げ、碁盤の目のような区画にしない」に対し、今回は依頼どおり主道を直線の十字にした。家の扉から主道への小道は土の道にした。
