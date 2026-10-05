# 011 確認画像

**以下はすべて、位置を直接読み込む確認用の状態の画像。本編で到達した記録ではない。** 歩行・階段は本番の矢印キー入力、描画は本番GameRoot、戦闘見本は本番RpgBattleViewを使う。画像の採否は依頼者・親の独立レビューへ渡す。通常のセーブファイルは変更しない。

## 原画の実測と派生

確認用図：[原画の幅の測定](measurements.png)、[測定座標](measurements.json)、[敵6体・ボスの素材見本](enemy-assets.png)、[見た目資料との比較](visual-target-comparison.png)。原画7点は基準mainと全バイト一致する。

## 各階の確認用状態

全体図は緑=通行、赤=不通、青=上層、黄=階段。通常歩行は一歩直後の歩行コマ。奥・手前は可視画素と遮蔽画素を実画面から数えて照合する。

| 階 | 全体図（通行＋上層） | 通常歩行 | 柱・石像の奥 | 同じ物の手前 | 初期の階段前 |
| --- | --- | --- | --- | --- | --- |
| 1階 | [全体](floor1-overview.png) | [歩行](latest/images/floor1-walking.png) | [奥](latest/images/floor1-behind.png) | [手前](latest/images/floor1-front.png) | [着地](latest/images/floor1-landing.png) |
| 2階 | [全体](floor2-overview.png) | [歩行](latest/images/floor2-walking.png) | [奥](latest/images/floor2-behind.png) | [手前](latest/images/floor2-front.png) | [着地](latest/images/floor2-landing.png) |
| 3階 | [全体](floor3-overview.png) | [歩行](latest/images/floor3-walking.png) | [奥](latest/images/floor3-behind.png) | [手前](latest/images/floor3-front.png) | [着地](latest/images/floor3-landing.png) |
| 最下層 | [全体](floor4-overview.png) | [歩行](latest/images/floor4-walking.png) | [奥](latest/images/floor4-behind.png) | [手前](latest/images/floor4-front.png) | [着地](latest/images/floor4-landing.png) |

## 階段を上り下りした直後（確認用状態・通常入力）

[1→2](latest/images/stairs-1-to-2.png)、[2→3](latest/images/stairs-2-to-3.png)、[3→最下層](latest/images/stairs-3-to-4.png)、[最下層→3](latest/images/stairs-4-to-3.png)、[3→2](latest/images/stairs-3-to-2.png)、[2→1](latest/images/stairs-2-to-1.png)。

## 戦闘描画器の素材見本（確認用状態・戦闘未有効化）

[新規3体](latest/images/battle-1.png)、[新規1体＋再利用2体](latest/images/battle-2.png)、[ボス](latest/images/battle-3.png)。既存画面の敵の最大数と重なりを守り、全7体を3枚に分けた。能力・勝敗・進行を実行した画面ではない。

実描画25枚の位置・向き・カメラ・可視／遮蔽画素・歩行コマ・敵の一致数は [撮影検査](latest/images/checks.json)。完成時固定と最新HEADの独立再撮影・検査記録は `ci/fixed/evidence/images` と `latest/images`。正式に記録した検査対象SHAは [固定・最新の集計](ci/summary.json)。CIが生成した最新の画面と、ブランチに記録した画面のSHAは区別する。
