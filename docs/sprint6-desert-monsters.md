# 第2地方の新しい敵3体と沿岸の通常遭遇

## 2026年9月30日：青緑色の修正

依頼者はPR #7の航路・沿岸の遭遇・新3体の形を採用した。サソリと砂の虫の体が紺・灰へ置き換わっていたため、IMG_1183に実在する青緑4色をnatural.gplの末尾に追加して2体を再配色した。元の72色の順番・値・バイト列、2体の形と透過範囲は維持する。ミイラは従来の72色で再現し、他の素材を変えない。

| 追加色 | RGB | 原画の採取位置（左上を0,0） | 理由 |
| --- | --- | --- | --- |
| #132D2E | 19,45,46 | IMG_1183 (198,149) | サソリの尾の暗部を紺へ置き換えない |
| #274742 | 39,71,66 | IMG_1183 (181,141) | サソリの体の主な青緑を残す |
| #426054 | 66,96,84 | IMG_1183 (609,234) | 砂の虫の頭と節の中間色を残す |
| #627D6C | 98,125,108 | IMG_1183 (632,228) | 明部が灰色になるのを防ぎ、体の形を見せる |

採取記録は `assets/source_records/natural-teal-extension.json`。`python tools/extend_natural_teal.py` → `python tools/import_owner_desert_monsters.py` の順で再現する。素材規約と `validate_assets.py` のnatural.gpl全体上限だけを72→76色へ同期し、1体32色以内などの条件は変えない。

比較画像は [サソリと砂の虫の原画比較](verification/sprint6-desert-monsters/teal-source-comparison.png)、再配色後の配置は [沿岸の3種](verification/sprint6-desert-monsters/runtime/08-coastal-three-desert.png)。対象外素材・輪郭・既存パレットの照合結果は `verification/sprint6-desert-monsters/teal-preservation.json`。

今後の原画由来4色までの追加許可をAGENTS.mdへ、砂の岸の平坦さと階段状の水際をroadmap-v2.mdの仕上げ一覧へ記録した。岸の見た目は今回は変えていない。

再配色後の確認：R-01〜R-08全件成功（R-07は89.5秒）、素材検査1,079画像ほか成功、凍結26件一致、追加境界91項目成功、通常ルート全体の再撮影73項目・9画像成功。対象外の1,077画像・14音・2字体は変更前と一致した。撮影記録の版IDは再実行による実測値である。

以下は初回取り込みの記録である。形・寸法・登録先は継続し、対象2体の配色と確認画像は上記の修正版を使う。

2026年9月30日の依頼。IMG_1183の左からサソリ・砂の虫・ミイラを取り込んだ。沿岸の通常遭遇は花咲く刺サボテン・サソリ・砂の虫。ミイラと石の翼像は今後の遺跡の候補で、通常遭遇へは登録しない。琥珀のしずくは使わない。

## 原本と変換

- 受領原本：`assets/_incoming/owner-2026-09-30-interiors/IMG_1183.png`。mainの5ece0d5で受領し、原本の999,023バイトは変更していない。
- SHA-256：`d812496d505273e10868813813cde4f4bd970c1a2a74a4a74ec4c4a80b10fa50`。
- 台帳が参照する従来の取り込みルートにも、同一バイトの保管コピーを `assets/_incoming/owner-2026-09-26/supplement-2026-09-30/IMG_1183.png` として保存。受領日・原本の実際の所在は2026年9月30日として記録し、双方のハッシュを照合した。元ファイルの移動や検査の許可範囲の変更はしていない。
- 外周につながる明るい灰色だけを除去する。RGB各値185以上、最大値と最小値の差16以下を背景候補として、外周から4方向に連結する部分だけを透明にする。切り抜き後に黒背景用の処理を再適用せず、サソリの暗い体と黒い輪郭を残した。
- 最近傍で縦横比を保って縮小し、natural.gplの最も近い色へ減色する。各32色以内・二値透過、右向き、静止1コマ。ゲーム上の表示は既存の敵と同じ4分の3。
- 変換記録は `assets/source_records/owner-desert-monsters-20260930.json`。`python tools/import_owner_desert_monsters.py` で再現できる。既存の素材とパレットは変更しない。

