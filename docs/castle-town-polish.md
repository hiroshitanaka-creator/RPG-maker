# 城下町（エルヴァ城下町・仮称）の見た目の仕上げ

目標は依頼者原画 IMG_0997（`docs/reference/visual-targets/first-castle-town.png`、付録B）。構造（壁・門・広場・噴水・教会・6棟の位置）、扉と部屋の対応、住人の役と台詞は初版（07ac451）のまま保つ。

## 経緯

1. 2026年9月28日、依頼者の6項目（木20本以上／門から噴水へまっすぐな十字の石畳／噴水のまわりに柵で囲んだ花壇4つ／大きな屋根の木造の家、屋根は赤・茶・青／家ごとの庭と樽・木箱・井戸・花／明るい緑の草地に花）を、案A・B・Cの3案で作った（20fdaab）。案Aは登録済み素材だけ、案Bは教会以外の5棟を木造の家に、案Cは宿屋・道具屋を町家に残した。3案の確認画像は 20fdaab の `docs/verification/castle-town-polish/variant-{A,B,C}/` に残っている。
2. 同日、依頼者が**案Bを採用**し、次の4点の修正を指示した。あわせて、南門で主人公が隠れる点は「門を主人公より奥に描く」、道の形は「城下町は十字の道、村はゆるく曲がる道」と仕様書に書き分けることに決まった。
   - 屋根：角が丸く柔らかい形 → 三角のはっきりした切妻屋根
   - 木：小さな木が一列に並んで生け垣のよう → 大きな丸い木を2〜3本ずつ固め、家の周りと町の縁を囲む
   - 道幅：十字の道が太く町が石畳で埋まる → 目標の絵と同じくらいに細くし、空いた分を庭と木に使う
   - 花壇：土の四角に見える → 柵で囲み、中に花がびっしり咲く形
3. 同日、依頼者が木・道幅・L字の花壇・南門・仕様書の書き分けを採用した（87b7e17）。スクリプトで描いた三角の屋根は、テントやピラミッドのように見えた。目標の屋根（斜め上から見下ろした台形の面と棟の線、正面の壁の上の小さな三角）をスクリプトで描くのは難しいと依頼者が判断したため、**家は案Aと同じ登録済みの町家・館の素材に戻した**。切妻屋根の家の素材は台帳とファイルから外した（87b7e17 に残る）。

## 修正後の内容

- **家**：登録済みの町家（赤2・青2）・館・教会。種類と位置は初版（07ac451）と同じで、扉のセルと出入口のつながりも初版と完全に一致する。屋根は赤・青と、館の赤茶。
- **木**：96×96（3×3セル）の大きな丸い木 `natural_tree_round_large` を16本、従来の丸い木を7本、計23本。隣り合う木をつないだ固まりは9個で、どれも2本か3本。同じ行に並ぶ木は4本まで。家の後ろの木は屋根の上の空いた角に重ね、屋根より奥に描く。
- **道幅**：南北の道は門と同じ4マス、東西の道は2マスのまま、噴水の広場を 14×11 から 12×8 セルへ縮めた。石畳のセル数は採用時の250から224へ減り、空いた場所に木と庭を置いた。
- **花壇**：噴水側の角を円弧で欠いたL字の花壇 `natural_fenced_flowerbed_{nw,ne,sw,se}` を噴水の斜め四方に置いた。木の縁と杭で囲み、中を葉と花で埋めて土を見せない。欠けた角は噴水を向く。
- **南門**：`scripts/world/first_region_view.gd` で、城下町の門（`gate_open`）を地面と同じく人物より奥に描く。門を使うのはこの城下町だけ。入場直後の位置（18,24）で主人公の不透明画素 707/707 が画面に見えることを通常操作の撮影で確かめた（採用前は同じ位置で不合格だった）。
- **仕様書**：`docs/experience-spec-v2.md` の「町・村・城」に「村の道はゆるく曲げ」「城下町は門から広場（噴水）へまっすぐな十字の道」と書き分けた。

住人は立ち位置だけ動かした（祠へ来た人は、教会前の1マス幅の通り道をふさがない (24,9)）。

## 素材（画像生成なし）

`tools/build_castle_town_polish_assets.py` が、登録済み素材の画素を切り貼りし、`natural.gpl` 内の色で描き足して作る。決定論的で、再実行するとバイト一致する。記録は `assets/source_records/castle-town-polish.json`、台帳は `assets/registry.json`（`component_sources` に元素材）。

