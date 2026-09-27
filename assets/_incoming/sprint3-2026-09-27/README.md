# スプリント3・第1回の生成原画

組み込みimagegenで、依頼者のIMG_1018〜1021を衣装、採用済みparty-design-sheetを顔・髪・体格の基準として生成した。元の依頼者画像は変更していない。

生成指示、参照原画、SHA-256、採否は `assets/source_records/sprint3-generation.json` に記録。`warrior-battle.png` は剣が長いため不採用とし、`warrior-battle-compact.png` を採用した。原画13枚は加工せず保持する。

ゲーム用画像は `tools/import_job_costumes.py` で別ファイルへ変換する。左右反転はせず、生成原画の別方向を使う。歩行32×48・12コマ、戦闘48×48・3コマ、接地行47、自然色パレット内16色、アルファ0/255。
