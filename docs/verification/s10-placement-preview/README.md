# S10初配置の静的比較（未採用・実ゲーム未接続）

2026-10-28、ルッカ作成。固定基点 a4dc7c9d0d705f3181391fdccee4e4c825ddcaaf。

既存人物用派生画像の参照を完全tree・台帳・人物718枚と照合し、正式原画由来の登録がないことを確認したため、原画を読取専用で使った静的比較を作成した。別人物の似た素材は代用しない。

- A: セル[7,6]。中央経路から左へ寄せる。
- B: セル[8,6]。水盤の正面。推奨候補だが未採用。
- 既存長老[12,6]、入口[8,10]、出口[8,11]は変更しない。
- 2位置とも固定地形は通行セル。ただしNPC占有・実操作の経路検証はまだ行っていない。

原画 `assets/_incoming/owner-2026-10-05-grok-batch3/oasis-shrine-keeper-chibi.png` のSHA256は manifest.json を参照。原画は1バイトも変更しない。背景除去は周縁につながる薄灰色だけを4近傍で選択、境界で切出し、最近傍縮小、既存natural.gplの16色以内へ決定論的減色、二値透過。新しい色・ポーズ・反転・歩行コマは作らない。素材案は32×48、足元47行目。

comparison.png は全室512×384を2枚並べた静的合成。ゲーム内部512×288のカメラ・主人公・入力・会話窓の再現ではない。overlayの順序は first_region_view.gd に合わせ、人物底セル+1、部品bottom_row-0.5を使用。source-comparison.pngで原画と8倍表示を比較できる。原画の細かな表情・顔の線・目の色の識別性は縮小で失われる部分があり、原画と同等に読めるとは主張しない。

本番assets/、registry、world、ゲームコード、保護・検査・CIは変更していない。初配置の採否は依頼者の判断であり、この保存は採用ではない。

## 再現

Python/Pillow/numpyを使用。`tools/preview_s10_placement.py` に --source で上記原画、--inputs で以下の同名ファイルを読み取り用に集めたディレクトリ、--out で本ディレクトリを指定する。

- assets/interiors/region2_village_shrine.png
- assets/interiors/region2_village_shrine_overlay.png
- assets/characters/npc_oasis_elder/walk.png
- assets/palette/natural.gpl
- world/region2_village_backdrops.json

実行結果：終了0。原画SHA不変、32×48、二値alpha、16色以内、配置候補の地形セルをassert確認。再実行した5枚のPNGは全bytes/SHA一致。初回のPillow getdata非推奨警告はnumpy検査へ修正後、警告なしで再実行した。

画像5枚を目視。背景の灰色矩形は残っていない。候補位置では祭壇/燭台と人物が重ならない。拡大した顔の細線は不鮮明であり未確認扱いにはせず限界として記録。実ゲームの可読性/動作/原CI検証は別工程。
