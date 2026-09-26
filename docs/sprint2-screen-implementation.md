# スプリント2：最初の地方の画面と操作

2026年9月27日。依頼者はスプリント1を採用し、スプリント2の開始を指示した。追加原画の保管と歩行素材の整備も同時に進めた。

現状は、描画・通常操作・音の接続を実装した段階。**探索中の常設セーブ・メニューボタン2個の撤去は未適用**。凍結R-07との入力契約の衝突について依頼者に判断を求めている。スプリント2全体やゲーム全体の完成とは扱わない。

## 実装した内容

| 内容 | 実装・データ |
| --- | --- |
| 画面全体の探索と、150msの1セル移動に合わせた表示補間 | `scripts/world/first_region_view.gd`、`scripts/ui/game_root.gd`。移動判定は既存の `WorldMovement` を継続利用 |
| 人物と建物を足元の順に描画 | 描画層と人物の重ね順。木の裏へ回ったときの表示も足元で判定 |
| 村の建物・畑・井戸・住人、家・宿・道具屋・武器屋の内部 | `world/first_region_visuals.json`、`world/first_region.json`、`world/interiors.json` |
| 自然な洞窟の岩壁・地底湖・階段・宝箱・ボス | 採用済みの64px岩壁の配置を再利用。宝箱は2階合計3個で、開閉は保存状態から描画 |
| 会話中の名前と本文 | `scripts/ui/first_region_screen.gd`。仲間加入直後も会話終了までは相手を表示 |
| 場所名の一時表示 | 場所を移った時に約2.2秒表示し、探索中の常設タイトルは出さない |
| Escapeで開くコマンド窓・道具・編成・手帳・保存・再開 | 通常のキーとボタンで操作。既存の装備・育成処理を継続利用 |
| 道具「世界地図」 | `scripts/ui/first_region_atlas.gd`。全256×256地形と現在地の点滅を表示。位置・所持品・進行を変えずに閉じる |
| 戦闘の背景・窓・敵の体格・味方表示・敵HPと行動予定 | `scripts/ui/rpg_battle_view.gd`。敵画像を登録時の実寸で描き、味方は48pxの戦闘コマを使う |
| 敵出現・勝利時の短い点滅、攻撃時の揺れ | 戦闘の計算結果を変えない表示処理 |
| BGMと効果音 | `scripts/ui/rpg_audio.gd`。BGM再生器2個、効果音再生器6個。登録済みの6曲・8効果音を使う |
| 住人の移動と向き | 一部の村人が決まった4セルを歩き、話しかけると主人公へ向く。位置と向きは追加の保存項目で保持 |

村・洞窟の表示は `docs/verification/art-review-2/mock-maps/` の配置から生成した。比較用JPEGをゲームの背景へ貼り付ける方式ではない。素材はすべて台帳にあるPNGを使用している。

## 地形と配置

- 村外観は36×24セル。カイナの家、宿、道具屋、武器屋は別の歩ける内部マップ。
- ソルダ洞窟は36×24セルの2階。階段の往復、宝箱3個、ボス、退出を通常の入力で通れる。
- 周辺の表示・通行は、既存256×256世界の `[24,40]` を起点とする32×18セルの専用層へ接続した。`world/terrain.json` と既存の拠点グラフは変更していない。
- ミルフェ村入口 `[32,53]`、ソルダ洞窟入口 `[48,50]`、ベルナの関所 `[43,47]`。村の東に洞窟、北に川と関所を配置した。
- 関所の川は、通行証なしで別経路から北へ回り込めない。地域の外周は山と海で通行を止めている。
- 比較案にある将来用の城・塔の印は、現在のプレイ可能範囲へ追加していない。後続スプリントで内部と一緒に接続する。
- 小物が玄関を塞いでいた2か所を本番用データで移した。原本の比較用JSONは変更していない。

再生成は `python tools/build_first_region_presentation.py`。通行証前後の到達性と、村の主要地点・洞窟の階段・宝箱・ボスへの経路を生成時に確認する。

