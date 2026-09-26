# 目標画像に合わせた素材の確認

2026年9月26日。今回は素材と静止配置だけを変更した。ゲーム画面・本番マップ・イベントは変更していない。

## 比較画像

- `village-farm-a-compare.png`：農村A。左が目標、右が登録素材の32pxタイル配置。
- `town-walled-a-compare.png`：城壁の町A。同上。
- `cave-natural-compare.png`：自然洞窟。同上。
- `world-organic.png`：32×18セルの世界マップ確認用配置。
- `new-assets-contact.png`：追加した建物・小物・地面79枚の一覧。
- `palette-natural-compare.png`：brightとnaturalの各64色。
- `target-color-samples.png`：目標10枚から採った代表色。
- `party-palette-review.png`：固定した形を変えず、人物の色だけを変換した前後比較。人物設定画そのものは変更していない。

目標との残る差は `../../visual-target-analysis.md` に記録する。素材検査の合格は絵の採用判断の代わりではない。

## 配置JSON

`mock-maps/` の4ファイルは、`tile_size: 32`、`width`、`height`、`tiles`、`layers`、`actors`、`anchors` を持つ。

`tiles` は台帳登録PNGのパスと32×32領域。各層の `cells` は `[x, y, tile_id]` の一覧で、記載順に重ねる。複数セルの建物も同じ規則で分割済み。`actors` だけは歩行規定の32×48領域を使い、セル上端から16px上に置く。カイナを大きく見せる追加拡大はない。

`anchors` は次の実装時に確認する入口などの候補位置であり、衝突・移動・イベントは定義していない。既存の `world/` は変更していない。

再描画は `python tools/build_visual_target_mocks.py`。画像の右側を描く `render()` は保存したJSONと台帳登録素材だけを読む。目標JPEGを開く処理は左側の比較欄だけに分離している。

## 接続タイル

土・石畳・川・地底湖・洞窟・森・山・丘・海岸の9系統。各47形と背景1形を、128px模様の4×4位相ごとに持つ。各アトラスは768セル、32pxセル8列×96行。通常の地面模様を32pxへ押し縮めずに接続するための構成である。

`autotile.masks` のビット順は北・東・南・西・北東・南東・南西・北西。対角のビットは、その両側の縦横セルが同じ地形の場合だけ有効。`stride=48`、`background_index=47`。JSON側では、位相と接続形から選んだ実際の領域を保存している。

`autotile-checks.json` は4×3の局所配置4,096通りから共有境界8,192件を照合した記録。`surface-seams.json` は反復面13枚の上下・左右端の不一致0件を記録する。これは形と模様の接続検査であり、自然に見えるという主観評価ではない。

## 変換・検査の記録

- `new-assets.json`：新規79枚のパス。接続アトラス9枚は台帳の `autotile` 項目と `autotile-checks.json` に記録。
- `requantization.json`：既存139枚の色数と前後ハッシュ、透過の不変確認。
- `scope-and-party-checks.json`：旧素材・音・設定画・パレットの不変確認、人物ごとの共通色数。
- `mock-checks.json`：4配置の寸法、領域数、セル数、登録素材だけであること。
- `palette-analysis.json`：色の標本化と誤差。`palette-mapping.json` は一般素材用の色相を保った最近色対応で、仲間の16色は各人の共通色から別途一対一で選ぶ。

生成指示と原画ハッシュは `assets/source_records/visual-target-generation.json`。生成原画の作業用コピーは検査対象外の `assets/_incoming/visual-targets/`。配布用の減色済みPNGは全件 `assets/` の台帳登録位置に保存した。

今回の順序は `build_natural_palette.py` → `requantize_natural_assets.py` → `import_visual_target_assets.py` → `build_natural_autotiles.py` → `build_visual_target_mocks.py` → `check_visual_target_assets.py`。再配色の原本は開始コミット `3c809e6` から取得する。取込は記録した生成原画が必要。以前の素材取込ツールは当時の再現用であり、今回の自然色を上書きするためには実行しない。

最終画像確認で、旧bright地形の葉の明部はそのまま移すと強すぎたため、自然色への対応前に明度を抑えた。山の青い陰は低彩度へ寄せ、水の青は維持した。世界の散布小物から海のセルを除き、川幅に合わせて橋を延ばした。人物の共通色・輪郭・ポーズにはこの地形用補正を適用していない。