| 敵 | 体格 | 素材寸法 | 不透明領域 | 色数 | 登録 |
| --- | --- | --- | --- | --- | --- |
| サソリ（仮） | 中80px | 96×96 | 70×80 | 32 | 沿岸 |
| 砂の虫（仮） | 大96px | 96×96 | 67×96 | 32 | 沿岸 |
| ミイラ（仮） | 中80px | 96×96 | 80×77 | 32 | 遺跡用の控え |

## 確認画像

- [原画・切り抜き・ゲーム用素材の比較](verification/sprint6-desert-monsters/source-comparison.png)：切り抜き後と、減色・縮小した素材を区別して示した。右側のゲーム用素材は3倍、その下は戦闘画面の表示サイズ。
- [新原画3体を砂漠に並べた見本](verification/sprint6-desert-monsters/runtime/07-imported-three-desert.png)：サソリ・砂の虫・ミイラ。本番の戦闘描画を使った素材見本。ミイラを通常遭遇へ登録した意味ではない。
- [沿岸に登録した3種の見本](verification/sprint6-desert-monsters/runtime/08-coastal-three-desert.png)：刺サボテン・サソリ・砂の虫。
- [通常歩行から始まった地上戦闘](verification/sprint6-desert-monsters/runtime/06-ground-natural-encounter.png)：実際の通常遭遇。この記録では刺サボテンと遭遇した。
- [航行](verification/sprint6-desert-monsters/runtime/01-crossing-to-second-region.png)、[上陸](verification/sprint6-desert-monsters/runtime/02-landed-on-sand-coast.png)、[海の通常戦闘](verification/sprint6-desert-monsters/runtime/03-second-region-sea-battle.png)、[沿岸の徒歩](verification/sprint6-desert-monsters/runtime/04-coast-walking.png)、[帰還](verification/sprint6-desert-monsters/runtime/05-returned-to-first-region.png)も、登録後の状態で撮り直した。

3体を並べた見本では通常宿泊後の状態を複製したセッションを使い、通常プレイの状態・保存は変えない。通常遭遇・航行では位置・乱数・勝敗・所持品を注入していない。通常プレイの記録ではハルドとスイナが戦闘不能のままであり、見本のためにその結果を修正していない。

## 通常遭遇と検査変更

第2地方の岸の遭遇率は既存の世界マップと同じ0.025。刺サボテン・サソリ・砂の虫の各1体編成から選ぶ。能力・技・弱点・報酬は、それぞれ既存shell_guard・bat・ward_slimeと同値で、既存の敵の定義は変えていない。難易度の最終採用を示すものではない。

依頼者の明示承認により、`game_session.gd` と `check_enemy_encounters.gd` の総数を36種へ更新した。旧30種の「5系統×6種」は旧本編の30種を対象にそのまま確認し、追加海3種・地上3種はIDを別に完全照合する。全36種の画像参照、回復・防御・蘇生・行動予定・連戦保存の条件は維持した。

`check_second_region_coast.gd` は、63241bcの旧30種の不変、新原画と保管コピーのSHA-256、変換記録、96px寸法、32色以内、二値透過を追加確認する。地上遭遇のID集合が指定3種と完全一致し、琥珀のしずく・ミイラ・石の翼像が含まれないことも確かめる。`capture_second_region_coast.gd` は通常の地上遭遇と、素材を並べた見本を区別して撮影する。R-01〜R-08・保護ファイル・時間上限は変更しない。

## 実施済みの検査

- 追加境界・素材対応検査：91項目成功、エラー・警告なし。
- 敵の遭遇検査：旧30種と追加6種、既存の戦闘・保存条件で成功。
- 通常撮影：73項目・9画像、373歩・536入力で成功。180秒・600歩・3,000入力・300ターンの上限を維持。
- 素材検査：画像1,079件・音14件・パレット3件・字体2件で問題なし。
- 凍結ファイル：26件一致。
- R-01〜R-08：36種の登録後に全件成功。R-07は91.1秒。
- 保存位置の置き直し：31部屋・199項目成功。
- 再生成：新3体と台帳が再実行前後で完全一致。既存1,076画像は5ece0d5の内容と全件一致。

CI全ジョブの最終結果は、push後の実行が終了してから報告する。港町の外観・室内6部屋と魔物職の解放は今回の範囲外である。