| 素材 | 大きさ | 作り方 |
| --- | --- | --- |
| `natural_tree_round_large` | 96×96 | 丸い木の葉の部分を5つ重ね、幹を足す |
| `natural_fenced_flowerbed_{nw,ne,sw,se}` | 96×96 | 葉の下地に花壇・花の小物を重ね、木の縁と杭で囲む。北西の絵を反転して4方向 |
| `natural_fence_low_horizontal` | 64×32 | 柵の角材から組んだ細い横の柵 |
| `natural_grass_meadow` | 128×128 | 草地2の暗い粒を中間の緑へ寄せ、目標画像の草地の明るさへ合わせる |

採用前に使った `natural_wood_house_*`・`natural_fenced_flowerbed`・`natural_grass_meadow_light`（20fdaab に残る）と、切妻屋根の家 `natural_gable_house_*`（87b7e17 に残る）は使わなくなったため、台帳とファイルから外した。

## 確認画像（`docs/verification/castle-town-polish/`）

- `overview.png`：目標・変更前（07ac451）・採用時の案B（20fdaab）・修正後の一覧。切妻屋根の家の版の画面は 87b7e17 の `variant-B/full-town.png`。
- `variant-B/comparison.png`：目標と修正後の城下町全体。
- `variant-B/adopted-vs-revised.png`：採用時と修正後。
- `variant-B/full-town.png`：本番の描画クラス `FirstRegionView` で城下町全体（36×26セル）を1枚に描いた画面（`tools/capture_castle_town_full.gd`）。`adopted-full-town.png` は採用時の同じ画面。
- `variant-B/runtime/`：新規開始から通常入力で城下町まで歩いた実ゲーム画面（南門の入場位置・広場・南西の庭・北東の教会前）と `checks.json`。`runtime-sheet.png` はその一覧。
- `variant-B/map-00.png`：配置データだけから描いた確認画像。
- `before-comparison.png`・`before-full-town.png`：目標と変更前。

比較画像は `python tools/build_castle_town_polish_review.py` で作り直せる。

## 検査

```bash
python tools/build_castle_town_polish_assets.py
(cd tools && python3 build_castle_town.py)          # CASTLE_TOWN_VARIANT=0 で初版を07ac451とバイト一致で再生成
python tools/check_castle_town_polish.py
python tools/validate_assets.py --strict
python tools/check_frozen_files.py
godot --headless --import
CASTLE_CAPTURE_OUTPUT=res://docs/verification/castle-town-polish/variant-B/runtime/ godot --path . --rendering-method gl_compatibility --script res://tools/capture_castle_town.gd
godot --path . --rendering-method gl_compatibility --script res://tools/capture_castle_town_full.gd -- res://docs/verification/castle-town-polish/variant-B/full-town.png
```

`tools/check_castle_town_polish.py` は、比較の相手を作業直前のコミット 07ac451（道幅は採用時の 20fdaab）に固定し、次を確かめる。

- 6項目：木の数と位置、十字の石畳、花壇4つ、屋根の色と木造の家の数、庭の小物、明るい草地と花
- 修正：家は登録済みの町家・館で種類と位置が初版と同じ・スクリプトで描いた家を使わない／大きな木6本以上・隣り合う木の固まりがどれも2本か3本・同じ行の木は4本まで／石畳のセル数が採用時より少なく東西の道は2マス幅／花壇の欠けた角が噴水を向く
- 変えていないこと：城下町以外の地図・部屋、扉と部屋の対応と扉のセル、城内・店の出入口、住人の役・絵・台詞、町の名前

(4)の「大きな屋根の木造の家を中心に」は、依頼者の決定で家を町家に戻したため検査しない。

`tools/capture_castle_town.gd` は、環境変数 `CASTLE_CAPTURE_OUTPUT` を指定したときだけ保存先を変え、城下町の撮影位置を4か所追加する（入場位置の撮影では主人公の画素が90%以上見えることも判定する）。保護済みのR-07の経路・14項目・上限は変更していない。

## 目標画像との残る違い

- 目標画像には南門がなく、南の石垣の切れ目から道が出ている。今回は初版の構造（南北2つの門）を保った。
- 目標の家は木造の大屋根（台形の屋根の面と棟の線）。今回は依頼者の決定で、半木骨造の町家・館の素材のまま。木造の大屋根の家は、新しい原画が用意できたときの課題として残る。