## 追加原画と歩行

`ユーザー作成オリジナル画像2.zip` のPNG43枚を `assets/_incoming/owner-2026-09-26/reference-pack-2/` へ元のファイル名・元のバイト列で保管した。内容の種類は42。重複している `IMG_1042.PNG` と `IMG_1042 2.PNG` も両方保持している。

若い4人の歩行は、32×48px・3列×4方向、人物ごとの既存共通16色、二値透過、接地線45行目で登録した。`IMG_1048.PNG` の向き違いは採用せず、正しい右向きの原画を使った。人物を左右反転してはいない。4人の名前・役・配置は未決のまま。

再生成は `python tools/import_owner_walks.py`。検査は `python tools/check_owner_walks.py`。検査は今回の記録用固定タグを参照し、後続作業の作業ツリーには依存しない。原画43枚の指紋は、提供ZIPから独立して取得した値へ固定している。

## 検査と未達

| 検査 | 現在の結果 |
| --- | --- |
| 保護されたR-07 | 14/14 PASS。実歩行・戦闘・保存・関所通過を維持 |
| R-01〜R-08 | ローカルで全件PASS |
| 素材検査 | 531画像・14音声・3パレットで問題なし |
| 保護ファイル | 26/26一致。変更していない |
| 画面の追加検査 | `tools/check_first_region_screen.gd`。10件中9件PASS、U03だけFAIL |
| U03：常設ボタン0件 | 未達。現在は凍結入力に必要な「セーブ」「メニュー」が画面端に残る |

U03を隠すためにボタンを透明化したり、検査時だけ別の画面にしたりはしていない。[衝突の説明](proposals/sprint2-r07-menu-input.md)と[具体的な差分](proposals/sprint2-r07-menu-input.patch)を用意した。14条件・上限・比較対象は維持し、通常のEscape操作へ合わせる提案。

実行例：

```powershell
. ./tools/prepare_scope_env.ps1
godot --headless --path . --script res://tools/smoke_first_region.gd
godot --headless --path . --script res://tools/check_first_region_screen.gd
godot --path . --rendering-method gl_compatibility --script res://tools/capture_first_region.gd
godot --path . --rendering-method gl_compatibility --script res://tools/check_first_region_screen.gd -- --capture
python tools/validate_assets.py --strict
python tools/check_frozen_files.py
python tools/check_build_identity.py
python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .
```

## 実画面と人間の確認

`docs/verification/first-region/01`〜`09` のPNGは実ゲームの通常操作を実描画で撮影する。10〜13はコマンド・道具・世界地図・編成の画面。歩行素材は `docs/verification/owner-originals-2/`。好み・読みやすさ・音量の採否は `PLAYTEST_QUEUE.md` に分離した。自動操作の時間を約60時間の人間のクリア時間と読み替えない。

## 実装修正と参考元

- 戦闘の再描画で自動的にボタンへフォーカスを移すと、表示送りのEnterがターン実行まで押すことがあった。戦闘では、プレイヤーが選んだフォーカスだけを維持するよう修正した。検査の入力・勝利条件は変えていない。
- Godot 4.7.2で、音声再生中の終了にOgg再生資源の警告が出る現象を小さいプログラムでも再現した。[Godotの報告 #76745](https://github.com/godotengine/godot/issues/76745)と同型の終了競合。通常の終了処理で停止・参照解放を行い、音声処理側の解放を100〜250ms待つ。headlessだけ音を無効化したり、警告を除外したり、検査の上限を延ばしたりはしていない。短い再現例5回とR-07で警告なしを確認した。
- [Godot RPG Creatorの固定版](https://github.com/newold3/Godot-RPG-Creator/tree/84c837af8826acf90f2c3fc2e6ea83e03f5bea70)の音声再生器の分離と窓の表示処理を参照した。作者Newold、MIT。コードの複写はなく、同梱の画像・音も取り込んでいない。ライセンスの記録は既存の `THIRD_PARTY_NOTICES.md` にある。
